---
title: ATRIUM — UFAL documentation
nav_order: 1
status: partial
round: 3
issue: 57
---

# ATRIUM — UFAL documentation

!!! warning "This page is still an outline — but the Tools section is written"
    The portal copy below has not been written yet. What **is** written, and is the
    reason to be here, is the tool documentation: **[page-classification](tools/page-classification/index.md)**
    and **[translator](tools/translator/index.md)**, five pages each, plus the
    [Pipelines](pipelines.md) and [External tools & services](external-tools.md)
    entries those two tools need.

    The round-2 build-time assembler is retired: it existed to slice each tool's
    `README.md` into site pages, which produced 38 pages carrying no information that
    was not already published. These pages are written instead, and each one's
    `## Sources` table records what it was written from, at which commit.


## Purpose

The portal. A reader arriving cold leaves knowing what ATRIUM is, which six repositories exist, what each one does, and which of the three entry points (Pipelines, External tools, a tool section) answers their question.

## Sources

| Source                     | Section                                            | Depth | Treatment                                               |
|----------------------------|----------------------------------------------------|-------|---------------------------------------------------------|
| `atrium-project/README.md` | whole file (1,094 B)                               | —     | not yet written into this page                          |
| —                          | portal copy, the six-card grid, the pipeline strip | —     | **pending**                                             |


## Outline


### What ATRIUM is

### The six repositories

### Start here

- **[page-classification](tools/page-classification/index.md)** — sort a scanned page into
  one of 11 structural categories, so you know what to do with it next
- **[translator](tools/translator/index.md)** — translate ALTO and AMCR XML in place, every
  tag and coordinate preserved
- **[Pipelines](pipelines.md)** — what the tools do, end to end, and the correction that
  every existing diagram in this ecosystem needs
- **[External tools & services](external-tools.md)** — the glossary, if a name is unfamiliar
- **[Repository map](ecosystem/repository-map.md)** — which repo owns what

The remaining three tool sections — alto-postprocess, nlp-enrich and llm-enrich — are not
written yet; their repositories' own landing pages are at
`ufal.github.io/atrium-<name>/`.

### How this site is built

<!-- one paragraph: derived at build time from untouched sources; link to issue #57 -->
