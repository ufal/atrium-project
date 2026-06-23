# 🏛️ ATRIUM Ecosystem Architecture and Source-Code Verification Audit

## 🗺️ Ecosystem Architecture and Baseline Verification

The computational ecosystem under evaluation is divided into five primary repositories, each handling a discrete, highly specialized phase of an advanced historical document processing pipeline. The baseline repository review plan, evaluated against the live states of the respective main branches, demonstrates profound progress in operationalizing complex machine learning workflows. These workflows are designed to execute the comprehensive digitization, categorization, semantic enrichment, and linguistic translation of historical and archaeological archives. However, alongside these advancements, the audit reveals critical vulnerabilities in testing infrastructure, version hygiene, and inter-repository code alignment that threaten the stability of the entire system.

The integration of these computational repositories is highly sequential and interdependent. Archival documents must first pass through visual classification to determine layout morphology, proceed to structural parsing and optical character recognition refinement, undergo deep language modeling for semantic enrichment, and finally conclude with an in-place semantic translation. Consequently, infrastructural failures, silent logical degradations, or configuration mismatches in upstream modules inevitably cascade throughout the ecosystem, magnifying errors in downstream processes. The current HEAD commits evaluated in this diagnostic assessment represent the absolute state of the respective repositories during the Opus 4.8 review round.

| Repository Module          | Active HEAD Commit | Operational Scope                                               | Live CI Health | Fast-Suite Testing Metrics           |
|----------------------------|--------------------|-----------------------------------------------------------------|----------------|--------------------------------------|
| atrium-page-classification | c6e7f0c            | Visual ingestion, Document Layout Analysis (DLA), image sorting | ✅ Green        | 210 passed, 3 environmental failures |
| atrium-translator          | 91836fb            | In-place ALTO/AMCR English semantic translation                 | ✅ Green        | 183 passed, 52% branch coverage      |
| atrium-alto-postprocess    | 5868b0f            | OCR structural refinement, LLM perplexity scoring               | ✅ Green        | 226 passed, 48% branch coverage      |
| atrium-nlp-enrich          | 6501591            | Semantic tagging, Named Entity Recognition, TEATER extraction   | 🔴 **Red**     | 192 passed, 35% branch coverage      |
| atrium-project             | dbcb6e7            | Master planning, milestone orchestration, roadmap oversight     | ➖ N/A          | N/A (Documentation hub)              |

---

## 🧵 Systemic Cross-Repository Technical Threads

Before isolating the diagnostic analysis to individual repositories, a macroscopic evaluation of the continuous integration pipelines and source-code structures reveals several overarching systemic threads. These technical threads require immediate, coordinated remediation across the entire organizational ecosystem. They represent instances where rapid academic prototype development paradigms have not successfully transitioned to the rigid production-grade software engineering standards required for high-availability microservices.

