# 📓 Digest — doc-schema-v2 (issue to be opened): the record and paradata changes of the output contract

> _Written **2026-11-11** after the meeting of that day, from the seven repositories at their heads of 11-09 and 11-10, and the
> contract's §5 and §8. The issue is not opened yet; rename this file to `{n}.digest.md` once it is. Plan:
> [`../plans/doc-schema-v2.plan.md`](../plans/doc-schema-v2.plan.md) · meeting digest:
> [`project_state_1111.md`](project_state_1111.md)._

Paths: **S** = hub `docs/templates/shared/` (vendored byte-identically to every tool root); **AD** =
`S/atrium_document.py`; **SCH** = `S/atrium_document.schema.json`; **DSM** = hub `docs/document_schema.md`.

**Status (2026-11-11)**: 📋 **Not opened. The contract's §8 lists eleven changes; K4TEL adds the common line
representation, SHA-512 everywhere and digital-convert's own marker set. Plans only this round.**

## What the record holds today (schema 1.0, `doc-schema-v1` + 12 registered additions)

**Run data inside the record** — all leave in v2 (D1, D2):

| Node                                                                                          | Written by                                                                                                         | Where                                                                                  |
|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `provenance.license`, `license_url`, `license_basis: "calculated"`, `license_detail`          | every tool through `_provenance()` (default CC BY-NC 4.0, plus an undeclared `license_note`)                       | AD:1379-1413; `para_licenses.resolve_effective_license()`/`merge_effective_licenses()` |
| `provenance.contributors[]` (`program`, `run_id`, `run_uuid`, `paradata_ref`, `blocks`, `at`) | every tool                                                                                                         | SCH:116-145                                                                            |
| `assembled.blocks.<name>` stamps (+ undeclared `contribution`)                                | every tool through `_stamp()`; the schema's `anyOf`/`allOf` key off them                                           | AD:1360-1377; SCH:10-44                                                                |
| `derived_from` (tool-local paths)                                                             | nlp-enrich `teitok`, page-classification `classification`, keyword-extract `enriched`, translator `translated_xml` | SCH:87-99                                                                              |
| `regenerable.markdown`                                                                        | keyword-extract                                                                                                    | `llm_client_shared.py:1456`                                                            |
| `source.sha256`                                                                               | digital-convert, ocr-postprocess                                                                                   | `digital_ir.sha256_file`; `page_split._sha256_of`                                      |

**Blocks no tool writes:** `forms` (SCH:448-473; owner keyword-extract by grant, no writer), `entities[].translation_en`
(SCH:382), `lines[].lemma/upos/feats/teitok_ref` (nlp-enrich's branch is `pass`:
`api_util/document_hook.py:407-420`). `translations` is written by the translator, with extra undeclared fields
(`utils.py:976-990`).

## `lines[]` today — one row, four writers

| Field                                  | Written by                                                                                                                         | Problem                                                                                                 |
|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `page` (label, the key with `line`)    | digital-convert, ocr-postprocess                                                                                                   | the label, not the physical page, is the key (AD:470-475)                                               |
| `line`                                 | ocr-postprocess from **1** (`classify_TEXT.py:1103`); digital-convert from **0** (`digital_ir.py:325-337`)                         | two numberings                                                                                          |
| `text`                                 | both originators                                                                                                                   | —                                                                                                       |
| `bbox`                                 | digital-convert only (pt, top-left; `digital_pdf.py:495-511`)                                                                      | ocr-postprocess reads ALTO boxes and drops them (`service/utils.py:175-277`); granted to nlp-enrich too |
| `categ`                                | ocr-postprocess (`Clear`/`Noisy`/`Trash`/`Non-text`/`Empty`); digital-convert (`Garbage`/`Inverted`, `digital_to_json.py:457-468`) | two vocabularies; ocr-postprocess never re-scores `Garbage`/`Inverted` (`document_hook.py:538`)         |
| `quality_score`                        | ocr-postprocess (text quality, `text_util.compute_quality_score`); digital-convert (decode sanity, `decode_sanity()` 408-454)      | two meanings                                                                                            |
| `lang`                                 | both                                                                                                                               | —                                                                                                       |
| `group_id`, `style`                    | digital-convert                                                                                                                    | —                                                                                                       |
| `lemma`, `upos`, `feats`, `teitok_ref` | nobody                                                                                                                             | granted to nlp-enrich                                                                                   |

