# Strategy — Issue [#84](https://github.com/ufal/atrium-project/issues/84): doc-schema-v2, the record and docproc contract after the 11 November meeting

> _**Refreshed 2026-11-14 (afternoon)** (round 6): #86 merged, the pins moved; the E2E lanes on the docproc route
> (task 7), rule 5's mark (Q16), rules 4 and 5, no object sampling, v2.0.0-beta (Status — round 6). Earlier:
> **refreshed 2026-11-14** (round 5): the seven PRs of 11-14 and their failing checks (Status — PRs); the crate
> root's `#no-licence-asserted` restored, as motyc confirmed on #6 on 11-12. Earlier: **refreshed 2026-11-13**
> (round 4): Kate's reply on #84 (posted 11-12), the status of the hub side, the tools and
> the push, Q11–Q15. The #84 files are named `doc-schema-v2.*` again (they were `84.*` on 11-12 and 11-13). Evidence:
> [`../digests/doc-schema-v2.digest.md`](../digests/doc-schema-v2.digest.md) · contract digest:
> [`../digests/project_state_1211.md`](../digests/project_state_1211.md). Each tool's slice is
> `<repo>/agent_dev_logs/plans/doc-schema-v2.plan.md`. Earlier: refreshed **2026-11-12** after motyc opened the issue
> on ARÚP's output contract of 12 November; written **2026-11-11** before the issue existed (one record built by
> every tool, one `run_uuid` per block, ALTO from the ATR, the D14 merge by decode verdict; superseded)._

**Status (2026-11-14, afternoon)**: 🟡 **#86 is merged (`2f6c82f`, also on `main`), `v1` moved to it and the six
tools are pinned to it. Round 6 completes the code that needs no outside answer: the E2E lanes on the docproc
route (task 7), rule 5's mark (`lines[].unit`, Q16), rules 4 and 5 in ocr-postprocess, no object sampling in
digital-convert, and v2.0.0-beta, unreleased, in every tool. Left: H6 (Q15), the coordinates (ask 10), Q6, Q9,
the DOCX rendering, the cluster run, then the tag.**

**Status (2026-11-14)**: 🟡 **K4TEL opened one PR per repository from `doc-schema-v2` into `test`: #86 here,
page-classification#71, translator#60, keyword-extract#5, nlp-enrich#45, digital-convert#10, ocr-postprocess#11.
Their checks fail for six reasons (Status — PRs). Round 5 fixes the code and the files the push missed; the
hub-ref pins move after #86 merges; the record-major check clears when each tool's release raises its major
version. Not tagged.** _(superseded 11-14 afternoon: #86 merged, round 6)_

**Status (2026-11-13)**: 🟡 **Kate answered on 11-12: points 1 and 2 agreed, with the stored docproc written by the
ATR (Q15). The hub and the six tools are adapted; the hub, page-classification, keyword-extract and digital-convert
are on `doc-schema-v2`, translator and ocr-postprocess on `test`, nlp-enrich not pushed yet. Ronald's answers on
ARUP-CAS/aiscr-docs-pipeline#17 are pending; `doc-schema-v2` is tagged only after the proof gate.** _(superseded
11-14: the PRs are open)_

**Status (2026-11-12)**: 🟡 **Opened by motyc; it takes over K4TEL's draft on #67. Due from Kate by 16 November:
agreement (or not) with the two-level contract and with dropping ALTO, which is also her consent as first author
for the paper revision (#13). A reply draft is below. Code starts after that answer and Ronald's on
ARUP-CAS/aiscr-docs-pipeline#17; `doc-schema-v2` is tagged only after the proof gate.** _(superseded 11-13: Kate
answered; the code is on branches)_

