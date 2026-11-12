# 🔎 ATRIUM cross-repo state — the output contract of 12 November 2026

> _Supersedes [`project_state_1111.md`](project_state_1111.md) where they differ. Source: ARÚP's "ATRIUM output
> contract", version of 12 November 2026 (David Novák), written after the meeting of 11 November; it replaces the
> meeting document of 10 November and its comments. Statuses as the document gives them: *Agreed* (at the
> meeting), *Decided* (by ARÚP on 12 November), *To confirm*, *Deferred*. D1–D19 keep their numbers; D20–D36 are
> new. The record and docproc part is on [#84](https://github.com/ufal/atrium-project/issues/84) (motyc, 11-12).
> Nothing was changed on GitHub._

## §0 — What changed since 11-11

| Topic                 | 11-11 (our logs)                                                               | 12-11 (the contract)                                                                                                                        |
|-----------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| Route                 | digital-convert on every input; the route sends pages to OCR; page merge (D14) | digital-convert first on PDFs and office files; **any `needs_atr` page → the whole document through the ATR**, those pages forced (H4, H12) |
| Images                | digital-convert reads them                                                     | skip digital-convert; the record's page rows come from docproc's routing (H13)                                                              |
| page-classification   | every PDF and image, bundled with the ATR call                                 | only the pages that need ATR, beside the ATR (H3); an optional weak signal to the ATR, never routing (D33)                                  |
| Layout contract       | docproc is the ATR's output                                                    | **docproc is the layout contract of both producers**, digital-convert and the ATR; one stored per document (D20, D22)                       |
| Who builds the record | digital-convert (born-digital), ocr-postprocess (scans), merge by decode       | **ocr-postprocess builds every record from docproc**; for a mixed document it merges the two outputs (H6, D21)                              |
| ALTO                  | `atr/alto-xml` from another component                                          | **none produced or stored** (D24, D15 withdrawn); an export later if a consumer needs it                                                    |
| Run data              | one `run_uuid` per block                                                       | **none in the record**, not even per block; the paradata `result` names the blocks and fields each run wrote (D1 extended)                  |
| Layout in the record  | `tables[]`, `group_id`, `style`, page verdicts                                 | **stays in docproc**; each record line links to its docproc block (D26)                                                                     |
| Empty pages           | ATR skips them (open, Q2)                                                      | no `pages[]` entry in docproc, every page in its routing, a row for every page in the record (D29)                                          |
| Routing               | to the paradata                                                                | **stays in docproc as data** (D9: the label and confidence are a signal about the content)                                                  |
| Line quality          | every line scored                                                              | the target state: eight rules, one scale for every source (D18, §7)                                                                         |
| Translator            | field list with each job                                                       | with each request; **no default list**; metadata mode refuses a request without one (D34)                                                   |
| PCSS OCR              | parked                                                                         | the existing ALTO 3.1 converted **once** into docproc (D31)                                                                                 |
| LINDAT                | postponed                                                                      | deferred; outputs produced through LINDAT services are **not published** until #78 is settled (D35)                                         |

## §1 — The route (§3)

```text
original + seed (AMČR)
  → digital-convert: a verdict for every page (never refuses a document, never samples)
      ├─ no page needs ATR ──────────────────────────────────────────────┐
      └─ any page needs ATR → page-classification (those pages)          │
                            → ATR on the whole document, those pages forced
  → ocr-postprocess: builds the record from docproc (merges two outputs), scores every line
  → nlp-enrich → keyword-extract
  → store: validate; AMČR writes all outputs of the job in one transaction
record-level job, on archiving: translator → metadata-en
```

| #   | Hand-off rule (short)                                                                                                                                                                                                                              |
|-----|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| H1  | AMČR passes the original and the seed (file id, SHA-512, file name, media type); the cluster side chunks and renders (D3)                                                                                                                          |
| H2  | The physical page number is the join key: `pages[].page_index` = docproc `pageNumber`; printed labels stay in `pages[].page`                                                                                                                       |
| H3  | page-classification on the `needs_atr` pages, beside the ATR; categories into the record; optional weak signal to the ATR (D33). *Changed*                                                                                                         |
| H4  | digital-convert first; any `needs_atr` page → whole document through the ATR, those pages forced. *Changed*                                                                                                                                        |
| H5  | docproc's routing lists every page; empty pages have no `pages[]` entry (D29). *Changed*                                                                                                                                                           |
| H6  | Two docproc outputs: keep digital-convert's exact lines on good pages, link each to the ATR block that contains it; ATR lines for the `needs_atr` pages and for blocks with no digital-convert line (figure OCR, scanned inserts) (D21). *Changed* |
| H7  | ocr-postprocess scores every line (D17, D18)                                                                                                                                                                                                       |
| H8  | `content` is rebuilt in docproc's reading order; the record never holds partial text                                                                                                                                                               |
| H9  | An incomplete step fails the job, nothing is written (D13); an ATR failure on a mixed document fails the job, no fallback to digital-convert alone                                                                                                 |
| H10 | What an external service may receive is decided per job from its licence flag; the docproc cloud fallback is off in the pilot (D32)                                                                                                                |
| H11 | digital-convert's `/describe` has no role                                                                                                                                                                                                          |
| H12 | digital-convert opens every PDF and office file, gives a verdict for every page, never refuses, never decides from a sample; a page it cannot use is `needs_atr`. *New*                                                                            |
| H13 | Images skip digital-convert; the record's page rows come from docproc's routing. *New*                                                                                                                                                             |
| H14 | The stored docproc is digital-convert's if no page needs ATR, otherwise the ATR's (D22). *New*                                                                                                                                                     |
| H15 | ocr-postprocess checks that every page of the original is in docproc `pages[]` or routed empty; otherwise the job fails (D29). *New*                                                                                                               |

| Case                                     | Steps                                                                                                         | Stored docproc  |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------|-----------------|
| Born-digital PDF or office file, all pages usable | digital-convert → ocr-postprocess → nlp-enrich → keyword-extract                                     | digital-convert |
| Mixed or scanned PDF (any `needs_atr`)   | digital-convert → page-classification (`needs_atr` pages) + ATR (whole, forced) → ocr-postprocess (merge) → … | ATR             |
| Image                                    | page-classification + ATR → ocr-postprocess → …                                                               | ATR             |
| Existing PCSS OCR (one-off)              | PCSS converter → ocr-postprocess → …                                                                          | converter       |
| AMČR metadata record                     | translator → `metadata-en`, on archiving                                                                      | —               |

CSV and TXT, which the 11-11 logs listed as digital-convert inputs (variant B), are not named by the contract.

## §2 — Layout level: `atr/docproc-json` (§4)

The schema becomes ARÚP's versioned contract under an ARUP-CAS identifier, kept in `aiscr-docs-pipeline`; Ronald and
ÚFAL propose, ARÚP decides (D30, to confirm by Ronald). Ronald's schema of 10 November is on #84, comment 1. The
`atr/` prefix names the text-workflow family; the producer is named in the paradata.

| Part                                                                                                   | As stored                                                                                                                                                                                            |
|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| producer                                                                                               | digital-convert, the ATR, or the PCSS converter                                                                                                                                                      |
| `version`, `sourceFormat`, `documentLanguage`                                                          | stay; `sourceFormat` gains ODT and spreadsheets                                                                                                                                                      |
| `metadata.routing`                                                                                     | stays; one entry for every page; for the ATR, the forced pages with `forced` and `forced_reason` (D27)                                                                                               |
| `readingOrderExtensions`, `crossPageClusters`                                                          | results stay; thresholds (`minConfidence`, `proximityPt`, `runCount`) to the paradata                                                                                                                |
| `pipeline`, `pipelineVersion`, `processedAt`, `sourceFile`, `sourceHash`, fallback details, `warnings` | paradata, or optional in the schema and written to paradata only (D9); the original named by its SHA-512                                                                                             |
| `all_engines_failed`                                                                                   | fails the job (to confirm with Ronald)                                                                                                                                                               |
| page                                                                                                   | `pageNumber`, `width`, `height`, `language`, `renderDpi`, the text-layer verdict (`digital`, `garbled`, `ocr`, `none`, `blank`), `needs_atr`, the UserUnit factor, the wrap ratio of images; unit pt |
| block                                                                                                  | as today, at paragraph level; plus optional `lines[]` (and words) with text, box and box precision; the handwriting marker                                                                           |
| `imageRef`, `imageData`                                                                                | not stored; a figure is cut again from the original by bbox and `renderDpi`; the ATR's ZIP and digital-convert's Markdown are development outputs                                                    |

## §3 — Record level: `atrium/document-json` (§5)

No run data and no copy of the layout (D1, D26). Released by ÚFAL as `doc-schema-v2` once proven; `doc-schema-v1`
stays (D12). The new field names are proposals for ÚFAL.

| Step                             | Fields it writes                                                                                                                                                                                                                                                                                                                                        |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| intake (pipeline)                | `schema_version`, `record_type`, `doc_id` (AMČR file id), `source.sha512`, `source.filename`, `source.media_type`                                                                                                                                                                                                                                       |
| record builder (ocr-postprocess) | `source.language`, `source.page_count`, `source.origin` (descriptive: `digital`, `atr`, `legacy`); `pages[]`: `page_index`, `page`, `canvas`, `content_status` (`text`, `empty`); `lines[]`: `page`, `line`, `text`, `bbox`, `block`, `text_source` (`text-layer`, `atr`, `legacy`), `bbox_precision` (`measured`, `derived`, `absent`); `content.text` |
| page-classification              | `page_categories`; `pages[].category`, `category_confidence` for the pages that needed ATR                                                                                                                                                                                                                                                              |
| scoring (ocr-postprocess)        | `lines[]`: `categ`, `quality_score`, `lang`; `pages[]`: `quality_score`, `quality_band`; `quality_summary`                                                                                                                                                                                                                                              |
| nlp-enrich                       | `lines[]`: `lemma`, `upos`, `feats`, `teitok_ref`; `pages[].teitok_surface`; `entities[]`                                                                                                                                                                                                                                                               |
| keyword-extract                  | `enrichment`; `keywords`; `entities[].pid`                                                                                                                                                                                                                                                                                                              |
| store (pipeline)                 | nothing; validation against `doc-schema-v2`                                                                                                                                                                                                                                                                                                             |
| **removed**                      | `provenance`, `assembled`, `derived_from`, `regenerable`, `forms`, any per-block `run_uuid`, `tables[]` (docproc's `cellGrid`; its text stays as lines), `content.reading_order`, `lines[].group_id`, `lines[].style`, `text_layer`, `needs_ocr`, `needs_ocr_reason`, `ocr`                                                                             |
| **reserved, not in the pilot**   | `translations`, `entities[].translation_en`                                                                                                                                                                                                                                                                                                             |

**One coordinate space (D28, to approve by Ronald and ÚFAL).** Every box, in docproc and in the record: origin at
the top-left of the CropBox, after `/Rotate`, in units of 1/72 inch × UserUnit. `canvas` carries the UserUnit factor
and, for images docproc wraps into a PDF, the ratio back to the image's pixels; its default unit becomes pt. PCSS
pages whose original cannot be matched may stay in px.

## §4 — Paradata and the hand-over (§6)

One schema.org `CreateAction` per step, RO-Crate 1.2 / Process Run Crate 0.5; each file describes the run that
produced the current version of its distribution (earlier runs: Fedora/OCFL history).

| Member         | What it holds                                                                                                                    |
|----------------|----------------------------------------------------------------------------------------------------------------------------------|
| `@id`          | the run's `run_uuid`                                                                                                             |
| `actionStatus` | kept; in what AMČR stores always completed (D13); development and tests use the same frame                                       |
| `instrument`   | name, version, release link, container image digest                                                                              |
| `agent`        | the operating organisation (ROR id)                                                                                              |
| `object`       | inputs by distribution name and SHA-512, the record version read; an input not stored named by SHA-512 and marked (D23)          |
| `result`       | outputs by distribution name and SHA-512; for the record, the blocks **and fields** written; a result not stored is marked (D23) |
| `parameters`   | only what shaped the output: model revision, thresholds, forced pages, the translator's field list                               |
| `limits`       | sampling and splitting notes                                                                                                     |
| `components`   | each component with version and terms; facts, never combined into a licence (D2)                                                 |

| Step                | Paradata file                                                                                                                  | Inputs                                              | Outputs                                                |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|--------------------------------------------------------|
| digital-convert     | `paradata/atr/docproc-json` when its docproc is stored; otherwise in `paradata/atrium/document-json`, result marked not stored | the original                                        | `atr/docproc-json`                                     |
| ATR                 | `paradata/atr/docproc-json`                                                                                                    | the original, the forced pages                      | `atr/docproc-json`                                     |
| PCSS converter      | `paradata/atr/docproc-json`                                                                                                    | PCSS ALTO, the original, the page geometry (marked) | `atr/docproc-json`                                     |
| page-classification | `paradata/atrium/document-json`                                                                                                | the original (pages)                                | record: `page_categories`, `pages`                     |
| record builder      | `paradata/atrium/document-json`                                                                                                | `atr/docproc-json`, the seed                        | record: `source`, `pages`, `lines`, `content`          |
| scoring             | `paradata/atrium/document-json`                                                                                                | the record version                                  | record: `lines`, `pages`, `quality_summary`            |
| nlp-enrich          | `paradata/atrium/document-json` and `paradata/atr/teitok-xml` (one action)                                                     | the record version, `atr/docproc-json`              | record: `lines`, `pages`, `entities`; `atr/teitok-xml` |
| keyword-extract     | `paradata/atrium/document-json`                                                                                                | the record version                                  | record: `enrichment`, `keywords`, `entities`           |
| translator          | `paradata/metadata-en`                                                                                                         | `metadata` (SHA-512)                                | `metadata-en`                                          |

**Hand-over:** one list of outputs per file job and one per record-level job (distribution, SHA-512, media type,
paradata). A file job always carries `atr/docproc-json`, `atrium/document-json`, `atr/teitok-xml` and their paradata;
there is no `atr/alto-xml`. The pipeline validates, AMČR validates and writes in one transaction or not at all; a
distribution whose SHA-512 a rerun did not change is kept with its paradata (aiscr-docs-pipeline#13).

## §5 — Line quality (§7, D18)

ocr-postprocess alone writes `categ` and `quality_score`. Target state:

1. Every line in the record is scored, whatever its text source.
2. `categ` holds only Clear, Noisy, Trash, Non-text, Empty; digital-convert's decode verdict (`Garbage`, `Inverted`)
   becomes a flag on docproc lines that scoring may read; flagged lines are no longer skipped.
3. `quality_score` from the text alone: one model, one set of constants, one band scheme for every source; the
   producer's confidence stays in docproc.
4. The pipeline gets the document passes (the page-context corrections) the evaluated batch runs.
5. The unit is a visual line; if the ATR's blocks keep no line breaks, the block is scored as one unit, marked, and
   kept out of calibrated statistics until rule 8.
6. `Trash` triggers no re-route; re-processing is a later campaign.
7. Empty pages carry no lines and no page score; `quality_summary` counts them separately.
8. Frozen for the pilot; validity on ATR and text-layer text measured on documents with both PCSS lines and an ATR
   run, before the production version is fixed.

## §6 — Translator, licences, LINDAT, RO-Crate (§8)

- `metadata-en` is a record-level job run on archiving (aiscr-docs-pipeline#13). The field list is AMČR's and comes
  **with each request**; no default list; metadata mode refuses a request without one; the list used is in
  `paradata/metadata-en`, with no field text and no per-field log (D34).
- Protected fields may go to LINDAT (a secure service); `metadata-en` follows the access rules of `metadata`; fields
  not translated are copied unchanged, so the Digital Archive serves `metadata-en` under the same protection (D36).
- Full-text translation stays a later decision; the translator README does not present ALTO or full-text
  translation as part of the pipeline.
- **Licences, three layers, nothing computed:** (1) rights in the content: the document's own licence, otherwise
  AMČR's default CC BY-NC 4.0, inherited by derived outputs, shown in the record's RO-Crate, the File API
  (`Link rel="license"`), the Digital Archive, OAI and ARIADNE; (2) produced with: each step's components and terms
  in its paradata, never merged; (3) AMČR conditions, stated with their reason.
- **LINDAT (#78), deferred** to the next meeting with Pavel: all of nlp-enrich (UDPipe, NameTag) and the translator;
  until settled, the linguistic layer, entities, TEITOK and `metadata-en` are not published (D35).
- **RO-Crate:** AMČR builds the crate of each archived record; ÚFAL's single-record crate is not AMČR's, but its
  building blocks (action and software descriptions, the validator) are reused; block entities and
  machine-derived terms stay out of the archival crate.

## §7 — Existing PCSS OCR (§9)

ALTO 3.1 (ABBYY FineReader Server 14) for the 113,101 documents of the CAA paper is converted once into docproc
(D31): a separate tool reads the page boxes of each original into a list keyed by the AMČR file id and SHA-512;
a converter turns ALTO plus that list into docproc (lines and words with measured positions, `PHYSICAL_IMG_NR` as
the page number, ABBYY among the components). Unmatched originals keep px. The converter meets the full contract,
so its output can form the first stored pilot batch where the ATR re-run has not landed; documents with both PCSS
lines and an ATR run are the benchmark for line quality (rule 8), the coordinate space and the two producers'
consistency. The contract does not name who builds the converter.

## §8 — Decisions D1–D36

| #   | Decision (short)                                                                                                 | Status                             |
|-----|------------------------------------------------------------------------------------------------------------------|------------------------------------|
| D1  | Record has its own paradata; no run data, not even a per-block `run_uuid`                                        | Agreed; extended 12 Nov            |
| D2  | No calculated licence anywhere                                                                                   | Agreed                             |
| D3  | AMČR passes only the original and the seed                                                                       | Agreed                             |
| D4  | Mixed PDFs keep their born-digital text in the pilot (how: D20, D21)                                             | Agreed in general; how changed     |
| D5  | Own ATR on the AIS CR cluster is the main OCR route; PCSS secondary; digital-convert preferred where it suffices | Agreed                             |
| D6  | The stage matrix                                                                                                 | Superseded by D20                  |
| D7  | `atr/json` renamed `atr/docproc-json`                                                                            | Agreed                             |
| D8  | docproc is the layout contract                                                                                   | Changed by D20                     |
| D9  | Run data to paradata; routing stays in the output as data                                                        | Agreed; routing changed            |
| D10 | Engine-neutral data contract; PCSS probably never produces docproc                                               | Agreed                             |
| D11 | Gaps in the docproc schema                                                                                       | Superseded by §11 asks             |
| D12 | Record schema changed natively, released as `doc-schema-v2` once proven                                          | Agreed; Kate's draft to polish     |
| D13 | A failed job writes nothing; `actionStatus` kept; reruns full-chain; unchanged distributions kept                | Agreed; details 12 Nov             |
| D14 | The route decides which pages go to OCR                                                                          | Superseded by H4, D21              |
| D15 | ALTO produced inside the ATR tool                                                                                | Withdrawn                          |
| D16 | Line boxes written by the record builder, precision marked                                                       | Decided 12 Nov                     |
| D17 | Every line is scored                                                                                             | Agreed                             |
| D18 | One owner of `categ` and `quality_score`; target state §7                                                        | Agreed; target 12 Nov              |
| D19 | `forms` removed                                                                                                  | Agreed                             |
| D20 | Two levels: docproc the layout contract of digital-convert and the ATR; ocr-postprocess builds the record        | Decided; to confirm (Ronald, ÚFAL) |
| D21 | The merge keeps exact lines and takes the layout from docproc                                                    | Decided 12 Nov                     |
| D22 | One stored docproc per document                                                                                  | Decided 12 Nov                     |
| D23 | Inputs not stored are named and marked in the paradata                                                           | Decided 12 Nov                     |
| D24 | No stored ALTO; an export only if a consumer needs it                                                            | Decided; to confirm (Ronald, ÚFAL) |
| D25 | Each record line states its text source and box precision                                                        | Decided 12 Nov                     |
| D26 | Layout in docproc; the record links lines to blocks                                                              | Decided 12 Nov                     |
| D27 | The page verdict lives in the stored docproc's routing; `needs_ocr` → `needs_atr`                                | Decided; ATR echo to confirm       |
| D28 | One coordinate space                                                                                             | Decided; to approve (Ronald, ÚFAL) |
| D29 | Empty pages: no `pages[]` entry, every page in routing and in the record                                         | Agreed; details 12 Nov             |
| D30 | The docproc schema lives in aiscr-docs-pipeline under an ARUP-CAS identifier                                     | Decided; to confirm (Ronald)       |
| D31 | Existing PCSS OCR converted once into docproc                                                                    | Decided 12 Nov                     |
| D32 | docproc cloud fallback off in the pilot                                                                          | Decided 12 Nov                     |
| D33 | Page categories an optional weak signal for the ATR                                                              | Decided; for Ronald to consider    |
| D34 | Translator gets its field list with each request; no default list                                                | Decided 12 Nov                     |
| D35 | LINDAT-produced outputs not published until #78 is settled                                                       | Decided 12 Nov                     |
| D36 | Digital Archive serves `metadata-en` under the same protection as `metadata`                                     | Decided 12 Nov                     |

## §9 — Open items (§11)

**Ronald** (ARUP-CAS/aiscr-docs-pipeline#17; 1–2 by 20 Nov): (1) no ALTO, docproc the stored layout; (2) docproc
the shared contract, schema moved under an ARUP-CAS `$id`; (3) run data to paradata or optional; routing stays;
(4) routing covers every page, empty ones routed `empty`; (5) `/convert` takes the forced pages and echoes them with
the reason; (6) page categories as a weak signal; (7) do OCR blocks keep a line break per visual line; (8) the
handwriting marker; (9) an unread block or page fails; (10) the coordinate space; (11) cloud fallback off, a
fallback page fails; (12) `imageRef`/`imageData` not stored; (13) additive changes: optional `lines[]` with box
precision, the verdict and `needs_atr`, more `sourceFormat` values, the `pipeline` pattern opened. The schedule
(public code in November–December, which steps first) goes to aiscr-docs-pipeline#15.

**ÚFAL (Kate)**, on #84 (1 by 20 Nov in the contract; #84 asks by **16 Nov**): (1) confirm the two-level contract
and dropping ALTO, and consent as first author for the paper revision; (2) digital-convert writes docproc,
ocr-postprocess builds the record, `source.origin` descriptive; (3) the record shape of §5; (4) the paradata of §6;
(5) line quality §7; (6) translator field list per request, refusal without one; (7) nlp-enrich's layout from the
record or docproc, #24's three-format decision revised; (8) no calculated licence, components with terms, `forms`
removed; (9) the docproc schema as the contract the record aligns to.

**Other:** LINDAT terms (#78) next meeting with Pavel. TrueOpen.AI: option B agreed — parked in the pilot phase,
ask why they want it; non-commercial use only; no archival images beyond the published dataset without ARÚP's
decision; Kate answers them. INRIA: Dana asks about the LaDaS-based segmentation model. Noted for later: a LaDaS
segmentation model (aiscr-management#154) inside the ATR's layout segmentation (the ATR repository); an ALTO export
from the stored docproc (D24).

**CAA paper (§13):** revised to the current shape before it closes on 30 November; method = the workflow agreed
for the pilot, implementation status = today with record contract v1; passages depending on D20/D24 final only
after Ronald's and Kate's confirmations, otherwise a short mention; entered by a human author in Overleaf's
suggestion mode. motyc's R1–R16 on #13 (11-12) carry this out.

## §10 — Issue map

| Issue                                            | What 12 November changes                                                                                    | Log                                           |
|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| #84 doc-schema-v2 (opened 11-12)                 | the consolidated record and docproc issue; Kate's answer by 16 Nov                                          | [`../plans/84.plan.md`](../plans/84.plan.md)  |
| #13 CAA paper                                    | R1–R16 supersede C1–C9; [GATED] passages wait for 16 Nov                                                    | `plans/13.plan.md`, `plans/13.corrections.md` |
| #16 storage locations                            | public AMČR copies in keyword-extract and digital-convert not approved; Figure 3 approved; Galaxy condition | `plans/16.plan.md`                            |
| #78 LINDAT                                       | deferred; covers all of nlp-enrich and the translator; nothing published meanwhile (D35)                    | `plans/78.plan.md`                            |
| #24 LLM applications                             | the three-format decision revised: no ALTO                                                                  | `plans/24.plan.md`                            |
| #6 licences                                      | D2 unchanged; D35, D36                                                                                      | `plans/6.plan.md`                             |
| #67, #77                                         | #84 takes over the draft on #67; D35 on the pilot outputs                                                   | `plans/67.plan.md`, `plans/77.plan.md`        |
| #79 docs, #66 Galaxy, #22 document understanding | the order of the steps; the Galaxy test-data condition; layout and tables in docproc                        | each `plans/{n}.plan.md`                      |
| #83 and its children; #81, #40, #72              | unchanged since 11-11 (parked; CI and PR rules; can close)                                                  | as on 11-11                                   |
| Each tool                                        | its slice of #84                                                                                            | `<repo>/agent_dev_logs/plans/84.plan.md`      |
