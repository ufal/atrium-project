# 🔎 ATRIUM cross-repo state — `test` / default / `agent-skill` HEADs

**Date: 7 September 2026 · Scope: all six `ufal` repositories, three branch families**

_Successor to [`project_state_3007.md`](project_state_3007.md) (2026-07-30) and
[`project_state_0208.md`](project_state_0208.md) (2026-08-02, lighter-touch). Prior baselines:
[`project_state_2207.md`](project_state_2207.md), [`project_state_1307.md`](project_state_1307.md),
[`project_state_2706.md`](project_state_2706.md). Covers the 39 days 07-30 → 09-07: two more
LLM-review rounds on issue [#10](https://github.com/ufal/atrium-project/issues/10) (08-06, 08-19),
the `docs/docker_gha_roadmap.md` audit (08-04), the `@v1` reusable-workflow pin going live
everywhere, a short-lived issue-log automation, and three new hub issues (#40, #51, #53)._

---

## §0 — How this pass was made

- **Branch HEADs and file contents** — `git fetch` on all six repos, reads against `origin/<branch>`.
- **Live CI** — GitHub Actions run history and job logs for the hub's five own workflows
  (`e2e-pipeline-smoke`, `e2e-digital-smoke`, `all-repos-smoke`, `hub-self-check`), including
  pulling the actual traceback out of the current `e2e-digital-smoke` failure rather than trusting
  its "failure" status alone.
- **Issue state** — `issue_read` (GitHub API `get`) on every issue this and prior digests have
  named, plus the three opened since 07-30. `list_issues` still returns `403 Resource not
  accessible by integration` for this session — the same gap every prior digest in this series has
  hit — so the open-issue count below is built by checking each known number individually, not by
  listing.
- **Per-repo state** — reused directly from the same-day per-repo `DEVLOG.md` refresh (this
  session's companion deliverable), which did its own live `git`/CI/API verification per repo; not
  re-derived here.
- **Spot-check discipline** — where a prior document's finding could be re-verified cheaply (the
  `docker_gha_roadmap.md` B1/B2 items; the `e2e-digital-smoke` root cause), it was, rather than
  carried forward as still-current by assumption. Both spot-checks below moved the finding.

---

## 🧭 Branch HEADs (fetched 2026-09-07)

| Repo                 | default  | default HEAD | `test` HEAD           | `agent-skill` HEAD | version              |
|----------------------|----------|--------------|-----------------------|--------------------|----------------------|
| atrium-project (hub) | `main`   | `8b1bf50`    | `8b1bf50` (identical) | —                  | tag `v1` → `8b1bf50` |
| page-classification  | `vit`    | `60f58bc`    | `60f58bc` (identical) | `0e45201` (07-31)  | `1.7.5-beta`         |
| alto-postprocess     | `master` | `cb235b5`    | `cb235b5` (identical) | `8dbaf16` (07-31)  | `1.4.6-beta`         |
| nlp-enrich           | `master` | `8dac20e`    | `8dac20e` (identical) | `9f48128` (07-31)  | `0.20.1`             |
| translator           | `master` | `dae197a`    | `dae197a` (identical) | `6176730` (07-31)  | `0.10.5`             |
| llm-enrich           | `main`   | `ee16913`    | `ee16913` (identical) | `815dcbb` (07-31)  | `0.6.2`              |

**`test` and default are now byte-identical in all six repos**, and have been since the 07-31 merge
wave — every push since lands on both. This is exactly the state `docs/docker_gha_roadmap.md`
(08-04) named as its second "settled decision": *retire `test`, protect the default branch,* on the
grounds that a mirror branch doubles CI spend and protects nothing. **That decision has not been
executed** — both branches still exist, both still receive every push, both still run full CI
(`hub-self-check`/`all-repos-smoke` fire twice per push on the hub alone, once per branch). Issue
#40 (branch protection) remains open with no visible progress.

All five `agent-skill` branches are frozen at their 07-31 "update GHA ref to v1" commits — no
further sync since. This is a **growing, unmeasured drift window** (now 38 days) of the same S2
class earlier digests flagged, this time with no repo-side digest tracking it (the per-repo DEVLOGs
refreshed today don't surface an `agent-skill`-specific issue anywhere in the ecosystem).

---

## Part A — What actually happened in this window

### A.1 The `docs/docker_gha_roadmap.md` audit (2026-08-04)

A comprehensive, deliberately **documentation-only** pass against issue #18, cataloguing:

- **9 live breakages (B1–B9)**: two API images (`page-classification`, `nlp-enrich`) with no ASGI
  server in any requirements file although both Dockerfiles/composes launch one; every suffixed
  compose `image:` reference asking for the wrong tag shape (`-api` as a repo-name suffix vs. the
  tag suffix CI actually publishes); a paradata self-report naming a GHCR tag that was never
  published (the leading `v` stripped by the tag pattern but expected back by `.env.example`); the
  E2E's own no-`OPENROUTER_KEY` fallback path guaranteed to fail its own unconditional `enrichment`
  assertion; llm-enrich's unbuilt `api` Dockerfile stage referenced by compose anyway; all five
  composes bind-mounting a `data/` directory that exists in no repo (root-owned on first
  auto-create, breaking the uid-10001 container user); a `.yml`/`.yaml` mismatch breaking nlp's and
  llm's documented GPU-overlay command; alto's production entrypoint using `uvicorn --reload`, a
  filesystem-watching dev server; and the E2E silently patching `alto-tools` at runtime inside the
  published image, contradicting the pinned commit in `requirements.txt`.
- **11 enforcement gaps (E1–E11)**: the hub's own self-check doesn't check the hub's own linter
  changes (checks out the linter at a fixed ref instead of by local path); `workflow_lint.py` has
  zero tests and crashes on the legal `permissions: read-all` shorthand; no rule for
  `timeout-minutes`/`concurrency`/workflow-level `permissions`/action-version floors; a second,
  unlinted `@test`-pinned copy of a caller example sits beside the linted `@v1` one because the
  lint glob misses `*.yaml`; `all-repos-smoke.yml` runs the untagged full pytest suite (including
  the model/network lane) on a GPU-less hosted runner and statically omits llm-enrich from its own
  matrix; two contradictory ruff gates (one advisory, one blocking) run on every PR; the four
  largest canonical shared files have zero tests of their own content, only byte-parity enforcement.
- **~1,020 uncollapsed lines (D1–D4)** across `release.yml`/`scheduled-smoke.yml`/
  `gpu-inference.yml`/`shellcheck.yml`, each already drifted in practice — most strikingly, **alto
  owns the ecosystem's only real GPU test and has no GPU workflow, while nlp and llm each have a
  GPU workflow that can collect zero tests.**

**Spot-checked today: B1 and B2 are fixed.** nlp-enrich's `service/requirements.txt` now declares
`fastapi`/`uvicorn[standard]`/`python-multipart` with a comment citing **`atrium-project#10, G3`**
— not this roadmap document — and a new `tests/test_service_requirements.py` gate; its
`docker-compose.yaml` now uses the tag-suffix form (`${ATRIUM_VERSION:-dev}-api`) the roadmap said
CI actually publishes. **The fix landed through issue #10's lettered review rounds, not through a
dedicated execution of this roadmap.** The roadmap's own four "settled decisions" — retire `test`,
runner-agnostic GPU lane, collapse the four duplicated families, `:edge`+hygiene — show no evidence
of execution as their own initiative; whether the individual B/E/D items not spot-checked here
(most of E1–E11 and all of D1–D4) have separately been absorbed into #10's rounds is **not
verified** and should not be assumed either way.

### A.2 Issue #10 keeps functioning as the ecosystem's de facto review umbrella

Two more dated "rounds" landed since 07-30, each with its own lettered findings referenced directly
in downstream code comments (`atrium-project#10, G3`, `D4`, `J3`, …):

- **08-06 round**: 5 P0s, each invisible to the repo that owned it — alto's `/process` merging a
  code path that returns nothing and writing a hardcoded one-page stub; the same endpoint and
  llm-enrich's remote CLIs both re-keying records via a lower-cased `Path.stem`, discarding
  upstream blocks; nlp's `teitok-schema.yml` red on its only run; pc's Dependabot `numpy` guard
  reverted five minutes after being added. Found in passing: **translator's `/translate` omitted
  `backend` entirely, so every real upload returned HTTP 500**, uncaught because every test mocked
  the pipeline — a defect of the same shape and severity as the numpy/Python-3.12 break the hub's
  07-30 digest caught in page-classification. `canonical_doc_id()` and `validate_document()`
  (Layer D) go from ~0% adoption to enforced on every production write path.
- **08-19 round**: 9 findings, "six of them mechanisms that could not fail — not absent gates,
  present ones checking something other than the thing that mattered." Headline: `set_source()`
  silently discarding a new `origin` sub-key when the baseline's `source` block was already
  partial, **reintroducing the exact bug the 08-06 round had just removed, through a different
  door** — fixed with a test that reproduces both arms. Every workflow's `concurrency` group keyed
  only by `${{ github.ref }}` meant a scheduled run and a push run on the same ref shared a group,
  and `cancel-in-progress` let the push silently kill the scheduled one with **no failure
  reported** — caught because a real cancellation happened eleven seconds before this review ran;
  fixed as a new `workflow_lint.py` check, not a hand-edit, now enforced on every push in all six
  repos. The round also **corrected two of its own claims** before publishing (a stale checkout
  that would have produced 11 false findings; an unsound inference from a lightweight tag's
  current target to its history) — the same self-auditing discipline this digest series has tried
  to model since `project_state_2207.md`.
- **`v1` moved** to `f54983e` at 08-19 09:37Z, carrying the widened `build-and-push` gate that
  admits pushes to `refs/heads/test` — the mechanism the 07-30 digest's N7/N8 findings were waiting
  on. **This is now live and confirmed**: all five tool repos' workflows reference the hub's
  reusables at `@v1`, not `@test` (re-verified today, independently, in each per-repo DEVLOG pass).

### A.3 `issue-log-refresh.yml` — ran once, then was abandoned

Closes out the N6 finding from `project_state_3007.md` (07-30: "has still never run") — with an
ending that finding didn't anticipate:

1. **08-10 and 08-17**: ran and **failed both times**, silently — an exhaustive `permissions:`
   block set `issues: none`, so even the failure-notification step 403'd.
2. **08-18**: fixed, with a `dry-run` input added specifically so it could be hand-verified first.
3. **09-04**: ran successfully via PR #52, importing a full `gh2md` export **including closed
   issues** for the first time — dozens of new `*.issue.closed.md` files.
4. **09-04, same day**: reverted (`dbaa44e`) — the closed-issue files were deleted and the rest
   reformatted for pre-commit. Closed issues are not this directory's convention (per #29: living
   exports track *open* issues only).
5. **09-06**: the workflow itself was **deleted outright** (281 lines, `3ea60ff`) after exactly one
   successful run. The ecosystem is back to the manual `gh2md` + `update_issues.sh` flow the
   automation was built to replace.

Read plainly: the automation did what it was asked, and the maintainer decided by hand that what it
produced wasn't the right shape, then removed it rather than reconfigure it. Worth remembering if
`issue-log-refresh.yml` is ever proposed again — the blocker was never "it doesn't run."

### A.4 Three new hub issues

- **#40** (08-02, open) — branch protection + GPU runner. @motyc explicitly **descopes the GPU half
  from UFAL infrastructure**: no live GPU access wired to ARUP/B's environment from this CI; the
  boundary is a Docker image built and run entirely inside ARUP/B's own fork/Kubernetes. Metacentrum
  (e-INFRA.cz's GPU grid, application-gated) is floated as the outside-infra alternative; nothing
  built yet. Branch protection (the other half) has no visible action either.
- **#51** (09-04, open) — DARIAH Vocabs namespace for publishing the AMCR+TEATER vocabulary as
  SKOS. @motyc defers it: a separate 18-month SKOSification project already exists
  (led by @petrpajdla); this issue should not block, and current vocab IDs become PID references
  once that project ships. Directly downstream of `nlp-enrich`'s issue #6 vocabulary work.
- **#53** (09-06, open) — apply the twelve-factor methodology across all six repos. No response
  yet. Likely successor framing for the ad-hoc lettered findings issue #10's rounds have
  accumulated; whether it absorbs #10 or runs alongside it is unresolved.

---

## Part B — CI state, verified live

| Workflow                                              | Status as of 09-07                                                                                                                                                                                                                                           |
|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `e2e-pipeline-smoke.yml` (5-stage JSON pipeline)      | **Green.** 112 runs; one failure since 08-19 (transient). Runs on every push to both `main` and `test` (double-fires per push, per the un-retired `test` branch).                                                                                            |
| `all-repos-smoke.yml` ("Cross-Repo Fast-Lane Matrix") | Green, same double-fire pattern. Still omits llm-enrich from its matrix and runs the untagged full suite on a hosted runner per `docker_gha_roadmap.md` E5 — not re-verified line-by-line this pass, but the workflow file's shape is unchanged since 08-04. |
| `hub-self-check.yml`                                  | Green, 140 runs, double-fires per push.                                                                                                                                                                                                                      |
| `e2e-digital-smoke.yml`                               | **Red on all 19 runs since it was created (08-06).** See §B.1 — this is the headline finding of this pass.                                                                                                                                                   |

### B.1 `e2e-digital-smoke.yml` — the failure mode has changed, and this pass is the first to notice

Every prior status on this workflow (`10.digest.md` §4.3, 08-19: *"7 runs, 7 failures, never
reaching an assert step... it has not been re-run since before its blocker cleared"*) described an
**image-resolution** failure — the workflow died before the pipeline ever ran. That is no longer
true, and has not been true for a while:

- **19 runs, 19 failures**, spanning scheduled crons, four manual `workflow_dispatch` attempts
  (09-06), and ordinary pushes, from `run #1` (08-06) through `run #19` (today).
- **The job now runs to completion.** Today's run's step list: image preflight ✅ → fixture
  generation ✅ → **Stage D1 digital-convert (happy path)** ✅ → born-digital contract assertion ✅ →
  **Stage D1b (garbled text layer)** ✅ → `needs_ocr` handoff assertion ✅ → **Stage D2 llm-enrich**
  ✅ → **"Assert the final accreted record"** ❌.
- **The actual error**, pulled from the job log:
  ```
  AssertionError: ❌ 'enrichment' block missing from llm-enrich stage
  ```
  preceded by `✅ doc_id: 'minimal' unchanged across 2 stage record(s)` and
  `✅ schema: … validates against atrium_document.schema.json`. Schema validity, `doc_id` stability
  and the OCR handoff all pass. The one thing that doesn't: the `-remote`/`-digital` image path this
  workflow drives **does not populate the `enrichment` block** that llm-enrich's `/enrich` API path
  does (per issue #10's 08-19 round, the API path reached parity on `document_json` weeks ago). The
  CLI path this E2E exercises apparently never got the same fix.
- **A bot-managed tracking issue already exists**: **#49**, opened 08-22, commented on again on
  every subsequent failure (7 comments, latest today) rather than duplicated — the workflow's own
  failure-handler correctly recognizes repeat failures via a body marker. Its guidance text (written
  08-22, still attached to every comment) still describes the *old* failure class ("`MISSING` in the
  preflight step means the image was never published... a schema failure names the owning repo per
  block") — **this guidance is now stale and points a future debugger at the wrong layer.** The
  fixture/OCR/schema paths it warns about are all passing; the actual defect is one layer up, in
  what the CLI writes.
- **Practical read**: this is not an infrastructure problem any more (GHCR images resolve fine,
  `:latest` for `-digital` now exists per the earlier B3/`-digital:latest 404` note being resolved
  by llm-enrich's subsequent releases). It is a genuine, currently-open **content defect** in
  llm-enrich's non-API digital-born code path, and it has been silently red for a month because
  nobody has re-read past the "still failing" comment to the actual traceback.

**Recommended action**: update issue #49's body (or open a fresh comment) to correct the stale
guidance, and file the real defect — `enrichment` not written on the CLI/remote path for
digital-born input — against `atrium-llm-enrich`, cross-referencing this repo's own #18 (the
PDF/DOCX-to-JSON converter that shipped the digital-convert originator) since that is the most
likely place the CLI-vs-API divergence originates.

---

## Part C — Issue tracker, verified individually (18 open)

| #  | Title                             | Opened | Status this pass                                                                             |
|----|-----------------------------------|--------|----------------------------------------------------------------------------------------------|
| 4  | SSH Open Marketplace records      | 03-13  | open, reopened; last activity 09-07                                                          |
| 6  | Review & summarise licenses       | 03-13  | open; quiet since 07-16                                                                      |
| 10 | LLM validation of source code     | 03-15  | open, reopened; **the active umbrella** — see §A.2                                           |
| 13 | CAA Proceedings paper             | 03-25  | open; quiet since 06-25                                                                      |
| 15 | Submission to IJDL                | 05-27  | open; quiet since 06-25                                                                      |
| 16 | ARUP/B data storage locations     | 05-27  | open, reopened; quiet since 07-16                                                            |
| 17 | SSHOMP workflow descriptions      | 05-27  | open; quiet since 06-28                                                                      |
| 18 | Docker/GHA wrapper for CU forks   | 05-27  | open; quiet since 08-02 — largely superseded in practice by #10's rounds and the roadmap doc |
| 21 | LINDAT annotated dataset release  | 06-12  | open; quiet since 07-20                                                                      |
| 22 | Document Understanding benchmark  | 06-17  | open; quiet since 08-01                                                                      |
| 24 | LLM applications to data (hub)    | 06-19  | open; quiet since 08-01                                                                      |
| 26 | Run models larger than GPU memory | 06-20  | open; quiet since 06-21                                                                      |
| 27 | H100 multi-GPU runs               | 06-20  | open; quiet since 06-21                                                                      |
| 31 | AGENT SKILL rollout               | 07-17  | open; quiet since 08-01 — `agent-skill` branches now 38 days stale, unremarked               |
| 32 | API service standardization       | 07-23  | open; quiet since 08-01                                                                      |
| 40 | Branch protection + GPU runner    | 08-02  | open; GPU half explicitly descoped from UFAL infra (§A.4)                                    |
| 51 | DARIAH Vocabs namespace           | 09-04  | open; deferred ~18 months by @motyc (§A.4)                                                   |
| 53 | 12-factor best practices          | 09-06  | open; no response yet (§A.4)                                                                 |

Closed since the last count: none newly closed on the hub itself in this window (#29 was already
closed prior to 07-30). Net change from 07-30's 15: **+3** (#40, #51, #53).

---

## ✅ Verdict

1. **The self-correcting review process (issue #10) is the real engine of this ecosystem right
   now**, more than any of the named cross-cutting issues (#18, #31, #32). Two more rounds landed
   real fixes, including a bug (`set_source()`) that recurred through a different door after being
   fixed once, and a CI mechanism (concurrency cancellation) that was silently eating scheduled
   signal. The rounds' habit of publishing corrections to their *own* prior claims — a stale
   checkout, an unsound tag-history inference — is the single healthiest process property visible
   in this whole series of digests, and this pass tries to hold itself to the same standard (§B.1,
   §A.1).
2. **One month-old, actively-misdiagnosed red light**: `e2e-digital-smoke.yml`. Its own tracking
   issue has been quietly restating a stale root cause for two weeks while the real one — a content
   gap in llm-enrich's CLI path, not an infra gap — sat one log-scroll away. This is exactly the
   failure mode T5 (`project_state_2207.md`) and N11 (`project_state_3007.md`) warned about, now
   observed on a CI signal instead of a digest.
3. **Two structural decisions are named but not executed**: retiring the `test` branch (still a
   full mirror, still double-firing CI on every push, six repos), and the GPU lane (now explicitly
   descoped from UFAL infrastructure by @motyc rather than merely blocked on a runner — a real
   answer, just not yet a built one).
4. **The `agent-skill` branches have gone quiet for 38 days** with no digest or issue currently
   watching that drift window — the exact repeatable risk `31.digest.md` (nlp-enrich's DEVLOG,
   refreshed today) already names for four of the five branches.

### Recommended actions, in order

1. **Re-diagnose `e2e-digital-smoke.yml` for real** — the fix is in llm-enrich's CLI/remote image
   path, not in the fixture/schema/OCR layers issue #49's stale guidance points at. Update or
   replace that guidance so the next person who reads it doesn't repeat this pass's initial
   assumption. *(§B.1, new finding this pass.)*
2. **Decide, explicitly, whether `docs/docker_gha_roadmap.md`'s four "settled decisions" are still
   wanted.** They were declared settled 08-04 and none has been executed in the 34 days since;
   either schedule the execution round or retire the document's authority to speak for current
   intent.
3. **Act on #40's two halves separately** — branch protection has no external dependency and could
   land this week; the GPU lane needs a Metacentrum access decision before anything else can move.
4. **Give the `agent-skill` branches one sync pass** before the drift compounds further — nlp-enrich
   is the reference (already aligned per its own `31.digest.md`), the other four are not.
5. **Close the loop on `docker_gha_roadmap.md`'s B3–B9 and all of E1–E11/D1–D4** — only B1/B2 were
   spot-checked this pass and found fixed (via #10, not via this document). The remaining ~20
   findings' current status is genuinely unknown, not assumed-fine.

---

_Cross-repo state digest generated 2026-09-07 from live branch, CI-log and issue state of all six
`ufal/atrium-*` repositories, cross-referenced against the same-session per-repo `DEVLOG.md`
refreshes. Like its predecessors it lives on `test`; forward-merging it to `main` is moot this time
only because the two branches are currently identical — see §A "retire `test`" discussion above for
why that should not be relied on going forward._
