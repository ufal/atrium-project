---
title: translator workflow
nav_order: 17
status: published
round: 7
issue: 57
repo: atrium-translator
role: workflow
authored: true
---

# Translating XML documents with a protected domain vocabulary

*The translator workflow.* Tool section: [translator](../tools/translator/index.md).

## Purpose

Archival collections hold text inside XML: OCR transcriptions in ALTO XML, and structured
metadata records such as those of the Archaeological Map of the Czech Republic (AMČR). This
workflow translates that text — into English by default — and writes it back into the same
document, so that tags, namespaces, attributes and, for ALTO, the position of every word
survive, and the result stays valid against its schema. Domain terms can be held to their
established translations from a controlled vocabulary, so that an archaeological term is
rendered the same way in every document.

## At a glance

|                    |                                                                                                                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | ALTO XML pages, or any well-formed XML with a list of the fields to translate (XPaths); files, folders or lists of URLs; optionally a vocabulary (CSV)                            |
| **Out**            | the translated document (same format); a translation log pairing source and target text (CSV); a paradata log (JSON); optionally the ATRIUM document record (JSON)                |
| **Runs as**        | a command-line tool (`main.py`); a container image; an HTTP service image (`POST /translate`); an [Agent Skill](../agent-skills.md)                                               |
| **Compute**        | CPU; a GPU only for a self-hosted translation model                                                                                                                               |
| **Network**        | the LINDAT translation service (the default backend) and the LINDAT UDPipe service (vocabulary matching); the Hugging Face Hub for the language-identification model on first use |
| **Code licence**   | MIT                                                                                                                                                                               |
| **Output licence** | computed per run: a default run is CC BY-NC-SA 4.0; a permissive run can be assembled (see below)                                                                                 |
| **Records**        | SSH Open Marketplace tool [`CizIUW`](https://marketplace.sshopencloud.eu/tool-or-service/CizIUW) and workflow [`13eHAZ`](https://marketplace.sshopencloud.eu/workflow/13eHAZ)     |

## Steps

| # | Step                                   | What happens                                                                                                                                                                                                                                                                                                                                                               | In → out    | Activity    |
|---|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|-------------|
| 1 | Prepare a domain vocabulary (optional) | The bundled harvester collects Czech–English term pairs from the AMČR vocabularies (over OAI-PMH) and the TEATER thesaurus, each pair pointing back to the concept it came from; a vocabulary of one's own in the same CSV form works as well.                                                                                                                             | → CSV       | Collecting  |
| 2 | Choose the mode and the fields         | ALTO transcriptions are translated in ALTO mode, which works on the words of each text line. For metadata records, the fields to translate are listed as XPaths; namespaces and OAI-PMH envelopes are handled by the tool.                                                                                                                                                 | ALTO, XML   | —           |
| 3 | Identify the source language           | A language-identification model detects the language of each text block (ALTO) or field (metadata), so a record that mixes languages is handled piece by piece. Naming the source language skips detection.                                                                                                                                                                | —           | —           |
| 4 | Protect domain terms (optional)        | Vocabulary terms found in the text are replaced by placeholders before translation and restored as their agreed translations afterwards; multi-word terms are matched first, single words by lemma. Language-model backends receive the vocabulary as a glossary instead.                                                                                                  | CSV         | Lemmatizing |
| 5 | Translate                              | The text goes to the chosen backend: the LINDAT translation service (CUBBITT, the default), a self-hosted CTranslate2 model, or an OpenAI-compatible language-model API. Long texts are split at sentence boundaries first.                                                                                                                                                | —           | Translating |
| 6 | Rebuild and validate the document      | ALTO: each text block is translated as a whole and line by line; the fluent whole-block translation is then divided among the original lines and written into the original word elements. Metadata: the translation replaces the source text, or is added beside it with language labels. Metadata output can be validated against an XSD schema, such as the AMČR schema. | → ALTO, XML | —           |
| 7 | Review and record provenance           | A translation log beside each output pairs source and target text line by line or field by field, for review. The paradata log records what was run and the licence it resolved to; the document record, on request, notes the languages, the backend and the translated file.                                                                                             | → CSV, JSON | —           |

The vocabulary step is its own workflow on Pipelines —
[W7, vocabulary harvesting and review](../pipelines.md#w7--vocabulary-harvesting--review-the-translators-half).

## What you get

* **The same document in another language** — `<name>_<target language>.<extension>`, every tag
  and namespace in place; for ALTO, every line where it was.
* **A review log** — `<name>_log.csv`, with the source and the translated text side by side.
* **Consistent terminology** — every protected term carries its agreed translation, and the
  paradata counts the protected terms per document.
* **A provenance record** — the paradata log of the run, with the licence it resolved to.

The translator's output is an end product: an edition for readers and for publication. No later
stage of the pipeline reads it; the [document record](../ecosystem/document-contract.md)
refers to it.

## Limits

* **Word positions in translated ALTO are approximate.** Line boundaries are exact; how the
  words of a line are spread over its word elements is constructed, because a translation has
  a different number of words.
* **Schema validation applies to metadata output.** ALTO output keeps the structure of its
  input but is not validated against the ALTO schema.
* **Language coverage is the backend's.** CUBBITT is centred on Czech; other language pairs
  need another backend.
* **Placeholders protect terms only for the LINDAT backend.** Language-model backends get a
  glossary instead, and the self-hosted neural translation models receive no vocabulary.

## Provenance and licence

Each run writes `<stamp>_translator.json`, the paradata log. The licence of the run is
computed from the components it actually used, as declared in the tool's `para_config.txt`;
the most restrictive one wins:

| Component                                 | Licence                    | Counts when                                |
|-------------------------------------------|----------------------------|--------------------------------------------|
| LINDAT translation (CUBBITT)              | CC BY-NC-SA 4.0            | the default backend is used                |
| language-identification model (FastText)  | CC BY-NC 4.0               | the source language is detected, not given |
| UDPipe 2 models / engine                  | CC BY-NC-SA 4.0 / MPL 2.0  | vocabulary terms are matched by lemma      |
| AMČR vocabularies, TEATER thesaurus       | CC BY-NC 4.0               | a vocabulary built from them is loaded     |
| CTranslate2; EuroLLM, MADLAD-400; OPUS-MT | MIT; Apache-2.0; CC BY 4.0 | a self-hosted model of these families      |
| NLLB-200                                  | CC BY-NC 4.0               | a self-hosted NLLB-200 model               |
| OpenAI-compatible language-model API      | provider terms             | the language-model backend is used         |

**A permissive run** needs all three: a self-hosted model of a permissive family (EuroLLM,
MADLAD-400 or OPUS-MT), the source language named explicitly, and no AMČR or TEATER vocabulary.
The full table is on [Reference → Licence](../tools/translator/reference.md#licence-is-computed-not-declared).

In the [document record](../ecosystem/document-contract.md) the tool owns the `translations`
block and records the translated file as `derived_from.translated_xml`.

## Where it sits

* **Translation branch** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
  It reads the per-page ALTO that alto-postprocess writes; its output ends that branch.
* **Translation** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP), where it translates AMČR
  metadata records.
* Also used in [W4](../pipelines.md#w4--containerised-service--api-workflow) (as a service),
  [W5](../pipelines.md#w5--agent-skill-workflow) (from a coding agent),
  [W6](../pipelines.md#w6--e2e-smoke-the-integration-contract) (the end-to-end test) and
  [W7](../pipelines.md#w7--vocabulary-harvesting--review-the-translators-half) (the vocabulary).

## On other platforms

**SSH Open Marketplace.** Tool record [`CizIUW`](https://marketplace.sshopencloud.eu/tool-or-service/CizIUW);
workflow record [`13eHAZ`](https://marketplace.sshopencloud.eu/workflow/13eHAZ), whose steps are the
seven above. Related records: LINDAT Translation, UDPipe.

**Galaxy sheet.**

|                          |                                                                                                                                                                                                             |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**      | a collection of documents — `alto` or `xml`; for metadata mode, the list of fields — `txt`; optionally the vocabulary — `csv`                                                                               |
| **Parameters**           | target language; source language (or detection); backend; replace or append; optional XSD schema                                                                                                            |
| **Workflow outputs**     | translated documents — `alto` or `xml`; translation logs — `tabular` (CSV); paradata — `json`; document record — `json`                                                                                     |
| **Container**            | `ghcr.io/ufal/atrium-translator:<version>` — the command-line image                                                                                                                                         |
| **Compute**              | CPU                                                                                                                                                                                                         |
| **Network**              | the LINDAT translation and UDPipe services, and the Hugging Face Hub for the language-identification model — or a self-hosted model with the source language given                                          |
| **Credentials**          | an API key only for the language-model backend, passed through Galaxy's credentials mechanism                                                                                                               |
| **Test data**            | `data_samples/` in the tool repository — AMČR metadata records with their translations and logs                                                                                                             |
| **Credit**               | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                    |
| **Closest Galaxy tools** | none translates; the language-model tools (`llm_hub`, `chatgpt_openai_api`) and the `xpath` tool are the nearest, and DARIAH's `gate-cloud-client` shows the pattern for a tool that calls a remote service |

## Sources

Read from `ufal/atrium-translator` at release **`v1.1.0-beta`** (branch **`master`**, commit
`a5d2213`) and from this site's translator section. This table records **provenance**, not a
build instruction.

| Source                                                                                            | What was taken from it                                |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| `README.md` §§ Features, Usage, Logic Overview, ALTO Dual-Pass Reconstruction, License & Citation | purpose, the step order, the permissive recipe        |
| `main.py`, `utils.py`, `processors/*`, `load_vocab.py`                                            | the steps, the backends, vocabulary protection        |
| `para_config.txt`                                                                                 | the licence components                                |
| `service/api.py`, `Dockerfile`                                                                    | the images, the HTTP service; no model weights inside |
| `data_samples/`                                                                                   | test data                                             |
| `CITATION.cff`                                                                                    | credit                                                |
| `atrium-project/docs_site/tools/translator/*`, `docs_site/pipelines.md` § W7                      | outputs, design limits, the vocabulary workflow       |
| SSH Open Marketplace `CizIUW`, `13eHAZ`                                                           | record identifiers                                    |
| `usegalaxy-eu/usegalaxy-eu-tools`; `bgruening/galaxytools`; `DARIAH-ERIC/atrium-galaxy-tools`     | the Galaxy analogues and conventions                  |
