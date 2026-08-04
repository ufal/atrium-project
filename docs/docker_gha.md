# ATRIUM GitHub Actions Strategy & Integration Report

> **Status:** Active Document (Updated: August 2026)
> **Scope:** `atrium-translator`, `atrium-nlp-enrich`, `atrium-page-classification`, `atrium-alto-postprocess`,
> `atrium-llm-enrich`, and `atrium-project` (templates).
>
> This document is the **current-state reference** for the ATRIUM GitHub Actions automation: what is
> deployed, what conventions hold, and what the version floor is. It is cited from all five tool repos.
>
> 📍 **The forward plan lives in [`docker_gha_roadmap.md`](docker_gha_roadmap.md)** — findings register,
> cross-cutting decisions, and the W1–W6 wave sequence. Keep planning material there; keep this file
> describing what is true today.

## 1. Current Deployment Status: Developed Workflows

The baseline CI/CD infrastructure has been distributed and localized across the five tool
repositories. Standardized configuration files (`ruff.toml`, `.coveragerc`, `dependabot.yml`,
`.pre-commit-config.yaml`) are present in every repository, ensuring localized control over quality
thresholds.

### Standardized Baselines (Active in All Repositories)

* **Automated Testing:** Fast suites run via `pytest -m "not slow"` with coverage reporting on push/PR.
* **Code Linting:** pre-commit runs in CI in every repo and is **blocking** — settled 2026-07-30. Note that
`docker-tool.reusable.yml` *also* runs `ruff check .` with `continue-on-error: true`; that advisory copy is
redundant against the blocking gate and is queued for removal (roadmap **E7**).
* **Dependency Management:** Weekly `pip` and GitHub Action updates via Dependabot. **Not covered:** the
`docker` and `pre-commit` ecosystems, in any repo (roadmap **H6**) — so base images and hook revisions do
not auto-update.
* **Docker Operations:** Docker build smoke tests trigger on Pull Requests. Full Docker builds and pushes to
the GitHub Container Registry (GHCR) trigger on version tags (`v*`) and published releases — **and only
there**, so CI can never exercise an image built from the current default branch (roadmap **W3**).
* **Version Syncing:** `CITATION.cff` files are synced with internal `para_config` versions across the board.
* **Paradata Drift Guard:** Every repo calls `para-drift.reusable.yml@v1` to diff its local canonical shared
files against the hub copies. Parity currently holds byte-identically in all five repos. Note this enforces
that the copies are *identical*, not that they are *correct* — the largest canonicals have no tests
(roadmap **E9**).

### Reusable Templates (`atrium-project`)

Seven reusable workflows are live, consumed by **38 caller jobs** (35 cross-repo + 3 hub-local):

* **Docker Tool** (`docker-tool.reusable.yml`) — environment setup, linting, testing with coverage,
multi-target Docker builds, GHCR publish, and the post-publish container scan.
* **Security** (`security.reusable.yml`) — version consistency check plus the periodic Trivy re-scan of the
published image.
* **Paradata Drift** (`para-drift.reusable.yml`) — canonical shared-file parity diff. Reads the canonical
files via a `hub-ref` input (default `v1`) rather than a hardcoded branch.
* **API Meta-Contract** (`api-contract.reusable.yml`) — the §4.1 service contract test.
* **CodeQL** (`codeql.reusable.yml`) — Python, `build-mode: none`. The caller supplies the schedule (`on:`
can only be declared by the caller) and **must** grant `security-events: write`.
* **pre-commit** (`pre-commit.reusable.yml`) — blocking, with the hook-environment cache. The repo's own
`.pre-commit-config.yaml` and `ruff.toml` still decide what runs.
* **Workflow Policy Lint** (`workflow-lint.reusable.yml`) — runs the hub's `tools/ci/workflow_lint.py`
against the caller's tree. ⚠️ It has no published caller example, so its own caller shape is not
policy-linted (roadmap **E4**).
* **Skill Branch Validation** (`skill-validate.reusable.yml`) — for `agent-skill` branches; no
default-branch callers.
* **Dependabot / GPU Inference / Scheduled Smoke / Release:** caller examples in
`docs/templates/workflows/`, localized per repo. These are **not** yet reusables — see §5.

