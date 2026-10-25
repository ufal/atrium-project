# CI/CD policy

> **Status:** policy, added 2026-10-20 for [#81](https://github.com/ufal/atrium-project/issues/81).
> **Scope:** the hub's reusable workflows and lanes, and the six tool repositories' callers.
> Tag rules, immutable releases and commit pins live in [`release_trust.md`](release_trust.md); the
> current workflow set is described in [`docker_gha.md`](docker_gha.md). This page sets the rules
> for both and says what each result means.

## Tiers

| Tier            | Runs on                                    | Must be                                                                                         | Never                                                                     |
|-----------------|--------------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 1. Pull request | `pull_request`, pushes to `test`           | fast (minutes), deterministic, no secrets, no network beyond package installs                   | a GPU, a live external service, a model download that a cache cannot hold |
| 2. Integration  | pushes and dispatch on the hub, a schedule | run against a **named** set of images or revisions, and record which (image digest, source SHA) | be read as release approval when the set was moving tags                  |
| 3. Release      | a version tag `v*`                         | validate and publish one release: its source, contract assets and image                         | publish part of a release while another required part failed              |
| 4. Monitoring   | a schedule, dispatch                       | watch what changes without a commit: dependencies, published images, LINDAT and LLM backends    | block a pull request                                                      |

GPU checks are dispatch-only until a GPU runner exists (#40); the pilot does not depend on them. No
ÚFAL workflow reaches AMČR infrastructure.

## Every check has a record

A new check, or a changed one, states in its workflow header or in the map below:

- **Owner:** who fixes it when it is red. K4TEL for the tool and hub workflows unless a row says
  otherwise; repository settings (rulesets, immutability) are stranak's.
- **Guarantee:** what a failure means, in one sentence.
- **Tier and trigger.**
- **Inputs:** secrets, images, network hosts, runners.
- **Status:** blocking, advisory or optional. A blocking check is a required status in the branch ruleset
  or a `needs:` of a publishing job; advisory and optional checks say so in their job name or summary.

## What a green result means

1. **A blocking check fails if it ran nothing it is named for.** "No tests collected", a skipped
   contract module, or an empty input list is a failure, not a pass.
2. **An allowed omission is written to the job summary with its reason** (`$GITHUB_STEP_SUMMARY`), not
   only as an annotation in the log: "skipped: no committed spec", "optional: no `OPENROUTER_KEY`".
3. **Optional work is labelled optional** in its job or step name and in the summary.
4. **`|| true`, `continue-on-error: true` and a remapped exit code carry a `# ci-optional: <reason>`
   comment** on that line. `tools/ci/workflow_lint.py` refuses one without it.
5. **Conformance is not integration, and integration is not quality.** A unit or contract test proves the
   code does what it says; the container probe proves the image starts, answers and stops; an E2E run
   proves the named stages work together; a model's accuracy is shown only by an evaluation. A summary
   names which one it is.

## Workflow shape

- YAML orchestrates. Logic of more than about 30 lines goes into `tools/ci/` with tests; a check shared
  by the tools is a hub reusable with thin callers.
- Comments state intent and invariants. Incident history and superseded reasoning go to
  [`decisions/`](decisions/README.md) (dated notes) or `docker_gha_roadmap.md`, not into the YAML.
- Names, summaries and error messages are written for someone who did not write the workflow.
- A workflow is split only where its failure domains separate cleanly, not to shorten it.

## Reproducible dependencies

The tool repositories call the hub's reusables by commit SHA with the matching `hub-ref`, and a hub change
reaches them only through a reviewed pin move ([`release_trust.md`](release_trust.md) step 7). Least
privilege, SHA-pinned write-scoped actions, no `secrets: inherit`, immutable release assets and the image
scans stay as they are (#69's waves; `docker_gha_roadmap.md` §1, "What is already good (and must not
regress)").

## Releases

**Decided on #81 (10-22):** a GitHub Release certifies its source, its contract assets (`openapi.json`
and the bundles) **and** its production image `ghcr.io/ufal/atrium-<tool>-api`, by digest. A failed
required build, probe or security gate means no release.

- **One tag run per repository.** `release.yml` calls `docker-tool.reusable.yml` as its `image` job with
  `release-gate: true`, and the release job `needs` it; `docker.yml` no longer runs on tags.
- **Promotion waits for the probe.** `build-and-push` needs `docker-build-smoke`; with `release-gate` a failed
  probe leg pushes and promotes nothing, for any target.
- **The release names its images.** The reusable's `images` job reads the digest each promoted tag resolves
  to; the release attaches it as `images.json` (source repository, tag and commit; per target the image,
  tag and digest) and names the `-api` digest in its notes.
- Scan by digest before tag promotion stays, and so does AMČR's right to rebuild from the immutable source
  tag in its own environment. AMČR's approval of the pilot images stays explicit: it names the six `-api`
  digests ([pilot page](https://ufal.github.io/atrium-project/pilot/)).
- **Rollout:** digital-convert first: `v1.2.2-beta` (10-22) was released this way. Its two dispatched dry runs
  of 10-25 are the demonstration: one with a simulated probe failure (`simulate-probe-failure`), which ended
  at the probe with nothing pushed or released
  ([run](https://github.com/ufal/atrium-digital-convert/actions/runs/40215852852)), and one clean
  ([run](https://github.com/ufal/atrium-digital-convert/actions/runs/40215872101)). The other five carry the
  same `image` job on `test` since 2026-10-25 and certify their images from their next tags; a clean dry run
  of each (dispatch on `test`) checks its own inputs before that tag.

Until a repository's next tag, its newest release and its image ran independently: check GHCR for
`atrium-<tool>-api:<version without v>` and its digest before using that release. Four releases of
October 2026 had no image or an image no release described (#81, 10-20; page-classification
`v1.9.6-beta`, whose images the CVE gate stopped after the release was published).

## Integration baseline

`latest` E2E runs monitor the published services, and `test` runs serve development. Neither is a
reproducible baseline. The combination AMČR consumes or rebuilds is a recorded set: per stage, the image
reference with its digest, the `/info` version and the source commit, kept as an artifact of a green run.

## Noise

One expensive check per guarantee. Scheduled jobs are spread over the week, not stacked on Monday morning.
A failing scheduled lane opens one issue, and its later failures comment on that issue while it is
open: the hub action `.github/actions/lane-failure-issue` (a marker per lane, and per matrix leg), used
by every scheduled lane that reports. Only scheduled runs report; a permitted skip is not a failure and
reports nothing. CodeQL and the image scans write native code-scanning alerts and open no issue.

## Changing CI

Before a new check or a change to a shared template, answer in the pull request:

1. Why is it needed: which failure did it, or would it, catch?
2. What exactly does it prove, and what does it not?
3. When does it run (tier, trigger) and what does it block?
4. What does it cost: minutes, runners, network, secrets?
5. Where is its one implementation?
6. How was it checked on real tool callers, including a forced failure and its skip path, and how is it
   rolled back?

A test of the linter alone does not show that the workflow works.

## Responsibility map

What each check family proves **today**. "Gap" names where the guarantee falls short; this page is
not a claim that every row already meets the rules above.

| Check (where)                                                   | Tier and trigger                          | Blocking?                                             | What it proves today                                                                                                                                                                   | Gap                                                                                                                                                      | Inspect                                           |
|-----------------------------------------------------------------|-------------------------------------------|-------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| pre-commit (`pre-commit.reusable.yml`)                          | 1: PR, push                               | yes                                                   | the repository's hooks (ruff, format, file checks) pass                                                                                                                                | —                                                                                                                                                        | the job log                                       |
| Unit tests (`docker-tool` `test`)                               | 1: PR, push                               | yes                                                   | the test suite passes; coverage and the skip count are in the summary                                                                                                                  | skips are counted, not limited, unless the caller sets `max-skips`                                                                                       | summary, test report                              |
| API contract (`api-contract.reusable.yml`, openapi-compat)      | 1: PR, push, tag                          | yes                                                   | `/info`, `/health`, `/ready`, the error body, the committed spec current and compatible with the last release                                                                          | until 10-20 an empty run (exit 5) passed; it now fails, with counts in the summary                                                                       | summary, contract job                             |
| Shared-file parity (`para-drift.reusable.yml`)                  | 1: PR, push                               | yes                                                   | the 24 hub files are byte-identical, their selftests pass, tool-to-tool copies match their pins                                                                                        | the owners' newer changes are a job summary, not a failure (#82, by design)                                                                              | the parity job                                    |
| Workflow policy (`workflow-lint.reusable.yml`)                  | 1: PR, push                               | yes                                                   | caller rules (pinned write-scoped actions, timeouts, permissions, release drafts), the production-image closure                                                                        | the six tools lint with `require-sha-pins`, pinned to `18f0668` (10-25); a hub change reaches them only by a pin move                                    | the lint job                                      |
| Documentation (`workflow-lint.reusable.yml`)                    | 1: PR, push                               | advisory until the newcomer review (#79 D), then yes  | `tools/docs_check.py`: no emoji in a heading; every relative link and anchor resolves under GitHub's rules; the README has its documentation map and the style-guide link              | not the prose, the examples, or whether the pages match the released code: that is the review's job (#79)                                                | the step's summary                                |
| Container probe (`docker-tool` `docker-build-smoke`)            | 1: PR, `test` push, tag, dispatch         | yes, for the job; with `release-gate`, for publishing | the image starts, passes HEALTHCHECK, `/health`, `/ready`, serves its spec, honours `PORT`/`HOST`/`LOG_LEVEL`, stops on SIGTERM                                                        | all six `release.yml` pass `release-gate`; the five other than digital-convert from their next tag                                                       | the probe job                                     |
| Publish and CVE gate (`docker-tool` `build-and-push`, `images`) | 3: tag; `test` push for `:test`           | yes on tags: fixable CRITICAL, scanned by digest      | the published digest passed the gate before `<version>` and `latest` moved; on a tag, `images` names each promoted digest                                                              | `:test` is promoted without the gate (by design)                                                                                                         | summary (promoted tags, certified digests), Trivy |
| Release (`release.yml`, per tool)                               | 3: tag; dispatch (dry run)                | yes, for the release                                  | tag = `CITATION.cff` = `para_config.txt`; the committed spec current; no breaking change; bundle or vocabulary assets; where moved, the image job passed and `images.json` is attached | the five other than digital-convert attach `images.json` from their next tag (their image job is on `test` since 10-25)                                  | the release job, `images.json`                    |
| Weekly image scan (`security.yml`)                              | 4: schedule (and push, PR)                | advisory                                              | the scanned image has no new fixable CRITICAL                                                                                                                                          | four repositories scan the base image, not `-api`; its alerts are native code-scanning alerts, with no issue (#81)                                       | Trivy summary, code scanning                      |
| CodeQL (`codeql.reusable.yml`)                                  | 1 and 4: PR, push, schedule               | advisory                                              | static-analysis alerts                                                                                                                                                                 | its alerts are native code-scanning alerts, with no issue (#81)                                                                                          | code scanning alerts                              |
| Fresh-environment suite (`scheduled-smoke.yml`, per tool)       | 4: nightly or weekly                      | advisory; one issue per lane                          | the suite still passes with freshly resolved dependencies                                                                                                                              | adds no coverage                                                                                                                                         | the job, the lane's issue                         |
| Scanned-document E2E (`e2e-pipeline-smoke.yml`)                 | 2: hub push, schedule, dispatch           | per run purpose                                       | the scanned chain runs end to end on published images and the records validate                                                                                                         | moving tags (each run's digests are in its `e2e-manifest` artifact); stages 1–4 run the CLI images, not `-api`; missing inputs warn (now in the summary) | the job, failure artifact, the lane's issue       |
| Born-digital E2E (`e2e-digital-smoke.yml`)                      | 2: hub push (`test`), schedule (`latest`) | per run purpose                                       | the converter's `/reformat` and its record on the published images                                                                                                                     | moving tags (each run's digests are in its `e2e-manifest` artifact)                                                                                      | the job, the lane's issue                         |
| Cross-repo fast lane (`all-repos-smoke.yml`)                    | 4: hub push, every third day              | advisory; one issue per leg                           | the six repositories' fast lanes pass against the hub's current files                                                                                                                  | —                                                                                                                                                        | the matrix, the leg's issue                       |
| Hub self-check (`hub-self-check.yml`)                           | 1: hub PR, push; weekly                   | yes, in the hub                                       | the linter from the PR, the shared tests, RO-Crate validation; the documentation check on the hub (advisory)                                                                           | —                                                                                                                                                        | the jobs                                          |
| Site (`pages.yml`)                                              | 1: PR, push (`main`, `test`); daily       | yes, for the build; deploys from `main`               | `mkdocs build --strict`; the deployed site                                                                                                                                             | —                                                                                                                                                        | summary                                           |
| Agent skill (`skill-validate.reusable.yml`)                     | 1: `agent-skill` branches                 | yes there                                             | the skill branch contract                                                                                                                                                              | an app that does not import only warns                                                                                                                   | the job                                           |
| translator `integration.yml`                                    | 1: PR, push (stub); dispatch (live)       | stub yes; live optional                               | the LINDAT client against a local stub; with `live`, against the real hosts                                                                                                            | the live lane is manual                                                                                                                                  | the job                                           |
| translator and nlp-enrich `lindat-daily.yml`                    | 4: daily, dispatch                        | advisory; one issue per lane                          | LINDAT answers 24 identical requests with plausible content (translation: no guard rejection, numbers kept, no Czech letter left; UDPipe/NameTag: expected lemmas and entities)        | a few sentences, not a quality evaluation; occasional manual sample review stays (#78)                                                                   | the job, the lane's issue                         |
| keyword-extract `vocab-drift.yml` / `vocab-refresh.yml`         | 1: PR, push / 4: monthly                  | yes / advisory                                        | the bundled vocabulary matches its build / a fresh harvest still builds                                                                                                                | —                                                                                                                                                        | the job                                           |
| keyword-extract `controlled-live.yml`                           | 4: weekly, dispatch                       | optional (needs `OPENROUTER_KEY`)                     | the controlled kind against a live LLM backend                                                                                                                                         | a scheduled failure opens the lane's issue                                                                                                               | the job                                           |
| nlp-enrich `teitok-schema.yml`, `shellcheck.yml`                | 1: PR, push                               | yes                                                   | the TEITOK output validates against its schema; the shell scripts pass shellcheck                                                                                                      | —                                                                                                                                                        | the job                                           |
| `gpu-inference.yml` (page-classification, keyword-extract)      | dispatch only                             | optional                                              | inference on a GPU, when a GPU runner exists                                                                                                                                           | no runner yet (#40)                                                                                                                                      | the job                                           |