* **🧪 Thread G: Testing Environment Instability and Dependency Bleed**
Across all computational repositories within the pipeline, the declaration of Python test requirements—typically stored in isolated `requirements-test.txt` files—is critically under-declared and mismanaged. The automated testing pipelines rely heavily on immense machine learning libraries, including PyTorch, FastText, TensorBoard, and the Hugging Face Transformers ecosystem. Currently, the testing infrastructure attempts to initialize these heavyweight bindings on pure CPU continuous integration lanes during standard pull-request evaluations. Because the testing infrastructure lacks lazy-importing wrappers or execution decorators (such as `@pytest.importorskip("torch")`) to cleanly segregate deep learning execution from standard unit testing logic, developers cannot independently verify fundamental application logic without forcing the continuous integration runners to download and compile gigabytes of CUDA bindings. This frequently leads to runner memory exhaustion.
* **📋 Thread H: Paradata Provenance Traceability Drift**
A foundational tenet of the data processing architecture is its heavy emphasis on data traceability through comprehensive paradata logging. This provenance mechanism captures execution IDs, exact tool names, computational repository URLs, Python environment versions, hyperparameter configurations, and dynamic license resolutions. However, the core license tracking logic (primarily within `para_licenses.py` and `atrium_paradata.py`) has suffered severe developmental drift across the codebases. The post-processing module recently integrated critical deduplication fixes and schema upgrades that failed to propagate to the translation, visual classification, and semantic enrichment repositories. Compounding this vulnerability is the complete absence of dedicated unit testing coverage for the paradata resolution engine.
* **🏷️ Thread F: Release Management and Version Hygiene**
There is a pervasive, systemic divergence between the semantic versions declared in internal Application Programming Interfaces, the standard citation configurations, and the external archive deployments. Compounding this traceability crisis, multiple repositories exhibit zero official release artifacts deployed via the standard version control interface, despite multiple overlapping beta distributions existing in external academic indices such as Zenodo. This fragmentation severely degrades the scientific validity of the output datasets.
* **⚙️ Thread I: Subprocess Testing Overhead and Coverage Masking**
Continuous Integration metrics across the project are artificially deflated due to an architectural over-reliance on executing Command Line Interface (CLI) tests via shell subprocesses rather than direct Python module imports. When the test suite invokes functions like `subprocess.run()` to execute application logic, standard coverage tracking tools are fundamentally blinded to the inner execution paths, frequently resulting in 0% coverage reports for functionally tested files and masking the true operational readiness of the codebase.

---

## 🔬 Repository Diagnostics: Ingestion to Translation

### 1. 🖼️ atrium-page-classification: Visual Ingestion and Layout Classification

The `atrium-page-classification` repository functions as the foundational ingestion layer for the computational pipeline. Humanities digitization projects routinely generate vast, heterogeneous quantities of historical page images, presenting profound manual sorting challenges. This computational node categorizes pages based on their visual content, evaluating incoming image patches to detect graphical elements, text typologies, and complex structural layouts, thereby enabling highly tailored downstream analysis.

**📊 Operational State and Implementation Upgrades**
The visual classification repository maintains a robust, green continuous integration pipeline across its Docker builds, code security evaluations, pre-commit hooks, and CodeQL workflows. Recent key updates include the remediation of Cross-Origin Resource Sharing (CORS) wildcard-with-credentials vulnerabilities, the removal of brittle hardcoded category fallbacks, and the deep integration of the `pymupdf` library (via the `fitz` module) for optimized PDF extraction. To protect constrained deployment environments, engineers integrated an automated profiling routine and a runtime overflow check to monitor Video Random Access Memory (VRAM) pressure and gracefully throttle tensor allocations. Furthermore, a silent architecture mismatch within the v1.3 model was successfully corrected to utilize the EfficientNetV2-M backbone, replacing the less capable EfficientNetV2-S variant.

The dataset utilized for fine-tuning this architecture consists of 48,499 PNG images extracted from 37,328 archival documents, provided under a Public Domain license via the LINDAT repository.

| Model Architecture Backbone | Patch Resolution | Training Dataset Provenance | Primary Operational Advantage                               |
|-----------------------------|------------------|-----------------------------|-------------------------------------------------------------|
| vit-base-patch16-384        | High (384x384)   | 48,499 Archival Documents   | Superior attention mapping for complex textual layouts      |
| regnety_160.swag_ft_in1k    | Variable         | ImageNet-1k pre-trained     | Highly efficient parameter scaling for mixed media          |
| efficientnetv2_m.in21k      | Medium (224x224) | ImageNet-21k pre-trained    | Optimal accuracy-to-VRAM ratio for high-throughput batching |

**⚠️ Versioning Deficiencies and Codebase Vulnerabilities**
Despite operational resilience, the repository suffers from severe release hygiene deficiencies with zero formalized GitHub releases. The external Zenodo archive hosts conflicting distributions labeled v1.3.0-beta, v1.4.1-beta, and v1.14.1-beta. Internally, the API reports `1.4.0-beta`, while the `CITATION.cff` reports `1.4.2-beta`. Additionally, the testing infrastructure harbors hazardous execution scripts. The `logs_stat.py` and `test_run.py` utility modules contain bare, top-level imports for pandas and tensorboard tracking functions, triggering immediate process exits on purely CPU-bound testing lanes.

