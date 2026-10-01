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
It takes over both kinds of keywords that used to be made in two places: the statistical
keywords of [nlp-enrich](nlp-enrich.md) and the vocabulary-controlled keywords of llm-enrich.
[nlp-enrich](nlp-enrich.md) keeps only the LINDAT calls.

!!! info "Scope"
    This page gives the **stable core** of the workflow: its purpose, its steps, the formats
    it reads and writes, and the licence floor of its output. The methods' options, the
    models and the prompts are documented with the code — in the tool's
    [README](https://github.com/ufal/atrium-keyword-extract#readme) — because they change as
    methods are compared and chosen. The tool is being assembled from its two sources: the
    statistical kind is in place, the controlled kind follows it.

## Purpose

Finding an archival document by what it is about needs its keywords, and two kinds answer
different questions. **Statistical keywords** are the phrases that characterise a document or
a page against the rest of its text; they need no vocabulary and say how they were found.
**Controlled keywords** are terms of the AMČR keyword lists and the TEATER thesaurus, chosen by
a language model that can only pick terms that exist in the vocabulary — with Czech and English
labels, a thematic category and the page that supports each. The two kinds are kept apart in
the output, and every keyword says which method produced it.

## At a glance

|                    |                                                                                                                                                                                                    |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | the ATRIUM document record, after nlp-enrich; or plain text                                                                                                                                        |
| **Out**            | keywords with their method, score and rank, per document and per page; a paradata log (JSON). The record's `keywords` block and, for the controlled kind, `enrichment` follow in the record contract |
| **Runs as**        | a command-line tool; a container image; an HTTP service image (`POST /extract_keywords`)                                                                                                           |
| **Compute**        | CPU for YAKE and the legacy method; a GPU is used by KeyBERT when there is one; the controlled kind calls a language-model server and carries no weights                                          |
| **Network**        | the Hugging Face Hub for the KeyBERT model on first use; for the controlled kind, the language-model server and the AIS CR services that the vocabulary is built from                              |
| **Code licence**   | MIT                                                                                                                                                                                                |
| **Output licence** | declared per run from the components used: KeyBERT and the legacy method add no restriction on their own; YAKE is AGPL-3.0; the AMČR and TEATER vocabularies are CC0                               |
| **Record**         | none of its own yet; the earlier llm-enrich record is to be re-pointed to it                                                                                                                       |

## Steps

| # | Step                      | What happens                                                                                                                                                                                                                             | In → out         | Activity                    |
|---|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|-----------------------------|
| 1 | Select the text           | The lines of the record are gathered per document and per page. Lines categorised `Trash` or `Empty` are left out. Methods that need linguistic annotation use the lemmas and part-of-speech tags that nlp-enrich wrote.                 | JSON → text      | —                           |
| 2 | Statistical keywords      | KeyBERT (the default) ranks candidate phrases by their similarity to the document's embedding; YAKE ranks them without a model; the legacy method counts nouns, proper nouns and adjectives by lemma. Scores differ in meaning per method. | text → keywords  | Keyword extraction          |
| 3 | Build the vocabulary      | The AMČR keyword lists and the TEATER thesaurus are harvested into one nested term list, each term pointing back to its source concept. The built vocabulary is published as a versioned, CC0 release asset.                            | → JSON, SKOS     | Collecting                  |
| 4 | Controlled keywords       | A language model maps each passage onto the vocabulary: keywords in Czech and English, a thematic category and a confidence. Its output is constrained by a schema whose allowed values are the vocabulary's terms.                     | text → JSON      | Enriching, Content Analysis |
| 5 | Record the result         | Keywords of both kinds are written with their method, score and rank; entities are linked to AMČR and AAT identifiers; a paradata log records the methods, the model and the vocabulary version.                                         | → JSON           | —                           |

Steps 3 and 4 are the controlled kind and step 2 the statistical one; the request chooses
which run (`kind=statistical`, `controlled` or `both`), and each kind can fail or be skipped on
its own and says so.

## Provenance and licence

Every run writes a paradata log, and the licence of the output is computed from the components
that ran, as declared in the tool's `para_config.txt`; the most restrictive one wins. The
statistical methods differ: the legacy method uses only the standard library, KeyBERT is MIT and
loads a sentence-transformers model (Apache-2.0), and YAKE is AGPL-3.0, so a run that selects YAKE
is declared accordingly. The vocabularies are CC0. The terms of a language model or of its provider
apply to the controlled kind on top.

In the [document record](../ecosystem/document-contract.md) the tool is the successor of
llm-enrich as a writer: it writes the `enrichment` and `forms` blocks and `entities[].pid`, and it is to own the new
`keywords` block (atrium-project#73), which the record contract does not carry yet. Records already
written keep the program id `llm-enrich`; the contract accepts both names for the one writer.

## Where it sits

* **After nlp-enrich** in the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline) —
  and **after digital-convert** in the born-digital route
  ([Pipelines → W2](../pipelines.md#other-workflows)). It reads the record, so it does not
  care which of the two made it.
* **Before the optional TEITOK projection.** nlp-enrich's `/project_record` reads the keywords
  and writes them into the TEITOK header, so the chain is nlp-enrich → keyword-extract →
  nlp-enrich's projection.
* **Vocabulary keywords** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).

## On other platforms

**SSH Open Marketplace.** The tool has no record of its own yet; the llm-enrich record
[`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo) described this stage and is
to be re-pointed to it.

**Galaxy.** Inputs map to `json` (the record) and `txt`; outputs to `json`. Inside ATRIUM,
DARIAH's Galaxy tools already chain PDF text extraction with vocabulary-driven information
extraction (task 4.2.1).

## Sources

Built from `ufal/atrium-nlp-enrich` at release **`v0.23.0`** (the statistical methods, `keywords.py`)
and `ufal/atrium-llm-enrich` at release **`v0.9.0`** (the controlled kind and the vocabulary
build, not yet moved). This table records **provenance**, not a build instruction.

| Source                                                | What was taken from it                              |
|-------------------------------------------------------|-----------------------------------------------------|
| nlp-enrich `README.md` § Extract Keywords, `keywords.py`, `para_config.txt` | the three statistical methods, their scores and licences |
| llm-enrich `README.md`, `llm_client_shared.py`, `vocab_build.py`            | the controlled kind, the vocabulary                 |
| the keyword-extract plan (`agent_dev_logs/plans/40.plan.md`)                | the one service, the kinds, the record's blocks     |
| `DARIAH-ERIC/atrium-galaxy-tools`                                           | the Galaxy analogue                                 |
