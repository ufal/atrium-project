# 📓 Digest — [#84](https://github.com/ufal/atrium-project/issues/84) `open`: doc-schema-v2: the record and docproc contract after the 11 November meeting

> _**Refreshed 2026-11-14**: the seven PRs of 11-14 and their checks (no new comment on the thread). Earlier:
> **refreshed 2026-11-13**: comment 2, Kate's reply (11-12 09:52 UTC). The #84 files are named
> `doc-schema-v2.*` again (`84.*` on 11-12 and 11-13). Earlier: refreshed **2026-11-12** when motyc opened the issue
> (08:22 UTC, the docproc schema as comment 1), read against ARÚP's output contract of 12 November
> ([`project_state_1211.md`](project_state_1211.md)) and the seven repositories at their `test` heads of 11-11; written
> **2026-11-11** before the issue existed (its sections below, from "What the record holds today", describe the code
> of 11-11)._
> _Source of truth: the live issue; no export in `issues/` yet (to be generated). Plan:
> [`../plans/doc-schema-v2.plan.md`](../plans/doc-schema-v2.plan.md)._

**Labels**: `enhancement`, `development` · **Type**: Task · **Milestone**: Q4 [WP3: Conclusion of Semantic
Harmonization] · **Assignees**: none · **Comments**: 2

Paths: **S** = hub `docs/templates/shared/` (vendored byte-identically to every tool root); **AD** =
`S/atrium_document.py`; **SCH** = `S/atrium_document.schema.json`; **DSM** = hub `docs/document_schema.md`.

**Status (2026-11-14)**: 🟡 **One PR per repository, `doc-schema-v2` into `test` (K4TEL): the hub's
[#86](https://github.com/ufal/atrium-project/pull/86) and the six tools' (below). No review or comment yet; every PR
has failing checks.**

**Status (2026-11-13)**: 🟡 **Kate answered on 11-12 (comment 2): points 1 and 2 agreed, with the stored docproc
written by the ATR, narrower than point 1 of the body (digital-convert or the ATR; Q15 in the plan). Ronald's
answers on ARUP-CAS/aiscr-docs-pipeline#17 are pending.** _(superseded 11-14: the PRs are open)_

**Status (2026-11-12)**: 🟡 **Opened by motyc; it takes over K4TEL's draft on #67 (11-11 18:30). One answer is
due from Kate by 16 November: whether she agrees with the two-level contract and with dropping ALTO (points 1
and 2), which is also her consent as first author for the paper revision (#13). Ronald gets the same two
questions on ARUP-CAS/aiscr-docs-pipeline#17. Everything else at the normal pace.** _(superseded 11-13: Kate
answered)_

**Status (2026-11-11)**: 📋 Not opened. The contract's §8 listed eleven changes; K4TEL added the common line
representation, SHA-512 everywhere and digital-convert's own marker set. _(superseded 11-12: the issue is #84;
the line shape is §2 of the body, with the layout in docproc)_

## 🧭 2026-11-14 — the PRs and their checks

