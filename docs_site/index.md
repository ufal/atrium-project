---
title: ATRIUM — UFAL documentation
nav_order: 1
status: published
round: 4
issue: 57
---

# ATRIUM — UFAL documentation

The tools the Institute of Formal and Applied Linguistics (ÚFAL, Charles University) builds for
**ATRIUM**, and how they fit together: a pipeline that takes scanned archival pages — typewritten
reports, handwritten field notes, photographs, drawings — and turns them into structured,
searchable, linguistically enriched records.

## What ATRIUM is

**ATRIUM** — *Advancing fronTier Research In the arts and hUManities* — is an EU project that
bridges four European research infrastructures: **DARIAH** (arts and humanities), **ARIADNE**
(archaeology), **CLARIN** (language technologies) and **OPERAS** (open scholarly communication).
More at [atrium-research.eu](https://atrium-research.eu/), and in the
[project presentation on Zenodo](https://zenodo.org/records/19500212).

This site documents ÚFAL's part: five tool repositories and the hub that holds them together.

## The six repositories

<div class="grid cards" markdown>

-   **[page-classification](tools/page-classification/index.md)**

    ---

    Sorts a scanned page into one of **eleven structural categories** — so a person or a script
    can decide whether it needs OCR, handwriting recognition, table extraction or image handling.

    [Overview](tools/page-classification/index.md) · [Guide](tools/page-classification/guide.md) · [Reference](tools/page-classification/reference.md)

-   **alto-postprocess**

    ---

    Turns OCR output into per-page ALTO, extracted text and a scored table of line quality — the
    point the whole pipeline fans out from.

    [Landing page](https://ufal.github.io/atrium-alto-postprocess/) · *documentation section to come*

-   **[translator](tools/translator/index.md)**

    ---

    Translates ALTO pages and AMCR metadata records **in place** — every tag, namespace and
    coordinate preserved; only the text changes.

    [Overview](tools/translator/index.md) · [Guide](tools/translator/guide.md) · [Reference](tools/translator/reference.md)

-   **nlp-enrich**

    ---

    Morphology, syntax and named entities for every text line, and the TEITOK corpus format with
    bounding boxes kept.

    [Landing page](https://ufal.github.io/atrium-nlp-enrich/) · *documentation section to come*

-   **llm-enrich**

    ---

    Keywords and vocabulary mapping against the ATRIUM controlled vocabulary, with local or remote
    LLMs — and the converter for born-digital documents.

    [Landing page](https://ufal.github.io/atrium-llm-enrich/) · *documentation section to come*

-   **atrium-project** — the hub

    ---

    The shared code every tool vendors, the CI they all run, the end-to-end tests, and this site.

    [Architecture](ecosystem/architecture.md) · [Repository map](ecosystem/repository-map.md)

</div>

The hub's own README lists llm-enrich among "experimental / auxiliary repositories"; the pipeline
treats it as its fifth stage, and the end-to-end tests run it as one. Both are true of it today.

## Start here

- **[page-classification](tools/page-classification/index.md)** — sort a scanned page into
  one of 11 structural categories, so you know what to do with it next
- **[translator](tools/translator/index.md)** — translate ALTO and AMCR XML in place, every
  tag and coordinate preserved
- **[Pipelines](pipelines.md)** — what the tools do, end to end, and the correction that
  every existing diagram in this ecosystem needs
- **[External tools & services](external-tools.md)** — the glossary, if a name is unfamiliar
- **[Repository map](ecosystem/repository-map.md)** — which repo owns what

And by question:

| If you want to…                                      | Read                                                                                            |
|------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| know what a record written by these tools looks like | [The document contract](ecosystem/document-contract.md)                                         |
| run a tool as a service, or on Kubernetes            | [Operations](operations.md)                                                                     |
| let a coding agent use a tool                        | [Agent skills](agent-skills.md)                                                                 |
| know what every field and label means                | [Schemas](contracts/schemas.md) · [SKOS & the ATRIUM vocabulary](contracts/skos.md)             |
| publish results to a repository or catalogue         | [RO-Crate export](contracts/rocrate.md)                                                         |
| change shared code, or contribute                    | [Architecture](ecosystem/architecture.md) · [Contributing standards](contributing-standards.md) |

## How this site is built

Every page here is **written**, not generated: each one ends with a *Sources* table naming what it
was written from and at which commit, and every value in it was read from the tools' code rather
than copied from their prose — where the two disagree, the page says so. The tools' own `README.md`
and `CONTRIBUTING.md` stay the canonical, full-length references; these pages are the map between
them, and the parts no single repository can state about itself.

The site's source is `docs_site/` in the hub. A pull request builds it with
`mkdocs build --strict`, which fails on any broken link or anchor between pages; a merge to `main`
publishes it to the `gh-pages` branch. The work is tracked in
[atrium-project#57](https://github.com/ufal/atrium-project/issues/57).

Two of the five tool sections — page-classification and the translator, the two furthest along —
are written; the other three follow.
