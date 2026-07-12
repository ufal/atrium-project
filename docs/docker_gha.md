# ATRIUM GitHub Actions Strategy & Integration Report

> **Status:** Active Document (Updated: July 2026 / Fable 5)
> **Scope:** `atrium-translator`, `atrium-nlp-enrich`, `atrium-page-classification`, `atrium-alto-postprocess`,
> `atrium-llm-enrich`, and `atrium-project` (templates).
>
> This document serves as the master plan for the ATRIUM GitHub Actions automation strategy. It outlines the current
> deployment status across the suite, details the implemented workflows, and provides a prioritized roadmap for
> completing the CI/CD integration.

## 1. Current Deployment Status: Developed Workflows

The baseline CI/CD infrastructure has been successfully distributed and localized across the five tool
repositories. Standardized configuration files (`ruff.toml`, `.coveragerc`, `dependabot.yml`,
`.pre-commit-config.yaml`) are now present in every repository, ensuring localized control over quality thresholds.

### Standardized Baselines (Active in All Repositories)

* **Automated Testing:** Fast suites run via `pytest -m "not slow"` with coverage reporting on push/PR.
* **Code Linting:** Ruff linting is active (currently non-blocking to allow for baseline stabilization); pre-commit
runs in CI in every repo.
* **Dependency Management:** Weekly `pip` and GitHub Action updates via Dependabot.
* **Docker Operations:** Docker build smoke tests trigger on Pull Requests. Full Docker builds and pushes to the
GitHub Container Registry (GHCR) trigger automatically on version tags (`v*`) and published releases.
* **Version Syncing:** The `CITATION.cff` files are synced with internal `para_config` versions across the board
(verified in-sync in all five repos as of this revision).
* **Paradata Drift Guard:** Every repo calls `paradata-drift.reusable.yml@test` to diff its local
`atrium_paradata.py` / `para_licenses.py` against the hub canonicals (parity currently clean everywhere).

### Reusable Templates (`atrium-project`)

The output includes foundational templates designed to be dropped into or called by individual tool repositories:

* **ATRIUM Docker Tool Template:** A reusable workflow (`docker-tool.reusable.yml`) handling environment setup,
linting, testing with coverage, and multi-target Docker builds.
* **ATRIUM Security Template:** A reusable workflow (`security.reusable.yml`) that handles version consistency checks,
Trivy container image scanning, and SBOM generation.
* **Paradata Drift Check:** A reusable workflow (`paradata-drift.reusable.yml`) verifying canonical shared-file parity.
* **CodeQL / Dependabot / GPU Inference / Pre-commit / Scheduled Smoke / Secret Scanning:** Caller examples in
`docs/templates/workflows/`, mirrored (localized) in the tool repos.

> 📌 **Ref-pin convention:** all callers pin reusable workflows to **`@test`** — the ecosystem's authoritative
> integration branch. The last off-convention caller (`nlp-enrich/docker.yml` on `@main`) was corrected in the
> July 2026 bug-fix round (§2).

### Localized Repository Workflows

* **`atrium-alto-postprocess`:** CodeQL, Docker Build & Publish, pre-commit, Automated Releases, Scheduled Smoke
Tests, Paradata Drift, and Security & Supply-chain scanning. ✅ Reference implementation — fully on the current
action-version floor with correct triggers throughout.
* **`atrium-nlp-enrich`:** CodeQL, multi-target Docker builds (`base`, `api`, `llm`), GPU Inference Tests, an
advisory (non-blocking) pre-commit run, Releases, Scheduled Smoke Tests, Security scans, Paradata Drift, and a
dedicated Shellcheck workflow.
* **`atrium-page-classification`:** CodeQL, Docker Build & Publish (incl. `vit`/`clip` branch triggers), GPU
Inference Tests, pre-commit, Automated Releases, Scheduled Smoke Tests (HF caching + a `v4.3` model-revision
reachability check matching the Dockerfile `CMD` pin), Paradata Drift, and Security Scans
(`para-config-path: setup/para_config.txt`).
* **`atrium-translator`:** CodeQL, Docker Build & Push, pre-commit, Scheduled Smoke Tests, Release Bundling,
Paradata Drift, and Security Scans. CPU-only tool — no GPU lane by design.
* **`atrium-llm-enrich`:** CodeQL, Docker Build & Publish (`remote` + `llm` targets — `base` deliberately
unpublished, it carries no ENTRYPOINT), GPU Inference Tests, advisory pre-commit, notes-only Releases, Scheduled
Smoke Tests, Paradata Drift, and Security scans targeting the `-llm` image variant (largest CVE surface).

