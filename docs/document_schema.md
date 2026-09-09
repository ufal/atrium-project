# 📄 ATRIUM Document Schema & Accretion Policy

This document defines the per-document aggregate record produced by `atrium_document.py` — the
**paradata pair**. Where [`paradata-schema.md`](paradata_schema.md) covers *how a run behaved*,
this covers *what we know about one document*: text, pages, entities and enrichment, gathered
across the pipeline into one FAIR, versioned JSON for search and catalogue export.

Template files: [`templates/shared/atrium_document.py`](templates/shared/atrium_document.py) ·
[`templates/shared/atrium_document.schema.json`](templates/shared/atrium_document.schema.json).
Several of this record's fields carry **controlled terms**; which values are legal in each, and what
they mean, is [`skos_strategy.md`](skos_strategy.md) and the registry it describes.
Design discussion: [ufal/atrium-llm-enrich#13](https://github.com/ufal/atrium-llm-enrich/issues/13).

## Why accretion, not an aggregator

The tools are separate containers reached over their own APIs, and **no tool sees another tool's
outputs**. So the record is not assembled by a central service; it travels *with* the document.
Each tool takes the previous version of the JSON — if it is given one — and returns it with
**only its own block** updated:

```
doc.json ──► [alto] ──► doc.json ──► [nlp] ──► doc.json ──► [llm] ──► doc.json
pages/lines           entities            enrichment
```

This keeps every tool independently runnable, makes updates granular (re-run one tool → one
block changes), and needs no shared volume or orchestrator.

## Schema `1.0` Context
- **Contract:** fixed `source`, `derived_from`, `regenerable`, `provenance` and `assembled`
  blocks, plus the content blocks (`pages`, `content`, `lines`, `tables`, `entities`,
  `translations`, `enrichment`, `page_categories`, `forms`) each written by exactly one tool
  per document — for the positional blocks, *which* tool is fixed by `source.origin`
  (see **Originators**, below).
- **First published version.** There is nothing to migrate yet; `load_document()` already
  carries the guard and `migrate_document()` the branch point, so the mechanism exists before
  it is needed.

## The accretion contract (six rules)

1. **Baseline in, record out.** Tools take an optional `--document-json` and write
   `--document-json-out` (default `<doc_id>.document.json`); services accept and return an
   optional `document_json` part. **`doc_id` travels WITH the baseline**: the originator derives
   it once with `canonical_doc_id()`, and every stage after it inherits that value —
   `DocumentRecord` keeps the baseline's `doc_id` and reports (never refuses) a caller that
   passed a different one. A stage's input is usually *not* the original document — the
   translator reads `PAGE_ALTO/<doc>/<doc>-1.alto.xml` — so a stage that keys its record off its
   own filename re-keys the document and orphans everything already in the record.
2. **Own block only.** A tool writes its own block(s); every other block is deep-copied through
   **unchanged**. This invariant is what makes the pair safe to pass around.
3. **No baseline → own part only** (plus `doc_id`/`schema_version`, and `source` if it is the
   first writer). Standalone runs keep working; `assembled.had_baseline` records which case it was.
   This is also the only case in which a non-originating tool's own `canonical_doc_id()` decides
   the key: with no baseline there is no document context to inherit.
4. **Per-block provenance.** Every write stamps `assembled.blocks[<block>]` with the writing
   tool's `program`, its paradata `run_id`, and a `paradata_ref`. Granularity comes from here.
   For a field-split block the stamp names the **most recent** writer, so the full picture lives
   in `provenance.contributors[]`, where each run lists the blocks it wrote.
5. **Licenses accrete** through `para_licenses.merge_effective_licenses` — the same
   most-restrictive union as paradata — so the JSON stays self-describing for catalogue export.
6. **Unknown or newer blocks are preserved** verbatim; a newer MAJOR `schema_version` is refused
   with the same guard as `load_paradata()`.

## Reference discipline (non-negotiable)

Only two classes of reference may appear: the **original input** (`source`, keyed by `doc_id` +
`sha256` — originals are archive-managed, so no path is required) and **persistent step outputs**
(`derived_from`).

Transient artifacts are **never** referenced. Page images and thumbnails are produced during
processing or created late by the presentation layer and are not stored; the annotated Markdown is
derived and disposable. Both belong in `regenerable` as a recipe:

```json
"regenerable": {
  "markdown": { "from": "TEITOK/CTX000000001.teitok.xml",
                "converter": "xml_to_md@0.3.0", "detail": "full" }
}
```

Visual overlay still works without stored images: every `bbox` is in one declared coordinate
space — **origin top-left, y increasing downwards, in the unit named by that page's
`pages[].canvas.unit`** — and `pages[].teitok_surface` is a **logical** `<surface>` id, so
the presentation layer re-renders on demand.

That convention is normative and format-independent. It is what ALTO already uses, so the
OCR path is unchanged, but it is **not** PDF user space, which puts the origin bottom-left:
a digital-born PDF adapter must convert before writing (with pdfplumber, use `top`/`bottom`,
never `y0`/`y1`). This used to read "bounding boxes stay in ALTO/TEITOK coordinate space",
which a digital-born record does not have — leaving the y-axis direction and the unit
undefined for exactly the writer whose whole selling point is exact coordinates.

## Block ownership

One owner per block. Blocks that several tools contribute to are split **by field**
(`BLOCK_FIELD_OWNERS`), so no field is ever co-mutated — use `merge_block()` for those and
`set_block()` for blocks you own outright.

### Originators (Issue #18 §1a)

Four blocks — `pages`, `content`, `lines`, `tables` — describe a document's **positional
plane**, and there are two ways to acquire one: OCR/ALTO, or direct extraction from a
digital-born PDF/DOCX. These are mutually exclusive per document, so those blocks have a
**tuple** of possible originators in `BLOCK_OWNERS` and the choice is fixed per record by
`source.origin`:

| `source.origin` prefix           | Originator         |
|----------------------------------|--------------------|
| `digital-born…` · `docx`         | `digital-convert`  |
| `ABBYY-ALTO` · `ocr:…` · `vlm:…` | `alto-postprocess` |

`_assert_origin_consistent()` enforces it on both `set_block()` and `merge_block()`. Matching
is case-insensitive; `resolve_originator(origin)` is the public form. An origin the table has
not been taught causes the check to **abstain**, not to fail — with a `NOTE` on stderr, so a
document that §1a has stopped applying to is visible rather than silent.

Calling `set_source()` before the first block write is the natural order but is **not
required**: a block written earlier is re-checked as soon as an origin arrives, and again in
`to_dict()`.

**One documented exception — the digital→OCR hand-off.** A record whose own `pages[]` sets
`needs_ocr: true` authorises `alto-postprocess` to re-originate its positional plane, even
though `source.origin` is a `digital-born-*` value. That is what the `needs_ocr` grant to
`digital-convert` exists for (Issue #10: an embedded text layer that decodes to corrupt
diacritics), and it keeps `source.origin` truthful — it records how the **original input** was
acquired, which really was a digital-born PDF. Who wrote the plane is `assembled.blocks[…]
.program`, as always, and `pages[].ocr` (never granted to `digital-convert`) records that an
engine ran, so "was this OCR'd" stays answerable.

> ⚠️ **`BLOCK_OWNERS` authorises writes; it is not the read-time contract.** To find out who
> wrote a block in a *given* record, read `assembled.blocks[<block>].program` — and for a
> field-split block, `provenance.contributors[]`, since the stamp names only the most recent
> writer. Code that hardcodes `alto-postprocess` as the source of `lines[]` was reading the
> wrong contract even before digital-born documents existed.

| Tool                | Owns                                                                                                                                                                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| page-classification | `page_categories` · `pages[]` *category, category_confidence*                                                                                                                                                                         |
| alto-postprocess    | `pages[]` *page_index, quality_score, quality_band, needs_ocr, needs_ocr_reason, ocr, canvas* · `content` · `lines[]` *categ, quality_score, lang, text* · `tables[]` — **originator, OCR/ALTO documents only**                       |
| digital-convert     | `pages[]` *page_index, canvas, quality_score, quality_band, needs_ocr, needs_ocr_reason* · `content` · `lines[]` *text, bbox, group_id, style, lang, quality_score, categ* · `tables[]` — **originator, digital-born documents only** |
| translator          | `translations` · `entities[]` *translation_en*                                                                                                                                                                                        |
| nlp-enrich          | `entities[]` · `lines[]` *lemma, upos, feats, teitok_ref, bbox* · `pages[]` *teitok_surface* · `derived_from.teitok`                                                                                                                  |
| llm-enrich          | `enrichment` · `forms` · `entities[]` *pid* · `regenerable.markdown`                                                                                                                                                                  |

`quality_score` is one axis — **text trustworthiness, 0–1** — with two derivations. On the
OCR path it is an engine-confidence proxy; on the digital-born path it is a decode-sanity
score (Issue #10's vowel/consonant ratio and dictionary hit-rate over the embedded text
layer). Which derivation produced a given value is answerable from `source.origin`, so the
field is not split. Consumers that filter on it (`json_to_md --min-quality`) are filtering
the same thing either way: *do not show this line to the model*.

## Usage

Alongside the tool's existing `ParadataLogger`, so both records share one `run_id`:

```python
from atrium_document import DocumentRecord

with DocumentRecord.open(doc_id, "llm-enrich",
                         baseline=args.document_json,      # may be None — rule 3
                         run_id=logger.run_id,
                         paradata_ref=paradata_path) as doc:
    doc.set_block("enrichment", {"items": items})
    doc.add_derived_from("enriched", f"{doc_id}_enriched.json")
    doc.add_regenerable("markdown", {"from": teitok_path,
                                     "converter": "xml_to_md@0.3.0", "detail": "full"})
    doc.add_license_detail(paradata["license_detail"])
```

Field-level contribution into a shared block:

```python
doc.merge_block("lines", rows)   # writes only this program's declared fields
```

Shell stages use the CLI shim, as they do for paradata:

```bash
python atrium_document.py set-block --doc-id "$DOC" --program alto-postprocess \
    --block pages --payload pages.json --baseline "$DOC.document.json" --out "$DOC.document.json"
```

## Versioning Rules

1. **Additive Updates:** adding an optional field or a new block requires **no bump** — rule 6
   means existing tools pass unknown keys through untouched.
2. **Breaking Changes:** renaming/removing a field, or changing block ownership, bumps
   `SCHEMA_VERSION` to the next major (e.g. `2.0`).

   * **Not breaking, and therefore no bump:** adding an authorised *originator* to a block's
     candidate set, where the choice is fixed per document by `source.origin` and no existing
     tool loses a capability. No field is renamed or removed, every existing record stays
     valid under the new module, and every existing tool keeps writing exactly what it wrote
     before. This is the Issue #18 §1a case, and it is called out explicitly because a
     literal reading of "changing block ownership" would have forced an unnecessary `2.0`
     migration across five repos. The distinction that matters: **widening write
     authorisation is additive; re-attributing an already-written block would not be.**
3. **Migration Mechanics:** a bump mandates a sequential `_migrate_X_to_Y()` and a branch in
   `migrate_document()`, exactly as in `atrium_paradata.py`.

## Consumers to Update on Bumps

* `merge_document_records()` and the `_cli()` shim in `atrium_document.py`
* `atrium_document.schema.json` (kept in step with the module — one is the contract, one the validator)
* Every tool's block writer, and any search/presentation layer indexing the record
* This document and the ownership table above

## Distribution

`atrium_document.py` and `atrium_document.schema.json` are **hub-canonical**: they live here in
`docs/templates/shared/` and are copied byte-identical into the tool repos, enforced by
`para-drift.reusable.yml` — the same guarantee already covering `atrium_paradata.py` and
`para_licenses.py`.

## Changelog — 2026-07-31 hardening pass

Prompted by the issue #13 alignment audit, which found that rule 2 ("own block only") was not
actually enforced and that three tools relied on it anyway:

* **`set_block()` now warns (raises under `strict=True`) on any block listed in
`BLOCK_FIELD_OWNERS`.** Those blocks (`pages`, `lines`, `entities`) are field-split by design;
a wholesale `set_block()` on one erases every co-contributor's fields. Use `merge_block()`.
* **`DocumentRecord.get_block(name, default=None)`** — read-only, deep-copied access to any
block, so a tool that needs to look at (not just write) a block no longer has to reach into
the private `_data` attribute.
* **`ParadataLogger.run_id`** (in `atrium_paradata.py`) — the public counterpart to `_run_id`,
matching `get_license_block()`. Several tools were already calling `logger.run_id` on the
assumption it existed; it did not, until now.
* **`canonical_doc_id(path)`** — one doc_id derivation for every tool to call, replacing four
independent ones (`Path.stem`, `name.split(".")[0]`, a bespoke TEITOK/CoNLL-U stripper, a CSV
column) that silently forked the same document into different records on multi-dot filenames.
* **`finalize()` writes atomically** (write to `.tmp`, then `os.replace`), so a crash mid-write
can no longer leave a corrupt record for the next tool's `load_document()` to trip over.
* **Schema:** `lines[]` now documents `lemma`/`upos`/`feats` — `BLOCK_FIELD_OWNERS` already
granted nlp-enrich these fields, but the schema didn't describe them (`additionalProperties: true` meant validation never caught the gap).

No `SCHEMA_VERSION` bump: all additive, and rule 6 (unknown fields pass through) already covers
tools not yet updated to call `merge_block()` or `canonical_doc_id()`.

## Changelog — 2026-08-03 (Issue #18 §1a)

* **`BLOCK_OWNERS` values may now be a tuple** — `pages`/`content`/`lines`/`tables` list
`("alto-postprocess", "digital-convert")`. Single-owner blocks are unchanged, including
their error message.
* **`ORIGIN_ORIGINATORS` + `_assert_origin_consistent()`** — the per-document originator is
selected by `source.origin` and checked on both write paths. `merge_block()` now runs the
check too; it previously bypassed `_assert_owner()` entirely, which is why `pages` and
`lines` were never ownership-checked at all.
* **`digital-convert` field grants** on `pages` and `lines`. The earlier draft granted the
digital converter only `["group_id"]` on `lines`, which `merge_block()` honours *silently*:
`text` and `bbox` were filtered out with no warning, and the result still validated because
`lines[]` requires only `page`+`line`. Fixed, and pinned by
`tests/test_document_originators.py`.
* **`llm-enrich-digital` renamed to `digital-convert`.** Every other identity in these tables
is a role (`alto-postprocess`, `page-classification`), not a repo; `llm-enrich-digital`
encoded the accident that the converter lives in `atrium-llm-enrich`, and it lands
permanently in `provenance.contributors[].program` in catalogue exports. It is also a
`ParadataLogger` identity needing a `para_config.txt` component→licence mapping, so it is a
two-schema commitment.
* **No `SCHEMA_VERSION` bump** — see the amendment to versioning rule 2 above.

> 📌 These edits are to the **hub canonical** files. `para-drift.reusable.yml` `diff -u`s
> `atrium_document.py` and `atrium_document.schema.json` against every tool repo, so the
> change is not landed until all five vendored copies are updated and `v1` is moved. Use
> `scripts/revendor_shared.sh`, and remember the check reads the hub side at `hub-ref`
> (default `v1`), not at the branch you merged to.

## Changelog — Issue #18 review pass (originator hardening)

A review of the §1a implementation against the repo found the contract correct in design and
escapable in practice. Everything here is **additive — no `SCHEMA_VERSION` bump**: no field
is renamed or removed, and every previously-valid record stays valid.

**Write-order.** `_assert_origin_consistent()` reads `source.origin`, so a run that wrote its
positional blocks *before* `set_source()` escaped the check permanently — and because
`set_source()` is first-writer-wins, the wrong origin was then frozen in. §1a's enforcement
therefore depended on a call order documented only in the issue plan. The abstain is now
**deferred**: such blocks are remembered and re-checked the moment an origin arrives, and
again in `to_dict()`. Callers no longer need the ordering discipline.

**Fan-in.** `merge_document_records()` was a third write path outside the contract. `source`
carries no `assembled.blocks` stamp, so both sides of its `updated_at` comparison were `""`,
`"" >= ""` was true, and every input file overwrote the previous — last-path-wins, silently
dropping the first record's `sha256` and able to swap the §1a origin out from under an
already-written plane. `derived_from` and `regenerable` are append-only maps and were
likewise replaced wholesale, losing the losing branch's entries. Now: `source` is
first-writer-wins per sub-key with a contradiction between inputs *refused*; those two maps
merge key-wise; ties keep the first record read (`>` not `>=`); and the merged plane is
checked against the merged origin.

**Origin spellings.** Matching was case-sensitive and had no bare `pdf` even though it
blessed bare `docx`, so `DOCX`, `abbyy-alto`, `Digital-Born-PDF` and `pdf` all matched
nothing — and since a non-match *abstains*, each of those silently switched §1a off for that
document. Matching is now casefolded, `pdf` is listed, and an unrecognised origin emits a
`NOTE` (never fatal — rule 6's spirit) so abstaining is visible. `resolve_originator()` is
public, so routing code and the write-time check cannot disagree.

**The digital→OCR hand-off.** `digital-convert` is granted `pages[].needs_ocr` so it can say
"this page's text layer does not decode — re-acquire it by OCR", but the origin frozen at
`digital-born-*` then refused every `pages`/`lines` write `alto-postprocess` attempted, making
§3's per-page routing unreachable while §1a insisted "no document is ever both". A record
whose own `pages[]` sets `needs_ocr: true` now authorises `alto-postprocess` to re-originate
it. This stays truthful: `source.origin` describes how the **original input** was acquired,
the block stamp names who wrote the plane, and `pages[].ocr` — never granted to
`digital-convert` — records that an engine ran.

**`merge_block()` field discipline.**
* `allowed = own_fields or …` treated an explicit `own_fields=[]` as "not supplied" and
  handed back the program's full grant, writing more than the caller asked for. Now
  `is not None`, which is what the `allowed is None` sentinel two lines down always implied.
* `own_fields` **conferred writership**: `merge_block()` never called `_assert_owner()` and
  the origin check abstains for non-candidates, so any undeclared program could write any
  block and be stamped as its author. It now narrows a declared grant rather than creating
  one.
* Dropped fields are **tracked**. The filtering stays silent by default (a co-contributor
  passing context fields it does not own is normal, and tightening it ecosystem-wide needs a
  call-site pass), but `dropped_fields()`, `assert_fields_survived()` and
  `warn_dropped_fields=True` make the loss inspectable. `assert_fields_survived()` is the
  round-trip check the §1b write-up asks for, in the module that owns the contract, since the
  JSON Schema cannot catch it — `lines[]` requires only `page`+`line`, so a row stripped of
  its `text` is a *valid* row.

**Row keys.** `_record_key()` hashed `json.dumps(value)`, so rows forked on Python **type**:
the schema types `page` as a string but nothing coerces it, and an originator passing `"1"`
beside a contributor passing `1` built **two** rows for one physical line — one with the
text, one with the morphology, neither complete, and the record still validated. Scalars now
normalise to text; container-valued keys (`entities[].char_span`) keep their JSON shape.

**`tables` was unreachable.** It had two declared originators but no `BLOCK_KEY_FIELDS` entry
and no `BLOCK_FIELD_OWNERS` entry, so `merge_block()` raised `no key fields known`, and with
`key_fields` supplied it emptied every row down to its key — the §1b silent drop again, on a
block the Definition of Done requires the converter to originate. Both entries added. The
`set_block()` field-split warning now names only genuine **co-contributors**, since
alternative *originators* are mutually exclusive per document and can never have fields on
one record to erase — so `set_block("tables", …)` is correct and quiet, while `pages`,
`lines` and `entities` warn exactly as before.

**Schema locator.** Plan §2's Layer D makes validation the output gate, but nothing could
*find* the schema: the hub keeps it under `docs/templates/shared/` and tool repos at their
root, and the only locator anywhere was a relative walk inside one test. `schema_path()`,
`load_schema()` and `validate_document()` resolve it next to whichever copy of the module was
vendored — which para-drift guarantees travel together. `validate_document()` raises when
`jsonschema` is absent rather than passing, because a gate that quietly no-ops is
indistinguishable from a passing one.

**Schema, additive fields and corrected descriptions.**
* `$defs/bbox` — the coordinate convention is now stated (see *Reference discipline*). It
  said "the coordinate space of the ALTO/TEITOK page", which the second declared writer's
  documents do not have.
* `pages[].needs_ocr_reason` — new, granted to both originators. `needs_ocr` means opposite
  things on the two paths and the renderer emits it as a cue, so with no field to carry the
  distinction every digital-born page rendered "no extractable text layer": false by
  definition for a document that has one.
* `pages[].page_index` — granted to `alto-postprocess` too, and documented as *the* ordering
  key. It is the only thing that orders a document whose `page` labels are roman numerals,
  which is at least as common in scanned volumes as in digital-born ones.
* `tables[].cells[].group_id` — new, and **the** join key. `tables[].group_id` was a single
  scalar for a whole table, so "cell text lives once in `lines[]` and is linked back via
  `group_id`" was unimplementable: nothing said which lines carry which cell, and positional
  inference fails the moment `rowspan`/`colspan` or a multi-line cell exists.
  `tables[].group_id` is now documented as the namespace prefix, and `cells[].lines` (an
  array of `$defs/line_ref`) covers a cell spanning several groups.
* `lines[].style` — new, `{bold, italic, heading_level}`, `digital-convert` only. Closes plan
  §1's last open mapping row as its own recommended option (c): semantic style only, no
  typeface or point size, because a downstream reader can act on "this was a heading" and
  cannot act on "this was Helvetica 12pt".
* `lines[].categ` — documents that `"Garbage"` and `"Inverted"` are load-bearing spellings
  (`json_to_md`'s `DROP_CATEGORIES`), so a synonym silently disables the filter rather than
  failing validation.
* `lines[].group_id` — says "table **cell**", not "table row", to match the join above, and
  its CONSUMER CONTRACT now names code that exists. It previously cited
  `rows_to_layout_markdown()`, which had no group tracking at all.
* `forms[].entity_key` — new, `$defs/entity_ref`, the natural key. `entity_ref` is an array
  index into `entities[]`, and a fan-in merge resolves blocks independently, so it can end up
  addressing whatever happens to sit at that position; it is marked deprecated with the
  reason.
* `pages[].canvas` — documents that `unit` must be written whenever any bbox is present.

## Changelog — 2026-08-06 (Issue #10: the doc_id fork the E2E caught)

`DocumentRecord` now **inherits `doc_id` from the baseline** instead of overwriting it with the
caller's value. Additive, no `SCHEMA_VERSION` bump: no field changes, and a run whose derivation
already agreed with its baseline behaves exactly as before.

**What happened.** `e2e-pipeline-smoke.yml`'s `assert_doc_id_stable()` — added days earlier for
D1/D2, and never yet triggered — failed on run
[31076188660](https://github.com/ufal/atrium-project/actions/runs/31076188660):

```
"work/doc_json/1_pc.json":       "CTX000000003"
"work/doc_json/2_alto.json":     "CTX000000003"
"work/doc_json/3_translate.json": "CTX000000003-1"   ← the fork
"work/doc_json/4_nlp.json":      "CTX000000003"
"work/doc_json/5_llm.json":      "CTX000000003"
```

**Why it is not a derivation bug.** The translator called `canonical_doc_id()`, exactly as D3
asks, on exactly the file it was given: `PAGE_ALTO/CTX000000003/CTX000000003-1.alto.xml`, a page
`page_split.py` had written. `CTX000000003-1` is the right answer *about that file*. The
translator is simply the one stage whose input is never the original document, and D1/D2 had
framed the finding as "hand-rolled derivations disagree with `canonical_doc_id()`" — true, but
one instance of the larger fault: **a doc_id derived from a stage's input is a guess about a
document the stage was never shown.**

Stripping a trailing `-<n>` would not close it. `sbn.2019-1` is a legal document name, so no
filename rule can tell a page label from a document's own last segment. The baseline does not
have to guess: the originator wrote the answer into it.

**The rule.** The originator derives `doc_id` once; every stage after it inherits. Concretely:

* `DocumentRecord.__init__` compares the caller's `doc_id` against the baseline's and keeps the
  **baseline's**, since every block already in the deep copy was written under that key. The
  divergence is reported through `_note()` — visible, never fatal, not even under `strict=True`:
  the record that comes out is the correct one, and raising would stall a pipeline over an id
  the constructor has just repaired. (`merge_document_records()` still *raises* on differing
  doc_ids: there two independent records disagree, which means two documents, not two names.)
* `DocumentRecord.derived_doc_id` keeps the caller's value, because a tool legitimately names its
  **own per-file outputs** after the file it read — `<file>_log.csv` collapsed onto the document
  would have page 2 of a batch truncate page 1's log. Only the record is re-keyed.
* `finalize()`'s default path follows `doc_id`, so a record's filename and the id inside it
  cannot disagree.
* `atrium-translator/main.py` applies the same rule to the two values computed *outside* the
  record — the CSV log's `file` column and the paradata `vocabulary_protected_terms` key — so
  the log, the paradata and the record name one document between them.

**Where the gate now points.** `assert_doc_id_stable()`'s failure message described the old rule
("derive it with `canonical_doc_id()` from the SAME original filename"), which is unactionable
for a stage that is never handed the original. It now names the inheritance rule and the reason a
correct derivation is still the wrong answer.

## Changelog — 2026-09-08 (issue #51: controlled terms get a declaration)

Additive throughout — **no `SCHEMA_VERSION` bump**. No field is renamed or removed, no ownership
changes, and every previously-valid record stays valid.

Seven of this record's fields carry controlled terms as bare strings — `page_categories`,
`pages[].category`, `lines[].categ`, `pages[].quality_band`, `entities[].type_teitok`,
`entities[].type_cnec`, `enrichment.items[].teater_category`. Each label set was declared in a
different repository in a different form, and nothing reconciled them. A new hub-canonical module,
[`templates/shared/atrium_vocab.py`](templates/shared/atrium_vocab.py), is now the single
declaration, published as SKOS. See [`skos_strategy.md`](skos_strategy.md).

* **`x-atrium-scheme`** — new annotation on each vocabulary-bearing field, naming its registry
  scheme. A JSON Schema annotation, so it is inert to validators and readable by tooling.
* **No `enum` was added, anywhere.** It is the obvious move and it is wrong here.
  `validate_document()` is a live output gate that *raises*, and `page-classification/utils.py`
  derives its label list from `sorted(os.listdir())` at run time — so an enum would convert a
  naming slip into a stalled pipeline. The registry's `validate_labels()` reports instead, matching
  the abstain-with-a-`NOTE` idiom §1a already uses for an unrecognised origin.
* **`page_categories.examples` corrected.** They were `{"1": "Text", "2": "Plate"}`; neither is a
  member of `model_registry.CATEGORIES`. The schema's own illustration of a controlled field used
  values the controlling code would never emit.
* **`lines[].categ` description corrected, and it is the substantive one.** It said `"Garbage"` and
  `"Inverted"` are load-bearing because `json_to_md.py`'s `DROP_CATEGORIES` filters them — true —
  and left the reader to infer that those are what the field carries. They are `digital-convert`'s
  labels. `alto-postprocess`, the *other* authorised originator, emits
  `Clear`/`Empty`/`Noisy`/`Non-text`/`Trash`, a **disjoint** set. So the filter matches nothing on
  the OCR/ALTO path: a `Trash` line reaches the model exactly like a `Clear` one. The description
  now states both sets and points at the defect (V-1) and its one-line fix rather than implying the
  field is already filtered. **The filter itself is unchanged** — correcting it changes what text
  the model reads, which is a behaviour decision with an owner, not a documentation fix.

`atrium_vocab.py` and `atrium_vocab.schema.json` join the hub-canonical set: `SHARED_FILES` in
`scripts/revendor_shared.sh`, two `diff -u` steps plus a `--selftest` step in
`para-drift.reusable.yml`, and the `[format] exclude` list in every repo's `ruff.toml` — without
that last one `ruff format` reflows the vendored copy to the local line length and para-drift fails,
which is the trap `force-exclude = true` was added for.

## Changelog — 2026-09-09 (issue #54: the freeze)

The WP3/T3.3 deliverable. `SCHEMA_VERSION` stays **`1.0`** — see *Why this is not a bump*
below, which is the load-bearing paragraph of this section. After it, the schema is a
compatibility obligation rather than a design surface: the next change to it is a `2.0` with a
migration, not another additive pass.

### What the top-level `required` was, and why it was wrong

```json
"required": ["schema_version", "doc_id"]
```

Two keys against seventeen declared properties. `validate_document()` is a live output gate in
five repos and a `SystemExit` gate in the hub's E2E, and the strongest statement it could make
about a record was *"it has a version and an id"*. A stage that ran, wrote nothing, and emitted
a two-key file passed every gate in the ecosystem — `finalize()` printed
`WARNING – <program> contributed no block to <doc_id>` and wrote the record anyway, and nothing
downstream distinguished that from a document that genuinely has no entities yet.

### What it is now

```json
"required": ["schema_version", "record_type", "doc_id", "provenance", "assembled"]
```

plus two assertions that could not be expressed as a flat list:

* **`anyOf` — a record must carry evidence that something was written into it.** Either
  `source`, or at least one entry in `assembled.blocks`. Nothing else changed about either.
* **`allOf` — stamp/payload coherence.** Every name in `assembled.blocks` must exist as a
  top-level property. Eleven `if`/`then` clauses: the nine content blocks plus `derived_from`
  and `regenerable`. A name this table has not been taught has no clause and passes, which is
  rule 6's spirit and the same abstain-rather-than-refuse idiom `ORIGIN_ORIGINATORS` uses.

The enumeration this rests on is not prose: `tests/test_document_required.py` carries every
record shape production writes, each annotated with the call site it was traced from, plus the
defect shapes the freeze refuses. It passes 18 cases against this schema and fails exactly five
against the previous one.

### Why the floor is exactly those five keys, and not six

`DocumentRecord.to_dict()` emits all five on **every** path, with no branch that can skip one:
`schema_version` and `record_type` are `setdefault` in `__init__`, `doc_id` is assigned there
unconditionally (and `__init__` raises on a falsy one), and `to_dict()` itself always assigns
`provenance` and always sets `assembled.had_baseline` / `assembled.note`.
`merge_document_records()` hardcodes all five at the end of its own build. So no record any tool
has ever written is newly rejected — only hand-built dicts are, which is the point.

`source` is **not** in the floor, and the reason is worth stating because it is the obvious
sixth candidate. Four of the five tools never call `set_source()` at all — `page-classification`,
`translator`, `nlp-enrich` and `llm-enrich` — and `page-classification` is stage 1 of the scanned
pipeline. Requiring `source` would refuse a legitimate rule-3 standalone run of most of the
ecosystem. For the same reason `source.sha256` and `source.origin` stay optional even when
`source` is present: `sha256` has exactly two writers (`page_split.py`, `digital_to_json.py`) and
`resolve_source_origin()` is allowed to return `None`.

### Why `assembled.blocks` alone was not enough — the branch that made `anyOf` necessary

The first draft of this change required `assembled.blocks` to be present and non-empty, on the
grounds that `_stamp()` runs only where a payload is written, so an empty stamp registry *is*
"contributed nothing". That would have broken the pipeline at stage 1.

`set_source()` deliberately does not call `_stamp()` — `source` is not a tool's block, it is the
first-writer handshake, and stamping it would put a `program`/`run_id`/`paradata_ref` on a
structural key that `RESERVED_KEYS` explicitly excludes from tool ownership. So
`alto-postprocess/page_split.py` — the originator, the first thing that touches a scanned
document — emits exactly `schema_version, record_type, doc_id, source, provenance, assembled`,
with **no `blocks` key at all**, and hands it to a hard gate (`document_hook.py`'s
`_validate_own_output()`). A blanket `blocks` requirement would have made the originator refuse
to emit its own first record.

The `anyOf` says the true thing instead: *`source` or a block*. `page_split`'s record satisfies
the first branch. Everything else satisfies the second. The only shape that satisfies neither is
a record with no origin information and no contribution — which is precisely what #54 asked to
make invalid.

`minProperties: 1` lives inside the `anyOf` branch rather than on `assembled.blocks` itself, so
that a fan-in merge of two source-only records — which legitimately carries `blocks: {}`, since
`merge_document_records()` always writes the key — still validates through the first branch.

### The one call site this newly refuses, and it is a defect

`atrium-alto-postprocess/classify_TEXT.py`'s `write_document_block()` call sits **outside** the
`if not df.empty` guard. An empty CSV therefore reaches `merge_blocks={"lines": []}`, which
passes the hook's `if not any([source, set_blocks, merge_blocks])` check (a dict with a key is
truthy) and then fails its own `if records:` check — so the `with` block runs, contributes
nothing, and writes a five-key record. In a real pipeline the baseline exists and its blocks pass
through, so this only bites a standalone run; but a standalone run is exactly what rule 3 exists
to support, and "wrote a record that says nothing" is not a supported outcome of it.

Fix at the call site (guard the hook call on `not df.empty`), not in the schema. The schema is
right to refuse it.

### Why this is not a `SCHEMA_VERSION` bump

Versioning rule 2 above bumps MAJOR for "renaming/removing a field, or changing block
ownership". None of that happens here: no property is renamed, none is removed, no ownership
moves, and — the test that actually matters — **every record any tool in the ecosystem has ever
written stays valid**, because the five floor keys are unconditional in `to_dict()` and the two
new assertions are satisfied by construction wherever `_stamp()` wrote the stamp.

That is the same distinction rule 2's Issue #18 amendment already draws: *widening write
authorisation is additive; re-attributing an already-written block would not be*. Here the
analogue is: **narrowing what a validator accepts is additive when the narrowed set still
contains everything the producers produce.** It stops being additive the moment a real producer
is excluded, and the way to know which case you are in is to enumerate the producers — which is
what the per-stage record table in `54.plan.md` does.

A bump would also be actively harmful. `SCHEMA_VERSION` is what `load_document()`'s MAJOR-refuse
guard reads: bumping to `2.0` would make every already-written `1.0` record refuse to load in
every updated tool, in exchange for a change that does not alter how a single one of them is
read. The migration mechanism exists for changes that need it; this is not one.

### Rejected alternatives, recorded so they are not relitigated

1. **Require every block (a flat seventeen-key `required`).** Rejected: it contradicts the
   accretion model outright. `assembled.note` literally says *"a block is absent until its tool
   has run"* — requiring all of them would make every intermediate record invalid and the only
   valid record the last one.
2. **Require a positive content block (`anyOf` over `pages`/`lines`/`entities`/…).** Rejected:
   `page_split`'s source-only record carries none, and each rule-3 standalone record carries
   exactly one, so the branch list would have to be all nine — at which point it says nothing
   the `assembled.blocks` branch does not say better, and it says it without the stamp that
   makes the claim auditable.
3. **Add `enum`s to the controlled-term fields while the schema is open.** Rejected for the
   reason already recorded under the 2026-09-08 pass: `validate_document()` raises, and
   `page-classification/utils.py` derives its label list from the filesystem at run time, so an
   enum turns a naming slip into a stalled pipeline. `atrium_vocab.validate_labels()` reports.
   (This freeze does, however, make the *drift* visible — see the fixture note below.)
4. **`minItems: 1` on `provenance.contributors`.** Rejected: the contributor append is gated on
   `if self._touched`, so the two records described above legitimately carry `[]`.
5. **Require `source.origin` whenever a positional block is present.** Deferred, not rejected —
   it would close a real §1a hole (a positional plane written by a run that never called
   `set_source()` escapes the originator check permanently), but it is a behaviour change to
   four production call sites, not a freeze. Tracked as a follow-up.

### Also recorded by this freeze

* **`forms` has no writer anywhere.** `BLOCK_OWNERS` assigns it to `llm-enrich`, the schema
  describes it in full, and no production code path in any of the six repos calls
  `set_block("forms")`. It stays in the schema as a reserved, specified block — a freeze is the
  right moment to say out loud that it is unimplemented rather than to discover it later from a
  consumer that expected it.
* **`fixtures/atrium_document.example.json` carries four controlled values the registry does not
  know**: `page_categories` `"Text"`/`"Plate"`, `lines[].categ` `"Text"`, and
  `enrichment.items[].teater_category` `"kostel"`. This is defect V-4 from `skos_strategy.md`
  §6 in its second home: that pass corrected the *schema's* `examples`, and the fixture — which
  is what a maintainer actually reads, and what `tests/test_fixture_schema.py` pins — kept the
  same wrong values. Nothing catches it today because the fixture test checks schema validity
  and the schema deliberately has no `enum`. Fix the fixture; do not add the enum.

### New: `atrium_rocrate.py` — the RO-Crate view

`docs/document_schema.md` has called this record "one FAIR, versioned JSON for search and
**catalogue export**" since it was written, and nothing had ever exported it. The DMP's WP3
standards column names RO-Crate. `templates/shared/atrium_rocrate.py` is the export, and it joins
the hub-canonical set (`SHARED_FILES`, a `diff -u` step and a `--selftest` step in
`para-drift.reusable.yml`, and a `[format] exclude` row in every repo's `ruff.toml`).

It **maps, it does not invent**. Every property comes from a field the record or its paradata
already carries, and a field that does not exist is omitted rather than guessed:

| RO-Crate                 | ATRIUM source                                                                                  |
|--------------------------|------------------------------------------------------------------------------------------------|
| root `license`           | `provenance.license_url` / `license` — already the most-restrictive union from `para_licenses` |
| root `author`            | the four ORCID `Person`s identical in every `CITATION.cff`                                     |
| root `hasPart`           | `derived_from` values, and **only** those                                                      |
| root `isBasedOn`         | `source`, as a contextual entity: no path, because originals are archive-managed               |
| root `about`             | every controlled term, as a `DefinedTerm` under `atrium_vocab.concept_uri()`                   |
| `CreateAction`           | one per `provenance.contributors[]` entry                                                      |
| `CreativeWork` per block | one per `assembled.blocks[…]` stamp — the accretion granularity, preserved                     |
| `SoftwareApplication`    | paradata `tool_version` / `repository` / `docker_image` / `runner_ref`                         |

**The reference-discipline rule, restated in RO-Crate terms.** `regenerable` entries are recipes
for files that do not exist, so they are contextual entities and never appear in `hasPart`. A
crate that lists a file it does not contain is invalid — which is the same failure the record's
"transient artifacts are never referenced" rule prevents one layer up. The module's `--selftest`
asserts it directly.

Two house rules it inherits deliberately: **stdlib only** (no RDF library, for the reason
`atrium_vocab.py` gives — a general-purpose serialiser emitting blank nodes or unordered graphs
fails a byte-comparison gate on every run), and **deterministic output** (`@graph` sorted by
`@id`, `sort_keys=True`, and `datePublished` derived from the record's own newest block stamp
rather than from the clock, so re-exporting an archived record reproduces the crate it shipped
with).

---

### Two edits elsewhere in this document

1. **"Schema `1.0` Context"** — replace the `**Contract:**` bullet's opening with a statement of
   the frozen assertions, so a reader meets them before the changelog:

   > **Contract:** every record carries `schema_version`, `record_type`, `doc_id`, `provenance`
   > and `assembled`; carries either `source` or at least one stamped block; and carries a
   > payload for every block its `assembled.blocks` names. Beyond that floor, blocks are written
   > by exactly one tool per document — for the positional blocks, *which* tool is fixed by
   > `source.origin` (see **Originators**, below).

2. **"Consumers to Update on Bumps"** — add two rows:

   > * `atrium_rocrate.py`, whose mapping table names the fields it reads
   > * `fixtures/atrium_document.example.json`, which `tests/test_fixture_schema.py` validates
   > * `tests/test_document_required.py`, which enumerates every record shape production writes —
   >   a change to `required` that reds a case there is a behaviour change to a shipped tool
