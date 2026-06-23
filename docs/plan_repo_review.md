# 🏛️ ATRIUM Source-Code Review · Opus 4.8 Round (2026-06-22) → Gemini DR (2026-06-23)

---

## 🗺️ Ecosystem Architecture and Baseline Verification

The computational ecosystem is divided into five primary repositories, each handling a discrete phase of the document
processing pipeline. The baseline repository review plan, evaluated against the live states of the respective main
branches, demonstrates significant progress in operationalizing the machine learning workflows, alongside critical
vulnerabilities in testing infrastructure, version hygiene, and inter-repository code alignment.

The integration of these repositories is highly sequential. Documents must pass through visual classification before
layout parsing, subsequent language modeling, and final translation. Consequently, infrastructural failures in upstream
modules cascade throughout the ecosystem. The current HEAD commits evaluated in this assessment represent the state
of the repositories during the Opus 4.8 review round:

| Repository Module          | Active HEAD Commit | Operational Scope                        | Live CI Health | Fast-Suite Testing Metrics           |
|:---------------------------|:-------------------|:-----------------------------------------|:---------------|:-------------------------------------|
| atrium-page-classification | c6e7f0c            | Visual ingestion, DLA, image sorting     | ✅ Green        | 210 passed, 3 environmental failures |
| atrium-translator          | 91836fb            | In-place ALTO/AMCR English translation   | ✅ Green        | 183 passed, 52% branch coverage      |
| atrium-alto-postprocess    | 5868b0f            | OCR refinement, perplexity scoring       | ✅ Green        | 226 passed, 48% branch coverage      |
| atrium-nlp-enrich          | 6501591            | Semantic tagging, TEATER JSON extraction | 🔴 **Red**     | 192 passed, 35% branch coverage      |
| atrium-project             | dbcb6e7            | Master planning, roadmap orchestration   | ➖ N/A          | N/A (Documentation hub)              |

---

### 🧵 Systemic Cross-Repository Technical Threads

Before isolating the diagnostics to individual repositories, a macroscopic analysis reveals several overarching systemic
threads that require immediate remediation across the entire organizational ecosystem. These threads represent instances
where prototype development paradigms have not successfully transitioned to production-grade software engineering standards.

**🧪 Thread G (Testing Environments):** Across all computational repositories, the Python test requirements—typically
stored in requirements-test.txt—are critically under-declared. Heavyweight machine learning libraries, such as PyTorch,
FastText, and TensorBoard, crash fundamental test collections when executed on pure CPU Continuous Integration lanes.
Because the infrastructure lacks lazy-importing wrappers (such as `pytest.importorskip`) to segregate deep learning
execution from standard unit testing logic, developers cannot independently verify fundamental string manipulation
or layout parsing logic without downloading gigabytes of CUDA bindings.

**📋 Thread H (Paradata Provenance Drift):** The ATRIUM project heavily emphasizes data traceability through paradata logging,
which captures execution IDs, tool names, hyperparameter configurations, and license resolutions. The core license tracking
logic (encapsulated in `para_licenses.py` and `atrium_paradata.py`) has drifted between codebases. The alto-postprocess module
contains deduplication fixes that have not been backported to the translator, page-classification, or nlp-enrich repositories.
Furthermore, the paradata resolution engine currently maintains **0% test coverage** across the ecosystem.

**🏷️ Thread F (Release and Version Hygiene):** There is a systemic divergence between the semantic versions declared in
internal APIs (`service/api.py`), standard citation configurations (`CITATION.cff`), and external archive deployments such
as Zenodo records. Compounding this issue, multiple repositories show zero official releases deployed via the GitHub
interface, despite multiple overlapping beta distributions existing in external academic indices.

**⚙️ Thread I (Subprocess Testing Overhead):** Continuous Integration metrics across the project are artificially deflated
because Command Line Interface (CLI) tests are executed via shell subprocesses rather than direct module imports. This
architectural choice prevents coverage tools from accurately tracking the execution of core application logic, resulting
in **0% coverage reports** for functionally tested files.

---

## 🔬 Repository Diagnostics: Ingestion to Translation

### 1. 🖼️ atrium-page-classification

The atrium-page-classification repository provides the foundational ingestion layer for the ATRIUM pipeline,
categorizing pages based on visual content (drawings, photos, text types, tabular layouts) to enable tailored downstream analysis.

#### 📊 Implementation Status and Version Analysis

- **CI/CD:** ✅ Maintains a robust green CI pipeline across Docker, Security, pre-commit, and CodeQL checks.
- **Key Updates Implemented:** CORS wildcard-with-credentials fix, removal of hardcoded category fallbacks, integration
  of pymupdf (via fitz), automated profiling routines, and runtime overflow check guards. The v1.3 model architecture was
  corrected to utilize EfficientNetV2-M.
