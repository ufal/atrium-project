---
title: Repository map
nav_order: 5
status: published
round: 4
issue: 57
---

# Repository map

Find the right repository in one look: what each of the six is for, which part of the
document record it is allowed to write, and where its documentation lives.

## The six at a glance

| Repository                   | Role                                                                                       | Default branch | Writes, in the record                                                                                                                            | Landing page                                                                                    | Docs here                                                        |
|------------------------------|--------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `atrium-page-classification` | Structural perception — eleven page categories that inform how each page is processed      | `vit`          | `page_categories` · `pages[]` *category, category_confidence*                                                                                    | [ufal.github.io/atrium-page-classification](https://ufal.github.io/atrium-page-classification/) | **[page-classification](../tools/page-classification/index.md)** |
| `atrium-alto-postprocess`    | Deserialisation and OCR quality control — the fan-out point of the whole pipeline          | `master`       | `pages` · `content` · `lines` · `tables` *(originator, OCR documents)*                                                                           | [ufal.github.io/atrium-alto-postprocess](https://ufal.github.io/atrium-alto-postprocess/)       | —                                                                |
| `atrium-translator`          | Protected translation — a terminal branch: its output is recorded, not consumed            | `master`       | `translations` · `entities[]` *translation_en*                                                                                                   | [ufal.github.io/atrium-translator](https://ufal.github.io/atrium-translator/)                   | **[translator](../tools/translator/index.md)**                   |
| `atrium-nlp-enrich`          | Morphosyntax and named entities — produces the TEITOK corpus format                        | `master`       | `entities` · parts of `lines[]` and `pages[]` · `derived_from.teitok`                                                                            | [ufal.github.io/atrium-nlp-enrich](https://ufal.github.io/atrium-nlp-enrich/)                   | —                                                                |
| `atrium-llm-enrich`          | Semantic enrichment against the ATRIUM controlled vocabulary; also hosts `digital-convert` | `main`         | `enrichment` · `forms` · `entities[]` *pid* · `regenerable.markdown` — and, as `digital-convert`, the positional plane of born-digital documents | [ufal.github.io/atrium-llm-enrich](https://ufal.github.io/atrium-llm-enrich/)                   | —                                                                |
| `atrium-project`             | The hub — shared code, reusable CI, the end-to-end tests and this site                     | `main`         | nothing                                                                                                                                          | [ufal.github.io/atrium-project](https://ufal.github.io/atrium-project/)                         | you are here                                                     |

The **Docs here** column fills in as each tool section is written; until then, a repository's
own `README.md` is the reference, and its landing page links to it.

!!! note "The order is accretion order, not a chain of file handoffs"
    The rows are in the order a document record travels — page-classification writes first,
    llm-enrich last. That is **not** the order files move in. Only three real file handoffs
    exist (`PAGE_ALTO/`, `DOC_LINE_CATEG/`, `TEITOK/`), the translator's output is read by
    nothing, and nothing reads `page_categories` automatically. [Pipelines](../pipelines.md)
    draws both layers.

## Who may write which block

Every block of the `atrium_document` record has exactly one authorised writer, declared once in
the hub-canonical `BLOCK_OWNERS` and vendored byte-identically into every tool:

| Block                                 | Authorised writer                                                                |
|---------------------------------------|----------------------------------------------------------------------------------|
| `page_categories`                     | `page-classification`                                                            |
| `pages`, `content`, `lines`, `tables` | `alto-postprocess` **or** `digital-convert` — one of the two, fixed per document |
| `translations`                        | `translator`                                                                     |
| `entities`                            | `nlp-enrich`                                                                     |
| `enrichment`, `forms`                 | `llm-enrich`                                                                     |

Shared blocks are split by field rather than by block: page-classification may write only
`category` and `category_confidence` inside `pages[]`, and the translator only `translation_en`
inside `entities[]`.

### The positional plane has two possible originators

`pages`, `content`, `lines` and `tables` — the positional plane — can be written by either of
two programs, and which one is decided **per document** by `source.origin`, through
`ORIGIN_ORIGINATORS`:

| `source.origin` starts with     | Originator         |
|---------------------------------|--------------------|
| `digital-born` · `docx` · `pdf` | `digital-convert`  |
| `ABBYY-ALTO` · `ocr:` · `vlm:`  | `alto-postprocess` |

Matching is a **case-insensitive prefix** match, first match wins. An origin that matches
nothing does not raise — the check simply abstains, so a new origin string can land before the
table learns about it.

!!! info "`digital-convert` is a role, not a repository"
    It originates the positional plane for born-digital PDFs and DOCX files, and it **lives in
    `atrium-llm-enrich`** — which therefore appears in records under two program names. The role
    was renamed from `llm-enrich-digital` precisely so that the program name records *what was
    done*, not *which repository happened to host it*.

!!! warning "Two things this table is not"
    **It authorises writes; it is not the read-time answer.** To find out who wrote a block in a
    *given* record, read `assembled.blocks[<block>].program` — and for a field-split block,
    `provenance.contributors[]`, since the stamp names only the most recent writer. See
    [The document contract](document-contract.md).

    **The hub's prose table is one prefix short.** `docs/document_schema.md` lists
    `digital-born…` and `docx` as the digital-convert prefixes; the code also accepts a bare
    `pdf`.

## Branches of the two documented tools

A default branch is where a clone lands, and in both repositories that is not the whole story.

=== "page-classification"

    | Branch        | What it is                                                                              |
    |---------------|-----------------------------------------------------------------------------------------|
    | **`vit`**     | the default branch and the code; `test` currently points at the same commit             |
    | `test`        | staging, and the base for pull requests                                                 |
    | `master`      | **stale** — last moved 2026-06-26, and still holds an older `vit/…` subdirectory layout |
    | `clip`        | a parallel model family (CLIP-based), with its own Hugging Face repository              |
    | `agent-skill` | the Agent Skill packaging — see [Agent skills](../agent-skills.md)                      |
    | `gh-pages`    | the landing card                                                                        |

    `CONTRIBUTING.md` describes `master` as the stable branch. In practice the stable line is
    `vit`; see [Contributing standards](../contributing-standards.md).

=== "translator"

    | Branch        | What it is                                                                  |
    |---------------|-----------------------------------------------------------------------------|
    | **`master`**  | the default branch and the code; `test` currently points at the same commit |
    | `test`        | staging, and the base for pull requests                                     |
    | `main`        | **vestigial** — holds only the initial commit from 2026-02-18               |
    | `agent-skill` | the Agent Skill packaging — see [Agent skills](../agent-skills.md)          |
    | `gh-pages`    | the landing card                                                            |

The hub itself has `main`, `test` and `gh-pages` (the built site), plus a **`v1` tag** — the
channel every tool repository's CI pins the hub's reusable workflows to. See
[Architecture](architecture.md#the-ci-federation).

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                      | What was taken from it                                 |
|-----------------------------------------------------------------------------|--------------------------------------------------------|
| `atrium-project/_generators/repos.py:14-109`                                | each repository's role, stage and default branch       |
| `git ls-remote --symref` on all six repositories, 2026-09-22                | default branches and branch heads, verified live       |
| `atrium-project/docs/templates/shared/atrium_document.py:108-163, 217, 275` | `BLOCK_OWNERS`, `ORIGIN_ORIGINATORS`, the field splits |
| `atrium-project/docs/document_schema.md:104-143, 254-261`                   | the ownership tables and the `digital-convert` rename  |
| `atrium-project/docs/templates/shared/atrium_rocrate.py:110-119`            | `digital-convert` → `atrium-llm-enrich`                |
