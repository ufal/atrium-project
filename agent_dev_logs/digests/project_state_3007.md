# 🔎 ATRIUM cross-repo state — `test` / default / `agent-skill` HEADs

**Date: 30 July 2026 · Scope: all six `ufal` repositories, three branch families**

_Successor to [`project_state_2207.md`](project_state_2207.md) (2026-07-22, corrected edition) ·
prior baselines [`project_state_1307.md`](project_state_1307.md), [`project_state_2706.md`](project_state_2706.md).
Covers the eight days 07-22 → 07-30: the OpenAPI meta-contract ([#32](https://github.com/ufal/atrium-project/issues/32)),
the `atrium_document` accretion, two release waves, the agent-skill re-alignment
([#31](https://github.com/ufal/atrium-project/issues/31)) and the full GHA/Docker overhaul
([#18](https://github.com/ufal/atrium-project/issues/18))._

---

## §0 — How this pass was made

Everything below was re-derived from live state, not from the previous digests:

- **Branch HEADs and file contents** — `git fetch --prune` on all six repos, then reads against
  `origin/<branch>` refs (no working-tree assumptions).
- **Tier-1 validation** — `python3 -m compileall` + `ruff check .` in **six isolated worktrees**
  checked out at `origin/test`.
- **Shared-code parity** — sha256 of every file in the hub's `docs/templates/shared/` against its
  vendored copy in each repo.
- **Releases / CI** — GitHub API: release lists per repo, workflow-run history per repo
  (last 40 runs), the failing job's step list and log tail, and the `skill-validate` history on
  every `agent-skill` branch.
- **Issue history** — the `agent_dev_logs/issues/` exports regenerated the same morning
  (footer: `Generated on 2026.07.30 at 07:30:06`).

Two limitations to be honest about: the session's GitHub App **cannot list issues**
(`403 Resource not accessible by integration`), so per-repo issue counts below come from the
repository object's `open_issues_count`, which includes open PRs — only nlp-enrich's count was
cross-checked against an empty PR list. And tags were not enumerated separately from releases,
so a superseded tag could still exist without a release attached to it (see §D, T3).

---

## 🧭 Branch HEADs (fetched 2026-07-30)

| Repo                 | default  | default HEAD | `test` HEAD | `agent-skill` HEAD | `test` vs default |
|----------------------|----------|--------------|-------------|--------------------|-------------------|
| atrium-project (hub) | `main`   | `563ccd0`    | `293b9f7`   | —                  | **test +2**       |
| page-classification  | `vit`    | `1b3d81a`    | `67a7d85`   | `deb2187` (07-29)  | **test +2**       |
| alto-postprocess     | `master` | `ba616c3`    | `ba616c3`   | `f08cd95` (07-29)  | identical         |
| nlp-enrich           | `master` | `4f1910c`    | `4f1910c`   | `1a8ff2c` (07-29)  | identical         |
| translator           | `master` | `80bc05e`    | `80bc05e`   | `fce1091` (07-29)  | identical         |
| llm-enrich           | `main`   | `260f861`    | `b2df630`   | `a90aa92` (07-29)  | **test +2**       |

⟳ **Correction to the current `18.digest.md`**: it states "`test` is now the default branch".
Live, the default branches are `main` (hub, llm-enrich), `master` (alto, nlp, translator) and
`vit` (page-classification) — unchanged. What actually happened is that `test` was **merged into**
each default branch, which is why `schedule`-triggered workflows finally reach the fixes. The
practical consequence the digest draws (a bad hub push now lands on production) still holds, but
the mechanism is the merge cadence, not a default-branch switch. In three repos `test` has since
moved ahead again (2 commits each), so the two branch families are already diverging.

---

## Part A — `test` / default branches (issue #10 continuation)

### A.1 Tier-1 validation matrix (re-run 2026-07-30, isolated worktrees at `origin/test`)

| Repo                | compileall | ruff                 | ruff config |
|---------------------|------------|----------------------|-------------|
| page-classification | OK         | All checks passed    | `ruff.toml` |
| alto-postprocess    | OK         | All checks passed    | `ruff.toml` |
| nlp-enrich          | OK         | All checks passed    | `ruff.toml` |
| translator          | OK         | All checks passed    | `ruff.toml` |
| llm-enrich          | OK         | All checks passed    | `ruff.toml` |
| **project (hub)**   | OK         | **1 finding** (F401) | **none**    |

The five tool repos are Tier-1 green and lint is now *blocking* in each of them (#18). The hub —
which authors and publishes the templates the others are linted against — has **no ruff config and
no lint workflow of its own**, and its single finding sits in a template it ships (N4 below).

### A.2 Versions, releases, tags

| Repo                | `CITATION.cff` == `para_config.txt` | latest release | published         |
|---------------------|-------------------------------------|----------------|-------------------|
| page-classification | `1.7.0-beta`                        | `v1.7.0-beta`  | 2026-07-26 15:46Z |
| alto-postprocess    | `1.4.0-beta`                        | `v1.4.0-beta`  | 2026-07-28 14:53Z |
| nlp-enrich          | `0.18.0`                            | `v0.18.0`      | 2026-07-26 15:41Z |
| translator          | `0.10.0`                            | `v0.10.0`      | 2026-07-26 18:16Z |
| llm-enrich          | `0.4.0`                             | `v0.4.0`       | 2026-07-25 09:33Z |

**All five repos' two in-repo version sources agree with each other and with the published tag** —
the first pass in this digest series where that is true everywhere. Two release waves drove it:
the 07-25 "OpenAPI standards draft + GHA release edit" wave and the 07-26 `atrium_document` wave,
with alto taking one more release on 07-28 for the per-line categorisation calibration contributed
by **david-spacil** (PR #32 — the first contribution from outside the core team).

⟳ Minor correction to `18.digest.md`, which says the latest tags "all date to **2026-07-26** or
earlier": alto's `v1.4.0-beta` is 07-28. The conclusion it supports is unaffected — every tag still
predates the GHA work that landed 07-29/07-30, so the release guards remain unexercised (N7).

### A.3 Shared-code parity — exact, and now wider

sha256 (first 12) of the hub canonical vs every vendored copy on the five `test` branches:

| File                          | hash           | alto | nlp | pc | translator | llm |
|-------------------------------|----------------|------|-----|----|------------|-----|
| `atrium_paradata.py`          | `712a7287f8e5` | ✅    | ✅   | ✅  | ✅          | ✅   |
| `para_licenses.py`            | `35b827ad16d8` | ✅    | ✅   | ✅  | ✅          | ✅   |
| `tests/test_para_licenses.py` | `ed522ff8a074` | ✅    | ✅   | ✅  | ✅          | ✅   |
| `service/atrium_service.py`   | `cd49d0377ae4` | ✅    | ✅   | ✅  | ✅          | ✅   |
| `check_version.py`            | `4bd64b27518e` | ✅    | ✅   | ✅  | ✅          | ✅   |
| `atrium_document.py`          | `d72f257080dc` | ✅    | ✅   | ✅  | ✅          | ✅   |

The enforced set has **doubled since 07-22** — the paradata trio has been joined by the #32 service
helper, the #18 version guard and the #26 document model, each added to `para-drift.reusable.yml`
as it landed. `atrium_document.schema.json` also sits in the hub canonical directory. This is the
single healthiest structural signal in the ecosystem: the "not-a-monorepo, enforce-by-copy" model
is holding byte-exactly across five repos and six files.

### A.4 CI state (last run per workflow × branch, 2026-07-30 04:00–05:20Z)

| Workflow                 | pc                     | alto    | nlp   | translator | llm   | hub                  |
|--------------------------|------------------------|---------|-------|------------|-------|----------------------|
| API Meta-Contract        | ✅ / ✅                  | ✅ / ✅   | ✅ / ✅ | ✅ / ✅      | ✅ / ✅ | —                    |
| Docker Build & Publish   | **❌ test** / ✅ default | ✅ / ✅   | ✅ / ✅ | ✅ / ✅      | ✅ / ✅ | —                    |
| Paradata Canonical Drift | ✅ / ✅                  | ✅ / ✅   | ✅ / ✅ | ✅ / ✅      | ✅ / ✅ | —                    |
| Security / Supply-chain  | ✅ / ✅                  | ✅ / ✅   | ✅ / ✅ | ✅ / ✅      | ✅ / ✅ | —                    |
| CodeQL · pre-commit      | ✅                      | ✅       | ✅     | ✅          | ✅     | —                    |
| Scheduled Smoke          | —                      | ✅ 04:02 | —     | ✅ 05:02    | —     | —                    |
| E2E Pipeline Smoke       | —                      | —       | —     | —          | —     | ✅ #33 (nightly), #34 |

- **#32's five CI-plumbing defects are all closed.** `API Meta-Contract` is green on both the
  `test` and default branches of all five repos — the malformed hub reusable, the `api-contract.ym;`
  filename, the empty `requirements-test.txt` pair, the exit-5 trap and the mislanded llm-enrich
  requirements file are gone. The hub's own four `api-contract.reusable.yml` failure runs are all
  from 07-23 and have not recurred.
- **The `startup_failure` wave at 04:50–04:54Z** (pc, alto, nlp, translator) is the Wave B
  `security-events` permission regression described in `18.digest.md`; the 05:09–05:19Z re-runs are
  green, so it is genuinely closed.
- **The one red light in the ecosystem is page-classification's `test` branch** — N1 below.

---

## Part B — `agent-skill` branches (issue #31)

### B.1 Enforcement is live and asserting

All five branches were re-pushed 2026-07-29 and `skill-validate` is **green on every one**, against
hub reusable `eb5ec4a`:

| Repo                | branch HEAD | run              | result                                                          |
|---------------------|-------------|------------------|-----------------------------------------------------------------|
| page-classification | `deb2187`   | #5 (07-29 06:15) | ✅                                                               |
| alto-postprocess    | `f08cd95`   | #5 (07-29 06:17) | ✅                                                               |
| nlp-enrich          | `1a8ff2c`   | #7 (07-29 06:44) | ✅ (after #6 failed at 06:19 — a real catch, fixed 25 min later) |
| translator          | `fce1091`   | #4 (07-29 06:12) | ✅                                                               |
| llm-enrich          | `a90aa92`   | #4 (07-29 06:14) | ✅                                                               |

§12.3 **step 4** is what makes this meaningful: 4a is static and zero-dependency so it can never
skip, 4b boots the app and asserts the §4.1 `/info` envelope, `/health`, the documented endpoint set
and OpenAPI validity — import-skipping only the model-heavy repos, and then with a CI warning.
nlp-enrich's run #6 → #7 sequence is the proof the gate bites rather than rubber-stamps.

Each branch carries **exactly one** workflow (`skill-validate.yml`) — correct scoping for a
test-stripped branch, unchanged since the rollout.

### B.2 Content drift — one repo aligned, four lagging

| Repo                | `agent-skill` version | `test` version | lag         |
|---------------------|-----------------------|----------------|-------------|
| nlp-enrich          | `0.18.0`              | `0.18.0`       | **aligned** |
| page-classification | `1.5.1-beta`          | `1.7.0-beta`   | 2 minors    |
| translator          | `0.8.1`               | `0.10.0`       | 2 minors    |
| llm-enrich          | `0.2.0`               | `0.4.0`        | 2 minors    |
| alto-postprocess    | `1.0.0-beta`          | `1.4.0-beta`   | 4 minors    |

This is the standing **S2 manual-drift risk** made concrete: `skill-validate` guarantees the
*contract*, `para-drift` does not extend to these branches (the shared trio is stripped with the
tests), and so the only thing keeping the copied `service/` business logic in step with `test` is a
hand sync. Between 07-24 and 07-29 the accretion work on `test` re-opened a gap that had been
closed five days earlier. alto is the worst case at four minors behind.

The one **intended** divergence to keep in mind while syncing: the skill branches' own
`service/requirements.txt` files are correct runtime manifests, while two of the `test`-branch
copies are not (N2).

---

## Part C — Findings

| ID      | Sev              | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Evidence                                                                                                                    |
|---------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| **N1**  | **P0**           | **page-classification `test` cannot build.** Dependabot PR #36 (merged as `67a7d85`) bumped `setup/requirements.txt` to `numpy>=2.5.1,<3.0`. **numpy 2.5.x requires Python ≥ 3.12**; every image and CI job in the ecosystem pins **3.11** (`FROM python:3.11-slim`, `Setup Python 3.11`). `pip` therefore fails outright — `Ignored the following versions that require a different python version: … 2.5.1 Requires-Python >=3.12` → `No matching distribution found for numpy<3.0,>=2.5.1`. `Docker Build & Publish` #195 fails at step 7 in 1 s; `vit` at `1b3d81a` (same tree minus the bump) is green as #193. Fix: floor back to `>=2.4.1,<2.5` (2.4.0 is **yanked**, hence the current lower bound), or move the images to 3.12; either way the group needs a dependabot `ignore` (or a declared Python floor) or the bump returns tomorrow. **This is a class risk, not a pc quirk** — any repo whose dependency ships a newer Requires-Python will hit it.                                                                                                                                                                                                                                      | run [`30516310969`](https://github.com/ufal/atrium-page-classification/actions/runs/30516310969), job `build / test` step 7 |
| **N2**  | **P1**           | **page-classification's service runtime manifest was overwritten with test dependencies.** `service/requirements.txt` on `test`/`vit` now reads `pytest`, `pytest-cov`, `fastapi`, `httpx`, `python-multipart`, `openapi-spec-validator` — no `uvicorn`, no `pillow`, no torch stack. **`uvicorn` appears in no requirements file in the repo**, yet `docker-compose.yml`'s `api` profile entrypoint is `uvicorn service.api:app`, and `setup/setup_api_service.sh` installs that same file and then tells the user to run `uvicorn service.api:app --reload`. Both the containerized and the documented local API paths are broken. nlp-enrich has the same shape (`pytest`/`pytest-cov`/`openapi-spec-validator` in `service/requirements.txt`) — flagged on 07-29 as "`test` needs fixing", still open. llm-enrich is the correct pattern (`-r ../requirements_remote.txt` + fastapi/uvicorn/python-multipart). Nothing catches this: the contract test import-skips on pc, and the `agent-skill` branch still carries the *right* runtime set, so `skill-validate` is green. Fix: split test deps into `requirements-test.txt` (which already exists in both repos) and restore the runtime manifest. | `service/requirements.txt`, `docker-compose.yml`, `setup/setup_api_service.sh` on `origin/test`                             |
| **N3**  | **P1**           | **The skill tooling landed at a path nothing cites.** `31.digest.md` and `31.plan.md` still list "`tools/skill_drift_check.py` and `tools/skill_ify.py` never landed" as next step #1 — they **did** land, as `docs/templates/skill/skill_drift_check.py` and `docs/templates/skill/skill_ify.py`. Meanwhile every citation points at `tools/`: `agent_skill_strategy.md` lines 219, 492, 497, 507, 519 and `31.plan.md` lines 26–27, 59, 105, 113, 127. The hub *does* have a `tools/` dir (`tools/e2e/`), so the paths look plausible and fail only when someone runs them. Fix either way — `git mv` into `tools/`, or update the citations — but do one.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `docs/templates/skill/` tree vs the cited paths                                                                             |
| **N4**  | **P2**           | **The hub lints nothing.** No `ruff.toml`/`pyproject.toml`, no pre-commit or lint workflow, while all five tool repos now run ruff blocking. `ruff check .` on hub `test` reports `F401 shutil imported but unused` in `docs/templates/skill/skill_ify.py:32` — a finding in a file the hub *publishes as a template*. Adopting the hub's own `docs/templates/ruff.toml` plus a pre-commit caller closes it.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `ruff check .` in the hub worktree                                                                                          |
| **N5**  | **P2**           | **740 KB of unrelated binary ships in every page-classification image.** `service/Master_Diploma.pdf` (740 180 B) is committed on `test` and `vit`; the Dockerfile's `COPY . .` puts it in the image. The `agent-skill` branch correctly does not have it, which is a good hint it was never meant to be there.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `git ls-tree origin/test service/` vs `origin/agent-skill`                                                                  |
| **N6**  | **P2**           | **`issue-log-refresh.yml` has never run.** Created 07-28, three fatal defects fixed 07-30, still zero runs in the hub's history. The issue exports in this repo are still produced by the local `gh2md` script (today's footer, `07:30:06` CEST, postdates every GHA run that morning). The automation that #18 designed to get a personal token out of a shell script is merged but unexercised — one `workflow_dispatch` would settle it.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | hub workflow list + 68-run history                                                                                          |
| **N7**  | **P1** (carried) | **The release path has never run.** Five tag-gated guards are merged and completely unexercised: `check_version.py --require-tag`, pc's release-bundle closure guard, the post-publish Trivy digest scan + SARIF upload, the buildkit SBOM/provenance attestations, and `build-and-push` under the new caller-side `security-events: write`. Every current tag predates them (newest: alto `v1.4.0-beta`, 07-28). **One patch release exercises all five** — translator remains the right pilot (no GPU, no torch, single build target). A deliberate mismatched-`CITATION.cff` tag would confirm the version gate blocks; it never has, and it would have caught both `v1.0.0.-beta` and `v1.16.2`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | release lists vs `test` HEADs                                                                                               |
| **N8**  | **P1** (carried) | **`@test` reusable pin — 45 live references, not 20.** 4 caller refs per repo on `test` (20) + the same 4 on each default branch (20, identical blobs where `test == default`) + 1 `skill-validate` caller per `agent-skill` branch (5). The `@v1` pin plus branch protection is still the highest-value structural fix outstanding, and the Wave B permission regression — one hub edit that broke `docker.yml` in five repos at once — is the demonstrated blast radius.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `git grep 'atrium-project/.github/workflows/.*@test'` across all branch families                                            |
| **N9**  | **P2** (carried) | **No GPU runner** (with @rharasim). Every `slow`-marked test is still unexecuted anywhere, and the E2E `alto → nlp` boundary still consumes a committed fixture CSV instead of a live classify stage. The 07-30 change to *remove* the GPU crons was right — the ecosystem no longer advertises coverage it does not have — but the gap itself is unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `18.digest.md`; `e2e-pipeline-smoke.yml`                                                                                    |
| **N10** | **P3**           | **agent-skill version lag** — four of five branches are 2–4 minors behind their `test` counterpart (§B.2). Not a defect today; it is the metric to watch, because it is what the §12.2 sync exists to keep near zero.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `CITATION.cff` / `para_config.txt` per branch                                                                               |
| **N11** | note             | **Digest-vs-live drift is now the recurring failure mode.** This pass corrected three claims in current hub digests (default-branch identity, latest-tag date, "tooling never landed") and one in the prior state file, none of them careless when written — the ecosystem simply moves faster than the write-ups. T5 from 07-22 stands and generalizes: **treat any state table in these files as a lower bound and re-check before acting on it.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | this pass                                                                                                                   |

**Closed since `project_state_2207.md`:** T1 (alto malformed tag — superseded, and four releases have shipped cleanly since), T2 (llm-enrich `date-released` — fresh), **T3 (nlp `v1.16.2` mistag — the 07-22 release now appears as `v0.16.2`, published 13:51Z, matching `CITATION`/`para_config`; the release list carries no `v1.16.2`, though a stray *tag* was not separately checked)**, S1 (skill branches pushed and green), and all five of #32's CI-plumbing defects. T4 (the release/tag consistency gate) is now *implemented* as `check_version.py --require-tag` but remains **unproven** — it is carried forward as N7 rather than closed.

---

## Part D — Issue-tracker delta since 07-22

- **Hub: 15 open issues** (was 14) — **#32 "API services per repo should be standardized"** opened
  2026-07-23 and is already substantially delivered; nothing closed.
- **Tool repos** (repository `open_issues_count`, which includes open PRs): alto **5**,
  nlp-enrich **7** (verified 0 open PRs → 7 real issues), page-classification **1**,
  translator **1**, llm-enrich **3**.
- **`atrium-llm-enrich` #13** (document-JSON accretion) is the feature behind the 07-24 → 07-29
  agent-skill re-drift, and `#10`/`#11` there carry the DU input-format decisions that Alfie's
  07-22 feedback on hub #22 endorsed.
- Long-running items unchanged in kind: **#4/#6/#17** (SSHOMP records + license tables — the
  workflow-record item is still parked on the marketplace 500), **#13/#15** (CAA proceedings,
  deadline **31 Oct 2026**; IJDL), **#16/#21** (data locations + LINDAT release — both handles now
  live and cross-linked, #16 stays open until project end by motyc's request),
  **#22/#24/#26/#27** (DU benchmark, LLM applications, oversized-model CPU offload, H100
  multi-GPU).

---

## ✅ Verdict

The ecosystem is in the **strongest structural shape it has been in across this digest series**,
and for once the versions, the tags and the branch contents all agree.

1. **Enforcement caught up with intent.** Six shared files are now byte-identical across five
   repos and guarded by `para-drift`; every service speaks the §4 meta-contract and is checked by
   `api-contract` on both branch families; `skill-validate` step 4 asserts rather than skips, and
   demonstrably caught a real break (nlp #6). Lint is blocking in all five tool repos. The nightly
   E2E genuinely runs all five stages, including the `llm` stage that was silently dark for weeks.
2. **The gaps that remain are the ones that have never been exercised, not the ones that are
   broken.** The release path (N7), the `@v1` pin (N8) and the GPU runner (N9) are all "written and
   waiting". Two of the three need one deliberate action each to move — a patch release on
   translator, and a tag-plus-45-edits atomic change.
3. **One live P0 and two P1 hygiene defects.** page-classification's `test` branch cannot build
   (N1) and its API service cannot start from either documented path (N2); the hub documents tools
   at paths that do not resolve (N3). None of these is architectural — all three are same-day fixes
   — but N1 will block the next pc release and N2 would surface as a support question the moment
   anyone tries to run the service from the repo instead of the skill branch.

### Recommended actions, in order

1. **Unbreak pc `test`** — pin `numpy>=2.4.1,<2.5` (2.4.0 is yanked) and add a dependabot `ignore`
   for numpy ≥ 2.5 until the images move to Python 3.12. *(N1, P0)*
2. **Restore the service runtime manifests** in page-classification and nlp-enrich; move the
   meta-contract test deps into the `requirements-test.txt` each repo already has. *(N2, P1)*
3. **Reconcile the skill tooling paths** — `git mv` into `tools/` or fix the citations in
   `agent_skill_strategy.md` and `31.plan.md`; either way, drop the stale "never landed" item from
   `31.digest.md`. *(N3, P1)*
4. **Pilot the release path on translator** — one patch tag exercises all five guards at once, then
   one deliberately mismatched `CITATION.cff` to prove the gate blocks. *(N7)*
5. **Cut `@v1` and repin** all 45 caller references as a single atomic change, then add branch
   protection on hub `test`. *(N8)*
6. **Fire `issue-log-refresh.yml` once** by `workflow_dispatch` to retire the local `gh2md` script
   and the personal token it carries. *(N6)*
7. **Sync the four lagging `agent-skill` branches** (alto first, at four minors behind), and teach
   `skill_drift_check.py` to follow `subprocess` invocations — it under-reported nlp-enrich for
   exactly that reason. *(N10, §B.2)*
8. **Give the hub a lint config** (`docs/templates/ruff.toml` + a pre-commit caller) and clear the
   `skill_ify.py` F401. *(N4)* Drop `service/Master_Diploma.pdf` while in there. *(N5)*

---

_Cross-repo state digest generated 2026-07-30 from live branch, release and CI state of all six
`ufal/atrium-*` repositories. Like its predecessors it lives on `test`; forward-merging it to the
default branches is the standing recommendation, since agents reading only default branches lack
exactly this context._