- **⚠️ Version/Release Issues:** Zero GitHub releases. The Zenodo archive hosts overlapping distributions (v1.3.0-beta,
  v1.4.1-beta, v1.14.1-beta). Internally, `api.py` reports `1.4.0-beta`, and `CITATION.cff` reports `1.4.2-beta`.

#### 🛠️ Development Roadmap and Corrective Actions

- **🐛 Open Issues:** No reported GitHub issues currently open.
- **🚨 Immediate (P0) Action:** Fix `logs_stat.py` which breaks the pytest suite on CPU testing lanes due to a bare import
  `pandas` and tensorboard exit triggers. Wrap in a lazy import.
- **🔴 High Priority (P1) Action:** Synchronize versioning. Align internal API, Zenodo records, and `CITATION.cff` to a single
  semantic version tag (e.g., `1.4.2-beta`).
- **🟡 Medium Priority (P2) Actions:** Add `@pytest.mark.slow` or `@requires_torch` to `test_run.py` to prevent CPU-lane CI
  pipeline failures. Remove hardcoded model mapping dictionaries in `logs_stat.py`.

---

### 2. 📄 atrium-alto-postprocess

The atrium-alto-postprocess module represents the core refinement tier, ingesting raw ALTO XML text lines and processing
them into structured statistics tables, assigning a quality score based on 10 distinct algorithmic signals
(Valid Word Ratio, Perplexity Score, Language Score, etc.).

#### 📊 Implementation Status and Active Issues

- **CI/CD:** ✅ Fully operational (226 tests passed).
- **Key Updates Implemented:** `CITATION.cff` aligned with paradata configuration.
- **⚠️ Coverage:** Suboptimal 48% due to subprocess shell command testing.
- **🐛 Open Issues (Not Done):**
  - Issue #4: Comprehensive documentation of algorithmic categorizations.
  - Issue #3: Calibration of categorization logic against new beta testing text strings.
  - Issue #2: Fundamental update to definitions of text categories.
- **🔴 Architectural Bug (A-2):** A hardcoded validation guard in `langID_classify.py` incorrectly triggers a warning when
  configuring perplexity thresholds above `500.0` (despite the max being `1000.0`). Testing requirements incorrectly claim
  "no ML models" are required.

---

### 3. 🧠 atrium-nlp-enrich

The most sophisticated computational node, executing Named Entity Recognition (NER), morpho-syntactic annotation,
and complex key-phrase extraction mapped to controlled vocabularies.

#### 📊 Baseline State and Pipeline Vulnerabilities

- **CI/CD:** 🔴 **Red state.** A Shellcheck runner deployed without `continue-on-error: true` stalls workflows on minor warnings.
- **Key Updates Implemented:** Updated `CITATION.cff`, new test cases for utilities (100% on `teitok_read.py`, 90% on `flexiconv_convert.py`).
- **⚠️ Version/Release Issues:** Codeversion drifted to `v0.14.2`, but no GitHub packages are published. Lacks a formalized `SECURITY.md`.
- **🐛 Open Issues (Not Done):**
  - Issue #6: Deployment of locally hosted LLM inference pipeline mapping unstructured text to TEATER vocabulary
    (Currently using Qwen 2.5 14B Instruct via dynamic vocabulary injection and LogitMatch masking).
  - Issue #7: Specialized NER pipeline training (NameTag3 with strict ontological guidelines for ARTEFACT, PERIOD, LOCATION, CONTEXT).
  - Issue #8: Wrapping pipeline into a REST API service.
  - Issue #9: Resolving image file dependence in TEITOK format outputs.
  - Issue #10: Establishing Flexiconv-supported input streams.
  - Issue #11: Multilingual NameTag3 bases.

#### 🛠️ Corrective Actions

- `keywords.py` sits at **21% coverage**. CPU lanes crash due to top-level `import torch` in `llm_utils.py`.

---

### 4. 🌐 atrium-translator

The concluding node executing in-place translation for NLP-enriched XML formats (ALTO/AMCR) into English.

#### 📊 Operational State and Vulnerabilities

- **CI/CD:** ✅ Green.
- **Key Updates Implemented:** XXE injection attack mitigations applied to `load_vocab.py`. Logic backend streams achieved **100% test coverage**.
- **⚠️ Version/Release Issues:** Internal API reports `0.6.1`, codebase tag sits at `0.6.2`, `CITATION.cff` date is stale.
- **🔴 Coverage & Dependency Deficiencies:** `load_vocab.py` has 0% dedicated testing for OAI-PMH and GraphQL schemas.
  Low coverage in `processors/identifier.py` (21%), `para_licenses.py` (20%), and `main.py` (34%). Missing dependencies
  (`numpy`, `tqdm`, `fasttext-wheel`, `huggingface-hub`) trigger Thread G failures.

