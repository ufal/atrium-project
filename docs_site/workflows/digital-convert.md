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

# Reading born-digital documents into their layout, without OCR

*The digital-convert workflow.* Tool: [atrium-digital-convert](https://github.com/ufal/atrium-digital-convert).
The tool was part of **llm-enrich** until 1 October 2026; it continues in a new repository under its own name, and
the keyword extraction that llm-enrich also did moved to [keyword-extract](keyword-extract.md).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licences of the components it uses. The converter's engines and
    options, the rules that give a page its verdict, and the service's limits and settings with their
    defaults are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-digital-convert/blob/test/README.md), whose documentation map leads to
    its usage, configuration and how-it-works pages, and its
    [service README](https://github.com/ufal/atrium-digital-convert/blob/test/service/README.md#limits) —
    because they change as the rules are calibrated on AMČR documents.

## Purpose

A PDF, a word-processor file or a spreadsheet that was never printed and scanned already carries its text; running
OCR on it would only add errors. This workflow reads such a file directly and writes its layout as docproc
(`atr/docproc-json`), the format the ATR, AIS CR's text-recognition service, writes for scanned pages: the pages,
the blocks in reading order with their lines (with their boxes, in a PDF or an office document), the headings,
running headers and footers, footnotes and tables. It also checks the text layer of every page. A page whose layer
is missing, does not decode to readable text or comes from an earlier OCR run is marked `needsAtr`, so that the
whole document goes through the ATR with those pages forced; so is an office document's page with no text of its
own (none outside its header and footer) that shows a picture, such as a pasted scan. No document is refused for its
pages.
[ocr-postprocess](ocr-postprocess.md) builds the ATRIUM document record from the docproc.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                                                                                                           |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | PDF, office documents (DOCX, DOC, ODT, RTF) read as their own text on the pages of a LibreOffice rendering, and, without pages to render, spreadsheets (ODS, XLSX, XLS) and text files (TXT, CSV, TSV, JSON), recognised by their content, not their extension; images go to the ATR instead; optionally AMČR's seed of the record (the document's identifier and the checksum of its original)           |
| **Out**                | the docproc (JSON), with a verdict on every page's text layer, the route of every page and a `figure` block for every picture, chart or drawing; an office document's rendered PDF when the ATR or page-classification reads it, not stored (the paradata name it by its SHA-512); on request, the document as annotated Markdown; the run's paradata (JSON)                                              |
| **Runs as**            | an HTTP service, `api-digital` (image `-api`: `POST /reformat`), and a command-line tool (`api_util/digital_to_json.py`, image `-digital`)                                                                                                                                                                                                                                                                |
| **Compute**            | CPU, no GPU; memory follows the text a document holds, not its file size; the optional layout-model engine for complex PDFs is a local, opt-in build                                                                                                                                                                                                                                                      |
| **Network**            | none; the optional layout-model engine fetches its models at build time                                                                                                                                                                                                                                                                                                                                   |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Component licences** | the default engine uses permissively licensed libraries; the optional layout-model engine adds model weights under Apache-2.0 and CDLA-Permissive-2.0; LibreOffice, which converts DOC and XLS and renders office documents, is listed. Each run lists the components it used, each with its own licence or terms. No licence of an output is computed: [Licences and paradata](../ecosystem/licences.md) |
| **Record**             | SSH Open Marketplace tool [`jGxgQI`](https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI)                                                                                                                                                                                                                                                                                                          |

## Steps

