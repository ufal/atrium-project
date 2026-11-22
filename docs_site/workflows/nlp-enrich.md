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

*The nlp-enrich workflow.* Tool: [atrium-nlp-enrich](https://github.com/ufal/atrium-nlp-enrich).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licences of the components it uses. The details of the TEITOK output,
    and the named-entity model in use are documented with the code — in
    the tool's [README](https://github.com/ufal/atrium-nlp-enrich/blob/test/README.md) and
    [`schemas/teitok/README.md`](https://github.com/ufal/atrium-nlp-enrich/blob/test/schemas/teitok/README.md) —
    because they change as the format and the models are refined. Keywords are not made here:
    [keyword-extract](keyword-extract.md) makes them.

## Purpose

Searching and linking archival documents needs more than their raw text: the base form of
each word, its part of speech, the structure of the sentence, and the people, places and
organisations it names. In the AMČR pipeline this workflow reads the document's ATRIUM record,
which ocr-postprocess builds: its lines are the text, and their boxes the page layout. It sends
the text to LINDAT's UDPipe 2 and NameTag 3 services, merges their answers, and adds the
linguistic layer and the named entities to the record. It also writes the document as TEITOK
XML, a TEI-based format that keeps every word tied to its place on the page image, with CoNLL-U
and tables beside it. For research collections the same stages run over tables of text lines,
with the OCR's ALTO files or a TEITOK file converted by flexiconv as the layout.

Until the terms of LINDAT's services are settled ([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)),
AMČR does not publish outputs made through them: the linguistic layer, the entities, the TEITOK
file and the English metadata.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                                                                                                          |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | the document's ATRIUM record (JSON, schema 2.0), whose lines are the text and whose line boxes are the layout. For research and batch use: tables of text lines (CSV or XLSX with a `text` column, such as ocr-postprocess's), or plain text (`.txt`, a form feed starting a page); optionally, for word positions, the original ALTO files or a TEITOK file converted by flexiconv, and the page images |
| **Out**                | the record with each line's lemma, part of speech and features, and its `entities` block; TEITOK XML; CoNLL-U per document; named entities per page (TSV); tokens, lemmas and entities per document (CSV); an entity summary for the collection (CSV); a paradata log (JSON); over HTTP, a JSON envelope or a ZIP of these files                                                                         |
| **Runs as**            | a command-line pipeline (four stage scripts, or `run_pipeline.py`); a batch container image; an HTTP service image (`/enrich`, `/enrich_text`, `/jobs`, `/rescale`, `/project_record`); an [Agent Skill](../agent-skills.md)                                                                                                                                                                             |
| **Compute**            | CPU; the annotation itself runs on LINDAT's servers                                                                                                                                                                                                                                                                                                                                                      |
| **Network**            | the LINDAT UDPipe 2 and NameTag 3 services, or self-hosted ones set by `UDPIPE_URL` and `NAMETAG_URL`                                                                                                                                                                                                                                                                                                    |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Component licences** | the UDPipe 2 and NameTag 3 models (CC BY-NC-SA 4.0), through the LINDAT services and their terms of use, on every run; the optional converter flexiconv (MIT). No licence of an output is computed: [Licences and paradata](../ecosystem/licences.md)                                                                                                                                                    |
| **Record**             | SSH Open Marketplace tool [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X)                                                                                                                                                                                                                                                                                                         |

## Steps

| #   | Step                  | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                           | In → out                                                                    | Activity                 |
|-----|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|--------------------------|
| 1   | Collect the text      | The lines of each document are put in page and line order into one text per document. From a record: its lines with text, less those ocr-postprocess categorised `Trash` or `Empty`. From a table: all its rows, or on request (`--skip-untrustworthy-lines`, `skip_untrustworthy_lines`) all but its `Trash` rows. A rows file keeps the page and line of every line, and a manifest lists the documents.                                             | JSON, CSV, XLSX, TXT → TXT, TSV                                             | —                        |
| 2   | Morphology and syntax | UDPipe 2 tokenises the text and adds lemmas, part-of-speech tags, morphological features and dependency syntax. A long text is sent in pieces cut at line ends, and the answers are joined again.                                                                                                                                                                                                                                                      | TXT → CoNLL-U                                                               | Lemmatizing, Tagging     |
| 3   | Named entities        | NameTag 3 finds names of people, places, organisations and other entities in the annotated text, and writes them page by page; the pages come from the rows file.                                                                                                                                                                                                                                                                                      | CoNLL-U → TSV                                                               | Named Entity Recognition |
| 4   | Merge and write       | Tokens, lemmas and entities are joined per document into tables, into CoNLL-U with the entities added, and into TEITOK XML. With a layout, each word in TEITOK carries its box on the page; without one, TEITOK keeps the pages and lines of the text. Every TEITOK file is checked against the format before the stage ends. With a record, each line gets the lemma, part of speech and features of its head word, and the record gets the entities. | CoNLL-U, TSV (+ record, ALTO, TEITOK) → CSV, CoNLL-U, TEITOK XML (+ record) | —                        |

**The layout** of a document comes from its ALTO file; else from a TEITOK file that flexiconv
converted; else from its record. In the AMČR pipeline only the record is used: no ALTO is produced
or stored. The record has the size of each page and a box for each line, so word boxes are shared
out from the line boxes and are approximate; a line whose box is only its block's gets none. The
boxes are in the record's coordinate space, PDF points: the command line scales them to the page
images (`INPUT_PAGES_DIR`) or to a resolution (`IMAGE_DPI`), and the service returns them in
points. A record without boxes, a spreadsheet's or a text file's, gives the pages and lines only.

**An optional stage** converts documents that are not ALTO — PDF, office files, PAGE XML,
hOCR — into TEITOK; with `FLEXICONV_ANNOTATE` (or `run_pipeline.py --with-flexiconv`) they are
then annotated like a table ([Pipelines → W11](../pipelines.md#other-workflows)). The converter
runs from the command line only; the service takes its output as an upload. The tool's
projection of the finished record into the TEITOK header (`/project_record`, opt-in) reads the
page categories and the keywords that [keyword-extract](keyword-extract.md) wrote, so it runs
after that step.

**Rescaling.** `POST /rescale` (or `fix_teitok_bboxes.py` on the command line) rewrites the
boxes of a finished TEITOK file for page images of another size, page by page. For the points of
a record, give `scale` = the images' DPI / 72.

**When a run stops**, the runner's exit code says why, and the service answers with the matching
HTTP status. LINDAT not answering after its retries is exit 6 (502 `upstream_unavailable`); every
attempt timing out is exit 7 (504); a TEITOK file that fails its check is exit 5 (500). Before the
first stage the runner checks that the stages' `python3` can import what they need; if it cannot,
it stops with exit 3 (500) and says how to fix it. A record that was asked for and not written
fails the run as well (exit 1, 502); the runner's `[document-json] NOT WRITTEN` line names the
cause. The usage guide's
[exit codes](https://github.com/ufal/atrium-nlp-enrich/blob/test/docs/usage.md#exit-codes) list them all.

## Provenance and licence

The stages write paradata logs, and a whole-pipeline run merges them into one run summary.
Over HTTP the run's paradata come back with the answer, as a Process Run Crate action
(`paradata`): the record read and the record and TEITOK written, as AMČR distributions by name
and SHA-512. The paradata list the components a run used, each with its licence or terms, as
declared in the tool's `para_config.txt`. Every core run uses the UDPipe 2 and NameTag 3 models
(CC BY-NC-SA 4.0) through the LINDAT services, under LINDAT's terms of use; the optional stage
declares its own component (the format converter flexiconv, MIT). No licence of an output is
computed: the rights in an output follow the source document
([Licences and paradata](../ecosystem/licences.md)).

In the [document record](../ecosystem/document-contract.md) the tool owns the `entities`
block and each line's `lemma`, `upos`, `feats` and `teitok_ref`: the lemma, part of speech and
features of the line's head word, and the sentence it belongs to in the TEITOK file. Each entity
points at its `<name>` in the TEITOK file (`teitok_ref`), and each page with a surface at its
`<surface>` (`pages[].teitok_surface`). The record carries no run data.

## Where it sits

* **After [ocr-postprocess](ocr-postprocess.md)**, the record builder, in the AMČR pipeline: the
  record's lines are its text and, with their boxes, the TEITOK file's layout, whether they came
  from a born-digital text layer, the ATR (AIS CR's text-recognition service) or both.
  [keyword-extract](keyword-extract.md) follows it and reads the record it leaves —
  [Pipelines → The route through the pipeline](../pipelines.md#the-route-through-the-pipeline) and
  [W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
* **The production service of its step**, the image `ghcr.io/ufal/atrium-nlp-enrich-api` —
  [Pipelines → W4](../pipelines.md#w4--containerised-service--api-workflow).
* **One route of format adaptation**, into TEITOK, outside the pipeline —
  [Pipelines → W11](../pipelines.md#other-workflows).
* **NLP enrichment** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X).
The LINDAT services it calls have their own records: [UDPipe](https://marketplace.sshopencloud.eu/tool-or-service/i6piia) and [NameTag](https://marketplace.sshopencloud.eu/tool-or-service/nMF4rm).

**Galaxy sheet.** The Galaxy wrappers were handed to DARIAH for testing; further Galaxy work is parked during the
AMČR pilot. The sheet describes the wrapper as delivered, for the batch image at `v1.3.4-beta`.

|                          |                                                                                                                                                                                                                                                                                                      |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**      | a line table — `csv` with a `text` column (the line table of ocr-postprocess), or `txt`, `xlsx`; optionally its ALTO — `xml`; a document record — `json`                                                                                                                                             |
| **Parameters**           | whether the lines marked untrustworthy are left out; the four stages always run and TEITOK is always written                                                                                                                                                                                         |
| **Workflow outputs**     | CoNLL-U with `NER=` per word — `tabular` (no `conllu` datatype on DARIAH's Galaxy); tokens — `csv`; entities per page — `csv`; TEITOK — `tei`; paradata — `json`; document record — `json`                                                                                                           |
| **Container**            | `ghcr.io/ufal/atrium-nlp-enrich:<version>` — the batch image (`run_pipeline.py`); it runs the job script Galaxy hands it (the hub-canonical `container_entrypoint.py`). Its paths come only from a config file, so a job script writes one with absolute paths. The service image `-api` is not used |
| **Galaxy tool**          | `atrium_nlp_enrich` `1.3.4-beta+galaxy0`, in the hub's [`galaxy/`](https://github.com/ufal/atrium-project/tree/test/galaxy) folder with the workflow *ATRIUM OCR to keywords*; for DARIAH's test Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>)                                               |
| **Compute**              | CPU                                                                                                                                                                                                                                                                                                  |
| **Network**              | outbound HTTPS to LINDAT UDPipe (`czech-pdt-ud-2.15-241121`) and NameTag 3 (`nametag3-multilingual-onto-260521`); Czech only                                                                                                                                                                         |
| **Credentials**          | none                                                                                                                                                                                                                                                                                                 |
| **Test data**            | one of the synthetic documents in `data_samples/` — its line table and ALTO — the line table the ocr-postprocess wrapper writes for a two-page CSV, and a table without a `text` column for the error test                                                                                           |
| **Credit**               | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                                                                             |
| **Closest Galaxy tools** | `stanza_nlp`, which tokenises, tags, parses and finds named entities with local models; UDPipe and NameTag themselves have been wrapped for Galaxy before, as tools calling LINDAT's services                                                                                                        |

## Sources

Read from `ufal/atrium-nlp-enrich` on its `test` branch, which carries release 2.0.0-beta, on 2026-11-21.
Earlier readings were at `v1.3.0-beta` (2026-10-29), `v1.2.0-beta` (2026-10-26) and `v1.1.2-beta` (2026-10-19).
This table records **provenance**, not a build instruction.
The Galaxy sheet (2026-11-07) follows `v1.3.4-beta` and the tool's wrapper in the hub's `galaxy/` folder (#66).

| Source                                                                                                                                                                                                 | What was taken from it                                                                                                |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `README.md` §§ TEITOK XML, Workflow Stages, Converting Other Input Formats with flexiconv, REST API Service, Paradata Logs, One-command pipeline run, Exit codes, Where things went (at `v1.3.0-beta`) | purpose, the step order, the layouts, the outputs, the exit codes                                                     |
| `README.md`, `docs/how-it-works.md`, `docs/usage.md`, `service/README.md`, `run_pipeline.py`, `api_util/record_layout.py`, `service/api.py`, `service/enrichment.py` (on `test`)                       | the record as text and layout, the fields written, an unwritten record failing the run, the step's place on the route |
| `run_pipeline.py`, `api_1_manifest.sh` … `api_4_stats.sh`, `api_flexiconv.sh`                                                                                                                          | the stages, the preflight, the exit codes                                                                             |
| `api_util/build_manifest_row.py`, `line_inputs.py`, `record_layout.py`, `lindat_errors.py`, `bbox_scale.py`                                                                                            | the rows file, the input reader shared with the service, the record as a layout, the LINDAT exit codes, the `pt` unit |
| `service/README.md`, `service/api.py`, `service/enrichment.py`                                                                                                                                         | the HTTP service: layout inputs, `/rescale`, exit codes as HTTP, partial results                                      |
| `para_config.txt`                                                                                                                                                                                      | the licence components                                                                                                |
| `config_api.txt`                                                                                                                                                                                       | the backing-service endpoints                                                                                         |
| `Dockerfile`, `.github/production-image.json`                                                                                                                                                          | the images                                                                                                            |
| `CITATION.cff`, `CONTRIBUTING.md` § Release History                                                                                                                                                    | the release and its date; what changed since `v0.21.0`                                                                |
| `data_samples/`                                                                                                                                                                                        | test data                                                                                                             |
| SSH Open Marketplace `EMhu3X`                                                                                                                                                                          | the record identifier                                                                                                 |
| `galaxyproject/tools-iuc` (`stanza`); `lappsgrid-incubator/GalaxyMods` (`tools/lindat`)                                                                                                                | the Galaxy analogues                                                                                                  |
