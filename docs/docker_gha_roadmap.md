# ATRIUM GHA + Docker — Refinement & Expansion Roadmap

> **Status:** Proposed · **Date:** 2026-08-04 · **Issue:** [#18](https://github.com/ufal/atrium-project/issues/18)
> **Companion:** [`docker_gha.md`](docker_gha.md) is the *current-state reference*. This file is the *plan*.
> **Scope of this document:** analysis and sequencing only. No workflow, Dockerfile or compose file was
> changed in the commit that introduced it.

## 0. Why this document exists

Issue #18 has done its original job. The ecosystem went from four un-containerised forks to a working
centralised CI/CD architecture: 7 hub reusable workflows, **38 caller jobs** (35 cross-repo + 3 hub-local)
all resolving to `@v1`, GHCR-published provenance-stamped images, two smoke workflows, and broadly green
CI across six repositories. Every done-criterion in [`../agent_dev_logs/plans/18.plan.md`](../agent_dev_logs/plans/18.plan.md)
is met except the two external items tracked in [#40](https://github.com/ufal/atrium-project/issues/40).

This document covers what comes after that, based on a full read of all six working trees plus live GitHub
state on 2026-08-04. It found three classes of thing:

1. **Breakages that are live today** — two published API images that cannot start, a set of compose image
   references nobody can pull, provenance that names a tag which was never published, and an E2E assertion
   that guarantees failure on the exact path the workflow's own gate is designed to allow.
2. **Enforcement gaps** — the guardrails meant to hold the 2026-07-30 hardening in place cannot see most
   of what they claim to enforce. This is the important category, because it is *why* drift returns.
3. **Unfinished convergence** — ~1,020 lines of per-repo copy-paste with no hub reusable, and a Docker
   layer that has never been converged the way the workflow layer was.

The organising claim of this roadmap is the sequencing in §4: **guardrails before refactor.** The
2026-07-30 round landed timeouts on 45 jobs and concurrency on 33 workflows. Two days later a new hub
workflow shipped without either, plus no `permissions:` block, and CI stayed green — because the policy
linter has no rule for any of them. Collapsing another ~1,000 lines into the hub before the linter can
hold the result repeats that regression at five times the blast radius.

### The four decisions this roadmap treats as settled

| Decision                                                                                                                                          | Rationale                                                                                                                                                                                          |
|---------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Documentation-only round.**                                                                                                                     | The findings below need review by the people who own the affected repos before five-repo diffs land.                                                                                               |
| **All four expansion themes in scope** (collapse duplication · `:edge` images · supply-chain & image hygiene · Docker convergence & new targets). | They are not independent: `:edge` is what lets the collapsed workflows be validated without cutting a release, and the hygiene work is what makes the images worth publishing on a second channel. |
| **Retire `test`; protect the default branch.**                                                                                                    | `test` is currently a byte-identical mirror of the default branch in all six repos (§3.5). It doubles CI spend on every push and protects nothing.                                                 |
| **The GPU lane becomes runner-agnostic** and the `slow` marker splits into `slow` + `gpu`.                                                        | Removes the single-supplier dependency in #40 and lets the network-integration tests start running immediately, with no runner at all.                                                             |

---

## 1. What is already good (and must not regress)

Recorded because a findings list read alone gives a false impression, and because these are the properties
every wave below has to preserve.

- **One publishing authority.** `docker-tool.reusable.yml` is the only thing in the ecosystem that pushes
  an image. Five thin callers differ only by genuine per-repo knobs.
- **`secrets: inherit` is gone**, structurally and permanently: `docker-tool.reusable.yml` declares the one
  secret it consumes (`CODECOV_TOKEN`), the other reusables declare none, and `workflow_lint.py` parses for
  the pattern rather than grepping — deliberately, because the explanatory comments in those very files
  contain the literal string.
- **The release gate is real and already fires.** A tag build fails on **fixable CRITICAL** CVEs
  (`docker-tool.reusable.yml:301-308`: tags only, `severity: CRITICAL`, `ignore-unfixed: true`,
  `exit-code: "1"`), addressed by immutable digest, deliberately *after* the SARIF upload so findings are
  recorded even when the gate blocks.
- **`para-drift` genuinely holds.** All seven canonical shared files are byte-identical across all five
  tool repos, including the vendored `check_version.py`.
- **The version guard is well-tested.** `tests/test_check_version.py` has 16 tests, two of which
  deliberately make the files disagree because deleting the tag-vs-CITATION comparison passed everything
  else. `test_para_licenses.py` adds 36 more.
- **The E2E threads real data.** Five stages, real LINDAT calls, real OpenRouter round-trip, ~4 minutes.
- **Write-scoped actions are SHA-pinned with verified `# vX` comments**, and the linter resolves annotated
  tags correctly — a distinction that bit this ecosystem in practice.

---

## 2. Findings register

Each row cites a file and, where useful, a line. Line numbers are as of `main` at 2026-08-04.

### 2.1 Live breakages

| #      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                           | Evidence                                                                                                                                                                                                                         |
|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **B1** | **Two API images cannot start.** `uvicorn` appears in **no** requirements file in `page-classification` or `nlp-enrich`, yet page-classification's compose sets `entrypoint: ["uvicorn", "service.api:app", …]` and nlp-enrich's Dockerfile `api` stage declares the same as its `ENTRYPOINT`. Nothing catches it: `tests/test_api_contract.py` import-skips when the service deps are absent, and building a stage never invokes its ENTRYPOINT. | `atrium-page-classification/service/requirements.txt`, `docker-compose.yml:27`; `atrium-nlp-enrich/service/requirements.txt` (byte-identical to `requirements-test.txt`), `Dockerfile:43,52`                                     |
| **B2** | **Every suffixed compose `image:` reference is unpullable.** CI publishes a **repo-name** suffix; compose asks for a **tag** suffix. Six references across two repos.                                                                                                                                                                                                                                                                             | `docker-tool.reusable.yml:214` (`images: ghcr.io/…${{ matrix.target != 'base' && format('-{0}', matrix.target) \|\| '' }}`) vs `atrium-nlp-enrich/docker-compose.yaml:23,44` and `atrium-llm-enrich/docker-compose.yaml:4,29,53` |
| **B3** | **Paradata self-reports a tag that was never published.** `type=semver,pattern={{version}}` strips the leading `v`, publishing `1.7.3-beta`; the `ATRIUM_RUNNER_IMAGE` build-arg is `:${{ github.ref_name }}` = `v1.7.3-beta`. Compose's `${ATRIUM_VERSION:-dev}` default also expects the `v`-prefixed `para_config.txt` value, which GHCR does not carry.                                                                                       | `docker-tool.reusable.yml:214,216,236`; `atrium-alto-postprocess/.env.example`                                                                                                                                                   |
| **B4** | **The E2E's own skip path can only fail.** With `OPENROUTER_KEY` unset — every PR, fork and push run — the workflow falls back to `work/doc_json/4_nlp.json` (`e2e-pipeline-smoke.yml:241-244`), but `e2e_assert.py:49` asserts `enrichment` unconditionally. That block is owned exclusively by llm-enrich. The gate and the assertion contradict each other; this is the same "dark stage" class of defect #18 already fixed once, inverted.    | `e2e-pipeline-smoke.yml:241-244`, `tools/e2e/e2e_assert.py:49`, `document_schema.md` block-ownership table                                                                                                                       |
| **B5** | `llm-enrich`'s Dockerfile `api` stage (`FROM remote AS api`) is **never built or published** — `build-targets: '["remote","llm"]'` excludes it — yet compose references `…-api`.                                                                                                                                                                                                                                                                  | `atrium-llm-enrich/Dockerfile:79`, `.github/workflows/docker.yml`, `docker-compose.yaml:53`                                                                                                                                      |
| **B6** | All five composes bind-mount `./data:/data`, but `data/` exists in **no** repo. Docker creates the host directory root-owned; containers run as uid 10001 → the first `docker compose run` write fails.                                                                                                                                                                                                                                           | all `docker-compose.y*ml`; `useradd --create-home --uid 10001 atrium` in all five Dockerfiles                                                                                                                                    |
| **B7** | `nlp-enrich`'s GPU overlay header instructs `-f docker-compose.yml -f docker-compose.gpu.yml`; both files are `.yaml` in that repo, so copy-pasting either documented line fails. The hub's own `server.template.sh:63` hardcodes `.yml` too → GPU start-up is broken for **`nlp-enrich` and `llm-enrich`**.                                                                                                                                      | `atrium-nlp-enrich/docker-compose.gpu.yaml:2-3`; `docs/templates/skill/server.template.sh:63`                                                                                                                                    |
| **B8** | `alto-postprocess`'s API entrypoint runs `uvicorn.run(..., reload=True)` — a filesystem-watching reloader as the container's production process. The reloader also spawns a subprocess whose `sys.path[0]` is `/app`, not `/app/service`, which the `text_api:app` import string depends on.                                                                                                                                                      | `atrium-alto-postprocess/service/text_api.py:309-311`                                                                                                                                                                            |
| **B9** | E2E `pip install`s `alto-tools` from `refs/heads/master.zip` **inside the published image**, contradicting the commit pin in `setup/requirements.txt`. In other words the published alto image lacks a working `alto-tools` and the E2E patches it at runtime. E2E also overrides every image's `--entrypoint`, so no Dockerfile ENTRYPOINT is ever exercised anywhere in CI.                                                                     | `e2e-pipeline-smoke.yml:166` and the five `--entrypoint` overrides; `atrium-alto-postprocess/setup/requirements.txt` (`alto-tools @ git+…@1f4f01e5…`)                                                                            |

### 2.2 Enforcement gaps — why drift returns

| #       | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Evidence                                                                                                                                     |
|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **E1**  | **The hub's self-check does not check the hub.** `hub-self-check.yml:39` calls the reusable by local path, documented as validating "the ref being pushed". But `workflow-lint.reusable.yml:62-66` then checks the hub out at `ref: ${{ inputs.hub-ref }}` (default `v1`) and line 88 runs `python hub-repo/tools/ci/workflow_lint.py`. **A change to the policy linter is never the code that runs on its own PR** — and `hub-self-check.yml` passes no `hub-ref`, so it cannot be overridden from the caller.                                                                                                                         | `hub-self-check.yml:39`; `workflow-lint.reusable.yml:62-66,88`                                                                               |
| **E2**  | `tools/ci/workflow_lint.py` has **zero tests** — six checks, ~250 lines of policy logic. By contrast `check_version.py` (140 lines) has 16 tests and `para_licenses.py` has 36: the tested surface is the small stuff. The linter also **crashes** (`TypeError`) rather than reporting if a caller uses the legal shorthand `permissions: read-all`, because the permission merge assumes a mapping.                                                                                                                                                                                                                                    | `tests/` contains only `test_check_version.py`; `granted = {**(doc.get("permissions") or {}), **(job.get("permissions") or {})}`             |
| **E3**  | The linter has **no rule** for: `timeout-minutes`, `concurrency`, workflow-level `permissions`, the action-version floor, required-input presence (`skill-validate.reusable.yml` declares `client-script: required: true`), undeclared **secrets** (only `secrets: inherit` is caught), the expression-into-`run:` doctrine the hub states in its own comments, or the "keep PR triggers identical to push" policy repeated across six caller templates. Every one of those is a parse-time or policy failure the linter was built to prevent.                                                                                          | `workflow_lint.py` checks: parse · pins · `secrets: inherit` · duplicate names · template inputs · caller/callee permissions                 |
| **E4**  | The lint glob (`.github/workflows/*.yml` + `docs/templates/workflows/*.yml`) misses `*.yaml`, `.github/dependabot.yml`, and `docs/templates/skill/*.yml`. That last omission is load-bearing: a **second, unlinted `skill-validate.caller.example.yml` pinned `@test`** sits beside the linted `@v1` twin.                                                                                                                                                                                                                                                                                                                              | `workflow_files()`; `docs/templates/skill/skill-validate.caller.example.yml` vs `docs/templates/workflows/skill-validate.caller.example.yml` |
| **E5**  | `all-repos-smoke.yml` (added 2026-08-01) has **no `timeout-minutes`, no `concurrency`, no `permissions`**; its `name:` is "Reusable E2E Pipeline Smoke (JSON Matrix)" although it is neither reusable-consumed nor E2E nor JSON — it runs each repo's pytest suite; it **omits `llm-enrich`** (4 of 5 in a statically-echoed matrix); it runs `pytest tests/` with **no `-m "not slow"`**, i.e. the model/network lane on a GPU-less hosted runner, against the hub's own CONTRIBUTING policy; it duplicates each repo's `docker.yml` test job; and it shares both the exact cron **and** the push trigger of `e2e-pipeline-smoke.yml`. | `.github/workflows/all-repos-smoke.yml:1,6-9,20,52-54`                                                                                       |
| **E6**  | `docker-tool.reusable.yml` has no workflow-level `permissions`, and its `test` and `docker-build-smoke` jobs have **no permissions block at all** → they run at the repository default on the jobs that execute arbitrary test and build code. Same for `security.reusable.yml`'s `version-check`. The linter's rule is *"an explicit block that omits a scope fails, but no block at all is fine"* — correct for callers, and exactly why these slip through.                                                                                                                                                                          | `docker-tool.reusable.yml`, `security.reusable.yml`; `check_template_permissions`                                                            |
| **E7**  | **Two contradictory lint gates run on every PR.** `docker-tool.reusable.yml` runs `ruff check .` with `continue-on-error: true` (advisory) while `pre-commit.reusable.yml` runs the same ruff blocking. One of them is wasted CI time and a misleading signal.                                                                                                                                                                                                                                                                                                                                                                          | both reusables                                                                                                                               |
| **E8**  | `skill-validate.reusable.yml` embeds a 57-line Python module (`skill_contract.py`) as a heredoc inside YAML — not linted by ruff, not covered by any test, not reusable by anything else. Its steps 2 and 3 also interpolate `${{ inputs.* }}` directly into Python source and into `run:`, violating the doctrine stated in `docker-tool.reusable.yml`'s own comments.                                                                                                                                                                                                                                                                 | `skill-validate.reusable.yml`                                                                                                                |
| **E9**  | The four largest canonical shared files have **zero tests**: `atrium_document.py` (776 lines), `atrium_paradata.py` (613), `atrium_service.py` (171); and `atrium_document.schema.json` is never validated against the committed `fixtures/atrium_document.example.json`. `para-drift` enforces that all five copies are byte-identical; nothing enforces that the bytes are correct.                                                                                                                                                                                                                                                   | `docs/templates/shared/`; `fixtures/atrium_document.example.json`                                                                            |
| **E10** | Caller hygiene: inputs that merely restate hub defaults (`hf-model-cache: false`, `build-targets: '["base"]'`, `requirements: "requirements.txt requirements-test.txt"`, `citation-path: CITATION.cff`); a dead `id-token: write` grant in nlp/llm `security.yml` (the reusable has no OIDC step); **`translator` and `page-classification` cannot manually re-scan at all** — the hub gates the Trivy job on `schedule \|\| workflow_dispatch` and neither declares `workflow_dispatch`, so a weekly cron is their only path; and permissions are declared at workflow level in `translator` but job level in the other four.          | 5 × `docker.yml`, 5 × `security.yml`; `security.reusable.yml:75`                                                                             |
| **E11** | **No `workflow_dispatch` on any hub check** (`hub-self-check`, `codeql`, `pre-commit`, both smokes) → no manual re-run path; a nightly that failed on a missing secret cannot be re-run once the secret exists. No reusable declares `outputs`, so callers get pass/fail only — no digest, version or report passthrough.                                                                                                                                                                                                                                                                                                               | all hub workflows                                                                                                                            |

### 2.3 Duplication still uncollapsed

Four workflow families, ~1,020 lines, no hub reusable:

| Family                | Lines   | Repos | Drift already present |
|-----------------------|---------|-------|-----------------------|
| `release.yml`         | **429** | 5     | see D2                |
| `scheduled-smoke.yml` | **378** | 5     | see D1                |
| `gpu-inference.yml`   | **183** | 3     | see D3                |
| `shellcheck.yml`      | 33      | 1     | see D4                |

| #      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Evidence                                                                                                 |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **D1** | `scheduled-smoke.yml`: five implementations, **three semantics** — `pytest tests/` (translator, the *whole* suite), `-m slow` (page-classification, alto), `-m slow` + exit-5 tolerance (nlp, llm). Translator is the ecosystem's only **Python 3.12** job (everything else, hub included, is 3.11). Two issue-label sets, two cache mechanisms, `concurrency` in page-classification only, two permission levels. nlp and llm are **byte-identical** (`md5 3196b76f…`) and **llm's copy carries nlp's header** — it documents LINDAT/UDPipe/NameTag and `requirements_llm.txt`, none of which are llm-enrich's concerns.                                    | 5 × `scheduled-smoke.yml`                                                                                |
| **D2** | `release.yml`: page-classification's ~60-line AST bundle-closure checker — dependency-free, repo-agnostic, derives first-party modules from `os.listdir(".")` — exists in **1 of 5**. translator and alto ship release zips with **no closure check at all**, and alto's `cp -r setup/ service/ … 2>/dev/null \|\| true` silently swallows a failed copy. `fetch-depth: 0` and `make_latest: true` in 2 of 5. translator's tag glob is `'v*.*.*'` vs `'v*'` elsewhere. nlp's header still says `uses: …@test`, left behind by the pin migration. **No repo sets up Python** for the `check_version.py` step — it relies on the runner's ambient interpreter. | 5 × `release.yml`                                                                                        |
| **D3** | `gpu-inference.yml`: nlp and llm **byte-identical** (`md5 2f9313c3…`); page-classification a separate implementation with **no `setup-python` step at all** and no exit-5 tolerance. Present in page-classification, nlp and llm — **and the two that lack it are the wrong two**: alto owns the ecosystem's only real GPU test (`tests/test_gpu_concurrency.py`, slow-marked) and has no GPU workflow, while nlp and llm each have a GPU workflow that can collect **zero** tests.                                                                                                                                                                          | 3 × `gpu-inference.yml`; `atrium-alto-postprocess/tests/test_gpu_concurrency.py`                         |
| **D4** | `shellcheck` exists as a workflow in `nlp-enrich` only — 7 scripts, double-covered by workflow *and* pre-commit hook. page-classification has **8** shell scripts, no workflow, and a hook regex `^(data_scripts\|setup\|supplementary/scripts)/.*\.sh$` that misses `result/stats/{dataset_stat,unused}.sh` → **2 scripts linted by nothing**. Three severity configs for one tool (`-e SC1091 -e SC2148`, `-e SC1091`, bare).                                                                                                                                                                                                                              | `atrium-nlp-enrich/.github/workflows/shellcheck.yml`; 5 × `.pre-commit-config.yaml`                      |
| **D5** | Hub-internal copy-paste: seven near-identical `diff -u` steps in `para-drift.reusable.yml` over a hardcoded file list (a repo lacking `service/` or `tests/` fails on *layout*, not on drift); four near-identical checkout+chmod pairs in `e2e-pipeline-smoke.yml`; the permission-capping paragraph verbatim in six files; five near-identical checkout + setup-python + pip prologues with **no composite action** (`.github/actions/` does not exist).                                                                                                                                                                                                   | those files                                                                                              |
| **D6** | Config-layer drift: ruff `line-length` 120/120/**100/100**/120; `ruff-format` hook in 3 of 5; **llm-enrich's ruff pinned `v0.4.4`** against `v0.15.18` elsewhere — in the repo whose B008 finding motivated making lint blocking in the first place; shellcheck hook `v0.10.0` vs `v0.11.0`; `pythonpath = .` in 2 of 5 `pytest.ini`; `.coveragerc` `fail_under` **28/30/42/50/70**. **No `pre-commit` dependabot ecosystem in any repo**, which is precisely how a 2024-era linter rev survived.                                                                                                                                                            | 5 × `ruff.toml`, `.pre-commit-config.yaml`, `pytest.ini`, `.coveragerc`, `dependabot.yml`                |
| **D7** | translator's `pytest.ini` `env =` block (which disables retry backoff) is **inert** — `pytest-env` is installed nowhere in the repo, and pytest only warns on unknown ini keys, so CI tests take real retry sleeps. nlp-enrich selects ruff `"B"` with **no `extend-immutable-calls`** while `service/api.py` has 16 call-in-default sites and only 3 `# noqa: B008` — under-suppressed against a blocking gate. llm-enrich and alto both solved this in `ruff.toml`.                                                                                                                                                                                        | `atrium-translator/pytest.ini`, `requirements-test.txt`; `atrium-nlp-enrich/ruff.toml`, `service/api.py` |

### 2.4 Branch policy, schedules and CI spend

| #      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Evidence                                                                                                                                                                 |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **S1** | **Zero of ~20 branches are protected**, in any of the six repositories. Not just the hub.                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `list_branches` on all six: every entry `"protected": false`                                                                                                             |
| **S2** | `test` sits at the **exact same SHA** as the default branch in all six repos, and every workflow triggers on both → **each push runs the whole suite twice**. Hub run history shows identical workflows firing on `main` and `test` minutes apart.                                                                                                                                                                                                                                                                                                                     | hub `main`/`test` both `db5a00f`; pc `test`/`vit` both `2ed7ba1`; translator `master`/`test` both `6a2c0c5`; nlp both `d616384`; llm both `a096c86`; alto both `617a3fa` |
| **S3** | Stale branches still exist and are still in trigger lists: page-classification's `master` (`1e80e7a`, behind) plus `clip`; translator carries a stale `main` (`e6c35ee`). page-classification fans out to `[test, vit, clip, master]` across seven files in **three different orderings/quotings**, including a double-space typo in `security.yml`.                                                                                                                                                                                                                   | `list_branches`; pc/translator `.github/workflows/*`                                                                                                                     |
| **S4** | **8 of 12 active weekly jobs land inside Monday 05:00–06:00 UTC.** Three-way collision at `0 5 * * 1`; two-way at `0 4 * * 1`, `0 6 * * 1` and the daily `0 3 * * *`. CodeQL *was* deliberately staggered 15 minutes apart across the ecosystem — and the comment saying so is in all five files — but the stagger was **never extended to `security.yml`**, which sits on round hours and now lands on two of the five CodeQL slots. Both hub smokes share `0 2 */3 * *`. The published `codeql.caller.example.yml` also collides with the hub's own pre-commit slot. | all `cron:` lines across six repos + `docs/templates/workflows/`                                                                                                         |
| **S5** | translator, nlp-enrich and llm-enrich have **0** `@pytest.mark.slow` tests, so their nightly lanes are permanent no-ops — nlp/llm held green by the exit-5 shim, translator by running the fast suite a second time. page-classification has 3 marks in 2 files; alto has 6 in 3.                                                                                                                                                                                                                                                                                      | `grep -rc "mark\.slow" */tests`                                                                                                                                          |
| **S6** | Dead fixture weight: five ALTO + CSV fixture pairs exist, `E2E_DOC` is hardcoded to `CTX000000003`, and the other four (~730 KB, including two large real scans) are referenced by no workflow, script or test. There is no matrix over `E2E_DOC`.                                                                                                                                                                                                                                                                                                                     | `fixtures/e2e/`; `e2e-pipeline-smoke.yml` `env:`                                                                                                                         |

### 2.5 Supply chain and image hygiene

| #       | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Evidence                                                                                   |
|---------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **H1**  | **No hash pinning and no lockfile anywhere** — 30 `requirements*.txt` across six repos; no `uv.lock`, `poetry.lock`, `pyproject.toml` or pip-compile output. **8 of the 30 are installed by nothing.** Pinning discipline ranges from fully exact (translator base) to fully unpinned (`llm-enrich/requirements.txt`, `alto/service/requirements.txt`, `nlp-enrich/requirements.txt`).                                                                                                                                                                                                                             | per-repo requirements inventory                                                            |
| **H2**  | Unpinned third-party HEAD baked into images: `flexiconv @ git+https://github.com/ufal/flexiconv.git` with **no ref** in nlp and llm (byte-identical files, and nlp's is installed by no Dockerfile stage at all), and alto's `git clone --filter=blob:none --depth 1 FreeOCR-AI/layoutreader` with **no commit pin**. Only `alto-tools@1f4f01e5…` is commit-pinned. Several hub steps also `pip install` unpinned tooling (`gh2md`, `pre-commit`, `pyyaml`, `pytest pytest-cov ruff`).                                                                                                                             | `requirements_flexiconv.txt` ×2; `atrium-alto-postprocess/Dockerfile:42-48`; hub reusables |
| **H3**  | alto downloads **~1.2 GB of weights at build time** from `…/resolve/main` — no revision pin, no checksum (only `test -s`) — and saves them as `lid.176.bin` although the artefact is `facebook/fasttext-language-identification/model.bin`, not the 126 MB fastText `lid.176.bin`. Misleading name, unpinned source, dominant size layer, and the only build-time weight bake in the suite (everyone else downloads at runtime into `hf-cache`).                                                                                                                                                                   | `atrium-alto-postprocess/Dockerfile:57-70`                                                 |
| **H4**  | Production images carry test and research dependencies. alto installs `setup/requirements-sweep.txt` (optuna, SALib, scikit-learn, matplotlib) **against that file's own header** — *"NOT needed by the production pipeline or by the test suite"* — plus pytest; page-classification installs `requirements-test.txt`; `build-essential g++` is never removed anywhere; and nlp/llm derived stages each repeat `chown -R /app`, duplicating the entire source tree once per stage.                                                                                                                                | 4 Dockerfiles                                                                              |
| **H5**  | `.dockerignore` misses large trees: `supplementary/` (19 MB, page-classification), `ker_data/` (26 MB, nlp), `tests/` + `agent_dev_logs/` (translator).                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 5 × `.dockerignore`                                                                        |
| **H6**  | No `docker` and no `pre-commit` dependabot ecosystem in any repo → `python:3.11-slim` is never auto-bumped in five Dockerfiles, and hook revs rot (D6). The hub's `dependabot.yml` header claims *"this repo ships no Python package manifest"* — `tools/e2e/requirements.txt` exists, pins `pillow>=12.3.0`, and is covered by nothing.                                                                                                                                                                                                                                                                           | 6 × `dependabot.yml`                                                                       |
| **H7**  | Trivy policy is **half-decided**, and the current-state doc overstates it in the other direction. A tag build already fails on fixable CRITICAL (`docker-tool.reusable.yml:301-308`, `exit-code: "1"`). The pre-publish SARIF scan (`:273`) and the periodic re-scan (`security.reusable.yml:108`) are `exit-code: "0"`. **HIGH and unfixable-CRITICAL have no policy.** `pip-audit` has been on the roadmap since June, appears in `scheduled-smoke.caller.example.yml` as `pip-audit \|\| true`, and gates nothing.                                                                                              | those three files                                                                          |
| **H8**  | No multi-arch: no `--platform`, no `platforms:`, no bake file — all images implicitly `linux/amd64`. No `cache_from:` in any compose file, so a developer's `docker compose build` shares no cache with CI.                                                                                                                                                                                                                                                                                                                                                                                                        | grep across six repos                                                                      |
| **H9**  | nlp and llm `llm` stages hardcode the **CPU** torch index and expose no `TORCH_INDEX_URL` ARG → their "GPU" stages cannot be built for CUDA without editing the Dockerfile. page-classification's ARG documents `cu126`; alto's comment says `cu121`. The reusable exposes a `torch-index-url` input and **no caller passes it**. nlp's `llm` stage also `sed`-deletes its own `torch==` pin at build time so vllm can resolve — the only requirements mutation in the ecosystem.                                                                                                                                  | 4 Dockerfiles; 5 × `docker.yml`; `atrium-nlp-enrich/Dockerfile:59-67`                      |
| **H10** | **No `HEALTHCHECK` in any Dockerfile and no `healthcheck:` in any compose file** — while the stated requirement (motyc, 2026-06-12) is that "we need to be able to run the individual containers with the tools reachable via API". Without a readiness signal there is nothing for an orchestrator to wait on. Also: llm's compose defaults `ALLOWED_ORIGINS: *` (the only wildcard in the suite); two `extends` syntaxes (scalar vs long form); `capabilities: ["gpu"]` vs `[gpu]`; GPU overlays skip the `api` service in nlp and alto; no `restart:` or `networks:` anywhere except the Label Studio side-car. | all Dockerfiles / compose files                                                            |
| **H11** | `requirements_digital.txt` (docling, pymupdf — with an in-file AGPL-3.0 warning) and `requirements_docmd.txt` exist in llm-enrich and are installed by **no** Dockerfile stage and no workflow, although they are the dependency set for the PDF/DOCX→JSON converter that `project_state_0208.md` names as bottleneck #1 ([llm-enrich#18](https://github.com/ufal/atrium-llm-enrich/issues/18)).                                                                                                                                                                                                                   | `atrium-llm-enrich/requirements_digital.txt`, `requirements_docmd.txt`                     |

### 2.6 Correctness and documentation rot

Cheap to fix, and each one currently misroutes a reader or a script.

| #      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **R1** | `docs/templates/workflows/update_issues.sh:92` unconditionally `export`s an **elided placeholder** token (`github_pat_…` containing a literal `...`, ~24 chars where a real PAT is 80+). Two consequences: the `if [[ -z "${GITHUB_ACCESS_TOKEN:-}" ]]` guard on line 94 is dead code, and a correctly-set `GITHUB_ACCESS_TOKEN` in the caller's environment is **overridden**, so the script can never authenticate — it fails with an opaque GitHub auth error instead of the helpful message it was written to print. It also discloses a 7-character prefix and 3-character suffix. *Not a usable credential:* the single commit that introduced this file already carried the ellipsis, and no full-length PAT literal appears in the 50 commits reachable from this shallow clone. **Worth confirming against GitHub's secret-scanning alerts**, which can see past the shallow boundary. `issue-log-refresh.yml`'s header nevertheless says this script was replaced *because* it "carried a personal token inline" — so the stated remediation and the committed file disagree. |
| **R2** | `agent_skill_strategy.md` (5 places) and both scripts' own docstrings cite `tools/skill_drift_check.py` / `tools/skill_ify.py`; the files live in `docs/templates/skill/`. The hub *does* have a `tools/` directory, so the paths look plausible and fail only when run. Flagged as P1 in `project_state_3007.md` and still open.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **R3** | `document_schema.md` cites `tests/test_document_originators.py` and `scripts/revendor_shared.sh` — **neither exists anywhere in the repo**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **R4** | `fixtures/e2e/README.md` is truncated mid-sentence; claims the CSV has "37 columns" (the header has 40); and claims *"All tool repos are checked out at the same ref (default `test`)"* when `e2e-pipeline-smoke.yml` passes **no `ref:` at all** for any tool repo (only the hub fixtures checkout is pinned, at `v1`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **R5** | `security.reusable.yml` contradicts itself three times in 130 lines: its docstring advertises an SBOM job that its own §3 records as removed; it says *"identical across the four tool repos"* (there are five); and it says *"ideally commit SHAs at adoption time"* eighty lines above *"NOW SHA-PINNED … the 'ideally' above is done"*.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **R6** | Caller-job counts disagree across the repo: `workflow_lint.py` says 37, `hub-self-check.yml` says 42; the actual figure is **38** (35 cross-repo + 3 hub-local).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **R7** | Two implementations of "refresh issue logs" with different flags: `issue-log-refresh.yml` (`--multiple-files --no-prs`, repository hardcoded rather than `github.repository`) vs `update_issues.sh` (`--no-closed-issues --no-prs --multiple-files`, plus R1 and a hardcoded `$HOME/PycharmProjects/alto` base dir).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **R8** | `docker-tool.reusable.yml:87` and page-classification's `docker.yml` both instruct maintainers to keep `PC_REVISION` in `e2e-pipeline-smoke.yml` in step — *"Bump all three together"* — but **that third leg no longer exists**; grep finds only the comments.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

---

## 3. Cross-cutting decisions to settle

These are the calls that several waves depend on. Each is a decision, not a task.

### 3.1 Image naming: adopt the CI form

Two schemes are in use (B2). **Recommendation: standardise on the CI form,**
`ghcr.io/ufal/atrium-<tool>-<target>:<version>`, and fix compose to match — not the reverse. Reasons: it is
what is actually published, what the GHCR packages are named, what `e2e-pipeline-smoke.yml` pulls, and what
nlp-enrich's own `docker.yml` comment documents. Changing the publisher instead would orphan every image
already in the registry.

### 3.2 Tag channels

| Channel                 | Published on                            | Meaning                              |
|-------------------------|-----------------------------------------|--------------------------------------|
| `<semver>`              | `v*` tag                                | the immutable release                |
| `latest`                | `v*` tag                                | most recent release                  |
| `sha-<sha>`             | tag, and (proposed) default-branch push | exact commit                         |
| **`edge`** *(proposed)* | default-branch push                     | current HEAD; **no support promise** |

Also fix the `v`-prefix inconsistency (B3): either publish `type=semver,pattern=v{{version}}` or derive
`ATRIUM_RUNNER_IMAGE` from the metadata action's output instead of `github.ref_name`. The second is
preferable — one source of truth rather than two conventions kept in step by hand.

### 3.3 Vendored versus referenced shared code

The existing split is right and should be stated as policy rather than rediscovered:

- **Vendored + `para-drift`-enforced** for anything a *release* depends on (`check_version.py`, and the
  bundle-closure checker proposed in W4). A release gate must not depend on a cross-repo `uses:` resolving
  at tag-push time.
- **Referenced from the hub** for everything else (`workflow_lint.py` is checked out, deliberately not
  vendored — a copy in six places would need its own parity step, and adding that step for a file the
  repos do not yet have fails `para-drift` in all five on their next push).

### 3.4 The `@v1` pin: an accepted trade-off, recorded

All 35 cross-repo references resolve to `@v1`, a **force-pushable tag**, and `workflow_lint.py`'s
`WRITE_SCOPED` allowlist deliberately exempts reusable-workflow refs from the SHA-pin rule. So the
ecosystem's single largest dependency is also its least-pinned one.

This is the right trade-off — "one edit updates all" is the reason the architecture exists — but it should
be explicit, with two guards: `v1` moves only to a commit that passed `Hub Self-Check`, and every move is
also recorded as an immutable `v1.x.y` tag so there is an audit trail of what `v1` pointed at. A linter rule
asserting that every caller ref is exactly `@v1` (E3) closes the remaining hole.

### 3.5 Branch model: one integration branch

`test` is a byte-identical mirror of the default branch in all six repos (S2), so it currently costs a full
duplicate CI run per push and protects nothing. **Recommendation:** the default branch becomes the only
integration branch; `test` is dropped from all trigger lists; the default branch gets protection in all six
repos (required review, required status checks, no force-push); stale `master` in page-classification and
stale `main` in translator are archived or deleted.

If `test` is to be kept, it must stop mirroring default and be used only for the pre-release validation
role `docker_gha.md` already describes — validating a hub change before `v1` moves. Either outcome is fine;
the current state is the one that isn't.

### 3.6 GPU: stop making it a single-supplier dependency

Two independent changes, neither of which needs a runner to land:

1. **Split the marker.** `slow` = network/integration, runnable on `ubuntu-latest` **today**. `gpu` = genuinely
   needs CUDA. The genuine network tests in translator, nlp and llm (LINDAT `call_udpipe`/`call_nametag`,
   llm-enrich's OpenRouter round-trip and AMCR OAI-PMH harvest) then have somewhere real to run, and three
   vacuous nightly lanes (S5) become substantive.
2. **Parameterise the runner.** A `runner-labels` input on the GPU reusable means a self-hosted runner, a
   GitHub-hosted GPU runner, or a Metacentrum/cluster job all satisfy it. #40 stops being blocked on one
   person.

---

## 4. Waves

Sequencing is the argument of this document, so each wave states why it is where it is.

### W1 — Make the guardrails real *(hub only)*

**Why first.** E1–E5 are the reason the 2026-07-30 policy regressed within 48 hours. Collapsing another
~1,000 lines into the hub before the linter can hold the result repeats that at five times the blast radius.
This wave touches no tool repo, so it is also the cheapest to review.

- Close the self-validation hole (**E1**): have `hub-self-check.yml` pass `hub-ref: ${{ github.sha }}`, or
  run the linter from the local checkout, so a linter change is exercised by its own PR.
- Add tests for `workflow_lint.py` and fix the `permissions: read-all` crash (**E2**), following the style
  of `tests/test_check_version.py` — including at least one test that deliberately breaks a single check to
  prove the others don't mask it.
- Add the missing rules (**E3**): `timeout-minutes`, `concurrency`, workflow-level `permissions`,
  action-version floor, required inputs, undeclared secrets, expression-into-`run:`, PR/push trigger parity,
  and caller-ref shape (`@v1` exactly).
- Widen the lint glob to `*.yaml`, `docs/templates/skill/*.yml` and `.github/dependabot.yml` (**E4**) — then
  reconcile or delete the duplicate `@test`-pinned caller example it surfaces.
- Fix `all-repos-smoke.yml` (**E5**): rename it to what it is, add `llm-enrich`, add `-m "not slow"`, add the
  three missing policy blocks, move it off the E2E cron slot — **and decide whether it earns its keep**, given
  that it re-runs work every repo's own `docker.yml` test job already does.
- Grant explicit least privilege to the reusable jobs currently running at repository default (**E6**);
  resolve the double lint gate (**E7**); add `workflow_dispatch` to every hub check (**E11**).
- Publish the cron allocation table (**S4**) and fix the `security.yml` slots the CodeQL stagger skipped.
- Begin tests for `atrium_document.py` / `atrium_paradata.py` / `atrium_service.py`, and validate the
  committed fixture against `atrium_document.schema.json` (**E9**).
- Put §3.5 to @stranak as a concrete repository-settings change (**S1–S3**), and fix the doc rot in
  **R1–R8** while the files are open.

**Acceptance.** `workflow_lint.py` fails on a deliberately-broken fixture for each new rule; the linter's own
test suite runs in `Hub Self-Check`; a PR that edits the linter is checked by the edited linter;
`all-repos-smoke.yml` reports its real name and covers five repos.
**Owner:** @K4TEL · **Blast radius:** hub only.

### W2 — The live breakages *(5 tool repos, small diffs)*

**Why second.** These are the smallest diffs with the most visible effect: two API images that cannot start,
six compose references nobody can pull, provenance naming a non-existent tag, and an E2E path that can only
fail. None of them depends on the later waves.

B1–B9, plus the §3.1 naming decision and the §3.2 `v`-prefix fix. Add `data/.gitkeep` (B6); drop
`reload=True` (B8); tighten the wildcard CORS default (H10, partial); normalise every compose file to `.yml`
(B7), which also repairs `server.template.sh`.

**Acceptance.** `docker compose --profile api up` reaches a serving state in all five repos from a clean
checkout; every `image:` in every compose file is pullable at the current release; a fresh tag's paradata
`docker_image` matches a tag that exists in GHCR; the E2E passes on a run with **no** `OPENROUTER_KEY`.
**Owner:** @K4TEL, with @rharasim reviewing the compose surface · **Blast radius:** 5 tool repos.

### W3 — An `:edge` channel, so CI can test HEAD *(hub + 5 callers)*

**Why third.** Depends on W2's naming decision, and unblocks W4: the collapsed workflows can then be
validated against edge images instead of waiting for a release tag — the workaround the 2026-08-01 E2E
rewrite had to improvise.

- Publish `type=raw,value=edge` + `type=sha` on default-branch pushes; extend the existing
  digest-addressed scan to edge; document that `edge` carries no support promise.
- Give both smoke workflows an `image-channel` input — `edge` on push/schedule, `latest` for release
  verification.
- Parameterise the E2E's hardcoded surface: `E2E_DOC` (**S6** — five fixtures exist, one is used), the five
  `:latest` refs, the missing `tool-ref` its own README already claims exists (**R4**), the
  page-classification model, and the 25 inline nlp config values.
- With an edge image carrying a working `alto-tools`, **B9** dissolves: drop the runtime zip install and add
  one lane that runs the images' real ENTRYPOINTs instead of overriding them.

**Acceptance.** A default-branch push produces `:edge`; the nightly E2E runs against `:edge` and a release
tag re-runs it against `:latest`; no CI step installs a package into a published image.
**Owner:** @K4TEL · **Blast radius:** hub + 5 callers.

### W4 — Finish the DRY collapse *(hub + 5 tool repos)*

**Why fourth.** The largest diff, hence last among the structural waves — and only safe once W1's rules can
hold the result and W3 can validate it without a release.

- New `release.reusable.yml`, `scheduled-smoke.reusable.yml`, `gpu-inference.reusable.yml`; fold shellcheck
  in (**D1–D4**). Reconcile the three nightly semantics into one with inputs, not three implementations.
- Promote the AST bundle-closure checker to `docs/templates/shared/check_bundle_closure.py` — **vendored per
  repo and held byte-identical by `para-drift`**, per §3.3, so translator and alto stop shipping unchecked
  bundles (**D2**).
- Caller hygiene (**E10**); lift `skill_contract.py` out of YAML into `tools/ci/` where ruff and tests reach
  it (**E8**); consider a composite action for the five duplicated prologues (**D5**).
- Implement §3.6: marker split, then mark the genuine network tests in translator/nlp/llm (**S5**);
  `runner-labels` on the GPU reusable; give alto a GPU caller, since it owns the only real GPU test (**D3**).
- Align the config layer (**D6**, **D7**) — including llm-enrich's `v0.4.4` ruff and translator's inert
  `pytest-env` block.

**Acceptance.** ~1,000 lines removed; the three new reusables have caller examples *and* linter coverage; a
release in every repo runs the same closure check; `pytest -m slow` collects >0 tests in all five repos on a
hosted runner.
**Owner:** @K4TEL · **Blast radius:** hub + 5 tool repos — stage one repo at a time, translator first.

### W5 — Supply chain and image hygiene *(5 tool repos)*

- Pin every VCS and clone ref to a commit, and every hub `pip install` of tooling (**H2**); pin the alto
  weight fetch to a revision plus checksum and rename it honestly (**H3**).
- Add `docker` and `pre-commit` dependabot ecosystems; cover `tools/e2e/requirements.txt`; correct the
  hub `dependabot.yml` header (**H6**).
- Make `pip-audit` a real gate rather than `|| true`, and settle the remaining Trivy policy (**H7**).
  **Recommendation:** keep fixable-CRITICAL blocking on tags; add HIGH as report-only with a review cadence;
  leave unfixable non-blocking, since an unpatchable CVE should not be able to wedge a release.
- Add an image-size budget that fails beyond a per-repo ceiling, and split builder/runtime so test and sweep
  dependencies leave the production images (**H4**, **H5**).
- Phase in hash-pinned lockfiles (`pip-compile` per manifest), piloting translator as the lightest (**H1**),
  and retire or wire up the 8 requirements files nothing installs.
- **arm64: defer, with the rationale recorded** (**H8**) — the torch/CUDA-bearing images have no arm64 story,
  the runners are amd64, and a second architecture would roughly double build time for no current consumer.
  Revisit if an Apple-silicon or ARM-server consumer appears.

**Acceptance.** No floating VCS ref or unpinned weight fetch in any image; `pip-audit` fails on a known-bad
pin; image sizes recorded with a ceiling per repo.
**Owner:** @K4TEL · **Blast radius:** 5 tool repos, independent of each other.

### W6 — Convergence and new targets *(5 tool repos + hub)*

- The compose convention spec, and a `HEALTHCHECK` + `/health` readiness contract wired into
  `api-contract.reusable.yml` (**H10**) — so "reachable via API", the requirement this issue was opened for,
  becomes a tested property rather than a claim.
- Extend GPU overlays to the `api` services; add `TORCH_INDEX_URL` to nlp/llm and settle one CUDA version
  across page-classification and alto (**H9**).
- Plan the `digital` build target and its publish name for llm-enrich's PDF/DOCX→JSON converter **before the
  converter lands** (**H11**), so it arrives with CI on day one rather than acquiring it later.
- Close page-classification's shellcheck gap (**D4**) and add a path-citation check to the linter so **R2/R3**
  cannot recur.

**Acceptance.** `docker compose up` reports healthy for every API profile; the contract test asserts
`/health` against a container, not just an imported app; a `digital` image publishes on the next llm-enrich
tag.
**Owner:** @K4TEL, with @rharasim on the orchestration surface · **Blast radius:** 5 tool repos + hub.

---

## 5. Dependency graph

```
W1 (guardrails, hub only) ──┬─→ W4 (DRY collapse) ──→ W6 (convergence, new targets)
                            │        ↑
W2 (live breakages) ────────┴─→ W3 (:edge channel)
                            │
                            └─→ W5 (supply chain, hygiene)   [independent of W3/W4]
```

W2 and W1 can proceed in parallel — W2 is tool-repo work, W1 is hub work. W5 depends only on W2. W4 wants
both W1 (to hold the result) and W3 (to validate it without cutting a release).

## 6. Out of scope, and why

- **An umbrella orchestration compose.** Ruled out on 2026-06-12 (motyc): *"I believe we won't need any
  overall Docker wrapper, i.e. we need to be able to run the individual containers with the tools reachable
  via API."* W6's healthcheck/`/health` work serves that requirement instead. `plan_repo_review.md` still
  references a planned `compose/docker-compose.pipeline.yml`; that reference should be removed.
- **gitleaks.** Dropped on 2026-07-30 after going unadopted; the blocker was policy, not tooling, and
  GitHub-native secret scanning with push protection covers the same ground without an org-owned
  `GITLEAKS_LICENSE`. **R1** is a reason to *verify* native scanning is enabled, not to reopen gitleaks.
- **Branch protection and the GPU runner themselves** — repository settings and external infrastructure,
  tracked in [#40](https://github.com/ufal/atrium-project/issues/40). This roadmap supplies the concrete
  proposal (§3.5) and removes the GPU single-supplier dependency (§3.6), but cannot land either.
