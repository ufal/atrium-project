# 🔎 ATRIUM cross-repo state — the AMČR baseline (atrium-project#67)

**Date: 26 September 2026 · Scope: all six `ufal` repositories, `test` HEADs, every open issue**

_Successor to [`project_state_0709.md`](project_state_0709.md) (2026-09-07). Prior baselines:
[`project_state_3007.md`](project_state_3007.md), [`project_state_0208.md`](project_state_0208.md),
[`project_state_2207.md`](project_state_2207.md), [`project_state_1307.md`](project_state_1307.md),
[`project_state_2706.md`](project_state_2706.md). Covers the 19 days 09-07 → 09-26: the twelve-factor family (#53)
nearly closed, the `atrium_document` freeze (#54), GitHub Pages rounds 3–8 (#57), the born-digital converter
(llm-enrich#18), TEITOK format 2 (nlp-enrich), non-ALTO inputs (alto-postprocess#31), translator production readiness
(#46) — and, on the last afternoon, AMČR's baseline for every open issue (#67)._

---

## §0 — How this pass was made

- **Tree state** — the six local clones, whose working branch equals `origin/test` in every repository (checked by
  `git branch -a`, 2026-09-26).
- **Hub CI** — GitHub Actions runs on hub `test`, read live. The tool repositories' Actions were not reachable from
  this session; their CI state below is taken from the hub DEVLOG and marked so.
- **Issue tracker** — the issue exports in each repository's `agent_dev_logs/issues/` (regenerated 2026-09-26
  18:45) and a live check of the hub's issue list for anything newer (none after 16:40 UTC).
- **Code facts** — every `file:line` in #67's pair and in the refreshed Finish plans was read in the clones, not
  taken from earlier logs.

## 🧭 Branch HEADs and releases (2026-09-26)

| Repository                   | `test` = working branch | Latest release (CITATION.cff)   | Notes                                                                     |
|------------------------------|-------------------------|---------------------------------|---------------------------------------------------------------------------|
| `atrium-project` (hub)       | `4f65b20`               | — (tags: `v1`, `doc-schema-v1`) | `v1` = `6167803`; `doc-schema-v1` = `544298b`; `CITATION.cff` added 09-26 |
| `atrium-page-classification` | `2e27073`               | **1.8.0-beta** (09-16)          | default branch `vit`                                                      |
| `atrium-alto-postprocess`    | `bcd7e01`               | **1.6.0-beta** (09-25)          | #31 released                                                              |
| `atrium-translator`          | `f876a2f`               | **1.2.1-beta** (09-26)          | production-ready fixes (#46)                                              |
| `atrium-llm-enrich`          | `79b857d`               | **0.7.0** (09-16)               | `c3575f5` (#18) on `test`, **not released**                               |
| `atrium-nlp-enrich`          | `40c48f0`               | **0.22.0** (09-25)              | TEITOK format 2, `/enrich` table + ALTO                                   |

All 19 para-drift canonical files are in parity across the five tool repositories (hub DEVLOG 09-26, after the
freeze re-vendor); `tests/test_schema_freeze.py` is blob `7c35fbf1` in all five.

---

## Part A — What happened in this window

### A.1 The twelve-factor family (#53) — ten sub-issues, eight closed
Between 09-10 and 09-16 every factor got a sub-issue and every sub-issue landed code: #59 (I), #60 (III), #61 (XI),
#62 + alto#50 (V), #63 (IV), #64 (X), nlp#35 (VI+VIII) closed; #58 (VII) waits on its deliberate-breakage run; #55
(IX) on the partners' runbook. On 09-16 all twelve factors were green.

### A.2 The `atrium_document` freeze (#54)
The tightened schema landed on 09-09 (`required` + `anyOf`/`allOf`); the freeze tag `doc-schema-v1` was cut at
`544298b` on 09-25; on 09-26 every repository gained the frozen copy and `tests/test_schema_freeze.py`, and each
README and `CITATION.cff` names the tag. The first additive change after the freeze, `lines[].style.region`
(llm-enrich#18), went through the new rule without a version bump. A formatter pass in the hub re-wrapped the
vendored test after copying and turned para-drift red in all five tool repositories for an afternoon; fixed the same
evening (tool repos re-vendored; hub `f9bfb1b` keeps formatters off the canonical files).

### A.3 GitHub Pages (#57), rounds 3–8
All six sites serve from `gh-pages`. The hub site was rewritten from generated mirrors into written pages (rounds
3–6), gained a **Workflows** section — one narrative per tool, shaped for SSHOMP and Galaxy records (round 7) — and
had its translator section re-read at `v1.2.1-beta` (round 8). Page-classification and the translator have full tool
sections; the other three have stable-core workflow pages.

### A.4 The tools
- **llm-enrich#18** — the born-digital converter (`digital-convert`): one route, layout cues, `style.region`, the
  licence resolved from the components that ran (MIT by default); #10's G1–G8 closed. On `test`, unreleased.
- **alto-postprocess#31** — any text-bearing input (PDF, DOCX, ODT, RTF, XLSX, ODS, HTML, TEI, …) to text lines;
  released in 1.6.0-beta. #30's calibration round with @david-spacil and @DanaKriv reached 336/508 on the re-check.
- **nlp-enrich** — TEITOK format 2 (v0.21.0), the flexiconv route (#10) and annotated flexiconv documents (#38,
  v0.22.0); `/enrich` takes a table together with its ALTO layout.
- **translator#46** — v1.2.0-beta, then 1.2.1-beta: the record licence corrected to CC BY-NC-SA 4.0, `--xsd` able to
  load AMČR 2.2; AMČR 2.2 validates `replace` output (15/15) and rejects `append` (0/15).

### A.5 AMČR's baseline (#67), 2026-09-26
David (@motyc, AMČR) proposed, for the 30 September meeting, a bucket for every open issue and seven pilot requests;
fifteen thread comments carry the thread-specific asks. ÚFAL adopted it the same day and refreshed every digest+plan
pair (this pass). The requests:
1. seeded baseline record — R1;
2. `CreateAction` paradata from every service — R2;
3. record-only mode — R3;
4. `atrium_rocrate.py` aligned (RO-Crate 1.2, Process Run Crate 0.5) — R4;
5. a `keywords` block — R5;
6. a document quality summary (optional) — R6;
7. an architecture cleanup — R7.

The detail is in [`67.digest.md`](67.digest.md) and [`../plans/67.plan.md`](../plans/67.plan.md).

## Part B — CI state

| Where                     | State (2026-09-26)                                                                                                                               |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| hub `test` @ `4f65b20`    | ✅ Hub Self-Check (36256783734), pre-commit, CodeQL, Documentation Site — all green, read live                                                    |
| tool repos, para-drift    | 🔴 → ✅ red from 16:08 (the re-wrapped `test_schema_freeze.py`), fix committed 18:36–18:39 in all five; **the green re-run was not checked here** |
| E2E pipeline / digital    | ✅ green on `eec0682` (hub DEVLOG, 09-24); both still run published CLI images and start **unseeded** (#67 R1)                                    |
| translator `live-backend` | ⏳ 0 dispatches — AMČR asked for one run (#46)                                                                                                    |

## Part C — Issue tracker, by AMČR bucket (44 open)

| Bucket                       | Hub                                               | page-classification | alto-postprocess             | translator             | llm-enrich                  | nlp-enrich  |
|------------------------------|---------------------------------------------------|---------------------|------------------------------|------------------------|-----------------------------|-------------|
| 🔒 close now                 | #18, #54                                          | —                   | #31                          | #46 (after AMČR's run) | #13, #18 (with its release) | #10, #38    |
| ✅ finish (pilot)             | #6, #32, #40, #53 (after #55, #58), #55, #58, #66 | —                   | #2, #3, #4, #30 (time-boxed) | #4                     | #10                         | —           |
| 🔧 reshape                   | #10 (a bounded CI check)                          | —                   | —                            | —                      | —                           | —           |
| ⏸️ defer (after the pilot)   | #22, #24, #51, #56                                | —                   | #23                          | —                      | #11                         | #6, #7, #18 |
| ⛔ stop (outside the project) | #26, #27, #31                                     | —                   | —                            | —                      | #24, #25                    | —           |
| 🧑‍⚖️ ÚFAL decides           | #57                                               | —                   | —                            | —                      | —                           | —           |
| 🏛️ AMČR's own               | #4, #13, #15, #16, #17, #21                       | —                   | —                            | —                      | —                           | —           |
| 🧭 umbrella                  | #67                                               | —                   | —                            | —                      | —                           | —           |

**Closed since 09-07:** hub #59–#64; alto #37, #50; nlp #9, #11 (06-28, pair still on disk), #19, #28, #35; llm #8;
page-classification #48. Their pairs are removed when the issue closes; four are still on disk (nlp #11, #19, alto
#37, page-classification #48).

## ✅ Verdict

The tools are closer to a production pilot than the tracker suggested on 09-07: the record is frozen and checked in
every repository, the services share one meta-contract, and three of the five tools shipped releases this month.
What the pilot adds is **contract work across all five at once** — a seeded record, one `CreateAction` per call,
record-only merging, every limit a setting — so the next month is dominated by shared-module changes and the
re-vendor/`v1` discipline, not by per-tool features.

Two things the refresh found that the tracker did not show:
- **A seed read-back bug.** alto-postprocess and llm-enrich return the untouched seed record when the AMČR
  `doc_id` differs from the filename-derived id (#67 plan §B). Found by reading the code, not yet reproduced; it
  goes first.
- **`uses: …@v1` is not the only moving reference.** para-drift and workflow-lint check the hub out at `hub-ref`,
  default `v1`, so pinning `uses:` by commit (#40) needs a matching `hub-ref`.

## Recommended actions, in order
1. **Post** the #67 reply and the close/stop/update comments (drafts in chat); close the eight close-now issues as
   each condition is met (llm#18 after its release; translator#46 after AMČR's run).
2. **Before 30 Sept:** run #58's deliberate breakage (it gates #53); dispatch the translator's `live-backend` once;
   open the CI-roadmap issue split from #18 and the seed-bug issue.
3. **Fix the seed read-back bug** (alto-postprocess, llm-enrich), with the regression test in all five.
4. **R4 → R2 in the hub** (`atrium_rocrate.py` 1.2 / Process Run Crate 0.5, then the `CreateAction` builder), with
   rocrate-validator in CI.
5. **One additive schema round**: `source.sha512`, the seed profile, `keywords`, `quality` (optional) — one
   changelog date, one re-vendor, one `v1` move; turn on immutable releases (#40) before the tool releases that
   follow it.
6. **Per tool, in pilot order:** `api-digital` and the born-digital types (llm#10); record-only PSNC ALTO import
   (alto); limits from the environment and in `/info` (#53, all five); PyMuPDF → `pypdfium2` (#6, page-classification);
   nlp-enrich without its `llm` stage (#67 R7).
7. **Time-box** alto-postprocess #2, #3, #4, #30 — proposed 2026-10-16, to confirm on 30 Sept.