| PR                                                                                          | Head      | Failing checks (job log)                                                                                                                                         |
|---------------------------------------------------------------------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [atrium-project#86](https://github.com/ufal/atrium-project/pull/86)                         | `1aef6ad` | RO-Crates: `ro-crate-1.2_13.3`, no root `license`, on 4 crates; shared modules: the ocr-postprocess image closure (1 of 730)                                     |
| [atrium-page-classification#71](https://github.com/ufal/atrium-page-classification/pull/71) | `d37a8bb` | drift (canonical): `atrium_limits.py` and others differ from the hub at `4435ffb`; api-contract: record major 1.0 → 2.0                                          |
| [atrium-translator#60](https://github.com/ufal/atrium-translator/pull/60)                   | `7b3b853` | drift (canonical); api-contract: record major                                                                                                                    |
| [atrium-keyword-extract#5](https://github.com/ufal/atrium-keyword-extract/pull/5)           | `9218faf` | drift (canonical); api-contract: record major                                                                                                                    |
| [atrium-nlp-enrich#45](https://github.com/ufal/atrium-nlp-enrich/pull/45)                   | `d0df625` | drift (canonical); api-contract: record major                                                                                                                    |
| [atrium-digital-convert#10](https://github.com/ufal/atrium-digital-convert/pull/10)         | `fd5951d` | drift (canonical); drift (vendored): `requirements_flexiconv.txt` against nlp-enrich `ba81709`; api-contract: `document_json` gone from `/describe`, `/reformat` |
| [atrium-ocr-postprocess#11](https://github.com/ufal/atrium-ocr-postprocess/pull/11)         | `1a9e778` | build / test; drift (canonical); api-contract: record major, `ocr_handoff` and `skipped_decode_verdict` gone                                                     |

The causes and fixes are in the [plan](../plans/doc-schema-v2.plan.md#status--prs-11-14). The RO-Crate failure
comes from round 2 dropping the root's `#no-licence-asserted`, which motyc confirmed on #6 on 11-12 08:24
([comment](https://github.com/ufal/atrium-project/issues/6#issuecomment-6818590785)); see [`6.digest.md`](6.digest.md).

## 🧭 2026-11-12 — what the issue asks

| §            | Content (the body's own terms)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Frame        | Kate's draft frame stays: three contracts, content only, run data in paradata, `doc-schema-v1` as published, `doc-schema-v2` tagged only after the validator, the E2E checks and a run through the assembled chain                                                                                                                                                                                                                                                                                                                                                                                         |
| 1 Two levels | layout = `atr/docproc-json` by digital-convert or the ATR, one stored per document; record = `atrium/document-json`, positional blocks built by ocr-postprocess from docproc; digital-convert writes docproc with lines and per-page verdicts (`text_layer`, `needs_atr`), never refuses, never samples; `needs_ocr`/`needs_ocr_reason` → `needs_atr` and its reason; the merge of a mixed document; `source.origin` descriptive (`digital`, `atr`, `legacy`); no ALTO; nlp-enrich's layout from the record or docproc, #24's three-format decision revised; page-classification on `needs_atr` pages only |
| 2 Record     | no run data (`provenance`, `assembled`, `derived_from`, `regenerable`, and the per-block `run_uuid`: it would change the checksum on every rerun); layout stays in docproc (`tables[]`, `content.reading_order`, `lines[].group_id`, `lines[].style`, the page verdicts); new `lines[].block`, `lines[].text_source`, `lines[].bbox_precision`, `pages[].content_status` (names are proposals); `forms` removed; `translations`, `entities[].translation_en` reserved; one coordinate space; `page_index` on every page row                                                                                |
| 3 Scoring    | rules 1–8 (the contract's §7); `/score_record` no longer skips `Garbage`/`Inverted` lines                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 4 Paradata   | distribution name and SHA-512, never `ni:///sha-256` or local paths; an output not stored but reaching a stored distribution is recorded with its SHA-512 and marked ("no **unmarked** outputs that are not stored"); `result` names blocks **and fields**; `actionStatus` stays; digital-convert's paradata per H14                                                                                                                                                                                                                                                                                       |
| 5 Translator | the field list with each request; no default list (`amcr-fields.txt` and `fields =` go); a metadata request without a list is refused; the list in `paradata/metadata-en` `parameters`, no field text                                                                                                                                                                                                                                                                                                                                                                                                      |
| 6 Licences   | unchanged from the draft and #6; no `merge_effective_licenses` in templates or validator; LINDAT outputs not published until #78                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 7 docproc    | schema to aiscr-docs-pipeline under an ARUP-CAS identifier (ARÚ/B decides, ATR and ÚFAL propose); `metadata.routing` stays in the output; routing lists every page, an empty one routed `empty`; the ATR echoes forced pages with their reason                                                                                                                                                                                                                                                                                                                                                             |
| Per tool     | digital-convert: docproc with lines and verdicts, `needs_atr`; ocr-postprocess: the record from docproc, rules 1–8; nlp-enrich: layout not from ALTO; page-classification: `needs_atr` pages, output unchanged; translator: field list per request; shared templates and validator: §2 and §4                                                                                                                                                                                                                                                                                                              |

## 🧭 2026-11-12 — comment 2, Kate's reply

[Comment 2](https://github.com/ufal/atrium-project/issues/84#issuecomment-6820372800) (K4TEL, 09:52 UTC):

- agrees with points 1 and 2: docproc the one stored layout output, "written by ATR", the record built from it by
  ocr-postprocess, no ALTO produced or stored;
- "I will also describe this shape in the paper revision under the gated wording on #13";
- the other points follow on the issue.

## 🧭 2026-11-12 — the docproc schema of comment 1

`docproc-document.actual.schema.json` (Ronald, 10 November; "as actually emitted, derived from code"),
`$id` `https://stellarbase.ai/schemas/docproc/v1/document.actual.schema.json`, draft 2020-12. Facts that bear on
our side:

| Area           | What the schema says                                                                                                                                                                                                                                                                                                                                                     | Against the contract                                                                                       |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| Top level      | required `version` (`MAJOR.MINOR`, v1.x additive only), `pipeline`, `processedAt`, `pages`; `additionalProperties: false`                                                                                                                                                                                                                                                | `pipeline`, `processedAt` to paradata or optional (Ronald's ask 3)                                         |
| Producer       | `pipeline` pattern `^pipeline-e2e(/[a-z0-9-]+)?$`                                                                                                                                                                                                                                                                                                                        | opened for other producers (ask 13)                                                                        |
| Source         | `sourceFile` is a temp path or bare name; `sourceHash` is SHA-256 of the file read (for images the wrapped PDF)                                                                                                                                                                                                                                                          | the original by SHA-512 in the paradata (§4, D9)                                                           |
| `sourceFormat` | `pdf-digital` (mixed PDFs too), `pdf-scanned`, `docx`, `pptx`, `image`                                                                                                                                                                                                                                                                                                   | gains ODT, spreadsheets (ask 13)                                                                           |
| `warnings`     | human-readable; consumers "MUST NOT treat as fatal"                                                                                                                                                                                                                                                                                                                      | an unread block or page fails (ask 9, D13)                                                                 |
| Routing        | `metadata.routing.pages[]`: `page`, `route`, `classifier_label`, `classifier_confidence`, `conf_tier`, `qc_required`, `text_layer` (boolean), `recovered_to_photo`; `counts`                                                                                                                                                                                             | stays as data; every page; forced pages with reason (asks 4, 5)                                            |
| Page           | required `pageNumber` (1-based), `width`, `height`, `blocks`; `coordinateUnit` `pt` locally, `px` on the cloud fallback; `rotation` only DOCX/PPTX (always 0); `renderDpi` absent on born-digital fast-path pages                                                                                                                                                        | UserUnit, verdict, `needs_atr` added; one coordinate space (asks 10, 13)                                   |
| Block          | required `id`, `type`, `bbox`, `readingOrder` (dense per page); `id` pattern `p{page}-b{n}` with suffixes `.f`, `.h`, `.c`, `.t0` (figure OCR child); `confidence` 1.0 for native text; opaque `sourceEngine`; `parent`/`children`, `continuedFrom`/`continuedTo`, `captionBlockId`; open `flags` (`all_engines_failed` = text extraction failed); `cellGrid` for tables | optional `lines[]` with box precision; handwriting marker (asks 8, 13); `all_engines_failed` fails the job |
| Block types    | 20 values; `seal`, `abstract`, `handwriting` never emitted; DOCX/PPTX use `paragraph`                                                                                                                                                                                                                                                                                    | handwriting marker to be added (ask 8)                                                                     |
| Images         | `imageRef` required on `image`/`figure`/`chart`; `imageData` base64 on DOCX/PPTX                                                                                                                                                                                                                                                                                         | not stored (ask 12)                                                                                        |
| Lines          | **none**: a block's `content` is its text; table content is HTML, Markdown or plain text depending on the path                                                                                                                                                                                                                                                           | optional `lines[]`; does OCR keep a line break per visual line (ask 7; rule 5)                             |
| Cloud fallback | `metadata.fallback` (`provider`, `model`, `reason`, `usage`, …), `metadata.engine`                                                                                                                                                                                                                                                                                       | off in the pilot (D32, ask 11)                                                                             |

The block id is the value `lines[].block` points to; `readingOrder` and `readingOrderRole` give the order the
record builder rebuilds `content` in (H8).

## 🧭 2026-11-12 — the record v1 → #84

| v1 node (who writes it today)                                                                            | In #84                                                                                              |
|----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| `provenance.*`, `assembled.*` (every tool), `derived_from` (four tools), `regenerable` (keyword-extract) | removed; no per-block `run_uuid` either                                                             |
| `source.sha256` (digital-convert, ocr-postprocess)                                                       | gone; `source.sha512` from intake                                                                   |
| `source.origin` (selects a writer today)                                                                 | descriptive: `digital`, `atr`, `legacy`                                                             |
| `pages[].text_layer`, `needs_ocr`, `needs_ocr_reason` (digital-convert)                                  | removed; the verdict and `needs_atr` live in docproc's routing (D27)                                |
| `pages[].ocr` (ocr-postprocess)                                                                          | removed                                                                                             |
| `pages[].page_index` (digital-convert only), `page`, `canvas` (digital-convert)                          | written by the record builder on every page row; `canvas` in pt with UserUnit; `content_status` new |
| `pages[].quality_score`, `quality_band` (two writers, two rules)                                         | ocr-postprocess only, one band scheme                                                               |
| `lines[].page`, `line` (0- or 1-based), `text`, `bbox` (digital-convert only)                            | the record builder; `block`, `text_source`, `bbox_precision` new                                    |
| `lines[].group_id`, `style` (digital-convert)                                                            | removed (layout in docproc)                                                                         |
| `lines[].categ`, `quality_score` (two vocabularies, two meanings)                                        | ocr-postprocess only, five categories; the decode verdict a flag on docproc lines                   |
| `lines[].lemma`, `upos`, `feats`, `teitok_ref` (never written)                                           | nlp-enrich                                                                                          |
| `tables[]` (digital-convert, ocr-postprocess), `content.reading_order`                                   | removed; `cellGrid` in docproc, the table's text as lines                                           |
| `forms` (never written), `translations` (translator)                                                     | `forms` removed; `translations` reserved                                                            |

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
| `group_id`, `style`                    | digital-convert                                                                                                                    | — _(11-12: both leave the record, D26)_                                                                 |
| `lemma`, `upos`, `feats`, `teitok_ref` | nobody                                                                                                                             | granted to nlp-enrich                                                                                   |

Side doors: `SCORING_FIELDS` (AD:423-429) and `OCR_HANDOFF` / `replace_page_rows()` (AD:449-460, 924), which replaces
**all** lines of a `needs_ocr` page.

## `pages[]` today

| Field                                                                                    | Written by                                                                                                  | Problem                                                                    |
|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| `page` (label)                                                                           | both originators                                                                                            | —                                                                          |
| `page_index`                                                                             | digital-convert only (`digital_to_json.py:996`)                                                             | ocr-postprocess only reads it; H2 wants it on every row                    |
| `canvas`                                                                                 | digital-convert only (`unit` defaults to `px` in the schema)                                                | —                                                                          |
| `text_layer` (`digital`/`garbled`/`ocr`/`none`/`blank`), `needs_ocr`, `needs_ocr_reason` | digital-convert                                                                                             | — _(11-12: move to docproc's routing as the verdict and `needs_atr`, D27)_ |
| `ocr` (`engine`, `lang`, + `source_pages`, `force_single_page`)                          | ocr-postprocess (`document_hook.py:705-752`)                                                                | `engine` is run data (D9)                                                  |
| `quality_score`, `quality_band`                                                          | digital-convert (thresholds 0.90/0.50) and ocr-postprocess (plurality vote, `document_hook.quality_band()`) | two rules (`atrium_vocab.QUALITY_BANDS` defines the vote)                  |
| `category`, `category_confidence`                                                        | page-classification                                                                                         | —                                                                          |
| `teitok_surface`                                                                         | nlp-enrich                                                                                                  | —                                                                          |

## Boxes

- digital-convert: PDF in pt, top-left (light engine; Docling converted with `top_left()`); DOCX/ODT/XLSX/RTF have
  no boxes and no canvas.
- ocr-postprocess: none in the record.
- nlp-enrich: `entities[].bbox` in the raw ALTO unit (pixel, mm10 or inch1200; `api_util/teitok_alto.py:358-367`);
  for a born-digital record it reads digital-convert's pt boxes (`api_util/record_layout.py`).
- ATR (docproc): region boxes in pt, top-left (D8); ALTO from another component, at block level. _(superseded
  11-12: no ALTO at all, D24; one coordinate space with CropBox, `/Rotate` and UserUnit, D28)_

## Hashes and paradata

- `atrium_rocrate.ni_uri()` (479-486) builds `ni:///sha-256;…`; `file_entity()` (612-639) hashes every upload and
  output with SHA-256 and is called by every service. No SHA-512 variant.
- `source.sha512` is optional since #71; the seed requires it (AD:94); digital-convert verifies it
  (`verify_seed_digest()`, a 422 `source_digest_mismatch`); hub `tools/e2e/make_seed.py` writes it.
- Results name unstored files: `predictions.json`, `cleaned_lines.json`, `results.json` (`docs/rocrate_export.md`
  §5.2). _(11-12: an output that is not stored is named only if it reaches a stored distribution, and then marked,
  D23)_
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
issue with Ronald's consent (§8). Until then the reader's block types and field names are unknown. _(superseded
11-12: the schema is comment 1 of #84, summarised above)_

---
_Derived reading aid; the issue, the contract and the code are the source of truth._
