# 🏛️ ATRIUM Ecosystem Architecture and Source-Code Verification Audit · Opus 4.8 Round (2026-06-22)

## 🗺️ Ecosystem Architecture and Baseline Verification

The computational ecosystem is divided into five primary repositories, each handling a discrete, specialized phase of 
the document processing pipeline. The baseline review, evaluated against the current state of the main branches,
demonstrates profound progress in operationalizing machine learning workflows. While core functionalities are maturing, 
the audit highlights specific areas for refinement regarding test dependency management, paradata centralization, and 
version synchronization.

The integration remains highly sequential: visual classification, structural parsing/OCR refinement, language modeling,
and final translation. Infrastructural alignment is critical to prevent downstream cascading errors.

| Repository Module              | Active HEAD Commit | Operational Scope                        | Live CI Health | Fast-Suite Testing Metrics |
|--------------------------------|--------------------|------------------------------------------|----------------|----------------------------|
| **atrium-page-classification** | c6e7f0c            | Visual ingestion, DLA, image sorting     | ✅ Green        | 210 passed                 |
| **atrium-translator**          | 91836fb            | In-place ALTO/AMCR English translation   | ✅ Green        | 183 passed                 |
| **atrium-alto-postprocess**    | 5868b0f            | OCR refinement, perplexity scoring       | ✅ Green        | 226 passed                 |
| **atrium-nlp-enrich**          | 6501591            | Semantic tagging, TEATER JSON extraction | 🔴 **Red**     | 192 passed                 |
| **atrium-project**             | dbcb6e7            | Master planning, roadmap orchestration   | ➖ N/A          | Documentation hub          |

---

## 🧵 Systemic Cross-Repository Technical Threads

These macroscopic threads require coordinated remediation to move from academic prototype to production-grade standards.

* **🧪 Thread G: Testing Environment Instability & Dependency Bleed**
Across all repositories, Python test requirements (`requirements-test.txt`) remain under-declared. Heavyweight libraries 
(PyTorch, FastText, etc.) are imported eagerly, causing CI runner exhaustion on CPU-only lanes. Implementing lazy-importing
wrappers or `@pytest.importorskip` decorators is necessary to isolate unit logic from deep learning runtimes.
* **📋 Thread H: Paradata Provenance Traceability Drift**
While paradata modules exist (`atrium_paradata.py`, `para_licenses.py`), they have diverged between repositories. 
The `atrium-translator` repository has successfully implemented dedicated unit tests for paradata, which should serve 
as the blueprint for the rest of the ecosystem to ensure standardized provenance logging.
* **🏷️ Thread F: Release Management & Version Hygiene**
Release hygiene has improved significantly, with formal GitHub releases now active for key repositories. However, 
there remains a systemic need to strictly synchronize semantic versions across internal APIs, `CITATION.cff` files, 
and external Zenodo deployments to avoid confusion.
* **⚙️ Thread I: Subprocess Testing Overhead**
Current CI metrics are artificially suppressed by executing CLI tests via shell subprocesses. Refactoring these to 
use direct Python module imports will provide accurate coverage metrics and expose hidden regressions.

---

## 🔬 Repository Diagnostics

### 1. 🖼️ atrium-page-classification

The foundational ingestion layer for the pipeline, handling image sorting and layout analysis.

* **Status:** ✅ CI is green. Formal GitHub releases are active (15+ releases to date).
* **Key Updates:** Integration of `pymupdf` (fitz) for optimized PDF extraction, runtime VRAM profiling, and successful 
architecture alignment to `EfficientNetV2-M`.
* **Action:** Ensure `CITATION.cff`, README, and GitHub release tags remain in strict lockstep - **DONE**

### 2. 📄 atrium-alto-postprocess

The core refinement tier, processing raw ALTO XML and assigning algorithmic quality scores.

* **Status:** ✅ CI is operational.
* **Key Updates:** Successful split-resource queuing (CPU workers for I/O; GPU worker for Qwen 2.5 0.5B perplexity scoring).
* **Action:** Update documentation to reflect `PERPLEXITY_THRESHOLD_MAX = 1000.0`. Refactor tests to invoke application
logic directly rather than using shell subprocesses to improve branch coverage.

### 3. 🧠 atrium-nlp-enrich

The most computationally intensive node, responsible for NER and LLM-constrained decoding.

* **Status:** 🔴 **Red.** CI failure is driven by top-level `import torch` statements in `llm_utils.py` that crash 
CPU-only CI runners, and Shellcheck configuration warnings.
* **Operational Note:** Qwen 2.5 14B (AWQ) is confirmed as the gold standard, effectively utilizing LogitMatch to
mitigate "Country Default" hallucinations.
* **Action:** Move heavy imports behind function guards/lazy-loaders. Add `SECURITY.md` to repository root. Fix 
Shellcheck `continue-on-error` directives.

### 5. 📁 atrium-project

The synchronization hub for orchestration and future scaling.

* **Focus:** Engineering hardware fail-over logic (GPU to CPU), legal review of paradata licensing, and finalizing a 
cross-repository Docker Compose wrapper to simplify pipeline initialization.

---

## 🚀 Upgraded Phased Strategic Roadmap

### ⚡ Phase 0: Immediate Triaging & CI Stabilization

