---
title: Contributing standards
nav_order: 12
status: draft
round: 2
issue: 57
---

# Contributing standards

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Read the family contribution standard once — the branch model, the commit convention, the PR format — and see where each repository deviates.

## Sources

| Source | Section | Depth | Treatment |
|---|---|---|---|
| `atrium-project/docs/templates/CONTRIBUTING.md` | the 9,288 B skeleton | 2 | render as the family standard — **and say plainly that the five copies are unenforced** |
| `<5 tool repos>/CONTRIBUTING.md` | `## 🔁 Contributor Workflow` (413 B, byte-identical ×4) | 2 | **render once**, link from 4 |
| `<5 tool repos>/CONTRIBUTING.md` | `## 📋 Pull Request Format` (688 B, byte-identical ×4) | 2 | **render once**, link from 4 |
| `<5 tool repos>/CONTRIBUTING.md` | `## ✏️ Commit Messages` (the 659 B type table is identical in all six) | 2 | **render once**, link from 5 |
| `<5 tool repos>/CONTRIBUTING.md` | `## 🌿 Branches & Environments` (970–998 B, similarity 0.75–0.91) | 2 | render once + a 3-row per-repo delta table |
| `atrium-llm-enrich/CONTRIBUTING.md` | `## 🔗 Shared ("drop-in") code` (720 B) | 2 | **render once** — the only repo that documents the shared-code mechanism at all |


## Outline

### The family standard

### Branches & environments

<!-- ASSEMBLER: render once; per-repo delta is 3 example branch names + master/main -->

### Contributor workflow

### Pull request format

### Commit messages

### Shared ("drop-in") code

### Where each repository deviates

<!-- The five CONTRIBUTING copies are NOT vendored: docs/templates/CONTRIBUTING.md is a
     9,288 B skeleton with «placeholders», absent from MANIFEST.json, revendor_shared.sh
     and para-drift. Pairwise similarity of the five copies never exceeds 0.57. -->