---

## 2. July 2026 Bug-Fix Round (issue #18 hardening)

An audit of all workflow files at `test` HEAD surfaced and fixed the following. Recorded here because two of the
fixes change published-image behavior.

### Cross-cutting (fixed in `docker-tool.reusable.yml`, propagates to all callers)

* 🐞 **Codecov gate was permanently false.** The upload step gated on `if: env.CODECOV_TOKEN != ''` while the token
only existed in the `secrets` context (invisible to `env.*` checks). Fixed by mirroring the secret into job-level
`env:` on the `test` job. Coverage now uploads as soon as a `CODECOV_TOKEN` secret exists.
* 🐞 **`base` build-target trap removed.** The template previously mapped `target: "base"` to an *empty* `--target`,
which Docker resolves to the **last** declared stage. In multi-stage repos this silently built/published the wrong
image — most concretely, `ghcr.io/ufal/atrium-nlp-enrich` (unsuffixed) was actually the `llm` stage. Since every
ATRIUM Dockerfile names its first stage `AS base`, targets now pass through verbatim.
  > ⚠️ **Consumer note:** the next tagged `nlp-enrich` release publishes a genuinely different (lighter,
  > batch-entrypoint) image under the unsuffixed tag. Anyone consuming it for LLM work must switch to `-llm`.
* **Release gate cleaned up:** `build-and-push` now fires on `startsWith(github.ref, 'refs/tags/v') ||
github.event_name == 'release'` (replacing the `target_commitish` hack).
* **Provenance correctness:** `ATRIUM_RUNNER_REPO` is passed as a full URL
(`https://github.com/<owner>/<repo>`), matching the Dockerfile ARG defaults; `ATRIUM_RUNNER_IMAGE` now carries the
per-target `-<suffix>`, so `:remote`/`:api`/`:llm` images self-report their own GHCR name in paradata.
* **Explicit tags block:** semver + sha + `latest` (on tag pushes) — previously `latest` was never applied.
* **Action-version floor raised:** `checkout@v7`, `setup-python@v6`, `cache@v6`, `upload-artifact@v7`,
`github-script@v9`, `codecov-action@v7`, `codeql-action@v4` (v3 deprecates Dec 2026), `gh-release@v3`,
`gitleaks-action@v3` (v2 EOL Sep 2026), docker actions at `login@v4` / `metadata@v6` / `buildx@v4` /
`build-push@v7`, `trivy-action@v0.36.0` (post-incident re-published tag, verified upstream).

### Per-repo

* **translator 🔴 P0:** `pre-commit.yml` contained an accidental *second* scheduled-smoke suite (midnight cron, full
`pytest tests/`, no Python setup, an issue-creating failure step lacking `issues: write`). Replaced with the real
pre-commit caller; the legitimate nightly lane in `scheduled-smoke.yml` is untouched.
* **nlp-enrich:** `docker.yml` re-pinned `@main` → `@test`; `shellcheck.yml` push trigger fixed
(`[main, master]` → `[test, master]` — `main` does not exist, so it never fired); action bumps.
* **nlp-enrich + llm-enrich 🐞:** the "exit-5 tolerant" guard in `scheduled-smoke.yml` / `gpu-inference.yml` was
dead code — `run:` steps execute under `bash -e`, so `pytest; rc=$?` aborted before `rc` was read, failing every
"no tests collected" run. Fixed with the `rc=0; pytest … || rc=$?` capture pattern.
* **llm-enrich:** action bumps to the floor; `docker.yml` build-targets comment refreshed for the new verbatim
target semantics (`base` stays excluded — no ENTRYPOINT, not a publishable image).
* **alto-postprocess / page-classification:** no functional changes required.

