---
title: External tools & services
nav_order: 3
status: draft
round: 2
issue: 57
authored: true
---

# External tools & services

!!! warning "Draft shell — issue #57, round 2 (2026-09-18)"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.


## Purpose

Meet every external standard, service, model and piece of infrastructure ATRIUM depends on, in two sentences each, with a pointer to where it is used. Written for a reader who has never seen SKOS, RO-Crate or LINDAT.

## Sources

| Source                                           | Section                     | Depth | Treatment                                    |
|--------------------------------------------------|-----------------------------|-------|----------------------------------------------|
| —                                                | ~60 entries in 7 categories | —     | **AUTHORED**, but ~60 % lifts existing prose |
| `atrium-project/docs/skos_strategy.md`           | §1 §3 §5                    | —     | lift — written for exactly this reader       |
| `atrium-project/docs/rocrate_export.md`          | §2 "RO-Crate from zero"     | —     | lift — an explicit from-scratch tutorial     |
| `atrium-translator/docs/translation-backends.md` | comparison table            | —     | lift                                         |
| `atrium-project/docs/k8s_deployment.md`          | probe table                 | —     | lift                                         |


## Outline

<!-- Each entry: what it is (2 sentences) | where ATRIUM uses it (file paths) | link onward -->

### Metadata standards & serialisations

<!-- SKOS · RO-Crate 1.1 + Process Run Crate · JSON-LD · schema.org · Turtle/RDF · Dublin Core · JSON Schema · SPDX & Creative Commons · ORCID · CITATION.cff · w3id.org -->

### Domain vocabularies

<!-- AMCR heslář · TEATER · CNEC 2.0 · Getty AAT · OAI-PMH -->

### Data & OCR formats

<!-- ALTO XML v1–v4 · PAGE XML · hOCR · METS · TEI P5 · TEITOK · CoNLL-U / UD · IOB2 · the `source.origin` originator set -->

### Hosting, repository & registration

<!-- LINDAT/CLARIAH-CZ · Handle System / PID · Zenodo & DOI · SSH Open Marketplace · DOG & CLARIN Switchboard · Hugging Face Hub · GHCR · OpenRouter · Label Studio / Doccano -->

### Models

<!-- `ufal/vit-historical-page` · `facebook/fasttext-language-identification` · `Qwen/Qwen2.5-0.5B` · `hantian/layoutreader` · `THUDM/glm-4v-9b` · the LLM registry · CUBBITT · UDPipe 2 · NameTag 3 · Korektor · KER / YAKE / KeyBERT -->

### Runtime & infrastructure

<!-- Docker & Compose · Kubernetes · GitHub Actions · vLLM · Ollama · FastAPI · flexiconv · alto-tools · ruff / pre-commit / Dependabot · Trivy / CodeQL / Codecov -->

### The ATRIUM project itself

<!-- the four bridged infrastructures (DARIAH · ARIADNE · CLARIN · OPERAS) · UFAL · ARÚP / ARÚB / AISCR · the work packages · the DMP -->

### Named in the DMP, deliberately not implemented

<!-- CIDOC-CRM, PROV-O, PeriodO, DataCite, IIIF — rocrate_export.md §3 is the
     definitive statement and deserves surfacing rather than burying. -->

### Entries with no existing prose anywhere (write fresh)

| Gap                                 | Why it matters                                                                                        |
|-------------------------------------|-------------------------------------------------------------------------------------------------------|
| Handle System / PID                 | `hdl.handle.net/20.500.12800/1-6184` is the project's primary dataset citation                        |
| LINDAT/CLARIAH-CZ as an institution | four live API services plus the dataset repository depend on it                                       |
| OAI-PMH                             | the AMCR harvest protocol, never named as a protocol                                                  |
| Dublin Core                         | `dcterms:` is emitted; the string "Dublin Core" appears in **zero** files                             |
| Korektor                            | a live LINDAT call in `tools/quality_model/correct.py:55`, absent from every Acknowledgements section |
| ARÚP / ARÚB / AISCR                 | **the acronyms are never expanded anywhere in the ecosystem**                                         |
| Work packages & the DMP             | cited as the authority for RO-Crate, SKOS and DOG; no WP table exists                                 |
| Trivy / CodeQL / SARIF / Codecov    | gate every release; named only as action refs                                                         |
| DOG / CLARIN Switchboard            | DMP-mandated, zero code, planned under #56                                                            |
