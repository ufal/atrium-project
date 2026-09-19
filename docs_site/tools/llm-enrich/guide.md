---
title: llm-enrich — Guide
nav_order: 71
status: draft
round: 2
issue: 57
repo: atrium-llm-enrich
role: guide
---

# llm-enrich — Guide

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Get llm-enrich running — install, configure, invoke — without reading the code.

## Sources

| Source                        | Section                                                            | Depth | Treatment                  |
|-------------------------------|--------------------------------------------------------------------|-------|----------------------------|
| `atrium-llm-enrich/README.md` | `## ⚙️ Setup`                                                      | 3     | split at depth 3 (1,368 B) |
| `atrium-llm-enrich/README.md` | `## Configuration (`llm_config.txt`)`                              | 3     | split at depth 3 (2,075 B) |
| `atrium-llm-enrich/README.md` | `## Vocabulary Harvesting (`vocab_build.py`)`                      | 3     | split at depth 3 (4,103 B) |
| `atrium-llm-enrich/README.md` | `## Local Inference — `transformers` / `vLLM` (`llm_run.py`)`      | 3     | split at depth 3 (896 B)   |
| `atrium-llm-enrich/README.md` | `## Remote Inference — OpenRouter (`openrouter_client.py`)`        | 3     | split at depth 3 (2,167 B) |
| `atrium-llm-enrich/README.md` | `## Lightweight Local — Ollama (`ollama_client.py`)`               | 3     | split at depth 3 (823 B)   |
| `atrium-llm-enrich/README.md` | `## Document-Level Input (`api_util/xml_to_md.py`)`                | 3     | split at depth 3 (866 B)   |
| `atrium-llm-enrich/README.md` | `## Visually-Rich Document Input (`api_util/doc_to_visual_md.py`)` | 3     | split at depth 3 (2,240 B) |
| `atrium-llm-enrich/README.md` | `## 🐳 Docker`                                                     | 3     | split at depth 3 (1,073 B) |


## Outline

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## ⚙️ Setup" depth=3 -->
### ⚙️ Setup

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Configuration (`llm_config.txt`)" depth=3 -->
### Configuration (`llm_config.txt`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Vocabulary Harvesting (`vocab_build.py`)" depth=3 -->
### Vocabulary Harvesting (`vocab_build.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Local Inference — `transformers` / `vLLM` (`llm_run.py`)" depth=3 -->
### Local Inference — `transformers` / `vLLM` (`llm_run.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Remote Inference — OpenRouter (`openrouter_client.py`)" depth=3 -->
### Remote Inference — OpenRouter (`openrouter_client.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Lightweight Local — Ollama (`ollama_client.py`)" depth=3 -->
### Lightweight Local — Ollama (`ollama_client.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Document-Level Input (`api_util/xml_to_md.py`)" depth=3 -->
### Document-Level Input (`api_util/xml_to_md.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## Visually-Rich Document Input (`api_util/doc_to_visual_md.py`)" depth=3 -->
### Visually-Rich Document Input (`api_util/doc_to_visual_md.py`)

<!-- ASSEMBLER: source="atrium-llm-enrich/README.md" section="## 🐳 Docker" depth=3 -->
### 🐳 Docker


!!! danger "Fence hazard"
    `atrium-llm-enrich/README.md` has **1 heading-looking line(s) inside fenced
    code blocks** at this depth. The splitter must track fence state — a bare
    `^## ` regex would emit phantom pages here. See `57.plan.md` §B.2.
