# 🔎 ATRIUM LLM Review State — `test` + `agent-skill` branch HEADs (Corrected Edition)

**Date: 22 July 2026 · Scope: all six `ufal` repositories, two branch families**

**Status of this document: independent re-verification of `agent_dev_logs/digests/project_state_2207.md`
(as committed on the `test` branch), performed the same day against live repo state. Corrections
are marked inline with `⟳ CORRECTED` and explained in the new §0.**

_Refresh of the issue #10 (LLM source-code validation) review state, extended to the issue #31
(Agent Skill) `agent-skill` branches. Prior baselines: `project_state_1307.md` (2026-07-13). The
citation to `issue10_alignment_1307.md` carried by both `project_state_1307.md` and the original
`project_state_2207.md` is dropped here — that file does not exist on `main` or `test` in
`ufal/atrium-project`; it appears to be a dangling reference that was never actually committed._

---

## §0 — What changed in this corrected edition

The original `project_state_2207.md` is a genuine, well-sourced live audit (isolated worktrees,
sha256 checks on shared paradata files, real CI-run lookups), not a copy-paste of the prior
digest. Re-checking its own claims against the repos at the same point in time surfaced four
issues, two of which invalidate headline findings:

1. **T1 (alto malformed tag) is stale, not open.** The original digest reports alto's current
   version as `1.0.0-beta` and flags the malformed release tag `v1.0.0.-beta` as an **open P1**.
   Live `test`-branch `CITATION.cff` and `setup/para_config.txt` are already at **`1.1.0-beta`**
   (`date-released: 2026-07-22`), shipped as a cleanly-tagged `v1.1.0-beta` release
   (published `2026-07-22T13:03:50Z`) — this already supersedes and resolves T1. See §A.2/§A.3
   below, corrected.
2. **The branch-HEAD table mislabels alto.** The original table lists alto's `test` HEAD as
   `bf75aef` (07-22 13:28). That SHA is actually alto's **`master`** HEAD (confirmed via
   `list_branches`); alto's real `test` HEAD is a later commit already carrying the `1.1.0-beta`
   bump. The two branches were conflated.
3. **T2 (llm-enrich stale `date-released`) is also stale, not open.** The original digest flags
   llm-enrich's `CITATION.cff` `date-released` (`2026-07-01`) as lagging its `v0.2.0` ship date
   (`2026-07-15`). Live `test`-branch `CITATION.cff` is already at **version `0.3.0`,
   `date-released: 2026-07-22`** — a `v0.3.0` release (published `2026-07-22T13:17:52Z`) shipped
   that the original digest never mentions at all.
4. **T3 (nlp-enrich mistagged release) independently confirmed still open.** Live `test`-branch
   `CITATION.cff` reads `version: "0.16.2"`; the corresponding GitHub release is tagged
   `v1.16.2`. This finding holds and is carried forward unchanged.
