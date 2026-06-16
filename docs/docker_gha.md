# Strategy: Align & Expand Docker + GitHub Actions across the 4 ATRIUM tool repos

## Core Idea: Separate the COMMON GROUND (a template) from the per-repo DIFFERENCES

The four repos share a large identical core and a small set of genuine per-repo knobs. This strategy formalizes the 
common ground as a **single reusable workflow template** and reduces each repo to a thin caller that supplies only its differences.

### The Template: A Reusable Workflow (`on: workflow_call`)
Hosted once in [docker-tool.reusable.yml](../.github/workflows/docker-tool.reusable.yml), each tool repo maintains 
a ~15-line `docker.yml` that calls the central template with `secrets: inherit` and passes its specific 
requirements as `inputs`. 

**Common ground baked into the template (identical for all 4 repos):**

* **Triggers:** `pull_request` + push `[main, master, test]` + tags `v*` + release `published`.
* **Runtime Override:** Enforces `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` as a global environment variable to 
preemptively suppress and fix the Node.js 20 deprecation warnings for older actions (like `upload-artifact@v4`).
* **`test` job:** Python 3.11 environment; installs requirements; runs `pytest -m "not slow" --cov 
--cov-report=term-missing --cov-report=xml`; generates coverage Step Summary + `coverage.xml` artifact + token-guarded 
Codecov; runs a non-blocking Ruff linting step.
* **`docker-build` smoke job:** Runs on PRs only (`push: false`) utilizing GitHub Actions cache to catch Dockerfile 
breakage that Python tests might miss.
* **`build-and-push` job:** Gated by `needs: test` AND `if: tag || release`; utilizes `permissions: {contents: read, 
packages: write}`; implements `docker/metadata-action` for tagging; bakes provenance build-args 
(`ATRIUM_RUNNER_REPO/REF/IMAGE`) into every image.

**Per-repo differences expressed as template `inputs`:**

| Input Knob              | `translator`                             | `alto-postprocess`                     | `nlp-enrich`                             | `page-classification`                                   |
|-------------------------|------------------------------------------|----------------------------------------|------------------------------------------|---------------------------------------------------------|
| **`image-name`**        | `ufal/atrium-translator`                 | `…/atrium-alto-postprocess`            | `…/atrium-nlp-enrich`                    | `…/atrium-page-classification`                          |
| **`apt-packages`**      | ""                                       | `build-essential g++`                  | *Variable* (e.g., `git`)                 | `build-essential g++ libgl1 libglib2.0-0 poppler-utils` |
| **`pre-install-torch`** | ""                                       | `torch` (cpu index)                    | ""                                       | `torch==2.7.1 torchvision==0.22.1` (cpu)                |
| **`requirements`**      | `requirements.txt requirements-test.txt` | `requirements.txt service/... test...` | `requirements.txt requirements-test.txt` | `requirements.txt requirements-test.txt`                |
| **`hf-model-cache`**    | `false`                                  | `false`                                | `false`                                  | **`true`**                                              |
| **`build-targets`**     | `["base"]`                               | `["base"]`                             | `["base","api","llm"]`                   | `["base"]`                                              |

---

## Current-State Audit (Post-Rollout)

All component repositories have successfully migrated to the centralized template, aligning their environments and resolving previous discrepancies.

| Tool                    | Workflow file | Action majors | Python | Test cmd        | Build gate        | Provenance args |
|-------------------------|---------------|---------------|--------|-----------------|-------------------|-----------------|
| **translator**          | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **alto-postprocess**    | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **nlp-enrich**          | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |
| **page-classification** | `docker.yml`  | Node 24       | 3.11   | `-m "not slow"` | `needs: test`+tag | Present         |

---

## Expansion Details

* **Coverage (Step Summary & Codecov):** Coverage is generated via `--cov` flags and parsed inline for the Step Summary. 
It utilizes `actions/upload-artifact@v4` and `codecov/codecov-action@v4` (guarded by `if: env.CODECOV_TOKEN != ''`) to 
process the `coverage.xml`. The initial [.coveragerc](templates/.coveragerc) setup begins non-blocking.
* **Ruff Linting:** An identical, non-blocking [ruff.toml](templates/ruff.toml) configuration is shared across all 
four repositories.
* **Dependency Updates:** Weekly automated updates for `pip` and `github-actions` are deferred for a future iteration, 
utilizing a ready-to-use [dependabot.yml](templates/dependabot.yml) draft available in the [templates](templates) directory.

---

## Rollout Status & Verification

The rollout sequence for the unified CI/CD wrapper was completed successfully across the project suite.

* **Deployment Logs:**
* `atrium-translator`:  Release `v0.6.1` successfully passed actions checks
* `atrium-page-classification`: Release `v1.4.0-beta` successfully passed actions checks
* `atrium-alto-postprocess`: Release `v0.18.0` successfully passed actions checks
* `atrium-nlp-enrich`: Release `v0.14.0` successfully passed actions checks

* **Provenance Verification:** For all tagged builds, `ATRIUM_RUNNER_REPO`, `ATRIUM_RUNNER_REF`, and 
`ATRIUM_RUNNER_IMAGE` are successfully passed through the Dockerfile ARGs and recorded directly into the output 
`paradata/*.json` files via `atrium_paradata.py`.