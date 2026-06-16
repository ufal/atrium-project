# ATRIUM Project CI/CD Strategy: Align & Expand Docker + GitHub Actions

## Core Idea: Template & Thin Callers
The four ATRIUM repositories (`atrium-translator`, `atrium-alto-postprocess`, `atrium-nlp-enrich`, `atrium-page-classification`) share a large identical workflow core with a small set of per-repo differences. 

To formalize the common ground, we use a **single reusable workflow template** (`on: workflow_call`) hosted in `ufal/atrium-project`. Each tool repository reduces its CI to a ~15-line `docker.yml` caller that passes its specific differences as `inputs`. One edit to the central template updates all four repositories.

### Common Ground (Baked into the Template)
- **Triggers (in the callers):** `pull_request`, push to `[test, master]`, tags `v*`, and release `published`.
- **`test` Job:** Python 3.11; `pytest -m "not slow" --cov --cov-report=term-missing --cov-report=xml`; coverage outputs to Step Summary and as a `coverage.xml` artifact. Includes a token-guarded Codecov step and a non-blocking Ruff lint step.
- **`docker-build` Smoke Job:** PR-only, `push: false`, utilizes GHA cache to catch Dockerfile breakage that Python tests might miss.
- **`build-and-push` Job:** Gated by `needs: test` AND `if: tag || release`. Includes `docker/metadata-action` tag block and bakes provenance build-args (`ATRIUM_RUNNER_REPO/REF/IMAGE`) on every build.
- **Action Majors:** Upgraded to Node-24 compatible versions (`checkout@v5`, `setup-python@v6`, `login-action@v4`, `metadata-action@v6`, `setup-buildx-action@v4`, `build-push-action@v7`).

### Per-Repo Differences (Template Inputs)
| input               | translator                               | alto-postprocess              | nlp-enrich              | page-classification                                     |
|---------------------|------------------------------------------|-------------------------------|-------------------------|---------------------------------------------------------|
| `image-name`        | `ufal/atrium-translator`                 | `.../atrium-alto-postprocess` | `.../atrium-nlp-enrich` | `.../atrium-page-classification`                        |
| `apt-packages`      | `""`                                     | `build-essential g++`         | `""`                    | `build-essential g++ libgl1 libglib2.0-0 poppler-utils` |
| `pre-install-torch` | `""`                                     | `torch` (cpu index)           | `""`                    | `torch==2.7.1 torchvision==0.22.1` (cpu index)          |
| `requirements`      | `requirements.txt requirements-test.txt` | `+ service/requirements.txt`  | base only               | `setup/requirements.txt setup/requirements-test.txt`    |
| `hf-model-cache`    | `false`                                  | `false`                       | `false`                 | `true`                                                  |
| `build-targets`     | `["base"]`                               | `["base"]`                    | `["base","api","llm"]`  | `["base"]`                                              |

## Current-State Audit
* **Workflow files:** Currently scattered and duplicated. Page-classification uses 3 files (`ci-python`, `docker-publish`, `release`).
* **Action Majors:** Mostly running deprecated Node-20 versions, except `alto-postprocess`.
* **Push Triggers:** Inconsistent across repositories.
* **Python:** Page-classification currently tests on 3.10 but builds Docker on 3.11.
* **Provenance args:** Missing from the base build in `page-classification`.

### Critical Finding: `page-classification` Release Blocker
The tagged build for `atrium-page-classification` currently fails. The workflow attempts to build `target: api` (which does not exist in the Dockerfile), and the Dockerfile attempts to install `-r service-requirements.txt` which is never copied into the container context.

## Expansion Details
- **Coverage:** Utilizing `--cov` with `pytest`. Inline Python parsing routes `coverage.xml` to the Step Summary. Guarded `codecov/codecov-action@v4` will trigger once `CODECOV_TOKEN` is available.
- **Ruff:** Identical, non-blocking `ruff.toml` linting deployed across all four repositories to inform without gating.
- **Dependabot:** Deferred to a later round (see Appendix for ready-to-use template for `pip` and `github-actions`).

## Rollout Sequence
1.  Stand up `docker-tool.reusable.yml` and shared `.coveragerc` / `ruff.toml` in `atrium-project`.
2.  **translator:** Implement as caller (proves the template).
3.  **alto-postprocess:** Transition to caller, normalizing triggers.
4.  **nlp-enrich:** Rename `docker.yaml` -> `docker.yml`, remove stray branches, map 3-target builds via `build-targets`.
5.  **page-classification:** Consolidate 3 workflows to 2. Apply Dockerfile fixes to resolve missing `COPY` manifests. Keep `release.yml` standalone but bump `checkout@v4` to `v5`.