---

### 2. 📄 atrium-alto-postprocess: Textual Refinement and Algorithmic Quality Control

Following the visual classification phase, pages identified as containing textual layouts are processed through optical character recognition systems to generate raw ALTO XML structures. This module explicitly ingests these raw outputs, extracts recognized text lines, and executes rigorous algorithmic quality control to filter out generative OCR hallucinations, scanning artifacts, and degraded archival ink.

**🖥️ Hardware Orchestration and Processing Architecture**
This repository operates on a highly sophisticated split-resource queuing model. To prevent resource starvation, the architecture separates CPU-bound structural parsing from GPU-bound deep learning evaluations, scaling dynamically up to a default limit of 32 concurrent CPU processes. Concurrently, a single dedicated GPU worker securely holds a loaded instance of the Qwen 2.5 0.5B inference model. The pipeline utilizes the FastText language identification model modulated by `EXPECTED_LANGS` and a critical `TRUSTED_FOREIGN_LANGS` vector, preventing genuine historical anomalies (e.g., Latin ecclesiastical citations embedded within Czech reports) from being forcefully remapped.

**🧮 Heuristic Validation and Categorization Logic**
The refinement logic calculates a composite quality score ranging from 0.0 to 1.0, synthesized from ten distinct algorithmic signals. Based on this score and structural bypass rules, the system routes every line into one of five terminal categories:

| Output Category | Operational Description and Downstream Routing Action                                                          |
|-----------------|----------------------------------------------------------------------------------------------------------------|
| **Clear** ✅     | Passes all structural checks with a high composite quality score. Routed directly to downstream NLP.           |
| **Noisy** ⚠️    | Moderate quality score indicating isolated symbol issues, mid-word uppercase, or elevated perplexity.          |
| **Trash** 🗑️   | Severely corrupted text. Composite score below the operational threshold. Requires alternative OCR processing. |
| **Non-text** 🔣 | Intercepted by bypass rules (e.g., pure digits, ratios). Filtered out to prevent LLM hallucination.            |
| **Empty** 🫙    | Line contains only whitespace or paragraph separators. Safely ignored by subsequent pipelines.                 |

**🚨 Algorithmic Vulnerabilities and Testing Deficiencies**
Despite its fully operational status with 226 passing tests, the repository harbors an undocumented architectural defect within the `langID_classify.py` execution path. A hardcoded structural validation guard actively misfires, throwing erroneous execution warnings when configuring the perplexity tolerance threshold above 500.0, despite the theoretical architectural ceiling supporting configurations up to 1000.0. Furthermore, the repository exhibits a suboptimal 48% branch coverage footprint due to the systemic subprocess shell command testing issue.

---

### 3. 🧠 atrium-nlp-enrich: Semantic Enrichment and Ontological Mapping

The `atrium-nlp-enrich` repository is the most sophisticated node in the ecosystem, responsible for transforming clean, post-processed text strings into highly structured, semantically mapped metadata payloads via a dual-layered paradigm: deterministic Named Entity Recognition (NER) and advanced Large Language Model (LLM) constrained decoding.

**🏷️ Morpho-Syntactic Annotation and NameTag3 Protocols**
The primary deterministic layer relies on the NameTag3 engine to execute rigid morpho-syntactic annotation based on strictly defined domain-specific ontological guidelines.

| Ontological Class     | Extraction Rule Constraints and Operational Guidelines                                                            | Permitted Examples              | Excluded Examples                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------|---------------------------------------------------------|
| **Location** (LOC)    | Extract precise municipalities, provinces, and full addresses. Aggressively strip generic directional adjectives. | "Zutphen", "Steenstraat 34"     | "Northern France", "Dutch coastal area"                 |
| **Material** (MAT)    | Annotate materials strictly when they reference physical composition of an artifact. Ignore ambient references.   | "bone", "brick wall"            | "the glass from this excavation"                        |
| **Species** (SPE)     | Include human remains as biological species, exclude broad human influence metrics.                               | "dwarf birch", "cattle skull"   | "human influence", "the human"                          |
| **Time Period** (PER) | Extract defined historical eras, dendrochronological dating parameters with uncertainty bands, and years.         | "Carolingian Empire", "1483 +6" | "Period Late Neolithic" (extract only "Late Neolithic") |

