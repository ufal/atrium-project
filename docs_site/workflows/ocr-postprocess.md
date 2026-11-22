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

# Building the document record and grading its text lines

*The ocr-postprocess workflow.* Tool: [atrium-ocr-postprocess](https://github.com/ufal/atrium-ocr-postprocess).
The tool was named **alto-postprocess** until 1 October 2026; it continues in a new repository under the new
name.

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licences of the components it uses. The rules that decide a line's
    category, their thresholds and the options of each step are documented with the code —
    in the tool's [README](https://github.com/ufal/atrium-ocr-postprocess/blob/test/README.md) and
    [`docs/categorization_logic.md`](https://github.com/ufal/atrium-ocr-postprocess/blob/test/docs/categorization_logic.md) —
    because they change as the rules are calibrated.

## Purpose

Every document in the AMČR pipeline reaches this tool as docproc: its layout as the ATR (AIS CR's
text-recognition service) read it from the scans, or as digital-convert read it from a born-digital file. This
workflow builds the ATRIUM document record from it: the pages, the text lines in reading order with their boxes,
and the document's text. It then labels every line by its language and by how well it can be read, so that later
stages work on the readable text and an archive can see which pages are legible. For research collections, the
same labelling runs as a batch pipeline over OCR output, ALTO first, and over text-bearing files such as PDF or
DOCX.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | docproc (`atr/docproc-json`), the ATR's or digital-convert's, both for a mixed document; optionally AMČR's seed (the document's identifier and the checksum of its original); for scoring alone, an existing ATRIUM document record (JSON). For research batches: ALTO XML (v2–v4), PAGE XML, hOCR, ABBYY FineReader XML, DjVuXML, Tesseract TSV, OCR JSON, PDF, office, e-mail and plain-text files, as listed in the tool's [input-format reference](https://github.com/ufal/atrium-ocr-postprocess/blob/test/docs/text_inputs.md) |
| **Out**                | the ATRIUM document record (JSON), every line and page scored; the run's paradata. For research batches: page texts, per-document tables of text lines with their language, quality score and category (CSV), per-page category counts (CSV), a report of what was read (CSV), a paradata log (JSON), optionally records                                                                                                                                                                                                             |
| **Runs as**            | an HTTP service image (`POST /build_record`, the pipeline's call; `POST /score_record`; `POST /process` for research uploads); the same from the command line (`build_record.py`, `score_record.py`); a batch pipeline (`run_pipeline.py`, or one script per step) and its container image; an [Agent Skill](../agent-skills.md)                                                                                                                                                                                                     |
| **Compute**            | the published images run on the CPU, and building a record needs no GPU; the batch classification and the layout-aware reading order are built for a GPU, from a local CUDA build of the same Dockerfile                                                                                                                                                                                                                                                                                                                             |
| **Network**            | the Hugging Face Hub for its models on first use; the images already hold the language-identification model                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Code licence**       | MIT; the vendored alto-tools are Apache-2.0                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Component licences** | the language-identification model (CC BY-NC 4.0) on every run; the layout-aware reading-order model (CC BY-NC-SA 4.0) when it orders ALTO lines. Each run lists the components it used, each with its own licence or terms. No licence of an output is computed: [Licences and paradata](../ecosystem/licences.md)                                                                                                                                                                                                                   |
| **Record**             | SSH Open Marketplace tool [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU)                                                                                                                                                                                                                                                                                                                                                                                                                                     |

## Steps

**Building the record**, as the AMČR pipeline calls it (`POST /build_record`):

| #   | Step                     | What happens                                                                                                                                                                                                                                                                                                                                           | In → out                       | Activity            |
|-----|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|---------------------|
| 1   | Read the docproc         | Pages by number, blocks in reading order. A block's own lines keep their boxes; otherwise its text is split at line breaks, and a table gives one line per row. A page the docproc neither lists nor marks empty, or a block whose text could not be read, fails the job.                                                                              | docproc → pages and lines      | Extracting          |
| 2   | Merge a mixed document   | digital-convert's exact lines are kept on the pages it could read, each linked to the ATR block that holds it; the ATR's lines fill the forced pages and the blocks no kept line falls into. The order is the ATR's. Two docprocs that disagree on the pages or their sizes fail the job.                                                              | two docprocs → pages and lines | —                   |
| 3   | Classify every text line | A pre-filter labels blank lines `Empty`, and numbers, dates, codes and stamps `Non-text`, with no model. Every other line gets its language, a quality score from structural checks, character-level measures and a language model's perplexity, and one of the other three categories. Passes over the whole document then correct isolated mistakes. | lines → scored lines           | Text Categorization |
| 4   | Write the record         | `source`, a row for every page of the original with its size, the lines with their boxes and categories, `content`, each page's score and band, and `quality_summary`. A failed step writes nothing.                                                                                                                                                   | → the record (JSON), paradata  | —                   |

**Research batches** (`run_pipeline.py`):

| #   | Step                     | What happens                                                                                                                                                                                                                                                                                                                                                          | In → out                                    | Activity            |
|-----|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|---------------------|
| 1   | Split into pages         | ALTO and OCR JSON documents are split into one file per page, named after the document and the page number. Any other file is recognised by its content and read into pages of lines, with a report of what was read and what was refused.                                                                                                                            | ALTO, JSON, other formats → ALTO, JSON, TXT | —                   |
| 2   | Build page statistics    | For every page: its text lines, illustrations, graphics and words, in one table per collection.                                                                                                                                                                                                                                                                       | ALTO, JSON, TXT → CSV                       | —                   |
| 3   | Extract the text         | The text of each page is extracted by one of five methods: in reading order by a layout-aware model (LayoutReader, the default for ALTO), in ALTO's own order (alto-tools; the service's `reading_order=alto`), from the page image by a vision-language model (GLM), from the text keys of OCR JSON (json-keys), or line by line from any other format (text-lines). | ALTO, JSON, TXT → TXT                       | Extracting          |
| 4   | Classify every text line | As step 3 above, with the same function, then the same passes over each document.                                                                                                                                                                                                                                                                                     | TXT → CSV                                   | Text Categorization |
| 5   | Aggregate                | The line categories are counted per page, with page averages, in one table for the collection and one per document, so a collection can be judged at a glance.                                                                                                                                                                                                        | CSV → CSV                                   | Aggregating         |

**The five categories:**

| Category   | What it means for the line                      | In the pipeline                                      |
|------------|-------------------------------------------------|------------------------------------------------------|
| `Clear`    | legible; nobody needs the page image to read it | goes on to language processing and keywords          |
| `Noisy`    | readable, with recognition errors to correct    | goes on as well                                      |
| `Trash`    | illegible                                       | left out of language processing and keywords         |
| `Non-text` | not language — numbers, codes, stamps, dates    | goes on; worth checking for identifiers              |
| `Empty`    | only whitespace                                 | left out                                             |

No step sends a `Trash` page back for another recognition pass; re-processing is a later, separate campaign.

**Whole documents and single uploads.** Every path runs the same pre-filter and scores a line with the same
function. A line the pre-filter settles carries the score 0.0 and the language `N/A`. Building or re-scoring a
record, and the batch pipeline, run the passes over the whole document; `POST /process` answers each line of an
upload on its own, so its categories can differ on the same document.

**Perplexity in batches.** The language model scores lines in batches (in the service, `PPL_BATCH_LINES` lines,
32). A batch that runs out of memory is split in halves and retried. A line that fails even on its own fails a
service call (422 `limit_exceeded`); the batch pipeline gives it perplexity 99999, the worst quality, and goes on.

## What you get

The record holds every line's category (`categ`), quality score and language, and every page's score and band
(`quality_band`); its `quality_summary` counts the pages and the lines per category. The category, not the score,
is the decision. A page's score is the mean of its `Clear` and `Noisy` lines, so read it together with the page's
`Trash` lines. A research batch gives the same answers as tables: one row per line with its measurements, and one
row per page with its category counts and ratios.

## Limits

* The rules were calibrated on Czech archaeological reports with German and English passages, and several of them
  act on every line whatever its language. A clean English, German or French line can read `Noisy`, and a German
  compound `Trash`; the categorisation reference lists the
  [foreign-language cases](https://github.com/ufal/atrium-ocr-postprocess/blob/test/docs/categorization_logic.md#foreign-language-lines).
* A `Clear` on a line of one to three words without Czech diacritics is less certain than the label suggests.
* The category rules are frozen for the AMČR pilot. They have been measured on a hand-labelled gold set and on
  corpus diffs, not validated in full.
* Building a record fails as a whole. The research paths, the batch pipeline and `POST /process`, go on past a
  file they cannot read, so their outputs are not written to AMČR.

## Provenance and licence

Every run records paradata: what it read and wrote, as AMČR distributions by name and SHA-512, and the components
it used, each with its own licence, as declared in the tool's `setup/para_config.txt`. The service returns them
with every response as one Process Run Crate action and writes no file; the batch steps write one log each, and a
whole-pipeline run merges them. The language-identification model (CC BY-NC 4.0) is used on every run. The
layout-aware reading-order model (LayoutLMv3-based, CC BY-NC-SA 4.0) is the batch pipeline's default method for
ALTO, and the service orders ALTO uploads with it unless a request asks for ALTO's own order
(`reading_order=alto`). The GLM method uses the GLM-4 model, whose licence is also non-commercial; the other
models and readers are permissive. No licence of an output is computed: the rights in an output follow the source
document ([Licences and paradata](../ecosystem/licences.md)).

In the [document record](../ecosystem/document-contract.md) the tool is the record builder. It writes `source`,
`pages`, `lines` and `content`, and, as the only scorer, every line's `categ`, `quality_score` and `lang`, every
page's `quality_score` and `quality_band`, and `quality_summary`: page-score statistics and line counts per
category, recomputed whenever it writes or scores pages and lines. It is numbers only, with no band or threshold,
and nothing in the pipeline routes on it. The record carries no run data. Records written before the rename name
their writer `alto-postprocess`, which the record contract reads as the same tool.

## Where it sits

* **The record builder of the AMČR pipeline**, after digital-convert and the ATR and before nlp-enrich and
  keyword-extract — [Pipelines → The route through the pipeline](../pipelines.md#the-route-through-the-pipeline)
  and [W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
* **Born-digital and mixed documents**: the record of a born-digital document is built from digital-convert's
  docproc, and that of a mixed document from both docprocs —
  [Pipelines → W2 and W3](../pipelines.md#other-workflows).
* **One route of format adaptation** for research documents that are not docproc —
  [Pipelines → W11](../pipelines.md#other-workflows).
* **ALTO post-processing and quality control** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU).

**Galaxy sheet.** The Galaxy wrappers were handed to DARIAH for testing; further Galaxy work is parked during the
AMČR pilot. The sheet describes the wrapper as delivered, for the batch pipeline at `v1.15.4-beta`.

|                               |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**           | one OCR document per job — ALTO as `xml` (DARIAH's Galaxy has `alto` only as an alias of `xml`), OCR JSON — `json`, or a text-bearing file: `txt`, `csv`/`tsv` with a `text` column, `html` (hOCR), `xml` (PAGE), `pdf`, `docx`, `xlsx`, `markdown`; optionally a document record — `json`                                                                                                                                                                                                       |
| **Parameters**                | the method (`text-lines` for ALTO and the text-bearing formats, `alto-tools` for ALTO, `json-keys` for OCR JSON); line quality only: the expected languages (`ces,deu,eng`) and the perplexity model (downloaded or staged)                                                                                                                                                                                                                                                                      |
| **Workflow outputs**          | the line table — `csv` (`file,page_num,line_num,text,page_label`); page texts — `txt`; per-page ALTO — `xml`; statistics — `csv`; paradata — `json`; document record — `json`; line quality only: lines with their category and the categories per page — `csv`                                                                                                                                                                                                                                  |
| **Container**                 | `ghcr.io/ufal/atrium-ocr-postprocess:<version>` — the batch image (`run_pipeline.py`); it runs the job script Galaxy hands it (the hub-canonical `container_entrypoint.py`). The pipeline starts its stages by name from `/app`, so a job script runs it there, with a config of absolute paths. The service image `-api` is not used                                                                                                                                                            |
| **Galaxy tool**               | `atrium_ocr_postprocess` (CPU: split, statistics, extract) and `atrium_ocr_line_quality` (GPU: the same, then classify and aggregate), `1.15.4-beta+galaxy0`, with the data manager *ATRIUM Hugging Face models* for Qwen2.5-0.5B, in the hub's [`galaxy/`](https://github.com/ufal/atrium-project/tree/test/galaxy) folder with the workflow *ATRIUM OCR to keywords*; for DARIAH's test Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>), the line-quality tool for an instance with GPUs |
| **Compute**                   | CPU for splitting, statistics and text extraction. The batch line classifier (Qwen2.5-0.5B) needs a CUDA GPU; on CPU, `score_record.py` scores records with the service's models                                                                                                                                                                                                                                                                                                                 |
| **Network or reference data** | the fastText language-identification model is in the image; Qwen2.5-0.5B and LayoutReader come from the Hugging Face Hub, or are staged once                                                                                                                                                                                                                                                                                                                                                     |
| **Test data**                 | four of the synthetic `data_samples/` — an ALTO page, a CSV, OCR JSON — under CC BY-NC 4.0, and an XML file that is not ALTO for the error test                                                                                                                                                                                                                                                                                                                                                  |
| **Credit**                    | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Closest Galaxy tools**      | the OCR tools that write ALTO and come before this step: Tesseract (IUC, installed on DARIAH's instance, ALTO as `xml`) and Kraken; none classifies OCR quality line by line                                                                                                                                                                                                                                                                                                                     |

## Sources

Read from `ufal/atrium-ocr-postprocess` on its `test` branch, which carries release 2.0.0-beta, on 2026-11-21;
earlier readings were at `v1.15.0-beta` (2026-10-29), `v1.13.1-beta` (2026-10-27) and `v1.12.0-beta` (2026-10-16).
The repository continues `ufal/atrium-alto-postprocess`, archived on 2026-10-19. The Galaxy sheet (2026-11-07)
follows `v1.15.4-beta` and the tool's wrapper in the hub's `galaxy/` folder. This table records **provenance**, not
a build instruction.

| Source                                                                                          | What was taken from it                                                                                                                 |
|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `README.md`, `docs/usage.md`, `service/README.md`                                               | purpose, the two ways of running it, the step order, the categories, the outputs, what the command line and the service do differently |
| `build_record.py`, `docproc.py`, `docproc_merge.py`, `record_scoring.py`, `service/text_api.py` | building the record from docproc, the merge of a mixed document, the document passes, the failures                                     |
| `docs/text_inputs.md`; `docs/categorization_logic.md` §§ Who runs it, Foreign-language lines    | the research input formats; the pre-filter, the known limits                                                                           |
| `text_util.py` (`calculate_perplexity_batch`), `tool_limits.py`, `atrium_limits.py`             | perplexity in batches, the out-of-memory retry, `PPL_BATCH_LINES`, the failing limits                                                  |
| `page_split.py`, `extract_LLM_ALTO_2_TXT.py`, `classify_TEXT.py`, `aggregate_STAT.py`           | the inputs and outputs of the batch steps                                                                                              |
| `atrium_document.py` (`BLOCK_OWNERS`, `BLOCK_FIELD_OWNERS`, `PROGRAM_SUCCESSORS`)               | the record fields the tool writes, the former program name                                                                             |
| `setup/para_config.txt`, `para_licenses.py`, `setup/config.txt` § `[PIPELINE]`                  | the licence components, the default extraction method                                                                                  |
| `Dockerfile`, `docker-compose.gpu.yml`                                                          | the images, their CPU build, the model inside them                                                                                     |
| `data_samples/README.md`, `data_samples/LICENSE`                                                | test data                                                                                                                              |
| SSH Open Marketplace `YParYU`                                                                   | the record identifier                                                                                                                  |
| `usegalaxy-eu/usegalaxy-eu-tools`; `galaxyproject/tools-iuc`; `bgruening/galaxytools`           | the Galaxy datatypes and analogues                                                                                                     |