**Status (2026-11-11)**: 📋 Planned, not opened. _(superseded 11-12: opened as #84)_

## Goal

Two levels, each content only. **Layout:** one `atr/docproc-json` per document, written by digital-convert or the
ATR (ARÚP's schema, moved to aiscr-docs-pipeline). **Record:** `atrium/document-json`, its positional blocks built by
ocr-postprocess from docproc, then enriched block by block. Run data only in each distribution's paradata.
`doc-schema-v1` stays as published and cited.

## The changes

| #  | Change                                                                                                                                   | Decision         | Code owner                                       |
|----|------------------------------------------------------------------------------------------------------------------------------------------|------------------|--------------------------------------------------|
| 1  | No run data in the record: `provenance`, `assembled`, `derived_from`, `regenerable`, and no per-block `run_uuid`                         | D1 (extended)    | hub; every tool stops writing them               |
| 2  | No calculated licence and no licence merging, in the record, the paradata, a crate, the templates or the validator                       | D2               | hub `atrium_paradata.py`, `para_licenses.py`     |
| 3  | digital-convert writes docproc (lines, per-page verdict, `needs_atr`), never refuses, never samples                                      | D20, H12         | digital-convert                                  |
| 4  | ocr-postprocess builds every record from docproc; for a mixed document it merges two outputs (exact lines kept, linked to the ATR block) | D20, D21, H6, H8 | ocr-postprocess; hub (`replace_page_rows` goes)  |
| 5  | Layout stays in docproc: `tables[]`, `content.reading_order`, `lines[].group_id`, `lines[].style`, the page verdicts leave the record    | D26, D27         | hub; digital-convert, ocr-postprocess            |
| 6  | New line fields `block`, `text_source`, `bbox_precision`; `pages[].content_status`; a row for every page                                 | D16, D25, D29    | hub; ocr-postprocess                             |
| 7  | `page_index` on every page row; one coordinate space (CropBox, `/Rotate`, UserUnit; `canvas` in pt)                                      | H2, D28          | hub; ocr-postprocess; digital-convert in docproc |
| 8  | Scoring rules 1–8; `categ` five values only; the decode verdict a docproc line flag                                                      | D17, D18         | ocr-postprocess; digital-convert                 |
| 9  | No ALTO produced or stored; nlp-enrich's layout from the record or docproc                                                               | D24              | nlp-enrich; hub E2E                              |
| 10 | page-classification on the `needs_atr` pages only                                                                                        | H3, D33          | page-classification; the pipeline                |
| 11 | Paradata: distribution name and SHA-512; unstored inputs/outputs marked; `result` names blocks and fields; `actionStatus` kept           | D13, D23, §6     | hub `atrium_rocrate.py`; every service           |
| 12 | `forms` removed; `translations`, `entities[].translation_en` reserved                                                                    | D19              | hub; translator stops writing `translations`     |
| 13 | Translator: field list per request, no default, refusal without one                                                                      | D34              | translator                                       |
| 14 | A limit that trims, skips or stops content fails the job; sampling and splitting recorded                                                | D13              | hub `atrium_limits.py`; each tool                |

## The v2 record (§5 of the contract)

Writers per step as in [`project_state_1211.md` §3](../digests/project_state_1211.md#3--record-level-atriumdocument-json-5).
In short:

- **Top level:** `schema_version` `"2.0"`, `record_type`, `doc_id`, `source` (`sha512` required, `filename`,
  `media_type` from intake; `language`, `page_count`, `origin` from the builder), `page_categories`, `pages[]`,
  `content` (`text`), `lines[]`, `entities[]`, `enrichment`, `keywords`, `quality_summary`. Reserved: `translations`,
  `entities[].translation_en`.
- **`pages[]`:** `page_index` (required, = docproc `pageNumber`), `page` (label), `canvas` (`width`, `height`,
  `unit: "pt"`, UserUnit factor; image pixel ratio when docproc wraps an image), `content_status` (`text`, `empty`);
  `category`, `category_confidence` (page-classification, `needs_atr` pages); `quality_score`, `quality_band`
  (scoring; none on empty pages); `teitok_surface` (nlp-enrich).
- **`lines[]`:** `page`, `line` (1-based in reading order; the key), `text`, `bbox`, `block` (docproc block id),
  `text_source` (`text-layer`, `atr`, `legacy`), `bbox_precision` (`measured`, `derived`, `absent`); `categ`,
  `quality_score`, `lang` (scoring); `lemma`, `upos`, `feats`, `teitok_ref` (nlp-enrich).
- **Removed:** `provenance`, `assembled`, `derived_from`, `regenerable`, `forms`, per-block `run_uuid`, `tables[]`,
  `content.reading_order`, `lines[].group_id`, `lines[].style`, `pages[].text_layer`, `needs_ocr`,
  `needs_ocr_reason`, `ocr`, `source.sha256`.
- The field names `block`, `text_source`, `bbox_precision`, `content_status` are ARÚP's proposals; ÚFAL may rename
  them on #84.

Consumers that filter lines (nlp-enrich, keyword-extract) read `categ` only; `atrium_vocab.UNTRUSTWORTHY_LINE_CATEGORIES`
(`("Garbage", "Inverted", "Trash")`, `atrium_vocab.py:357`) keeps `Trash` only.

## docproc: what ÚFAL relies on (Ronald's asks, §11)

| Ask | Needed by                                                                                                                                                                       |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 3   | run data out of the output (or optional): the record builder reads content only                                                                                                 |
| 4   | routing lists every page, empty ones routed `empty`: H15's check in ocr-postprocess                                                                                             |
| 5   | forced pages echoed with the reason: digital-convert's `needs_atr` reaches the ATR (D27)                                                                                        |
| 7   | a line break per visual line in OCR blocks: rule 5 (a block scored as one unit otherwise)                                                                                       |
| 8   | the handwriting marker                                                                                                                                                          |
| 9   | an unread block or page fails (D13; `all_engines_failed`)                                                                                                                       |
| 10  | the coordinate space (D28)                                                                                                                                                      |
| 12  | `imageRef`/`imageData` not stored                                                                                                                                               |
| 13  | optional `lines[]` with box precision, the verdict and `needs_atr`, ODT/spreadsheet `sourceFormat`, the `pipeline` pattern opened: digital-convert can then write valid docproc |

## The paradata (version 3, §6)

One `CreateAction` per step: `@id` = `run_uuid`; `actionStatus` (always completed in what AMČR stores);
`instrument` (name, version, release link, image digest); `agent` (ROR id); times; `object` and `result` by
distribution name and SHA-512, the record version read, the record blocks **and fields** written; anything not
stored named by its SHA-512 and marked (D23); `parameters` that shaped the output (model revision, thresholds,
forced pages, the translator's field list); `limits` (sampled, split); `components` with their terms, never merged.
The files per step are in [`project_state_1211.md` §4](../digests/project_state_1211.md#4--paradata-and-the-hand-over-6).
The ÚFAL crate module keeps its building blocks (action, software, validator); AMČR builds the record's crate. A
root that asserts no licence names `#no-licence-asserted`: RO-Crate 1.2 requires a root `license`, and motyc
confirmed the placeholder on #6 on 11-12 ([comment](https://github.com/ufal/atrium-project/issues/6#issuecomment-6818590785)). _(Corrected 11-14: this line said
the placeholder goes; round 2 removed it, and #86's RO-Crate check failed.)_

## Tasks

**Hub (first; then re-vendored with `scripts/revendor_shared.sh`, `--check` in CI).** Paths in `docs/templates/shared/`:

1. `atrium_document.py`: `SCHEMA_VERSION = "2.0"` (73); `_migrate_1_to_2()` drops the run data, the layout fields
   and the page verdicts, renumbers 0-based lines from 1, maps `Garbage`/`Inverted` out of `categ`; `FREEZES[2]`;
   `atrium_document.schema.doc-schema-v2.json`; `_stamp()` (1360), `_provenance()` (1379), `OCR_HANDOFF` (449-450)
   and `replace_page_rows()` (924) go; field grants per §5 (the record builder owns the positional blocks).
2. `atrium_paradata.py` (`_license_block`, 235), `para_licenses.py` (`resolve_effective_license`, 136;
   `merge_effective_licenses`, 214): no licence block, rank or merge; the component registry stays as facts.
3. `atrium_rocrate.py`: `file_entity()` (612) with SHA-512 and the distribution name, a `stored: false` mark; no
   `ni_uri()` (479) for AMČR files; `result` with blocks and fields; `action_problems()` (730) checks the new shape.
4. `atrium_limits.py`: `EFFECTS` (65) — `trimmed`, `skipped`, `stopped` raise; `sampled`, `split` go to `limits`.
5. `atrium_vocab.py`: one line-category originator (`LINE_CATEGORY_ORIGINATORS`); the decode flag is docproc's.
   `atrium_service.py`: the `ocr_text_layer` error code (185-246) goes with digital-convert's refusal (H12); also
   in `docs/agent_skill_strategy.md:219` and `docs/k8s_deployment.md:245` (`OCR_LAYER_DOCUMENT_SHARE`).
6. Docs: `docs/document_schema.md` (register and changelog; the MAJOR-bump procedure at 485-495),
   `docs/paradata_schema.md`, `docs/rocrate_export.md`, and the pages that describe the order of the steps (#79).
7. E2E: `e2e-pipeline-smoke.yml` and `e2e-digital-smoke.yml` follow the route of §3; `fixtures/e2e/ALTO/` gives way
   to docproc fixtures (from comment 1's schema; a born-digital one from digital-convert, a scanned one in the
   ATR's shape); `tools/e2e/make_seed.py` keeps writing the seed.

**Tools** — each slice plan lists its own work and code:

| Repository          | Its part                                                                                                                                                                                                                               |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| digital-convert     | docproc with lines, verdicts and `needs_atr`; no refusal, no sampling; images skip it; the decode flag; paradata per H14; a page whose words lose letters left to scoring, office files rendered for page geometry (digital-convert#9) |
| ocr-postprocess     | the record builder (docproc reader, merge of two outputs, H15 check, `content` in reading order); scoring rules 1–8                                                                                                                    |
| nlp-enrich          | layout from the record or docproc, not ALTO; TEITOK's limits stated; one action in two paradata files                                                                                                                                  |
| page-classification | the `needs_atr` pages only; output unchanged; `page_index`; no `derived_from`                                                                                                                                                          |
| keyword-extract     | no run data; `result` names its blocks and fields; lines by `categ`                                                                                                                                                                    |
| translator          | field list per request, no default, refusal without one; `amcr-fields.txt` an example only; nothing in the record                                                                                                                      |

## Order of work

1. 11-12: the logs. Kate's answer on #84: given 11-12 (below).
2. Ronald's answers on aiscr-docs-pipeline#17 (asks 1–2 by 20 November; 3–13 after).
3. Hub shared modules and docs, one PR against #84.
4. ocr-postprocess (the builder and scoring) and digital-convert (the docproc producer), then the four others; one
   PR per repository, each referring to #84.
5. The E2E lanes on the new route with docproc fixtures; then the proof gate.

## Status — hub side (11-12)

Tasks 1–6 done on a local branch from `test` (pushed 11-13 as `doc-schema-v2`); task 7 in part. Hub tests 724
passed, shared 207 passed; the selftests pass; the RO-Crate validator runs in CI only (its context hosts are not
reachable here).

- **Record 2.0**: as §5, plus `_migrate_1_to_2()` (every reader takes a 1.x record), `written()` in place of the
  stamps, `RemovedInSchema2` from `add_derived_from()`, `add_regenerable()`, `add_license_detail()`.
- **Paradata 3.0, `para_licenses`, `atrium_limits`, `atrium_rocrate`**: as §6 and task 2–4; the crate root names no
  licence (`#no-licence-asserted` gone). _(Restored 11-14: see Status — PRs, cause A.)_
- **E2E**: `e2e_assert.py` and `rocrate_check.py` read every record and paradata file through the migration; new
  `--require-current-major` for the proof gate; `--expect-needs-ocr` kept as an alias of `--expect-atr-pages`.
  The workflows and the ALTO fixtures are unchanged until the tools adopt 2.0.
- **Deviations from the tasks above**:
  - no `FREEZES[2]` or `doc-schema-v2` copy yet: MAJOR 2 is in `PENDING_FREEZES` until the proof gate;
  - `ocr_text_layer` deprecated, not removed (a published reason code is never removed);
  - pages are keyed by `page_index` (H2); `source` is not required, so a standalone run stays valid (rule 3);
  - seeds carry no `schema_version`, so a 1.x and a 2.0 tool read the same seed;
  - `canvas.user_unit` and `pixel_ratio` are names this implementation proposes;
  - `Garbage`/`Inverted` kept as `atrium_vocab.DECODE_FLAGS`, a docproc line flag; the name is still open (Q5);
  - `fixtures/atrium_document.example.json` is a 2.0 record; the 1.x one is `atrium_document.v1.example.json`.
- **Next**: the PR against #84 waits for review (pushed to `doc-schema-v2` on 11-13, with the addendum below).

## Status — tools (11-13)

The six tools were adapted on local branches (one per repository, from `test`), on the re-vendored shared modules
with the hub addendum below, and delivered as one archive per repository (pushed 11-13; see Status — pushed). Per
tool, the detail and what is deferred are in its `plans/doc-schema-v2.plan.md`, "Status — round 2".

| Repository          | Done                                                                                                                 | Tests                      |
|---------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------|
| page-classification | page rows by `page_index`; paradata 3.0                                                                              | 873 passed (offline lane)  |
| translator          | the field list per request (D34); nothing in the record; D13; `metadata` → `metadata-en` paradata                    | 1160 passed (offline lane) |
| keyword-extract     | no run data; lines by `categ`; D13 (windows `split`, vocabulary budget `sampled`)                                    | 1014 passed                |
| nlp-enrich          | layout from the record (`block`, `bbox_precision`); per-line linguistic fields; TEITOK's limits stated               | 1085 passed                |
| digital-convert     | docproc 1.1 against comment 1's schema with asks 3 and 13; no refusal; decode verdicts as line flags; paradata (H14) | 959 passed                 |
| ocr-postprocess     | the docproc reader and the record builder (`POST /build_record`, one producer); every line scored; D13               | 2324 passed, 16 skipped    |

- **Hub addendum** (on `doc-schema-v2`): `atrium_service` answers `ContentLimitError` with `422 limit_exceeded`;
  `action_problems()` accepts an action with no `result` (a call that stores nothing); `e2e_assert.py` accepts
  nlp-enrich's `entities` on a 2.x born-digital record (1.x unchanged). Hub tests 933 passed, 50 skipped.
- **Local chain check, passed:**
  - the chain: a seed, digital-convert's docproc of `two_column.pdf`, `build_record.py`, nlp-enrich `/enrich` and
    keyword-extract's YAKE;
  - then `e2e_assert.py --require-current-major --expect-layout --seed --teitok-dir`;
  - where a file is passed on as written, each stage's input SHA-512 equals the previous stage's output; a service's
    response is re-serialized (Q12);
  - stand-ins: no models here, so a stub line classifier, and UDPipe and NameTag stood in as in nlp-enrich's tests.
- **Deferred:**
  - the merge of a mixed document (H6): a docproc with a `needsAtr` page fails the build;
  - scoring rule 4 (the service's page and document passes); _(done 11-14, round 6)_
  - digital-convert's coordinates (D28, ask 10) and its object cap: a page over 20,000 objects is still judged on
    its first ones; _(the cap gone 11-14, round 6; the coordinates still wait on ask 10)_
  - the E2E workflows on the docproc route (task 7): they wait for images built from these branches. _(written
    11-14, round 6; they run on images once the tools' `test` branches are merged)_
- **Proof gate:** the validator part holds in the tools' tests and the local chain; the E2E lanes and the cluster
  run do not yet.

## Status — pushed (11-13)

K4TEL pushed round 3 on 11-13: the hub, page-classification, keyword-extract and digital-convert to
`doc-schema-v2`; translator and ocr-postprocess to `test`; nlp-enrich not yet. Round 4 closes the gaps of the push:

- the addendum's shared files (`atrium_rocrate.py`, `service/atrium_service.py`) re-vendored in the five pushed
  tools;
- digital-convert: the docproc writer, its schemas, `tools/docproc_proposal.py` and their test, which the push left
  out (a conversion failed without the writer);
- ocr-postprocess: the docproc fixtures added, `tests/test_ocr_handoff.py` removed;
- digital-convert#9 points 1–3: a page whose words lose letters to unmapped glyphs is no longer sent to the ATR (its
  lines go to scoring), and `garbled` means a layer that does not decode;
- the hub's tests that read the sibling checkouts, run against these trees: ocr-postprocess and digital-convert
  declare their new modules in `.github/production-image.json` (`build_record.py`, `docproc.py`, `score_record.py`;
  `api_util/docproc_writer.py`), and the environment tables (`docs/k8s_deployment.md`, `docs_site/operations.md`)
  drop `AMCR_FIELDS_PATH` and `OCR_LAYER_DOCUMENT_SHARE`. Hub tests 933 passed.

The workflows' `hub-ref` pins still point at `v1`: `para-drift` fails until the hub PR merges and the pins move.

## Status — PRs (11-14)

K4TEL pushed round 4 and opened one PR per repository from `doc-schema-v2` into `test` (no review yet). Each failing
check traced to one of six causes:

| Cause | Where                                        | What fails                                                                                                                                                         | Fix                                                                                               |
|-------|----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| A     | #86, "Validate the RO-Crates"                | RO-Crate 1.2 rule 13.3: the root has no `license` (all four sample crates)                                                                                         | round 5: the root names `#no-licence-asserted` again (#6, motyc 11-12)                            |
| B     | #86, "Test canonical shared modules"         | the image-closure test reads ocr-postprocess's `test` head: `build_record.py`, `docproc.py`, `score_record.py` there, their declaration only in ocr-postprocess#11 | none: clears when ocr-postprocess#11 merges                                                       |
| C     | the six tool PRs, "check-drift (canonical)"  | the callers read the hub at `v1` (`4435ffb`); the tools' copies are v2, byte-identical with `doc-schema-v2`                                                        | after #86 merges: `v1` moves to the merge commit and `scripts/pin_hub_reusables.py --sha` pins it |
| D     | the six tool PRs, "api-contract"             | record schema 1.0 → 2.0 (digital-convert and ocr-postprocess also drop response fields) without a major version                                                    | each tool's release raises its major version (K4TEL, 11-14); `2.0.0-beta` passes                  |
| E     | ocr-postprocess#11, "build / test"           | `tests/fixtures/docproc/*.json` not committed; `tests/test_ocr_handoff.py` still there (imports `OCR_HANDOFF`, gone in 2.0)                                        | round 5: the fixtures added, the test removed                                                     |
| F     | digital-convert#10, "check-drift (vendored)" | the TEITOK pin names nlp-enrich `ba81709` (flexiconv v0.3.11); the copy pins v0.3.12                                                                               | round 5: the pin names `c9e94ee` (2026-11-10, flexiconv v0.3.12), which matches all 11 copies     |

Also missing from the push: digital-convert's `digests/9.digest.md`, and nlp-enrich's `api_2_udp.sh` lost its
exec bit. The hub's docs named a branch `84-doc-schema-v2` that does not exist; they now say the hub's `test`.

**Merge order.** 1. #86, with B the only red check. 2. `v1` to the merge commit; the six tools pinned to it
(`pin_hub_reusables.py --sha`, then `--check`), committed on each `doc-schema-v2`: C clears. 3. The six tool PRs,
with D red until each release. Checked locally: every tool's suite; the hub's tests with the round-5 tools as
siblings; the four sample crates through roc-validator 0.12.0 (0 issues at the gates); the pin sweep and
`workflow_lint.py --require-sha-pins` on copies of the six tools.

**At each tool's release** (D): `[tool] version` in `para_config.txt`, `version` in `CITATION.cff`, `info.version`
in `service/openapi.json`, and keyword-extract's vocabulary sidecars (`vocab_build.py --from-flat --skos`) move to
the new major.

## Status — round 6 (11-14)

After #86 merged, K4TEL moved `v1` to `2f6c82f` and pinned the six tools: drift went green on all six PRs. Hub
Self-Check still fails on cause B until ocr-postprocess#11 merges. The E2E runs on `main` failed on the old route:
the born-digital lane met digital-convert's v1 `:test` image, and the scanned lane's translator stage, still
translating ALTO full text, could not reach LINDAT. Round 6 (local, delivered as archives):

- **Hub, a second PR for #84:**
  - **Task 7, the E2E lanes on the docproc route.**
    - Born-digital: the `-digital` image writes docproc → `tools/e2e/docproc_assert.py` → ocr-postprocess's batch
      image builds the record → `e2e_assert.py --require-current-major`. The ATR cases are routed to the ATR, and
      `build_record` refuses them alone (`needs_atr`). The service case chains `/reformat` and `/build_record`.
    - Scanned: `tools/e2e/alto_to_docproc.py` wrote stand-ins in the ATR's shape (`fixtures/e2e/docproc/`). The
      chain is `build_record` → page-classification → nlp-enrich (`--text-from-record`) → keyword-extract; the
      translator left the chain.
    - Neither lane is scheduled any longer; a push runs `:test`.
    - Checked locally on the round-6 tool code: every case of both lanes and the record crate. The stand-ins
      were a scorer with the model's signals, a fixed page-classification answer, and a LINDAT stand-in, since
      LINDAT reset this session's connections.
  - **Rule 5's mark:** `lines[].unit: "block"` (record builder), kept out of the page score and of
    `quality_summary.lines.by_categ`, counted as `block_units`. It is additive within 2.0 (not frozen yet). Its
    name is proposed: Q16.
- **Tools:**
  - ocr-postprocess: rule 4 (the batch's `apply_document_postprocessing()` after scoring, in `build_record` and
    `/score_record`) and rule 5 (the mark, out of the page score);
  - ocr-postprocess and digital-convert: a PDF page is judged on all its objects (`PDF_OBJECT_CAP` and
    digital-convert's `IMAGE_CAP` gone). digital-convert's reader pin names ocr-postprocess's merge commit once
    #11 is merged.
  - every tool: re-vendored, `v2.0.0-beta` unreleased (para_config, CITATION.cff, spec, CONTRIBUTING; keyword-extract's
    vocabulary sidecars), so api-contract passes;
  - the four ocr-postprocess fixtures again (`git add -f`), nlp-enrich's exec bit (`--chmod=+x`), and
    translator's usage page link to its record section.
- **Checked:** hub 738 and shared 210 passed; the tools' suites (page-classification 876, translator 1163,
  keyword-extract 1017, nlp-enrich 1088, digital-convert 962, ocr-postprocess 2332); `compare` against each latest
  release: compatible at v2.0.0-beta.
- **Order:** this hub PR first, then `v1` and the pins again; ocr-postprocess#11; digital-convert's reader pin to
  ocr's merge commit, then #10 and the other four; a dispatch of both lanes on `:test`; the releases.

## Proof gate (D12)

`doc-schema-v2` is tagged only when all three hold: the validator accepts every tool's output and the migrated
fixtures; both E2E lanes pass on the new route; one document of each case — born-digital, mixed or scanned PDF,
image, and a converted PCSS document — has run through the assembled chain on the cluster. Not on review alone.

## Questions

The 11-11 list, answered by the contract of 12 November:

| 11-11                                | Now                                                                                                      |
|--------------------------------------|----------------------------------------------------------------------------------------------------------|
| Q1 per-block `run_uuid`              | none in the record; the paradata `result` names blocks and fields (D1)                                   |
| Q2 empty pages                       | no `pages[]` entry, every page in routing and in the record (D29, H15)                                   |
| Q3 ALTO                              | none produced or stored (D24); docproc is the input of the builder and nlp-enrich                        |
| Q4 docproc schema                    | on #84, comment 1                                                                                        |
| Q5 decode names; handwriting         | the decode verdict is a docproc line flag (rule 2), name open; the handwriting marker is ask 8 to Ronald |
| Q6 a model's input cut to its window | **open**; meanwhile a line over the perplexity window fails the run (ocr-postprocess)                    |
| Q7 a line that cannot be scored      | rule 1 scores every line; whether a failure to score fails the job: **open**                             |

New, for the next meeting (not posted):

- **Q8** — Who builds the PCSS converter and the page-geometry tool (§9)? ocr-postprocess holds the ALTO readers.
- **Q9** — CSV and TXT: the 11-11 logs had digital-convert read them (variant B); the contract names PDFs and office
  files only. Out of the pipeline, or a docproc with no geometry? _(11-13: in the pipeline, without the visual
  steps, straight to scoring — [digital-convert#9](https://github.com/ufal/atrium-digital-convert/issues/9#issuecomment-6838301982)
  point 4; still open: whether digital-convert writes them a docproc without geometry or ocr-postprocess reads them)_
- **Q10** — digital-convert's line-level docproc for a mixed document is not stored (H14): is its SHA-512 in the
  record builder's `object`, marked, enough to reproduce the merge, or does the ATR's docproc carry the kept lines?
- **Q11** — AMČR's distribution name for the original file. The tools name it `original` (one constant each) until
  AMČR says.
- **Q12** — The stored record's bytes. A tool names the record it wrote by SHA-512. A service returns the record as
  JSON, so the digest holds only if AMČR stores it as `DocumentRecord.finalize()` writes it: UTF-8,
  `ensure_ascii=False`, `indent=2`, no final newline (checked in the local chain). Fix that as the stored form, or
  have the services return the bytes?
- **Q13** — docproc has no page label. A born-digital PDF's labels (`i`, `ii`) are lost, and the builder labels
  pages by number. Ask Ronald for a label on the page (digital-convert can write it), or drop labels from the record?
- **Q14** — D35 in the pilot. On #78 Pavel asked to ignore LINDAT's Terms of Use unless told otherwise, and David
  agreed for now, with written terms needed for the production release
  ([comment](https://github.com/ufal/atrium-project/issues/78#issuecomment-6827422711)). Does D35 (outputs produced
  through LINDAT not published) still hold in the pilot? The tools' docs keep it until this is answered.
- **Q15** — Which docproc is stored. Kate's reply has the stored docproc written by the ATR; the contract stores
  digital-convert's docproc for a born-digital document (D20, H14), which round 3 implements. Is digital-convert's
  docproc ever stored?
- **Q16** — Rule 5's mark. A row holding a whole docproc block scored as one unit is marked `lines[].unit: "block"`
  and kept out of the page score and `quality_summary.lines.by_categ` (counted as `block_units`). The name is
  proposed by this implementation. Until the ATR keeps a line break per visual line (ask 7), a one-line heading
  cannot be told from a paragraph that lost its breaks, so both are marked.

## Reply on #84 (posted 11-12)

Posted by K4TEL on 11-12, 09:52 UTC ([comment 2](https://github.com/ufal/atrium-project/issues/84#issuecomment-6820372800)),
changed from the draft in two places:

- docproc is "written by ATR" (the draft: "by digital-convert or the ATR"): the stored docproc is the ATR's (Q15);
- the consent sentence became "I will also describe this shape in the paper revision under the gated wording on
  #13": Kate's part of #13's gate is given; Ronald's is pending.

## Done when

The changes are released in the shared modules and all six tools; the proof gate holds; the tag `doc-schema-v2`
exists and `doc-schema-v1` (`544298b`) is untouched.

## Boundaries

- Parked scope stays parked: decision models (#83 and children), Galaxy beyond the 30 September agreement,
  digital-convert's `/describe` in the pipeline, `forms`, full-text and ALTO translation.
- docproc's schema is ARÚP's (aiscr-docs-pipeline, D30); the ATR is ARÚP's; ÚFAL proposes, ARÚP decides.
- AMČR's crate, the import and the store step are AMČR's and the pipeline's (aiscr-webamcr, aiscr-docs-pipeline#13).
- LINDAT-produced outputs are not published until #78 is settled (D35; Q14 asks whether that holds in the pilot).

## History

- **11-11:** planned as `doc-schema-v2` after the meeting: one record built by every tool, one common line shape,
  a `run_uuid` per block, ALTO from the ATR, the page merge by decode verdict (D14), Q1–Q7; issue body drafted.
- **11-11 18:30:** K4TEL posted the draft on #67.
- **11-12:** ARÚP's contract of 12 November; motyc opened #84 from the draft, with the two-level contract.
- **11-12 09:52:** Kate's reply on #84 (see Reply).
- **11-12 (later):** the hub side implemented on a local branch (see Status — hub side).
- **11-13:** the six tools adapted, the hub addendum, a local chain check (see Status — tools).
- **11-13 (later):** pushed (see Status — pushed); the files named `doc-schema-v2.*` again; digital-convert#9
  points 1–3.
- **11-14:** round 4 pushed; the seven PRs opened; round 5 (see Status — PRs).
- **11-14 (afternoon):** #86 merged, `v1` moved, the tools pinned; round 6 (see Status — round 6).
