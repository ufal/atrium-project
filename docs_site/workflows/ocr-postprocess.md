---
title: ocr-postprocess workflow
nav_order: 16
status: published
round: 7
issue: 57
repo: atrium-ocr-postprocess
role: workflow
authored: true
---

# Turning OCR output into clean, classified text lines

*The ocr-postprocess workflow.* Tool: [atrium-ocr-postprocess](https://ufal.github.io/atrium-ocr-postprocess/).
The tool was named **alto-postprocess** until 1 October 2026; it continues in a new repository
under the new name, with its code, its pipeline and its categories unchanged.

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The rules that decide a line's
    category, their thresholds and the options of each step are documented with the code —
    in the tool's [README](https://github.com/ufal/atrium-ocr-postprocess#readme) and
    [`docs/categorization_logic.md`](https://github.com/ufal/atrium-ocr-postprocess/blob/master/docs/categorization_logic.md) —
    because they change as the rules are calibrated.

## Purpose

OCR output mixes readable text with lines that were misread, lines that are not text at all,
and empty lines. This workflow splits OCR output into pages, extracts the text of each page in
reading order, and labels every text line by its language and by how well it was recognised,
so that later stages can work on the readable text and send the rest back for another
attempt. ALTO is its main input; the other OCR formats, and text-bearing files such as PDF or
DOCX, are labelled the same way. It also scores the lines of a born-digital record, so that
scanned and born-digital documents get one quality answer. It is the point where the ATRIUM
pipeline fans out: the per-page ALTO feeds the translator, the line tables feed the NLP
enrichment, and the record feeds keyword extraction.

## At a glance

|                    |                                                                                                                                                                                                                                                                                                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | ALTO XML (v2–v4) from OCR; the other OCR formats — PAGE XML, hOCR, ABBYY FineReader XML, DjVuXML, Tesseract TSV, OCR JSON; PDF, office, e-mail and plain-text files, as listed in the tool's [input-format reference](https://github.com/ufal/atrium-ocr-postprocess/blob/master/docs/text_inputs.md); for scoring alone, an existing ATRIUM document record (JSON) |
| **Out**            | per-page ALTO or JSON, and plain text; page statistics (CSV); per-document tables of text lines with their language, quality score and category (CSV); per-page category counts (CSV); for the other formats, a report of what was read (CSV); a paradata log (JSON); optionally the ATRIUM document record (JSON)                                                  |
| **Runs as**        | a command-line pipeline (`run_pipeline.py`, or one script per step); a container image; an HTTP service image (`POST /process`, which also merges an OCR'd page into a born-digital record, and `POST /score_record` to score the lines of an existing record); an [Agent Skill](../agent-skills.md)                                                                |
| **Compute**        | the line classification step and the default, layout-aware text extraction are built for a GPU; the service also runs on a CPU and uses a GPU when it finds one; the published images are CPU builds, and a GPU image is built locally from the same Dockerfile                                                                                                     |
| **Network**        | the Hugging Face Hub for its models on first use; the images already hold the language-identification model                                                                                                                                                                                                                                                         |
| **Code licence**   | MIT; the vendored alto-tools are Apache-2.0                                                                                                                                                                                                                                                                                                                         |
| **Output licence** | CC BY-NC 4.0 at minimum, because the language-identification model counts toward every run; CC BY-NC-SA 4.0 when the layout-aware reading-order model orders ALTO lines, as it does by default (see below)                                                                                                                                                          |
| **Record**         | SSH Open Marketplace tool [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU)                                                                                                                                                                                                                                                                    |

## Steps

| # | Step                     | What happens                                                                                                                                                                                                                                                                                                                                                             | In → out                                    | Activity            |
|---|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|---------------------|
| 1 | Split into pages         | ALTO and OCR JSON documents are split into one file per page, named after the document and the page number. Any other file is recognised by its content and read into pages of lines, with a report of what was read and what was refused.                                                                                                                               | ALTO, JSON, other formats → ALTO, JSON, TXT | —                   |
| 2 | Build page statistics    | For every page: its text lines, illustrations, graphics and words, in one table per collection.                                                                                                                                                                                                                                                                          | ALTO, JSON, TXT → CSV                       | —                   |
| 3 | Extract the text         | The text of each page is extracted by one of five methods: in reading order by a layout-aware model (LayoutReader, the default for ALTO), in ALTO's own order (alto-tools), from the page image by a vision-language model (GLM), from the text keys of OCR JSON (json-keys), or line by line from any other format (text-lines).                                        | ALTO, JSON, TXT → TXT                       | Extracting          |
| 4 | Classify every text line | A CPU pre-filter labels blank lines `Empty`, and numbers, dates, codes and stamps `Non-text`, with no model. Every other line gets its language, a quality score from structural checks, character-level measures and a language model's perplexity, and one of the other three categories. The batch pipeline then revises the labels against the rest of the document. | TXT → CSV                                   | Text Categorization |
| 5 | Aggregate                | The line categories are counted per page, with page averages, in one table for the collection and one per document, so a collection can be judged at a glance.                                                                                                                                                                                                           | CSV → CSV                                   | Aggregating         |

**The five categories:**

| Category   | What it means for the line                      |
|------------|-------------------------------------------------|
| `Clear`    | legible; ready to be processed by further NLP   |
| `Noisy`    | readable, with recognition errors to correct    |
| `Trash`    | illegible; worth re-processing with another OCR |
| `Non-text` | not language — numbers, codes, stamps, dates    |
| `Empty`    | only whitespace; can be ignored                 |

**The service and the batch pipeline.** Both run the same pre-filter and score a line with
the same function. A line the pre-filter settles carries the score 0.0 and the language `N/A`.
The document passes of step 4 are batch only: the service answers each line on its own, so
over a whole document its categories can differ from a batch run's.

**Perplexity in batches.** The language model scores lines in batches (in the service,
`PPL_BATCH_LINES` lines, 32 since v1.12.0-beta). A batch that runs out of memory is split in
halves and retried. A line that fails even on its own gets perplexity 99999, the worst
quality, and the service names it in the response's `limits_applied`.

**Known limits.** The rules were calibrated on Czech archaeological reports with German and
English passages, and several of them act on every line whatever its language. A clean
English, German or French line can read `Noisy`, and a German compound `Trash`; the
categorisation reference lists the
[foreign-language cases](https://github.com/ufal/atrium-ocr-postprocess/blob/master/docs/categorization_logic.md#foreign-language-lines).
A `Clear` on a line of one to three words without Czech diacritics is less certain than the
label suggests.

## Provenance and licence

The steps write paradata logs, and a whole-pipeline run merges them into one run summary
that records the licence of the output. The service writes no paradata file: every response
carries its provenance as `paradata`, one Process Run Crate action. The licence is computed
from the components the run used, as declared in the tool's `setup/para_config.txt`; the most
restrictive one wins. The language-identification model is CC BY-NC 4.0 and counts toward
every run, so no output is less restricted than that. The layout-aware reading-order model
(LayoutLMv3-based) raises a run that uses it to CC BY-NC-SA 4.0; it is the batch pipeline's
default method for ALTO, and the service orders ALTO uploads with it. The GLM method adds the
GLM-4 model licence, also non-commercial; the other models and readers are permissive.

In the [document record](../ecosystem/document-contract.md) the tool originates the positional
text layer of a scanned document: the `pages`, `content`, `lines` and `tables` blocks. Its
blocks are stamped `ocr-postprocess`; records written before the rename keep
`alto-postprocess`, which the record contract accepts as the same writer. A born-digital
record is originated by digital-convert: there the tool writes only into the pages flagged
`needs_ocr`, whose lines it replaces, and `POST /score_record` adds the category, score and
language of the existing lines and the score and band of their pages, never their text. As the
owner of the quality model it also writes `quality_summary` on every origin
(atrium-project#73, v1.10.0-beta): page-score statistics and line counts per category,
recomputed from the record whenever it writes or scores pages and lines. It is numbers only,
with no band or threshold, and nothing in the pipeline routes on it.

## Where it sits

* **Second stage** of the scanned-document pipeline, and the point where the files fan out —
  [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
* **One route of format adaptation** for documents that are not ALTO —
  [Pipelines → W11](../pipelines.md#other-workflows).
* **The OCR hand-off of the born-digital route.** A page [digital-convert](digital-convert.md)
  flags `needs_ocr` is OCR'd, and its ALTO comes here with the record: the page's lines are
  replaced by the OCR lines, and the other pages are left as the converter wrote them —
  [Pipelines → W3](../pipelines.md#other-workflows).
* **The quality model of the born-digital route.** When digital-convert is set to call it, its
  `POST /describe` sends the record to `POST /score_record`, which scores the converter's lines
  with the same five categories as OCR lines — [Pipelines → W2](../pipelines.md#other-workflows).
* **ALTO post-processing and quality control** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU).

**Galaxy.** Inputs map to the `alto` and `json` datatypes (plus `txt`, `pdf`, `docx` and others
for the text-bearing formats); outputs to `alto`, `txt`, `tabular` and `json`. The closest
tools already in Galaxy are the OCR tools that produce ALTO — `tesseract`, and the Kraken tools
in the Digital Humanities section — which would sit directly before this workflow; no Galaxy
tool classifies OCR quality line by line. The container is the service image
`ghcr.io/ufal/atrium-ocr-postprocess-api:<version>` (`POST /process`, `POST /score_record`),
where `<version>` is the release without its leading `v`; it is a CPU build. Test data: the
synthetic `data_samples/` — ALTO, OCR JSON and one file of each text-lines format, with the
page texts and line tables of the ALTO samples — under CC BY-NC 4.0.

## Sources

Read from `ufal/atrium-ocr-postprocess` at release **`v1.12.0-beta`** (2026-10-16). The
repository continues `ufal/atrium-alto-postprocess`, archived on 2026-10-19. This table records **provenance**, not
a build instruction.

| Source                                                                                                                                                      | What was taken from it                                                                     |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| `README.md` §§ intro, Setup, Workflow Stages, Steps 1–4, API Service Integration, Paradata logging, Output licensing, Document record schema, Vendored code | purpose, the step order, the categories, the outputs, the licence floor, the record blocks |
| `docs/text_inputs.md`; `docs/categorization_logic.md` §§ Who runs it, CPU Pre-filter, Foreign-language lines                                                | the input formats; the pre-filter, what the service does differently, the known limits     |
| `service/README.md`, `service/text_api.py`, `service/text_inference.py`                                                                                     | the HTTP service, its two endpoints, the OCR hand-off, the scoring of a record             |
| `text_util.py` (`calculate_perplexity_batch`), `tool_limits.py`                                                                                             | perplexity in batches, the out-of-memory retry, `PPL_BATCH_LINES`                          |
| `page_split.py`, `extract_LLM_ALTO_2_TXT.py`, `classify_TEXT.py`, `aggregate_STAT.py`                                                                       | the inputs and outputs of the batch steps                                                  |
| `setup/para_config.txt`, `para_licenses.py`, `setup/config.txt` § `[PIPELINE]`                                                                              | the licence components, their ranking, the default extraction method                       |
| `Dockerfile`, `docker-compose.gpu.yml`                                                                                                                      | the images, their CPU build, the model inside them                                         |
| `data_samples/README.md`, `data_samples/LICENSE`                                                                                                            | test data                                                                                  |
| `CITATION.cff`, `CONTRIBUTING.md` release rows v1.5.1-beta to v1.12.0-beta                                                                                  | the release and its date, what changed since the last reading                              |
| SSH Open Marketplace `YParYU`                                                                                                                               | the record identifier                                                                      |
| `usegalaxy-eu/usegalaxy-eu-tools`; `galaxyproject/tools-iuc`; `bgruening/galaxytools`                                                                       | the Galaxy datatypes and analogues                                                         |