---

## 3. Roadmap: Further Changes Needed

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

> 📎 Note: the template now targets `gitleaks-action@v3`, which **requires** an org-level `GITLEAKS_LICENSE` secret
> for `ufal/*` repositories (free for education/OSS) — provision it alongside the policy sign-off.

* **Supply Chain Audits:** Integrate `pip-audit` into the scheduled smoke tests to catch vulnerabilities that
Dependabot might lag on.

### B. Quality Gates & Test Substance

* **Populate the slow lane:** `nlp-enrich` and `llm-enrich` still have **0** `@pytest.mark.slow` tests, so their
smoke/GPU lanes pass vacuously (via the now-working exit-5 tolerance). Mark the genuine network-integration tests
(LINDAT `call_udpipe`/`call_nametag`; llm-enrich's AMCR OAI-PMH harvest and a real OpenRouter/Ollama round-trip).
* **Ratchet Gates:** Once coverage counts and linting warnings settle, flip Ruff from non-blocking to **blocking**,
and establish a hard `fail_under` coverage threshold.
* **Codecov activation:** with the gate fixed, adding a `CODECOV_TOKEN` org secret is now sufficient to light up
coverage dashboards across all five repos — no further workflow changes needed.

### C. Infrastructure-Gated Goals

* **Self-Hosted GPU Validation:** `gpu-inference.yml` is deployed in `page-classification`, `nlp-enrich`, and
`llm-enrich` but stays inert until the ARUP self-hosted runner with an NVIDIA GPU is provisioned and labeled
`[self-hosted, gpu]` (@rharasim). `alto-postprocess`'s GPU lane (LayoutReader / Qwen-perplexity / GLM-4v paths)
remains to be added once the runner exists.
* **Reachability Testing:** Fold external LINDAT NMT endpoint and HuggingFace model URL pings into the scheduled
smoke tests for early-warning pipeline degradation detection (page-classification's HF `v4.3` revision check is
the existing prototype).
* **End-to-End Pipeline Smoke:** a minimal cross-repo fixture (single-page ALTO → postprocess → translate → enrich
→ TEITOK) run in CI — tracked as the issue #18 follow-up proposal; especially valuable given the `@test`-pinned
reusable architecture.

---

## 4. The Workflow Menu (Reference)

All ready-to-commit templates for these recommendations live in `docs/templates/workflows/`. Action versions strictly
match the Node-24 baseline (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`); see §2 for the current version floor.

| Workflow            | What it does                                 | Deployment state                                                             | Lives as        |
|---------------------|----------------------------------------------|------------------------------------------------------------------------------|-----------------|
| **Docker Tool**     | Test + coverage + multi-target GHCR publish. | ✅ All 5 repos (thin callers → `docker-tool.reusable.yml@test`).              | Reusable Bundle |
| **Security**        | Version-check + Trivy CVE scan + SBOM.       | ✅ All 5 repos (→ `security.reusable.yml@test`).                              | Reusable Bundle |
| **Paradata Drift**  | Canonical shared-file parity diff vs hub.    | ✅ All 5 repos.                                                               | Reusable Bundle |
| **CodeQL**          | Static security/quality analysis for Python. | ✅ All 5 repos (highest value: `nlp-enrich` subprocess/FastAPI surface).      | Standalone      |
| **Scheduled Smoke** | Runs `pytest -m slow` on a cron.             | ✅ All 5 repos — but slow lanes in `nlp`/`llm` are empty (see §3.B).          | Standalone      |
| **GPU Inference**   | Real CUDA paths on self-hosted runner.       | 🕐 Deployed in 3 repos, inert pending ARUP runner; `alto` lane still to add. | Standalone      |
| **Pre-commit**      | Enforces Ruff + ShellCheck + whitespace.     | ✅ All 5 repos (advisory in `nlp`/`llm`, blocking elsewhere).                 | Standalone      |
| **Secret Scanning** | Push-protection + Gitleaks history sweep.    | ⛔ **Blocked** pending ARUB/ARUP policy review + `GITLEAKS_LICENSE`.          | Standalone      |