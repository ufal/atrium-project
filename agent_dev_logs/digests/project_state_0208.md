# ATRIUM UFAL Pipeline — Refreshed Project State Review

**Date:** August 2, 2026

## 1. Headline Verdict

The ATRIUM ecosystem is in its strongest structural shape to date, successfully converging around the new
`atrium_document` standard. The experimental `test` branches have been merged into their respective default
branches across all five tool repositories, followed by a coordinated wave of releases on July 31, 2026.
End-to-end (E2E) integration is functionally verified, with CI successfully threading a single document
JSON through all five processing stages.

---

## 2. Distributed Repository Architecture & Release State

The pipeline consists of six distributed repositories (one hub and five processing stages). A coordinated
release wave occurred on July 31, bringing the ecosystem up to date following the GitHub Actions (GHA) and Docker overhaul.

| Repository                        | Role                                         | Release Version (July 31) | Default Branch |
|-----------------------------------|----------------------------------------------|---------------------------|----------------|
| `ufal/atrium-project`             | Planning hub and cross-repo CI tracker       | —                         | `main`         |
| `ufal/atrium-page-classification` | Structural Perception (ViT/CNN classifier)   | `v1.7.2-beta`             | `vit`          |
| `ufal/atrium-alto-postprocess`    | Deserialization, OCR QC, Line Categorization | `v1.4.1-beta`             | `master`       |
| `ufal/atrium-translator`          | Protected XML/ALTO In-place Translation      | `v0.5.0`                  | `master`       |
| `ufal/atrium-nlp-enrich`          | NER, Morphosyntax, and TEITOK output         | `v0.18.1`                 | `master`       |
| `ufal/atrium-llm-enrich`          | LLM Semantic Enrichment (Local + Remote)     | `v0.10.2`                 | `main`         |

(Note: Release versions reflect the final July 31 cuts.)

---

## 3. Architectural Milestone: The `atrium_document` Standard

The most significant architectural shift is the full integration of the `atrium_document` standard.

* The pipeline now operates on a paradata-pair accretion model.


* Every tool in the pipeline receives a document JSON, modifies only its owned blocks, and outputs an
updated JSON that is byte-identical for untouched parameters.
* The `atrium_document.py` and `atrium_document.schema.json` files are now hub-canonical shared files, strictly
enforced across the ecosystem via the `para-drift` GHA check.

---

## 4. Pipeline Phase Updates (Current to August 2)

### Phase A: Page Classification (`atrium-page-classification`)

* **Model Deployment:** The Hugging Face hub push was completed, and the canonical vX.4 release was finalized.
* **Agent Skill Integration:** Issue #15 and Issue #26 were closed after successfully completing agent-skill
integration tasks, which included the client, `SKILL.md`, `serve.sh`, install docs, and smoke fixtures.

### Phase B/C: ALTO Post-Processing (`atrium-alto-postprocess`)

* **Document Schema Alignment:** The pipeline switched from `set_blocks` to `merge_blocks` for field-split outputs to
prevent downstream overwrites.
* **Text Extraction:** A JSON-2-TXT extractor draft was released in `v1.2.1-beta`, adding multi-structure JSON handling capabilities.

### Phase D.1: Protected Translation (`atrium-translator`)

* **Logic Cleanup:** The repository's logic was cleaned up by stripping out dead entity translation code and
strictly enforcing schema boundaries.
* **API Stability:** API version drift was permanently resolved, locking `_read_tool_version()` to the `para_config.txt` source.

### Phase D.2: NLP Enrichment (`atrium-nlp-enrich`)

* **Refactoring:** CoNLL-U parsing and ALTO bounding-box alignment were centralized in `teitok_alto.py` to prevent data drift.
* **Integration Testing:** The `run_document_hook()` was entirely rewritten with real ALTO and CoNLL-U integration
testing to fix previous native production errors.
* **Data Curation Tools:** Evaluated toolsets for collaborative document curation, confirming INCEpTION as top for
curation workflows and Label Studio as best for bulk ingestion.

### Phase D.3: LLM Semantic Enrichment (`atrium-llm-enrich`)

* **Document Generation:** Introduced `api_util/json_to_md.py` to efficiently regenerate annotated-Markdown files
directly from the JSON record, removing the need to re-request a TEITOK or PDF file.
* **Client Updates:** The `openrouter_client.py` was updated to fully support the converged flag structure for single-file scoping.
* **Data Formats:** Finalized data formats for LLM processing, establishing JSON for metadata storage, MD (+HTML/CSS)
for simplified textual layouts, and TEITOK XML for visually correct bounding boxes and NLP enrichment.

---

## 5. Cross-Cutting Infrastructure & CI/CD

* **End-to-End (E2E) Pipeline Smoke:** The E2E pipeline script was rewritten to thread a document JSON through all five
stages for genuine validation. Fixes were implemented for input types, permission mismatches, and entrypoint issues. A
second E2E GHA script was added to run both JSON-based and default pipelines in parallel.
* **OpenAPI & Agent Skills:** API services are standardized across all repositories in compliance with the OpenAPI
meta-contract (#32). The `agent-skill` branches are aligned, heavily gated, and functioning correctly.
* **Version Tagging:** The `@v1` tag was added to the `atrium-project` repository, and this tag is now referenced
everywhere in the other repositories, including the `agent-skill` branches.

---

## 6. Active Bottlenecks and Immediate Next Steps

1. **Digital-Born Document Support:** It is necessary to build an explicit PDF and DOCX to JSON converter to properly
map formatting actions and service digital-born documents.
2. **API Input Standardization:** A standing TODO is to ensure all `test` and `agent-skill` branches contain APIs that
accept JSON inputs in strict accordance with the `atrium_document` standard.
3. **CI/CD Finalization:** While CI hardening is largely complete, the team must address the external GPU runner for
`slow`-marked tests and establish branch protection on the hub's `main` and `test` branches.
