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
  `docs/decisions/` (dated notes) or `docker_gha_roadmap.md`, not into the YAML.
- Names, summaries and error messages are written for someone who did not write the workflow.
- A workflow is split only where its failure domains separate cleanly, not to shorten it.

## Reproducible dependencies

The tool repositories call the hub's reusables by commit SHA with the matching `hub-ref`, and a hub change
reaches them only through a reviewed pin move ([`release_trust.md`](release_trust.md) step 7). Least
privilege, SHA-pinned write-scoped actions, no `secrets: inherit`, immutable release assets and the image
scans stay as they are (#69's waves; `docker_gha_roadmap.md` §1, "What is already good (and must not
regress)").

## Releases

**Recommendation, for decision on #81:** a GitHub Release certifies its source, its contract assets
(`openapi.json` and the bundles) **and** its production image `ghcr.io/ufal/atrium-<tool>-api`, by digest.

- One tag run per repository: the release job `needs` the image job, so a failed build, probe or CRITICAL
  gate means no release.
- The release records the digests of the images it promoted (an `images.json` asset and a line in the
  notes), next to the source commit.
- Scan by digest before tag promotion stays, and so does AMČR's right to rebuild from the immutable source
  tag in its own environment.

Until that is decided and built, the two run independently on a tag. A release then says nothing about its
image: check GHCR for `atrium-<tool>-api:<version without v>` and its digest before using it. Three
releases of October 2026 had no image or an image that no release described (#81, 10-20).

## Integration baseline

`latest` E2E runs monitor the published services, and `test` runs serve development. Neither is a
reproducible baseline. The combination AMČR consumes or rebuilds is a recorded set: per stage, the image
reference with its digest, the `/info` version and the source commit, kept as an artifact of a green run.

## Noise

One expensive check per guarantee. Scheduled jobs are spread over the week, not stacked on Monday morning.
A recurring failure updates one open issue (the marker pattern of `e2e-digital-smoke.yml`) instead of
opening a new one per run, and an issue is opened only by scheduled runs.

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

| Check (where)                                              | Tier and trigger                          | Blocking?                                        | What it proves today                                                                                                            | Gap                                                                                                                                                      | Inspect                          |
|------------------------------------------------------------|-------------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| pre-commit (`pre-commit.reusable.yml`)                     | 1: PR, push                               | yes                                              | the repository's hooks (ruff, format, file checks) pass                                                                         | —                                                                                                                                                        | the job log                      |
| Unit tests (`docker-tool` `test`)                          | 1: PR, push                               | yes                                              | the test suite passes; coverage and the skip count are in the summary                                                           | skips are counted, not limited, unless the caller sets `max-skips`                                                                                       | summary, test report             |
| API contract (`api-contract.reusable.yml`, openapi-compat) | 1: PR, push, tag                          | yes                                              | `/info`, `/health`, `/ready`, the error body, the committed spec current and compatible with the last release                   | until 10-20 an empty run (exit 5) passed; it now fails, with counts in the summary                                                                       | summary, contract job            |
| Shared-file parity (`para-drift.reusable.yml`)             | 1: PR, push                               | yes                                              | the 24 hub files are byte-identical, their selftests pass, tool-to-tool copies match their pins                                 | the owners' newer changes are a job summary, not a failure (#82, by design)                                                                              | the parity job                   |
| Workflow policy (`workflow-lint.reusable.yml`)             | 1: PR, push                               | yes                                              | caller rules (pinned write-scoped actions, timeouts, permissions, release drafts), the production-image closure                 | `@v1` accepted until `require-sha-pins` is set by the pin sweep                                                                                          | the lint job                     |
| Container probe (`docker-tool` `docker-build-smoke`)       | 1: PR, `test` push, tag                   | yes, for the job                                 | the image starts, passes HEALTHCHECK, `/health`, `/ready`, serves its spec, honours `PORT`/`HOST`/`LOG_LEVEL`, stops on SIGTERM | publishing does not wait for it (`build-and-push` needs `test` only)                                                                                     | the probe job                    |
| Publish and CVE gate (`docker-tool` `build-and-push`)      | 3: tag; `test` push for `:test`           | yes on tags: fixable CRITICAL, scanned by digest | the published digest passed the gate before `<version>` and `latest` moved                                                      | `:test` is promoted without the gate (by design); the release does not depend on it                                                                      | summary (promoted tags), Trivy   |
| Release (`release.yml`, per tool)                          | 3: tag                                    | yes, for the release                             | tag = `CITATION.cff` = `para_config.txt`; the committed spec current; no breaking change; bundle or vocabulary assets           | runs no tests and knows nothing of the image; records no digest                                                                                          | the release job                  |
| Weekly image scan (`security.yml`)                         | 4: schedule (and push, PR)                | advisory                                         | the scanned image has no new fixable CRITICAL                                                                                   | four repositories scan the base image, not `-api`; no failure notice                                                                                     | Trivy summary, code scanning     |
| CodeQL (`codeql.reusable.yml`)                             | 1 and 4: PR, push, schedule               | advisory                                         | static-analysis alerts                                                                                                          | no failure notice                                                                                                                                        | code scanning alerts             |
| Fresh-environment suite (`scheduled-smoke.yml`, per tool)  | 4: nightly                                | advisory; opens an issue                         | the suite still passes with freshly resolved dependencies                                                                       | adds no coverage; issues are not de-duplicated                                                                                                           | the job, the opened issue        |
| Scanned-document E2E (`e2e-pipeline-smoke.yml`)            | 2: hub push, schedule, dispatch           | per run purpose                                  | the scanned chain runs end to end on published images and the records validate                                                  | moving tags (each run's digests are in its `e2e-manifest` artifact); stages 1–4 run the CLI images, not `-api`; missing inputs warn (now in the summary) | the job, failure artifact        |
| Born-digital E2E (`e2e-digital-smoke.yml`)                 | 2: hub push (`test`), schedule (`latest`) | per run purpose                                  | the converter's `/reformat` and its record on the published images                                                              | moving tags (each run's digests are in its `e2e-manifest` artifact)                                                                                      | the job, the de-duplicated issue |
| Cross-repo fast lane (`all-repos-smoke.yml`)               | 4: hub push, every third day              | advisory                                         | the six repositories' fast lanes pass against the hub's current files                                                           | no failure notice                                                                                                                                        | the matrix                       |
| Hub self-check (`hub-self-check.yml`)                      | 1: hub PR, push; weekly                   | yes, in the hub                                  | the linter from the PR, the shared tests, RO-Crate validation                                                                   | —                                                                                                                                                        | the jobs                         |
| Site (`pages.yml`)                                         | 1: PR, push (`main`, `test`); daily       | yes, for the build; deploys from `main`          | `mkdocs build --strict`; the deployed site                                                                                      | —                                                                                                                                                        | summary                          |
| Agent skill (`skill-validate.reusable.yml`)                | 1: `agent-skill` branches                 | yes there                                        | the skill branch contract                                                                                                       | an app that does not import only warns                                                                                                                   | the job                          |
| translator `integration.yml`                               | 1: PR, push (stub); dispatch (live)       | stub yes; live optional                          | the LINDAT client against a local stub; with `live`, against the real hosts                                                     | the live lane is manual                                                                                                                                  | the job                          |
| keyword-extract `vocab-drift.yml` / `vocab-refresh.yml`    | 1: PR, push / 4: monthly                  | yes / advisory                                   | the bundled vocabulary matches its build / a fresh harvest still builds                                                         | —                                                                                                                                                        | the job                          |
| keyword-extract `controlled-live.yml`                      | 4: push, weekly, dispatch                 | optional (needs `OPENROUTER_KEY`)                | the controlled kind against a live LLM backend                                                                                  | no failure notice                                                                                                                                        | the job                          |
| nlp-enrich `teitok-schema.yml`, `shellcheck.yml`           | 1: PR, push                               | yes                                              | the TEITOK output validates against its schema; the shell scripts pass shellcheck                                               | —                                                                                                                                                        | the job                          |
| `gpu-inference.yml` (page-classification, keyword-extract) | dispatch only                             | optional                                         | inference on a GPU, when a GPU runner exists                                                                                    | no runner yet (#40)                                                                                                                                      | the job                          |
