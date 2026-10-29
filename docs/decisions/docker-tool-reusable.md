# Docker tool workflow: decisions and history

> **Status:** decision record, added 2026-10-25 for [#81](https://github.com/ufal/atrium-project/issues/81)
> (B.1, workflow readability).
> **Scope:** [`docker-tool.reusable.yml`](../../.github/workflows/docker-tool.reusable.yml), the reusable
> workflow every tool repository calls to test, probe and publish its images.

The workflow's comments say what each job and step does and which invariants it must keep. This page
keeps the reasoning and the incidents behind them: the failures that shaped a step, the designs it
replaced and the runs that showed it. Each section quotes, verbatim, the comment that stood at that
place in the workflow until 2026-10-25; sections follow the workflow's order. Dates, run numbers and
"today" in a quote are as of when it was written; the workflow is the authority on what holds now.

The current workflow set is described in [`docker_gha.md`](../docker_gha.md), the rules every
workflow follows in [`ci_policy.md`](../ci_policy.md), and the dated plan in
[`docker_gha_roadmap.md`](../docker_gha_roadmap.md).

## Secrets

### Declared secrets

Why `secrets:` declares `CODECOV_TOKEN` alone (#18, the 2026-07-29 audit).

> Declared explicitly so callers can drop `secrets: inherit`, which handed
> this workflow EVERY secret in the calling repo — HF_TOKEN, OPENROUTER_KEY,
> GH2MD_READ_ACCESS — while it only ever needs this one (#18, 2026-07-29
> audit). GITHUB_TOKEN is provided automatically to reusable workflows and
> must NOT be declared here; GitHub rejects `secrets.GITHUB_TOKEN` as a
> workflow_call secret name.

## The test job

### Test job permissions

The `permissions:` block of `test` (issue #10, G8).

> Least privilege (issue #10, G8). A reusable workflow's job inherits the
> CALLER's default token scope when it declares none, so this job — which
> executes the consuming repo's whole test suite, i.e. arbitrary code — ran
> at whatever each of the five repos happened to grant. It only needs to read
> the tree; the Codecov upload authenticates with its own token, not GITHUB_TOKEN.

### CODECOV_TOKEN in the job environment

The job-level `env:` of `test` (#18).

> Written to job env so the Codecov step's `if:` can see it — the
> `secrets` context alone is invisible to `env.*` checks, which made the
> old `if: env.CODECOV_TOKEN != ''` permanently false (#18).

### Hugging Face cache key

The `key:` of the "Cache HuggingFace Models" step (#18).

> Keyed on the caller's MODEL revision, not source code. The old key was
> `hashFiles('**/*.py')`, which changed on every Python edit and therefore
> missed the cache almost every run — the opposite of the intent (#18).
> (e2e-pipeline-smoke.yml keys its own HF cache by image tag instead,
> `e2e-hf-<tag>-regnety160`; the `PC_REVISION` it once used is gone.)

### Inputs passed through env

Above the "Install APT packages", "Pre-install PyTorch" and "Install dependencies" steps (#18).

> The three steps below take their values through `env:` rather than
> interpolating ${{ inputs.* }} straight into the shell. Inputs are
> caller-controlled so this was not exploitable, but expression-into-`run:`
> is the pattern actionlint and CodeQL flag, and quoting "$VAR" also stops a
> value with spaces or globs from being re-split by the shell (#18).

### The removed advisory ruff run

Where the advisory `ruff check .` step stood until W6 (2026-08-06; roadmap E7).

> W6 (2026-08-06): the advisory `ruff check .` that stood here was REMOVED.
> `pre-commit.reusable.yml` already runs ruff BLOCKING on the same events, so
> every PR carried two contradictory signals for one rule set — an amber
> "lint failed (ignored)" beside a red "pre-commit failed", both about the same
> finding. `continue-on-error: true` also means it could never gate anything, so
> deleting it loses no enforcement. Repos wanting lint here should call the
> pre-commit reusable, which is where the ruff config already lives.

### Skipped tests

On the "Test & Coverage" step and above "Skipped-test visibility" (W6).

> `-rs` reports every SKIPPED test with its reason. Phase 6's lesson, made
> ecosystem-wide: a skipped test is not a cheaper test, it is an untested
> module wearing a green tick — docx_to_md.py sat at 15% coverage behind a
> green run with 17 tests silently skipping in CI. Skips are now visible in
> the log and summarised below.
> `tee` so the skip step below parses THIS run's real terminal summary
> rather than re-collecting (a re-collect re-evaluates skipif markers and can
> legitimately disagree with the run that just happened).

> W6: surface the skip count, and let a repo ratchet it down over time.
> Default `max-skips: -1` means "report only", so this is non-breaking for all
> five repos on day one; a repo that has cleaned up sets a real ceiling and CI
> holds the line.

### Tests must not change tracked files

Above "Assert the working tree is unchanged by the tests" (W6).

> W6: idempotency. A test suite that mutates tracked files is not a test suite,
> it is a build step with assertions — and the mutation lands in whoever's next
> commit. nlp-enrich's suite reordered the committed
> `data_samples/manifest.tsv` on every run; that was found by hand. This makes
> the whole ecosystem fail loudly instead, in the one place all five repos share.

## The docker-build-smoke job

### When the probe runs

The `if:` of `docker-build-smoke`: why it runs on pushes to `test` (W3) and why `build-and-push` needs
it (atrium-project#81).

> W3: was `github.event_name == 'pull_request'` alone, and that gate is why
> the container probe below could be published without ever being proven.
>
> alto-postprocess added its `api` stage on a PUSH to `test`, so the job did
> not run and nothing ever started the image; the first thing to actually do
> so was a fork PR weeks later, which found the ENTRYPOINT dying at import
> (`python service/text_api.py` puts /app/service on sys.path[0], not /app).
> The fix was then ALSO pushed to `test` — where this job skipped again — so
> the fix shipped unproven by any container start, and it surfaced as a red
> check on an unrelated contributor's PR that had not caused it.
>
> A probe that only runs on pull_request tests contributor branches and not
> the integration branch they merge into, which is backwards: `test` is what
> `build-and-push` publishes from. This gate now mirrors that job's own,
> minus the release leg (a released image is built from a tag that already
> passed here on its way through `test`).
>
> `build-and-push` needs this job (atrium-project#81). It was kept apart while this job
> skipped on push, because a `needs:` on a skipped job would have stopped `:test` from
> publishing; the job has run on every `test` push since. With `release-gate: true` a
> failed probe now stops publishing; without it, publishing waits for the probe and then
> goes ahead as before. A dispatched run probes too, so a release workflow's dry run
> exercises the gate before a tag does.

### Probe job permissions

The `permissions:` block of `docker-build-smoke` (issue #10, G8).

> Least privilege (issue #10, G8). This job builds the image but never pushes
> it — publication happens in `build-and-push`, which scopes `packages: write`
> for itself. Building from a PR needs nothing beyond the tree.

### Independent targets

The `fail-fast: false` of `docker-build-smoke` (atrium-project#10).

> Same reasoning as `build-and-push` below: the targets are independent images, so
> stopping at the first broken one hides the state of the rest and costs a review
> cycle per target rather than per push. (issue atrium-project#10)

### Buildx boot retry

The same comment stood on the "Set up Docker Buildx" step of both `docker-build-smoke` and
`build-and-push`, above their `# ci-optional:` line.

> Booting the container driver pulls moby/buildkit:buildx-stable-1 from
> Docker Hub, so an anonymous round-trip to a third-party registry gates
> every Docker job in all six tool repos. A single TCP reset there fails
> a job that has nothing to do with Docker Hub — alto-postprocess run
> 34620887123 ("edit env example - corrector") lost `docker-build-smoke
> (api)` to `read: connection reset by peer` on auth.docker.io while the
> other THREE buildx boots in the same run, the same minute, succeeded.
>
> continue-on-error is required here so that a failed boot does not ABORT
> the job — without it the run stops at this step and the guarded retry
> below is dead code. (It is not about `steps.<id>.outcome` being set:
> that is populated for any step with an id. `outcome` is the result
> BEFORE continue-on-error is applied and `conclusion` is after, which
> is why the retry tests `outcome`, not `conclusion`.)
>
> The retry itself is NOT continue-on-error, so a real outage still
> fails the job loudly. This buys one attempt, not silence — and it is a
> mitigation, not a cure: the dependency on Docker Hub is unchanged.
>
> Switching to `driver: docker` would remove the pull outright, but the
> gha cache exporter used below requires the container driver; trading
> the build cache away for a rarely-hit network dependency is the wrong
> side of that deal.

### Build target

On the `target:` of the "Smoke Build" step.

> Every ATRIUM Dockerfile names its first stage `AS base`, so the
> target is passed through verbatim. The old `'base' -> ''` mapping
> resolved to the LAST declared stage, silently building/publishing
> the wrong image in multi-stage repos (nlp-enrich, digital-convert).

### Loading the image for the probe

On the `load: true` of the "Smoke Build" step (issue #55; roadmap B9 and H8).

> load: true puts the built image into this runner's local Docker daemon so
> the container-run probe below (issue #55) can start it. Single-platform
> only — fine, every ATRIUM image is implicitly linux/amd64 today (roadmap
> H8). Before this, the smoke build produced an image nothing ever started:
> roadmap B9 recorded that no Dockerfile ENTRYPOINT was exercised anywhere in
> CI. `load` is a no-op cost for targets not in probe-targets.

### Shared model cache

The step "Share one model cache across the probe containers", and the page-classification tag that
prompted it.

> Every step below starts a FRESH container from the same image. An image whose service
> downloads its models at warm-up (page-classification: five ViT revisions from the
> Hugging Face Hub into HF_HOME) therefore downloaded them once per step, four times per
> job, and an ATRIUM service's warm-up runs in its lifespan, before uvicorn listens. On
> page-classification's v1.9.2-beta tag (run 37269822039) the PORT=9000 container was
> still loading its fifth model when Docker's HEALTHCHECK budget (start-period 180s +
> 3 x 30s) ran out, and that step blamed $PORT. One named volume at the image's own
> HF_HOME, mounted into every probe container of this job, lets the first container pay
> for the download and the others start from disk. An image that sets no HF_HOME gets no
> mount, so its probes are exactly as before.
>
> A named volume rather than a bind mount: Docker seeds an empty named volume with the
> image's directory, ownership included, so the image's non-root user can write to it.
> Hosted runners are discarded after the job, so the volume needs no cleanup.

### The container probe

The step "Run container and wait for HEALTHCHECK (issue #55)". The subsections quote the comments in
its script.

> Opt-in per target via probe-targets — most build-targets are batch CLIs with
> no HTTP server to probe. This is the assertion that would have caught "no
> service handles SIGTERM" and "no Dockerfile declares HEALTHCHECK" on day one:
> it is the only place in this whole workflow that starts one of these
> containers and watches it behave, rather than merely building the image.

#### HEALTHCHECK budget

Above the wait loop (`deadline=$((SECONDS + 330))`).

> docker inspect's Health.Status is what HEALTHCHECK exists to make
> meaningful — a wrong probe path or a missing interpreter in the image is
> otherwise invisible.
>
> The budget is derived from the HEALTHCHECK convention in
> docs/docker_gha.md §3.4 (--start-period=180s --interval=30s --retries=3),
> and it has to cover the UNHEALTHY verdict, not just the healthy one.
> Docker only marks a container unhealthy after `retries` consecutive
> failing probes past the start period: 180 + 3x30 = 270s. The old 240s
> budget cleared the healthy path (180 + 30 = 210s) but expired 30s BEFORE
> a genuinely broken container could be declared unhealthy — so a real
> failure was reported as an ambiguous "did not report healthy within the
> timeout", which reads like a slow runner. 330s = 270 + one interval of
> slack, still far inside this job's timeout-minutes: 45.

#### Log format control

Above and below the `LEVEL_ALLOWLIST` assignment (issue #61; atrium-project#60).

> (issue #61) The control half of the LOG_LEVEL probe below: at the default
> level (no LOG_LEVEL set -> INFO), startup/warmup already emitted at least
> one record in the agreed
> "%(asctime)s %(levelname)s %(name)s %(message)s" shape. If this ever stops
> matching, the WARNING-suppression step below would pass for the wrong
> reason -- nothing being logged at all, not INFO being filtered out.
>
> LEVEL_ALLOWLIST intentionally accepts any of the five standard levelnames,
> not just INFO: the invariant this asserts is "the configured root logger is
> wired and its formatter matches the agreed shape", not "warmup happened to
> succeed". A backend that requires a secret CI legitimately does not have
> (e.g. llm-enrich's OPENROUTER_API_KEY, atrium-project#60) logs its warmup
> failure at WARNING via the same formatter and should pass this check exactly
> as a clean INFO-only startup does -- narrowing to INFO alone made this step
> fail every run for that service regardless of the format string being fine.

> Some services (keyword-extract's KeyBERT warmup, in particular) keep emitting
> HF Hub metadata calls for a few seconds after Docker's own HEALTHCHECK
> first reports healthy, so a single immediate grep can race a genuinely
> correct container. Poll instead of checking once.

#### Served OpenAPI document

Above the served-versus-committed spec comparison (atrium-project#32, round 2).

> (atrium-project#32 round 2) The image serves the spec that was committed and that
> the release attaches: GET /openapi.json must equal a committed service/openapi*.json
> (info.version aside — the committed file is stamped only at release time), and
> /info `openapi_sha256` must be the digest of what is served. This is the check the
> AMČR pipeline runs against a deployed image, and the only container-level proof for
> a torch-bound service whose light lane generates the spec with a stub (pc). A spec
> per service is matched by content, so a repo with two HTTP images would pass against
> its own file (none has two today: digital-convert's planned second image became its
> one service, `-api`, with one service/openapi.json).
> Skipped where the repo has not adopted the typed contract yet (no committed spec, or
> no vendored atrium_openapi.py), because the hub's `v1` moves for all six at once.

#### SIGTERM budget

Above `stop_budget=30`.

> The budget must EXCEED the graceful-shutdown budget the service is
> entitled to, or the probe kills a correctly-behaving container and
> blames it. The ATRIUM api convention is GRACEFUL_SHUTDOWN_S=20 (passed
> to uvicorn's --timeout-graceful-shutdown) with a connection drain
> defaulting to 25s above it, so `--time 15` sent SIGKILL five seconds
> before uvicorn's own deadline: a service that actually used its drain
> window would exit 137 and fail here for doing the right thing. It has
> only ever passed because the probe sends no requests, which is exactly
> the case it is not testing.
>
> 30s clears the 25s drain with slack. This asserts "SIGTERM alone is
> enough", not "shutdown is fast" — the second is not this probe's business.

### Non-default port

The step "Run container on a NON-DEFAULT port (issue #58)".

> The step above proves the DEFAULT path: it must stay exactly as it is, because
> it is what guarantees the reference manifest and every probe in it keep working
> unchanged. This is a SECOND, deliberately shorter start that proves $PORT is a
> real knob rather than a documented one.
>
> Why simply reaching `healthy` is the whole assertion: Docker runs the image's
> HEALTHCHECK *inside* the container, with the container's environment, and that
> probe body (service/healthcheck.py, byte-identical in all five repos) builds its
> URL from $PORT. So a container that reports healthy with PORT=9000 has proved in
> ONE status transition that the listener moved AND that the in-container probe
> found it there. Before issue #58 the four non-alto services ignored $PORT while
> healthcheck.py honoured it, so this exact start reported unhealthy forever — the
> failure this step exists to keep from coming back.
>
> A regression surfaces here as a ~5.5-minute TIMEOUT, not an immediate error:
> the listener is simply not where the probe looks, so the container never leaves
> `starting` until the budget expires. That is expected, not a slow runner.
>
> No /ready probe and no SIGTERM assertion here: both belong to the default-port
> step above, and repeating them would double this job's slowest phase to re-test
> what is not port-dependent.

### HOST bound to loopback

The step "Run container bound to HOST=127.0.0.1 (issue #58)".

> $PORT's sibling knob. HOST is proved the same way PORT was above: bind the
> listener to the loopback interface only, and show the effect from both sides —
> the in-container HEALTHCHECK (which probes 127.0.0.1 regardless, per
> service/healthcheck.py's own comment) must still report healthy, while the
> PUBLISHED interface, which is what a misconfigured HOST is supposed to close
> off, must stop answering. Reversing either half would prove nothing: healthy
> alone doesn't show HOST took effect (the in-container probe never used the
> public interface anyway), and an unreachable curl alone doesn't rule out the
> container simply failing to start.

### Log level suppression

The step "Run container with LOG_LEVEL=WARNING and assert INFO is suppressed (issue #61)".

> The end-to-end half of #61's second acceptance criterion: "LOG_LEVEL=DEBUG
> docker run … visibly changes output volume". This is the WARNING direction —
> raising the bar, not lowering it — because it needs no request traffic to
> observe: startup/warmup alone emit INFO records at the default level (the
> control asserted in the HEALTHCHECK step above), so silencing them is
> visible from the container's own logs with nothing more than a clean start
> and stop. A test that only checked DEBUG adding MORE output would pass even
> if LOG_LEVEL were read and ignored in the "less" direction — this repo's own
> history: LOG_LEVEL was wired correctly and controlled nothing in two
> services until #61.
>
> Deliberately no request/SIGTERM battery here — that behaviour is not
> LOG_LEVEL-dependent and is already covered by the step above. Reaching
> `healthy` is enough exposure for startup/warmup logging to have run.

## The build-and-push job

### When publishing runs

The `if:` of `build-and-push`: the release gate (atrium-project#81) and the `:test` channel (W2,
2026-08-06).

> atrium-project#81: on a version tag a release certifies its image, so with
> `release-gate: true` nothing is pushed unless every probe leg passed. `!cancelled()`
> lets this job run after a failed probe when the gate is off, as it did before it
> needed the probe; a cancelled run still publishes nothing.
>
> W2 (2026-08-06): `push` to `refs/heads/test` added. Issue #10 introduced the
> `type=raw,value=test` tag rule below, but this gate still admitted only tag
> pushes and release events — and `github.ref` is never `refs/heads/test` on a
> tag. The two were MUTUALLY EXCLUSIVE, so the `:test` channel could not be
> published by any event, and `#10.plan.md`'s "BLOCKED (soft) — needs one branch
> push per repo" was a hard block: llm-enrich pushed `test` six times on
> 2026-08-06, every run green, no image published. `type=sha` lives in this same
> job, so a branch push published nothing at all.
>
> `:test` is deliberately NOT release-gated. The Trivy blocker below is
> `if: startsWith(github.ref, 'refs/tags/')`, so it does not apply here — a
> pre-release channel that a CVE can block is not usable for the triage it
> exists to serve. Release tags keep the gate; `test` keeps moving.
>
> Cost is bounded by the CALLER's concurrency group, which every one of the five
> already sets to `cancel-in-progress: ${{ !startsWith(github.ref, 'refs/tags/') }}`
> — superseded `test` builds cancel; only tag builds are protected from cancellation.

### Independent legs

The `fail-fast: false` of `build-and-push`, and the llm-enrich v0.6.0 release that showed why
(atrium-project#10).

> Each leg publishes a DIFFERENT image (`-llm`, `-digital`, `-api`, `-remote`), so
> one leg's failure says nothing about another's. With the default fail-fast the
> release gate's rejection of one target cancels the promotion of targets that
> already built and scanned clean. Live proof — llm-enrich v0.6.0, run
> 32242079038: `build-and-push (llm)` failed the fixable-CRITICAL gate on vllm
> 0.9.2, which is the gate doing its job; `build-and-push (digital)` was then
> CANCELLED mid-promotion despite its own build and Trivy scan both passing, so
> `ghcr.io/ufal/atrium-llm-enrich-digital:latest` -- the first-ever `:latest` for
> the born-digital converter -- was never published and still 404s, while the
> digital E2E cron resolves `:latest`. One target's CVE must not withhold another
> target's clean image. (issue atrium-project#10)

### Scan, then promote

Above the two metadata steps (W3, 2026-08-06), and the llm-enrich v0.5.2 release that showed why.

> ── W3: scan-then-promote (2026-08-06) ──────────────────────────────────
> The metadata is split in two. Only `meta-immutable` is PUSHED by the build;
> `meta-release` is applied afterwards, and only once the release gate passes.
>
> Why: the gate ran AFTER the push, so a blocked release still shipped. Live
> proof — llm-enrich v0.5.2, run 31093843094: "Build and push" succeeded
> 10:36→10:42, then "Fail the release on fixable CRITICAL" failed 10:43→10:44,
> leaving ghcr.io/ufal/atrium-llm-enrich-llm tagged 0.5.2 + latest + sha-6c71425
> in GHCR carrying the CVE the gate rejected, while the workflow reported
> failure. Consumers pulling `:latest` got the rejected image; the run's red
> tick said otherwise. Not systemic in outcome (pc v1.7.4-beta and alto
> v1.4.3-beta both passed) but systemic in shape.
>
> After this change a failed gate leaves ONLY `sha-<short>` — an immutable,
> unadvertised audit tag that nothing consumes by default.

### The test channel tag

Inside the `tags:` of the "Extract metadata (release tags …)" step (issue #10).

> A moving tag for the pre-release channel (issue #10).
>
> `latest` moves only on a version tag, so until now NOTHING published an image
> tracking `test`. The hub's E2E runs published images, which meant it could only
> ever validate the LAST RELEASE: hub run 31075185518 rejected
> `entities[].type_cnec: null` from nlp-enrich, the fix was already on `test`, and
> no source change could green the run because `:latest` still pointed at the
> pre-fix v0.18.2. A fix that cannot be verified until after it ships is a gate
> working backwards.
>
> `sha-<short>` was already published per push and is the immutable audit trail;
> this adds the MOVING pointer the E2E needs so it can be asked "does the code we
> are about to release still satisfy the contract?" before the tag is cut.
> `latest` is untouched, so nothing consuming released images changes.

### The runner image build argument

Above the `build-args:` of "Build and push" (roadmap B3, atrium-project#69).

> ATRIUM_RUNNER_IMAGE names the tag THIS job publishes, taken from the step that
> computes it (roadmap B3, atrium-project#69). It used to be
> `:${{ github.ref_name }}` = `v1.7.3-beta`, while `type=semver,pattern={{version}}`
> publishes `1.7.3-beta`: every released image's paradata named a tag that does
> not exist in GHCR, and #67 R2's `CreateAction.instrument` would repeat it.
> `meta-release.outputs.version` is the highest-priority tag it emits: the semver
> on a version tag, `test` on a `test` push. With no release tag (only `sha-*` is
> pushed) the immutable `sha-<short>` is the only name the image has.
>
> NOT `sha-<short>` always: that changes on every push, and this value is baked
> into the ENV layer the Dockerfiles' apt-upgrade layer deliberately sits under
> (their "CACHE INTERACTION" note, guarded by test_dockerfile_security_layer.py).
> `test` is stable across `test` pushes and the semver is unique per release, so
> the cache still hits day to day and every release still re-patches.
>
> ATRIUM_RUNNER_REF stays `github.ref_name`: it is a git ref, where the `v` is right.

### SBOM and provenance

On the `sbom:` and `provenance:` inputs of "Build and push" (#18).

> SBOM + provenance as buildkit attestations pushed alongside the image.
> This is the alternative security.reusable.yml's own closing comment
> recommended, and it replaces the anchore/sbom-action job that raced the
> publish and pinned a floating `@v0` major (#18). Attestations are
> attached in the registry, so `docker buildx imagetools inspect` and
> `cosign`/`syft` can read them without a workflow artifact.

### Scanning the published digest

Above "Trivy scan the published digest" (#18, the 2026-07-29 audit), and on its `exit-code: "0"`.

> ── Post-publish vulnerability scan ─────────────────────────────────────
> Scans the image THIS step just pushed, addressed by immutable digest.
>
> Why here and not in security.reusable.yml: that workflow scanned
> `<image>:latest` on the same tag-push event that publishes it, from a
> separate workflow with no ordering guarantee — so it raced, and on a first
> release or a slow push it scanned the PREVIOUS image or failed to pull
> (#18, 2026-07-29 audit). Scanning by digest inside the publishing job
> removes the race by construction. security.reusable.yml keeps the weekly
> `:latest` re-scan, which is about newly-disclosed CVEs, not this build.

> Stays report-only ON PURPOSE. This step's job is to get the full
> CRITICAL+HIGH picture into code scanning on every build; the blocking
> decision is a separate, narrower step below. Keeping them apart means a
> blocked release still records its findings.

### Trivy DB retry

Added 2026-10-29 ([#72](https://github.com/ufal/atrium-project/issues/72)), on "Trivy scan the published digest"
here and on the weekly scan in `security.reusable.yml`.

On 2026-10-26 the weekly scan failed in digital-convert and keyword-extract before it scanned anything: Trivy
0.70 (the one `trivy-action` v0.36.0 installs) asked `mirror.gcr.io/aquasec/trivy-db:2` for its vulnerability
DB and got `404 Not Found` on a layer. Trivy lists `ghcr.io/aquasecurity/trivy-db:2` as a second source, but it
moves on only after an error it counts as temporary (a 429 or 5xx), and a 404 is not one, so the run stopped. The
publishing job downloads the same DB, after the images are pushed: the same outage during a tag would fail the
release.

Both scans are report-only (`exit-code: "0"`), so their failure means Trivy did not run. Each is now
`continue-on-error` and followed by one retry that names `ghcr.io` as the only source (`TRIVY_DB_REPOSITORY`,
`TRIVY_JAVA_DB_REPOSITORY`), a different registry from the mirror. The retry is not `continue-on-error`, so an
outage of both still fails the job, as the Buildx boot retry does. The CVE release gate needs no retry of its
own: it reads the DB the scan or its retry left on disk, fresh, without a download.
`tests/test_trivy_db_retry.py` holds both workflows to this shape.

### The CVE release gate

Above "Fail the release on fixable CRITICAL vulnerabilities" (#18, 2026-07-31).

> The release gate (#18, 2026-07-31) — the policy call that was deferred
> while there had never been a real digest scan to triage. There have now
> been two (translator v0.10.1, page-classification v1.7.1-beta).
>
> Deliberately AFTER the SARIF upload: if this step fails, the findings are
> already in code scanning, so the failure is diagnosable from the Security
> tab rather than only from this log.
>
> Three narrowings, each removing a way this could obstruct rather than protect:
> ```text
>   tags only    — day-to-day pushes and PRs are untouched; this stops a
>                  RELEASE, which is the only thing worth stopping.
>   CRITICAL     — HIGH stays report-only; blocking on it is too noisy to hold.
>   fixable only — `ignore-unfixed` keeps an unpatchable CVE from wedging
>                  releases indefinitely, since there would be no action to take.
> ```
>
> To revert to report-only, set exit-code to "0". Trivy's DB is cached by the
> step above, so this second scan costs a few seconds.

### Promotion

Above "Promote release tags to the scanned digest" (W3).

> ── W3: promote the release tags, only now that the gate has passed ──────
> `if: success()` is what makes this a gate rather than a report: every step
> above must have passed, including "Fail the release on fixable CRITICAL".
>
> `imagetools create` re-points tags at an EXISTING digest in the registry —
> no rebuild, no re-push of layers, so this costs a few seconds and cannot
> produce a different artifact than the one just scanned. `packages: write`
> is already granted by this job.
>
> On a `test` branch push this applies `:test`; on a version tag it applies
> `<semver>` and `latest`. When neither rule matched, `meta-release` emits no
> tags and the step no-ops (guarded below) — a PR build promotes nothing.
