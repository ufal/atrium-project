---
title: Agent skills
nav_order: 10
status: draft
round: 2
issue: 57
---

# Agent skills

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Install and use the five ATRIUM Agent Skills, and understand the contract they all implement.

## Sources

| Source | Section | Depth | Treatment |
|---|---|---|---|
| `atrium-project/docs/skills_catalog.md` | all 6 `## ` sections | 2 | split at depth 2 |
| `atrium-project/docs/agent_skill_strategy.md` | 18 real `## ` sections | 2 | ⚠️ **fence-aware split required** — a naive `^## ` regex finds 23 and shatters `## Appendix A` |
| `atrium-project/docs/skill_acceptance_runbook.md` | all `## ` | 2 | render, minus the "Results log (fill in)" table |


## Outline

### The five skills

### The server–client pattern

### The service contract

### Installing

### Authoring a skill
