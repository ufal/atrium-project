---
title: nlp-enrich workflow
nav_order: 18
status: published
round: 7
issue: 57
repo: atrium-nlp-enrich
role: workflow
authored: true
---

# Linguistic annotation and named entities, kept on the page

*The nlp-enrich workflow.* Tool: [atrium-nlp-enrich](https://ufal.github.io/atrium-nlp-enrich/).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The details of the TEITOK output,
    and the named-entity model in use are documented with the code — in
    the tool's [README](https://github.com/ufal/atrium-nlp-enrich#readme) and
    [`schemas/teitok/README.md`](https://github.com/ufal/atrium-nlp-enrich/blob/master/schemas/teitok/README.md) —
    because they change as the format and the models are refined. Keywords are no longer made
    here: they moved to [keyword-extract](keyword-extract.md) on 1 October 2026 (release
    `v1.0.0-beta`).

## Purpose

Searching and linking archival documents needs more than their raw text: the base form of
each word, its part of speech, the structure of the sentence, and the people, places and
organisations it names. This workflow sends the text lines of each document to LINDAT's
UDPipe 2 and NameTag 3 services, merges their answers, and writes the result as tables, as
CoNLL-U and as TEITOK XML — a TEI-based format that keeps every word tied to its place on the
page image when a page layout is supplied: the OCR's ALTO files, a TEITOK file converted by
flexiconv, or the record of a born-digital PDF.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | tables of text lines (CSV or XLSX with a `text` column) from ocr-postprocess, or plain text (`.txt`, a form feed starting a page), on the command line and over HTTP alike; or the lines of an ATRIUM document record; optionally, for word positions, the original ALTO files or a TEITOK file converted by flexiconv, and the page images; optionally the ATRIUM document record (JSON) to add to — the record digital-convert writes for a born-digital PDF is a layout too |
| **Out**                | CoNLL-U per document; named entities per page (TSV); tokens, lemmas and entities per document (CSV); an entity summary for the collection (CSV); TEITOK XML; a paradata log (JSON); optionally the ATRIUM document record (JSON); over HTTP, a JSON envelope or a ZIP of these files                                                                                                                                                                                           |
| **Runs as**            | a command-line pipeline (four stage scripts, or `run_pipeline.py`); a batch container image; an HTTP service image (`/enrich`, `/enrich_text`, `/jobs`, `/rescale`, `/project_record`); an [Agent Skill](../agent-skills.md)                                                                                                                                                                                                                                                   |
| **Compute**            | CPU; the annotation itself runs on LINDAT's servers                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Network**            | the LINDAT UDPipe 2 and NameTag 3 services, or self-hosted ones set by `UDPIPE_URL` and `NAMETAG_URL`                                                                                                                                                                                                                                                                                                                                                                          |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Component licences** | the UDPipe 2 and NameTag 3 models (CC BY-NC-SA 4.0), through the LINDAT services and their terms of use, on every run. These do not by themselves set the rights in the output: [Licences and paradata](../ecosystem/licences.md)                                                                                                                                                                                                                                              |
| **Record**             | SSH Open Marketplace tool [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X)                                                                                                                                                                                                                                                                                                                                                                               |

## Steps

| # | Step                  | What happens                                                                                                                                                                                                                                                                                                                       | In → out                                                                | Activity                 |
|---|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|--------------------------|
| 1 | Collect the text      | The lines of each document are put in page and line order into one text per document; on request (`--skip-untrustworthy-lines`, `SKIP_UNTRUSTWORTHY_LINES`) the lines ocr-postprocess marked `Trash`, `Garbage` or `Inverted` are left out. A rows file keeps the page and line of every line, and a manifest lists the documents. | CSV, XLSX, TXT → TXT, TSV                                               | —                        |
| 2 | Morphology and syntax | UDPipe 2 tokenises the text and adds lemmas, part-of-speech tags, morphological features and dependency syntax. A long text is sent in pieces cut at line ends, and the answers are joined again.                                                                                                                                  | TXT → CoNLL-U                                                           | Lemmatizing, Tagging     |
| 3 | Named entities        | NameTag 3 finds names of people, places, organisations and other entities in the annotated text, and writes them page by page; the pages come from the rows file.                                                                                                                                                                  | CoNLL-U → TSV                                                           | Named Entity Recognition |
| 4 | Merge and write       | Tokens, lemmas and entities are joined per document into tables, into CoNLL-U with the entities added, and into TEITOK XML. With a layout, each word in TEITOK carries its box on the page; without one, TEITOK keeps the pages and lines of the table. Every TEITOK file is checked against the format before the stage ends.     | CoNLL-U, TSV (+ ALTO, TEITOK, JSON) → CSV, CoNLL-U, TEITOK XML (+ JSON) | —                        |

**The layout** of a document comes from its ALTO file; else from a TEITOK file that flexiconv
converted; else from its born-digital record. The record digital-convert writes for a PDF
(`POST /reformat`) has the size of each page and a box for each line. Word boxes are shared out
from the line boxes, so they are approximate. The boxes are in PDF points: the command line
scales them to the page images (`INPUT_PAGES_DIR`) or to a resolution (`IMAGE_DPI`), and the
service returns them in points. A DOCX record has no boxes.

**An optional stage** converts documents that are not ALTO — PDF, office files, PAGE XML,
hOCR — into TEITOK; with `FLEXICONV_ANNOTATE` (or `run_pipeline.py --with-flexiconv`) they are
then annotated like a table ([Pipelines → W11](../pipelines.md#other-workflows)). The converter
runs from the command line only; the service takes its output as an upload. The tool's
projection of the finished record into the TEITOK header (`/project_record`, opt-in) reads the
page categories and the keywords that [keyword-extract](keyword-extract.md) wrote, so it runs
after that step.

**Rescaling.** `POST /rescale` (or `fix_teitok_bboxes.py` on the command line) rewrites the
boxes of a finished TEITOK file for page images of another size, page by page. For the points of
a born-digital record, give `scale` = the images' DPI / 72.

**When a run stops**, the runner's exit code says why, and the service answers with the matching
HTTP status. LINDAT not answering after its retries is exit 6 (502 `upstream_unavailable`); every
attempt timing out is exit 7 (504); a TEITOK file that fails its check is exit 5 (500). Before the
first stage the runner checks that the stages' `python3` can import what they need; if it cannot,
it stops with exit 3 (500) and says how to fix it. The usage guide's
[exit codes](https://github.com/ufal/atrium-nlp-enrich/blob/test/docs/usage.md#exit-codes) list them all.

## Provenance and licence

The stages write paradata logs, and a whole-pipeline run merges them into one run summary.
Over HTTP the run's provenance comes back with the answer, as a Process Run Crate action
(`paradata`). The paradata lists the components a run used, each with its licence, as declared
in the tool's `para_config.txt`. Every core run uses the UDPipe 2 and NameTag 3 models
(CC BY-NC-SA 4.0) through the LINDAT services, under LINDAT's terms of use; the optional stage
declares its own component (the format converter, GPL-3.0). The paradata's computed label is
therefore CC BY-NC-SA 4.0 for every core run. It is not the licence of the annotations: how the
models' licence and the services' terms bear on the output is an open question
([#78](https://github.com/ufal/atrium-project/issues/78), [#6](https://github.com/ufal/atrium-project/issues/6));
see [Licences and paradata](../ecosystem/licences.md).

In the [document record](../ecosystem/document-contract.md) the tool owns the `entities`
block. Each entity points at its `<name>` in the TEITOK file (`teitok_ref`), and each page with
a surface at its `<surface>` (`pages[].teitok_surface`). When the record cannot be updated, the
runner says so (`[document-json] NOT WRITTEN`) and the service returns `null` in its place; the
other outputs are complete, and the record sent is unchanged.

## Where it sits

* **Fourth stage** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
  It reads the line tables of [ocr-postprocess](ocr-postprocess.md) and the original ALTO;
  [keyword-extract](keyword-extract.md) follows it and reads the record it leaves.
* **The production service of its stage**, the image `ghcr.io/ufal/atrium-nlp-enrich-api` —
  [Pipelines → W4](../pipelines.md#w4--containerised-service--api-workflow).
* **After [digital-convert](digital-convert.md)** for a born-digital PDF: the record it writes
  gives the TEITOK its layout.
* **One route of format adaptation**, into TEITOK — [Pipelines → W11](../pipelines.md#other-workflows).
* **NLP enrichment** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X).
The LINDAT services it calls have their own records: UDPipe and NameTag.

**Galaxy.** Inputs map to `tabular` (or `csv`), `alto`, `png`, `tei` for a converted TEITOK
file and `json` for a record; outputs to `tei` for TEITOK, `tabular` for the tables and for
CoNLL-U (Galaxy has no CoNLL-U datatype), and `json`. The closest tool already in Galaxy is
`stanza_nlp`, which tokenises, tags, parses and finds named entities with local models; UDPipe
and NameTag themselves have been wrapped for Galaxy before, as tools calling LINDAT's services.
The container is the CPU-only service image `ghcr.io/ufal/atrium-nlp-enrich-api:<version>`
(`POST /enrich`, `/enrich_text`, or `/jobs` for a long document); it needs outbound HTTPS to
LINDAT. Test data: the three synthetic documents in `data_samples/` — line tables, ALTO, a page
image and the outputs of every stage.

## Sources

Read from `ufal/atrium-nlp-enrich` at release **`v1.2.0-beta`** (2026-10-26); an earlier reading was
at `v1.1.2-beta` (2026-10-19). This table records **provenance**, not a build instruction.

| Source                                                                                                                                                                              | What was taken from it                                                                                                |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `README.md` §§ TEITOK XML, Workflow Stages, Converting Other Input Formats with flexiconv, REST API Service, Paradata Logs, One-command pipeline run, Exit codes, Where things went | purpose, the step order, the layouts, the outputs, the exit codes                                                     |
| `run_pipeline.py`, `api_1_manifest.sh` … `api_4_stats.sh`, `api_flexiconv.sh`                                                                                                       | the stages, the preflight, the exit codes                                                                             |
| `api_util/build_manifest_row.py`, `line_inputs.py`, `record_layout.py`, `lindat_errors.py`, `bbox_scale.py`                                                                         | the rows file, the input reader shared with the service, the record as a layout, the LINDAT exit codes, the `pt` unit |
| `service/README.md`, `service/api.py`, `service/enrichment.py`                                                                                                                      | the HTTP service: layout inputs, `/rescale`, exit codes as HTTP, partial results                                      |
| `para_config.txt`                                                                                                                                                                   | the licence components                                                                                                |
| `config_api.txt`                                                                                                                                                                    | the backing-service endpoints                                                                                         |
| `Dockerfile`, `.github/production-image.json`                                                                                                                                       | the images                                                                                                            |
| `CITATION.cff`, `CONTRIBUTING.md` § Release History                                                                                                                                 | the release and its date; what changed since `v0.21.0`                                                                |
| `data_samples/`                                                                                                                                                                     | test data                                                                                                             |
| SSH Open Marketplace `EMhu3X`                                                                                                                                                       | the record identifier                                                                                                 |
| `galaxyproject/tools-iuc` (`stanza`); `lappsgrid-incubator/GalaxyMods` (`tools/lindat`)                                                                                             | the Galaxy analogues                                                                                                  |