---

### 5. 📁 atrium-project (Orchestration and Planning)

The central synchronization hub storing documentation, review trackers, and the macroscopic roadmap.

#### 🗂️ Open Issues and Future Scaling (Not Done)

- **🖥️ Hardware Utilization:** Issue #27 (H100 model parallelization), Issue #26 (Fail-over logic to CPU).
- **🤖 Advanced Automation:** Issue #24 (Broad LLM heuristics for standard archival data), Issue #10 (LLM self-auditing feedback loop).
- **📢 Dissemination:** Issue #13 (CAA Proceedings drafting), Issue #22 (Document Understanding platform evaluations),
  Issue #16 (Data storage mapping for ARUP/B), Issue #21 (Releasing datasets to LINDAT).
- **🔒 Compliance and Containerization:** Issue #6 (Legal review of model licenses for paradata), Issue #9 (Governing
  unified paradata logs), Issue #18 (Cross-repository Docker Compose wrappers).

---

## 🚀 Upgraded Phased Strategic Roadmap

This upgraded strategy provides an actionable framework to unify the divergent codebases, resolve CI/CD failures,
and scale the machine learning infrastructure.

### ⚡ Phase 0: Immediate Triaging and Pipeline Stabilization *(Immediate Execution)*

- **🔴 Restore CI Stability in nlp-enrich:** Inject `continue-on-error: true` into the failing Shellcheck runner. Modify
  pre-commit hooks to strip `--exit-non-zero-on-fix` from the Ruff code linter.
- **🏷️ Ecosystem Version Convergence:** Enforce ecosystem-wide alignment of semantic version tags across Zenodo, internal
  APIs, and citations. Generate official GitHub release artifacts corresponding to external container deployments.
- **🧹 Cull Hazardous Testing Scripts:** Mute or mock `logs_stat.py` and `test_run.py` shell smokers in page-classification.

### 📅 Phase 1: Fast Lane Integrity and Dependency Management *(Days 1–7)*

- **🧪 Isolate Deep Learning Requirements:** Institute comprehensive `requirements-test.txt` files specific to each repo.
  Implement Pytest import-skips (e.g., `@pytest.importorskip("torch")`) for all heavy ML modules to allow rapid, local logic testing.
- **🔧 Synchronize Quality Thresholds:** Rectify the misfiring warning loop in `langID_classify.py` (alto-postprocess) to
  allow the perplexity threshold to scale fully up to `1000.0`.

### 📅 Phase 2: High-Value Core Coverage and Provenance Unification *(Weeks 2–3)*

- **🧩 Test Mocking and Import Substitution:** Refactor test suites in atrium-alto-postprocess to execute application
  logic via standard Python imports instead of `subprocess.run()`. Develop rigid mock response objects for `load_vocab.py` (translator).
- **📋 Standardize Paradata Generation:** Extract deduplicated paradata logic from alto-postprocess, refactor it into a
  standardized cross-repository submodule, and enforce deployment across all repositories.

### 📅 Phase 3: Advanced Pipeline Maturity and Hardware Scaling *(Weeks 4–6)*

- **🤖 Deploy Structured LLM Inference:** Finalize Issue #6 in nlp-enrich. Standardize Ollama execution engines running
  Qwen 2.5 14B Instruct (AWQ) with Pydantic model serialization and LogitMatch mapping.
- **🐳 Container Orchestration:** Execute atrium-project Issue #18 by deploying an overarching Docker Compose environment
  simulating the complete chronological workflow.
- **🖥️ Implement Hardware Fail-Overs:** Develop runtime evaluation checks to transition inference loads from GPU to heavy
  multi-core CPUs upon VRAM exhaustion (Issue #26).

### 🏁 Phase 4: Ground Truth Deployment and Dissemination *(Project Milestones)*

- **🏷️ NameTag3 Domain Customization:** Synthesize annotated historical datasets adhering to strict ontological constraints
  and commence fine-tuning (Issue #7).
- **🔒 Repository Hardening:** Audit organizational structure using automated secret scanning tools (e.g., Gitleaks).
  Introduce formalized `SECURITY.md` protocols across active repositories.
- **📤 External Delivery:** Proceed with formal submissions to CAA Proceedings and IJDL. Transition pipeline datasets
  into LINDAT archival repositories for long-term open-access preservation.