5. **Visibility gap.** This document (like the original) lives only on `test`, not `main` — the
   exact blind spot the ATRIUM digests themselves have repeatedly warned about ("agents working
   from default branches lack this context"). Recommend forward-merging to `main` once reviewed.

Net effect: the ecosystem is in **better** shape than the original digest's own "New findings"
table suggested — two of four flagged issues already self-resolved via same-day releases that
outran the write-up. The corrected headline verdict is in §Verdict below.

---

## 🧭 Branch HEADs reviewed (fetched 2026-07-22)

| Repo                 | `test` HEAD                                                                                                                                                                                    | `agent-skill` HEAD          | skill-validate CI                      |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|----------------------------------------|
| atrium-project (hub) | `8b66c83` (07-22 13:27)                                                                                                                                                                        | — (hub has no skill branch) | reusable `skill-validate.reusable.yml` |
| page-classification  | `ef26347` (07-22 13:31)                                                                                                                                                                        | `9526f42` (07-22 11:23)     | ✅ green (run #2)                       |
| alto-postprocess     | ⟳ CORRECTED — later than `bf75aef`; `bf75aef` is `master`'s HEAD, carrying `CITATION.cff 1.0.0-beta`. The real `test` HEAD already carries the `1.1.0-beta` bump (`date-released 2026-07-22`). | `9be447b` (07-22 11:14)     | ✅ green (run #3)                       |
| nlp-enrich           | `12fd042` (07-22 13:3x)                                                                                                                                                                        | `49daede` (07-22 11:12)     | ✅ green (run #4)                       |
| translator           | `68f491e` (07-22 13:31)                                                                                                                                                                        | `c14cf3c` (07-22 09:49)     | 🟡 re-pushed, green expected¹          |
| llm-enrich           | `ea93f28` (07-22 13:30)                                                                                                                                                                        | `50aef70` (07-22 09:50)     | 🟡 re-pushed, green expected¹          |

¹ pc/alto/nlp skill-validate confirmed `success` on their 07-22 HEADs; translator & llm-enrich were
re-pushed in the same 07-22 window (09:49/09:50) against the now-working reusable, so the 07-18
timing failure no longer applies — not individually CI-confirmed in this pass.

---

## Part A — `test` branch HEADs (issue #10 continuation)

### A.1 Validation matrix (re-run 2026-07-22, isolated worktrees)

| Repo                | compileall | ruff                  | Δ vs 2026-07-13                                                             |
|---------------------|------------|-----------------------|-----------------------------------------------------------------------------|
| page-classification | OK         | All checks passed     | —                                                                           |
| alto-postprocess    | OK         | All checks passed     | version 0.20.2 → 1.0.0-beta → ⟳ **1.1.0-beta** (same-day follow-up release) |
| nlp-enrich          | OK         | All checks passed     | —                                                                           |
| translator          | OK         | All checks passed     | —                                                                           |
| llm-enrich          | OK         | **All checks passed** | was 3 findings (B905/W292) → **fixed** in v0.2.0; ⟳ now shipped as v0.3.0   |
| project (hub)       | OK         | (no ruff cfg)         | +issue #31 skill workstream, e2e smoke scripts                              |

The whole ecosystem is Tier-1 green, and llm-enrich's three residual ruff findings from the 07-13
audit are closed (the v0.2.0 "Fable review" release, itself now one release behind the current
v0.3.0). The `code-review` findings that were still open on 07-13 are otherwise unchanged in kind.

### A.2 Version / release / shared-code state ⟳ CORRECTED

- **Versions (CITATION == `para_config.txt [tool] version`, verified all 5):** pc `1.5.1-beta`,
  alto ~~`1.0.0-beta`~~ **`1.1.0-beta`** (⟳ corrected — see §0.1), nlp `0.16.2`, translator
  `0.8.1`, llm-enrich ~~`0.2.0`~~ **`0.3.0`** (⟳ corrected — see §0.3). The in-repo version
  *sources* agree in every repo; the mismatch is between nlp's source and its published git tag
  (T3 below).
- **Recent releases (checked this pass on pc / nlp / translator; alto / llm checked earlier, now
  re-checked):** pc latest `v1.5.1-beta` (07-15), translator latest `v0.8.1` (07-15) — both match
  CITATION. nlp published a **new release 2026-07-22** but as **`v1.16.2`** while the source
  declares `0.16.2` (T3, still open). alto's latest is now **`v1.1.0-beta`** (07-22, cleanly
  formed tag — supersedes the malformed `v1.0.0.-beta` from 07-16, T1 closed). llm-enrich's
  latest is now **`v0.3.0`** (07-22, `date-released` matches, T2 closed).
- **Shared-code parity still exact.** `atrium_paradata.py` (598 ln), `para_licenses.py` (194 ln)
  and `tests/test_para_licenses.py` are sha256-identical across all five test branches and equal
  to the hub canonical `docs/templates/shared/*`. `para-drift` enforcement held through alto's
  1.0.0 **and** 1.1.0 bumps. (Hashes match the 07-13 audit exactly.)

### A.3 Findings on `test` (this pass) ⟳ CORRECTED

| ID | Sev                   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Evidence                                                                   |
|----|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| T1 | ~~P1~~ **Resolved** ⟳ | ~~alto release tag malformed~~ — the malformed `v1.0.0.-beta` tag (07-16) has already been superseded by a cleanly-tagged `v1.1.0-beta` release (07-22). CITATION/`para_config` on `test` both read `1.1.0-beta`. No action needed beyond noting the earlier bad tag remains in the release history (harmless, superseded).                                                                                                                                                                                                                                   | `refs/tags/v1.1.0-beta` (07-22) vs. stale `refs/tags/v1.0.0.-beta` (07-16) |
| T2 | ~~P2~~ **Resolved** ⟳ | ~~llm-enrich `date-released` stale~~ — CITATION now reads `version: 0.3.0`, `date-released: 2026-07-22`, matching the `v0.3.0` release published the same day. The F2-class drift the June review flagged is not recurring here after all; the original digest simply hadn't caught the 07-22 release.                                                                                                                                                                                                                                                        | `llm-enrich CITATION.cff` on `test`, re-fetched                            |
| T3 | **P1**                | **nlp release mistagged — wrong major version.** The 2026-07-22 release is tagged **`v1.16.2`** but the repo's own version source says **`0.16.2`** (`CITATION.cff` and `para_config.txt [tool]`). So the published tag jumped `0.16.1 → 1.16.2` for a patch-level change (dep bumps + annotator folder + api_3/4 config-ref fixes). `date-released` is fresh (`2026-07-22`), so the old code-ahead-of-release gap is closed — but a mistag replaced it. **Confirmed still open on independent re-check.**                                                    | tag `v1.16.2` @ `b93ce70` vs `test` version `0.16.2`                       |
| T4 | P2                    | **Release/tag version-consistency check is not catching T3** (and did not catch the now-superseded T1 either, at the time). `security.reusable.yml` is meant to validate tag == CITATION == `para_config`; malformed/mistagged releases have twice reached publication (alto's stray-dot tag, nlp's major-version mistag). Either the check doesn't run on the release job or its tag-normalisation is too loose. This remains the real, durable finding of this section — not the individual bad tags, which age out as soon as the next release fixes them. | pattern across alto (historical) + nlp (current)                           |
| T5 | P3, new               | **The digest-writing cadence cannot keep pace with the release cadence.** Both T1 and T2 in the original 07-22 digest were already overtaken by same-day releases by the time of independent re-verification hours later. This is not a code defect, but it means any digest's "latest release" table should be treated as a lower bound, re-checked against `list_releases`/CITATION before acting on it — especially on days with multiple auto-releases in flight.                                                                                         | this re-verification                                                       |

Everything else from the 07-13 plan (Thread-G alto test-dep under-declaration; nlp C4
`summarize_nt_udp` `build_parser`; `fail_under` gates unset; gitleaks not adopted) remains **open
and unchanged** — no regressions, no new closures on those items.

---

## Part B — `agent-skill` branch HEADs (issue #31, NEW review dimension)

*(Independently spot-checked: issue #31 confirmed open on the hub tracker, opened 2026-07-17,
milestone Q3 [WP8/WP7], 3 comments; `agent_dev_logs/plans/31.plan.md` and
`agent_dev_logs/digests/31.digest.md` confirmed to exist on `test` with content consistent with
the summary below; alto-postprocess's `agent-skill` branch confirmed to exist via `list_branches`.
No corrections needed to Part B.)*

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
  all five `agent-skill` branches and the hub `skill-validate.reusable.yml`. Confirmed open,
  opened 2026-07-17.
- **pc #26** — "agent skill branch for page classifier prediction" — the exemplar origin.
- No issues closed on the tool repos since 07-13; alto still 5 open, nlp 5, pc 2, translator 1,
  llm-enrich 1, hub 14 (now including #31).

---

## ✅ Headline verdict ⟳ CORRECTED

Both branch families are **healthy and aligned with their governing plans**, and the gap since the
last review (07-13 → 07-22, nine days) was productive rather than drifting. Independent
re-verification the same day as the original digest found the ecosystem in even better shape than
the original write-up reported:

1. **`test` branches**: Tier-1 green ecosystem-wide, shared-code parity exact, llm-enrich's ruff
   debt cleared. Two of the original digest's four "new findings" (T1 alto malformed tag, T2
   llm-enrich stale `date-released`) **already self-resolved via same-day releases** (alto
   `v1.1.0-beta`, llm-enrich `v0.3.0`) that the original write-up didn't catch — not because they
   were wrong when written, but because the release cadence outran the audit cadence (see new
   finding T5). The one genuinely open release-hygiene issue is **T3**: nlp's `v1.16.2` tag vs.
   its own `0.16.2` version source. **T4** (the release/tag consistency gate not catching
   mismatches) is the durable, structural finding worth fixing — individual bad tags will keep
   recurring until it does.
2. **`agent-skill` branches**: the issue #31 Agent-Skill rollout is structurally complete and
   functionally verified — all five compile, expose a valid SKILL.md, ship a proven zero-dep
   client, and (3/5 confirmed) pass skill-validate CI. The main correction is documentary: the
   hub #31 digest's "CI failing / not pushed" headline is stale — the branches are pushed and
   green as of 2026-07-22. (No changes to this section vs. the original digest.)

**Recommended actions (updated):**
1. ~~Re-tag alto `v1.0.0.-beta` → `v1.0.0-beta`~~ — moot; superseded by the clean `v1.1.0-beta` tag.
2. **Re-tag nlp-enrich's `v1.16.2` → `v0.16.2`** so the published tag matches `CITATION`/
   `para_config` (T3, still open).
3. **Harden the release gate** — make `security.reusable.yml` fail the release job when the tag
   doesn't match `CITATION`/`para_config` exactly (T4). This is the one action that prevents this
   whole class of finding from recurring, rather than fixing it after the fact.
4. ~~Fix llm-enrich `date-released`~~ — moot; already fresh as of the `v0.3.0` release.
5. Update `plans/31.plan.md` + `digests/31.digest.md` status to "landed + CI green (2026-07-22)".
6. Note in `plan_repo_review.md` that shared-code (`para-drift`) parity is guaranteed on
   `test`/default only, not on the slim `agent-skill` branches.
7. **New:** drop the dangling `issue10_alignment_1307.md` citation from future digests (the file
   was never committed), or commit the file it's referring to if one exists outside the repo.
8. **New:** forward-merge this digest (and the original it corrects) from `test` to `main` so it
   is visible to agents that only read the default branch — the exact failure mode the ATRIUM
   digests have repeatedly flagged in themselves.