> The CodeQL and pre-commit reusables replaced ten near-identical local workflows (431 lines) on
> 2026-07-30 (#18, T3). Their only real differences were an arbitrary weekly cron and whether the
> pre-commit cache was present. They were deferred until the pins were on `@v1`, because collapsing them
> while callers still pointed at a mutable branch would have raised coupling from 20 refs to 30.

> 📌 **Ref-pin convention: two channels.**
>
> | Channel     | Who uses it                                                  | Mutability                                       |
> |-------------|--------------------------------------------------------------|--------------------------------------------------|
> | **`@v1`**   | every caller in every tool repo                              | moving **major tag**; only a maintainer moves it |
> | **`@test`** | pre-release validation of a hub change, before `v1` is moved | branch — moves on every merge                    |
>
> Callers previously pinned `@test` directly, so **every merge to the hub's integration branch changed
> what all five repos executed, immediately**. Once `test` became the default branch that meant landing
> straight on production. The Wave B permission change is the concrete demonstration: one hub-side edit
> put `docker.yml` into `startup_failure` in all five repos at once.
>
> `@v1` keeps the "one edit updates all" property the architecture exists for — you still ship a hub fix
> centrally, by moving the tag — while removing the per-merge mutability. Exact tags (`v0.1.0`, …) stay
> as the audit record of what `v1` pointed at over time.
>
> **Moving `v1`:** land the hub change on `main`, validate it via a caller temporarily pinned `@test`,
> then `git tag -f v1 <sha> && git push -f origin v1`. Callers need no edit.
>
> ⚠️ **The trade-off, stated plainly:** `v1` is a **force-pushable tag**, and `workflow_lint.py`'s
> `WRITE_SCOPED` allowlist deliberately exempts reusable-workflow refs from the SHA-pin rule. So the
> ecosystem's single largest dependency is also its least-pinned one. This is accepted — pinning callers to
> SHAs would destroy the property the architecture exists for — but it carries two obligations: **`v1` moves
> only to a commit that passed `Hub Self-Check`**, and **every move is also recorded as an immutable
> `v1.x.y` tag** so there is an audit trail.
>
> ⚠️ `para-drift.reusable.yml` also reads the canonical `docs/templates/shared/*` files via its
> **`hub-ref`** input (default `v1`). Keep it in step with the ref the workflow is called at — a caller
> on `@test` should pass `hub-ref: test`, or it compares against the wrong generation of templates.

### Localized Repository Workflows

* **`atrium-alto-postprocess`:** CodeQL, Docker Build & Publish, pre-commit, Automated Releases, Scheduled
Smoke Tests, Paradata Drift, API Meta-Contract, Workflow Policy Lint, and Security & Supply-chain scanning
(`para-config-path: setup/para_config.txt` — configs moved into `setup/`). Fully on the current
action-version floor with correct triggers throughout. ⚠️ Owns the ecosystem's only real GPU test
(`tests/test_gpu_concurrency.py`) but has **no GPU workflow**.
* **`atrium-nlp-enrich`:** CodeQL, multi-target Docker builds (`base`, `api`, `llm`), GPU Inference Tests,
pre-commit, Releases, Scheduled Smoke Tests, Security scans, Paradata Drift, API Meta-Contract, Workflow
Policy Lint, and a dedicated Shellcheck workflow (the only one in the ecosystem).
* **`atrium-page-classification`:** CodeQL, Docker Build & Publish (incl. `vit`/`clip` branch triggers), GPU
Inference Tests, pre-commit, Automated Releases, Scheduled Smoke Tests (HF caching + a model-revision
reachability check), Paradata Drift, API Meta-Contract, Workflow Policy Lint, and Security Scans
(`para-config-path: setup/para_config.txt`). Its `release.yml` carries the **only** bundle-closure guard in
the ecosystem — a generic, dependency-free AST check that belongs in the hub (roadmap **D2**).
* **`atrium-translator`:** CodeQL, Docker Build & Push, pre-commit, Scheduled Smoke Tests, Release Bundling,
Paradata Drift, API Meta-Contract, Workflow Policy Lint, and Security Scans. CPU-only tool — no GPU lane by
design.
* **`atrium-llm-enrich`:** CodeQL, Docker Build & Publish (`remote` + `llm` targets — `base` deliberately
unpublished, it carries no ENTRYPOINT), GPU Inference Tests, pre-commit, notes-only Releases, Scheduled
Smoke Tests, Paradata Drift, API Meta-Contract, Workflow Policy Lint, and Security scans targeting the
`-llm` image variant (largest CVE surface).

---

## 2. Version floor and action pinning

Action versions match the Node-24 baseline (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`). The current floor:

`checkout@v7`, `setup-python@v7`, `cache@v6`, `upload-artifact@v7`, `github-script@v9`,
`codecov-action@v7`, `codeql-action@v4` (v3 deprecates Dec 2026), `gh-release@v3`, docker actions at
`login@v4` / `metadata@v6` / `buildx@v4` / `build-push@v7`, `trivy-action@v0.36.0`.

**Write-scoped actions are SHA-pinned** with a `# vX` comment that the linter verifies resolves to the
pinned SHA — including correct handling of annotated tags, where `refs/tags/v3` names the tag object rather
than the commit. The gate set is `softprops/action-gh-release`, `peter-evans/create-pull-request`,
`docker/build-push-action`, `aquasecurity/trivy-action`.

⚠️ **Two hub workflows are below this floor:** `e2e-pipeline-smoke.yml` (`checkout@v4`, `setup-python@v5`,
`upload-artifact@v4`, `github-script@v7`) and `all-repos-smoke.yml` (`checkout@v5`, `setup-python@v6`), as
are the `gpu-inference` and `scheduled-smoke` caller templates. Nothing enforces the floor, because the
linter has no rule for it (roadmap **E3**).

---

## 3. Container and image conventions

### 3.1 Image names

`docker-tool.reusable.yml` publishes with a **repo-name suffix** per build target:

```
ghcr.io/ufal/atrium-<tool>                  # the `base` target
ghcr.io/ufal/atrium-<tool>-<target>         # every other target, e.g. -api, -llm, -remote
```

⚠️ **The compose files in `nlp-enrich` and `llm-enrich` use a *tag* suffix instead**
(`ghcr.io/ufal/atrium-nlp-enrich:<ver>-api`), so those six references are not pullable. The publisher form
above is authoritative; compose is queued for correction (roadmap **B2**, decision §3.1).

### 3.2 Tag channels

| Channel     | Published on | Meaning               |
|-------------|--------------|-----------------------|
| `<semver>`  | `v*` tag     | the immutable release |
| `latest`    | `v*` tag     | most recent release   |
| `sha-<sha>` | `v*` tag     | exact commit          |

⚠️ `type=semver,pattern={{version}}` **strips the leading `v`** (publishing `1.7.3-beta`), while the
`ATRIUM_RUNNER_IMAGE` build-arg uses `github.ref_name` (`v1.7.3-beta`) — so paradata self-reports a tag
that was never published (roadmap **B3**).

⚠️ **There is no channel for the default branch.** Both smoke workflows therefore exercise the last
*tagged release*, never current HEAD. An `:edge` channel is proposed in roadmap **W3**.

### 3.3 Container scanning

Two Trivy paths, with **different policies** — worth stating precisely, because "Trivy is report-only" is
not true:

| Path                    | Where                                           | Severity                      | `exit-code` | Effect                      |
|-------------------------|-------------------------------------------------|-------------------------------|-------------|-----------------------------|
| Post-publish SARIF scan | inside `build-and-push`, by immutable digest    | `CRITICAL,HIGH`               | `"0"`       | reports to the Security tab |
| **Release gate**        | inside `build-and-push`, tags only, by digest   | `CRITICAL` + `ignore-unfixed` | **`"1"`**   | **fails the release**       |
| Periodic re-scan        | `security.reusable.yml`, schedule/dispatch only | `CRITICAL,HIGH`               | `"0"`       | reports only                |

The release gate is deliberately narrowed three ways — tags only, CRITICAL only, fixable only — so an
unpatchable CVE cannot wedge a release, and it runs *after* the SARIF upload so findings are recorded even
when it blocks. **HIGH and unfixable-CRITICAL have no policy yet** (roadmap **H7**).

⚠️ `security.reusable.yml` gates its scan job on `schedule || workflow_dispatch`. `atrium-translator` and
`atrium-page-classification` do not declare `workflow_dispatch`, so **their weekly cron is the only way to
run a scan at all** (roadmap **E10**).

---

## 4. Scheduled workload allocation

Cron slots, UTC. **The current allocation collides** — 8 of 12 active weekly jobs land inside Monday
05:00–06:00, because the deliberate 15-minute CodeQL stagger was never extended to `security.yml`.

**Current state:**

| Slot          | Jobs                                                 |
|---------------|------------------------------------------------------|
| `0 0 * * 1`   | translator security                                  |
| `0 3 * * *`   | page-classification smoke **+** alto smoke           |
| `0 3 * * 1`   | page-classification security                         |
| `0 4 * * *`   | translator smoke                                     |
| `0 4 * * 1`   | nlp smoke **+** llm smoke                            |
| `0 5 * * 1`   | alto CodeQL **+** nlp security **+** llm security    |
| `15 5 * * 1`  | llm CodeQL **+** hub CodeQL                          |
| `30 5 * * 1`  | nlp CodeQL **+** hub pre-commit                      |
| `45 5 * * 1`  | page-classification CodeQL **+** hub self-check      |
| `0 6 * * 1`   | translator CodeQL **+** alto security                |
| `0 2 */3 * *` | hub `e2e-pipeline-smoke` **+** hub `all-repos-smoke` |

**Convention going forward:** one slot per (repo × workflow) pair; 15-minute spacing within a family;
families separated by at least an hour. `gpu-inference` crons stay commented out until a runner exists —
deliberately, so the ecosystem does not advertise coverage it does not have.

---

## 5. What is *not* yet centralized

Four workflow families remain per-repo copy-paste with **no hub reusable** — ~1,020 lines:

| Family                | Lines | Repos | Note                                                                                                                                                                                          |
|-----------------------|-------|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `release.yml`         | 429   | 5     | Kept standalone on purpose: a release gate must not depend on a cross-repo `uses:` resolving at tag-push time. A reusable that keeps the *guard* vendored is still possible — roadmap **W4**. |
| `scheduled-smoke.yml` | 378   | 5     | Three different semantics have already diverged.                                                                                                                                              |
| `gpu-inference.yml`   | 183   | 3     | Two byte-identical copies plus one separate implementation; deployed in the wrong three repos.                                                                                                |
| `shellcheck.yml`      | 33    | 1     | nlp-enrich only, while page-classification has more shell scripts and no workflow.                                                                                                            |

The hub also ships **no Dockerfile and no compose file**. `plan_repo_review.md` references a planned
`compose/docker-compose.pipeline.yml`; that file does not exist and, per the 2026-06-12 decision that no
umbrella wrapper is needed, is not planned. That reference should be removed.

---

## 6. The Workflow Menu (Reference)

All ready-to-commit templates live in `docs/templates/workflows/`.

| Workflow                 | What it does                                        | Deployment state                                                                      | Lives as        |
|--------------------------|-----------------------------------------------------|---------------------------------------------------------------------------------------|-----------------|
| **Docker Tool**          | Test + coverage + multi-target GHCR publish + scan. | ✅ All 5 repos (→ `docker-tool.reusable.yml@v1`).                                      | Reusable Bundle |
| **Security**             | Version check + periodic Trivy re-scan.             | ✅ All 5 repos (→ `security.reusable.yml@v1`). ⚠️ No dispatch in TR/PC.                | Reusable Bundle |
| **Paradata Drift**       | Canonical shared-file parity diff vs hub.           | ✅ All 5 repos.                                                                        | Reusable Bundle |
| **CodeQL**               | Static security/quality analysis for Python.        | ✅ All 5 repos (→ `codeql.reusable.yml@v1`).                                           | Reusable Bundle |
| **pre-commit**           | Ruff + ShellCheck + whitespace, **blocking**.       | ✅ All 5 repos (→ `pre-commit.reusable.yml@v1`).                                       | Reusable Bundle |
| **API Meta-Contract**    | §4.1 service contract test.                         | ✅ All 5 repos (→ `api-contract.reusable.yml@v1`).                                     | Reusable Bundle |
| **Workflow Policy Lint** | Pins, `secrets:`, permissions, caller shape.        | ✅ All 5 repos + hub. ⚠️ No caller example published.                                  | Reusable Bundle |
| **Skill Validation**     | `agent-skill` branch contract checks.               | ✅ On the five `agent-skill` branches only.                                            | Reusable Bundle |
| **E2E Pipeline Smoke**   | Threads one document JSON through all 5 stages.     | ✅ Hub, nightly-ish. ⚠️ Tests the last release, not HEAD.                              | Hub workflow    |
| **Repo Suites Smoke**    | Runs each repo's pytest suite in parallel.          | ⚠️ Hub. Misnamed, omits `llm-enrich`, no marker filter, no timeout/concurrency.       | Hub workflow    |
| **Scheduled Smoke**      | Runs `pytest -m slow` on a cron.                    | ✅ All 5 repos — but slow lanes in TR/nlp/llm are **empty**, so 3 of 5 pass vacuously. | Standalone      |
| **GPU Inference**        | Real CUDA paths on a GPU runner.                    | 🕐 3 repos, inert pending a runner; alto — the one with a GPU test — has none.        | Standalone      |
| **Release**              | Version guard + release bundle/notes.               | ✅ All 5 repos. ⚠️ Bundle-closure guard in only 1 of 5.                                | Standalone      |
| **Shellcheck**           | Lints `*.sh`.                                       | ⚠️ nlp-enrich only.                                                                   | Standalone      |
| **Secret Scanning**      | Push protection + history sweep.                    | ⛔ Dropped 2026-07-30 — unadopted; GitHub-native scanning covers it.                   | —               |

### Secret scanning — why it was dropped

The gitleaks caller template was never adopted by any repo after being added on 2026-06-21, so it was
removed rather than left as indefinitely "paused" scaffolding. GitHub-native secret scanning with push
protection covers HuggingFace tokens and internal credentials without needing the ARUB/ARUP policy sign-off
or the org-owned `GITLEAKS_LICENSE` that `gitleaks-action` requires for organisation repositories.

> ⚠️ **If reopening:** the original blocker was policy, not tooling — the scope of secret rotation and a
> historical-history sweep still need security/infrastructure sign-off before adopting a scanner that acts
> on findings. Verify `gitleaks-action` versioning first; v2 reaches EOL in Sep 2026.
>
> **ARUP/ARUB institutional contacts for policy review:** Pavel (UFAL) or Ronald (ARUB).

> 📎 Related: `docs/templates/workflows/update_issues.sh` unconditionally exports an **elided placeholder**
> token, which both kills its own `-z` guard and overrides a correctly-set environment variable (roadmap
> **R1**). Not a usable credential, but a good reason to confirm GitHub-native secret scanning is enabled
> on all six repos.

---

## 7. Known-open items

Tracked in detail in [`docker_gha_roadmap.md`](docker_gha_roadmap.md); summarised here so this reference is
not read as "all green".

1. **Branch protection** — zero of ~20 branches are protected in any of the six repos, and `test` is a
   byte-identical mirror of the default branch everywhere, so every push runs the full suite twice
   ([#40](https://github.com/ufal/atrium-project/issues/40), roadmap §3.5).
2. **GPU runner** — still gates every `gpu`-class test. Roadmap §3.6 removes the single-supplier dependency
   by parameterising the runner labels and splitting the `slow` marker.
3. **Two API images cannot start** — `uvicorn` is absent from every requirements file in
   `page-classification` and `nlp-enrich` (roadmap **B1**).
4. **The E2E's secret-less path always fails** — the workflow's gate allows a skipped Stage 5, but
   `e2e_assert.py` asserts the block only Stage 5 writes (roadmap **B4**).
5. **Supply chain** — no lockfiles or hash pinning; two floating VCS refs and one unpinned ~1.2 GB
   build-time weight fetch baked into images (roadmap **H1–H3**).
6. **The policy linter has no tests** and no rule for `timeout-minutes`, `concurrency` or the action floor —
   which is how a new hub workflow shipped without any of them two days after they were rolled out
   (roadmap **E1–E5**).
