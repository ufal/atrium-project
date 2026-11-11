# Strategy — doc-schema-v2 (issue to be opened): one record, one line shape, paradata AMČR can store

> _Written **2026-11-11** after the meeting of that day (contract §5, §8; K4TEL's points in session). Evidence:
> [`../digests/doc-schema-v2.digest.md`](../digests/doc-schema-v2.digest.md) · meeting digest:
> [`../digests/project_state_1111.md`](../digests/project_state_1111.md). The issue is not opened; rename this file
> and the tools' slices (`<repo>/agent_dev_logs/plans/doc-schema-v2.plan.md`) to the issue number once it is._

**Status (2026-11-11)**: 📋 **Planned, not opened. One consolidated issue in the hub for every record and paradata
change, with the docproc schema shared there as the contract the record aligns to. Code starts in the next round;
`doc-schema-v2` is tagged only after the proof gate.**

## Goal

One record per document that holds content only, with one line shape that every tool reads and writes; paradata
that AMČR can store as they are. The changes arrive during the pilot phase (§6 of the contract), released as
`doc-schema-v2` once proven. `doc-schema-v1` stays as published and cited.

## The changes

| #  | Change                                                                                                                                           | Decision    | Owner of the code                                                                   |
|----|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------|-------------------------------------------------------------------------------------|
| 1  | No calculated licence: `provenance.license`, `license_url`, `license_basis`, the computed `license_detail`, the merging                          | D2          | hub shared modules                                                                  |
| 2  | Run history out of the record (`contributors[]`, the stamps); one `run_uuid` per block                                                           | D1          | hub                                                                                 |
| 3  | `derived_from` and `regenerable` out of the record                                                                                               | D1          | hub; nlp-enrich, page-classification, keyword-extract, translator stop writing them |
| 4  | Every line scored by ocr-postprocess; one `categ` vocabulary, one `quality_score`; digital-convert's verdict out of `categ` into its own markers | D17, D18    | ocr-postprocess, digital-convert                                                    |
| 5  | The page merge takes the route's pages and replaces only the lines that do not decode                                                            | D14         | ocr-postprocess, hub                                                                |
| 6  | `content` rebuilt after a page merge                                                                                                             | H8          | ocr-postprocess                                                                     |
| 7  | `page_index` on every page and line row                                                                                                          | H2          | all originators                                                                     |
| 8  | A line's box written by its originator, in pt, top-left                                                                                          | D16, D8     | digital-convert, ocr-postprocess; nlp-enrich stops                                  |
| 9  | `forms` removed; `translations` and `entities[].translation_en` reserved                                                                         | D19         | hub; translator stops writing `translations`                                        |
| 10 | Alignment with docproc: pt, top-left, `pageNumber` = `page_index`, ISO 639-1, a line's link to its block                                         | D8          | hub, ocr-postprocess                                                                |
| 11 | Paradata in the stored form: distribution names and SHA-512, stored outputs only                                                                 | §5.5        | hub; every service                                                                  |
| 12 | One common line representation (below)                                                                                                           | K4TEL       | all                                                                                 |
| 13 | SHA-512 for every file AMČR identifies; `source.sha512` required                                                                                 | K4TEL, §5.5 | hub, digital-convert, ocr-postprocess                                               |
| 14 | A limit that trims, skips or stops content fails the job; sampling and splitting are recorded                                                    | D13         | hub `atrium_limits.py`; each tool                                                   |

## The v2 record

**Top level.** `schema_version` `"2.0"`, `record_type`, `doc_id` (the AMČR file id), `source` (`sha512` required,
`filename`, `media_type`, `origin`, `page_count`, `language[]`), the per-block run map (Q1), `page_categories`,
`pages[]`, `content`, `lines[]`, `tables[]`, `entities[]`, `enrichment`, `keywords`, `quality_summary`. Reserved:
`translations`, `entities[].translation_en`. Removed: `provenance`, `assembled`, `derived_from`, `regenerable`,
`forms`, `source.sha256`.

**`pages[]`**

| Field                                         | Writer              | Note                                                                    |
|-----------------------------------------------|---------------------|-------------------------------------------------------------------------|
| `page_index` (required)                       | the originator      | physical page, 1-based; = docproc `pageNumber` = ALTO `PHYSICAL_IMG_NR` |
| `page`                                        | the originator      | the label (i, ii, A-1)                                                  |
| `canvas`                                      | the originator      | `{width, height, unit: "pt"}`                                           |
| `origin`                                      | the originator      | `text_layer` or `atr`; replaces `ocr` (`engine` goes to the paradata)   |
| `text_layer`, `needs_ocr`, `needs_ocr_reason` | digital-convert     | signals to the route, not decisions                                     |
| `decode_score`                                | digital-convert     | the page's share of decodable text (its markers)                        |
| `category`, `category_confidence`             | page-classification |                                                                         |
| `quality_score`, `quality_band`               | ocr-postprocess     | one banding rule (the plurality vote of `atrium_vocab.QUALITY_BANDS`)   |
| `teitok_surface`                              | nlp-enrich          |                                                                         |

**`lines[]` — one shape for every origin**

| Field                                  | Writer               | Note                                                                                                               |
|----------------------------------------|----------------------|--------------------------------------------------------------------------------------------------------------------|
| `page_index`, `line` (required)        | the originator       | `line` 1-based, in reading order within the page; the key                                                          |
| `text` (required)                      | the originator       |                                                                                                                    |
| `origin`                               | the originator       | `text_layer` or `atr`                                                                                              |
| `bbox`                                 | the originator only  | `[x0, y0, x1, y1]`, pt, top-left                                                                                   |
| `bbox_level`                           | the originator       | `line` (digital-convert) or `block` (ATR: region boxes, no words)                                                  |
| `block`                                | ocr-postprocess      | the docproc block the line came from                                                                               |
| `handwritten`                          | ocr-postprocess      | ATR's handwritten/typed type (Q5)                                                                                  |
| `group_id`, `style`                    | the originator       | layout cues; for ATR lines `style.region` from docproc's cross-page clusters (running headers, footers, footnotes) |
| `decode`, `decode_score`               | digital-convert      | the text-layer marker set: `ok`, `garbled`, `inverted`; never called a category (Q5)                               |
| `categ`, `quality_score`, `lang`       | ocr-postprocess only | five categories, one scale, every line                                                                             |
| `lemma`, `upos`, `feats`, `teitok_ref` | nlp-enrich           |                                                                                                                    |

Consumers that filter lines (nlp-enrich, keyword-extract) read `categ` only; `atrium_vocab.UNTRUSTWORTHY_LINE_CATEGORIES`
loses `Garbage` and `Inverted`.

## The paradata (version 3)

One `CreateAction` per step (RO-Crate 1.2, Process Run Crate 0.5), as the meeting digest gives it: `@id` =
`run_uuid`; `instrument`; `agent`; times; `object` and `result` by distribution name and SHA-512, the record version
read, the blocks written; `parameters`; `limits` (sampled, split); `components` with their terms, never combined.
The distribution names come from the pipeline with the job; a tool hashes what it reads and writes. The ÚFAL crate
module keeps the building blocks (action, software, validator) and drops the `#no-licence-asserted` root: AMČR builds
the record's crate and puts the source's licence in `File.license`.

## Tasks

**Hub (first; then re-vendored with `scripts/revendor_shared.sh`, `--check` in CI):**

1. `atrium_document.py`: `SCHEMA_VERSION = "2.0"`, `_migrate_1_to_2()` (drops the run data, moves stamps' `run_uuid`
   into the run map, renumbers digital-convert's lines from 1, maps `Garbage`/`Inverted` to `decode`),
   `FREEZES[2]`, `atrium_document.schema.doc-schema-v2.json`; the merge of D14 in place of `OCR_HANDOFF` /
   `replace_page_rows()`; field grants per the tables above.
2. `atrium_paradata.py`, `para_licenses.py`: no `_license_block`, rank or merge; `para_licenses` keeps the component
   registry as facts.
3. `atrium_rocrate.py`: `file_entity(name, data)` with SHA-512 and the distribution name; `object`/`result` per
   §5.5; fragments only; `action_problems()` checks the new shape.
4. `atrium_limits.py`: `trimmed`, `skipped`, `stopped` raise; `sampled`, `split` go to `limits`.
5. `atrium_vocab.py`: one line-category originator; the decode vocabulary.
6. Docs: `docs/document_schema.md` (register and changelog), `docs/paradata_schema.md`, `docs/rocrate_export.md`,
   and the pages that describe the order of the steps (#79).
7. E2E: both lanes in the new order; a docproc fixture once the schema is shared (Q4).

**Tools** — each slice plan lists its own work:

| Repository          | Its part                                                                                                                                        |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| digital-convert     | every input (images, CSV/TXT added); `/describe` calls nothing; the decode markers; lines from 1; `page_index`; SHA-512; refusing limits        |
| ocr-postprocess     | the docproc reader; the record built from ATR; the D14 merge and `content` rebuild; every line scored; boxes in pt; `page_index`                |
| page-classification | `page_index`; no `derived_from`; the original as input                                                                                          |
| nlp-enrich          | the `lines[]` linguistic fields; `entities[].bbox` in pt; TEITOK boxes from the originator; no `derived_from`; one action in two paradata files |
| keyword-extract     | no `derived_from`, no `regenerable`; components with their terms                                                                                |
| translator          | `metadata-en` as a record-level job; the field list per request; nothing in the record; no field text in the paradata                           |

## Order of work

1. This round: the logs (done 11-11).
2. Open the issue (body below); attach the docproc schema with Ronald's consent.
3. Hub shared modules and docs, one PR.
4. digital-convert and ocr-postprocess (the line originators), then the four others; one PR per repository, each
   referring to the hub issue.
5. The E2E lanes in the new order; then the proof gate.

## Proof gate (D12)

`doc-schema-v2` is tagged only when all three hold: the validator accepts every tool's output and the migrated
fixtures; both E2E lanes pass in the new order; one document of each variant (A–D) has run through the assembled
chain on the cluster. Not on review alone.

## Questions for the next meeting

- **Q1** — The per-block `run_uuid`: one top-level map from block name to `run_uuid` (recommended: rows stay
  content), or a member inside each block?
- **Q2** — ATR skips empty pages without an entry, against H5. The reader then needs the route's page list to tell
  an empty page from a lost one; or can docproc keep an empty entry with a reason?
- **Q3** — ALTO comes from "another component": which step's paradata records it? Should docproc be the primary
  input of ocr-postprocess and nlp-enrich, and ALTO an output for AMČR only?
- **Q4** — The docproc schema on the consolidated issue (with Ronald's consent), so the reader follows its block
  types and fields.
- **Q5** — The names `decode` / `decode_score`; whether the handwritten/typed type is stored per line.
- **Q6** — A model's input cut to its window — keyword-extract's vocabulary fitted to the context, ocr-postprocess's
  perplexity window: is that the trimming D13 forbids, or a recorded limit like sampling?
- **Q7** — A line ocr-postprocess cannot score: does the job fail, or does the line get a category?

## Issue body (draft, for K4TEL to post)

```markdown
Record and paradata changes agreed on 11 November (the output contract, §5 and §8), released as `doc-schema-v2` once proven.

**Changes**
1. No calculated licence in the record, the paradata or a crate; components keep their terms (D2).
2. Run history, stamps, `derived_from` and `regenerable` leave the record; one `run_uuid` per block (D1).
3. One line shape for every tool: `page_index`, `line` (1-based), `text`, `origin`, `bbox` in pt from the line's originator, `bbox_level`, `block`; `categ`, `quality_score` and `lang` from ocr-postprocess only; digital-convert's text-layer verdicts as their own markers (D8, D14, D16–D18).
4. `page_index` on every row; `content` rebuilt after a page merge (H2, H8).
5. `forms` removed; `translations` and `entities[].translation_en` reserved (D19).
6. Paradata name inputs and outputs by distribution and SHA-512, stored outputs only (§5.5).
7. A step whose limits trim, skip or stop content fails the job (D13).

**Contract it aligns to:** `atr/docproc-json` (schema attached with Ronald's consent).

**Release:** tagged `doc-schema-v2` after the validator, both E2E lanes and one run through the assembled chain; `doc-schema-v1` stays as published.
```

## Done when

The issue's changes are released in the shared modules and all six tools; the proof gate holds; the tag
`doc-schema-v2` exists and `doc-schema-v1` is untouched.

## Boundaries

- Parked scope stays parked: decision models, `/describe` in the pipeline, `forms`, full-text translation.
- AMČR's crate, the import and the store step are AMČR's and the pipeline's (aiscr-webamcr, aiscr-docs-pipeline).
- The ATR service and its schema are ARÚP's (aiscr-atr); ÚFAL proposes, ARÚP decides.
