# 🔎 ATRIUM cross-repo state — 19 November 2026: Ronald's answers, the pilot's dates

> _Supersedes [`project_state_1211.md`](project_state_1211.md) where they differ; the contract of 12 November stays
> the base (D1–D36, H1–H15 as numbered there). Sources: the seven `test` heads of 11-19, every open issue's thread
> (exports regenerated where behind), and the ARÚP issues they link: ARUP-CAS/aiscr-docs-pipeline (#13, #15, #17,
> #18–#20), ARUP-CAS/aiscr-atr PR #5, ARUP-CAS/aiscr-webamcr (#3570, the storage contract `9e62a43`). The CAA
> manuscript of 11-19 is checked in [`13.findings.md`](13.findings.md). Nothing was posted or pushed._

## §0 — What changed since 12 November

| Topic                    | 12-11 (the contract)                      | 19-11                                                                                                           |
|--------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| Confirmations (D20, D24) | Kate's and Ronald's answers due by 16 Nov | both in: Kate 11-12 (#84), Ronald 11-17 (aiscr-docs-pipeline#17), accepted by motyc                             |
| Implementation           | the contract on paper                     | record 2.0, paradata 3.0, docproc route on every `test` (#86–#92 and the tools' PRs); `v1` = `02cbd01`          |
| E2E                      | lanes on record 1.0                       | both lanes green on the `:test` images (11-19); keyword-extract's live lane green                               |
| Page categories (D33)    | an optional weak signal for the ATR       | **not sent** (Ronald, ask 6; motyc agreed)                                                                      |
| Handwriting              | a marker asked of the ATR (ask 8)         | **no separate type**: read as a text block; detection later, untested                                           |
| Coordinate space (D28)   | to approve                                | approved; the ATR's text-layer fast path still MediaBox without `/Rotate`/`UserUnit`, fixed in the open variant |
| docproc schema           | ARÚP's, aligned on #84                    | the open ATR's draft (aiscr-atr PR #5) diverges from the docproc on `test`; to align on #17                     |
| doc-schema-v2's release  | once proven (D12)                         | after the pilot run on the cluster (AMČR's storage contract); the cluster in 2/2027                             |
| AMČR samples (#16)       | not approved in two repositories          | replaced (digital-convert#15, keyword-extract#7); git history stays (motyc)                                     |
| Spreadsheets (dc#9)      | text cells only                           | every non-empty cell, as the sheet displays it (motyc 11-18; ocr-postprocess#16, digital-convert#14, #92)       |
| CAA paper (#13)          | R1–R16 with Fallback texts                | the gated texts entered (motyc, 11-19); Figure 2 replaced; Figure 1 to redo                                     |

## §1 — Heads, releases, pins (11-19)

| Repository          | `test`    | `main` / `master`                     | Last release (date)                              | Commits since | Pilot starting set |
|---------------------|-----------|---------------------------------------|--------------------------------------------------|---------------|--------------------|
| atrium-project      | `a7e440b` | `main` = `test`                       | —; `v1` = `02cbd01`, `doc-schema-v1` = `544298b` | —             | —                  |
| digital-convert     | `88137dd` | `main` = `test`                       | `v1.4.7-beta` (11-08)                            | 13            | `v1.4.4-beta`      |
| ocr-postprocess     | `fac15d4` | `master` = `test`                     | `v1.15.4-beta` (11-06)                           | 21            | `v1.15.3-beta`     |
| page-classification | `340be2d` | `master` = `1e80e7a`                  | `v1.14.2-beta` (11-08)                           | 17            | `v1.12.3-beta`     |
| nlp-enrich          | `c5c9525` | `master` = `test`                     | `v1.3.4-beta` (11-06)                            | 14            | `v1.3.3-beta`      |
| keyword-extract     | `8508e2f` | `master` = `test`                     | `v1.6.5-beta` (11-06)                            | 22            | `v1.6.4-beta`      |
| translator          | `3b966c5` | `master` = `test`; `main` = `e6c35ee` | `v1.7.8-beta` (11-06)                            | 18            | `v1.7.5-beta`      |

All six tools call the hub's workflows at `02cbd01` (`v1`). Every tool declares the unreleased `2.0.0-beta`
(`CITATION.cff`, `para_config`); no release carries record 2.0 yet. Tagged, not released: digital-convert
`v1.4.3-beta`, `v1.4.6-beta`; ocr-postprocess `v1.13.0-beta`; page-classification `v1.14.0-beta`, `v1.14.1-beta`;
keyword-extract `v1.6.3-beta` (and the mistyped `v1.6.3.-beta`); translator `v1.7.3-beta`, `v1.7.4-beta`,
`v1.7.6-beta`, `v1.7.7-beta`.

## §2 — Decisions moved by Ronald's answers (11-17)

| #   | Decision                                                               | Status on 19-11                                                            |
|-----|------------------------------------------------------------------------|----------------------------------------------------------------------------|
| D9  | run data to paradata; routing stays in the output                      | confirmed (ask 3)                                                          |
| D13 | a failed job writes nothing                                            | confirmed for `all_engines_failed` and fallback pages (asks 9, 11)         |
| D20 | two levels: docproc the shared layout contract; ocr-postprocess builds | confirmed (asks 1, 2)                                                      |
| D24 | no stored ALTO                                                         | confirmed (ask 1)                                                          |
| D27 | the forced pages echoed                                                | the open variant only; the current service forces whole documents (ask 5)  |
| D28 | one coordinate space                                                   | approved; the fast path fixed in the open variant, checked in #20 (ask 10) |
| D29 | every page in routing                                                  | confirmed (ask 4)                                                          |
| D30 | the docproc schema in aiscr-docs-pipeline under an ARUP-CAS identifier | confirmed (ask 2); the open variant states its version in `/info`          |
| D32 | cloud fallback off                                                     | confirmed (ask 11)                                                         |
| D33 | page categories a weak signal for the ATR                              | **resolved: not sent** (ask 6)                                             |

## §3 — ARÚP's issues that ÚFAL's work depends on

| Issue                                      | What it holds (19-11)                                                                                                                                         |
|--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| aiscr-docs-pipeline #2–#7                  | one step each; the bodies predate #12's route: #2 "a category for every page", #3 and #5 ALTO, `needs_ocr`, `/convert`; #6 statistical keywords in nlp-enrich |
| aiscr-docs-pipeline #11–#14                | Temporal (#11), routing and the ATR connector (#12), the AMČR interface (#13), Docker compose then the cluster (#14)                                          |
| aiscr-docs-pipeline #15                    | the pilot batch and its dates (§5); motyc's GPU question open                                                                                                 |
| aiscr-docs-pipeline #17                    | the docproc contract; Ronald's answers 11-17; the open variant's "will not emit" list asked                                                                   |
| aiscr-docs-pipeline #18, #19, #20          | PCSS page geometry; the one-time PCSS ALTO → docproc conversion; the benchmark (PCSS against the ATR, two docproc producers)                                  |
| aiscr-atr #2, PR #5                        | the open ATR; PR #5's draft schema (open; motyc's review of 11-18 unanswered)                                                                                 |
| aiscr-webamcr #3570                        | `metadata-en`; AMČR's XPath list not posted; criterion 3 still says "translation licence" (motyc 11-12: SHA-512 and the components' terms)                    |
| aiscr-webamcr #2590                        | the licence AMČR moves its records to (#78's licence question)                                                                                                |
| aiscr-webamcr `9e62a43` (storage contract) | record 2.0 released after the cluster run; KeyBERT the keyword default; LINDAT's terms before production                                                      |

## §4 — Open issues and what each waits for

| Repository / issue                                                                   | Waits for                                                                                        |
|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| hub #84 doc-schema-v2                                                                | the open ATR's schema aligned (#17); the cluster run, then the tag                               |
| hub #13 CAA paper                                                                    | Figure 1; the findings; word count; versions; motyc's confirmation; submission by 30 Nov         |
| hub #16 storage locations                                                            | the dc#5 attachments, the Galaxy test images, the copies not named (meeting); a living reference |
| hub #6 licences                                                                      | `licences.md` rewritten (one PR)                                                                 |
| hub #40 CI                                                                           | branch protection; the CI-trigger cleanup (one PR per repository; three schedules to ask)        |
| hub #77 pilot handover                                                               | the release batch; the pilot's acceptance                                                        |
| hub #67                                                                              | closes with #77                                                                                  |
| hub #78 LINDAT                                                                       | written terms before production; Q14                                                             |
| hub #22, #24, #10, #83                                                               | after the pilot (research, umbrella, advisory CI, decision models)                               |
| hub #4, #17 SSHOMP                                                                   | `13eHAZ`; motyc's `0xSpVP` update                                                                |
| hub #15 IJDL, #56 DOG, #66 Galaxy, #79 docs                                          | no change this round; #66 parked, #79's steps follow #84                                         |
| digital-convert #9                                                                   | done and answered; closing is motyc's                                                            |
| digital-convert #5                                                                   | samples replaced (#15); motyc 11-10: can close after the meeting                                 |
| digital-convert #8, ocr-postprocess #10, page-classification #58, keyword-extract #3 | parked with #83                                                                                  |
| ocr-postprocess #14                                                                  | the open ATR's emit list (#17); Ronald's real samples                                            |
| ocr-postprocess #4, nlp-enrich #7, #18, keyword-extract #2                           | after the pilot                                                                                  |
| translator #61                                                                       | done (`master` = `test`); closing is motyc's; a release-notes line                               |

## §5 — The pilot's dates (aiscr-docs-pipeline#15, Ronald 11-17)

| When           | What                                                                      |
|----------------|---------------------------------------------------------------------------|
| 27 Nov         | orchestration skeleton and the first step on Temporal                     |
| 30 Nov         | Docker compose, first steps; the CAA submission                           |
| 4 Dec          | the AMČR interface; the routing step and the ATR connector                |
| 11 Dec         | Docker compose with all services                                          |
| 18 Dec         | all steps                                                                 |
| Christmas      | first version (S2)                                                        |
| 12/2026–1/2027 | pilot batch and its evaluation; the open ATR published (12/2026)          |
| 2/2027         | the move to the cluster; then the proof gate's last leg and doc-schema-v2 |

## §6 — Questions batched for the next meeting (not posted)

1. **The open ATR's draft schema** (aiscr-atr PR #5) against the docproc on `test`: block `id`, `cellGrid`, the
   inter-block links, one list of names; and the list of what the open variant will not emit (#84 Q24).
2. **Rotated or cropped mixed documents** fail until the open variant measures the displayed page
   (`coordinate_mismatch`): accepted for the pilot batch, or kept out of it (#84 Q25)?
3. **The step issues' bodies** (aiscr-docs-pipeline #2, #3, #5, #6) still describe the route before #12: updated by
   ARÚP, or read through #12?
4. **aiscr-webamcr#3570:** AMČR's XPath list; criterion 3's "translation licence" worded as motyc read it (D2, D34).
5. **The release batch:** `v2.0.0-beta` in every tool, with curated notes, before compose on 30 November (#77).
6. **CI triggers** (#40): drop the non-security schedules; `lindat-daily`, `controlled-live`, `vocab-refresh`; the push
   triggers beside the PR triggers.
7. **Figure 1's "also handles handwriting"** against Ronald's ask 8 (#13, motyc).
8. **LINDAT** (#78): who drafts the written terms; Q14 (D35 in the pilot).
9. Carried from 11-16: Q15, Q17–Q23 in the [#84 plan](../plans/84.plan.md#questions).

## §7 — Gaps against the working agreement (recorded, not fixed)

- **Scheduled CI** in all seven repositories beyond `codeql` and `security` (#40, table in its digest).
- **`docs_site/ecosystem/licences.md:44-75`** still presents the calculated licence field (#6).
- **Wording that has page classification route pages:** page-classification `README.md:5`, `CITATION.cff:7`;
  ocr-postprocess `README.md:96` (#84, later PRs).
- **Log pairs of closed issues** removed on 11-19 per the 10-21 rule: hub #51, #72, #81, #82; digital-convert #2,
  #3, #4, #6; ocr-postprocess #1, #2, #6, #8; nlp-enrich #41, #42; keyword-extract #1; translator #4, #52.

---
_Derived reading aid; the issues, the contract and the code are the source of truth._
