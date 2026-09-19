---
title: alto-postprocess — Changelog
nav_order: 43
status: draft
round: 2
issue: 57
repo: atrium-alto-postprocess
role: changelog
---

# alto-postprocess — Changelog

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Find what changed in alto-postprocess between two versions, and link to a single release.

## Sources

| Source | Section | Depth | Treatment |
|---|---|---|---|
| `atrium-alto-postprocess/CONTRIBUTING.md` | `## 📦 Release History` | 3 | **transposed** — one anchored `###` per version, newest first (section is 69,669 B file total) |


## Outline

<!-- ASSEMBLER: source="atrium-alto-postprocess/CONTRIBUTING.md" section="## 📦 Release History" depth=3 note="transpose: 3-col table -> one ### per version" -->
### Releases

<!-- Two parsing hazards the transposer must survive:
       * page-classification's rows contain `|` inside code spans, so a naive
         split('|') reads a 3-column row as 5;
       * translator's section carries 17 non-table lines (block-quote
         expansions between rows) that a table-only transposer would drop.
     Assert row counts before and after. -->
