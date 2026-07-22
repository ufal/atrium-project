# 🔎 ATRIUM LLM Review State — `test` + `agent-skill` branch HEADs

**Date: 22 July 2026 · Scope: all six `ufal` repositories, two branch families**

_Refresh of the issue #10 (LLM source-code validation) review state, extended to the issue #31
(Agent Skill) `agent-skill` branches. Every verdict below was produced this pass against the live
remote HEADs via throw-away worktrees + GitHub releases/Actions — not inherited from the
maintainer digests under review. Prior baselines: `issue10_alignment_1307.md`,
`project_state_1307.md` (both 2026-07-13)._

## 🧭 Branch HEADs reviewed (fetched 2026-07-22)

| Repo                 | `test` HEAD             | `agent-skill` HEAD          | skill-validate CI                      |
|----------------------|-------------------------|-----------------------------|----------------------------------------|
| atrium-project (hub) | `8b66c83` (07-22 13:27) | — (hub has no skill branch) | reusable `skill-validate.reusable.yml` |
| page-classification  | `ef26347` (07-22 13:31) | `9526f42` (07-22 11:23)     | ✅ green (run #2)                       |
| alto-postprocess     | `bf75aef` (07-22 13:28) | `9be447b` (07-22 11:14)     | ✅ green (run #3)                       |
| nlp-enrich           | `12fd042` (07-22 13:3x) | `49daede` (07-22 11:12)     | ✅ green (run #4)                       |
| translator           | `68f491e` (07-22 13:31) | `c14cf3c` (07-22 09:49)     | 🟡 re-pushed, green expected¹          |
| llm-enrich           | `ea93f28` (07-22 13:30) | `50aef70` (07-22 09:50)     | 🟡 re-pushed, green expected¹          |

¹ pc/alto/nlp skill-validate confirmed `success` on their 07-22 HEADs; translator & llm-enrich were
re-pushed in the same 07-22 window (09:49/09:50) against the now-working reusable, so the 07-18
timing failure no longer applies — not individually CI-confirmed in this pass.

---

## Part A — `test` branch HEADs (issue #10 continuation)

### A.1 Validation matrix (re-run 2026-07-22, isolated worktrees)

| Repo | compileall | ruff | Δ vs 2026-07-13 |
|---|---|---|---|
| page-classification | OK | All checks passed | — |
| alto-postprocess | OK | All checks passed | version 0.20.2 → **1.0.0-beta** |
| nlp-enrich | OK | All checks passed | — |
| translator | OK | All checks passed | — |
| llm-enrich | OK | **All checks passed** | was 3 findings (B905/W292) → **fixed** in v0.2.0 |
| project (hub) | OK | (no ruff cfg) | +issue #31 skill workstream, e2e smoke scripts |

The whole ecosystem is Tier-1 green, and llm-enrich's three residual ruff findings from the 07-13
audit are closed (the v0.2.0 "Fable review" release). The `code-review` findings that were still
open on 07-13 are otherwise unchanged in kind.

### A.2 Version / release / shared-code state

- **Versions (CITATION == `para_config.txt [tool] version`, verified all 5):** pc `1.5.1-beta`,
  alto **`1.0.0-beta`**, nlp **`0.16.2`**, translator `0.8.1`, llm-enrich **`0.2.0`**. The
  in-repo version *sources* agree in every repo; the mismatch is between nlp's source and its
  published git tag (T3 below).
- **Recent releases (checked this pass on pc / nlp / translator; alto / llm checked earlier):**
  pc latest `v1.5.1-beta` (07-15), translator latest `v0.8.1` (07-15) — both match CITATION.
  nlp published a **new release 2026-07-22** but as **`v1.16.2`** while the source declares
  `0.16.2` (T3). alto latest `v1.0.0.-beta` (07-16, malformed — T1), llm-enrich `v0.2.0` (07-15).
- **Shared-code parity still exact.** `atrium_paradata.py` (598 ln), `para_licenses.py` (194 ln)
  and `tests/test_para_licenses.py` are sha256-identical across all five test branches and equal
  to the hub canonical `docs/templates/shared/*`. `para-drift` enforcement held through alto's
  1.0.0 bump. (Hashes match the 07-13 audit exactly.)

### A.3 New findings on `test` (this pass)

| ID | Sev    | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Evidence                                             |
|----|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| T1 | P1     | **alto release tag malformed** — the tag/release is `v1.0.0.-beta` (stray dot before `-beta`); CITATION is clean `1.0.0-beta`. Breaks tidy `vX.Y.Z-beta` sorting and any tag-regex tooling.                                                                                                                                                                                                                                                                  | `refs/tags/v1.0.0.-beta` @ `b160aaa`                 |
| T2 | P2     | **llm-enrich `date-released` stale** — CITATION says `2026-07-01` (the 0.1.0 date) but v0.2.0 shipped `2026-07-15`. Same F2-class drift the June review flagged for translator/alto, now recurring on the newest repo.                                                                                                                                                                                                                                       | `llm-enrich CITATION.cff` on `test`                  |
| T3 | **P1** | **nlp release mistagged — wrong major version.** The 2026-07-22 release is tagged **`v1.16.2`** but the repo's own version source says **`0.16.2`** (`CITATION.cff` and `para_config.txt [tool]`). So the published tag jumped `0.16.1 → 1.16.2` for a patch-level change (dep bumps + annotator folder + api_3/4 config-ref fixes). `date-released` is now fresh (`2026-07-22`), so the old code-ahead-of-release gap is closed — but a mistag replaced it. | tag `v1.16.2` @ `b93ce70` vs `test` version `0.16.2` |
| T4 | P2     | **Release/tag version-consistency check is not catching T1/T3.** `security.reusable.yml` is meant to validate tag == CITATION == `para_config`; two malformed tags reached publication (alto `v1.0.0.-beta`, nlp `v1.16.2`). Either the check doesn't run on the release job or its tag-normalisation is too loose.                                                                                                                                          | pattern across alto + nlp                            |

Everything else from the 07-13 plan (Thread-G alto test-dep under-declaration; nlp C4
`summarize_nt_udp` `build_parser`; `fail_under` gates unset; gitleaks not adopted) remains **open
and unchanged** — no regressions, no new closures on those items.

---

## Part B — `agent-skill` branch HEADs (issue #31, NEW review dimension)

### B.1 What these branches are

Per-repo **slimmed deployment branches** that wrap each service's API as an installable **Agent
Skill** (the [agentskills.io](https://agentskills.io) open standard). Each strips the dev surface
(tests, `tools/`, large sample/model data — pc's diff drops ~1.1M lines) and keeps only: minimal
runnable code, a `SKILL.md`, a **zero-dependency** stdlib client under `scripts/`, a FastAPI
`service/` + `service/README.md`, and a single `skill-validate.yml` CI caller. Driven by hub issue
**#31** (opened 2026-07-17) with pc as the exemplar (its own issue #26).

### B.2 Skill-contract validation (re-run 2026-07-22, isolated worktrees)

| Repo                | compileall | SKILL.md frontmatter | zero-dep client (`python3 -I --help`) | client                          |
|---------------------|------------|----------------------|---------------------------------------|---------------------------------|
| page-classification | OK         | ✅ name+desc (329 ch) | ✅ stdlib-only                         | `scripts/atrium_classify.py`    |
| alto-postprocess    | OK         | ✅ name+desc (441 ch) | ✅ stdlib-only                         | `scripts/atrium_postprocess.py` |
| nlp-enrich          | OK         | ✅ name+desc (374 ch) | ✅ stdlib-only                         | `scripts/atrium_enrich.py`      |
| translator          | OK         | ✅ name+desc (432 ch) | ✅ stdlib-only                         | `scripts/atrium_translate.py`   |
| llm-enrich          | OK         | ✅ name+desc (471 ch) | ✅ stdlib-only                         | `scripts/atrium_keywords.py`    |

- **Zero-dependency client contract holds** across all five: each client runs `--help` under
  `python3 -I` (isolated mode, no site-packages) — proving no torch/httpx/fastapi import leak.
- **SKILL.md valid** everywhere: `name` (= repo slug, matches `^[a-z0-9-]+$`) + `description`
  (329–471 chars, well under the 1024-char standard limit), no stray top-level keys.
- **Correct CI scoping:** the skill branches carry **only** `skill-validate.yml`; they correctly
  dropped `para-drift.yml`/`docker.yml`/`pre-commit.yml` etc. that would fail on a test-stripped
  branch.

### B.3 Findings on `agent-skill` / issue #31

| ID | Sev           | Finding                                                                                                                                                                                                                                                                                                                                                                                    | Evidence                                       |
|----|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| S1 | P1 → resolved | **Hub #31 digest headline is stale.** It states "first CI run stale-failed … needs a rerun" and "delivered as files, not pushed." In reality all five branches were **pushed 2026-07-22** and skill-validate is now **green** (pc/alto/nlp confirmed `success`). The digest predates the successful push wave by hours and should be updated to "landed + green."                          | GH Actions runs 07-22; branch HEAD dates 07-22 |
| S2 | P2            | **Manual drift model is the standing risk.** Skill branches are hand-synced from default/test (decision #5, no auto forward-merge). `skill-validate` catches *contract* breakage on push, but not silent divergence of the copied `service/` business logic from the evolving `test` branch. The `para-drift` guarantee does **not** extend here (shared trio is stripped with the tests). | `plans/31.plan.md` §5; branch anatomy          |
| S3 | note          | The 07-18 first CI failures (all 5) were a **workflow-timing artifact**, not a code defect: caller workflows were pushed ~11:5x UTC before the reusable landed on hub `test` at 17:35 UTC, so `uses: …@test` didn't resolve. Fully resolved by the 07-22 re-push.                                                                                                                          | run #1 vs #2 `referenced_workflows` sha        |

### B.4 Issue-tracker delta since `project_state_1307` (07-13)

- **NEW hub #31** — "AGENT SKILL — based on API service to each repo" (Q3 WP8/WP7); the driver of
  all five `agent-skill` branches and the hub `skill-validate.reusable.yml`.
- **pc #26** — "agent skill branch for page classifier prediction" — the exemplar origin.
- No issues closed on the tool repos since 07-13; alto still 5 open, nlp 5, pc 2, translator 1,
  llm-enrich 1, hub 14 (now including #31).

---

## ✅ Headline verdict

Both branch families are **healthy and aligned with their governing plans**, and the two-week gap
since the last review was productive rather than drifting:

1. **`test` branches**: Tier-1 green ecosystem-wide, shared-code parity exact, llm-enrich's ruff
   debt cleared, alto promoted to 1.0.0-beta. The new findings are **release-hygiene**, and two
   of them are now P1: **malformed published tags** in alto (`v1.0.0.-beta`) and nlp (`v1.16.2`
   vs a `0.16.2` source) that the tag-consistency check let through (T4), plus a stale
   llm-enrich `date-released` (T2). Code quality itself is clean; the release *plumbing* is the
   weak spot this round.
2. **`agent-skill` branches**: the issue #31 Agent-Skill rollout is structurally complete and
   functionally verified — all five compile, expose a valid SKILL.md, ship a proven zero-dep
   client, and (3/5 confirmed) pass skill-validate CI. The main correction is documentary: the
   hub #31 digest's "CI failing / not pushed" headline is stale — the branches are pushed and
   green as of 2026-07-22.

**Recommended actions:** (1) **Re-tag the two bad releases** — delete/retag alto `v1.0.0.-beta`
→ `v1.0.0-beta` and nlp `v1.16.2` → `v0.16.2` so tags match their CITATION sources; (2) **harden
the release gate** — make `security.reusable.yml` fail the release job when the tag doesn't match
`CITATION`/`para_config` exactly (T4); (3) fix llm-enrich `date-released` (T2); (4) update
`plans/31.plan.md` + `digests/31.digest.md` status to "landed + CI green (2026-07-22)"; and
(5) note in `plan_repo_review.md` that shared-code (`para-drift`) parity is guaranteed on
`test`/default only, not on the slim `agent-skill` branches.
