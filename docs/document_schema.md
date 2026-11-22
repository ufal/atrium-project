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
Schema 2.0 follows ARÚP's output contract of 12 November 2026
([atrium-project#84](https://github.com/ufal/atrium-project/issues/84)). How the schema got here, change by
change: [`decisions/document-schema-history.md`](decisions/document-schema-history.md).

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

## Schema `2.0`

**Status.** `SCHEMA_VERSION = "2.0"` on the hub's `test` branch. The tag `doc-schema-v2` is
cut only after the schema validator, the E2E checks (`e2e_assert.py --require-current-major`) and a
run through the assembled pipeline chain have passed. Until then `test_schema_freeze.py` lists
MAJOR 2 in `PENDING_FREEZES` and skips its freeze checks with that reason. `doc-schema-v1` is not
moved; 1.x records stay readable (see [Reading 1.x records](#reading-1x-records)).

**Content only.** The record holds what is known about the document. It holds no run data, no
licence and no layout:

| Removed in 2.0                                                         | Where it is now                                                                                              |
|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `provenance` (contributors, `license`, `license_url`, `license_basis`) | the run's paradata `components` (facts only, no calculated licence) and its RO-Crate `CreateAction`          |
| `assembled` (block stamps, `had_baseline`)                             | the paradata output entry: `record_fields`, the blocks and fields the run wrote (`DocumentRecord.written()`) |
| `derived_from`, `regenerable`                                          | the paradata inputs and outputs, by AMČR distribution name and SHA-512                                       |
| `tables`, `content.reading_order`, `lines[].group_id`, `lines[].style` | docproc (`atr/docproc-json`), the layout's one home; `lines[].block` joins a line to it                      |
| `forms`                                                                | nowhere: removed, with no other home                                                                         |
| `pages[].text_layer`, `needs_ocr`, `needs_ocr_reason`, `ocr`           | docproc's routing (`needsAtr`); a line says where its text came from (`text_source`)                         |
| `source.sha256`                                                        | `source.sha512` only: one digest, of the original                                                            |
| the `Garbage` and `Inverted` line categories                           | docproc line flags `decode:garbled`, `decode:inverted` (`atrium_vocab.DECODE_FLAGS`), which scoring may read |

The schema declares each removed name with `not: {}`, so a record that carries one fails validation
by name, and `DocumentRecord` refuses to write one: `add_derived_from()`, `add_regenerable()` and
`add_license_detail()` raise `RemovedInSchema2`, `set_source(sha256=…)` is refused.

**New or changed in 2.0:**

| Field                               | Values                                                                      | Meaning                                                                                                                                                                                                                |
|-------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `source.origin`                     | `digital` · `atr` · `legacy`                                                | how the text was obtained; **descriptive only**, it selects no writer; a mixed document is `digital` while it keeps a text-layer line, else `atr`                                                                      |
| `pages[].page_index`                | integer ≥ 1, **required**                                                   | the physical page, the join key with docproc `pageNumber`; `page` stays the printed label                                                                                                                              |
| `pages[].content_status`            | `text` · `empty`                                                            | an `empty` page has no lines and no page score, and is counted apart in `quality_summary`                                                                                                                              |
| `pages[].canvas`                    | `width`, `height`; `unit` `pt` (default) · `px`; `user_unit`, `pixel_ratio` | the displayed page's size and the unit of every box on it; `px` only for PCSS pages whose original cannot be matched; from docproc's `userUnit` and `pixelRatio`, the two factor names proposed by this implementation |
| `lines[].line`                      | integer ≥ 1                                                                 | numbered from 1 on every page                                                                                                                                                                                          |
| `lines[].block`                     | `p<page>-b<n>`, e.g. `p3-b7`                                                | the docproc block the line belongs to                                                                                                                                                                                  |
| `lines[].text_source`               | `text-layer` · `atr` · `legacy`                                             | where this line's text came from; a mixed document has more than one                                                                                                                                                   |
| `lines[].bbox_precision`            | `measured` · `derived` · `absent`                                           | a box the producer measured, one derived from the containing block, or none; required with `bbox`                                                                                                                      |
| `lines[].categ`                     | `Clear` · `Noisy` · `Trash` · `Non-text` · `Empty`                          | the five text-quality categories of the line-quality model                                                                                                                                                             |
| `lines[].unit`                      | `block`                                                                     | a row holding a whole docproc block scored as one unit (the block had no line breaks): scored, but kept out of the page score and `by_categ`; the name is proposed by this implementation                              |
| `quality_summary.pages.empty`       | integer                                                                     | the empty pages, counted apart                                                                                                                                                                                         |
| `quality_summary.lines.block_units` | integer                                                                     | the `unit: block` rows, counted apart from `by_categ`                                                                                                                                                                  |

`entities`, `enrichment`, `keywords`, `page_categories` and `quality_summary` keep their 1.x shape, but for the
line key below.
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
   carries it as `recordFields` on the action's result. Nothing is stamped into the record.
5. **No licence.** The record carries no licence, calculated or otherwise: the rights in an
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
  entities and enrichment items on it follow; a `line` still below 1 (1.x's "unknown") is dropped
  from an entity or enrichment item, which keeps its page;
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

In the AMČR pilot the archive writes the record before the first stage. That
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
named anywhere.

Every `bbox` is in one coordinate space: **origin top-left, y increasing downwards, in the unit
named by that page's `pages[].canvas.unit`** — `pt` (1/72 inch × `user_unit`) by default, `px`
only for PCSS pages whose original cannot be matched. A born-digital PDF writer converts
from PDF user space, which puts the origin bottom-left (with pdfplumber, use `top`/`bottom`,
never `y0`/`y1`). `bbox_precision` says whether a line's box was measured or derived from its
block.

**One line key** (`$defs/line_key`). A line is named by `page` and `line`, the key `lines[]` rows
carry and merge on. `entities[]` rows and `enrichment.items[]` rows name their line by the same pair:
`line` is an integer from 1 and needs its `page`. When the record has `lines[]`, `validate_document()`
also checks that every such reference names an existing row (`line_key_problems()`); a record without
`lines[]` (a seed, a text enriched without the record builder) has no line to name and is not checked.
A writer that cannot name the record's line leaves `line` out: keyword-extract does for an item of a
file sent beside a record. The services answer in the record's field names too (`line`, `categ`,
`page_index`, `page` as the label).

The TEITOK references are **local ids inside that document's TEITOK file** (nlp-enrich), in
TEITOK's own scheme: `pages[].teitok_surface` = the page's `<surface id>` (`facs-1`),
`entities[].teitok_ref` = the entity's `<name id>` (`n-5`), `lines[].teitok_ref` = a sentence
`<s id>` (`s-3`). They are not globally unique, so they are always read together with `doc_id`
and the TEITOK distribution the same run wrote. `pages[].teitok_surface` is set only for pages
that have a `<surface>`. `entities[].page` is the page of the entity's first token, the same page
as the `<pb>` in force where its `<name>` starts. The E2E lane checks that every
reference resolves to the right element and that the pages agree
(`tools/e2e/e2e_assert.py --teitok-dir`).

The other direction — the record's facts inside the TEITOK file — is **off by default**: page
classification and line quality stay "only in the record" (the AMČR storage contract).
nlp-enrich's opt-in projection (`POST /project_record`) writes the page
categories and keyword-extract's categories and keywords into the TEITOK header and `<pb>`
attributes; it never writes line quality, and it changes no block owner.

## Block ownership

One owner per block. Blocks that several tools contribute to are split **by field**
(`BLOCK_FIELD_OWNERS`), so no field is ever co-mutated — use `merge_block()` for those and
`set_block()` for blocks you own outright.

**One writer of the positional blocks.** `pages`, `content` and `lines` have one writer, the
**record builder**, `ocr-postprocess` (`RECORD_BUILDER`), on every route: it builds them from
docproc, whether the text came from a born-digital text layer, the ATR or PCSS ALTO. It also writes
the described `source` fields and, as the owner of the line-quality model, every line and
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

¹ The successor of `alto-postprocess` and of `llm-enrich` respectively. Each predecessor id resolves to
it — see [Program successors](#program-successors).

### Program successors

Two repositories were succeeded on 2026-10-01: `alto-postprocess` continues as `ocr-postprocess`, and the
keyword stage of `llm-enrich` (with the keyword extraction of `nlp-enrich`) continues as
`keyword-extract`. `PROGRAM_SUCCESSORS` in `atrium_document.py` maps each predecessor id to its
successor; `canonical_program()` and `same_program()` compare program names through it, so a record or
paradata file written under a predecessor's name still loads and compares equal. Grants are keyed by the
current names.

A list block's rows are keyed by `BLOCK_KEY_FIELDS`: pages by `page_index`, lines by `page` and
`line`, entities by `page`, `line` and `char_span`. A page-classification run with no baseline
writes `pages[]` rows keyed by `page_index`; the record builder adds the `page` label.

`quality_score` is one axis — **text trustworthiness, 0–1** — written by the one line-quality
model for every line, whatever its `text_source`. Consumers that filter on it are filtering the
same thing on every route: *do not show this line to the model*.

**The two read-outs.**

* `keywords` (keyword-extract): the statistical keywords of the document (`document`) and of each
  page (`pages[]`, keyed by the `lines[].page` label), every one with its `method`, `score` and
  `rank`. One run writes one method's lists, and a re-run replaces the block. The controlled
  keywords stay in `enrichment`; the two kinds are never merged into one list.
* `quality_summary` (the record builder): `atrium_document.quality_summary(record)` written
  whenever it writes pages and lines — `pages` {`total`, `empty`, `scored`, `mean`, `median`,
  `min`, `max`} of `quality_score`, and `lines` {`total`, `by_categ`, and `block_units` when a row
  holds a whole block}. Numbers only: no band, no
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
`test_schema_freeze.py` travel with them; see below. All six tools carry schema 2.0. A change reaches
a tool with `scripts/revendor_shared.sh --repo atrium-<tool>`, which copies the files; then the tool's
callers change.

## Freeze & conformance

Schema `1.0` is frozen as the tag **`doc-schema-v1`**. From that tag on, the
schema is a compatibility obligation, not a design surface.

**MAJOR 2 is pending.** Schema `2.0` has taken the MAJOR bump's first step (below): the module,
the schema and `_migrate_1_to_2()`. Its tag `doc-schema-v2` is cut only after the proof gate:
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

Each tool's `docs/reference/paradata.md` and its `CITATION.cff` (a `references:` entry of type
`standard`) name `doc-schema-v1` and its commit, so
the baseline is visible from every repository without reading the hub.

### Changing the schema after the freeze

**One freeze tag per MAJOR.** An additive change does not cut a tag and does not bump
`SCHEMA_VERSION`; `doc-schema-v1` stays the reference. What makes a change additive is versioning
rule 1 (a new optional field or block) and the freeze's rule for narrowing (a validator may accept less
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
   MAJOR 2 in `PENDING_FREEZES` (done for schema 2.0);
2. cut `doc-schema-v2` on the hub commit that carries them, **only after the proof gate**: the
   validator, the E2E checks with `--require-current-major`, and a complete run through the
   assembled chain. Remove MAJOR 2 from `PENDING_FREEZES` in the same commit;
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

## Change history

Each change to the schema since July 2026 has a dated entry. The entries are kept in full in
[`decisions/document-schema-history.md`](decisions/document-schema-history.md); their headings stay here,
one line each, because the freeze check reads them (`tests/test_schema_freeze_records.py`). An entry
marked 1.x describes a field or rule that schema 2.0 removed.

## Changelog — 2026-07-31 hardening pass

Rule 2 (own block only) made enforceable: `set_block()` warns, or raises under `strict=True`, on another tool's block. [Full entry](decisions/document-schema-history.md#changelog--2026-07-31-hardening-pass).

## Changelog — 2026-08-03 (Issue #18 §1a)

1.x: the positional blocks got two possible writers (alto-postprocess or digital-convert) with an origin-consistency check. [Full entry](decisions/document-schema-history.md#changelog--2026-08-03-issue-18-1a).

## Changelog — Issue #18 review pass (originator hardening)

1.x: additive hardening of those writer rules; no field renamed or removed. [Full entry](decisions/document-schema-history.md#changelog--issue-18-review-pass-originator-hardening).

## Changelog — 2026-08-06 (Issue #10: the doc_id fork the E2E caught)

`DocumentRecord` inherits `doc_id` from the baseline instead of overwriting it with the caller's value. [Full entry](decisions/document-schema-history.md#changelog--2026-08-06-issue-10-the-doc_id-fork-the-e2e-caught).

## Changelog — 2026-09-08 (issue #51: controlled terms get a declaration)

The fields that carry controlled terms are annotated with their scheme (`x-atrium-scheme`), linked to the SKOS registry. [Full entry](decisions/document-schema-history.md#changelog--2026-09-08-issue-51-controlled-terms-get-a-declaration).

## Changelog — 2026-09-09 (issue #54: the freeze)

Schema 1.0 frozen as `doc-schema-v1`, and why that was not a version bump; the RO-Crate view (`atrium_rocrate.py`) added. [Full entry](decisions/document-schema-history.md#changelog--2026-09-09-issue-54-the-freeze).

## Changelog — 2026-09-25 (llm-enrich#18: `lines[].style.region`, CDLA-Permissive-2.0)

1.x: `lines[].style.region` declared as a closed enum (removed with the line styles in 2.0); CDLA-Permissive-2.0 ranked. [Full entry](decisions/document-schema-history.md#changelog--2026-09-25-llm-enrich18-linesstyleregion-cdla-permissive-20).

## Changelog — 2026-09-26 (#54: the freeze made traceable)

The freeze made traceable: the frozen copy and `test_schema_freeze.py` vendored into every repository, and `doc-schema-v1` cited. [Full entry](decisions/document-schema-history.md#changelog--2026-09-26-54-the-freeze-made-traceable).

## Changelog — 2026-09-30 (#70: `translation_en` reserved, detail profiles described)

`entities[].translation_en` reserved; detail profiles described. Descriptions only. [Full entry](decisions/document-schema-history.md#changelog--2026-09-30-70-translation_en-reserved-detail-profiles-described).

## Changelog — 2026-10-01 (#71: the AMČR seed, `source.sha512`, `run_uuid`)

The AMČR seed, `source.sha512`, and 1.x's `run_uuid` on block stamps (the stamps are gone in 2.0). [Full entry](decisions/document-schema-history.md#changelog--2026-10-01-71-the-amčr-seed-sourcesha512-run_uuid).

## Changelog — 2026-10-04 (atrium-digital-convert#4 W3: the quality model scores a born-digital record)

1.x: the line-quality model scores a born-digital record written by another tool. [Full entry](decisions/document-schema-history.md#changelog--2026-10-04-atrium-digital-convert4-w3-the-quality-model-scores-a-born-digital-record).

## Changelog — 2026-10-05 (W4: the OCR hand-off per page, `pages[].text_layer`)

1.x: the per-page OCR hand-off and `pages[].text_layer` (both replaced by docproc's routing in 2.0). [Full entry](decisions/document-schema-history.md#changelog--2026-10-05-w4-the-ocr-hand-off-per-page-pagestext_layer).

## Changelog — 2026-10-09 (#73: `keywords` and `quality_summary`; `upstream_unavailable`)

The `keywords` and `quality_summary` blocks; the `upstream_unavailable` reason. [Full entry](decisions/document-schema-history.md#changelog--2026-10-09-73-keywords-and-quality_summary-upstream_unavailable).

## Changelog — 2026-10-13 (#51: `teater_category_ids` declared; the crate stops minting theme URIs)

`enrichment.items[].teater_category_ids` declared; the crate stops minting theme URIs. [Full entry](decisions/document-schema-history.md#changelog--2026-10-13-51-teater_category_ids-declared-the-crate-stops-minting-theme-uris).

## Changelog — 2026-10-22 (#51: `teater_category` stays a source label, decided)

No schema change: `teater_category` keeps the AMČR/TEATER label. [Full entry](decisions/document-schema-history.md#changelog--2026-10-22-51-teater_category-stays-a-source-label-decided).

## Changelog — 2026-11-04 (#6: `license_basis`; the crate root asserts no licence)

1.x: `provenance.license_basis: "calculated"`, and the crate root asserts no licence (the calculated licence is gone in 2.0). [Full entry](decisions/document-schema-history.md#changelog--2026-11-04-6-license_basis-the-crate-root-asserts-no-licence).

## Changelog — 2026-11-12 (#84: record schema 2.0, paradata 3.0)

Record schema 2.0 (content only) and paradata 3.0 (distributions by name and SHA-512, no licence). [Full entry](decisions/document-schema-history.md#changelog--2026-11-12-84-record-schema-20-paradata-30).

## Changelog — 2026-11-14 (#84: `lines[].unit`, rule 5)

`lines[].unit: block`, a docproc block scored as one unit. [Full entry](decisions/document-schema-history.md#changelog--2026-11-14-84-linesunit-rule-5).

## Changelog — 2026-11-16 (#84 round 8: one line key; decode verdicts apart; `forms` gone)

One line key (`$defs/line_key`); decode verdicts kept apart from line categories; `forms` removed. [Full entry](decisions/document-schema-history.md#changelog--2026-11-16-84-round-8-one-line-key-decode-verdicts-apart-forms-gone).
