---
title: digital-convert workflow
nav_order: 19
status: published
round: 7
issue: 57
repo: atrium-digital-convert
role: workflow
authored: true
---

# Reading born-digital documents into the document record, without OCR

*The digital-convert workflow.* Tool: [atrium-digital-convert](https://ufal.github.io/atrium-digital-convert/).
The tool was part of **llm-enrich** until 1 October 2026; it continues in a new repository under
its own name, and the keyword extraction that llm-enrich also did moved to
[keyword-extract](keyword-extract.md).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The converter's engines, its
    options and the formats still being added are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-digital-convert#readme) — because they change
    while the service is being built.

## Purpose

A PDF or DOCX file that was never printed and scanned already carries its text; running OCR on
it would only add errors. This workflow reads such a file directly and writes the ATRIUM document
record from what it finds: the pages, the lines with their boxes, the blocks they belong to,
the headings, running headers and footers, footnotes and tables. It also checks the text
layer. A page whose layer does not decode to readable text is flagged `needs_ocr`, so that the
orchestration can send exactly those pages to OCR; a PDF whose text layer is itself the result of
an earlier OCR run is refused, because it belongs to [ocr-postprocess](ocr-postprocess.md).

## At a glance

|                    |                                                                                                                                                                                                 |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | PDF, DOCX, ODT, ODS, XLSX and RTF files, and DOC/XLS through LibreOffice; optionally the AMČR seed record, whose `source.sha512` must match the file                                            |
| **Out**            | the ATRIUM document record (JSON); on request the same document as Markdown; a paradata log (JSON)                                                                                              |
| **Runs as**        | an HTTP service (`-api`: `POST /reformat`, and `POST /describe` for a per-page assessment) and a command-line tool (`-digital`), since v1.1.0-beta                                              |
| **Compute**        | CPU; the optional layout-model engine for complex PDFs is a local, opt-in build                                                                                                                 |
| **Network**        | none for `/reformat` and the command line; `/describe` calls page-classification and ocr-postprocess when their URLs are set; the optional layout-model engine fetches its models at build time |
| **Code licence**   | MIT                                                                                                                                                                                             |
| **Output licence** | MIT with the default engine, which uses permissively licensed libraries; the optional layout-model engine adds weights under CDLA-Permissive-2.0, which leaves the output unchanged             |
| **Record**         | none of its own yet                                                                                                                                                                             |

## Steps

| # | Step                   | What happens                                                                                                                                                                                                                                                                                      | In → out        | Activity   |
|---|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|------------|
| 1 | Read the file          | A light engine reads the PDF or DOCX structure directly; for complex PDFs a layout-model engine can be selected instead.                                                                                                                                                                          | PDF, DOCX → IR  | Converting |
| 2 | Check the text layer   | Every page's text layer is tested and its verdict recorded as `text_layer` (`digital`, `garbled`, `ocr`, `none`, `blank`). A page without a usable layer is marked `needs_ocr` with its reason; a PDF whose layer is mostly an earlier OCR run is refused with a registered reason and no record. | IR → IR         | —          |
| 3 | Build the record       | Pages, lines with boxes and block ids, line styles (heading level, running header or footer, footnote), tables and the source's identity are written as the blocks the tool owns.                                                                                                                 | IR → JSON       | Converting |
| 4 | Render, when asked for | The record is turned into Markdown in reading order — the form in which the keyword stage shows a document to a language model.                                                                                                                                                                   | JSON → Markdown | —          |

## Provenance and licence

Every run writes a paradata log. The record's licence is computed from the components that ran,
as declared in the tool's `para_config.txt`, and the most restrictive one wins; with the default
engine that is MIT. The source document's own licence applies to its text.

In the [document record](../ecosystem/document-contract.md) the tool is one of the two
originators of the positional layer — `pages`, `content`, `lines` and `tables` — for a
born-digital document, as [ocr-postprocess](ocr-postprocess.md) is for a scanned one; the
document's `source.origin` decides which of the two writes, and never both. The program id in the
record is `digital-convert`, as before the move.

## Where it sits

* **First stage of the born-digital route** — [Pipelines → W2](../pipelines.md#other-workflows).
  Scans and images go through OCR and ocr-postprocess instead; the route step of the AMČR
  pipeline chooses by the file type AMČR detected.
* **The OCR hand-off.** Pages flagged `needs_ocr` go to the ATR service. ocr-postprocess then
  merges the ATR ALTO of each such page back into the same record, page by page; the born-digital
  pages stay as the converter wrote them.
* **What follows it.** The record goes on to [keyword-extract](keyword-extract.md), which reads
  the converter's lines like any other record's.

## On other platforms

**SSH Open Marketplace.** No record of its own yet.

**Galaxy.** Inputs map to `pdf` and `docx`; the output to `json`. Galaxy's own `grobid` and
`markitdown` tools convert born-digital documents but do not write the ATRIUM record. The container is the
service image `ghcr.io/ufal/atrium-digital-convert-api:<version>` (`POST /reformat`), released since `v1.1.1-beta`.

## Sources

Read from `ufal/atrium-llm-enrich` at release **`v0.8.0`** (the converter as a command-line
tool) and from its plan for the repository's move to `ufal/atrium-digital-convert` (2026-10-01).
This table records **provenance**, not a build instruction.

| Source                                                                            | What was taken from it                           |
|-----------------------------------------------------------------------------------|--------------------------------------------------|
| `README.md` §§ intro, the converter                                               | purpose, the steps, the inputs and outputs       |
| `api_util/digital_to_json.py`, `api_util/doc_to_visual_md.py`                     | the converter's route, its checks and its output |
| `requirements_digital.txt`, `requirements_digital_docling.txt`, `para_config.txt` | the engines and the licence components           |
| `DARIAH-ERIC/atrium-galaxy-tools`; `bgruening/galaxytools`                        | the Galaxy analogues                             |
