# Strategy: Align & Expand Docker + GitHub Actions across the 4 ATRIUM tool repos

## Core Idea: Separate the COMMON GROUND (a template) from the per-repo DIFFERENCES

The four repos share a large identical core and a small set of genuine per-repo knobs. This strategy formalizes the 
common ground as a **single reusable workflow template** and reduces each repo to a thin caller that supplies only its differences.

### The Template: A Reusable Workflow (`on: workflow_call`)
Hosted once in [docker-tool.reusable.yml](../.github/workflows/docker-tool.reusable.yml), each tool repo maintains 
a ~15-line `docker.yml` that calls the central template with `secrets: inherit` and passes its specific 
requirements as `inputs`. 

**Common ground baked into the template (identical for all 4 repos):**
* **Triggers:** `pull_request` + push `[test, master]` + tags `v*` + release `published`.
* **`test` job:** Python 3.11 environment; installs requirements; runs `pytest -m "not slow" --cov 
--cov-report=term-missing --cov-report=xml`; generates coverage Step Summary + `coverage.xml` artifact + token-guarded 
Codecov; runs a non-blocking Ruff linting step.
* **`docker-build` smoke job:** Runs on PRs only (`push: false`) utilizing GitHub Actions cache to catch 
Dockerfile breakage that Python tests might miss.
* **`build-and-push` job:** Gated by `needs: test` AND `if: tag || release`; utilizes `permissions: {contents: read, 
packages: write}`; implements `docker/metadata-action` for tagging; bakes provenance build-args 
(`ATRIUM_RUNNER_REPO/REF/IMAGE`) into every image.
* **Actions:** Standardized on Node-24 action majors throughout (e.g., `checkout@v5`, `setup-python@v6`, `login-action@v4`).

**Per-repo differences expressed as template `inputs`:**

| Input Knob              | `translator`                             | `alto-postprocess`           | `nlp-enrich`           | `page-classification`                                   |
|:------------------------|:-----------------------------------------|:-----------------------------|:-----------------------|:--------------------------------------------------------|
| **`image-name`**        | `ufal/atrium-translator`                 | `…/atrium-alto-postprocess`  | `…/atrium-nlp-enrich`  | `…/atrium-page-classification`                          |
| **`apt-packages`**      | ""                                       | `build-essential g++`        | ""                     | `build-essential g++ libgl1 libglib2.0-0 poppler-utils` |
| **`pre-install-torch`** | ""                                       | `torch` (cpu index)          | ""                     | `torch==2.7.1 torchvision==0.22.1` (cpu)                |
| **`requirements`**      | `requirements.txt requirements-test.txt` | `+ service/requirements.txt` | base only              | `requirements.txt requirements-test.txt`                |
| **`hf-model-cache`**    | `false`                                  | `false`                      | `false`                | **`true`**                                              |
| **`build-targets`**     | `["base"]`                               | `["base"]`                   | `["base","api","llm"]` | `["base"]`                                              |

---

## Current-State Audit (Post-Rollout)

All component repositories have successfully migrated to the centralized template, aligning their environments 
and resolving previous discrepancies.

| Tool                    | Workflow file | Action majors | Python | Test cmd        | Build gate        | Provenance args |
|:------------------------|:--------------|:--------------|:-------|:----------------|:------------------|:----------------|
| **translator**          | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **alto-postprocess**    | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **nlp-enrich**          | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **page-classification** | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |

### Resolved Issues
* **`page-classification` consolidation:** The previously failing Docker release was resolved by deleting 
`ci-python.yml` and `docker-publish.yml` in favor of the new thin caller. The `target: api` build was dropped, 
and Python environments were unified to version 3.11. The Dockerfile was updated to properly copy 
`setup/requirements.txt` to `requirements.txt`.

---

## Expansion Details

* **Coverage (Step Summary & Codecov):** Coverage is generated via `--cov` flags and parsed inline for the Step 
Summary. It utilizes `actions/upload-artifact@v4` and `codecov/codecov-action@v4` (guarded by 
`if: env.CODECOV_TOKEN != ''`) to process the `coverage.xml`. The initial [.coveragerc](templates/.coveragerc) setup begins non-blocking.
* **Ruff Linting:** An identical, non-blocking [ruff.toml](templates/ruff.toml) configuration is shared across all four repositories.
* **Dependency Updates:** Weekly automated updates for `pip` and `github-actions` are deferred for a future iteration, 
utilizing a ready-to-use [dependabot.yml](templates/dependabot.yml) draft available in the [templates](templates) directory.

---

## Rollout Status & Verification

The rollout sequence for the unified CI/CD wrapper was completed successfully across the project suite.

* **Deployment Logs:**
  * `atrium-translator`: Automation steps verified and passed on June 15 and June 16, 2026.
  * `atrium-page-classification`: Release `v1.3.0-beta` successfully passed actions checks on June 15, 2026, with subsequent runs passing on June 16.
  * `atrium-nlp-enrich`: Automation steps verified and passed on June 16, 2026.
* **Provenance Verification:** For all tagged builds, `ATRIUM_RUNNER_REPO`, `ATRIUM_RUNNER_REF`, and 
`ATRIUM_RUNNER_IMAGE` are successfully passed through the Dockerfile ARGs and recorded directly into the output 
`paradata/*.json` files via `atrium_paradata.py`.