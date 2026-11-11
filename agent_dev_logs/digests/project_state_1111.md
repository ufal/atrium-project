# 🔎 ATRIUM cross-repo state — the output contract of 11 November 2026

> _Supersedes [`project_state_0411.md`](project_state_0411.md) where they differ. Source: ARÚP's draft "ATRIUM
> output contract" of 10 November (David Novák), read and commented in the meeting of 11 November 14:00, and K4TEL's
> clarifications in session the same evening. The minutes are ARÚP's; this file is the working digest the issue
> logs link to. Repositories read on 11-11 at their heads of 11-09 and 11-10. Nothing was changed on GitHub._

## §0 — What changed

- **The record loses its run data** (D1, D2): `provenance`, `assembled`, `derived_from`, `regenerable` and the
  calculated licence leave `atrium/document-json`; it keeps its content, its identity and one `run_uuid` per block.
  The record gets its own paradata file, `paradata/atrium/document-json`.
- **One common line representation** (K4TEL): every tool reads and writes `lines[]` in one shape; today the row is
  split by field across four tools, numbered from 0 or 1, and boxed by one tool only. This is the core of
  doc-schema-v2 ([`../plans/doc-schema-v2.plan.md`](../plans/doc-schema-v2.plan.md)).
- **SHA-512 and distribution names** identify every input and output in the paradata; `ni:///sha-256` identifiers
  and unstored files go.
- **Licences: three layers, nothing computed** (below).
- **The ATR step is part of the contract:** its product is `atr/docproc-json` (D7, D8, D10); its run data go to its
  paradata (D9).
- **Order of the steps** (below): digital-convert first on every input; the route is the pipeline's step; page
  classification is bundled with the ATR call; ocr-postprocess right after ATR.
- **A failed or trimmed step writes nothing to AMČR** (D13).
- **The pilot is a phase**, in which the chain is assembled step by step; the release set of #77 is its starting
  point, and a step takes a newer release once it is proven (§6 of the contract). It is a stage of ATRIUM, not its
  end.
