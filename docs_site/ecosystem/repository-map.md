---
title: Repository map
nav_order: 5
status: published
round: 6
issue: 57
---

# Repository map

Find the right repository in one look: what each of the six is for, which part of the
document record it is allowed to write, and where its documentation lives.

## The six at a glance

| Repository                                                                         | Role                                                                                                                                 | Default branch | Authorised to write, in the record                                                                                                               | Landing page                                                                                    | Docs here                                                        |
|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`atrium-page-classification`](https://github.com/ufal/atrium-page-classification) | Structural perception — eleven page categories that inform how each page is processed                                                | `vit`          | `page_categories` · `pages[]` *category, category_confidence*                                                                                    | [ufal.github.io/atrium-page-classification](https://ufal.github.io/atrium-page-classification/) | **[page-classification](../tools/page-classification/index.md)** |
| [`atrium-alto-postprocess`](https://github.com/ufal/atrium-alto-postprocess)       | Deserialisation of ALTO and every other OCR or text-bearing input, and OCR quality control — the fan-out point of the whole pipeline | `master`       | `pages` · `content` · `lines` · `tables` *(originator, OCR documents)*                                                                           | [ufal.github.io/atrium-alto-postprocess](https://ufal.github.io/atrium-alto-postprocess/)       | —                                                                |
| [`atrium-translator`](https://github.com/ufal/atrium-translator)                   | Protected translation — a terminal branch: its output is recorded, not consumed                                                      | `master`       | `translations` · `entities[]` *translation_en*                                                                                                   | [ufal.github.io/atrium-translator](https://ufal.github.io/atrium-translator/)                   | **[translator](../tools/translator/index.md)**                   |
| [`atrium-nlp-enrich`](https://github.com/ufal/atrium-nlp-enrich)                   | Morphosyntax and named entities — produces the TEITOK corpus format                                                                  | `master`       | `entities` · parts of `lines[]` and `pages[]` · `derived_from.teitok`                                                                            | [ufal.github.io/atrium-nlp-enrich](https://ufal.github.io/atrium-nlp-enrich/)                   | —                                                                |
| [`atrium-llm-enrich`](https://github.com/ufal/atrium-llm-enrich)                   | Semantic enrichment against the ATRIUM controlled vocabulary; also hosts `digital-convert`                                           | `main`         | `enrichment` · `forms` · `entities[]` *pid* · `regenerable.markdown` — and, as `digital-convert`, the positional plane of born-digital documents | [ufal.github.io/atrium-llm-enrich](https://ufal.github.io/atrium-llm-enrich/)                   | —                                                                |
| [`atrium-project`](https://github.com/ufal/atrium-project)                         | The hub — shared code, reusable CI, the end-to-end tests and this site                                                               | `main`         | nothing                                                                                                                                          | [ufal.github.io/atrium-project](https://ufal.github.io/atrium-project/)                         | you are here                                                     |

Where a repository has no section in **Docs here**, its own `README.md` is the reference, and
its landing page links to it.

Of the two documented tools, both are MIT-licensed code. **page-classification** runs its
models locally — on CPU, or faster on a CUDA GPU; **the translator** calls remote LINDAT
services by default and needs no GPU unless a self-hosted CTranslate2 model is chosen.

!!! note "The order is accretion order, not a chain of file handoffs"
    The rows are in the order a document record travels — page-classification writes first,
    llm-enrich last. That is **not** the order files move in. Only three real file handoffs
    exist (`PAGE_ALTO/`, `DOC_LINE_CATEG/`, `TEITOK/`), the translator's output is an end
    product rather than an input to a later stage, and `page_categories` informs a routing
    decision rather than feeding a program. [Pipelines](../pipelines.md)
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
inside `entities[]` — a field the schema reserves for it; entities themselves are created later, by nlp-enrich.

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

alto-postprocess records a truthful origin per input format: `ABBYY-ALTO` for ALTO, `ocr:<format>`
for the other OCR formats (PAGE XML, hOCR, ABBYY FineReader XML, DjVuXML, Tesseract TSV, a PDF's
OCR layer), `ocr:generic` for text whose making the file does not record, and
`digital-born-<kind>` for the born-digital documents it reads. For a born-digital document it
writes `source` only and leaves the plane to `digital-convert` — which reads only PDF and DOCX,
so a born-digital spreadsheet, slide deck, ODT, EPUB, RTF, HTML page or e-mail gets no positional
plane yet. The per-format list is in alto-postprocess's
[input formats reference](https://github.com/ufal/atrium-alto-postprocess/blob/master/docs/text_inputs.md#6-provenance-sourceorigin).

!!! info "`digital-convert` is a role, not a repository"
    It originates the positional plane for born-digital PDFs and DOCX files, and it **lives in
    `atrium-llm-enrich`** — which therefore appears in records under two program names. The role
    was renamed from `llm-enrich-digital` precisely so that the program name records *what was
    done*, not *which repository happened to host it*.

!!! note "This table authorises writes; the record says who wrote"
    To find out who wrote a block in a *given* record, read
    `assembled.blocks[<block>].program` — and for a field-split block,
    `provenance.contributors[]`, since the stamp names only the most recent writer. See
    [The document contract](document-contract.md).

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

| Source                                                                                                 | What was taken from it                                 |
|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| `atrium-project/_generators/repos.py:14-110`                                                           | each repository's role, stage and default branch       |
| `git ls-remote --symref` on all six repositories, 2026-09-23                                           | default branches and branch heads                      |
| `atrium-project/docs/templates/shared/atrium_document.py:108-163, 217, 275`                            | `BLOCK_OWNERS`, `ORIGIN_ORIGINATORS`, the field splits |
| `atrium-project/docs/document_schema.md:104-143, 254-261`                                              | the ownership tables and the `digital-convert` rename  |
| `atrium-translator/utils.py` (`process_metadata_xml`)                                                  | `translation_en` reserved but not filled               |
| `atrium-project/docs/templates/shared/atrium_rocrate.py:110-119`                                       | `digital-convert` → `atrium-llm-enrich`                |
| `atrium-alto-postprocess` @ `test` `2e2794d` — `text_formats.py` (`READERS`), `docs/text_inputs.md` §6 | the origins alto-postprocess records per input format  |
