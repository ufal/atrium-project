---
title: alto-postprocess workflow
nav_order: 16
status: published
round: 7
issue: 57
repo: atrium-alto-postprocess
role: workflow
authored: true
---

# Turning OCR output into clean, classified text lines

*The alto-postprocess workflow.* Tool: [atrium-alto-postprocess](https://ufal.github.io/atrium-alto-postprocess/).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The rules that decide a line's
    category, their thresholds and the options of each step are documented with the code —
    in the tool's [README](https://github.com/ufal/atrium-alto-postprocess#readme) and
    [`docs/categorization_logic.md`](https://github.com/ufal/atrium-alto-postprocess/blob/master/docs/categorization_logic.md) —
    because they change as the rules are calibrated.

## Purpose

OCR output mixes readable text with lines that were misread, lines that are not text at all,
and empty lines. This workflow splits OCR output into pages, extracts the text of each page in
reading order, and labels every text line by its language and by how well it was recognised,
so that later stages can work on the readable text and send the rest back for another
attempt. It is the point where the ATRIUM pipeline fans out: the per-page ALTO feeds the
translator, the line tables feed the NLP and LLM enrichment.

## At a glance

|                    |                                                                                                                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | ALTO XML from OCR; OCR output in JSON; other text-bearing formats as listed in the tool's [input-format reference](https://github.com/ufal/atrium-alto-postprocess/blob/master/docs/text_inputs.md) |
| **Out**            | per-page ALTO and plain text; page statistics (CSV); per-document tables of text lines with their language and category (CSV); a paradata log (JSON); optionally the ATRIUM document record (JSON)  |
| **Runs as**        | a command-line pipeline (`run_pipeline.py`, or one script per step); a container image; an HTTP service image (`POST /process`); an [Agent Skill](../agent-skills.md)                               |
| **Compute**        | the line classification step is built for a GPU                                                                                                                                                     |
| **Network**        | the Hugging Face Hub for its models on first use                                                                                                                                                    |
| **Code licence**   | MIT; the vendored alto-tools are Apache-2.0                                                                                                                                                         |
| **Output licence** | CC BY-NC 4.0 at minimum, because the language-identification model is used on every line; higher with some text-extraction methods (see below)                                                      |
| **Record**         | SSH Open Marketplace tool [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU)                                                                                                    |

## Steps

| # | Step                     | What happens                                                                                                                                                               | In → out                | Activity            |
|---|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|---------------------|
| 1 | Split into pages         | Multi-page documents are split into one file per page, named after the document and the page number.                                                                       | ALTO, JSON → ALTO, JSON | —                   |
| 2 | Build page statistics    | For every page: its text lines, illustrations, graphics and words, in one table per collection.                                                                            | ALTO, JSON → CSV        | —                   |
| 3 | Extract the text         | The text of each page is extracted in reading order, by one of several methods — from the ALTO geometry alone, with a layout-aware reading-order model, or from JSON keys. | ALTO, JSON → TXT        | Extracting          |
| 4 | Classify every text line | Each line gets its language and one of five categories (below), from structural checks, a language model's perplexity and character-level measures.                        | TXT → CSV               | Text Categorization |
| 5 | Aggregate                | The line categories are summed per page and per document, so a collection can be judged at a glance.                                                                       | CSV → CSV               | Aggregating         |

**The five categories:**

| Category   | What it means for the line                      |
|------------|-------------------------------------------------|
| `Clear`    | ready to be processed by further NLP            |
| `Noisy`    | readable, with recognition errors to correct    |
| `Trash`    | illegible; worth re-processing with another OCR |
| `Non-text` | not running text — codes, numbers, stamps       |
| `Empty`    | only whitespace; can be ignored                 |

## Provenance and licence

The steps write paradata logs, and a whole-pipeline run merges them into one run summary
that records the licence of the output. The licence is computed from the components the run
used, as declared in the tool's `setup/para_config.txt`; the most restrictive one wins. The
language-identification model is CC BY-NC 4.0 and is used on every run, so no output is less
restricted than that; the layout-aware reading-order model (LayoutLMv3-based) raises a run
that uses it to CC BY-NC-SA 4.0.

In the [document record](../ecosystem/document-contract.md) the tool originates the positional
text layer of a scanned document: the `pages`, `content`, `lines` and `tables` blocks.

## Where it sits

* **Second stage** of the scanned-document pipeline, and the point where the files fan out —
  [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
* **One route of format adaptation** for documents that are not ALTO —
  [Pipelines → W11](../pipelines.md#other-workflows).
* **ALTO post-processing and quality control** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU).

**Galaxy.** Inputs map to the `alto` and `json` datatypes (plus `txt`, `pdf`, `docx` and others
for the text-bearing formats); outputs to `alto`, `txt`, `tabular` and `json`. The closest
tools already in Galaxy are the OCR tools that produce ALTO — `tesseract`, and the Kraken tools
in the Digital Humanities section — which would sit directly before this workflow; no Galaxy
tool classifies OCR quality line by line.

## Sources

Read from `ufal/atrium-alto-postprocess` at release **`v1.5.1-beta`**, and at branch **`master`**,
commit `a584b7d`, for the input-format reference. This table records **provenance**, not a
build instruction.

| Source                                                                                | What was taken from it                                     |
|---------------------------------------------------------------------------------------|------------------------------------------------------------|
| `README.md` §§ Workflow Stages, Steps 1–4, Paradata logging, Output licensing         | purpose, the step order, the categories, the licence floor |
| `setup/para_config.txt`                                                               | the licence components                                     |
| `docs/text_inputs.md`, `docs/categorization_logic.md`                                 | where the formats and the rules are documented             |
| `service/README.md`                                                                   | the HTTP service                                           |
| SSH Open Marketplace `YParYU`                                                         | the record identifier                                      |
| `usegalaxy-eu/usegalaxy-eu-tools`; `galaxyproject/tools-iuc`; `bgruening/galaxytools` | the Galaxy datatypes and analogues                         |