* **Repair CI (nlp-enrich):** Inject `continue-on-error: true` into the Shellcheck job and gate heavy `torch` imports
behind lazy-loading functions/guards.
* **Version Convergence:** Audit and lock version strings across Zenodo, APIs, and citations.

### 📅 Phase 1: Dependency Management

* **Requirements Hygiene:** Audit and complete `requirements-test.txt` for every repository.
* **Import Optimization:** Apply `@pytest.importorskip` across all repositories to prevent CPU-only CI crashes.

### 📅 Phase 2: Core Coverage & Provenance Standardization

* **Refactor Tests:** Migrate CLI-based tests in `alto-postprocess` to direct Python imports.
* **Centralize Paradata:** Refactor the existing paradata logic into a unified shared submodule to prevent further 
drift between repositories.

### 📅 Phase 3: Orchestration & Hardware Scaling

* **Containerization:** Execute Issue #18 by deploying the cross-repository Docker Compose matrix.
* **Hardware Resilience:** Develop runtime monitors to trigger GPU→CPU fail-overs upon VRAM saturation.

### 🏁 Phase 4: Ground Truth & Security

* **Domain Training:** Finalize NameTag3 ontological fine-tuning (Issue #7).
* **Hardening:** Implement org-wide automated secret scanning and standardized `SECURITY.md` protocols.

---

#### 📚 Works cited

1. Classification of historical page images using ViT and CNN - for ATRIUM project - GitHub, [https://github.com/ufal/atrium-page-classification](https://github.com/ufal/atrium-page-classification)
2. ufal/atrium-translator: ATRIUM project in-place translation ... - GitHub, [https://github.com/ufal/atrium-translator](https://github.com/ufal/atrium-translator)
3. Extract keywords from the user-defined "vocabulary" using LLM request (TEATER topics) · Issue #6 · ufal/atrium-nlp-enrich - GitHub, [https://github.com/ufal/atrium-nlp-enrich/issues/6](https://github.com/ufal/atrium-nlp-enrich/issues/6)
4. ATRIUM's page classifier: Classification of historical page images using fine-tuned ViT, RegNetY,and EfficientNetV2 models | Zenodo, [https://zenodo.org/records/20737616](https://zenodo.org/records/20737616)
5. ATRIUM's page classifier: Classification of historical page images using fine-tuned ViT, RegNetY,and EfficientNetV2 models | Zenodo, [https://zenodo.org/records/20737638](https://zenodo.org/records/20737638)
6. ATRIUM's page classifier: Classification of historical page images using fine-tuned ViT, RegNetY,and EfficientNetV2 models - Zenodo, [https://zenodo.org/records/20681312](https://zenodo.org/records/20681312)
7. ufal/atrium-alto-postprocess: Post processing of ALTO XML files - GitHub, [https://github.com/ufal/atrium-alto-postprocess](https://github.com/ufal/atrium-alto-postprocess)
8. (PDF) Page image classification for content-specific data processing - ResearchGate, [https://www.researchgate.net/publication/394100556_Page_image_classification_for_content-specific_data_processing](https://www.researchgate.net/publication/394100556_Page_image_classification_for_content-specific_data_processing)
9. Calibration of the categorization logic applied to the set of extracted, [https://github.com/ufal/atrium-alto-postprocess/issues/3](https://github.com/ufal/atrium-alto-postprocess/issues/3)
10. Issues · ufal/atrium-alto-postprocess - GitHub, [https://github.com/ufal/atrium-alto-postprocess/issues](https://github.com/ufal/atrium-alto-postprocess/issues)
11. ufal - ÚFAL · GitHub, [https://github.com/ufal](https://github.com/ufal)
12. Q1-Q2 [WP4 / WP5: Mid-Project Workflow Beta Testing & Integration] · Milestone #1 - GitHub, [https://github.com/ufal/atrium-nlp-enrich/milestone/1](https://github.com/ufal/atrium-nlp-enrich/milestone/1)
13. NER - Training of domain-specific NameTag model · Issue #7 · ufal/atrium-nlp-enrich, [https://github.com/ufal/atrium-nlp-enrich/issues/7](https://github.com/ufal/atrium-nlp-enrich/issues/7)
14. Security - Overview · ufal/atrium-nlp-enrich - GitHub, [https://github.com/ufal/atrium-nlp-enrich/security](https://github.com/ufal/atrium-nlp-enrich/security)
15. atrium-translator/main.py at master · ufal/atrium-translator · GitHub, [https://github.com/ufal/atrium-translator/blob/master/main.py](https://github.com/ufal/atrium-translator/blob/master/main.py)
16. Workflows - ATRIUM Project, [https://atrium-research.eu/workflows/](https://atrium-research.eu/workflows/)
17. ufal/atrium-project: Repository backing the Project for ... - GitHub, [https://github.com/ufal/atrium-project](https://github.com/ufal/atrium-project)
18. Issues · ufal/atrium-project - GitHub, [https://github.com/ufal/atrium-project/issues](https://github.com/ufal/atrium-project/issues)
19. Issues · ufal/atrium-nlp-enrich - GitHub, [https://github.com/ufal/atrium-nlp-enrich/issues](https://github.com/ufal/atrium-nlp-enrich/issues)
20. ufal repositories - GitHub, [https://github.com/orgs/ufal/repositories](https://github.com/orgs/ufal/repositories)