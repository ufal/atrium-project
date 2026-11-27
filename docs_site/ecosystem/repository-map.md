---
title: Repository map
nav_order: 5
status: published
round: 7
issue: 57
---

# Repository map

The tools write record schema 2.0 since their 2.0.0-beta releases (26 November 2026). The published record
schema is `doc-schema-v1`; 2.0 is published as `doc-schema-v2` once the pilot has proven it.

Find the right repository in one look: what each of the seven is for, which part of the
document record it is allowed to write, and where its documentation lives.

## The seven at a glance

| Repository                                                                         | Role                                                                                                                                        | Default branch | Authorised to write, in the record                                                   | Landing page                                                                                    | Docs here                                                                                         |
|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| [`atrium-page-classification`](https://github.com/ufal/atrium-page-classification) | Page types — eleven categories that describe what each page holds; in the pilot, the pages forced to the ATR and those with graphics        | `vit`          | `page_categories` · `pages[]` *category, category_confidence*                        | [ufal.github.io/atrium-page-classification](https://ufal.github.io/atrium-page-classification/) | **[page-classification](https://github.com/ufal/atrium-page-classification/blob/test/README.md)** |
| [`atrium-ocr-postprocess`](https://github.com/ufal/atrium-ocr-postprocess)         | The record builder — the ATRIUM record from docproc, and every line's language and quality; research batches over ALTO and other OCR output | `master`       | `pages` · `content` · `lines` · `quality_summary` · `source` *(described fields)*    | [ufal.github.io/atrium-ocr-postprocess](https://ufal.github.io/atrium-ocr-postprocess/)         | [ocr-postprocess workflow](../workflows/ocr-postprocess.md)                                       |
| [`atrium-translator`](https://github.com/ufal/atrium-translator)                   | In-place translation of XML — in the pilot, a record-level job that writes `metadata-en`; its output is stored, not consumed                | `master`       | nothing: `translations` and `entities[]` *translation_en* stay reserved              | [ufal.github.io/atrium-translator](https://ufal.github.io/atrium-translator/)                   | **[translator](https://github.com/ufal/atrium-translator/blob/test/README.md)**                   |
| [`atrium-nlp-enrich`](https://github.com/ufal/atrium-nlp-enrich)                   | Morphosyntax and named entities — the linguistic layer of the record, and the TEITOK file                                                   | `master`       | `entities` · `lines[]` *lemma, upos, feats, teitok_ref* · `pages[]` *teitok_surface* | [ufal.github.io/atrium-nlp-enrich](https://ufal.github.io/atrium-nlp-enrich/)                   | [nlp-enrich workflow](../workflows/nlp-enrich.md)                                                 |
| [`atrium-keyword-extract`](https://github.com/ufal/atrium-keyword-extract)         | Both kinds of keywords: statistical (KeyBERT, YAKE, KER) and from the AMČR and TEATER vocabularies, through a language model                | `master`       | `enrichment` · `keywords` · `entities[]` *pid*                                       | [ufal.github.io/atrium-keyword-extract](https://ufal.github.io/atrium-keyword-extract/)         | [keyword-extract workflow](../workflows/keyword-extract.md)                                       |
| [`atrium-digital-convert`](https://github.com/ufal/atrium-digital-convert)         | Born-digital files read into docproc without OCR, with a verdict for every page; `POST /reformat`                                           | `main`         | nothing: it writes docproc, which the record builder reads                           | [ufal.github.io/atrium-digital-convert](https://ufal.github.io/atrium-digital-convert/)         | [digital-convert workflow](../workflows/digital-convert.md)                                       |
| [`atrium-project`](https://github.com/ufal/atrium-project)                         | The hub — shared code, reusable CI, the end-to-end tests and this site                                                                      | `main`         | nothing                                                                              | [ufal.github.io/atrium-project](https://ufal.github.io/atrium-project/)                         | you are here                                                                                      |

Where a repository has no tool section in **Docs here**, its own `README.md` is the reference;
its workflow page gives the stable core of what it does, and its landing page links to both.

Of the two documented tools, both are MIT-licensed code. **page-classification** runs its
models locally — on CPU, or faster on a CUDA GPU; **the translator** calls remote LINDAT
services by default and needs no GPU unless a self-hosted CTranslate2 model is chosen.

!!! note "The order of the route"
    In the AMČR pilot, digital-convert or the ATR writes the layout as docproc, ocr-postprocess builds
    the record from it, and page-classification, nlp-enrich and keyword-extract add to it; the translator
    runs apart, when a record is archived. [Pipelines](../pipelines.md#the-route-through-the-pipeline)
    draws the route.

## Who may write which block

Every block of the record has exactly one authorised writer, declared once in the hub-canonical
`BLOCK_OWNERS` and vendored byte-identically into every tool:

| Block                                          | Authorised writer                                                                                |
|------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `pages`, `content`, `lines`, `quality_summary` | `ocr-postprocess`, the record builder                                                            |
| `page_categories`                              | `page-classification`                                                                            |
| `entities`                                     | `nlp-enrich`                                                                                     |
| `enrichment`, `keywords`                       | `keyword-extract` — the controlled and the statistical kind, side by side, never in one list     |
| `translations`                                 | `translator` — reserved: declared, written by no tool in the pilot                               |

Shared blocks are split by field (`BLOCK_FIELD_OWNERS`): inside `pages[]`, page-classification writes
only `category` and `category_confidence`, and nlp-enrich only `teitok_surface`; inside `lines[]`,
nlp-enrich writes only `lemma`, `upos`, `feats` and `teitok_ref`; inside `entities[]`, keyword-extract
writes only `pid`, and `translation_en` stays reserved for the translator. The record builder alone
writes the described fields of `source`; the identity fields come from AMČR's seed.

The record holds content only: who wrote what, with which components and when, is in the paradata of each
distribution, not in the record ([The document contract](document-contract.md)).

!!! info "Program ids and repositories"
    The program id in a record or its paradata names the **role**, not the repository, and a repository
    move does not rewrite it. Two ids have a successor since 1 October 2026: `alto-postprocess` continues
    as `ocr-postprocess`, and `llm-enrich` was split — its keyword stage continues as `keyword-extract`,
    while its born-digital converter keeps the role id `digital-convert` and has its own repository. The
    hub's `PROGRAM_SUCCESSORS` map accepts each successor beside its predecessor, so a record written
    before the move still loads. The old repositories are archived (read-only); their releases and
    images stay where they were.

## Branches

A default branch is where a clone lands. Both documented tools stage changes on a `test`
branch before they reach it, and both keep the Agent Skill on a branch of its own.

=== "page-classification"

    | Branch        | What it is                                                                             |
    |---------------|----------------------------------------------------------------------------------------|
    | **`vit`**     | the default branch and the code                                                        |
    | `test`        | staging, and the base for pull requests                                                |
    | `master`      | an index of the model families, from the repository's earlier layout; not developed on |
    | `clip`        | a parallel model family (CLIP-based), with its own Hugging Face repository             |
    | `agent-skill` | the Agent Skill packaging — see [Agent skills](../agent-skills.md)                     |
    | `gh-pages`    | the landing card                                                                       |

    `vit` and `clip` name model families, not development stages.

=== "translator"

    | Branch        | What it is                                                         |
    |---------------|--------------------------------------------------------------------|
    | **`master`**  | the default branch and the code                                    |
    | `test`        | staging, and the base for pull requests                            |
    | `main`        | the repository's initial commit; not developed on                  |
    | `agent-skill` | the Agent Skill packaging — see [Agent skills](../agent-skills.md) |
    | `gh-pages`    | the landing card                                                   |

The hub itself has `main`, `test` and `gh-pages` (the built site), plus a **`v1` tag** — the
channel every tool repository's CI pins the hub's reusable workflows to. See
[Architecture](architecture.md#the-ci-federation).

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                                   | What was taken from it                                |
|------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| `atrium-project/_generators/repos.py:14-110`                                                                                             | each repository's role, stage and default branch      |
| `git ls-remote --symref` on the repositories, 2026-09-23; the three new ones, 2026-10-01                                                 | default branches and branch heads                     |
| `atrium-project/docs/templates/shared/atrium_document.py` on `test` (`BLOCK_OWNERS`, `BLOCK_FIELD_OWNERS`, `RECORD_BUILDER`), 2026-11-21 | the block and field owners of record schema 2.0       |
| `atrium-project/docs/document_schema.md:104-143, 254-261`                                                                                | the ownership tables and the `digital-convert` rename |
| `atrium-translator/utils.py` (`process_metadata_xml`)                                                                                    | `translation_en` reserved but not filled              |
| `atrium-project/docs/templates/shared/atrium_rocrate.py` (`REPO_URLS`)                                                                   | program → repository, including the predecessors      |
| `atrium-ocr-postprocess` @ `v1.12.1-beta` — `text_formats.py` (`READERS`), `docs/text_inputs.md` §6                                      | the origins ocr-postprocess records per input format  |
