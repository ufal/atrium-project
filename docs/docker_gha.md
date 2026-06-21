# GitHub Actions — per-repo workflow options & recommendations

> Companion to [`docker_gha.md`](./docker_gha.md). That document describes the **baseline already
> shipped** across the four ATRIUM tool repos (the reusable Docker build/test/publish template). This
> document explores **what else is worth running, and where each option is most useful** — turning the
> open "GH Actions automation" thread on [atrium-project#18](https://github.com/ufal/atrium-project/issues/18)
> into a prioritized, per-repo plan. Ready-to-commit templates for every recommendation live in
> [`templates/workflows/`](./templates/workflows/).

## 1. Current baseline (what already runs — do not re-add)

Provided by [`docker-tool.reusable.yml`](../.github/workflows/docker-tool.reusable.yml) + each repo's thin
caller, plus localized configs:

| Already in place                                                                         | Where                                        |
|------------------------------------------------------------------------------------------|----------------------------------------------|
| `pytest -m "not slow"` + coverage (Codecov, Step Summary, `coverage.xml` artifact)       | reusable `test` job                          |
| Ruff lint (non-blocking)                                                                 | reusable `test` job                          |
| Docker build **smoke** on PRs                                                            | reusable `docker-build-smoke` job            |
| Docker **build & push** to GHCR on `v*` tags/releases, with `ATRIUM_RUNNER_*` provenance | reusable `build-and-push` job                |
| Dependency updates (pip + github-actions, weekly → `test`)                               | localized `dependabot.yml`                   |
| Shell linting (non-blocking)                                                             | **nlp-enrich only** — `shellcheck.yml`       |
| Service-zip GitHub Release on tags                                                       | **page-classification only** — `release.yml` |

The issue's remaining ask — "build new tags/releases" ✅ (done), "test coverage + report generation"
✅ (done), "pip dependency updates" ✅ (done) — is therefore largely closed. Everything below is the
**next layer**: security/supply-chain, the untested `slow` paths, GPU validation, quality gates, and
release/version hygiene.

## 2. The menu — possible & useful workflows

Value/cost are relative; **all of these are free on GitHub-hosted runners for public repos** unless the
"Cost / infra" column says otherwise.

### A. Security & supply-chain

| Workflow                    | What it does                                                                      | Value                                                               | Cost / infra                                                          | Lives as                             | Template                                                               |
|-----------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------|-----------------------------------------------------------------------|--------------------------------------|------------------------------------------------------------------------|
| **CodeQL**                  | Static security/quality analysis for Python; results in Security tab; PR + weekly | High (all four now ship FastAPI; nlp spawns subprocesses)           | Free (public)                                                         | standalone                           | [`codeql.yml`](./templates/workflows/codeql.yml)                       |
| **Image vuln scan (Trivy)** | Scans the published GHCR image for OS+pip CVEs → SARIF to Security tab            | High for the torch images (page, alto)                              | Free                                                                  | reusable bundle                      | [`security.reusable.yml`](./templates/workflows/security.reusable.yml) |
| **Secret scanning**         | GitHub native push-protection (primary) + gitleaks history sweep                  | High for page (HF-token history)                                    | Free public; gitleaks-action needs a free `GITLEAKS_LICENSE` for orgs | standalone                           | [`secret-scan.yml`](./templates/workflows/secret-scan.yml)             |
| **SBOM + provenance**       | SPDX SBOM per image; optional signed build-provenance attestation                 | Med — supply-chain transparency; fits the paradata provenance theme | Free                                                                  | reusable bundle                      | `security.reusable.yml` (`sbom` job)                                   |
| **pip-audit**               | Audits installed deps against the PyPI advisory DB (catches what Dependabot lags) | Med                                                                 | Free                                                                  | add to scheduled-smoke or standalone | (snippet in §6)                                                        |

> ⚠️ **Trivy supply-chain note:** `aquasecurity/trivy-action` tags **≤ 0.34.2 were compromised** (March
> 2026 incident). Use **≥ 0.35.0** and pin to a commit SHA. The template already pins `0.36.0` with this note.

### B. Scheduled / integration ("slow" lane)

| Workflow                            | What it does                                                                                     | Value                                                                                       | Cost / infra   | Lives as                  | Template                                                           |
|-------------------------------------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|----------------|---------------------------|--------------------------------------------------------------------|
| **Scheduled smoke**                 | Runs `pytest -m slow` (the network/model paths PR-CI skips) on a cron; opens an issue on failure | High for LINDAT-dependent repos (translator, nlp) and HF-revision-pinned repos (page, alto) | Free (minutes) | standalone                | [`scheduled-smoke.yml`](./templates/workflows/scheduled-smoke.yml) |
| **Dependency reachability monitor** | Lightweight ping of LINDAT endpoints / HF model URLs                                             | Med — early warning before a user hits it                                                   | Free           | fold into scheduled-smoke | scheduled-smoke.yml                                                |

### C. GPU / heavy inference (infra-gated)

| Workflow                | What it does                                         | Value                                               | Cost / infra                                      | Lives as   | Template                                                       |
|-------------------------|------------------------------------------------------|-----------------------------------------------------|---------------------------------------------------|------------|----------------------------------------------------------------|
| **GPU inference tests** | Runs the real CUDA paths on a self-hosted GPU runner | High — ubuntu-latest can only test the CPU fallback | **Needs ARUP self-hosted GPU runner** (@rharasim) | standalone | [`gpu-inference.yml`](./templates/workflows/gpu-inference.yml) |

### D. Quality gates & hygiene

| Workflow                        | What it does                                                              | Value                                                 | Cost / infra | Lives as                               | Template                                                                                                                                              |
|---------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------|--------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **pre-commit in CI**            | Enforces ruff + shellcheck + whitespace/large-file hooks                  | Med — closes parity gap (missing in nlp + translator) | Free         | standalone                             | [`pre-commit.yml`](./templates/workflows/pre-commit.yml) + [`.pre-commit-config.example.yaml`](./templates/workflows/.pre-commit-config.example.yaml) |
| **shellcheck (promote/expand)** | Make nlp's non-blocking lint blocking once clean; add alto's setup script | Med (nlp), Low (alto)                                 | Free         | existing `shellcheck.yml` / pre-commit | —                                                                                                                                                     |
| **Ratchet gates**               | Flip Ruff to blocking + set coverage `fail_under` once counts settle      | Med                                                   | Free         | edit reusable/config                   | — (see `docker_gha.md`)                                                                                                                               |
| **Type checking (mypy)**        | Optional non-blocking static types on the pydantic-heavy services         | Low                                                   | Free         | standalone                             | (optional)                                                                                                                                            |

### E. Release & versioning

| Workflow                      | What it does                                                                               | Value                                                                     | Cost / infra | Lives as                     | Template                                                           |
|-------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|--------------|------------------------------|--------------------------------------------------------------------|
| **Version-consistency check** | Asserts `CITATION.cff` == `para_config.txt [tool] version` == git tag                      | **High — kills the recurring version skew** flagged across all four repos | Free         | reusable bundle / standalone | [`version-check.yml`](./templates/workflows/version-check.yml)     |
| **Requirements-pin check**    | (page) assert torch/torchvision pins match between `setup/` and `service/requirements.txt` | Med                                                                       | Free         | add to version-check         | version-check.yml                                                  |
| **Automated Release**         | Auto release notes + artifact attach on `v*`                                               | Med — page has it; others could adopt                                     | Free         | standalone                   | [`release.example.yml`](./templates/workflows/release.example.yml) |

### F. Docs / repo health (low priority)

| Workflow                | What it does                                                               | Value                                        | Lives as                  |
|-------------------------|----------------------------------------------------------------------------|----------------------------------------------|---------------------------|
| **Markdown link check** | `lycheeverse/lychee-action` over the doc-heavy READMEs/CONTRIBUTING        | Low                                          | standalone                |
| **Image size report**   | `wagoodman/dive` / compressed-size comment to track torch bloat            | Low (page, alto)                             | standalone                |
| **Concurrency control** | `concurrency: { group, cancel-in-progress: true }` cancels superseded runs | Low cost, saves minutes on slow torch builds | add to existing workflows |

## 3. Per-repo recommendations

Priorities: **P0** = do first / security-critical · **P1** = high value, cheap · **P2** = worthwhile later.

### atrium-translator
*Light, CPU-only; LINDAT NMT + UDPipe + FastText; OAI-PMH/GraphQL vocab harvest in `load_vocab.py`; dual CLI+API; pinned deps; no pre-commit config.*

| Pri | Workflow                                           | Why here specifically                                                                                                                                |
|-----|----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| P1  | Scheduled smoke (`-m slow`)                        | Core translation depends on external LINDAT NMT/UDPipe; PR CI never exercises it. `load_vocab.py` (OAI-PMH/GraphQL) is 0%-covered and network-bound. |
| P1  | Version-consistency check                          | `CITATION.cff` lagged `para_config` (`0.5.1` vs `0.6.1`); `date-released` drift noted.                                                               |
| P1  | pre-commit in CI (+ add config)                    | Parity gap — pre-commit config missing here.                                                                                                         |
| P1  | CodeQL                                             | New `service/api.py` adds a request-handling surface.                                                                                                |
| P2  | Trivy scan · SBOM · gitleaks · LINDAT reachability | Hygiene; image is small so scan cost is trivial.                                                                                                     |

*No GPU work — CPU-only tool.*

### atrium-nlp-enrich
*Shell-heavy LINDAT pipeline (`api_*.sh`) + **subprocess-spawning** FastAPI + 3 build targets (base/api/llm); lowest coverage; already has `shellcheck.yml`; no pre-commit config.*

| Pri | Workflow                                                     | Why here specifically                                                                                                 |
|-----|--------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| P1  | Scheduled smoke (`-m slow`)                                  | UDPipe/NameTag calls to LINDAT are the core; highest upstream-fragility of the four.                                  |
| P1  | CodeQL                                                       | The FastAPI wrapper **spawns subprocesses** → command-injection surface worth static analysis.                        |
| P1  | Promote shellcheck + add pre-commit config                   | Only shell-heavy repo (review thread D); make the existing lint blocking once clean; close the pre-commit parity gap. |
| P1  | Version-consistency check                                    | `CITATION.cff 0.14.0` vs `para_config 0.14.1`.                                                                        |
| P2  | GPU test for `llm` target · Trivy across base/api/llm · SBOM | The `llm` path is never exercised on CPU CI.                                                                          |

### atrium-page-classification
*GPU-first ViT classifier; biggest CUDA image; HF model pinned by revision (`-rev v4.3`); has `release.yml`; torch-pin mismatch (`setup/` pinned vs `service/requirements.txt` unpinned); prior plaintext-HF-token history in `setup/config.txt`.*

| Pri    | Workflow                                                          | Why here specifically                                                                                                                 |
|--------|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **P0** | Secret scanning (native + gitleaks)                               | A plaintext HF token previously lived in `setup/config.txt` before being moved to the `HF_TOKEN` env var — guard against regressions. |
| P1     | GPU inference tests (self-hosted)                                 | The only GPU-first tool; ubuntu CI can't run the real ViT inference path.                                                             |
| P1     | Trivy image scan                                                  | Largest attack surface (CUDA torch wheels).                                                                                           |
| P1     | Scheduled smoke incl. HF revision check                           | A pinned `-rev vX.Y` breaks silently if the HF model is moved/renamed.                                                                |
| P1     | Version-consistency + requirements-pin check                      | `CITATION.cff` vs `para_config` drift; `setup/` vs `service/` torch pins diverge.                                                     |
| P2     | CodeQL · SBOM · standardize `release.yml` · HF model-size monitor | —                                                                                                                                     |

### atrium-alto-postprocess
*CPU torch (+ optional CUDA) + LayoutReader sparse-checkout + `lid.176.bin` (~2 GB) baked at build; Qwen2.5/GLM-4v GPU paths; heaviest image; "healthiest of the four"; already has pre-commit.*

| Pri | Workflow                                                              | Why here specifically                                                                                                                           |
|-----|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| P1  | Trivy image scan                                                      | Heaviest image (torch + LayoutReader + fastText model).                                                                                         |
| P1  | Scheduled smoke + reachability                                        | The build pulls `FreeOCR-AI/layoutreader` and HF `lid.176.bin`/Qwen — fragile if any upstream moves; verify on a schedule, not just at release. |
| P1  | GPU inference tests (self-hosted)                                     | LayoutReader / Qwen perplexity / GLM-4v extraction are GPU paths.                                                                               |
| P1  | Version-consistency check                                             | Keep `CITATION.cff` ↔ `para_config` aligned.                                                                                                    |
| P2  | CodeQL · SBOM · image size monitor · shellcheck `setup_api_server.sh` | —                                                                                                                                               |

## 4. Shared vs per-repo placement

Mirror the DRY split already proven by `docker-tool.reusable.yml`:

- **Centralize** the uniform checks (Trivy scan, SBOM, version-consistency) as a **second reusable
  workflow**, [`security.reusable.yml`](./templates/workflows/security.reusable.yml), called from each repo
  via a ~15-line [`security.caller.example.yml`](./templates/workflows/security.caller.example.yml). One edit
  updates all four.
- **Keep standalone** the workflows that differ per repo or need different runners/secrets: `codeql.yml`,
  `scheduled-smoke.yml` (per-repo PARAM apt/torch/requirements), `gpu-inference.yml` (self-hosted),
  `secret-scan.yml`, `pre-commit.yml`, `release.yml`.
- **CodeQL specifically** is best left standalone (it runs in the analyzed repo and benefits from the
  language matrix) rather than wrapped in a reusable workflow.

## 5. Cost & infra notes

- **Free on public repos:** Actions minutes, CodeQL, native secret scanning + push protection, and
  code-scanning SARIF upload (Trivy results). No paid tooling is required for any P0/P1 item except GPU tests.
- **Needs ARUP infra:** the GPU inference tests require a **self-hosted runner with an NVIDIA GPU** labelled
  `[self-hosted, gpu]` — owner **@rharasim**. Until it exists, `gpu-inference.yml` simply queues; it does not
  block anything else.
- **Org licensing gotcha:** `gitleaks-action` asks org-owned repos for a free `GITLEAKS_LICENSE` secret.
  Native GitHub secret scanning has no such requirement, so prefer it as the primary control.
- **Minute budget:** the torch repos (page, alto) have slow builds — add
  `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` to cancel
  superseded runs. Scheduled jobs cost little; tune the cron frequency per repo.
- **Action currency (verified June 2026):** CodeQL **v4** (Node 24; v3 deprecates Dec 2026); gitleaks-action
  **v3** (Node 24; v2 EOL Sep 2026); Trivy-action **≥ 0.35.0** (SHA-pin). These match the Node-24 posture the
  repos already adopted (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`).

## 6. Suggested rollout

1. **P0/P1 cheap wins first (all repos):** `version-check.yml`, `codeql.yml`, the pre-commit pair for nlp +
   translator, and `scheduled-smoke.yml`. No new infra, immediate signal.
2. **page P0:** enable native secret scanning + push protection; add `secret-scan.yml`.
3. **Security bundle:** stand up `security.reusable.yml` in `atrium-project`, then add the thin caller to each
   repo (Trivy + SBOM + version-check in one). Start Trivy `exit-code: "0"` (report-only), flip to `"1"` later.
4. **Release/version hygiene:** adopt `release.example.yml` in translator/nlp/alto; add the page
   requirements-pin assertion.
5. **GPU tests last (infra-gated):** once @rharasim provisions a GPU runner, enable `gpu-inference.yml` for
   page, alto, and nlp's `llm` target.
6. **Ratchet:** flip Ruff to blocking and set coverage `fail_under` once numbers settle (review thread E).

`pip-audit` snippet (add to `scheduled-smoke.yml` or a standalone job):

```yaml
      - run: pip install pip-audit && pip-audit || true   # report-only; drop `|| true` to gate
```

## 7. Template index

All under [`templates/workflows/`](./templates/workflows/). Each is parameterized with `# PARAM` markers and
matches the repo's Node-24 action baseline.

| Template                                                | Purpose                                      | Primary repos                     |
|---------------------------------------------------------|----------------------------------------------|-----------------------------------|
| `security.reusable.yml` + `security.caller.example.yml` | Trivy image scan + SBOM + version-check, DRY | all four                          |
| `codeql.yml`                                            | CodeQL Python analysis (PR + weekly)         | all four                          |
| `secret-scan.yml`                                       | gitleaks history sweep                       | page (then all)                   |
| `scheduled-smoke.yml`                                   | `pytest -m slow` on cron + issue-on-failure  | translator, nlp (then page, alto) |
| `gpu-inference.yml`                                     | self-hosted GPU runner tests                 | page, alto, nlp-llm               |
| `pre-commit.yml` + `.pre-commit-config.example.yaml`    | run hooks in CI                              | nlp, translator (parity)          |
| `version-check.yml`                                     | standalone version-consistency               | all four                          |
| `release.example.yml`                                   | auto GitHub Release                          | translator, nlp, alto             |

## 8. Verification (when a template is adopted in a repo)

1. **Lint:** every template already parses (`python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('docs/templates/workflows/*.yml')]"`).
2. **CodeQL / Trivy / gitleaks:** open a PR (or push a `v0.0.0-rc` tag for image jobs); confirm results land
   in the repo's **Security** tab (Code scanning / Secret scanning).
3. **Scheduled smoke / GPU:** trigger manually via **workflow_dispatch** rather than waiting for the cron;
   confirm the `slow` suite runs and (for GPU) lands on the self-hosted runner.
4. **Version-check:** intentionally bump `para_config.txt` out of sync with `CITATION.cff` on a branch and
   confirm the job fails with the `::error::` annotation.
5. **Adoption pin:** replace `@main` in the reusable caller with a tag/SHA, and re-confirm the security
   action versions are still current (CodeQL/Trivy/gitleaks move fast).

   
# NEXT STAGE

An audit of the workflow configurations across the ATRIUM repositories reveals that while the bulk of the baseline 
automation has been successfully deployed, there are several architectural deviations, redundant files, and a 
critical security gap that need to be synchronized with the master plan.

Here is the exact breakdown of what is currently misaligned and how to resolve it.

---

## 1. Critical Security Gap (P0 Check)

### `atrium-page-classification`

* **Missing P0 Secret Scanner:** The repository currently has no `secret-scan.yml` workflow. The master plan 
explicitly flags this as a **P0 priority item** to prevent regressions due to a historical plaintext HuggingFace 
token leak in `setup/config.txt`.


* **Centralization Bypass:** It is completely missing the centralized `security.yml` caller. Instead, it uses 
standalone `image-scan.yml` and `version-check.yml` files. This completely bypasses the DRY centralized security 
architecture.



---

## 2. Redundant Workflow Work (DRY Cleanup)

The uniform security bundle `security.reusable.yml` centralizes three key actions into one pipeline: the container 
image vulnerability scan (Trivy), the SPDX SBOM generation, and the **version-consistency check**. Centralized 
callers invoke this via `security.yml`.

Because the version-consistency check is already baked into the central security workflow, keeping a standalone 
`version-check.yml` alongside an active `security.yml` causes the check to execute twice per run.

* **`atrium-translator`:** Contains both `security.yml` and `version-check.yml`. The standalone `version-check.yml` 
is redundant and should be deleted.


* **`atrium-alto-postprocess`:** Contains both `security.yml` and `version-check.yml`. The standalone 
`version-check.yml` is redundant and should be deleted.

---

## 3. Repository Hygiene & File Standardizations

### `atrium-nlp-enrich`

* **Extension Mismatch:** The mainline pipeline caller is named `docker.yaml` instead of standardizing on the `.yml` 
extension used across the rest of the project ecosystem. Rename this to `docker.yml` for uniform tracking.


### `atrium-project`

* **Unintended Active Pipelines:** The central project repository currently hosts active workflows like `gpu-inference.yml`
and `scheduled-smoke.yml` directly in its active `.github/workflows/` directory. Because `atrium-project` acts as a 
master documentation and planning repo rather than an application runtime environment, running these heavy integration 
workflows here will trigger unnecessary failures due to missing code dependencies. These belong strictly inside the 
`docs/templates/workflows/` folder as pristine references.



---

## 4. Per-Repo Cleanup Action Plan

Use this checklist to clean up your workspace and bring all repositories to a complete, production-ready state:

| Repository                       | Current File State                                   | Required Action                                                                                                                                                                                                                                                                                                                |
|----------------------------------|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`atrium-project`**             | Active testing pipelines in `.github/workflows/`<br> | **Remove** `gpu-inference.yml` and `scheduled-smoke.yml` from active workflows; ensure they exist only in your template directory.                                                                                                                                                                                             |
| **`atrium-translator`**          | Redundant version-checking pipelines                 | **Delete** `.github/workflows/version-check.yml` (The version check runs inside `security.yml`).                                                                                                                                                                                                                               |
| **`atrium-nlp-enrich`**          | Non-standard filename extensions                     | **Rename** `.github/workflows/docker.yaml` to `docker.yml`.                                                                                                                                                                                                                                                                    |
| **`atrium-page-classification`** | Redundant version-checking pipelines                 | Missing central security wrapper & missin1. **Delete** `image-scan.yml` and `version-check.yml`.  2. **Add** the central `security.yml` caller. 3. **Add** `secret-scan.yml` (P0 Priority blocker). **`atrium-alto-postprocess`** 3.  **Delete** `.github/workflows/version-check.yml` (Handled by the central security loop). |