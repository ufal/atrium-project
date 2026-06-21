# ATRIUM GitHub Actions Strategy & Audit Report

> **Status:** Active Document
> **Scope:** `atrium-translator`, `atrium-nlp-enrich`, `atrium-page-classification`, `atrium-alto-postprocess`, and `atrium-project` (templates).
> 
> This document serves as the master plan for the ATRIUM GitHub Actions automation strategy. It outlines the current deployment status, details immediate architectural fixes required from the recent audit, and provides a prioritized roadmap for further CI/CD enhancements.

## Current Deployment Status & Audit

The baseline reusable Docker build/test/publish template is successfully deployed across the four tool repositories. 
This includes:

* `pytest -m "not slow"` + coverage reporting
* Ruff linting
* Docker build smoke tests on PRs
* Docker build & push to GHCR on tags
* Weekly pip dependency updates via Dependabot

## Mid-to-Long Term Roadmap (Further Items)

Once the immediate cleanup is complete, the following strategic items represent the next layer of CI/CD maturity for 
the project.

### Infrastructure-Gated Goals

* **Self-Hosted GPU Validation:** Deploy `gpu-inference.yml` for `page`, `alto`, and `nlp`'s LLM targets once the 
ARUP self-hosted runner with an NVIDIA GPU is provisioned and labeled `[self-hosted, gpu]` by @rharasim.

### Quality & Hygiene Ratcheting

* **Ratchet Gates:** Flip Ruff from non-blocking to blocking, and establish a coverage `fail_under` threshold once 
standard counts settle across the repositories.
* **Shellcheck Promotion:** Make the existing `shellcheck.yml` in `nlp-enrich` blocking once clean, and expand linting 
to `alto`'s setup scripts.

### Dependency Monitoring

* **Reachability Testing:** Fold LINDAT endpoint and HuggingFace model URL pings into the scheduled smoke tests for 
early warning detection.
* **Supply Chain Audits:** Integrate `pip-audit` into the `scheduled-smoke.yml` to catch vulnerabilities that 
Dependabot might lag on:
* 
```yaml
      - run: pip install pip-audit && pip-audit || true   # report-only; drop `|| true` to gate
```

---

## The Workflow Menu (Reference)

All ready-to-commit templates for these recommendations live in `docs/templates/workflows/`. Action versions strictly 
match the Node-24 baseline (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`).

### A. Security & Supply-Chain

| Workflow            | What it does                                | Value                                        | Lives as        | Template                |
|---------------------|---------------------------------------------|----------------------------------------------|-----------------|-------------------------|
| **CodeQL**          | Static security/quality analysis for Python | High (FastAPI surfaces, subprocess spawning) | standalone      | `codeql.yml`            |
| **Trivy Scan**      | Scans published GHCR image for CVEs → SARIF | High (Torch images)                          | reusable bundle | `security.reusable.yml` |
| **Secret scanning** | Push-protection + gitleaks history sweep    | High (Page HF-token history)                 | standalone      | `secret-scan.yml`       |
| **SBOM**            | SPDX SBOM per image for provenance          | Med                                          | reusable bundle | `security.reusable.yml` |

> ⚠️ **Trivy note:** `aquasecurity/trivy-action` tags ≤ 0.34.2 were compromised. Templates must pin **≥ 0.35.0** and 
> use the commit SHA.

### B. Scheduled / Integration ("Slow" lane)

| Workflow            | What it does                                  | Value                           | Lives as   | Template              |
|---------------------|-----------------------------------------------|---------------------------------|------------|-----------------------|
| **Scheduled smoke** | Runs `pytest -m slow` on a cron; opens issues | High (LINDAT & HF dependencies) | standalone | `scheduled-smoke.yml` |

### C. GPU / Heavy Inference

| Workflow          | What it does                          | Cost / Infra               | Lives as   | Template            |
|-------------------|---------------------------------------|----------------------------|------------|---------------------|
| **GPU inference** | Real CUDA paths on self-hosted runner | Needs ARUP self-hosted GPU | standalone | `gpu-inference.yml` |

### D. Quality Gates & Release

| Workflow          | What it does                                   | Value                     | Lives as        | Template                |
|-------------------|------------------------------------------------|---------------------------|-----------------|-------------------------|
| **pre-commit**    | Enforces ruff + shellcheck + whitespace        | Med (Parity gap)          | standalone      | `pre-commit.yml`        |
| **Version-check** | Asserts `CITATION.cff` == `para_config` == tag | High (Kills version skew) | reusable bundle | `security.reusable.yml` |
| **Auto Release**  | Auto release notes + artifact attach on `v*`   | Med                       | standalone      | `release.example.yml`   |

---

## Per-Repo Profiles & Context

### atrium-translator

*Light, CPU-only; LINDAT NMT + UDPipe + FastText; OAI-PMH/GraphQL vocab harvest in `load_vocab.py`; dual CLI+API.*

* **Priority:** Scheduled smoke (`-m slow`) because core translation relies on external LINDAT paths not exercised in 
standard PR CI. CodeQL is highly recommended due to the new `service/api.py` request-handling surface.

### atrium-nlp-enrich

*Shell-heavy LINDAT pipeline (`api_*.sh`) + subprocess-spawning FastAPI + 3 build targets (base/api/llm).*

* **Priority:** CodeQL is critical here because the FastAPI wrapper spawns subprocesses, creating a command-injection 
attack surface. Scheduled smoke is required due to upstream LINDAT fragility.

### atrium-page-classification

*GPU-first ViT classifier; biggest CUDA image; HF model pinned by revision (`-rev v43`).*

* **Priority (P0):** Native secret scanning and gitleaks history sweep are mandatory to guard against HF token regressions. 
Self-hosted GPU testing is highly critical because standard Ubuntu CI cannot run the real ViT inference path.

### atrium-alto-postprocess

*CPU torch (+ optional CUDA) + LayoutReader sparse-checkout; Qwen2.5/GLM-4v GPU paths; heaviest image.*

* **Priority:** Trivy image scanning is highly valuable given the heavy footprint (torch + LayoutReader + fastText). 
Scheduled smoke tests are necessary to ensure the upstream `FreeOCR-AI/layoutreader` and HF `lid.176.bin` dependencies 
remain reachable.