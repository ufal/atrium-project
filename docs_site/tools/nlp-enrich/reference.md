---
title: nlp-enrich — Reference
nav_order: 62
status: draft
round: 2
issue: 57
repo: atrium-nlp-enrich
role: reference
---

# nlp-enrich — Reference

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Look up a flag, an environment variable, an endpoint or an output field for nlp-enrich and stop reading as soon as you have it.

## Sources

| Source | Section | Depth | Treatment |
|---|---|---|---|
| `atrium-nlp-enrich/README.md` | `## Paradata Logs` | 3 | split at depth 3 (13,215 B) |
| `atrium-nlp-enrich/service/README.md` | whole file | 3 | render — REST service contract |
| `atrium-nlp-enrich/schemas/teitok/README.md` | whole file | 3 | render — TEITOK schema notes |
| `atrium-nlp-enrich/annotation/README.md` | whole file | 3 | render — Annotation section |
| `atrium-nlp-enrich/annotation/GUIDELINES.md` | whole file | 3 | render — Annotation section |
| `atrium-nlp-enrich/prompts/RUNBOOK.md` | whole file | 3 | render — OWNER of this file; llm-enrich transcludes it |
| `atrium-nlp-enrich/data_samples/vocab/RUNBOOK.md` | whole file | 3 | render — OWNER of this file; llm-enrich transcludes it |
| `atrium-nlp-enrich/data_samples/vocab/6.D-eval.decision-package.md` | — | — | **EXCLUDED** — open memo addressed to named individuals |
| `atrium-nlp-enrich/data_samples/vocab/6.O3O4.decision-package.md` | — | — | **EXCLUDED** — open memo addressed to named individuals |


## Outline

<!-- ASSEMBLER: source="atrium-nlp-enrich/README.md" section="## Paradata Logs" depth=3 -->
### Paradata Logs

### Annotation

<!-- ASSEMBLER: source="atrium-nlp-enrich/annotation/README.md" section="*" depth=3 -->
<!-- ASSEMBLER: source="atrium-nlp-enrich/annotation/GUIDELINES.md" section="*" depth=3 -->

### Vocabulary & prompts

<!-- ASSEMBLER: source="atrium-nlp-enrich/data_samples/vocab/RUNBOOK.md" section="*" depth=3 -->
<!-- ASSEMBLER: source="atrium-nlp-enrich/prompts/RUNBOOK.md" section="*" depth=3 -->

### TEITOK schema

<!-- ASSEMBLER: source="atrium-nlp-enrich/schemas/teitok/README.md" section="*" depth=3 -->
