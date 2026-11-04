# 🔎 ATRIUM cross-repo state — the pilot set released (2026-11-04)

> _Supersedes [`project_state_3009.md`](project_state_3009.md), written before the 10-01 repository split. Read on
> 2026-11-04 between 11:20 and 13:10 UTC: the remote heads, releases, workflow runs and issues of the seven
> repositories, through the GitHub API and `git ls-remote`. Nothing was changed on GitHub. Detail per issue:
> `digests/{n}.digest.md` and `plans/{n}.plan.md`; history: `DEVLOG.md`._

## §0 — What changed since 30 September

- **The split (10-01):**
  - alto-postprocess became **ocr-postprocess**;
  - llm-enrich became **digital-convert** (the born-digital stage);
  - the keyword stage left nlp-enrich and llm-enrich for **keyword-extract**.

  Six tool repositories and the hub.
- **Release trust (#72):** a `v*` tag ruleset and immutable releases in all six; each release certifies its images by
  digest in `images.json` (#81); the hub's reusables are called by commit (`require-sha-pins`).
- **The licence change (#6, step 1):** a crate's root names `#no-licence-asserted`; a record marks its calculated
  value `provenance.license_basis: "calculated"`.
- **Documentation (#79):** phases A–C and F; E runs advisory in CI.
- **The pilot set (#77):** final on 11-04.

## Heads, pilot releases and pins

| Repository          | Default branch | Pilot release (commit)    | `-api` digest (`images.json`)                                             | Hub pin                |
|---------------------|----------------|---------------------------|---------------------------------------------------------------------------|------------------------|
| page-classification | `vit`          | `v1.12.3-beta` (`0a96bce`) | `sha256:715258bee1e2f2b5dc8a8b75a2b8bcebdb25be59a12b4239175af8c5dcfd7395` | `51aad6c` (sweep 11-04) |
| ocr-postprocess     | `master`       | `v1.15.3-beta` (`9ab887a`) | `sha256:2240b39eeb0c41d8aa2c32d127e26afa64c9d83bba10e68cac251ce3f68351f0` | `51aad6c` (sweep 11-04) |
| digital-convert     | `main`         | `v1.4.4-beta` (`fac54b1`)  | `sha256:57ebac40ee78dcc5dbe7e0b8d862a23d81f6f2d91c3ad3994980c829b0c38cdb` | `51aad6c`              |
| nlp-enrich          | `master`       | `v1.3.3-beta` (`b0e80ca`)  | `sha256:c6771de5b988a23d75b75a227125be2eac527b1bc016606c41c66aa6afc89538` | `51aad6c` (sweep 11-04) |
| keyword-extract     | `master`       | `v1.6.4-beta` (`0d5a2f3`)  | `sha256:26f87f5ad23415e4fc20f9ef768a4453a2e4346f58f41b1b67ac613f3368c018` | `51aad6c`              |
| translator          | `master`       | `v1.7.5-beta` (`17e2832`)  | `sha256:c2ccb0c94d0428c312dec62c8c0b4fb09a8b5c9188b49f5326534f803ed72b5d` | `51aad6c`              |
| hub                 | `main`         | no releases; `v1` = `51aad6c` | —                                                                      | —                      |

All six pilot releases are immutable and carry `images.json` (read 11-04). In each tool `test` equals the default
branch. The sweep marked "11-04" is prepared in this afternoon's files; until it is pushed, those three still call
`14110d7`.

**Tags without a release:**
- digital-convert `v1.4.3-beta`: no run;
- keyword-extract `v1.6.3-beta` (CVE gate, registry error) and `v1.6.3.-beta` (mistyped);
- translator `v1.7.3-beta` (Trivy download) and `v1.7.4-beta` (no run).

The next patch number shipped the same code. `docs/release_trust.md` § State on 2026-11-04 lists them.

## CI

- Every push run on the pilot commits is green, para-drift included.
- **One flake:** translator CodeQL 41819773270 on `master` (upload, disk space). The same commit passed on `test`.
- **The fix for ocr-postprocess#9 holds:** the dispatched `scheduled-smoke` 41821703975 is green with scipy 1.17.1 and
  numpy 2.4.6. No lane-failure issue is open in any repository.
- **E2E: not yet run on the final set.**
  - The pipeline smoke of 10:29 (`main`, `5c25d32`) ran on `:latest` while translator's pointed at the unreleased
    `1.7.3-beta` image.
  - The digital lane's last run (06:10) used digital-convert `1.4.2-beta`.
  - Hub `main` has no runs for `51aad6c` or `91e1223`.
- **Hardening of 11-04 (#81):** the report-only scan's retry waits 30 s (`5c25d32`); the CVE gate runs once more after
  30 s, blocking (`51aad6c`).

## Open issues and what each waits for

| Issue | Owner | Waits for |
|---|---|---|
| hub #4 SSHOMP records | AMČR; ÚFAL its own | the two workflow records; `0xSpVP` (#17); the versions are entered (11-04) |
| hub #6 Licences | motyc, K4TEL | motyc on step 1 (11-04); box 1 to tick; box 2 with #78; GLM-4 terms; ufal/flexiconv#1 |
| hub #10 LLM validation | — | deferred after the pilot |
| hub #13 CAA paper | the authors | motyc's check of v31 and the three §3.2 questions; JCAA guidelines; APCs; deadline 30 Nov |
| hub #15 IJDL / new submission | AMČR | the venue (IJDAR or ACM JOCCH), not chosen |
| hub #16 Data locations | AMČR | a living reference until the project ends |
| hub #17 SSHOMP workflows | motyc | the `0xSpVP` update |
| hub #22 Document Understanding | K4TEL | the pilot's acceptance; region types (heads-up 11-04) |
| hub #24 LLM applications | — | deferred after the pilot |
| hub #40 Branch protection, GPU runner | stranak | the hub's `main` protection; GPU later |
| hub #56 DOG / Switchboard | — | deferred after the pilot |
| hub #66 Galaxy | greenwoodma, K4TEL | the test-instance deployment; K4TEL back this week |
| hub #67 Pilot baseline | motyc | his sub-issue check; closes with #72 |
| hub #72 Production hardening | motyc | his review; then closes, with #67 |
| hub #77 Pilot handover | K4TEL, then AMČR | E2E on the final set; approval by digest on 11 Nov; acceptance; S2 from December |
| hub #78 LINDAT services | stranak | the written permission and the output terms; monitoring runs daily |
| hub #79 Documentation | david-spacil, stranak | D's notes by 11 Nov; stranak's OK on the acknowledgement |
| hub #81 CI/CD governance | motyc | closing (proposed 11-04) |
| page-classification #58 LDMs | K4TEL | annotators for track 2; track 1 can start |
| ocr-postprocess #4 quality-model fine-tuning | — | deferred |
| digital-convert #5 AMČR PDFs | — | Dana's 15 PDFs (experiments) |
| nlp-enrich #7, #18 | — | deferred after the pilot |
| keyword-extract #2 TEATER topics | — | research, deferred after the pilot |

## Pilot timeline

| Date        | What                                                                  | Who                         |
|-------------|-----------------------------------------------------------------------|-----------------------------|
| before 11-11 | both E2E lanes green on the final set, posted on #77                  | K4TEL                       |
| 11-11       | the six `-api` digests approved; LINDAT terms (#78); D's notes (#79)   | AMČR; stranak; david-spacil |
| second half of November | acceptance on AMČR's cluster                              | AMČR (@rharasim)            |
| 11-30       | the CAA paper: Zenodo, then PCI Archaeology (#13)                      | the authors                 |
| December–January | S2: AMČR runs the six services                                   | AMČR                        |