| # | Step                   | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | In → out                    | Activity   |
|---|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|------------|
| 1 | Read the file          | When an AMČR seed is sent, its `source.sha512` is checked against the file's bytes first, and a mismatch is refused. The type is recognised from the content, and decides the workflow. Visual: a light engine reads a PDF on its own pages, and an office document as its own text placed on the pages of a LibreOffice rendering. Textual: a spreadsheet keeps every non-empty cell as the sheet displays it, and a text file its lines.                                                                       | file → pages, blocks, lines | Converting |
| 2 | Check the text layer   | Every page's text layer is tested: `digital` (it decodes), `garbled` (it does not), `ocr` (an earlier OCR run) or `none` (no text). A PDF page that is not `digital` is `needsAtr`, with a reason; an office page is `needsAtr` only by the PDF rule: no text of its own (none outside its header and footer) and a picture. A line that does not decode keeps the flag `decode:garbled` (`decode:inverted` for mirrored text): a verdict on its characters, apart from the line quality ocr-postprocess scores. | pages → verdicts            | —          |
| 3 | Write the docproc      | Pages, blocks with their lines and boxes, headings, tables as cell grids, and the route of every page in `metadata.routing`: `text-layer`, `atr` or `empty`; a picture, chart or drawing is a `figure` block with its box. An empty page is routed `empty` and left out of `pages[]`. The docproc is validated against its schema; one that fails is never returned, and a limit that would cut content fails the job.                                                                                           | → docproc (JSON), paradata  | Converting |
| 4 | Render, when asked for | The document is turned into annotated Markdown, page by page in reading order, with the layout carried in HTML comments: the one form in which a document is given to a language model, as in keyword-extract's whole-document runs.                                                                                                                                                                                                                                                                             | → Markdown                  | —          |

## What you get

The docproc: for every page, its size, its blocks in reading order with their lines and boxes, and its verdict in
`textLayer`; for every page of the original, its route in `metadata.routing`. When no page needs the ATR, this
docproc is the one stored for the document. When a page needs it, the ATR's docproc is the stored one, and this one
is an intermediate that ocr-postprocess merges with it. An office document's text is what the file holds, read in
full; one of its pages needs the ATR by the PDF rule, when it has no text of its own (none outside its header and
footer) and shows a picture, such as a pasted scan, and the ATR then reads that page as it reads a PDF page. A
picture, chart or drawing is a `figure` block with its box and nothing of the picture; with the forced pages, the
pages with `figure` blocks are the ones page-classification reads. In a PDF only raster images are figures; a chart
drawn as vectors is not. When the ATR or page-classification reads an office document, its rendered PDF comes with
it; it is not stored, and every office document's paradata name it by its SHA-512, because its pages are the ones
the docproc's page numbers and boxes refer to.

## Limits

* Unruled tables are read by column, and letter-spaced captions and map labels split into pieces.
* An office document's pages are LibreOffice's, which can break pages differently from Word; the docproc and the
  rendered PDF use the same pages.
* Text inside a picture on an office page that has text of its own (a photo of a page beside a paragraph, a
  caption under a scan) is not read: the page keeps its text, and its `figure` block puts it among the pages for
  page-classification.
* Spreadsheets and text files have no geometry: their pages and lines have no positions.
* The converter was tried on 15 AMČR excavation reports, which showed its defects; there is no accuracy figure.

## Provenance and licence

Every `/reformat` call returns the run's paradata: an RO-Crate `CreateAction` that names the file it read as
`original`, the seed when one was sent, and the docproc it wrote, each by SHA-512; when a page needs the ATR the
docproc is marked as not stored. On the command line, `--paradata-dir` writes a paradata file. The paradata list the
components that ran, each with its licence, as declared in the tool's `para_config.txt`: with the default engine,
permissively licensed libraries only, and the layout-model engine adds only permissive ones. LibreOffice, which
converts DOC and XLS and renders office documents for their pages, is listed with its version whenever a run uses
it, as a fact; the text stays the document's own. An office document's rendered PDF is named among the outputs by
its digest, as a stored distribution, when it is handed over. No licence of an output is computed: the rights in an output follow the source
document ([Licences and paradata](../ecosystem/licences.md)).

The tool owns no block of the [document record](../ecosystem/document-contract.md): it writes docproc, and
ocr-postprocess, the record builder, writes the record from it. Records written by releases before 2.0.0-beta name
the converter as `digital-convert`, the program id it keeps.

## Where it sits

