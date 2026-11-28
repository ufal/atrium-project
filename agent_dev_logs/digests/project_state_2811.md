# 🔎 ATRIUM cross-repo state — 28 November 2026: v2.0.0-beta released

> _Supersedes `project_state_1911.md` where they differ. Sources: the seven `test` heads and tags of 11-28, the six
> release runs and releases, every open issue's thread (exports of 11-28 11:11, none behind), and #84's comments 6
> (K4TEL, 11-25) and 7 (motyc, 11-27: ARÚP's answers). Nothing was posted or pushed._

## §0 — What changed since 19 November

| Topic                 | 19-11                                   | 28-11                                                                                                 |
|-----------------------|-----------------------------------------|-------------------------------------------------------------------------------------------------------|
| Releases              | `2.0.0-beta` declared, unreleased       | all six tools released as `v2.0.0-beta` (11-28), on their `test` heads, images certified              |
| Hub pins (`v1`)       | `02cbd01`                               | `ff0a8ea` (#95's merge), called by commit from all six tools                                          |
| Route decisions (#84) | the agreed route                        | ARÚP's answers (comment 7) implemented and released: 1(c), 2(b), 3(b), 4(b), 5(a) with a change, 6(c) |
| Page categories       | the pages forced to the ATR             | forced ∪ pages with `figure` blocks; the caller selects, page-classification records `page_selection` |
| Office documents      | never to the ATR (11-25)                | a page holding only a picture goes to the ATR (the PDF rule); the rendered PDF named, not stored      |
| docproc routing       | `graphics`, `tables` keys (11-25)       | dropped; pictures, charts and drawings are `figure` blocks (no `imageRef`)                            |
| Batch paradata        | paths in `config`                       | settings and models only; files by name and SHA-512 as `inputs`/`outputs`; SHA-512 everywhere         |
| Samples               | made from the release-prep code (11-25) | regenerated on the cluster from the release code; the chain sample `CTX000000003` through four tools  |
| E2E                   | both lanes green on `:test`             | not yet run on the merged or released images; the digital lane red on pre-merge `:test` since 11-25   |
| doc-schema-v2         | after the pilot run on the cluster      | untagged; the question whether to tag before the cluster run is drafted for motyc                     |

## §1 — Heads, releases, pins (11-28)

| Repository          | `test` = tag | Default branch                          | Release (published, UTC)        | Release run   |
|---------------------|--------------|-----------------------------------------|---------------------------------|---------------|
| atrium-project      | `becdaeb`    | `main` = `ff0a8ea` = `v1` (1 behind)    | —; `doc-schema-v1` = `544298b`  | —             |
| digital-convert     | `27f94a5`    | `main` = `test`                         | `v2.0.0-beta` (11:52)           | 46141418199   |
| ocr-postprocess     | `6008e0c`    | `master` = `test`                       | `v2.0.0-beta` (11:44)           | 46140643800   |
| page-classification | `9d5f4b8`    | `vit` = `test` (`master` = `1e80e7a`)   | `v2.0.0-beta` (11:47)           | 46140784765   |
| nlp-enrich          | `328da74`    | `master` = `test`                       | `v2.0.0-beta` (11:44)           | 46140962382   |
| translator          | `a2559aa`    | `master` = `test` (`main` = `e6c35ee`)  | `v2.0.0-beta` (11:49)           | 46141127255   |
| keyword-extract     | `e93cc67`    | `master` = `test`                       | `v2.0.0-beta` (12:03)           | 46141283279   |

- Each tool's tag is its #84 PR's squash merge plus a CITATION date commit (`date-released: 2026-11-28`);
  `service/openapi.json` and `para_config.txt` read 2.0.0-beta.
- Every release run green: tests, smoke builds, build-and-push with Trivy, the CVE gate and the promotion to the
  scanned digest, the OpenAPI checks, the release with `images.json` and `openapi.json` (and per-tool bundles).
- The schema blob `4e080e8` (record 2.0) is the same at `ff0a8ea`, `becdaeb` and in all six tags.

## §2 — #84's six decisions as released

| # | ARÚP (comment 7)                                      | Where it is                                                                                                                                |
|---|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | (c) settings in `config`, files as entries            | shared `add_input_files`/`add_output_files`; every batch CLI and shell stage; `start --config-name` gone                                   |
| 2 | (b) SHA-512 everywhere                                | the translator's vocabulary, keyword-extract's prompt template as input entries; no copied SHA-256                                         |
| 3 | (b) a page holding only a picture goes to the ATR     | digital-convert (no line outside header/footer + a picture); ocr-postprocess's keep-native withdrawn                                       |
| 4 | (b) forced ∪ graphics pages, the rule in `parameters` | shared `atrium_page_selection`; page-classification's `page_selection` and its statement                                                   |
| 5 | (a) with a change: named, not stored                  | digital-convert names `rendered-pdf` `stored: false` for every office document; page-classification reads it so                            |
| 6 | (c) blocks, not routing keys                          | digital-convert's `figure` blocks (`bbox`, drawings boxed on the rendering, `figures_without_box`); the proposal schema relaxes `imageRef` |

## §3 — Open, in order

1. Both hub E2E lanes on `test` with `image-tag=2.0.0-beta`; Hub Self-Check on `test` (`becdaeb`).
2. The chain sample re-run on the cluster at the four tools' tags (its paradata now name the PR heads); a small hub
   PR replacing `fixtures/chain/CTX000000003`.
3. The summary for motyc on #84, with the `doc-schema-v2` question: tag now on the validator, the lanes and the chain
   sample, the full D12 cases following on the assembled pipeline (2/2027), or wait. Drafted, not posted.
4. digital-convert#9: points 2 and 5 as released; the close. Drafted, not posted.
5. After a yes on `doc-schema-v2`: the tag on the hub commit that carries the 2.0 schema, then the freeze commit
   (frozen copy, MANIFEST row, `FREEZES[2]`, MAJOR 2 out of `PENDING_FREEZES`), re-vendor, re-pin.

## §4 — Open issues and what each waits for

| Repository / issue                                                                   | Waits for                                                                          |
|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| hub #84 doc-schema-v2                                                                | the lanes and the chain at the tags; motyc's answer on the tag (§3)                |
| hub #77 pilot handover                                                               | the releases are out (11-28); the pilot's acceptance                               |
| hub #67                                                                              | closes with #77                                                                    |
| hub #40 CI                                                                           | branch protection; the schedules ended with the release merges                     |
| hub #13 CAA paper                                                                    | no comment since 11-24; submission by 30 Nov                                       |
| hub #6, #16, #78, #79                                                                | no change since 11-19 (#79: the docs follow the releases)                          |
| hub #22, #24, #10, #83                                                               | after the pilot (research, umbrella, advisory CI, decision models, parked)         |
| hub #4, #17 SSHOMP; #15 IJDL; #56 DOG; #66 Galaxy                                    | no change; #66 parked                                                              |
| digital-convert #9                                                                   | released in v2.0.0-beta; the decisions comment, then the close                     |
| digital-convert #5                                                                   | motyc 11-10: can close after the meeting                                           |
| digital-convert #8, ocr-postprocess #10, page-classification #58, keyword-extract #3 | parked with #83                                                                    |
| ocr-postprocess #14                                                                  | the open ATR's emit list (aiscr-docs-pipeline#17); real ATR samples                |
| ocr-postprocess #4, nlp-enrich #7, #18, keyword-extract #2                           | after the pilot                                                                    |

Translator #61 was closed on 11-25 (its export removed); the translator has no open issue.