Side doors: `SCORING_FIELDS` (AD:423-429) and `OCR_HANDOFF` / `replace_page_rows()` (AD:449-460, 924), which replaces
**all** lines of a `needs_ocr` page.

## `pages[]` today

| Field                                                                                    | Written by                                                                                                  | Problem                                                   |
|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `page` (label)                                                                           | both originators                                                                                            | —                                                         |
| `page_index`                                                                             | digital-convert only (`digital_to_json.py:996`)                                                             | ocr-postprocess only reads it; H2 wants it on every row   |
| `canvas`                                                                                 | digital-convert only (`unit` defaults to `px` in the schema)                                                | —                                                         |
| `text_layer` (`digital`/`garbled`/`ocr`/`none`/`blank`), `needs_ocr`, `needs_ocr_reason` | digital-convert                                                                                             | —                                                         |
| `ocr` (`engine`, `lang`, + `source_pages`, `force_single_page`)                          | ocr-postprocess (`document_hook.py:705-752`)                                                                | `engine` is run data (D9)                                 |
| `quality_score`, `quality_band`                                                          | digital-convert (thresholds 0.90/0.50) and ocr-postprocess (plurality vote, `document_hook.quality_band()`) | two rules (`atrium_vocab.QUALITY_BANDS` defines the vote) |
| `category`, `category_confidence`                                                        | page-classification                                                                                         | —                                                         |
| `teitok_surface`                                                                         | nlp-enrich                                                                                                  | —                                                         |

## Boxes

- digital-convert: PDF in pt, top-left (light engine; Docling converted with `top_left()`); DOCX/ODT/XLSX/RTF have
  no boxes and no canvas.
- ocr-postprocess: none in the record.
- nlp-enrich: `entities[].bbox` in the raw ALTO unit (pixel, mm10 or inch1200; `api_util/teitok_alto.py:358-367`);
  for a born-digital record it reads digital-convert's pt boxes (`api_util/record_layout.py`).
- ATR (docproc): region boxes in pt, top-left (D8); ALTO from another component, at block level.

## Hashes and paradata

- `atrium_rocrate.ni_uri()` (479-486) builds `ni:///sha-256;…`; `file_entity()` (612-639) hashes every upload and
  output with SHA-256 and is called by every service. No SHA-512 variant.
- `source.sha512` is optional since #71; the seed requires it (AD:94); digital-convert verifies it
  (`verify_seed_digest()`, a 422 `source_digest_mismatch`); hub `tools/e2e/make_seed.py` writes it.
- Results name unstored files: `predictions.json`, `cleaned_lines.json`, `results.json` (`docs/rocrate_export.md`
  §5.2).
- The crate root is `#no-licence-asserted` (`atrium_rocrate.py` 121, 343). AMČR builds the record's crate (§5.7).
- `limits_applied` notes carry the effects `sampled`, `split`, `trimmed`, `skipped`, `stopped`
  (`atrium_limits.EFFECTS`); D13 keeps only the first two.
- Not file identities, so not in scope: image digests, OpenAPI digests, decision-client cache keys, vocabulary
  build hashes.

## The procedure already written

DSM:485-495 describes a MAJOR bump: `_migrate_1_to_2()`, `SCHEMA_VERSION = "2.0"`,
`atrium_document.schema.doc-schema-v2.json`, `FREEZES[2]`, the `doc-schema-v2` tag. `docs/shared_components.md`
rule 4 classes it as (c), which needs AMČR's agreement; the contract gives it (D12), with the proof gate.

## Docproc

No repository mentions docproc. The schema arrived on 10 November with ARÚP; it is to be shared on the consolidated
issue with Ronald's consent (§8). Until then the reader's block types and field names are unknown.

---
_Derived reading aid; the code, the contract and the issue (once opened) are the source of truth._