* **The first step of a born-digital document** — [Pipelines → The route through the pipeline](../pipelines.md#the-route-through-the-pipeline)
  and [W2](../pipelines.md#other-workflows). Scans and images go to the ATR instead. The AMČR pipeline calls
  `/reformat`, which calls no other service: the pipeline's orchestrator (Temporal) chains the steps.
* **Mixed documents** — [Pipelines → W3](../pipelines.md#other-workflows). When some pages need the ATR, the whole
  document goes through the ATR with those pages forced, and page-classification classifies those pages and the
  pages with `figure` blocks beside it; ocr-postprocess keeps this docproc's exact lines on the other pages.
* **What follows it.** The record ocr-postprocess builds goes on to [nlp-enrich](nlp-enrich.md) and
  [keyword-extract](keyword-extract.md).
* **Born-digital extraction** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP) (step 6, beside GROBID).
* **The service image** is one of the containerised services —
  [Pipelines → W4](../pipelines.md#w4--containerised-service--api-workflow).

## On other platforms

**SSH Open Marketplace.** Tool record [`jGxgQI`](https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI), "Born-digital document converter: PDF and
office files into structured text without OCR" (created 24 October 2026).

**Galaxy sheet.** The Galaxy wrappers were handed to DARIAH for testing; further Galaxy work is parked during the
AMČR pilot. The sheet describes the wrapper as delivered, for the command-line image at `v1.4.5-beta`, when the
converter still wrote the record.

|                          |                                                                                                                                                                                                                                                                                                      |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**      | one born-digital file per job — `pdf`, `docx` or `xlsx` (ODT, ODS, RTF, DOC and XLS have no datatype on DARIAH's Galaxy); optionally the record to add to — `json`                                                                                                                                   |
| **Parameters**           | page breaks in DOCX (`auto`, `explicit`, `none`); Markdown output                                                                                                                                                                                                                                    |
| **Workflow outputs**     | the document record — `json`, with the pages that need OCR flagged; Markdown — `markdown`; paradata — `json`                                                                                                                                                                                         |
| **Container**            | `ghcr.io/ufal/atrium-digital-convert-digital:<version>` — the command-line image (`api_util/digital_to_json.py`), light engine and headless LibreOffice; it runs the job script Galaxy hands it (the hub-canonical `container_entrypoint.py`). The Docling image is built locally, and not used here |
| **Galaxy tool**          | `atrium_digital_convert` `1.4.5-beta+galaxy0`, in the hub's [`galaxy/`](https://github.com/ufal/atrium-project/tree/test/galaxy) folder with the workflow *ATRIUM born-digital documents to keywords*; for DARIAH's test Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>)                       |
| **Compute**              | CPU                                                                                                                                                                                                                                                                                                  |
| **Network**              | none: no models                                                                                                                                                                                                                                                                                      |
| **Test data**            | four of the PDF and DOCX files `tests/fixtures/digital/make_fixtures.py` generates with the standard library, and an XLSX made the same way, MIT                                                                                                                                                     |
| **Credit**               | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                                                                             |
| **Closest Galaxy tools** | Galaxy's `markitdown` and `grobid` convert born-digital documents but write no ATRIUM record; DARIAH's `atrium_pdf_text_extraction`, on the instance, writes a PDF's text as page-based JSON                                                                                                         |

## Sources

Read from `ufal/atrium-digital-convert` on its `test` branch, which carries release 2.0.0-beta, on 2026-11-21. Earlier
readings were at `v1.4.0-beta` (2026-10-29), `v1.3.0-beta` (2026-10-26), `v1.2.1-beta` (2026-10-19) and, before the
move, `ufal/atrium-llm-enrich` at `v0.8.0`. The Galaxy sheet (2026-11-07) follows `v1.4.5-beta` and the tool's
wrapper in the hub's `galaxy/` folder. This table records **provenance**, not a build instruction.

| Source                                                                                                                        | What was taken from it                                            |
|-------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `README.md`, `docs/how-it-works.md`, `docs/reference/formats.md`                                                              | purpose, the two workflows, the verdicts, the formats, the routes |
| `service/README.md` §§ Endpoints, Errors, Configuration, Limits, How it works; `service/api.py`                               | the HTTP service and its limits                                   |
| `api_util/digital_to_json.py`, `docproc_writer.py`, `digital_pdf.py`, `digital_text.py`, `digital_legacy.py`, `json_to_md.py` | the reading, the checks, the docproc, the Markdown                |
| `para_config.txt`, `LICENSE`                                                                                                  | the licence components, the code licence                          |
| `.env.example`, `tool_limits.py`                                                                                              | the settings named on this page                                   |
| `CONTRIBUTING.md` § Release History, `CITATION.cff`                                                                           | the releases, the move from llm-enrich                            |
| `tests/fixtures/MANIFEST.json`                                                                                                | test data                                                         |
| `DARIAH-ERIC/atrium-galaxy-tools`; `bgruening/galaxytools`                                                                    | the Galaxy analogues                                              |
