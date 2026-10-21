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

*The keyword-extract workflow.* Tool: [atrium-keyword-extract](https://ufal.github.io/atrium-keyword-extract/).
It takes over both kinds of keywords that used to be made in two places: the statistical
keywords of [nlp-enrich](nlp-enrich.md) and the vocabulary-controlled keywords of llm-enrich.
[nlp-enrich](nlp-enrich.md) keeps only the LINDAT calls.

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The methods' options, the
    models and the prompts are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-keyword-extract#readme) and its
    [service README](https://github.com/ufal/atrium-keyword-extract/blob/master/service/README.md) —
    because they change as methods are compared and chosen. Both kinds now live in the tool:
    the statistical kind since its first release, the controlled kind since v1.1.0-beta. No
    controlled category has been checked against a reviewed answer yet, so treat the
    categories as research output.

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

|                        |                                                                                                                                                                                                                                                                                                                                               |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | the ATRIUM document record, after nlp-enrich; or plain text. The batch tools read files instead: nlp-enrich's CoNLL-U or TEITOK for the statistical kind; line tables (CSV), TEITOK or records for the controlled kind                                                                                                                        |
| **Out**                | statistical keywords with their method, score and rank, per document and per page; controlled keywords per line (JSON); the run's paradata (JSON). With a record sent: the record with its `keywords` block (statistical kind) and its `enrichment` block (controlled kind), side by side. The batch CLI writes CSV tables                    |
| **Runs as**            | an HTTP service image (`POST /extract_keywords`, `/extract_keywords_text`), the production image; a command-line tool for the statistical kind (`keywords.py`) and its image; batch clients for the controlled kind; a research run on GPUs (`llm_run.py`) and its image                                                                      |
| **Compute**            | CPU for YAKE and the legacy method; a GPU is used by KeyBERT when there is one; the service's controlled kind calls a language-model service and carries no weights; the research run loads a model's weights onto GPUs                                                                                                                       |
| **Network**            | the Hugging Face Hub for the KeyBERT model, on first use (the service fetches it at startup); for the controlled kind, the language-model service (OpenRouter, or a local Ollama). Only the vocabulary build reaches the AMČR and TEATER sources                                                                                              |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                                           |
| **Component licences** | KeyBERT (MIT) with its sentence-transformers model (Apache-2.0), YAKE (AGPL-3.0) when chosen, the AMČR and TEATER vocabularies (CC0), and for the controlled kind the language model's own terms; each run lists the ones it used. These do not by themselves set the rights in the output: [Licences and paradata](../ecosystem/licences.md) |
| **Record**             | none of its own yet; the earlier llm-enrich record is to be re-pointed to it                                                                                                                                                                                                                                                                  |

## Steps

| # | Step                 | What happens                                                                                                                                                                                                                                                                                                                        | In → out          | Activity                    |
|---|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|-----------------------------|
| 1 | Select the text      | The lines of the record are gathered per document and per page. Lines categorised `Trash`, `Garbage`, `Inverted` (a born-digital text layer that does not decode) or `Empty` are left out. Methods that need linguistic annotation use the lemmas and part-of-speech tags that nlp-enrich wrote.                                    | JSON → text       | —                           |
| 2 | Statistical keywords | KeyBERT (the default) ranks candidate phrases by their similarity to the document's embedding; YAKE ranks them without a model; the legacy method counts nouns, proper nouns and adjectives by lemma. Scores differ in meaning per method.                                                                                          | text → keywords   | Keyword extraction          |
| 3 | Build the vocabulary | The AMČR keyword lists and the TEATER thesaurus are harvested and nested into one term list, each term pointing back to the records it came from. This is done once, not per run: each release carries the built vocabulary as a CC0 asset, `atrium-vocabulary-<version>.zip`, with its `.sha256`.                                  | → JSON, CSV, SKOS | Collecting                  |
| 4 | Controlled keywords  | A language model reads each line among its neighbours on the page and answers with the term that describes it (with the AMČR and TEATER records behind it), the Czech keywords found in it with their English translations, and a confidence. Its answer must fit a schema whose allowed categories are the vocabulary's terms.     | text → JSON       | Enriching, Content Analysis |
| 5 | Record the result    | Statistical keywords go into the record's `keywords` block, each with its method, score and rank; controlled keywords into its `enrichment` block, one item per line with its page. Entities that are vocabulary terms are linked to AMČR and AAT identifiers. The paradata names the method, the model and the vocabulary sources. | → JSON            | —                           |

Step 2 is the statistical kind and step 4 the controlled one; step 3 is done when the vocabulary
is built, and a run reads its result. The request chooses which kind runs (`kind=statistical`,
`controlled` or `both`, the default), and each kind can fail or be skipped on its own and says
so. The service and the batch clients reach the model through OpenRouter or a local Ollama; the
research run `llm_run.py` loads it onto its own GPUs.

Two limits follow from how the controlled kind works (the service README's
[Known limits](https://github.com/ufal/atrium-keyword-extract/blob/master/service/README.md#known-limits)).
The schema keeps a category inside the vocabulary, not on topic: a model can be forced onto an
unrelated term that shares the start of the word it began. And `confidence_score` is not
calibrated: most lines get one of two values, so do not rank or filter on it.

## Provenance and licence

Every run records its paradata, which lists the components that ran, each with its licence, as
declared in the tool's `para_config.txt`. The
service returns the paradata in its response, as a Process Run Crate `CreateAction`; the
command-line and batch runs write it as a log (JSON), and the controlled ones name the
vocabulary build they used. The statistical methods differ: the legacy method uses only the
standard library, KeyBERT is MIT and loads a sentence-transformers model (Apache-2.0), and YAKE
is AGPL-3.0; a run that selects YAKE lists it. The vocabularies are CC0. The language model is not
in that list: its own licence or its provider's terms apply to the controlled kind, and every
controlled run records the model's id. The paradata's computed label, the most restrictive of the
licences listed, is not the licence of the output: [Licences and paradata](../ecosystem/licences.md).

In the [document record](../ecosystem/document-contract.md) the tool is the successor of
llm-enrich as a writer: the contract lets it write the `enrichment` and `forms` blocks and
`entities[].pid`, and, since v1.2.0-beta, the `keywords` block (atrium-project#73). It writes
`keywords` when the statistical kind ran — the keywords of the document and of each page, every
one with its method, score and rank — and `enrichment` with `entities[].pid` when the controlled
kind contributed; it writes no `forms`. The two kinds stay in their own blocks and never share a
list, and a re-run replaces each block whole. Records already written keep the program id
`llm-enrich`; the contract accepts both names for the one writer.

## Where it sits

* **After nlp-enrich** in the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline) —
  and **after digital-convert** in the born-digital route
  ([Pipelines → W2](../pipelines.md#other-workflows)). It reads the record, so it does not
  care which of the two made it.
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

**SSH Open Marketplace.** The tool has no record of its own yet; the llm-enrich record
[`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo) described this stage and is
to be re-pointed to it.

**Galaxy.** Inputs map to `json` (the record) and `txt`; outputs to `json`. Inside ATRIUM,
DARIAH's Galaxy tools already chain PDF text extraction with vocabulary-driven information
extraction (task 4.2.1). The container is the service image
`ghcr.io/ufal/atrium-keyword-extract-api:<version>` (`POST /extract_keywords`); for Galaxy the statistical
kind is the capability to wrap. The controlled kind needs a language-model service, and its
output is still research output.

## Sources

Read from `ufal/atrium-keyword-extract` at release **`v1.4.0-beta`** (2026-10-19). The
statistical methods of `atrium-nlp-enrich` and the controlled kind and vocabulary build of
`atrium-llm-enrich` have moved into it. This table records **provenance**, not a build
instruction.

| Source                                                                                             | What was taken from it                                                                               |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `README.md`; `CONTRIBUTING.md` § Release History                                                   | the two kinds, the paths that run them, the move from nlp-enrich and llm-enrich, the release history |
| `service/README.md` (kinds, endpoints, the controlled kind, Known limits); `service/api.py`        | the service, the record's blocks, the paradata, the limits                                           |
| `keywords.py`, `kw_config.txt`                                                                     | the three statistical methods, their scores, the batch CLI's inputs and outputs                      |
| `llm_client_shared.py`, `openrouter_client.py`, `ollama_client.py`, `llm_run.py`, `llm_config.txt` | the controlled kind, its schema, its paradata, the research run                                      |
| `vocab_build.py`, `vocab_sources.py`, `vocab_manager.py`, `.github/workflows/release.yml`          | the vocabulary build, its sources, the release asset                                                 |
| `para_config.txt`                                                                                  | the licence components                                                                               |
| `atrium_document.py`                                                                               | the blocks the tool may write, the program-id succession                                             |
| `CITATION.cff`                                                                                     | the release and its date                                                                             |
| `.github/production-image.json`, `.github/workflows/docker.yml`                                    | the images                                                                                           |
| `DARIAH-ERIC/atrium-galaxy-tools`                                                                  | the Galaxy analogue                                                                                  |
