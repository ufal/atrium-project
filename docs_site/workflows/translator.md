---
title: translator workflow
nav_order: 17
status: published
round: 8
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

|                        |                                                                                                                                                                                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | ALTO XML pages, or any well-formed XML with a list of the fields to translate (XPaths); files, folders or lists of URLs; optionally a vocabulary (CSV)                                                                                                                                                                                                          |
| **Out**                | the translated document (same format); a translation log pairing source and target text (CSV); a paradata log (JSON); the ATRIUM document record (JSON)                                                                                                                                                                                                         |
| **Runs as**            | a command-line tool (`main.py`); a container image; an HTTP service image (`POST /translate`); an [Agent Skill](../agent-skills.md)                                                                                                                                                                                                                             |
| **Compute**            | CPU; a GPU only for a self-hosted translation model (Qwen3.8-27B was measured on one 96 GB GPU)                                                                                                                                                                                                                                                                 |
| **Network**            | the LINDAT translation service (the default backend) and the LINDAT UDPipe service (vocabulary matching), or the server of a language-model backend; the Hugging Face Hub for the language-identification model on first use; GitHub when the vocabulary is fetched from keyword-extract's release                                                              |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                                             |
| **Component licences** | a default run uses CUBBITT through the LINDAT service (a CC BY-NC-SA 4.0 model, under LINDAT's terms of use) and, when the source language is detected, FastText (CC BY-NC 4.0); a run with only permissive components can be assembled (see below). These do not by themselves set the rights in the output: [Licences and paradata](../ecosystem/licences.md) |
| **Records**            | SSH Open Marketplace tool [`CizIUW`](https://marketplace.sshopencloud.eu/tool-or-service/CizIUW) and workflow [`13eHAZ`](https://marketplace.sshopencloud.eu/workflow/13eHAZ)                                                                                                                                                                                   |

## Steps

| # | Step                                   | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | In → out    | Activity    |
|---|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|-------------|
| 1 | Prepare a domain vocabulary (optional) | Czech–English term pairs from the AMČR vocabularies and the TEATER thesaurus, each pointing back to the concept it came from. The project keeps one curated list, which keyword-extract publishes with each release: `load_vocab.py --from-release` builds the CSV from that asset, checked against its `.sha256`, and adds the concept's description where there is one. The bundled harvester collects pairs from the live sources instead (AMČR over OAI-PMH, TEATER over GraphQL). The shipped `data_samples/vocabulary.csv` is keyword-extract's `v1.3.0-beta` list: 4,715 pairs, 1,961 with a description. A vocabulary of one's own in the same CSV form works as well.                                                       | → CSV       | Collecting  |
| 2 | Choose the mode and the fields         | ALTO transcriptions are translated in ALTO mode, which works on the words of each text line. For metadata records, the fields to translate are listed as XPaths; namespaces and OAI-PMH envelopes are handled by the tool.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | ALTO, XML   | —           |
| 3 | Identify the source language           | A language-identification model detects the language of each text block (ALTO) or field (metadata), so a record that mixes languages is handled piece by piece. A guess is used only when it is confident and names a language the backend translates; otherwise the element's own label, the document's language, then a configured default decide. A confident guess of a language the backend cannot translate is reported for review. Naming the source language skips detection. Before anything is translated, the named language, or the default, is checked against the backend: a pair it cannot translate is refused (exit 1 on the command line, 422 `unsupported_language_pair` from the service) and is never rerouted. | —           | —           |
| 4 | Protect domain terms (optional)        | Vocabulary terms found in the text are replaced by placeholders before translation and restored as their agreed translations afterwards; multi-word terms are matched first, single words by lemma. Language-model backends receive the matching terms as a glossary in the prompt instead; the OpenAI-compatible backend can add each term's description as context (off by default). The command line takes the vocabulary with `--vocabulary`; the service applies one only when `VOCABULARY_PATH` names it.                                                                                                                                                                                                                      | CSV         | Lemmatizing |
| 5 | Translate                              | The text goes to the chosen backend: the LINDAT translation service (CUBBITT, the default), an OpenAI-compatible language-model API (such as Qwen3.8-27B on one's own vLLM server), or a self-hosted CTranslate2 model. Long texts are split at sentence boundaries first. Every reply is checked against its source: one that is empty, runaway, cut short, looping, or mixes Latin and Cyrillic letters in a word is requested again, re-run at the end of the document if it still fails, and never written.                                                                                                                                                                                                                      | —           | Translating |
| 6 | Rebuild and validate the document      | ALTO: each text block is translated as a whole and line by line; the fluent whole-block translation is then divided among the original lines and written into the original word elements — replacing their text, or added beside it as an alternative. Metadata: the translation replaces the source text, or is added beside it with language labels. Metadata output can be validated against an XSD schema, such as the AMČR schema, which accepts replaced records and not appended ones.                                                                                                                                                                                                                                        | → ALTO, XML | —           |
| 7 | Review and record provenance           | A translation log beside each output pairs source and target text line by line or field by field, with a status saying whether each was translated normally, recovered by a re-run, placed approximately, kept as source, or translated from a fallback language because the backend cannot translate the detected one. The paradata log records what was run and the licence it resolved to; the document record notes the languages, the backend, the translated file and the same licence.                                                                                                                                                                                                                                        | → CSV, JSON | —           |

**Which backend.** LINDAT stays the default. The recommended self-hosted alternative is
`openai_compatible` with Qwen3.8-27B (Apache-2.0) on one's own vLLM server: in the bake-off
of 2026-10-19 it kept numbers and vocabulary terms about as well as LINDAT (terms 0.978 against
0.987) and failed no segment. `ct2`
with EuroLLM is no longer recommended, because it drops short segments (see Limits). The
bake-off compares the backends without reference translations. Its script is
`eval/bakeoff.py`, its results are in `eval/results/issue4_bakeoff_2610/`, and the decision
is in the tool's `docs/translation-backends.md`.

The vocabulary step is its own workflow on Pipelines —
[W7, vocabulary harvesting and review](../pipelines.md#w7--vocabulary-harvesting--review-the-translators-half).

## What you get

* **The same document in another language** — `<name>_<target language>.<extension>`, every tag
  and namespace in place; for ALTO, every line where it was.
* **A review log** — `<name>_log.csv`, with the source and the translated text side by side, and a
  status per line that points a reviewer at what was recovered, approximated, left untranslated
  or translated from a fallback language.
* **Consistent terminology** — every protected term carries its agreed translation, and the
  paradata counts the protected terms per document.
* **A provenance record** — the paradata log of the run, with the licence it resolved to, and a
  document record per file, `<name>.document.json`.

The translator's output is an end product: an edition for readers and for publication. No later
stage of the pipeline reads it; the [document record](../ecosystem/document-contract.md)
refers to it.

## Limits

* **Word positions in translated ALTO are approximate.** Line boundaries are exact; how the
  words of a line are spread over its word elements is constructed, because a translation has
  a different number of words.
* **Schema validation applies to metadata output, on the command line.** ALTO output keeps the
  structure of its input — and is valid ALTO in either mode — but is not validated by the tool.
  The service does no XSD check.
* **Appended AMČR records are not valid AMČR.** The AMČR schema allows neither a language label
  on the translated fields nor a second copy of them; a record that must validate is translated
  in replace mode.
* **Language coverage is the backend's.** Into English, LINDAT translates from Czech, German,
  French, Polish, Russian and Ukrainian. A pair the backend has no model for is refused, not
  routed through Czech; other pairs need another backend.
* **Placeholders protect terms only for the LINDAT backend.** Language-model backends get a
  glossary instead, and the self-hosted neural translation models receive no vocabulary.
* **EuroLLM on `ct2` drops short segments.** In the bake-off EuroLLM-9B ran on past the source
  in 96 of 1,230 segments, almost all a number or a single word. The guard keeps their source
  text and logs them `untranslated`.

## Provenance and licence

Each run writes `<stamp>_translator.json`, the paradata log; the service returns the same
provenance in its response instead of writing a file. The paradata lists the components the run
actually used, each with its licence or terms, as declared in the tool's `para_config.txt`:

| Component                                                         | Licence                   | Used when                                                   |
|-------------------------------------------------------------------|---------------------------|-------------------------------------------------------------|
| language-identification model, FastText (`fasttext`)              | CC BY-NC 4.0              | the source language is detected, not given                  |
| LINDAT translation, CUBBITT (`lindat_cubbitt`)                    | CC BY-NC-SA 4.0           | the default backend, `lindat`, is used                      |
| UDPipe 2 engine / models (`udpipe2_engine`, `udpipe2_models`)     | MPL 2.0 / CC BY-NC-SA 4.0 | LINDAT applies a vocabulary (terms matched by lemma)        |
| AMČR vocabularies, TEATER thesaurus (`amcr_vocab`, `teater_data`) | CC0                       | a vocabulary is applied                                     |
| OpenAI-compatible language-model API (`llm_api`)                  | LLM provider ToS          | `openai_compatible` is used without `LLM_LICENSE_COMPONENT` |
| Qwen3.8-27B or -FP8, self-hosted (`qwen3_8`)                      | Apache-2.0                | `openai_compatible` with `LLM_LICENSE_COMPONENT=qwen3_8`    |
| CTranslate2 engine (`ctranslate2`)                                | MIT                       | the `ct2` backend is used                                   |
| EuroLLM, MADLAD-400 (`eurollm`, `madlad400`)                      | Apache-2.0                | a `ct2` model of these families                             |
| NLLB-200 (`nllb200`)                                              | CC BY-NC 4.0              | a `ct2` NLLB-200 model                                      |
| Opus-MT (`opus_mt`)                                               | CC BY 4.0                 | a `ct2` Opus-MT model                                       |

A hosted language-model API is recorded with its provider's terms of service (`LLM provider ToS`).
The paradata's computed label, the most restrictive of the licences listed, treats terms it does not
know as the most restrictive. The label is not the licence of the output: [Licences and paradata](../ecosystem/licences.md).

**A run with only permissive components** needs both: a self-hosted model under a permissive licence and the source
language named explicitly. The recommended model is Qwen3.8-27B through `openai_compatible`,
recorded with `LLM_LICENSE_COMPONENT=qwen3_8`; a `ct2` model of the EuroLLM, MADLAD-400 or
Opus-MT family also qualifies. The AMČR and TEATER vocabularies are CC0 and do not stand in its
way. How the label is computed is on
[Reference → Licence](../tools/translator/reference.md#licence-is-computed-not-declared).

In the [document record](../ecosystem/document-contract.md) the tool owns the `translations`
block and records the translated file as `derived_from.translated_xml`. The block also counts
the segments in a language the backend cannot translate (`unsupported_source_langs`).

## Where it sits

* **Translation branch** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
  It reads the per-page ALTO that ocr-postprocess writes; its output ends that branch.
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

|                          |                                                                                                                                                                                                                                                                                                                                                                    |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**      | a collection of documents — `alto` or `xml`; for metadata mode, the list of fields — `txt`; optionally the vocabulary — `csv`                                                                                                                                                                                                                                      |
| **Parameters**           | target language; source language (or detection); backend; replace or append; optional XSD schema                                                                                                                                                                                                                                                                   |
| **Workflow outputs**     | translated documents — `alto` or `xml`; translation logs — `tabular` (CSV); paradata — `json`; document record — `json`                                                                                                                                                                                                                                            |
| **Container**            | `ghcr.io/ufal/atrium-translator-api:<version>` — the service image (`POST /translate`), which applies a vocabulary only when started with `VOCABULARY_PATH` (the image carries `data_samples/vocabulary.csv`); the XSD check (`--xsd`) is an option of the command-line image `ghcr.io/ufal/atrium-translator` only; neither image includes the `ct2` dependencies |
| **Compute**              | CPU                                                                                                                                                                                                                                                                                                                                                                |
| **Network**              | the LINDAT translation and UDPipe services, and the Hugging Face Hub for the language-identification model — or a self-hosted model with the source language given                                                                                                                                                                                                 |
| **Credentials**          | an API key only for a hosted language-model API (`LLM_API_KEY`; a local server may need none), passed through Galaxy's credentials mechanism                                                                                                                                                                                                                       |
| **Test data**            | `data_samples/` in the tool repository — 15 AMČR metadata records and one ALTO page, with their translations, logs and paradata in both output modes                                                                                                                                                                                                               |
| **Credit**               | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                                                                                                                                           |
| **Closest Galaxy tools** | none translates; the language-model tools (`llm_hub`, `chatgpt_openai_api`) and the `xpath` tool are the nearest, and DARIAH's `gate-cloud-client` shows the pattern for a tool that calls a remote service                                                                                                                                                        |

## Sources

Read from `ufal/atrium-translator` at release **`v1.5.0-beta`** (2026-10-19) and from this site's
translator section; the licence table follows the `para_config.txt` of that release. This table
records **provenance**, not a build instruction.

| Source                                                                                                                                                                                                                       | What was taken from it                                                                         |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `README.md` §§ Features, Usage (with Harvesting the Vocabulary and Output mode), Logic Overview, Source-language identification, ALTO Dual-Pass Reconstruction, Translation CSV Logs, Paradata JSON Logs, License & Citation | purpose, the step order, the outputs, the permissive recipe                                    |
| `service/README.md` §§ Response, Errors, Configuration, Known limits                                                                                                                                                         | the service's vocabulary, provenance and 422 refusal; the limits                               |
| `docs/translation-backends.md` §§ Recommendation, The bake-off, The result                                                                                                                                                   | the backend decision                                                                           |
| `main.py`; `processors/backend.py`, `translator.py`, `llm_translator.py`, `ct2_translator.py`, `language.py`, `identifier.py`, `quality.py`; `load_vocab.py`                                                                 | the steps, the backends, the language-pair check, vocabulary protection                        |
| `para_config.txt`                                                                                                                                                                                                            | the licence components                                                                         |
| `.env.example`, `Dockerfile`, `.dockerignore`, `requirements.txt`, `requirements-llm.txt`                                                                                                                                    | the images, `VOCABULARY_PATH`, `LLM_LICENSE_COMPONENT`, `LLM_API_KEY`; no model weights inside |
| `eval/bakeoff.py`, `eval/results/issue4_bakeoff_2610/bakeoff_summary.csv`                                                                                                                                                    | the bake-off and its result                                                                    |
| `data_samples/README.md`, `data_samples/vocabulary.csv`                                                                                                                                                                      | test data; the shipped vocabulary                                                              |
| `CITATION.cff`                                                                                                                                                                                                               | credit, the release date                                                                       |
| `CONTRIBUTING.md` (release rows `v1.2.2-beta` to `v1.5.0-beta`; Branches & Environments), `.github/workflows/release.yml`, `docker.yml`                                                                                      | what changed since `v1.2.1-beta`; the release branch                                           |
| `atrium-project/docs_site/tools/translator/*`, `docs_site/pipelines.md` § W7                                                                                                                                                 | outputs, design limits, the vocabulary workflow                                                |
| SSH Open Marketplace `CizIUW`, `13eHAZ`                                                                                                                                                                                      | record identifiers                                                                             |
| `usegalaxy-eu/usegalaxy-eu-tools`; `bgruening/galaxytools`; `DARIAH-ERIC/atrium-galaxy-tools`                                                                                                                                | the Galaxy analogues and conventions                                                           |
