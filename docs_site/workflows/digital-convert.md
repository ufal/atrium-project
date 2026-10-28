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
    it reads and writes, and the licence floor of its output. The converter's engines and
    options, the rules that route a page, and the service's limits and settings with their
    defaults are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-digital-convert#readme), whose documentation map leads to its usage, configuration
    and how-it-works pages, and its
    [service README](https://github.com/ufal/atrium-digital-convert/blob/main/service/README.md#limits) —
    because they change as the rules are calibrated on AMČR documents.

## Purpose

A PDF, a word-processor file or a spreadsheet that was never printed and scanned already carries
its text; running OCR on it would only add errors. This workflow reads such a file directly and
writes the ATRIUM document record from what it finds: the pages, the lines (with their boxes, in
a PDF), the blocks they belong to, the headings, running headers and footers, footnotes and
tables. It also checks the text layer of every page. A page whose layer is missing, does not
decode to readable text or comes from an earlier OCR run is flagged `needs_ocr`, so that the
orchestration can send those pages to OCR; on request the tool also assesses every page and says
where it should go next. A PDF whose text layer is mostly the result of an earlier OCR run is
refused, because it belongs to the OCR route and [ocr-postprocess](ocr-postprocess.md).

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | PDF, DOCX, ODT, ODS, XLSX and RTF files, and DOC/XLS through LibreOffice, recognised by their content, not their extension; optionally the AMČR seed record, whose `source.sha512` must match the file                                                                                                         |
| **Out**                | the ATRIUM document record (JSON); on request the same record as annotated Markdown; a per-page assessment (JSON), from `/describe` or, since v1.3.0-beta, the command line's `--describe`; the run's paradata (JSON)                                                                                          |
| **Runs as**            | an HTTP service, `api-digital` (image `-api`: `POST /reformat`, and `POST /describe` for a per-page assessment), and a command-line tool (`api_util/digital_to_json.py`, image `-digital`), under these names since v1.1.0-beta                                                                                |
| **Compute**            | CPU, no GPU; memory follows the text a document holds, not its file size; the optional layout-model engine for complex PDFs is a local, opt-in build                                                                                                                                                           |
| **Network**            | none for `/reformat` and a plain command-line run; `/describe` (`--describe`) calls page-classification and ocr-postprocess when their URLs are set; the optional layout-model engine fetches its models at build time                                                                                         |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                            |
| **Component licences** | the default engine uses permissively licensed libraries; the optional layout-model engine adds model weights under Apache-2.0 and CDLA-Permissive-2.0; LibreOffice, which converts DOC and XLS, is listed. The rights in the text are the source document's: [Licences and paradata](../ecosystem/licences.md) |
| **Record**             | SSH Open Marketplace tool [`jGxgQI`](https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI)                                                                                                                                                                                                               |

## Steps

| # | Step                             | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | In → out                                      | Activity   |
|---|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|------------|
| 1 | Read the file                    | When an AMČR seed is sent, its `source.sha512` is checked against the file's bytes first, and a mismatch is refused. The type is recognised from the content. A light engine reads the PDF or DOCX structure directly; for complex PDFs a layout-model engine can be selected instead. ODT, ODS, XLSX and RTF go through the reader shared with ocr-postprocess; DOC and XLS are first converted to DOCX and XLSX by headless LibreOffice.                                                                                                                                                            | PDF, DOCX, ODT, ODS, XLSX, RTF, DOC, XLS → IR | Converting |
| 2 | Check the text layer             | Every page's text layer is tested and its verdict recorded as `text_layer` (`digital`, `garbled`, `ocr`, `none`, `blank`); a line that does not decode is marked `Garbage`. A page without a usable layer is marked `needs_ocr` with its reason; a PDF whose layer is mostly an earlier OCR run is refused with a registered reason and no record.                                                                                                                                                                                                                                                    | IR → IR                                       | —          |
| 3 | Build the record                 | Pages, lines with their block ids (and exact boxes in a PDF; the other formats have none), line styles (heading level, bold and italic, running header or footer, footnote), tables and the source's identity are written as the blocks the tool owns. In a PDF a heading is a line set larger than the body text, or a bold line at the body size that reads as a title, unless bold body-size text is more than `BOLD_HEADING_MAX_SHARE` of the body text. The record is written only if it keeps to the tool's own fields and passes the schema.                                                   | IR → JSON                                     | Converting |
| 4 | Assess the pages, when asked for | `/describe`, or the command line's `--describe`, says for every page whether its text can be used as it is, what kind of page it is ([page-classification](page-classification.md)), whether its text reads ([ocr-postprocess](ocr-postprocess.md)), and its route: `nlp` (use the text), `ocr` or `htr` (re-acquire it, for handwriting with HTR) or `none` (nothing to read). The two stages are called only when their URLs are set, and may add their own fields to the record; without them the tool answers from the converter alone. A stage that is down is reported, never a failed request. | JSON → JSON                                   | —          |
| 5 | Render, when asked for           | The record is turned into annotated Markdown, page by page in reading order, with the layout carried in HTML comments: the one form in which a document is given to a language model, as in keyword-extract's whole-document runs.                                                                                                                                                                                                                                                                                                                                                                    | JSON → Markdown                               | —          |

## Provenance and licence

Every `/reformat` and `/describe` call returns the run's paradata: an RO-Crate `CreateAction` that
names the file it read, with its digest, the seed when one was sent, and the record blocks it
wrote; `/describe` adds each stage's own paradata. On the command line, `--paradata-dir` writes a
paradata log (JSON). The paradata lists the components that ran, each with its licence, as
declared in the tool's `para_config.txt`: with the default engine, permissively licensed libraries
only, so the computed label is MIT, and the layout-model engine keeps it there. LibreOffice is
declared but left out of the label: it changes the container of a text it does not author, and the
conversion is reported beside the record instead. The label is not the licence of the output: the
source document's own rights apply to its text ([Licences and paradata](../ecosystem/licences.md)).

In the [document record](../ecosystem/document-contract.md) the tool is one of the two
originators of the positional layer — `pages`, `content`, `lines` and `tables` — for a
born-digital document, as [ocr-postprocess](ocr-postprocess.md) is for a scanned one; the
document's `source.origin` decides which of the two writes. The one exception is a page flagged
`needs_ocr`, whose lines ocr-postprocess may replace with the OCR lines. Every page row also
carries the converter's `text_layer`. In `/describe`, page-classification and ocr-postprocess may
add their own fields (page categories, line and page quality); the tool keeps their write only
when its own part of the record comes back unchanged. The program id in the record is
`digital-convert`, as before the move.

## Where it sits

* **First stage of the born-digital route** — [Pipelines → W2](../pipelines.md#other-workflows).
  Scans and images go through OCR and ocr-postprocess instead; the route step of the AMČR
  pipeline chooses by the file type AMČR detected. That route calls `/reformat`, which calls no
  other service: in the AMČR deployment Temporal chains the stages.
* **The OCR hand-off** — [Pipelines → W3](../pipelines.md#other-workflows). Pages flagged
  `needs_ocr` go to the ATR service. `/describe` refines that list in `summary.reacquire_pages`:
  it leaves out drawings and photographs, sends handwriting to HTR, and adds decoding pages whose
  prose the quality model rejects. A page that loses letters to unmapped glyphs is flagged in the
  record itself since v1.2.2-beta (`garbled`), and goes to OCR whatever its page type. ocr-postprocess then merges the ATR ALTO
  of each flagged page back into the same record, page by page; the born-digital pages stay as
  the converter wrote them.
* **What follows it.** The record goes on to [nlp-enrich](nlp-enrich.md) and
  [keyword-extract](keyword-extract.md), which reads the converter's lines like any other
  record's.
* **The service image** is one of the containerised services —
  [Pipelines → W4](../pipelines.md#w4--containerised-service--api-workflow).

## On other platforms

**SSH Open Marketplace.** Tool record [`jGxgQI`](https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI), "Born-digital document converter: PDF and
office files into structured text without OCR" (created 24 October 2026).

**Galaxy.** PDF and DOCX inputs map to `pdf` and `docx`; the record to `json`. Galaxy's own
`grobid` and `markitdown` tools convert born-digital documents but do not write the ATRIUM
record. The container is the service image `ghcr.io/ufal/atrium-digital-convert-api:<version>`
(`POST /reformat`), released since `v1.1.0-beta` and tagged with the release without its leading
`v`; the command line is published as `-digital`. Test data: the small generated PDF and DOCX
files in `tests/fixtures/digital/`.

## Sources

Read from `ufal/atrium-digital-convert` at release **`v1.3.0-beta`** (2026-10-26). Earlier readings
were at `v1.2.1-beta` (2026-10-19) and, before the move, `ufal/atrium-llm-enrich` at `v0.8.0`. This
table records **provenance**, not a build instruction.

| Source                                                                                                                                                       | What was taken from it                                                    |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `README.md` §§ intro, Where it sits in the pipeline, Formats, What the record holds, The per-page assessment, Configuration, Docker, Paradata and provenance | purpose, the steps, the formats, the routes, the images, the licence rule |
| `service/README.md` §§ Endpoints, Errors, Configuration, Limits, How it works; `service/api.py`, `service/stages.py`, `service/describe.py`                  | the HTTP service, the stage calls and their guard, the limits             |
| `api_util/digital_to_json.py`, `digital_pdf.py`, `digital_text.py`, `digital_legacy.py`, `digital_report.py`, `json_to_md.py`                                | the reading, the checks, the headings, the routes, the Markdown           |
| `para_config.txt`, `LICENSE`                                                                                                                                 | the licence components, the code licence                                  |
| `.env.example`, `tool_limits.py`                                                                                                                             | the settings named on this page                                           |
| `CONTRIBUTING.md` § Release History, `CITATION.cff`                                                                                                          | the releases, the move from llm-enrich                                    |
| `tests/fixtures/MANIFEST.json`                                                                                                                               | test data                                                                 |
| `DARIAH-ERIC/atrium-galaxy-tools`; `bgruening/galaxytools`                                                                                                   | the Galaxy analogues                                                      |