**🧩 Dynamic Vocabulary Injection and Constrained LLM Decoding**
Following NER, text undergoes semantic enrichment via a locally hosted LLM inference engine. The pipeline utilizes a dynamic vocabulary harvesting script to fetch hierarchies of Czech-English archaeological term pairs from external TEATER GraphQL endpoints. It uses an embedding model (e.g., all-MiniLM-L6-v2) to perform semantic similarity searches, isolating only exact broad and narrow category trees. Using LogitMatch masking alongside a Pydantic schema formulation, the token generation probabilities are manipulated at the hardware level, guaranteeing the LLM can only select vocabulary tokens that perfectly populate the JSON template, eradicating LLM hallucination regarding output formatting.

**📈 Model Benchmarking and "Country Default" Vulnerabilities**
The system defaults to the Qwen 2.5 14B Instruct (AWQ) model as its operational gold standard. Lesser parameter models (Bielik 11B and Llama 3.1 8B) suffer from a "Country Default" hallucination phenomenon, defaulting to randomly selecting geographic entities like "Denmark" or "Djibouti" for dense, non-semantic archival metadata lines. The Mistral Nemo 12B model demonstrates extreme over-generalization, blindly assigning the category of "hillfort" (hradiště) to nearly all structural headers.

**🔴 Continuous Integration Collapse**
The continuous integration pipeline for this repository currently sits in a catastrophic red state. A misconfigured Shellcheck runner without a `continue-on-error: true` directive instantly stalls upon trivial Bash formatting warnings. The `keywords.py` module suffers from disastrously low test coverage (21%). CPU testing lanes actively crash during Pytest execution due to a top-level hardware binding request (`import torch`) in `llm_utils.py`. Finally, the repository lacks a formalized `SECURITY.md` protocol.

---

### 4. 🌐 atrium-translator: Linguistic Translation and Final Delivery

The `atrium-translator` repository serves as the concluding operational node, ingesting the semantically enriched ALTO and AMCR XML matrices and executing a complex, in-place linguistic transformation from Czech to English. This facilitates seamless integration with international aggregation portals and semantic web frameworks. By executing translations directly within the existing XML document object model, the repository preserves complex bounding-box coordinate geometries and structural hierarchies.

While the primary continuous integration pipelines report a stable, green operational status—bolstered by recent security patches mitigating XML External Entity (XXE) injection attacks—the repository exhibits severe testing logic vulnerabilities. The `load_vocab.py` module, responsible for orchestrating external HTTP requests against dynamic OAI-PMH and GraphQL endpoints, lacks any mocked connection testing. Critical operational files (`processors/identifier.py`, `para_licenses.py`, `main.py`) suffer from deeply suboptimal branch coverage (20% to 34%). Vital testing dependencies (`numpy`, `tqdm`, `fasttext-wheel`, `huggingface-hub`) are also omitted from the explicitly declared testing requirements.

---

### 5. 📁 atrium-project: Project Orchestration and Scalability Directives

The `atrium-project` repository does not harbor active inference pipelines but functions as the central nervous system for macroscopic organizational orchestration, hosting the master roadmap, milestone trackers, academic publication drafts, and long-term infrastructure planning documentation.

An audit reveals the trajectory of the ecosystem's future scalability:

