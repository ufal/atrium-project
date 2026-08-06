# 📄 ATRIUM Document Schema & Accretion Policy

This document defines the per-document aggregate record produced by `atrium_document.py` — the
**paradata pair**. Where [`paradata-schema.md`](paradata_schema.md) covers *how a run behaved*,
this covers *what we know about one document*: text, pages, entities and enrichment, gathered
across the pipeline into one FAIR, versioned JSON for search and catalogue export.

Template files: [`templates/shared/atrium_document.py`](templates/shared/atrium_document.py) ·
[`templates/shared/atrium_document.schema.json`](templates/shared/atrium_document.schema.json).
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
