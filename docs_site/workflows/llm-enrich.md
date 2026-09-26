---
title: llm-enrich workflow
nav_order: 19
status: published
round: 7
issue: 57
repo: atrium-llm-enrich
role: workflow
authored: true
---

# Mapping archival text onto controlled vocabularies with a language model

*The llm-enrich workflow.* Tool: [atrium-llm-enrich](https://ufal.github.io/atrium-llm-enrich/).

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The models, the backends, the
    prompts and the form in which text is given to the model are documented with the code —
    in the tool's [README](https://github.com/ufal/atrium-llm-enrich#readme) — because they
    change as models are compared and chosen.

## Purpose

Archaeological archives describe their holdings with controlled vocabularies: the keyword
lists of the Archaeological Map of the Czech Republic (AMČR) and the TEATER thesaurus. This
workflow reads archival text — line by line or a whole document at a time — and asks a large
language model to map it onto those vocabularies, giving Czech and English keywords, a
thematic category and a confidence score. The answer is held to the vocabulary: the model can
only choose terms that exist in it, and anything else is dropped rather than guessed. The same
tool converts born-digital documents — PDF and DOCX files with a usable text layer — into the
ATRIUM document record without OCR, keeping their pages, headings, running headers and
footers, footnotes and tables.

## At a glance

|                    |                                                                                                                                                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | text lines (CSV from alto-postprocess, TEITOK XML from nlp-enrich) or whole documents (Markdown, plain text); for conversion, PDF and DOCX                                                                                   |
| **Out**            | one enrichment file per document (JSON); a paradata log (JSON); from the converter, the ATRIUM document record (JSON)                                                                                                        |
| **Runs as**        | command-line tools with local models (`transformers`, `vLLM`) or remote ones (OpenRouter, Ollama); container images; an HTTP service image; an [Agent Skill](../agent-skills.md)                                             |
| **Compute**        | one or more GPUs for local models; none when a remote provider answers; the converter runs on a CPU                                                                                                                          |
| **Network**        | the AIS CR services, to harvest the vocabularies; the Hugging Face Hub for local models, or the remote provider; none for the converter, whose optional layout-model engine fetches its models once, when its image is built |
| **Code licence**   | MIT                                                                                                                                                                                                                          |
| **Output licence** | CC BY-NC 4.0 at minimum when the AMČR or TEATER vocabulary is used; the terms of the model or of the remote provider apply on top                                                                                            |
| **Record**         | SSH Open Marketplace tool [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo)                                                                                                                             |

## Steps

| # | Step                    | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | In → out                                    | Activity                    |
|---|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|-----------------------------|
| 1 | Build the vocabulary    | The AMČR keyword lists and the TEATER thesaurus are harvested and arranged into one nested term list, each term pointing back to its source concept.                                                                                                                                                                                                                                                                                                                                 | → JSON, CSV                                 | Collecting                  |
| 2 | Prepare the text        | Lines are read from the line tables or from TEITOK; whole documents are turned into Markdown — a PDF or DOCX by way of its document record, so the model reads what the record stores. Born-digital PDF and DOCX files can be converted to the document record here instead of going through OCR, by a light default engine or, on request, a layout-model engine for complex PDFs. A PDF whose text layer comes from an earlier OCR run is refused: it belongs to alto-postprocess. | CSV, TEITOK XML, PDF, DOCX → Markdown, JSON | Converting                  |
| 3 | Map onto the vocabulary | For each line or passage the model returns keywords in Czech and English, a category and a confidence. Its output is constrained by a schema whose allowed values are the vocabulary's terms.                                                                                                                                                                                                                                                                                        | → JSON                                      | Enriching, Content Analysis |
| 4 | Record the result       | One enrichment file per document gathers the answers; a paradata log records the model, the backend and the run.                                                                                                                                                                                                                                                                                                                                                                     | → JSON                                      | —                           |

## Provenance and licence

Every run writes a paradata log. The vocabularies are CC BY-NC 4.0, so any output that uses
them is non-commercial at minimum. Each local model carries its own licence, and a remote
provider its own terms; both apply to what the model produced. The born-digital converter's
default engine uses permissively licensed libraries, so its records carry MIT; the optional
layout-model engine adds model weights under CDLA-Permissive-2.0, which places no terms on the
output and leaves that unchanged. The source document's own licence applies to its text.

In the [document record](../ecosystem/document-contract.md) the tool owns the `enrichment`
block; its converter originates the positional text layer of a born-digital document.

## Where it sits

* **Fifth stage** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
* **The converter of the born-digital pipeline**, which replaces the OCR stages for documents
  that already have a text layer — [Pipelines → W2](../pipelines.md#other-workflows).
* **The document-understanding benchmark** — [Pipelines → W10](../pipelines.md#other-workflows).
* **Born-digital text extraction** and **vocabulary keywords** steps of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo).

**Galaxy.** Inputs map to `tabular`, `tei`, `markdown`, `txt`, `pdf` and `docx`; outputs to
`json`. Inside ATRIUM, DARIAH's Galaxy tools already chain PDF text extraction with
vocabulary-driven information extraction (task 4.2.1). Among Galaxy's own tools, `llm_hub`
runs language models hosted by the Galaxy server, and `grobid` and `markitdown` convert
born-digital documents.

## Sources

Read from `ufal/atrium-llm-enrich` at release **`v0.7.0`**; the converter's engines, route
and licence from branch **`test`** at `c3575f5` (2026-09-25), which is **not yet released**.
This table records **provenance**, not a build instruction.

| Source                                                                                                                                                                | What was taken from it                            |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `README.md` §§ intro, Backends at a glance, Vocabulary Harvesting, Inputs and Outputs                                                                                 | purpose, the steps, the inputs and outputs        |
| `llm_client_shared.py`, `vocab_build.py`, `api_util/digital_to_json.py`                                                                                               | constrained output; the vocabulary; the converter |
| `para_config.txt`                                                                                                                                                     | the licence components                            |
| `test` @ `c3575f5` — `api_util/digital_to_json.py`, `api_util/doc_to_visual_md.py`, `requirements_digital.txt`, `requirements_digital_docling.txt`, `para_config.txt` | the converter's engines and route; its licence    |
| `service/README.md`                                                                                                                                                   | the HTTP service                                  |
| SSH Open Marketplace `j9fqxo`                                                                                                                                         | the record identifier                             |
| `DARIAH-ERIC/atrium-galaxy-tools`; `bgruening/galaxytools`                                                                                                            | the Galaxy analogues                              |