* **Hardware Orchestration:** Engineering intelligent fail-over algorithms capable of seamlessly transitioning active machine learning inference loads from massively parallel H100 GPU clusters to heavy multi-core CPU queues in the event of persistent VRAM memory exhaustion or thermal throttling limits (Issues #26 and #27).
* **Compliance and Dissemination:** Tracking the critical legal review of paradata model licensing structures (Issue #6), establishing governance models for unified paradata logs (Issue #9), mapping storage architectures (Issue #16), and drafting official publications for the CAA Proceedings (Issue #13).
* **Containerization:** Addressing the absence of a unified, cross-repository Docker Compose orchestration matrix (Issue #18) to deploy an overarching containerization wrapper for the full five-node sequential pipeline.

---

## 🚀 Upgraded Phased Strategic Roadmap

To stabilize the failing continuous integration pipelines, rectify the pervasive traceability drift, and permanently resolve the architectural bottlenecks identified during this verification audit, a highly aggressive, multiphased strategic remediation matrix must be implemented.

### ⚡ Phase 0: Immediate Triaging and Pipeline Stabilization

* **Restore CI Stability in atrium-nlp-enrich:** Inject the `continue-on-error: true` directive into the misconfigured Shellcheck runner block. Modify pre-commit configurations to strip the `--exit-non-zero-on-fix` flag from the Ruff code formatting hook.
* **Ecosystem Version Convergence:** Synchronize internal REST API endpoint definitions, `CITATION.cff` configuration blocks, and external Zenodo payload indices to a single, unalterable semantic version string.
* **Isolate Hazardous Testing Scripts:** Dynamically mute or mock the `logs_stat.py` and `test_run.py` shell scripts in the page-classification repository to prevent top-level dependency imports from throwing immediate exit codes on pure CPU environments.

### 📅 Phase 1: Fast Lane Integrity and Dependency Management

* **Isolate Deep Learning Requirements:** Institute comprehensive, repository-specific `requirements-test.txt` files that explicitly declare all testing-specific dependencies. Audit every application and test file to implement rigid conditional imports (e.g., `@pytest.importorskip("torch")`).
* **Synchronize Algorithmic Quality Thresholds:** Rectify the hardcoded, misfiring warning validation loop within the `langID_classify.py` execution path in the `atrium-alto-postprocess` module, permitting the threshold to scale accurately up to 1000.0.

### 📅 Phase 2: High-Value Core Coverage and Provenance Unification

* **Refactor Shell Subprocess Testing:** Rewrite the integration test suites in `atrium-alto-postprocess` to directly invoke application logic via standard Python namespace imports, completely eliminating reliance on shell `subprocess.run()` calls.
* **Engineer Mock HTTP Responses:** Inject rigid mock HTTP response objects into the `load_vocab.py` test suite within the `atrium-translator` repository.
* **Standardize Paradata Generation Logic:** Extract deduplicated paradata tracking schemas currently isolated within the `atrium-alto-postprocess` environment, refactor into a standardized, cross-repository utility submodule, and guarantee deployment across all active computation nodes.

### 📅 Phase 3: Advanced Pipeline Maturity and Hardware Scaling

* **Finalize Structured LLM Inference Deployment:** Cement the Ollama execution engine running the Qwen 2.5 14B Instruct (AWQ) model as the immutable operational baseline in `atrium-nlp-enrich`. Permanently enforce dynamic Pydantic model serialization and LogitMatch mapping logic.
* **Unified Container Orchestration:** Execute Issue #18 by engineering an overarching Docker Compose matrix capable of wrapping all five sequential processing nodes.
* **Develop Runtime Evaluation Monitors:** Actively track GPU VRAM saturation metrics, implementing intelligent failover protocols to route active inference queues to multi-core CPU clusters upon detecting severe memory exhaustion (Issue #26).

### 🏁 Phase 4: Ground Truth Deployment and Dissemination

* **Synthesize Historical Training Datasets:** Adhere rigidly to the defined ontological constraint protocols to commence the final fine-tuning of the NameTag3 extraction logic (Issue #7).
* **Comprehensive Security Hardening Audit:** Utilize automated secret-scanning integrations (e.g., Gitleaks) and introduce formalized, rigid `SECURITY.md` protocols across all active repositories.
* **External Delivery:** Transition the resulting datasets, enriched with verifiable paradata and semantic translation matrices, into the LINDAT archival repositories for secure, long-term open-access preservation.

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