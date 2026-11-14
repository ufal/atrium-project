# ATRIUM Document Schema & Accretion Policy

This document defines the per-document record produced by `atrium_document.py`
(`atrium/document-json`): *what we know about one document* — text, pages, lines, entities and
enrichment — gathered across the pipeline into one versioned JSON for search and catalogue export.
*How a run behaved* is the run's paradata ([`paradata_schema.md`](paradata_schema.md)) and its
RO-Crate ([`rocrate_export.md`](rocrate_export.md)), never the record.

Template files: [`templates/shared/atrium_document.py`](templates/shared/atrium_document.py) ·
[`templates/shared/atrium_document.schema.json`](templates/shared/atrium_document.schema.json).
Several of this record's fields carry **controlled terms**; which values are legal in each, and what
they mean, is [`skos_strategy.md`](skos_strategy.md) and the registry it describes.
Design discussion: [ufal/atrium-llm-enrich#13](https://github.com/ufal/atrium-llm-enrich/issues/13);
schema 2.0: [atrium-project#84](https://github.com/ufal/atrium-project/issues/84) and ARÚP's output
contract of 12 November 2026.

## Why accretion, not an aggregator

The tools are separate containers reached over their own APIs, and **no tool sees another tool's
outputs**. So the record is not assembled by a central service; it travels *with* the document.
Each tool takes the previous version of the JSON — if it is given one — and returns it with
**only its own block or fields** updated:

```
seed ──► [ocr-postprocess] ──► record ──► [page-classification] ──► [nlp-enrich] ──► [keyword-extract]
          pages/content/lines             pages[] category         entities, lemmas   enrichment, keywords
```

This keeps every tool independently runnable, makes updates granular (re-run one tool → one
block changes), and needs no shared volume or orchestrator.

## Schema `2.0` (doc-schema-v2, atrium-project#84)

**Status.** `SCHEMA_VERSION = "2.0"` on the hub's `test` branch. The tag `doc-schema-v2` is
cut only after the schema validator, the E2E checks (`e2e_assert.py --require-current-major`) and a
run through the assembled pipeline chain have passed (D12). Until then `test_schema_freeze.py` lists
MAJOR 2 in `PENDING_FREEZES` and skips its freeze checks with that reason. `doc-schema-v1` is not
moved; 1.x records stay readable (see [Reading 1.x records](#reading-1x-records)).

**Content only.** The record holds what is known about the document. It holds no run data, no
licence and no layout:

| Removed in 2.0                                                                  | Where it is now                                                                                              |
|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `provenance` (contributors, `license`, `license_url`, `license_basis`)          | the run's paradata `components` (facts only, no calculated licence) and its RO-Crate `CreateAction` (D1, D2) |
| `assembled` (block stamps, `had_baseline`)                                      | the paradata output entry: `record_fields`, the blocks and fields the run wrote (`DocumentRecord.written()`) |
| `derived_from`, `regenerable`                                                   | the paradata inputs and outputs, by AMČR distribution name and SHA-512                                       |
| `forms`, `tables`, `content.reading_order`, `lines[].group_id`, `lines[].style` | docproc (`atr/docproc-json`), the layout's one home (D26); `lines[].block` joins a line to it                |
| `pages[].text_layer`, `needs_ocr`, `needs_ocr_reason`, `ocr`                    | the route step's decision and docproc; a line says where its text came from (`text_source`)                  |
| `source.sha256`                                                                 | `source.sha512` only: one digest, of the original                                                            |
| the `Garbage` and `Inverted` line categories                                    | docproc line flags (`atrium_vocab.DECODE_FLAGS`): decode verdicts, not text quality (D18 rule 2)             |

The schema declares each removed name with `not: {}`, so a record that carries one fails validation
by name, and `DocumentRecord` refuses to write one: `add_derived_from()`, `add_regenerable()` and
`add_license_detail()` raise `RemovedInSchema2`, `set_source(sha256=…)` is refused.

**New or changed** (#84 §2):

| Field                               | Values                                                   | Meaning                                                                                                                                                                 |
|-------------------------------------|----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `source.origin`                     | `digital` · `atr` · `legacy`                             | how the text was obtained; **descriptive only**, it selects no writer (#84 §1)                                                                                          |
| `pages[].page_index`                | integer ≥ 1, **required**                                | the physical page, the join key with docproc `pageNumber` (H2); `page` stays the printed label                                                                          |
| `pages[].content_status`            | `text` · `empty`                                         | an `empty` page has no lines and no page score, and is counted apart in `quality_summary` (D29)                                                                         |
| `pages[].canvas`                    | `unit` `pt` (default) · `px`; `user_unit`, `pixel_ratio` | the unit of every box on the page (D28); `px` only for PCSS pages whose original cannot be matched; the two factor names are proposed by this implementation            |
| `lines[].line`                      | integer ≥ 1                                              | numbered from 1 on every page                                                                                                                                           |
| `lines[].block`                     | `p<page>-b<n>`, e.g. `p3-b7`                             | the docproc block the line belongs to (D26)                                                                                                                             |
| `lines[].text_source`               | `text-layer` · `atr` · `legacy`                          | where this line's text came from (D25); a mixed document has more than one                                                                                              |
| `lines[].bbox_precision`            | `measured` · `derived` · `absent`                        | a box the producer measured, one derived from the containing block, or none; required with `bbox` (D16)                                                                 |
| `lines[].categ`                     | `Clear` · `Noisy` · `Trash` · `Non-text` · `Empty`       | the five text-quality categories of the line-quality model                                                                                                              |
| `lines[].unit`                      | `block`                                                  | a row holding a whole docproc block scored as one unit (D18 rule 5): scored, but kept out of the page score and `by_categ`; the name is proposed by this implementation |
| `quality_summary.pages.empty`       | integer                                                  | the empty pages, counted apart                                                                                                                                          |
| `quality_summary.lines.block_units` | integer                                                  | the `unit: block` rows, counted apart from `by_categ` (D18 rule 5)                                                                                                      |

`entities`, `enrichment`, `keywords`, `page_categories` and `quality_summary` keep their 1.x shape.
`translations` and `entities[].translation_en` stay declared and **reserved**: the pilot translates
only the record-level metadata, into its own distribution (`metadata-en`), never the full text.

The top level requires `schema_version`, `record_type` and `doc_id`, plus `source` or at least one
content block, so a standalone run (rule 3) without `source` stays valid while an empty shell does
not.

## The accretion contract (six rules)

1. **Baseline in, record out.** Tools take an optional `--document-json` and write
   `--document-json-out` (default `<doc_id>.document.json`); services accept and return an
   optional `document_json` part. **`doc_id` travels WITH the baseline**: the first writer derives
   it once with `canonical_doc_id()` (or takes it from the AMČR seed), and every stage after it
   inherits that value — `DocumentRecord` keeps the baseline's `doc_id` and reports (never
   refuses) a caller that passed a different one. A stage's input is usually *not* the original
   document, so a stage that keys its record off its own filename re-keys the document and
   orphans everything already in the record.
2. **Own block only.** A tool writes its own block(s) and fields; every other block is
   deep-copied through **unchanged**. This invariant is what makes the record safe to pass around.
3. **No baseline → own part only** (plus `doc_id`/`schema_version`, and `source` if it is the
   first writer). Standalone runs keep working. This is the only case in which a tool's own
   `canonical_doc_id()` decides the key: with no baseline there is no document context to inherit.
4. **What a run wrote is paradata.** `DocumentRecord.written()` returns `{block: [fields]}` for
   this run; the run's paradata name the record output with it (`record_fields`), and the RO-Crate
   carries it as `recordFields` on the action's result. Nothing is stamped into the record (D1).
5. **No licence.** The record carries no licence, calculated or otherwise (D2): the rights in an
   output depend on the source document and are stated only by whoever holds them. The paradata
   list each component with its own terms, as facts.
6. **Unknown or newer blocks are preserved** verbatim; a newer MAJOR `schema_version` is refused.
   An older MAJOR is migrated on read (`load_document()`, `migrate_document()`, and a dict
   baseline in `DocumentRecord`). A baseline that does not validate is still accreted onto,
   except where a tool must add rows: a list block it merges into (`pages`, `lines`,
   `entities`) that is not a list of objects raises `InvalidRecordError` before anything is
   written, and a service answers it with 422 `invalid_record` (#72).

## Reading 1.x records

Every reader migrates a 1.x record to 2.0 (`_migrate_1_to_2()`); content survives, run data,
licence and layout do not:

* the removed blocks and fields are dropped;
* `source.origin` maps by prefix: `digital-born…`, `docx`, `pdf` → `digital`; `ABBYY…`, `alto…` →
  `legacy`; `ocr:…`, `vlm:…` → `atr`; anything else is dropped. Each line's `text_source` follows
  from it;
* a page whose lines were numbered from 0 (1.x digital-convert) is renumbered from 1, and the
  entities on it follow;
* a `Garbage` or `Inverted` `categ` is dropped with its `quality_score`;
* a missing `page_index` is the numeric page label, else the row's position; a missing
  `content_status` follows from whether the page has lines (when the record has `lines`), and an
  empty page loses its page score;
* a canvas with no unit gets 1.x's default, `px`; a line with a box gets `bbox_precision:
  measured`;
* `quality_summary` is recomputed, since it reads the rows rewritten above.

A seed is identity only, the same in every major, so only its `schema_version` moves. The E2E gate
reads every stage record through the migration, so images older than #84 keep passing until they
adopt 2.0; `--require-current-major` refuses any record not written at 2.x.

## The AMČR seed

In the AMČR pilot the archive writes the record before the first stage (atrium-project#71). That
record is a **seed**: the document's identity and nothing a tool writes.

| Key                 | Value                                                 | Required |
|---------------------|-------------------------------------------------------|----------|
| `doc_id`            | the AMČR file id                                      | yes      |
| `source.sha512`     | the Fedora digest of the original, lower-case hex     | yes      |
| `source.filename`   | the original's file name in the archive               | yes      |
| `source.media_type` | the original's media type, as the archive detected it | yes      |
| `schema_version`    | any `MAJOR.MINOR`; best left out                      | no       |
| `record_type`       | `"atrium-document"`                                   | no       |

Nothing else, and in particular **no `source.origin`**: it describes what the record builder found
in the original. A seed is the same in every major, so it carries no `schema_version`
(`tools/e2e/make_seed.py` writes none) and a 1.x tool and a 2.0 tool read the same seed.
`python atrium_document.py seed-schema` prints the seed's JSON Schema; it is built from this
schema's own subschemas, so the two cannot drift. A worked example is
[`fixtures/atrium_document.seed.example.json`](../fixtures/atrium_document.seed.example.json).

**A seed is valid input; what a tool emits is a full record.** Every tool's gate on the record it
was HANDED calls `validate_baseline()`, which checks a seed against the seed profile (`is_seed()`,
`validate_seed()`) and anything else in full, after migration. The gate on the record a tool
WRITES stays `validate_document()`.

**The keep rule.** `doc_id`, `sha512`, the file name and the media type are never changed:

* `doc_id` is inherited (accretion rule 1): a tool that derives another id from the file it reads
  keeps the seed's and says so in a NOTE;
* the identity fields are first-writer-wins. A tool reading a derived file or a temporary upload
  sees another file name and media type than the archive's; that difference is reported as a NOTE
  and never refused, even by a strict writer. A different `sha512` is a conflict;
* the described fields (`origin`, `language`, `page_count`) are the record builder's, and no later
  stage changes them.

The seeded path is the integration baseline of the pilot: the E2E smokes start from a seed whose
`doc_id` matches no file name, and `e2e_assert.py --seed` fails any stage that changes the four
values or rewrites a described field.

## References and coordinates

The record names no file: the original is `source` (keyed by `doc_id` and `sha512`; originals are
archive-managed), and every other input and output of a run is named in that run's paradata by
its AMČR distribution name and SHA-512. A temporary file, a page image or a rendering is never
named anywhere (contract §6).

Every `bbox` is in one coordinate space: **origin top-left, y increasing downwards, in the unit
named by that page's `pages[].canvas.unit`** — `pt` (1/72 inch × `user_unit`) by default, `px`
only for PCSS pages whose original cannot be matched (D28). A born-digital PDF writer converts
from PDF user space, which puts the origin bottom-left (with pdfplumber, use `top`/`bottom`,
never `y0`/`y1`). `bbox_precision` says whether a line's box was measured or derived from its
block.

The TEITOK references are **local ids inside that document's TEITOK file** (nlp-enrich), in
TEITOK's own scheme: `pages[].teitok_surface` = the page's `<surface id>` (`facs-1`),
`entities[].teitok_ref` = the entity's `<name id>` (`n-5`), `lines[].teitok_ref` = a sentence
`<s id>` (`s-3`). They are not globally unique, so they are always read together with `doc_id`
and the TEITOK distribution the same run wrote. `pages[].teitok_surface` is set only for pages
that have a `<surface>`. `entities[].page` is the page of the entity's first token, the same page
as the `<pb>` in force where its `<name>` starts (nlp-enrich#38). The E2E lane checks that every
reference resolves to the right element and that the pages agree
(`tools/e2e/e2e_assert.py --teitok-dir`).

The other direction — the record's facts inside the TEITOK file — is **off by default**: page
classification and line quality stay "only in the record" (the AMČR storage contract; #24's
three-format decision). nlp-enrich's opt-in projection (atrium-project#70 item 2) writes the page
categories and keyword-extract's categories and keywords into the TEITOK header and `<pb>`
attributes; it never writes line quality, and it changes no block owner.

## Block ownership

One owner per block. Blocks that several tools contribute to are split **by field**
(`BLOCK_FIELD_OWNERS`), so no field is ever co-mutated — use `merge_block()` for those and
`set_block()` for blocks you own outright.

**One writer of the positional blocks (D20).** `pages`, `content` and `lines` have one writer, the
**record builder**, `ocr-postprocess` (`RECORD_BUILDER`), on every route: it builds them from
docproc, whether the text came from a born-digital text layer, the ATR or PCSS ALTO. It also writes
the described `source` fields and, as the owner of the line-quality model (D18), every line and
page score. digital-convert writes docproc and no record block. So 1.x's originator arbitration
(`source.origin` selecting the writer, the per-page OCR hand-off, the scoring co-contribution) has
no role and is gone.

| Tool                | Writes                                                                                                                                                                                                                                         |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ocr-postprocess ¹   | `pages[]` *page, canvas, content_status, quality_score, quality_band* · `content` · `lines[]` *text, bbox, block, text_source, bbox_precision, unit, categ, quality_score, lang* · `quality_summary` · `source` *language, page_count, origin* |
| page-classification | `page_categories` · `pages[]` *category, category_confidence*                                                                                                                                                                                  |
| nlp-enrich          | `entities[]` · `lines[]` *lemma, upos, feats, teitok_ref* · `pages[]` *teitok_surface*                                                                                                                                                         |
| keyword-extract ¹   | `enrichment` · `keywords` · `entities[]` *pid*                                                                                                                                                                                                 |
| translator          | `translations` · `entities[]` *translation_en* — **reserved**: granted, written by no tool in the pilot                                                                                                                                        |
| digital-convert     | — (writes docproc, `atr/docproc-json`)                                                                                                                                                                                                         |

¹ The successor of `alto-postprocess` and of `llm-enrich` respectively, since the repository moves of
2026-10-01. Each predecessor id resolves to it — see [Program successors](#program-successors-2026-10-01).

A list block's rows are keyed by `BLOCK_KEY_FIELDS`: pages by `page_index`, lines by `page` and
`line`, entities by `page`, `line` and `char_span`. A page-classification run with no baseline
writes `pages[]` rows keyed by `page_index`; the record builder adds the `page` label.

`quality_score` is one axis — **text trustworthiness, 0–1** — written by the one line-quality
model for every line, whatever its `text_source`. Consumers that filter on it are filtering the
same thing on every route: *do not show this line to the model*.

**The two read-outs of atrium-project#73.**

* `keywords` (keyword-extract): the statistical keywords of the document (`document`) and of each
  page (`pages[]`, keyed by the `lines[].page` label), every one with its `method`, `score` and
  `rank`. One run writes one method's lists, and a re-run replaces the block. The controlled
  keywords stay in `enrichment`; the two kinds are never merged into one list.
* `quality_summary` (the record builder): `atrium_document.quality_summary(record)` written
  whenever it writes pages and lines — `pages` {`total`, `empty`, `scored`, `mean`, `median`,
  `min`, `max`} of `quality_score`, and `lines` {`total`, `by_categ`}. Numbers only: no band, no
  threshold, and no tool reads it to route or refuse a document.

## Usage

Alongside the tool's `ParadataLogger`:

```python
from atrium_document import DocumentRecord

with DocumentRecord.open(doc_id, "keyword-extract", baseline=args.document_json) as doc:
    doc.set_block("enrichment", {"items": items})
logger.add_output("atrium/document-json", path=doc_path, record_fields=doc.written())
```

`baseline` may be None (rule 3), an AMČR seed, or a 1.x record (migrated). `run_id`, `run_uuid`
and `paradata_ref` are still accepted so a caller need not change at once; none is written into
the record. Field-level contribution into a shared block:

```python
doc.merge_block("lines", rows)  # writes only this program's declared fields
```

Shell stages use the CLI shim:

```bash
python atrium_document.py set-block --doc-id "$DOC" --program ocr-postprocess \
    --block pages --payload pages.json --baseline "$DOC.document.json" --out "$DOC.document.json" \
    --written written.json
python atrium_document.py migrate --path old.document.json
```

## Versioning Rules

1. **Additive Updates:** adding an optional field or a new block requires **no bump** — rule 6
   means existing tools pass unknown keys through untouched.
2. **Breaking Changes:** renaming/removing a field, or changing block ownership, bumps
   `SCHEMA_VERSION` to the next major. Schema 2.0 is such a bump.
3. **Migration Mechanics:** a bump mandates a sequential `_migrate_X_to_Y()` and a branch in
   `migrate_document()`, exactly as in `atrium_paradata.py`.

## Consumers to Update on Bumps

* `merge_document_records()` and the `_cli()` shim in `atrium_document.py`
* `atrium_document.schema.json` (kept in step with the module — one is the contract, one the validator)
* Every tool's block writer, and any search/presentation layer indexing the record
* `tools/e2e/e2e_assert.py`, the fixtures and this document

## Distribution

`atrium_document.py` and `atrium_document.schema.json` are **hub-canonical**: they live here in
`docs/templates/shared/` and are copied byte-identical into the tool repos, enforced by
`para-drift.reusable.yml` — the same guarantee covering `atrium_paradata.py` and
`para_licenses.py`. The frozen copy `atrium_document.schema.doc-schema-v1.json` and
`test_schema_freeze.py` travel with them; see below. Each tool adopts 2.0 in its own repository:
`scripts/revendor_shared.sh --repo atrium-<tool>` copies the files, then the tool's callers change.

## Freeze & conformance

Schema `1.0` is frozen as the tag **`doc-schema-v1`** (atrium-project#54). From that tag on, the
schema is a compatibility obligation, not a design surface.

**MAJOR 2 is pending.** Schema `2.0` has taken the MAJOR bump's first step (below): the module,
the schema and `_migrate_1_to_2()`. Its tag `doc-schema-v2` is cut only after the proof gate (D12):
the validator, the E2E checks and a complete run through the assembled pipeline chain. Until then
`test_schema_freeze.py` keeps MAJOR 2 in `PENDING_FREEZES`: the checks against the current major's
freeze skip with that reason, its register (`POST_FREEZE_CHANGES_BY_MAJOR[2]`) is empty, and the v1
frozen copy is still checked byte for byte. The 1.x register below stays as the record of 1.x.

### Three references, three jobs

| Reference               | What it names                                                                    | Moves?                                          |
|-------------------------|----------------------------------------------------------------------------------|-------------------------------------------------|
| `doc-schema-v1`         | the frozen contract for schema MAJOR 1                                           | **never**; it is not moved, deleted or re-cut   |
| `v1`                    | the current canonical shared files, which the tools vendor and para-drift checks | yes, on every hub change the tools must pick up |
| `schema_version: "2.0"` | what every record carries, and what `load_document()`'s MAJOR guard reads        | only on a MAJOR bump                            |

`v1` is the reusable-workflow tag and says nothing about the schema by itself; `doc-schema-v1` says
nothing about workflows. Neither replaces the other.

The frozen file, immutably:

* release: <https://github.com/ufal/atrium-project/releases/tag/doc-schema-v1>
* file: <https://github.com/ufal/atrium-project/blob/doc-schema-v1/docs/templates/shared/atrium_document.schema.json>
* commit `544298bb5817fe57d8521579700332184b86d778`, schema git blob
  `1945c43ea5a4b6e370022fba75fe1d835b32b34c`

### The frozen copy, and the check that travels with it

Two shared files carry the freeze into every repository, vendored by `scripts/revendor_shared.sh`
like the rest of `docs/templates/shared/`:

| Shared file                                 | In a tool repo                                    | What it is                                                                         |
|---------------------------------------------|---------------------------------------------------|------------------------------------------------------------------------------------|
| `atrium_document.schema.doc-schema-v1.json` | beside `atrium_document.schema.json`, at the root | the schema exactly as `doc-schema-v1` has it; never edited, only re-vendored       |
| `test_schema_freeze.py`                     | `tests/test_schema_freeze.py`                     | checks that repository's own `atrium_document.schema.json` against the frozen copy |

`test_schema_freeze.py` is stdlib-only, so it runs in every tool repo's ordinary test lane. It
checks that:

* the frozen copy is byte-for-byte the file `doc-schema-v1` names, by git blob id, so it needs no
  git and no tags;
* nothing declared at the freeze was removed or renamed;
* every constraining difference since the freeze is registered in its `POST_FREEZE_CHANGES`,
  pinned to the node it adds; descriptions, `$comment`s and examples are free.

What only the hub can check is [`tests/test_schema_freeze_records.py`](../tests/test_schema_freeze_records.py):

* the tag itself has not moved, wherever it is present (skipped in CI's tagless checkout);
* every register entry has its `## Changelog — <date>` section here;
* every record shape the tools write (`tests/test_document_required.py`'s `VALID_SHAPES`, and the
  committed example) validates under **both** the frozen and the current schema, and the floor's
  defect shapes are refused by both.

### What conforming means

A repository implements `atrium_document` 1.0 when its own copy of `test_schema_freeze.py` passes:
its schema keeps everything the freeze declared and differs from it only by registered, additive
changes. para-drift adds that the schema, the frozen copy and the test are all byte-identical to
hub `v1`, and the hub's records test that those registered changes still admit every record the
tools write.

Until `doc-schema-v2` is cut, a repository implements `atrium_document` 2.0 when it carries the
re-vendored shared files, its own tests pass, and the records it writes pass the E2E lane with
`--require-current-major`, natively and not only after migration.

Each tool repo's README (a *Document record schema* subsection under its paradata section) and its
`CITATION.cff` (a `references:` entry of type `standard`) name `doc-schema-v1` and its commit, so
the baseline is visible from every repository without reading the hub.

### Changing the schema after the freeze

**One freeze tag per MAJOR.** An additive change does not cut a tag and does not bump
`SCHEMA_VERSION`; `doc-schema-v1` stays the reference. What makes a change additive is versioning
rule 1 (a new optional field or block) and #54's rule for narrowing (a validator may accept less
only while it still accepts everything the producers produce). An additive change lands in one
hub commit carrying all of:

1. the schema edit;
2. its `POST_FREEZE_CHANGES` entry in `docs/templates/shared/test_schema_freeze.py` (pointer, the
   node as it now is, issue, changelog date);
3. a `## Changelog — <date>` section in this document;
4. the producer shapes it has to keep admitting, in `tests/test_document_required.py`.

Then the usual order ([`docker_gha.md`](docker_gha.md), "The procedure"): land the hub commit, move
`v1` to it, then one commit per tool repo with the copies (`scripts/revendor_shared.sh`) and the pins
(`scripts/pin_hub_reusables.py`).

**Removing or renaming a declared field, or re-attributing a written block, is a MAJOR bump**
(rule 2). The test has no register entry for a removal on purpose. The order:

1. `_migrate_1_to_2()`, its branch in `migrate_document()`, and `SCHEMA_VERSION = "2.0"`, with
   MAJOR 2 in `PENDING_FREEZES` (done for atrium-project#84);
2. cut `doc-schema-v2` on the hub commit that carries them, **only after the proof gate**: the
   validator, the E2E checks with `--require-current-major`, and a complete run through the
   assembled chain (D12). Remove MAJOR 2 from `PENDING_FREEZES` in the same commit;
3. add `atrium_document.schema.doc-schema-v2.json` (the file as that tag has it) to
   `docs/templates/shared/` with its `MANIFEST.json` row, add `FREEZES[2]` to
   `test_schema_freeze.py`, and start its `POST_FREEZE_CHANGES` empty;
4. move `v1` to that hub commit, then one commit per tool repo with the copies
   (`scripts/revendor_shared.sh`) and the pins (`scripts/pin_hub_reusables.py`);
5. update the tool repos' README and `CITATION.cff` references to the new tag.

`doc-schema-v1` and its frozen copy stay: `1.0` records already written still exist, and
`load_document()` migrates them on read.

**A change of meaning needs AMČR's agreement**, whatever its size in the schema. The record is the
exchange contract with AMČR, so a change to what a field, a block, the paradata or the RO-Crate
asserts (for example, which licence or rights statement a record carries) is class (c) in
[`shared_components.md`](shared_components.md): reviewed by every affected tool, run end to end, and
merged only after AMČR has agreed on the change's issue. An additive field that only adds
information is class (b) and follows the steps above.

### Checking it yourself

```bash
git fetch --tags
git rev-parse doc-schema-v1                                                     # 544298bb…
git rev-parse doc-schema-v1:docs/templates/shared/atrium_document.schema.json   # 1945c43e…
git diff doc-schema-v1 -- docs/templates/shared/atrium_document.schema.json     # every change since
python -m pytest tests/test_schema_freeze_records.py -v                         # hub, with jsonschema
(cd docs/templates/shared && python -m pytest test_schema_freeze.py -v)         # the vendored check
scripts/revendor_shared.sh --check                                              # every tool repo's copies
```

In a tool repository, `python -m pytest tests/test_schema_freeze.py` runs the same check against
that repository's own copy.

### Post-freeze register

| Pointer                                                                            | Change                                                                        | Issue                     | Changelog                                                                                               |
|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|---------------------------|---------------------------------------------------------------------------------------------------------|
| `/properties/lines/items/properties/style/properties/region`                       | added: closed enum `page_header` / `page_footer` / `footnote`; absent = body  | ufal/atrium-llm-enrich#18 | [2026-09-25](#changelog--2026-09-25-llm-enrich18-linesstyleregion-cdla-permissive-20)                   |
| `/properties/source/properties/sha512`                                             | added: optional, `^[a-f0-9]{128}$`, the archive's digest of the original      | ufal/atrium-project#71    | [2026-10-01](#changelog--2026-10-01-71-the-amčr-seed-sourcesha512-run_uuid)                             |
| `/properties/provenance/properties/contributors/items/properties/run_uuid`         | added: optional, `urn:uuid:` + a lower-case UUID                              | ufal/atrium-project#71    | [2026-10-01](#changelog--2026-10-01-71-the-amčr-seed-sourcesha512-run_uuid)                             |
| `/properties/assembled/properties/blocks/additionalProperties/properties/run_uuid` | added: optional, the same pattern                                             | ufal/atrium-project#71    | [2026-10-01](#changelog--2026-10-01-71-the-amčr-seed-sourcesha512-run_uuid)                             |
| `/properties/pages/items/properties/text_layer`                                    | added: optional, closed enum `digital` / `garbled` / `ocr` / `none` / `blank` | ufal/atrium-project#71    | [2026-10-05](#changelog--2026-10-05-w4-the-ocr-hand-off-per-page-pagestext_layer)                       |
| `/properties/keywords`                                                             | added: optional block, statistical keywords per document and per page         | ufal/atrium-project#73    | [2026-10-09](#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable)               |
| `/$defs/statistical_keyword`                                                       | added: `keyword`, `method`, `score`, `rank`, all required                     | ufal/atrium-project#73    | [2026-10-09](#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable)               |
| `/properties/quality_summary`                                                      | added: optional block, page-score statistics and line counts per `categ`      | ufal/atrium-project#73    | [2026-10-09](#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable)               |
| `/properties/enrichment/properties/items/items/properties/teater_category_ids`     | added: optional `[{source, id}]`, the AMČR and TEATER records of the label    | ufal/atrium-project#51    | [2026-10-13](#changelog--2026-10-13-51-teater_category_ids-declared-the-crate-stops-minting-theme-uris) |
| `/allOf/12`                                                                        | added: a stamped `keywords` must be present                                   | ufal/atrium-project#73    | [2026-10-09](#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable)               |
| `/allOf/13`                                                                        | added: a stamped `quality_summary` must be present                            | ufal/atrium-project#73    | [2026-10-09](#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable)               |
| `/properties/provenance/properties/license_basis`                                  | added: optional, closed enum `calculated`                                     | ufal/atrium-project#6     | [2026-11-04](#changelog--2026-11-04-6-license_basis-the-crate-root-asserts-no-licence)                  |

Not registered, because it does not constrain: the `lines[].style` description correction of the
same pass.

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
> change is not landed until all six vendored copies are updated and each tool's pin is moved.
> Use `scripts/revendor_shared.sh` and `scripts/pin_hub_reusables.py`, and remember the check
> reads the hub side at each caller's `hub-ref` (its pinned commit), not at `v1` or the branch you
> merged to.

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
  derives its label list from its training tree's sub-directory names at run time — so an enum would convert a
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
  *Update 2026-09-25:* the owner took it — `DROP_CATEGORIES` now filters on
  `atrium_vocab.UNTRUSTWORTHY_LINE_CATEGORIES` (Garbage, Inverted, Trash), and the `categ` description
  says so (V-1 fixed, atrium-alto-postprocess#31).

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
what the per-stage record table in the plan for issue #54 does.

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
  **Fixed 2026-10-19:** the pages are `TEXT`/`PHOTO` and the line `Clear`, and
  `test_fixture_controlled_values_are_registry_members` keeps the fixture's page categories,
  quality bands, line categories and entity types inside `atrium_vocab`'s registry. `kostel`
  was never wrong: `teater_category` holds the vocabulary's own label (the schema's description
  uses it as the example), not a registry value.

### New: `atrium_rocrate.py` — the RO-Crate view

`docs/document_schema.md` has called this record "one FAIR, versioned JSON for search and
**catalogue export**" since it was written, and nothing had ever exported it. The DMP's WP3
standards column names RO-Crate. `templates/shared/atrium_rocrate.py` is the export, and it joins
the hub-canonical set (`SHARED_FILES`, a `diff -u` step and a `--selftest` step in
`para-drift.reusable.yml`, and a `[format] exclude` row in every repo's `ruff.toml`).

It **maps, it does not invent**. Every property comes from a field the record or its paradata
already carries, and a field that does not exist is omitted rather than guessed:

| RO-Crate                 | ATRIUM source                                                                                                                              |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| root `license`           | `#no-licence-asserted`, which asserts nothing (#6, 2026-11-04); the calculated `provenance.license` is not exported                        |
| tool `creator`           | the ORCID `Person`s of every `CITATION.cff` (`atrium_rocrate.AUTHORS`; root `author` until #71)                                            |
| root `hasPart`           | `derived_from` values, and **only** those                                                                                                  |
| root `isBasedOn`         | `source`, as a contextual entity: no path, because originals are archive-managed                                                           |
| root `about`             | every controlled term, as a `DefinedTerm` under `atrium_vocab.concept_uri()`                                                               |
| `CreateAction`           | one per `provenance.contributors[]` entry                                                                                                  |
| `CreativeWork` per block | one per `assembled.blocks[…]` stamp — the accretion granularity, preserved                                                                 |
| `SoftwareApplication`    | paradata `tool_version` / `repository` / `docker_image` / `runner_ref`                                                                     |

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

## Changelog — 2026-09-25 (llm-enrich#18: `lines[].style.region`, CDLA-Permissive-2.0)

atrium-llm-enrich#18 (the explicit PDF/DOCX → JSON converter, on llm-enrich `test` @ `c3575f5`)
started writing one key the schema did not declare, and running one component whose licence
`para_licenses.py` did not rank. This pass declares the first and ranks the second. **No
`SCHEMA_VERSION` bump.**

It is the **first change after the freeze tag** `doc-schema-v1` (`544298b`, cut 2026-09-25). The
tag keeps naming the schema as frozen, and stays correct for every record: each one written
before or after this pass — including every llm-enrich record that already carries `region` —
validates against both. Since 2026-09-26 that is checked rather than stated:
the hub's `tests/test_schema_freeze_records.py` validates every producer shape against both
schemas, and the vendored `test_schema_freeze.py` carries `region` as the first entry of its
post-freeze register (see [Freeze & conformance](#freeze--conformance)).

### `lines[].style.region` — declared, as a closed enum

| Value         | The line is…                            | Written from                                                                   |
|---------------|-----------------------------------------|--------------------------------------------------------------------------------|
| `page_header` | the page's running header               | DOCX header parts · PDF lines repeating in the top margin · Docling's label    |
| `page_footer` | the page's running footer               | DOCX footer parts · PDF lines repeating in the bottom margin · Docling's label |
| `footnote`    | a footnote or endnote                   | DOCX footnote/endnote parts · Docling's label                                  |
| *(absent)*    | body text — every line on the ALTO path | —                                                                              |

**Consumer contract.** `api_util/json_to_md.py` renders each page as header, body, footnotes,
footer: the header and footer inside the `HEADER_START`/`FOOTER_START` cues, footnotes as `[^n]:`
definitions. `digital_to_json.py` keeps header and footer lines out of `content.text`, so a
running header is not repeated into the text on every page. A misspelled value would undo both
silently — the line would render as body text and reach `content.text` — which is why the value
set is closed.

**Why this is additive.** Versioning rule 1 covers the new optional key. The enum also *narrows*
what the validator accepts, and #54's rule above applies: that is additive when the narrowed set
still contains everything the producers produce. There is one producer, `digital-convert`, and
its three values are module constants (`api_util/digital_ir.py` `REGIONS`). The enumeration is
executable: `tests/test_document_required.py` gains the DOCX record shape with the layout cues
(positive) and `test_style_region_is_a_closed_enum` (negative: `"sidebar"`, `"header"`,
`"Page_Header"` are refused).

**Why an enum here, when the freeze rejected enums on controlled-term fields** (rejected
alternative 3 above). That rejection was about fields whose label sets come from data at run
time and have several writers — `page_categories` is whatever folders page-classification finds
— so an enum turns a naming slip into a stalled pipeline. `region` is the opposite case: one
writer, a fixed set in code, and a writer that validates its own record before writing it
(`digital_to_json.py` `_gate()`, run on every generated fixture by llm-enrich's tests). A slip
turns llm-enrich's CI red; it cannot reach a pipeline. That puts `region` on the same footing as
`pages[].quality_band` and `regenerable.*.detail`, the schema's other closed enums. It is
not a SKOS scheme: it records a position on the page, not a descriptive term, so nothing is
added to `atrium_vocab.py`.

**No ownership change.** `style` was already granted to `digital-convert` alone
(`BLOCK_FIELD_OWNERS`); a key inside a granted object is not a new grant, so the ownership table
above is unchanged.

**Also corrected in the schema:** the `style` description said heading-ness "is already carried
by categ". It never was — `digital-convert`'s `categ` set is `Garbage`/`Inverted` — and it is
`style.heading_level` that carries it.

### `para_licenses.py` — CDLA-Permissive-2.0 ranked 1

The converter's opt-in heavy engine (`--engine docling`) runs Docling's TableFormer weights,
licensed CDLA-Permissive-2.0. The licence places no terms on *Results* (the output of a
computation over the data), so it ranks with MIT and Apache-2.0. Unranked, it resolved as
**unknown**, which `resolve_effective_license()` treats as maximally restrictive *in its terms
too* — so every `--engine docling` record would have claimed non-commercial and share-alike. The
light engine (pdfplumber, pypdfium2, python-docx) was never affected. Pinned in
`test_para_licenses.py` (`test_cdla_permissive_model_weights_stay_permissive`).

### Also in this pass

* The `quality_score` paragraph under **Block ownership** described the digital-born derivation
  as a vowel/consonant ratio and a dictionary hit-rate. That was never built; the paragraph now
  says what `decode_sanity()` computes.
* `tools/e2e/e2e_assert.py --expect-layout`, and three new cases in `e2e-digital-smoke.yml`
  (`rich.docx`, `two_column.pdf`, and `ocr_layer.pdf`, which must be refused with exit 3). The
  cases turn themselves on only when both the fixture generator and the image carry #18, so the
  nightly on `:latest` (v0.7.0) skips them with a notice instead of failing.
* **Distribution:** the schema, `para_licenses.py` and `test_para_licenses.py` are hub-canonical.
  `scripts/revendor_shared.sh` copies them into the five tool repos, and `v1` has to move
  before `para-drift` compares against them.

## Changelog — 2026-09-26 (#54: the freeze made traceable)

The tag `doc-schema-v1` existed, but nothing outside this document named it, and no repository
could show that the schema it carries still honoured it. This pass adds the check, vendored into
every repository, and the references. **No schema change and no `SCHEMA_VERSION` bump. Two new
shared files, so the usual re-vendor and `v1` move follow.**

* **[Freeze & conformance](#freeze--conformance)**, above: what `doc-schema-v1`, `v1` and
  `schema_version` each name; what a repository must satisfy to implement 1.0; the rule for
  changes after the freeze (one tag per MAJOR, additive changes registered); the MAJOR procedure.
* **Shared, vendored by `scripts/revendor_shared.sh` (MANIFEST 17 → 19 files):**
  * `atrium_document.schema.doc-schema-v1.json`: the schema exactly as the tag has it, git blob
    `1945c43e…`, vendored beside `atrium_document.schema.json`;
  * `test_schema_freeze.py` → `tests/test_schema_freeze.py`: each repository's own schema against
    the frozen copy (blob pin, no removals, the post-freeze register). Stdlib-only.
  * `docs/templates/ruff.toml` and the five tool repos' `ruff.toml` exclude the test from
    formatting, like every vendored `.py`; page-classification's and the template's stated
    count move to 19.
* **Hub-only: `tests/test_schema_freeze_records.py`**: the live tag, the changelog sections, and
  every producer shape under both schemas.
* **Verified to fail on each defect it exists for:** a byte changed in the frozen copy, a frozen
  property renamed, a constraint edited without a register entry, the registered `region` enum
  widened, a register entry whose changelog section is missing, `SCHEMA_VERSION` moved to `2.0`
  with no freeze recorded, a moved tag (in a clone that carries it), and a narrowing that excludes
  a producer's value. A description-only edit passes.
* **References in every repository.** Each tool repo's README gains a *Document record schema*
  subsection naming `doc-schema-v1` and its commit, and its `CITATION.cff` a `references:` entry
  of type `standard`; the column-0 `version:` that `check_version.py` reads is untouched. The hub
  gains a `CITATION.cff`: the 2026-09-16 pass recorded one (F6), but it is not in the tree.
* `docs_site`: the schemas page's version policy and the document-contract page link the tag;
  the architecture page's shared-file table gains the two files, and the counts there and on the
  contributing and SKOS pages move to 19.

## Changelog — 2026-09-30 (#70: `translation_en` reserved, detail profiles described)

**Descriptions only: no constraint changes, no register entry, no `SCHEMA_VERSION` bump.** Two
canonical files change (`atrium_document.schema.json`, `atrium_document.py`), so the re-vendor
and the `v1` move follow, hub first (para-drift diffs every tool repo against the hub at `v1`).

* **`entities[].translation_en` is reserved.** Declared for the translator, written by no tool:
  the translator runs before nlp-enrich creates `entities[]`, so it cannot write a field on rows
  that do not exist yet, and the AMČR pilot produces English only for free-text metadata
  (`metadata-en`; vocabulary fields use AMČR's own English labels; entity facets go by the coarse
  types). The field and the grant stay: removing it is a MAJOR, re-attributing it is breaking
  (see [Versioning Rules](#versioning-rules)). `entities` and `translation_en` gain descriptions
  saying so; `atrium_document.py` gains a comment beside the grant; the ownership table above says
  *reserved*.
* **`regenerable.*.detail` gains a description** naming the three profiles, and this document
  their definition ([References and coordinates](#references-and-coordinates)). The enum is
  unchanged. llm-enrich implements `standard` and `minimal` (`--detail`; `json_to_md@1.1`).
* **TEITOK projection (opt-in)** noted under Reference discipline: nlp-enrich can write the page
  categories and keywords into the TEITOK header; no record field changes.
* Verified: `test_schema_freeze.py` passes with the description edits (they are annotations) and
  still fails on a constraining edit.

## Changelog — 2026-10-01 (#71: the AMČR seed, `source.sha512`, `run_uuid`)

**Three additive nodes, registered; no `SCHEMA_VERSION` bump, `doc-schema-v1` stays the
reference.** Every record written before this date still validates, and so does every record
written after it under the frozen schema (`tests/test_schema_freeze_records.py`). Canonical files
change, so the re-vendor and the `v1` move follow, hub first.

* **`source.sha512`** (optional, lower-case hex): the archive's digest of the original, written by
  the seed and carried unchanged.
* **`run_uuid`** on `provenance.contributors[]` and on each `assembled.blocks` stamp (optional,
  `urn:uuid:…`): the run's stable id, the `@id` of its CreateAction. `DocumentRecord(run_uuid=…)`
  writes it, and refuses a malformed one before anything is written.
* **[The AMČR seed](#the-amčr-seed)**: its definition, the keep rule, `seed_schema()` /
  `validate_seed()` / `validate_baseline()` / `is_seed()`, and the CLI `seed-schema`. The tools'
  inherited-baseline gates move to `validate_baseline()`: they used to report a seed as an
  invalid baseline and demote their own output check to a warning.
* **`set_source()`**: a different `filename` or `media_type` from a later writer is a NOTE, never
  a WARNING, and never refused under `strict`. On the seeded path they differ on nearly every
  call, and digital-convert, which runs strict, refused the seed outright.
* Producer shape added to `tests/test_document_required.py`: a seeded record after its reading
  stage. Tests: hub `tests/test_document_seed.py`, `tests/test_fixture_schema.py` (the example
  seed), `tests/test_e2e_assert.py` (`--seed`).
* Not in this round (atrium-project#71 plan): the program successors of the coming repository
  renames, and #73's `keywords` block. Each will get its own register entries and changelog
  section.

## Program successors (2026-10-01)

**Changelog — 2026-10-01 (#72: the repository moves).** `alto-postprocess` continues as
**`ocr-postprocess`**, and the keyword stage of `llm-enrich` (with the keyword extraction of
`nlp-enrich`) continues as **`keyword-extract`**; the born-digital converter keeps its role id
`digital-convert` and the LLM-free remainder of the old repository. **An additive change; no
`SCHEMA_VERSION` bump, `doc-schema-v1` stays the reference.**

* **`PROGRAM_SUCCESSORS`** in `atrium_document.py`: `{"alto-postprocess": "ocr-postprocess",
  "llm-enrich": "keyword-extract"}`, with `canonical_program()` and `same_program()`. Each successor
  is added **beside** its predecessor in `BLOCK_OWNERS` and `BLOCK_FIELD_OWNERS` with exactly the
  predecessor's grant (one hop; the table is built once, so the two cannot drift).
* **Comparisons go through the canonical name.** The §1a origin check (`_assert_origin_consistent`),
  the `needs_ocr` hand-off (it is `ocr-postprocess` that may re-originate a digital-born document,
  whichever of the two names is running) and the fan-in check of `merge_document_records()`.
  `ORIGIN_ORIGINATORS` (and so `resolve_originator()`) now names the **current** program, `ocr-postprocess`; both spellings are the one writer. A
  block is a multi-originator block only when it has two distinct writers *after* that, so
  `enrichment` (llm-enrich + keyword-extract) is a single-owner block.
* **Nothing written is re-attributed.** An existing `assembled.blocks[*].program` or
  `provenance.contributors[].program` is never rewritten: a record written by `alto-postprocess`
  keeps that stamp, still loads, merges with one written by `ocr-postprocess`, and passes the origin
  check. Consumers that compare program names should compare `canonical_program()` of both sides.
* **`atrium_vocab.validate_labels(originator="ocr-postprocess")`** resolves to `alto-postprocess`'s
  label set through an alias; `LINE_CATEGORY_ORIGINATORS` keeps one row per label set.
* **Repository URLs** (`atrium_rocrate.REPO_URLS`, `atrium_paradata._REPO_URLS`) name each current
  program's own repository (`ocr-postprocess`, `keyword-extract`, `digital-convert`) and keep the
  predecessors' archived ones, so a crate links the release that really produced a run.
* **Descriptions only in the schema JSON** (`atrium_document.schema.json`): the owner names in the
  property descriptions. No constraint changed, so the freeze register has no new entry.
* **Not in this round:** #73's `keywords` block, which keyword-extract will own from its first release.
  It gets its own register entry and changelog section.

Tests: `docs/templates/shared/test_document_originators.py` (the successor cases),
`test_atrium_vocab.py`, `test_atrium_rocrate.py`; hub `tests/test_e2e_assert.py`.

## Changelog — 2026-10-04 (atrium-digital-convert#4 W3: the quality model scores a born-digital record)

**An additive change to `atrium_document.py`; no `SCHEMA_VERSION` bump, the schema JSON is
unchanged, `doc-schema-v1` stays the reference.**

* **`SCORING_FIELDS`** (`lines`: *categ, quality_score, lang*; `pages`: *quality_score,
  quality_band*) and `SCORING_PROGRAM = "ocr-postprocess"`. A merge by `ocr-postprocess` limited to
  them, into a plane another originator wrote, is a co-contribution: `_assert_origin_consistent()`
  notes it (it gets the merge's writable fields now; a deferred check keeps them), `merge_block()`
  does not append unmatched rows for it (and complains, which raises under `strict`), and
  `_stamp()` marks the block `contribution: "scoring"`.
* **`merge_document_records()`**: a stamp marked `contribution: "scoring"` by `ocr-postprocess` is
  not a second positional originator.
* **Unchanged:** every other foreign write is refused as before; the `needs_ocr` hand-off; the
  originator's own merges (no `contribution` key, rows appended).
* **Consumers:** `ocr-postprocess` v1.9.0-beta's `POST /score_record` (`document_hook.write_scores`),
  which atrium-digital-convert v1.1.0-beta's `POST /describe` calls; `tools/e2e/e2e_assert.py`
  accepts a scoring stamp on the born-digital branch's `lines`.
* **Tests:** `test_document_originators.py` (canonical) — the scoring merge under `strict`, no new
  row, `text`/full grant/`content` still refused, only `ocr-postprocess` scores, the originator's own
  merges unchanged, the deferred check, the fan-in.
* **Re-vendored** into the six tool repositories with `scripts/revendor_shared.sh`, which also
  gained its first sibling-owned row (`text_formats.py`, atrium-ocr-postprocess → atrium-digital-convert).

## Changelog — 2026-10-05 (W4: the OCR hand-off per page, `pages[].text_layer`)

**Additive: no `SCHEMA_VERSION` bump, `doc-schema-v1` stays the reference.** One schema node is new
(registered above). The module changes tighten a write path that only ocr-postprocess uses and add
one method.

### `pages[].text_layer` — declared, as a closed enum

* **What:** `digital | garbled | ocr | none | blank`, the converter's verdict on a page's embedded text
  layer, written by `digital-convert` (granted in `BLOCK_FIELD_OWNERS`, no other tool) on every page
  from its v1.1.1-beta. The route step reads a value instead of parsing `needs_ocr_reason`'s prose
  (proposed on ufal/atrium-project#71).
* **Meaning:** `garbled`, `ocr` and `none` are exactly the pages the converter flags `needs_ocr`
  (`tools/e2e/e2e_assert.py` checks it where the field is present). `blank` is an empty page of a
  format without page images (DOCX, ODT, a sheet): nothing to re-acquire.
* **Why additive:** every record written before it validates (the field is optional, and `pages`
  items already admitted extra keys), and the one producer writes only the five values.

### The OCR hand-off, page by page (atrium-digital-convert#4 W4)

* **`OCR_HANDOFF = "ocr-handoff"`, `OCR_HANDOFF_PROGRAM`, `ocr_handoff_pages()`,
  `DocumentRecord.handoff_pages()`**.
* **`_assert_origin_consistent()`** takes the pages a row write touches: under the hand-off, a row on
  a page the record does not flag is refused, and so is a wholesale `set_block()` (it raises under
  `strict`, like every §1a refusal). Before, any flagged page opened the whole plane.
* **`DocumentRecord.replace_page_rows(name, pages, records)`** (new): the rows of whole pages of a
  block keyed by `page` are replaced, then the block is put in page order. The origin check runs
  before anything is removed. An empty `records` empties the pages.
* **`merge_block()`** stamps such a write `contribution: "ocr-handoff"`.
  **`merge_document_records()`** accepts that stamp by `ocr-postprocess` while the merged `pages[]`
  flags a page. This settles the question left open on ufal/atrium-project#71: the fan-in honours
  the hand-off as the single-record path does, and per page.
* **Unchanged:** the scoring co-contribution (W3); every write by the record's own originator; an
  `ocr-postprocess` write onto a born-digital record that flags nothing (still refused).
* **Consumers:** ocr-postprocess v1.9.1-beta (`POST /process` with an ATR ALTO page, the record and
  the optional `page` form field; `document_hook.write_document_block()` for its batch stages);
  `tools/e2e/e2e_assert.py`, whose born-digital branch accepts a hand-off stamp when a page is
  flagged.
* **Tests:** `test_document_originators.py` (canonical, +13): the per-page refusal, the replacement
  and its ordering, the stamp, the empty OCR pass, the wholesale refusal, the fan-in with and without
  a flagged page, the deferred check, the converter-only `text_layer` grant.
  `tests/test_document_required.py`: a hand-off record shape and the `text_layer` enum.
  `tests/test_e2e_assert.py`: +6.

### Also in this round

* `atrium_service.REASON_CODES` registers **`source_digest_mismatch`** (HTTP 422), with the wording
  digital-convert has published since v1.1.0-beta (atrium-digital-convert#2). Every service's spec
  publishes the registry, so all six specs were regenerated in the same re-vendor round.
* **Re-vendored** into the six tool repositories with `scripts/revendor_shared.sh`:
  `atrium_document.py`, `atrium_document.schema.json`, `atrium_service.py`,
  `test_document_originators.py`, `test_schema_freeze.py`.

## Changelog — 2026-10-09 (#73: `keywords` and `quality_summary`; `upstream_unavailable`)

**Additive: no `SCHEMA_VERSION` bump, `doc-schema-v1` stays the reference.** Two blocks, one
`$defs` entry and their two stamp/payload clauses are new (registered above); every record written
before them validates, and a record carrying them validates under the frozen schema too (the top
level admits extra blocks).

### `keywords` — keyword-extract's statistical keywords (#67 R5)

* **What:** `{document: [k], pages: [{page, keywords: [k]}]}`, `k` =
  `$defs/statistical_keyword` {`keyword`, `method`, `score`, `rank`}, all required.
* **Who:** `BLOCK_OWNERS["keywords"] = "keyword-extract"`, from its v1.2.0-beta: `POST
  /extract_keywords` with a record writes it whenever the statistical kind runs, beside
  `enrichment` when the controlled kind runs too. No other program, `llm-enrich` included, may
  write it.
* **Consumers:** the Digital Archive's keyword facets, per document and per page
  (ARUP-CAS/aiscr-digiarchiv-2#711); nlp-enrich's opt-in TEITOK projection, which reads the block
  instead of a keyword CSV of its own (v1.1.0-beta).

### `quality_summary` — the document-level quality read-out (#67 R6)

* **What:** `atrium_document.quality_summary(record)`, a pure function of `pages[]` and `lines[]`:
  `pages` {`total`, `scored`, `mean`, `median`, `min`, `max`} over `quality_score` (the statistics
  are absent when no page is scored), `lines` {`total`, `by_categ`}. Rounded to four decimals,
  keys sorted, so the same record gives the same block.
* **Who:** `BLOCK_OWNERS["quality_summary"] = "ocr-postprocess"`, the quality model's owner. Its
  record writers (`document_hook.write_document_block()`, `write_scores()`) recompute it whenever
  they write or score `pages`/`lines`, so `/process`, `/score_record` and the batch stages leave it
  current on both branches (v1.10.0-beta).
* **Not:** a band, a threshold or a gate. `pages[].quality_score` stays the authoritative signal.

### Also in this round

* `atrium_service.REASON_CODES` registers **`upstream_unavailable`** (HTTP 502): a backing service
  that did not answer after the tool's own retries (atrium-nlp-enrich#41, LINDAT UDPipe and
  NameTag), so a client tells an outage from a 502 with `reason: null` such as an empty run. A
  backing service's timeout stays a 504 `limit_exceeded` naming the timeout setting.
* `DocumentRecord.to_dict()` orders the two blocks beside their neighbours (`quality_summary`
  after `tables`, `keywords` after `enrichment`).
* **Tests:** `test_document_originators.py` (canonical, +8): the two owners, both keyword kinds
  side by side, the refusals, the stamp/payload clauses, the summary on a born-digital record, the
  summary's numbers and its determinism. `test_schema_freeze.py`: five register entries.
  `tests/test_document_required.py`: the new producer shapes. `tools/e2e/e2e_assert.py`:
  `--keywords-stage-ran` and `--quality-summary`.
* **Re-vendored** into the six tool repositories with `scripts/revendor_shared.sh`:
  `atrium_document.py`, `atrium_document.schema.json`, `atrium_service.py`,
  `test_document_originators.py`, `test_schema_freeze.py`; every service's spec regenerated.

## Changelog — 2026-10-13 (#51: `teater_category_ids` declared; the crate stops minting theme URIs)

**Additive: no `SCHEMA_VERSION` bump, `doc-schema-v1` stays the reference.** One optional field is
new (registered above); every record written before it validates.

* **`enrichment.items[].teater_category_ids`**: `[{source, id}]`, the AMČR (`HES-…`) and TEATER
  records the item's `teater_category` stands for, its own and those of the same label the
  vocabulary build merged into it. keyword-extract has written it since the controlled kind moved
  there (`EMIT_CATEGORY_IDS`); the schema now says so. `source` and `id` are required strings; no
  enum, so an unknown source is reported downstream, never refused.
* **`teater_category` is a source label** (`kostel`), as the vocabulary spells it, not one of the
  ATRIUM themes. The description says so. Whether the field should carry the theme instead (V-5 in
  `skos_strategy.md`) is still the contract owner's question; this round records what producers
  write, it does not decide it.
* **`atrium_rocrate.py`** stops minting `https://w3id.org/atrium/theme/<label>` for
  `teater_category`: an ATRIUM identifier for an AMČR concept, and a false one when the label is
  not a theme. The crate now names each concept in `teater_category_ids` by its source URI
  (`https://api.aiscr.cz/id/<id>`, `https://teater.aiscr.cz/id/<id>`), in the harvest scheme the
  released vocabulary asset files it under (`scheme/amcr-harvest`, `scheme/teater-harvest`). An item
  without ids contributes no term. The 2026-09-17 note on #51 described this as done; it was not
  in the code until now.
* **`atrium_vocab.py`**: `HESLAR_TO_THEME` drops `jazyk` (keyword-extract excludes it) and
  `TEATER_BRANCH_TO_THEME["1"]` is `Methods`, as in keyword-extract's `taxonomy_config.json` of
  2026-10-08 (74 mappings). Scheme authorities name the successor repositories.
* **`atrium_service.py`**: the shared 502 description says when to retry: with
  `reason: upstream_unavailable`, three times with backoff; without a reason, `detail` names the
  cause, and an input that yielded nothing fails the same way again (atrium-nlp-enrich#41).
* **Tests:** `test_atrium_rocrate.py` (+5: source URIs, nothing minted without ids, unknown sources
  skipped, one term per concept whatever the item order, degraded mode); `test_schema_freeze.py`:
  one register entry.
* **Re-vendored** into the six tool repositories with `scripts/revendor_shared.sh`; every service's
  spec regenerated.

## Changelog — 2026-10-22 (#51: `teater_category` stays a source label, decided)

No schema change. motyc decided V-5 (`skos_strategy.md`): `enrichment.items[].teater_category` keeps the
AMČR/TEATER label (or the meta-text sentinel) and `teater_category_ids` its source identities, as the schema
already describes them. The registry's theme scheme names no record field any more (`atrium_vocab.py`); a theme
is a derived classification, and persisting one would be a new optional field, not added now.

## Changelog — 2026-11-04 (#6: `license_basis`; the crate root asserts no licence)

Step 1 of the rights proposal ([`proposals/rights-and-policy.md`](proposals/rights-and-policy.md)), option (a)
as motyc chose it on #6 (2026-10-29).

- **`provenance.license_basis`** (added, optional, closed enum `calculated`). Every record a tool writes from this
  release on carries it next to `license` and `license_url`. It says the value is calculated: the most restrictive
  component licence (`para_licenses`), or the conservative default when no component is recorded. It is never the
  licence of the record's content. A record written earlier has the same calculated value without the mark;
  `DocumentRecord` adds the mark when it next writes one. Registered under the freeze above. A record that
  carries it is still valid under `doc-schema-v1`, whose `provenance` allows further properties.
- **`license_detail.notes`** describes the components, not the output: "N component(s) used; each keeps its own
  licence or terms (see components). No output licence is asserted." It no longer says "Effective output license
  is X, the most restrictive among N component(s) used". The NON-COMMERCIAL and SHARE-ALIKE notes name the
  components that carry those licences. `effective_license` and the two flags stay, as the calculated label.
- **RO-Crate export** (`atrium_rocrate.py`, not the record): a document or run crate's root `license` names
  `#no-licence-asserted`, a contextual entity that asserts nothing and says the rights depend on the source and on
  AMČR's permission. The calculated value is no longer exported as the crate's licence. A fragment carries no
  licence entity: the host's root decides its own. `--wrap` gives its stub root `#no-licence-asserted` unless a
  licence is passed.
- Not in this change: the paradata `license` fields (paradata 3.0) and moving the calculated value out of the record.

## Changelog — 2026-11-12 (#84: record schema 2.0, paradata 3.0)

The hub side of doc-schema-v2, after ARÚP's output contract of 12 November 2026 and atrium-project#84.
On the hub's `test` branch; the tools adopt it each in its own repository.

- **Record 2.0** (`SCHEMA_VERSION = "2.0"`): content only. Removed: `provenance`, `assembled`,
  `derived_from`, `regenerable`, `forms`, `tables`, `content.reading_order`, `lines[].group_id`,
  `lines[].style`, `pages[].text_layer`, `needs_ocr`, `needs_ocr_reason`, `ocr`, `source.sha256`, and the
  `Garbage`/`Inverted` line categories (D1, D2, D19, D26). New: `lines[].block`, `text_source`,
  `bbox_precision`; `pages[].content_status`; `canvas.unit` `pt`/`px` with `user_unit` and `pixel_ratio`
  (names proposed); `source.origin` `digital`/`atr`/`legacy`, descriptive. Pages are keyed by
  `page_index`; lines are numbered from 1. See [Schema 2.0](#schema-20-doc-schema-v2-atrium-project84).
- **One writer of the positional blocks** (D20): ocr-postprocess, the record builder. digital-convert
  owns no block. `ORIGIN_ORIGINATORS`, `resolve_originator()`, the OCR hand-off and the scoring
  co-contribution are gone.
- **`written()`** replaces the stamps: the blocks and fields a run wrote go into its paradata.
  `add_derived_from()`, `add_regenerable()` and `add_license_detail()` raise `RemovedInSchema2`.
- **Migration**: `_migrate_1_to_2()` in `migrate_document()`, so every reader takes a 1.x record
  ([Reading 1.x records](#reading-1x-records)). The 1.x example is kept as
  `fixtures/atrium_document.v1.example.json`; `fixtures/atrium_document.example.json` is a 2.0 record.
  Seeds carry no `schema_version`.
- **Freeze**: MAJOR 2 is in `PENDING_FREEZES`; `doc-schema-v2` waits for the proof gate (D12).
  `doc-schema-v1` is unchanged.
- **Paradata 3.0, RO-Crate, limits** (shared, see [`paradata_schema.md`](paradata_schema.md) and
  [`rocrate_export.md`](rocrate_export.md)): no licence fields and no calculated licence; inputs and outputs
  by distribution name and SHA-512; a trimmed, skipped or stopped content raises `ContentLimitError` (D13).
- **E2E gate** (`tools/e2e/e2e_assert.py`): reads every record through the migration; no stamp or
  provenance checks; `--expect-atr-pages` (alias `--expect-needs-ocr`) reads the ATR pages off
  `lines[].text_source`; `--expect-layout` checks `lines[].block`; `--require-current-major` is new.
  The workflows are unchanged.
- `ocr_text_layer` stays in the service reason codes as deprecated: a published code is not removed.

## Changelog — 2026-11-14 (#84: `lines[].unit`, rule 5)

- **`lines[].unit`** (record builder; additive, 2.0 is not frozen yet): `block` marks a row that holds a whole
  docproc block scored as one unit, because the block came without lines and without a line break (D18 rule 5;
  ask 7 to the ATR). The row keeps its `categ` and `quality_score` (rule 1).
- **`quality_summary()`**: such rows stay out of `lines.by_categ` and are counted as `lines.block_units`;
  ocr-postprocess leaves them out of `pages[].quality_score`. Both are the calibrated statistics rule 5 means.
- The name is proposed by this implementation, as `canvas.user_unit` is.
