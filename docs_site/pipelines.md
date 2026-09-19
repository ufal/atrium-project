---
title: Pipelines
nav_order: 2
status: draft
round: 2
issue: 57
authored: true
---

# Pipelines

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Understand every ATRIUM workflow from beginning to end — what goes in, what each stage does, what comes out, and what the point of it is. This is the page issue #57's 2026-09-17 TODO asks for.

## Sources

| Source                                                    | Section                                  | Depth | Treatment                                 |
|-----------------------------------------------------------|------------------------------------------|-------|-------------------------------------------|
| —                                                         | the two-layer model and all 13 workflows | —     | **AUTHORED** — see note below             |
| `atrium-project/docs/document_schema.md`                  | `## ` the accretion rules                | 2     | reference, not copied                     |
| `atrium-alto-postprocess/README.md`                       | `## 🛤️ Workflow Stages` (42,775 B)      | 3     | reference                                 |
| `atrium-translator/README.md`                             | `## 🧠 Logic Overview`                   | 3     | reference                                 |
| `atrium-nlp-enrich/README.md`                             | `## Workflow Stages`                     | 3     | reference                                 |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml` | header + stage steps                     | —     | reference (the real integration contract) |
| `atrium-project/.github/workflows/e2e-digital-smoke.yml`  | header                                   | —     | reference (born-digital path)             |


## Outline

### The correction this page makes

<!-- AUTHORED. Every existing diagram in the corpus draws five boxes with arrows
     between them. Verified against the tree 2026-09-17:
       * no repo reads TRANSLATED/  (0 hits in all four downstream repos)
       * nlp-enrich reads DOC_LINE_CATEG/ + the ORIGINAL ALTO/ (config_api.txt:2,15)
       * alto never consumes page_categories (hits are vendored schema only)
     So the file topology is a DAG that fans out from alto and terminates at the
     translator; what is linear is the RECORD. Draw both layers. -->

### Layer 1 — the file DAG

```mermaid
%% AUTHORED round 3. First Mermaid diagram in the corpus:
%% there are currently zero ```mermaid blocks across all six repos.
flowchart LR
  %% fans out from alto-postprocess; translator is terminal
```

### Layer 2 — the record accretion chain

```mermaid
%% AUTHORED round 3. Linear: each stage writes only its own block.
```

### The thirteen workflows

#### W1 — Scanned / OCR document pipeline

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W2 — Born-digital pipeline

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W3 — Digital → OCR re-origination hand-off

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W4 — Containerised service / API

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W5 — Agent-Skill workflow

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W6 — E2E smoke / integration contract

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W7 — Vocabulary harvesting & review

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W8 — Training / evaluation (page-classification)

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W9 — Parameter optimisation / rule coverage (alto)

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W10 — Document-understanding benchmark (llm-enrich)

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W11 — Format adaptation via flexiconv

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W12 — Annotation round trip

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

#### W13 — RO-Crate export / FAIR publication

<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->

### Two gaps this page must state, not paper over

<!-- 1. There is no cross-service orchestration: atrium-project/compose/
        docker-compose.pipeline.yml does not exist. Reproduce the E2E's
        invocations as the de-facto recipe.
     2. fixtures/e2e/README.md is truncated mid-sentence at the
        'Why the DOC_LINE_CATEG bridge exists' section. -->
