---
title: keyword-extract workflow
nav_order: 18
status: published
round: 7
issue: 57
repo: atrium-keyword-extract
role: workflow
authored: true
---

# Keywords from archival text: statistical, and from the controlled vocabularies

*The keyword-extract workflow.* Tool: [atrium-keyword-extract](https://github.com/ufal/atrium-keyword-extract).
It makes both kinds of keywords, the statistical and the vocabulary-controlled ones.

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licences of the components it uses. The methods' options, the
    models and the prompts are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-keyword-extract/blob/test/README.md), whose documentation map leads to its
    usage, how-it-works and reference pages, and its
    [service README](https://github.com/ufal/atrium-keyword-extract/blob/test/service/README.md) —
    because they change as methods are compared and chosen. No controlled category has been
    checked against a reviewed answer yet, so treat the categories as research output.

## Purpose

Finding an archival document by what it is about needs its keywords, and two kinds answer
different questions. **Statistical keywords** are the phrases that characterise a document or
a page against the rest of its text; they need no vocabulary and say how they were found.
**Controlled keywords** are given per line: a language model picks the term of the AMČR keyword
lists or the TEATER thesaurus that describes the line, and can only pick a term that exists in
the vocabulary. With the term come the records behind it, the Czech keywords found in the line
with their English translations, and the page and line it came from. The two kinds are kept
apart in the output, and every statistical keyword says which method produced it.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | the ATRIUM document record that nlp-enrich leaves: the text of its lines and, for the legacy method, each line's lemma; or plain text. The statistical kind also reads files, on the command line (`keywords.py`) and as `POST /extract_keywords`'s `file` alike: nlp-enrich's CoNLL-U or TEITOK, a line table (CSV) or a `.txt`. The controlled kind's batch clients read line tables (CSV), TEITOK or records                                                    |
| **Out**                | statistical keywords with their method, score and rank, per document and per page; controlled keywords per line (JSON); the run's paradata (JSON). With a record sent: the record with its `keywords` block (statistical kind) and its `enrichment` block (controlled kind), side by side. The batch CLI writes CSV tables and, on request, each page's keywords (`--per-page`) and the record's `keywords` block (`--document-json-out-dir`), as the service does |
| **Runs as**            | an HTTP service image (`POST /extract_keywords`, `/extract_keywords_text`), the production image; a command-line tool for the statistical kind (`keywords.py`) and its image; batch clients for the controlled kind; a research run on GPUs (`llm_run.py`) and its image                                                                                                                                                                                           |
| **Compute**            | CPU for YAKE and the legacy method; a GPU is used by KeyBERT when there is one; the service's controlled kind calls a language-model service and carries no weights; the research run loads a model's weights onto GPUs                                                                                                                                                                                                                                            |
| **Network**            | the Hugging Face Hub for the KeyBERT model, on first use (the service fetches it at startup); for the controlled kind, the language-model service (OpenRouter, or a local Ollama). Only the vocabulary build reaches the AMČR and TEATER sources                                                                                                                                                                                                                   |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Component licences** | KeyBERT (MIT) with its sentence-transformers model (Apache-2.0), YAKE (AGPL-3.0) when chosen, the AMČR and TEATER vocabularies (CC0), and for the controlled kind the language model's own terms; each run lists the ones it used. No licence of an output is computed: [Licences and paradata](../ecosystem/licences.md)                                                                                                                                          |
| **Record**             | SSH Open Marketplace tool [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo)                                                                                                                                                                                                                                                                                                                                                                   |

## Steps

| #   | Step                 | What happens                                                                                                                                                                                                                                                                                                                                                   | In → out          | Activity                    |
|-----|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------|
| 1   | Select the text      | The lines of the record are gathered per document and per page. Lines categorised `Trash` or `Empty` are left out. The legacy method counts the lemma nlp-enrich wrote for each line, that of its head word, when the line's part of speech is a noun, a proper noun or an adjective.                                                                          | JSON → text       | —                           |
| 2   | Statistical keywords | KeyBERT (the default) ranks candidate phrases by their similarity to the document's embedding; YAKE ranks them without a model; the legacy method counts nouns, proper nouns and adjectives by lemma. Scores differ in meaning per method.                                                                                                                     | text → keywords   | Keyword extraction          |
| 3   | Build the vocabulary | The AMČR keyword lists and the TEATER thesaurus are harvested and nested into one term list, each term pointing back to the records it came from. This is done once, not per run: each release carries the built vocabulary as a CC0 asset, `atrium-vocabulary-<version>.zip`, with its `.sha256`.                                                             | → JSON, CSV, SKOS | Collecting                  |
| 4   | Controlled keywords  | A language model reads each line among its neighbours on the page and answers with the term that describes it (with the AMČR and TEATER records behind it), the Czech keywords found in it with their English translations, and a confidence. Its answer must fit a schema whose allowed categories are the vocabulary's terms.                                | text → JSON       | Enriching, Content Analysis |
| 5   | Record the result    | Statistical keywords go into the record's `keywords` block, each with its method, score and rank; controlled keywords into its `enrichment` block, one item per line with its page. Entities that are vocabulary terms are linked to AMČR and AAT identifiers. The paradata name the method and, for the controlled kind, the model and the vocabularies used. | → JSON            | —                           |

Step 2 is the statistical kind and step 4 the controlled one; step 3 is done when the vocabulary
is built, and a run reads its result. The request chooses which kind runs (`kind=statistical`,
`controlled` or `both`, the default), and each kind can fail or be skipped on its own and says
so. The service and the batch clients reach the model through OpenRouter or a local Ollama; the
research run `llm_run.py` loads it onto its own GPUs.

Two limits follow from how the controlled kind works (the service README's
[Known limits](https://github.com/ufal/atrium-keyword-extract/blob/test/service/README.md#known-limits)).
The schema keeps a category inside the vocabulary, not on topic: a model can be forced onto an
unrelated term that shares the start of the word it began. And `confidence_score` is not
calibrated: most lines get one of two values, so do not rank or filter on it.

## Provenance and licence

Every run records its paradata, which lists the components that ran, each with its licence, as
declared in the tool's `para_config.txt`. The service returns the paradata in its response, as a
Process Run Crate `CreateAction`: the record read and the record written, as AMČR distributions by
name and SHA-512. The command-line and batch runs write it as a log (JSON), and the controlled
ones name the vocabulary build they used. The statistical methods differ: the legacy method uses
only the standard library, KeyBERT is MIT and loads a sentence-transformers model (Apache-2.0),
and YAKE is AGPL-3.0; a run that selects YAKE lists it. The vocabularies are CC0. The language
model is not in that list: its own licence or its provider's terms apply to the controlled kind,
and every controlled run records the model's id. No licence of an output is computed: the rights
in an output follow the source document ([Licences and paradata](../ecosystem/licences.md)).

In the [document record](../ecosystem/document-contract.md) the tool writes the `keywords` block,
the `enrichment` block and `entities[].pid`. It writes `keywords` when the statistical kind ran —
the keywords of the document and of each page, every one with its method, score and rank — and
`enrichment` with `entities[].pid` when the controlled kind contributed; an `enrichment` item
names its record line by `page` and `line`, the record's line key, and keeps only its page when it
cannot name one. The two kinds stay in their own blocks and never share a list, and a re-run
replaces each block whole. The record carries no run data. Records written before the move name
the writer of `enrichment` `llm-enrich`; the contract accepts both names for the one writer.

## Where it sits

* **After nlp-enrich** in the AMČR pipeline: it reads the record nlp-enrich leaves —
  [Pipelines → The route through the pipeline](../pipelines.md#the-route-through-the-pipeline) and
  [W1](../pipelines.md#w1--scanned--ocr-document-pipeline). It reads the record, so it does not
  care whether the text came from a born-digital file, the ATR or both.
* **Before the optional TEITOK projection.** nlp-enrich's `/project_record` reads the keywords
  and writes them into the TEITOK header, so the chain is nlp-enrich → keyword-extract →
  nlp-enrich's projection.
* **The source of the translator's vocabulary** —
  [Pipelines → W7](../pipelines.md#w7--vocabulary-harvesting--review-the-translators-half).
  The vocabulary asset of each release can be read by the translator instead of a harvest of
  its own.
* **Vocabulary keywords** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** Tool record [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo),
"Keyword extraction from archival documents (statistical and vocabulary-controlled)". It described the
llm-enrich stage before it was re-pointed to this repository.

**Galaxy sheet.** The Galaxy wrappers were handed to DARIAH for testing; further Galaxy work is parked during the
AMČR pilot. The sheet describes the wrapper as delivered, for the batch image at `v1.6.5-beta`.

|                               |                                                                                                                                                                                                                                                                                                                                                                                                                 |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**           | a collection of CoNLL-U — `tabular`; TEITOK — `tei` or `xml`; document records — `json`; line tables — `csv`; text — `txt`                                                                                                                                                                                                                                                                                      |
| **Parameters**                | the method (`yake`, the default; `keybert`, its model downloaded or staged; `legacy`); how many keywords; the longest keyword; the language; per page too                                                                                                                                                                                                                                                       |
| **Workflow outputs**          | the keyword table — `csv` (`document_id, kw-1, score-1, …`); keywords per document and per page — lists of `csv`; document records — a list of `json`; paradata — `json`                                                                                                                                                                                                                                        |
| **Container**                 | `ghcr.io/ufal/atrium-keyword-extract:<version>` — the batch image (`keywords.py`); it runs the job script Galaxy hands it (the hub-canonical `container_entrypoint.py`). The `llm` image (the controlled kind, on a GPU) and the service image `-api` are not used                                                                                                                                              |
| **Galaxy tool**               | `atrium_keyword_extract` `1.6.5-beta+galaxy0`, the statistical kind only, with the data manager *ATRIUM Hugging Face models* for KeyBERT's model, in the hub's [`galaxy/`](https://github.com/ufal/atrium-project/tree/test/galaxy) folder with the workflows *ATRIUM OCR to keywords* and *ATRIUM born-digital documents to keywords*; for DARIAH's test Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>) |
| **Compute**                   | CPU; KeyBERT uses a GPU when the destination has one                                                                                                                                                                                                                                                                                                                                                            |
| **Network or reference data** | `yake` and `legacy` need none; `keybert` downloads `paraphrase-multilingual-MiniLM-L12-v2` from the Hugging Face Hub, so a server stages it once                                                                                                                                                                                                                                                                |
| **Credentials**               | none for the statistical kind; the controlled kind needs a language-model API key, and its output is still research output, so it is not offered                                                                                                                                                                                                                                                                |
| **Test data**                 | `data_samples/UDP/CTX000000003.conllu`, nlp-enrich's `data_samples/TEITOK/CTX000000001.teitok.xml`, a record of the born-digital converter's wrapper, and a table without a `text` column for the error test                                                                                                                                                                                                    |
| **Credit**                    | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT; YAKE, one of the statistical methods, is AGPL-3.0                                                                                                                                                                                                                                                                                     |
| **Closest Galaxy tools**      | none extracts keywords; DARIAH's ATRIUM tools on the instance chain PDF text extraction with vocabulary-driven information extraction (task 4.2.1)                                                                                                                                                                                                                                                              |

## Sources

Read from `ufal/atrium-keyword-extract` on its `test` branch, which carries release 2.0.0-beta, on 2026-11-21.
Earlier readings were at `v1.6.0-beta` (2026-10-29), `v1.5.1-beta` (2026-10-27) and `v1.4.0-beta` (2026-10-19).
The statistical methods of `atrium-nlp-enrich` and the controlled kind and vocabulary build of `atrium-llm-enrich`
have moved into it. This table records
**provenance**, not a build instruction.
The Galaxy sheet (2026-11-07) follows `v1.6.5-beta` and the tool's wrapper in the hub's `galaxy/` folder (#66).

| Source                                                                                                                  | What was taken from it                                                                                                   |
|-------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `README.md`; `CONTRIBUTING.md` § Release History                                                                        | the two kinds, the paths that run them, the move from nlp-enrich and llm-enrich, the release history                     |
| `README.md`, `docs/usage.md`, `docs/how-it-works.md`, `service/README.md`, `service/api.py`, `kw_inputs.py` (on `test`) | the record nlp-enrich leaves as the input, the lemma per line, the start-up, the paradata, the step's place on the route |
| `service/README.md` (kinds, endpoints, the controlled kind, Known limits); `service/api.py`                             | the service, the record's blocks, the paradata, the limits                                                               |
| `keywords.py`, `kw_inputs.py`, `kw_config.txt`                                                                          | the three statistical methods, their scores, the batch CLI's inputs and outputs, the reader shared with the service      |
| `llm_client_shared.py`, `openrouter_client.py`, `ollama_client.py`, `llm_run.py`, `llm_config.txt`                      | the controlled kind, its schema, its paradata, the research run                                                          |
| `vocab_build.py`, `vocab_sources.py`, `vocab_manager.py`, `.github/workflows/release.yml`                               | the vocabulary build, its sources, the release asset                                                                     |
| `para_config.txt`, `docs/reference/licences.md`                                                                         | the licence components; YAKE's licence as its `LICENSE` file states it; the legacy method and KER                        |
| `atrium_document.py`                                                                                                    | the blocks the tool may write, the program-id succession                                                                 |
| `CITATION.cff`                                                                                                          | the release and its date                                                                                                 |
| `.github/production-image.json`, `.github/workflows/docker.yml`                                                         | the images                                                                                                               |
| `DARIAH-ERIC/atrium-galaxy-tools`                                                                                       | the Galaxy analogue                                                                                                      |