- **Parked during the pilot phase:** decision models (#83 and its children), Galaxy work beyond the 30 September
  agreement (between ÚFAL and Mark), digital-convert's `/describe` inside the pipeline, the `forms` block.
- **Working agreement** (§4.2): one thing at a time; questions batched for the meetings, with a week or two to
  answer; one PR per issue, squash-merged, no direct pushes to main branches; deliberate releases with notes (about
  one per tool every one or two weeks); CI on pull requests and releases only, security updates excepted; no tasks
  assigned without asking; requests to ARÚP and ARÚB staff go through David Novák.

## The order of the steps

1. **Intake (pipeline).** AMČR passes the original and the seed: `doc_id` (the AMČR file id), SHA-512, file name,
   media type. Chunking and page rendering happen on the cluster side (D3, H1).
2. **digital-convert, on every input** (PDF, office files, images, CSV/TXT). It checks each page's text layer,
   extracts the text it can, and describes the visual elements; the JSON record and the Markdown view carry the same
   content and are interchangeable. It calls no other tool (H11).
3. **Route (pipeline).** From the text-layer verdicts, the page categories and the job's licence flag, it decides
   which pages go to OCR: no text layer, a layer that does not decode, an earlier OCR layer; scanned PDFs and images
   whole (H4, H10). A refusal by digital-convert of a document that is mostly an earlier OCR layer means "OCR it".
4. **page-classification with ATR**, bundled at the AIS CR's ATR service. The classifier runs on every PDF and image
   (K4TEL, 11-11), without ATR when no page needs OCR; its categories are hints, not gates (H3). ATR is OCR with
   layout segmentation and HTR for readable handwriting; it returns `atr/docproc-json` (blocks with region boxes, in
   reading order) and `atr/alto-xml`.
5. **ocr-postprocess** builds the record of a scanned document from docproc, or merges the route's OCR pages into
   the born-digital record: OCR lines replace only the lines that do not decode; `content` is rebuilt (D14, H6, H8).
6. **ocr-postprocess scoring:** every line on every origin; the only writer of `categ`, `quality_score`, `lang` and
   page quality (D17, D18).
7. **nlp-enrich**, then **keyword-extract**.
8. **Store (pipeline):** validate, hand AMČR one list of outputs per job (distribution, SHA-512, media type,
   paradata); AMČR writes them in one transaction (aiscr-docs-pipeline#13).

**Separate record-level job:** the translator turns the `metadata` XML into `metadata-en` (aiscr-docs-pipeline#13
gets the job type). Full-text and ALTO translation stay a later decision.

| Variant | What digital-convert finds                                         | Steps                                             |
|---------|--------------------------------------------------------------------|---------------------------------------------------|
| A       | Born-digital PDF or office file; the text decodes on every page    | 2 → (4: classification only, for a PDF) → 6 → 7   |
| B       | Text without a visual part (CSV, TXT)                              | 2 → 6 → 7                                         |
| C       | Scanned PDF or image (no text layer, or only an earlier OCR layer) | 2 → 3 → 4 (all pages) → 5 (build) → 6 → 7         |
| D       | Mixed PDF                                                          | 2 → 3 → 4 (the route's pages) → 5 (merge) → 6 → 7 |
| E       | An AMČR metadata record                                            | translator only → `metadata-en`                   |

## The ATR step (answers given in the meeting's comments, and K4TEL)

| Question (§7 of the contract) | Answer                                                                                                                                                                                           |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 Lines and words             | No. A block is a region of text; word-level accuracy is out of the question (K4TEL).                                                                                                             |
| 5 One entry per page          | "Empty are skipped without record" — this conflicts with H5 (question Q2 below).                                                                                                                 |
| 6 Images                      | Optional: a ZIP of Markdown and images, the JSON referring to the images.                                                                                                                        |
| 8 Handwriting                 | Yes, and the type is recorded (handwritten vs typed). HTR serves ordinary readable text; handwritten identifiers, technical notes and signatures are usually misrecognised as gibberish (K4TEL). |
| 9 ALTO                        | Produced by another component; positions at block level only (rows relatively good, not very reliable).                                                                                          |
| 10 Page list                  | Open: ATR can decide from layout and text layer, but digital-convert's signals help; the hand-off is explored in practice.                                                                       |
| 11 Cloud fallback             | Optional; activates only when needed (H10: decided per job).                                                                                                                                     |
| 12 Plan                       | The full code public in November/December.                                                                                                                                                       |
| 2, 3, 4, 7                    | Not answered in the comments; "to be checked by Ronald in detail" (§5.4).                                                                                                                        |

nlp-enrich (comment 4): consider docproc as the primary input, to skip producing an artificial ALTO.

## Licences — three layers, nothing computed

1. **Rights in the content:** the document's own licence, otherwise AMČR's default CC BY-NC 4.0; derived outputs
   inherit it. Stored only in the RO-Crate of the AMČR record (`File.license`), which AMČR builds.
2. **Produced with:** each step's components — software, models, datasets, services — with their versions and terms,
   listed in that step's paradata, one paradata action per step and document; never merged into one licence.
3. **AMČR conditions:** what AMČR decides to honour (for example from the LINDAT terms), with its reason.

The ÚFAL crate of one record is not AMČR's crate; its building blocks are reused (the action, the software
entities, the validator). LINDAT's terms (#78) were postponed: Pavel was absent.

## Paradata — one action per step

`@id` = `run_uuid`; `instrument` (software, version, release link, image digest); `agent` (ROR id); `startTime`,
`endTime`; `object` and `result` by distribution name and SHA-512, plus the record version read and the blocks
written, stored outputs only; `parameters` that shaped the output; `limits` (sampling and splitting); `components`
(facts). Each paradata file describes the run that produced the current version of its distribution.

| Step                       | Paradata file                                              | Inputs                                                   | Outputs                                                 |
|----------------------------|------------------------------------------------------------|----------------------------------------------------------|---------------------------------------------------------|
| page-classification        | `paradata/atrium/document-json`                            | the original                                             | record: `page_categories`, `pages`                      |
| digital-convert            | `paradata/atrium/document-json`                            | the original, the previous record version                | record: `source`, `pages`, `content`, `lines`, `tables` |
| ATR                        | `paradata/atr/docproc-json`, `paradata/atr/alto-xml`       | the original, the route's pages                          | `atr/docproc-json`, `atr/alto-xml`                      |
| ocr-postprocess, OCR route | `paradata/atrium/document-json`                            | `atr/docproc-json` or `atr/alto-xml`, the record version | record: `pages`, `lines`, `content`                     |
| ocr-postprocess, scoring   | `paradata/atrium/document-json`                            | the record version                                       | record: `lines`, `pages`, `quality_summary`             |
| nlp-enrich                 | `paradata/atrium/document-json`, `paradata/atr/teitok-xml` | the record version                                       | record: `lines`, `pages`, `entities`; `atr/teitok-xml`  |
| keyword-extract            | `paradata/atrium/document-json`                            | the record version                                       | record: `enrichment`, `keywords`, `entities`            |
| translator                 | `paradata/metadata-en` (no field text)                     | `metadata`, the AMČR field list                          | `metadata-en`                                           |

## Questions batched for the next meeting

Not posted on GitHub (working agreement); collected in [`../plans/doc-schema-v2.plan.md`](../plans/doc-schema-v2.plan.md#questions-for-the-next-meeting).
Answers ÚFAL can already give:

- **Which unit do digital-convert's lines use?** pt, top-left origin, from pdfplumber
  (`api_util/digital_pdf.py:495-511`); office files carry no boxes.
- **Does the translator service take the field list per request?** Not today: it loads the XPaths once at startup
  from `AMCR_FIELDS_PATH` (`service/api.py:332,472`); the CLI takes `--xpaths`.

## Issue map

| Issue                                                                                    | What the meeting changes                                                    | Log                                                                |
|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------|
| doc-schema-v2 (to be opened)                                                             | §8 changes 1–11, the common line representation, SHA-512, docproc alignment | [`../plans/doc-schema-v2.plan.md`](../plans/doc-schema-v2.plan.md) |
| #13 CAA paper                                                                            | minimal corrections C1–C9 and K4TEL's points                                | [`../plans/13.corrections.md`](../plans/13.corrections.md)         |
| #6 licences                                                                              | three layers; nothing computed                                              | `plans/6.plan.md`                                                  |
| #77 pilot handover                                                                       | the pilot is a phase; the set is its starting point                         | `plans/77.plan.md`                                                 |
| #78 LINDAT                                                                               | postponed; protected fields may go to LINDAT                                | `plans/78.plan.md`                                                 |
| #83 and digital-convert#8, ocr-postprocess#10, keyword-extract#3, page-classification#58 | parked                                                                      | each `plans/{n}.plan.md`                                           |
| #66 Galaxy                                                                               | parked beyond the 30 September agreement                                    | `plans/66.plan.md`                                                 |
| #72, #67                                                                                 | #72 can close; #67 follows                                                  | `plans/72.plan.md`, `plans/67.plan.md`                             |
| #81, #40                                                                                 | event-driven CI; one PR per issue, squash, no direct pushes                 | `plans/81.plan.md`, `plans/40.plan.md`                             |
| #79                                                                                      | the docs that describe the old order                                        | `plans/79.plan.md`                                                 |
| #22                                                                                      | `forms` removed (D19)                                                       | `plans/22.plan.md`                                                 |
| digital-convert#5, keyword-extract#2, ocr-postprocess#4                                  | superseded statements marked                                                | in each repository                                                 |
| Each tool                                                                                | its slice of doc-schema-v2                                                  | `<repo>/agent_dev_logs/plans/doc-schema-v2.plan.md`                |
