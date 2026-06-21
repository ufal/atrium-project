# ATRIUM GitHub Actions Strategy & Integration Report

> **Status:** Active Document (Updated: June 2026 / Opus 4.8)
> **Scope:** `atrium-translator`, `atrium-nlp-enrich`, `atrium-page-classification`, `atrium-alto-postprocess`, and `atrium-project` (templates).
> 
> This document serves as the master plan for the ATRIUM GitHub Actions automation strategy. It outlines the current 
> deployment status across the suite, details the implemented workflows, and provides a prioritized roadmap for 
> completing the CI/CD integration.

## 1. Current Deployment Status: Developed Workflows

The baseline CI/CD infrastructure has been successfully distributed and localized across the four primary tool 
repositories. Standardized configuration files (`ruff.toml`, `.coveragerc`, `dependabot.yml`) are now present in every 
repository, ensuring localized control over quality thresholds.

### Standardized Baselines (Active in All Repositories)

* **Automated Testing:** Fast suites run via `pytest -m "not slow"` with coverage reporting on push/PR.
* **Code Linting:** Ruff linting is active (currently non-blocking to allow for baseline stabilization).
* **Dependency Management:** Weekly `pip` and GitHub Action updates via Dependabot.
* **Docker Operations:** Docker build smoke tests trigger on Pull Requests. Full Docker builds and pushes to the 
GitHub Container Registry (GHCR) trigger automatically on version tags (`v*`).
* **Version Syncing:** The `CITATION.cff` files are now synced with internal `para_config` tags across the board.

### Reusable Templates (`atrium-project`)

The output includes foundational templates designed to be dropped into or called by individual tool repositories:

* **CodeQL:** Static security and quality scanning for Python.
* **Dependabot:** Weekly update schedules for `github-actions` and `pip`.
* **Docker Build & Publish:** A template workflow that calls a reusable Docker tool workflow (`docker-tool.reusable.yml`).
* **GPU Inference Tests:** A template configured for self-hosted GPU runners.
* **Pre-commit:** A CI job to run `.pre-commit-config.yaml`.
* **Scheduled Smoke Tests:** A template for nightly slow-lane testing.
* **Secret Scanning:** A template utilizing Gitleaks for history sweeps.
* **ATRIUM Security Template:** A reusable workflow (`security.reusable.yml`) that handles version consistency checks, 
Trivy container image scanning, and SBOM generation.
* **ATRIUM Docker Tool Template:** A reusable workflow (`docker-tool.reusable.yml`) handling environment setup, linting, 
testing with coverage, and multi-target Docker builds.

### Localized Repository Workflows

The output also contains the specific implementations of these workflows across the four active tool repositories:

* **`atrium-alto-postprocess`:** Includes localized workflows for CodeQL, Docker Build & Publish, pre-commit, 
Automated Releases, Scheduled Smoke Tests, and Security & Supply-chain scanning.
* **`atrium-nlp-enrich`:** Features workflows for CodeQL, multi-target Docker builds (`base`, `api`, `llm`), GPU 
Inference Tests, an advisory (non-blocking) pre-commit run, Releases, Scheduled Smoke Tests, Security scans, and a dedicated Shellcheck workflow.
* **`atrium-page-classification`:** Contains localized configurations for Docker Build & Publish, GPU Inference Tests,
pre-commit, Automated Releases, Scheduled Smoke Tests (including HuggingFace caching steps), and Security Scans.
* **`atrium-translator`:** Includes workflows for CodeQL, Docker Build & Push, Scheduled Smoke Testing Suites, Release Bundling, and Security Scans.

---

## 2. Roadmap: Further Changes Needed

To complete the GHA integration and reach full maturity, the following architectural updates and missing workflows must be deployed.

### A. Security & Secret Management (Pending Expert Review)

* **Secret Scanning (`secret-scan.yml`):** The implementation of native secret scanning (e.g., Gitleaks) to prevent 
HuggingFace tokens or internal credentials from leaking into the history is **currently paused**.

> ⚠️ **Action Required:** The specific scope and handling of secret checks is up for question. We require consultation 
> from security/infrastructure experts to establish the official policy for secret rotation and historical sweep 
> permissions before this workflow is activated, particularly for `atrium-page-classification`. 
> 
> **ARUP/ARUB Institutional Contacts for Policy Review:**
> * Pavel (UFAL)
> * or Ronald (ARUB)

* **Supply Chain Audits:** Integrate `pip-audit` into the scheduled smoke tests to catch vulnerabilities that Dependabot might lag on.

### B. Quality Gates & Linting Parity

* **Pre-commit Parity:** Deploy `.pre-commit-config.yaml` to `atrium-translator` and `atrium-nlp-enrich` to achieve parity 
with the Alto and Page-Classification repositories.
* **ShellCheck Integration:** Deploy `shellcheck.yml` to `atrium-nlp-enrich` to secure its heavy shell-scripting layer
(`api_*.sh`), which is currently unlinted. Expand to `alto`'s setup scripts as a secondary goal.
* **Ratchet Gates:** Once coverage counts and linting warnings settle, flip Ruff from non-blocking to **blocking**, 
and establish a hard `fail_under` coverage threshold.

### C. Infrastructure-Gated Goals

* **Self-Hosted GPU Validation:** Deploy `gpu-inference.yml` for `page-classification`, `alto-postprocess`, and 
`nlp-enrich`'s LLM targets. This is currently blocked until the ARUP self-hosted runner with an NVIDIA GPU is provisioned and labeled `[self-hosted, gpu]`.
* **Reachability Testing:** Fold external LINDAT NMT endpoint and HuggingFace model URL pings into the scheduled smoke 
tests for early warning pipeline degradation detection.

---

## 3. The Workflow Menu (Reference)

All ready-to-commit templates for these recommendations live in `docs/templates/workflows/`. Action versions strictly 
match the Node-24 baseline (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`).

| Workflow            | What it does                                  | Target Repo Profile                                                                      | Lives as        |
|---------------------|-----------------------------------------------|------------------------------------------------------------------------------------------|-----------------|
| **CodeQL**          | Static security/quality analysis for Python.  | High priority for **`nlp-enrich`** and **`translator`** (FastAPI / Subprocess surfaces). | Standalone      |
| **Trivy Scan**      | Scans published GHCR images for CVEs → SARIF. | High priority for **`alto-postprocess`** and **`page-class`** (Heavy Torch images).      | Reusable Bundle |
| **Secret Scanning** | Push-protection + Gitleaks history sweep.     | **Blocked** pending ARUB/ARUP policy review.                                             | Standalone      |
| **Scheduled Smoke** | Runs `pytest -m slow` on a cron.              | All repos (Crucial for external dependencies).                                           | Standalone      |
| **GPU Inference**   | Real CUDA paths on self-hosted runner.        | Needs ARUP self-hosted GPU provisioning.                                                 | Standalone      |
| **Pre-commit**      | Enforces Ruff + ShellCheck + Whitespace.      | **`translator`** and **`nlp-enrich`** (To reach parity).                                 | Standalone      |

