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
    the named-entity model in use and the keyword options are documented with the code — in
    the tool's [README](https://github.com/ufal/atrium-nlp-enrich#readme) and
    [`schemas/teitok/README.md`](https://github.com/ufal/atrium-nlp-enrich/blob/master/schemas/teitok/README.md) —
    because they change as the format and the models are refined.

## Purpose

Searching and linking archival documents needs more than their raw text: the base form of
each word, its part of speech, the structure of the sentence, and the people, places and
organisations it names. This workflow sends the text lines of each document to LINDAT's
UDPipe 2 and NameTag 3 services, merges their answers, and writes the result as tables, as
CoNLL-U and as TEITOK XML — a TEI-based format that, when the OCR's ALTO files are supplied,
keeps every word tied to its place on the page image.

## At a glance

|                    |                                                                                                                                                                                                                                  |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | tables of text lines (CSV or XLSX with a `text` column) from alto-postprocess; optionally the original ALTO files and the page images, for word positions                                                                        |
| **Out**            | CoNLL-U per document; named entities per page (TSV); tokens, lemmas and entities per document (CSV); an entity summary for the collection (CSV); TEITOK XML; a paradata log (JSON); optionally the ATRIUM document record (JSON) |
| **Runs as**        | a command-line pipeline (four stages, or `run_pipeline.py`); a container image; an HTTP service image (`POST /enrich`); an [Agent Skill](../agent-skills.md)                                                                     |
| **Compute**        | CPU; the annotation itself runs on LINDAT's servers                                                                                                                                                                              |
| **Network**        | the LINDAT UDPipe 2 and NameTag 3 services                                                                                                                                                                                       |
| **Code licence**   | MIT                                                                                                                                                                                                                              |
| **Output licence** | CC BY-NC-SA 4.0 at minimum, because the UDPipe and NameTag models are used on every run                                                                                                                                          |
| **Record**         | SSH Open Marketplace tool [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X)                                                                                                                                 |

## Steps

| # | Step                  | What happens                                                                                                                                                                                      | In → out                                         | Activity                 |
|---|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|--------------------------|
| 1 | Collect the text      | The lines of each document are gathered in page and line order into one text per document, with a manifest that keeps track of where every line came from.                                        | CSV → TXT, TSV                                   | —                        |
| 2 | Morphology and syntax | UDPipe 2 tokenises the text and adds lemmas, part-of-speech tags, morphological features and dependency syntax.                                                                                   | TXT → CoNLL-U                                    | Lemmatizing, Tagging     |
| 3 | Named entities        | NameTag 3 finds names of people, places, organisations and other entities in the annotated text.                                                                                                  | CoNLL-U → TSV                                    | Named Entity Recognition |
| 4 | Merge and write       | Tokens, lemmas and entities are joined per document into tables, into CoNLL-U with the entities added, and into TEITOK XML; with the ALTO files, each word in TEITOK carries its box on the page. | CoNLL-U, TSV (+ ALTO) → CSV, CoNLL-U, TEITOK XML | —                        |

**Optional stages** add keywords per page or per document, and convert documents that are not
ALTO — PDF, office files, PAGE XML, hOCR — into TEITOK before annotation
([Pipelines → W11](../pipelines.md#other-workflows)). The converter runs from the command line
only.

## Provenance and licence

The stages write paradata logs, and a whole-pipeline run merges them into one run summary.
The licence of a run is computed from the components it used, as declared in the tool's
`para_config.txt`; the most restrictive one wins. The UDPipe 2 and NameTag 3 models are
CC BY-NC-SA 4.0 and take part in every run, so every core run's output is CC BY-NC-SA 4.0;
the optional stages declare their own components (the format converter, for example, is
GPL-3.0).

In the [document record](../ecosystem/document-contract.md) the tool owns the `entities`
block.

## Where it sits

* **Fourth stage** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
  It reads the line tables of alto-postprocess and the original ALTO, and its TEITOK is read by
  llm-enrich.
* **One route of format adaptation**, into TEITOK — [Pipelines → W11](../pipelines.md#other-workflows).
* **The review half of the vocabulary workflow** — the reviewed SKOS vocabulary
  ([SKOS & the ATRIUM vocabulary](../contracts/skos.md)).
* **NLP enrichment** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X).
The LINDAT services it calls have their own records: UDPipe and NameTag.

**Galaxy.** Inputs map to `tabular` (or `csv`), `alto` and `png`; outputs to `tei` for TEITOK,
`tabular` for the tables and for CoNLL-U (Galaxy has no CoNLL-U datatype), and `json`. The
closest tool already in Galaxy is `stanza_nlp`, which tokenises, tags, parses and finds named
entities with local models; UDPipe and NameTag themselves have been wrapped for Galaxy before,
as tools calling LINDAT's services.

## Sources

Read from `ufal/atrium-nlp-enrich` at release **`v0.21.0`**. This table records
**provenance**, not a build instruction.

| Source                                                                                  | What was taken from it                                    |
|-----------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `README.md` §§ TEITOK XML, Workflow Stages, Inputs and Outputs, flexiconv               | purpose, the step order, the outputs, the optional stages |
| `para_config.txt`                                                                       | the licence components                                    |
| `service/README.md`                                                                     | the HTTP service                                          |
| SSH Open Marketplace `EMhu3X`                                                           | the record identifier                                     |
| `galaxyproject/tools-iuc` (`stanza`); `lappsgrid-incubator/GalaxyMods` (`tools/lindat`) | the Galaxy analogues                                      |
