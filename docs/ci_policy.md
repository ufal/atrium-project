# CI/CD policy

> **Status:** policy, added 2026-10-20 for [#81](https://github.com/ufal/atrium-project/issues/81); its
> triggers follow the working agreement of 11 November 2026.
> **Scope:** the hub's reusable workflows and lanes, and the six tool repositories' callers.
> Tag rules, immutable releases and commit pins live in [`release_trust.md`](release_trust.md); the
> current workflow set is described in [`docker_gha.md`](docker_gha.md). This page sets the rules
> for both and says what each result means.

## The rule

**CI runs on pull requests and releases.** No workflow runs on a branch push, and none runs on a
schedule when the code has not changed, apart from the security scans. In practice:

- **Pull requests** run the checks: lint, tests, the API contract, the shared-file parity, the container
  probe. A pull request merged into `test` (its `closed` event) runs them again on the merge commit and
  publishes the `:test` images; an unmerged close runs nothing.
- **Releases** start with a pushed `v*` tag, the one push trigger of the tool repositories: `release.yml`
  certifies the release and its images.
- **Security** is the exception that keeps a schedule: the weekly CodeQL run (`codeql.yml`) and the weekly
  scan of the published image (`security.yml`). Dependabot opens security updates only
  (`open-pull-requests-limit: 0` stops routine version updates).
- **Manual lanes** run by `workflow_dispatch` only, before a release or when something looks wrong: the
  fresh-environment suites, the LINDAT checks, the live LLM check, the vocabulary refresh, the
  cross-repository fast lane and the GPU lane.
- **Deployment** of the hub's site happens on a merge into `main` (a push to `main`): it publishes, it does
  not test.

`tools/ci/workflow_lint.py --event-driven`, which every repository's Workflow Policy Lint runs, refuses
a branch push and a schedule outside these exceptions.

## Tiers

| Tier            | Runs on                                                                   | Must be                                                                                         | Never                                                                     |
|-----------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 1. Pull request | `pull_request` (and its merged `closed` event, for the `:test` images)    | fast (minutes), deterministic, no secrets, no network beyond package installs                   | a GPU, a live external service, a model download that a cache cannot hold |
| 2. Integration  | hub pull requests that touch a lane's files, dispatch                     | run against a **named** set of images or revisions, and record which (image digest, source SHA) | be read as release approval when the set was moving tags                  |
| 3. Release      | a version tag `v*`, a published release                                   | validate and publish one release: its source, contract assets and image                         | publish part of a release while another required part failed              |
| 4. Security     | a weekly schedule (CodeQL, the image scan); Dependabot's security updates | watch for new advisories against code and images that did not change                            | block a pull request                                                      |
| Manual          | `workflow_dispatch`                                                       | check what a commit cannot show: fresh dependencies, LINDAT and LLM backends, a GPU             | run on its own                                                            |

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
  or a `needs:` of a publishing job; advisory and optional checks say so in their job name or summary. No
  repository has a branch ruleset yet (#40), so until it lands only the `needs:` of a publishing job blocks
  anything: on a pull request every check is in practice advisory. The working agreement still asks for
  one reviewed, squash-merged pull request per issue and no direct push to `test` or `master`.

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

- **Tagging.** A release tag is created with `scripts/tag_release.py` on the release commit that a merged
  pull request put on `test`, once that pull request's checks have passed, and pushed alone; a tag that
  started no run is released by dispatching Release Bundle on the tag
  ([release_trust.md](release_trust.md#tagging-a-release)).
- **Before tagging,** dispatch the hub's two e2e lanes at `image-tag: test` and the tool's
  fresh-environment suite (`scheduled-smoke.yml`): with no schedule, nothing else runs them on code that
  no pull request touched. The manual lanes that call live services (the LINDAT checks, the live LLM
  check) belong to the same list when the release changes their part.
- **One tag run per repository.** `release.yml` calls `docker-tool.reusable.yml` as its `image` job with
  `release-gate: true`, and the release job `needs` it; `docker.yml` no longer runs on tags.
- **Promotion waits for the probe.** `build-and-push` needs `docker-build-smoke`; with `release-gate` a failed
  probe leg pushes and promotes nothing, for any target.
- **The release names its images.** The reusable's `images` job reads the digest each promoted tag resolves
  to; the release attaches it as `images.json` (source repository, tag and commit; per target the image,
  tag and digest) and names the `-api` digest in its notes.
- Scan by digest before tag promotion stays, and so does AMČR's right to rebuild from the immutable source
  tag in its own environment. AMČR chooses the version of each tool when its step joins the pilot chain,
  and names the `-api` image by digest ([Production pilot](https://ufal.github.io/atrium-project/pilot/)).
- **What a published image does not promise:** steps that run after the images are promoted (the release
  bundle, the vocabulary stamps) can still fail. The version then has published images but no GitHub
  Release, and it is not a release: use a version only when its GitHub Release exists and names the
  digest. Each cause found so far now fails on a pull request, and the fix of a release is a new patch
  version, never a moved tag.

How the gate was rolled out in October 2026, and the releases that ended without one:
[`decisions/release-trust-log.md`](decisions/release-trust-log.md#the-release-gate-rollout-october-2026).

## Integration baseline

`latest` E2E runs check the published services, and `test` runs, which pull requests use, serve development. Neither is a
reproducible baseline. The combination AMČR consumes or rebuilds is a recorded set: per stage, the image
reference with its digest, the `/info` version and the source commit, kept as an artifact of a green run.

## Noise

One expensive check per guarantee. The only scheduled runs are the weekly security scans, spread over the
week rather than stacked on Monday morning; CodeQL and the image scans write native code-scanning alerts and
open no issue. A manual lane reports to whoever dispatched it, in its run summary. A permitted skip is not a
failure and reports nothing. The hub action `.github/actions/lane-failure-issue`, which opened one issue per
failing scheduled lane, has no caller since the lanes lost their schedules.

A scan that fails before it scans, because Trivy cannot download its vulnerability database, is not a
finding: both scans retry the download, and the CVE release gate runs once more, before they fail
([Trivy DB retry](decisions/docker-tool-reusable.md#trivy-db-retry)).

## Changing CI

Before a new check or a change to a shared template, answer in the pull request:

1. Why is it needed: which failure did it, or would it, catch?
2. What exactly does it prove, and what does it not?
3. When does it run (tier, trigger) and what does it block? A pull request, a release or a dispatch; a
   schedule only for a security scan.
4. What does it cost: minutes, runners, network, secrets?
5. Where is its one implementation?
6. How was it checked on real tool callers, including a forced failure and its skip path, and how is it
   rolled back?

A test of the linter alone does not show that the workflow works.

## Responsibility map

What each check family proves. "Gap" names where the guarantee falls short; this page is
not a claim that every row already meets the rules above.

| Check (where)                                                   | Tier and trigger                           | Blocking?                                             | What it proves today                                                                                                                                                                   | Gap                                                                                                                                                                                            | Inspect                                                                     |
|-----------------------------------------------------------------|--------------------------------------------|-------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| pre-commit (`pre-commit.reusable.yml`)                          | 1: PR                                      | yes                                                   | the repository's hooks (ruff, format, file checks) pass                                                                                                                                | —                                                                                                                                                                                              | the job log                                                                 |
| Unit tests (`docker-tool` `test`)                               | 1: PR, and a merged PR's merge commit      | yes                                                   | the test suite passes; coverage and the skip count are in the summary                                                                                                                  | skips are counted, not limited, unless the caller sets `max-skips`                                                                                                                             | summary, test report                                                        |
| API contract (`api-contract.reusable.yml`, openapi-compat)      | 1: PR; 3: tag                              | yes                                                   | `/info`, `/health`, `/ready`, the error body, the committed spec current and compatible with the last release                                                                          | until 10-20 an empty run (exit 5) passed; it now fails, with counts in the summary                                                                                                             | summary, contract job                                                       |
| Shared-file parity (`para-drift.reusable.yml`)                  | 1: PR                                      | yes                                                   | the 26 hub files are byte-identical, their selftests pass, tool-to-tool copies match their pins                                                                                        | the owners' newer changes are a job summary, not a failure (#82, by design)                                                                                                                    | the parity job                                                              |
| Workflow policy (`workflow-lint.reusable.yml`)                  | 1: PR                                      | yes                                                   | caller rules (pinned write-scoped actions, timeouts, permissions, release drafts, triggers: `--event-driven`), the production-image closure                                            | the six tools lint with `require-sha-pins`, pinned to one hub commit (`02cbd01`); a hub change reaches them only by a pin move                                                                 | the lint job                                                                |
| Documentation (`workflow-lint.reusable.yml`)                    | 1: PR                                      | advisory until the newcomer review, then yes          | `tools/docs_check.py`: no emoji in a heading; every relative link and anchor resolves under GitHub's rules; the README has its documentation map and the style-guide link              | not the prose, the examples, or whether the pages match the released code: that is the review's job (#79)                                                                                      | the step's summary                                                          |
| Container probe (`docker-tool` `docker-build-smoke`)            | 1: PR (a merged one too); 3: tag; dispatch | yes, for the job; with `release-gate`, for publishing | the image starts, passes HEALTHCHECK, `/health`, `/ready`, serves its spec, honours `PORT`/`HOST`/`LOG_LEVEL` (uvicorn's records included), stops on SIGTERM                           | all six `release.yml` pass `release-gate`, and each has released through it                                                                                                                    | the probe job                                                               |
| Publish and CVE gate (`docker-tool` `build-and-push`, `images`) | 3: tag; a PR merged into `test`: `:test`   | yes on tags: fixable CRITICAL, scanned by digest      | the published digest passed the gate before `<version>` and `latest` moved; on a tag, `images` names each promoted digest                                                              | `:test` is promoted without the gate (by design)                                                                                                                                               | summary (promoted tags, certified digests, CRITICAL and HIGH listed), Trivy |
| Release (`release.yml`, per tool)                               | 3: tag; dispatch (dry run)                 | yes, for the release                                  | tag = `CITATION.cff` = `para_config.txt`; the committed spec current; no breaking change; bundle or vocabulary assets; where moved, the image job passed and `images.json` is attached | a step after promotion (bundle, stamps) can fail with the images published: no release, so not a release (Releases above)                                                                      | the release job, `images.json`                                              |
| Weekly image scan (`security.yml`)                              | 4: weekly schedule (and PR, release)       | advisory                                              | the scanned image has no new fixable CRITICAL                                                                                                                                          | its alerts are native code-scanning alerts, with no issue (#81)                                                                                                                                | Trivy summary, code scanning                                                |
| CodeQL (`codeql.reusable.yml`)                                  | 1 and 4: PR, weekly schedule               | advisory                                              | static-analysis alerts                                                                                                                                                                 | its alerts are native code-scanning alerts, with no issue (#81)                                                                                                                                | code scanning alerts                                                        |
| Fresh-environment suite (`scheduled-smoke.yml`, per tool)       | manual: dispatch                           | advisory                                              | the suite still passes with freshly resolved dependencies                                                                                                                              | adds no coverage                                                                                                                                                                               | the job                                                                     |
| Scanned-document E2E (`e2e-pipeline-smoke.yml`)                 | 2: hub PR touching the lane; dispatch      | per run purpose                                       | the scanned route of 2.0 (the ATR's docproc, stood in) on published images; the records validate                                                                                       | moving tags (each run's digests are in its `e2e-manifest` artifact); stages 1–4 run the CLI images, not `-api`; missing inputs warn (now in the summary)                                       | the job, failure artifact                                                   |
| Born-digital E2E (`e2e-digital-smoke.yml`)                      | 2: hub PR touching the lane; dispatch      | per run purpose                                       | docproc from `-digital` and `/reformat`, the record ocr-postprocess builds from it                                                                                                     | moving tags (each run's digests are in its `e2e-manifest` artifact)                                                                                                                            | the job                                                                     |
| Cross-repo fast lane (`all-repos-smoke.yml`)                    | manual: dispatch                           | advisory                                              | the six repositories' fast lanes pass against the hub's current files                                                                                                                  | —                                                                                                                                                                                              | the matrix                                                                  |
| Hub self-check (`hub-self-check.yml`)                           | 1: hub PR; dispatch                        | yes, in the hub                                       | the linter from the PR, the shared tests (with the six tools' `test` heads beside the hub, and the tags), RO-Crate validation; the documentation check on the hub (advisory)           | a hub change the tools have not followed fails here until they follow it, unless its PR is labelled `siblings:<branch>`; with no weekly run, a force-pushed action tag is found on the next PR | the jobs                                                                    |
| Site (`pages.yml`)                                              | 1: PR; deploys on a merge into `main`      | yes, for the build; deploys from `main`               | `mkdocs build --strict`; the deployed site                                                                                                                                             | —                                                                                                                                                                                              | summary                                                                     |
| Agent skill (`skill-validate.reusable.yml`)                     | 1: `agent-skill` branches                  | yes there                                             | the skill branch contract                                                                                                                                                              | an app that does not import only warns                                                                                                                                                         | the job                                                                     |
| translator `integration.yml`                                    | 1: PR (stub); dispatch (live)              | stub yes; live optional                               | the LINDAT client against a local stub; with `live`, against the real hosts                                                                                                            | the live lane is manual                                                                                                                                                                        | the job                                                                     |
| translator and nlp-enrich `lindat-daily.yml`                    | manual: dispatch                           | advisory                                              | LINDAT answers 24 identical requests with plausible content (translation: no guard rejection, numbers kept, no Czech letter left; UDPipe/NameTag: expected lemmas and entities)        | a few sentences, not a quality evaluation; occasional manual sample review stays (#78)                                                                                                         | the job                                                                     |
| keyword-extract `vocab-drift.yml` / `vocab-refresh.yml`         | 1: PR / manual: dispatch                   | yes / advisory                                        | the bundled vocabulary matches its build / a fresh harvest still builds                                                                                                                | —                                                                                                                                                                                              | the job                                                                     |
| keyword-extract `controlled-live.yml`                           | 1: PR touching its files; dispatch         | optional (needs `OPENROUTER_KEY`)                     | the controlled kind against a live LLM backend                                                                                                                                         | paid per run; a fork's pull request has no secret, and the test skips                                                                                                                          | the job                                                                     |
| nlp-enrich `teitok-schema.yml`, `shellcheck.yml`                | 1: PR                                      | yes                                                   | the TEITOK output validates against its schema; the shell scripts pass shellcheck                                                                                                      | —                                                                                                                                                                                              | the job                                                                     |
| `gpu-inference.yml` (page-classification, keyword-extract)      | dispatch only                              | optional                                              | inference on a GPU, when a GPU runner exists                                                                                                                                           | no runner yet (#40)                                                                                                                                                                            | the job                                                                     |
