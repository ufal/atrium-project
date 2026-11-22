---
title: The document contract
nav_order: 6
status: partial
round: 6
issue: 57
---

# The document contract

The `atrium_document` record is the one thing that travels through the whole pipeline. This
page says what it holds, who may write which part of it, how it is built up step by step,
and where the history of each run is kept. It is for integrators.

> **Versions.** The tools write record schema 2.0 and paradata 3.0. The published record schema is
> `doc-schema-v1`; 2.0 is published as `doc-schema-v2` once it has passed the validator, the end-to-end
> checks and a run through the assembled chain.

!!! info "Normative text lives in the hub"
    [`docs/document_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md)
    is the specification. This page explains it, with page-classification as the worked case.

## The object

One JSON file per document, named `<doc_id>.document.json`, schema version **`2.0`**. The module
that writes it, `atrium_document.py`, is vendored byte-identically into every tool, so every tool
writes the record the same way; what differs is which calls each tool makes.

| Part                                                                                                 | What it holds                                                                                                                                                                           | Written by                                         |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| `schema_version`, `record_type`, `doc_id`                                                            | identity; `doc_id` is the AMČR file id                                                                                                                                                  | intake                                             |
| `source`                                                                                             | the original: `sha512`, `filename`, `media_type`; then `language`, `page_count` and `origin` (`digital`, `atr`, `legacy`: how the text was obtained)                                    | intake; the record builder                         |
| `pages`, `content`, `lines`                                                                          | a row for every page (`page_index`, the label `page`, `canvas`, `content_status`), the text in reading order, and every line with its box, docproc block, text source and box precision | the record builder (ocr-postprocess), from docproc |
| `page_categories`, `pages[].category`, `category_confidence`                                         | the page type of the pages that needed the ATR                                                                                                                                          | page-classification                                |
| `lines[].categ`, `quality_score`, `lang`; `pages[].quality_score`, `quality_band`; `quality_summary` | line quality: one model and one scale for every line                                                                                                                                    | scoring (ocr-postprocess)                          |
| `lines[].lemma`, `upos`, `feats`, `teitok_ref`; `pages[].teitok_surface`; `entities`                 | the linguistic layer and the named entities                                                                                                                                             | nlp-enrich                                         |
| `enrichment`, `keywords`, `entities[].pid`                                                           | keywords from the AMČR and TEATER vocabularies, statistical keywords, links of entities                                                                                                 | keyword-extract                                    |
| `translations`, `entities[].translation_en`                                                          | reserved: no tool writes them in the pilot                                                                                                                                              | —                                                  |

The record holds content only. It carries no run data, no licence and no layout: `provenance`,
`assembled`, `derived_from`, `regenerable`, `forms`, `tables`, `content.reading_order`, the line
styles and the page verdicts are gone, and the schema refuses each of them by name. The layout is
docproc's (`atr/docproc-json`); a line names its docproc block in `lines[].block`. A record must
have `schema_version`, `record_type`, `doc_id`, and `source` or a content block.

**One line key.** A line is named by `page` and `line`. An `entities[]` row and an
`enrichment.items[]` row name their line by the same pair, and when the record has `lines[]` the
validator checks that the line exists. A writer that cannot name a line of the record leaves `line`
out.

### The life of a record

1. **Load.** A stage opens the record it was given — the *baseline* — or starts a new one. A record
   of a newer major schema version is refused; a 1.x record is migrated as it is read.
2. **Write.** The stage writes only the blocks and fields it owns: `set_block()` replaces a whole
   block, `merge_block()` updates chosen fields inside a keyed list such as `pages[]`. Everything
   else in the baseline is carried through untouched.
3. **Validate.** The finished record is checked against `atrium_document.schema.json` and its line
   references; a stage never emits a record that fails.
4. **Write out.** The file is written atomically — to a temporary name, then renamed — so a
   reader never sees half a record.

The next stage repeats the cycle with this file as its baseline. What each run read and wrote is in
its paradata, not in the record (below).

## The six rules, for page-classification

The rules are the hub's; page-classification applies them so:

| Rule                                | page-classification                                                                                                                                                                    |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1 · Baseline in, record out**     | **Opt-in.** No record is written unless `--document-json-out` or `--document-json-out-dir` is set (or their `[DOCUMENT]` config keys)                                                  |
| **2 · Own block only**              | `set_block("page_categories", …)` merged with the baseline's categories, plus a `merge_block("pages", …)` keyed by `page_index` and restricted to `category` and `category_confidence` |
| **3 · No baseline → own part only** | derives `doc_id` from the filename: a trailing `-N` or `_N` is the page, the rest is the document (`scan_0007.png` → document `scan`, page `"7"`)                                      |
| **4 · No run data in the record**   | what the run read and wrote is in its paradata                                                                                                                                         |
| **5 · Facts, not a licence**        | the run lists its components with their own terms in its paradata; nothing is computed into a licence                                                                                  |
| **6 · Unknown blocks preserved**    | ✓ through the shared module                                                                                                                                                            |

The translator writes nothing into the record: its pilot job is the record-level `metadata-en`,
run when a record is archived, with its own paradata.

### What the references point at

The record names no file. The original is `source`, by `doc_id` and SHA-512; every other input and
output of a run — docproc, the TEITOK file, the record version read — is named in that run's
paradata by its AMČR distribution name and SHA-512. The TEITOK ids in the record (`teitok_surface`,
`teitok_ref`) are local to that document's TEITOK file.

## Over HTTP

The services that write to the record take it as a multipart part named `document_json` and return
it in their JSON response as `document_json`; every service returns its run as `paradata`, one
Process Run Crate `CreateAction`. A service whose own output fails the schema, on a valid baseline,
answers **500** and returns no record.

## A worked example

The committed example record,
[`fixtures/atrium_document.example.json`](https://github.com/ufal/atrium-project/blob/main/fixtures/atrium_document.example.json),
shows the blocks the steps write, for a two-page document. Its first page row:

```json
{"page": "1", "page_index": 1, "canvas": {"width": 612, "height": 792, "unit": "pt", "user_unit": 1},
 "content_status": "text", "quality_score": 0.98, "quality_band": "Clear",
 "category": "TEXT", "category_confidence": 0.97, "teitok_surface": "facs-1"}
```

`page`, `page_index`, `canvas` and `content_status` are the record builder's, the quality fields
scoring's and `teitok_surface` nlp-enrich's; page-classification writes `category`,
`category_confidence` and the `page_categories` map, and passes every other field through. The values
are the
[eleven labels](https://github.com/ufal/atrium-page-classification/blob/test/docs/reference/categories.md#definitions).

## Where the run history is

Every step writes **paradata**: one `CreateAction` per run, in RO-Crate 1.2 and Process Run Crate 0.5.
It says which program and version ran, when, for which organisation, with which parameters, which
inputs it read and which outputs it wrote (by distribution name and SHA-512; for the record, the blocks
and fields written), and which components it used, each with its own terms, as facts. It never
states a calculated licence ([Licences and paradata](licences.md)). The format is paradata **`3.0`**,
in the hub's `docs/paradata_schema.md`; AMČR stores it as the distribution's `paradata/<distribution>`.

Both formats follow the same rule for changes: an **additive** change keeps the version; a
**breaking** one raises the major version and ships a `_migrate_X_to_Y()` function. A reader refuses
a file with a *newer* major version than it knows, and migrates an older one.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                  | What was taken from it                   |
|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_document.schema.json`, `atrium_paradata.py` (`test`) | the object, the life cycle, the paradata |
| `atrium-project/docs/document_schema.md`, `docs/paradata_schema.md`, `fixtures/atrium_document.example.json` (`test`)   | the rules as specified, the example      |
| `atrium-page-classification@test` — `atrium_document_adapter.py`, `service/document_json.py`                            | what page-classification writes          |
