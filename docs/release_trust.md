# Release trust — immutable releases, protected refs, pinned workflows

> **Status:** Active document (added 2026-09-30, issues [#72](https://github.com/ufal/atrium-project/issues/72)
> and [#40](https://github.com/ufal/atrium-project/issues/40)).
> **Scope:** the hub and the six tool repositories.

AMČR builds its production images from ÚFAL release tags, after its own checks: contract tests,
security and licence scans, and a diff review against the last trusted tag (report item 7,
aiscr-docs-pipeline#8). That only works if a tag means one thing, permanently. #72 states it as
an acceptance criterion: *"production release tags cannot be silently retargeted."* The
mechanisms below give it, each with a tool in this repository.

| Mechanism                                                | What it guarantees                                                                                                                         | Tool                                                        |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Immutable releases** (six tool repos)                  | a published release, its tag and its assets never change                                                                                   | `scripts/release_trust.py immutable`                        |
| **Release-tag ruleset** (six tool repos; hub: planned)   | a release tag `v*`, or a hub `doc-schema-v*` freeze, cannot be moved or deleted by anyone; the bypass list is empty                        | `scripts/release_trust.py tag-rules`                        |
| **Tagger ruleset** (all seven; planned, #40)             | only maintainers create, move or delete a tool's `v*` tag or the hub's `v1` and `doc-schema-v*`                                            | `scripts/release_trust.py tag-rules`                        |
| **Branch-history ruleset** (all seven; planned, #40)     | the default branch and `test` cannot be deleted or force-pushed, by anyone                                                                 | `scripts/release_trust.py branch-rules`                     |
| **Pull-request ruleset** (all seven; planned, #40)       | everyone but the maintainers changes the default branch and `test` by a pull request with one approval and the required checks             | `scripts/release_trust.py branch-rules`                     |
| **Reusable workflows pinned by commit** (six tool repos) | a moving `v1` cannot change what a repository's CI runs                                                                                    | `scripts/pin_hub_reusables.py`, `tools/ci/workflow_lint.py` |

"Maintainers" are the repository roles Maintain and Admin: a bypass list can name roles, teams, apps and deploy
keys, but no single user. Admin alone would not do: the maintainer who pushes and tags the releases holds Maintain
in the hub, nlp-enrich, page-classification and translator (read on 2026-11-06). What that means per person, once
the planned rulesets are on:

| Who                                     | Push to the default branch or `test`                        | Push a `v*` tag, move the hub's `v1` | Delete or force-push those branches, move a release tag |
|-----------------------------------------|-------------------------------------------------------------|--------------------------------------|---------------------------------------------------------|
| A maintainer (Maintain or Admin)        | directly; GitHub reports it as a bypass in the push output  | yes                                  | no                                                      |
| A collaborator with Write               | by a pull request, after one approval and the checks        | no                                   | no                                                      |
| Dependabot, `vocab-refresh` (their PRs) | by a pull request, merged by a maintainer or after approval | —                                    | no                                                      |

A rule with an empty bypass list holds for admins too: one who has to break it disables the ruleset first, which
the organisation's audit log records.

## Tag identity

| Name                  | Form                                                                          | Fixed?                                                                       |
|-----------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| Source release (tool) | Git tag `vX.Y.Z[-suffix]`, e.g. `v1.2.0-beta`                                 | yes: tag ruleset and immutable release                                       |
| Image tag             | the same version without the `v`: `ghcr.io/ufal/atrium-<tool>-api:1.2.0-beta` | no: a registry tag can be pushed again                                       |
| Image identity        | the image digest, `…-api@sha256:<64 hex>`                                     | yes                                                                          |
| Development channels  | images `test` and `latest`                                                    | no, by design                                                                |
| Hub workflow pointer  | `v1`                                                                          | no: it moves with every hub change; only maintainers are to move it (step 4) |
| Hub schema freezes    | `doc-schema-v*`                                                               | not yet: no hub ruleset (step 4)                                             |

Protecting a Git tag does not make an image tag immutable. A release is identified by its source
tag and commit and by the digest of each image built from it, so release evidence records all three,
and the S2 pilot names its six images by digest (`k8s_acceptance_runbook.md` §"Image identity").
`test` and `latest` are never a reproducible baseline.

**The hub is the exception.** Its `v1` is a compatibility pointer for the tool repositories'
workflow callers, not a source release, so it is in no fixed-tag rule, only in the rule that leaves moving it to
maintainers (step 4). The tool repositories stop
following it when they call the hub's reusables by commit (step 7). The hub's genuinely fixed
references, the `doc-schema-v*` freezes, are to get their own rule (step 4); on 2026-11-06 the hub has no
ruleset, so `doc-schema-v1` is fixed by convention only.

## State on 2026-11-06

The five releases of 11-06 (#66) change only the batch image's entry point (the hub-canonical
`container_entrypoint.py`) and the version stamps; page-classification stays at `v1.12.3-beta`. Every caller and
`hub-ref` in the six tool repositories is pinned to `da7a066` (`v1`). No repository has a branch ruleset or branch
protection, and the hub has no ruleset at all (`GET /repos/ufal/atrium-project/rulesets` returns `[]`).

| Repository          | Tag ruleset on `v*` | Latest release, immutable, with `images.json` | Hub references by commit (`da7a066`) |
|---------------------|---------------------|-----------------------------------------------|--------------------------------------|
| page-classification | yes                 | yes (`v1.12.3-beta`, 11-04)                   | all callers and action steps         |
| ocr-postprocess     | yes                 | yes (`v1.15.4-beta`)                          | all                                  |
| digital-convert     | yes                 | yes (`v1.4.5-beta`)                           | all                                  |
| nlp-enrich          | yes                 | yes (`v1.3.4-beta`)                           | all                                  |
| keyword-extract     | yes                 | yes (`v1.6.5-beta`)                           | all                                  |
| translator          | yes                 | yes (`v1.7.8-beta`)                           | all                                  |
| hub                 | `doc-schema-v*`: no | —                                             | —                                    |

The pilot set on [#77](https://github.com/ufal/atrium-project/issues/77) is the 11-04 one below.

## State on 2026-11-04

Read on 11-04 with the public API (the pilot releases' `immutable` flag and assets) and the `test` trees (the
callers). These are the six pilot releases, final on [#77](https://github.com/ufal/atrium-project/issues/77). The
callers' column assumes the 11-04 pin sweep of page-classification, ocr-postprocess and nlp-enrich to `51aad6c`
(`v1`); the other three were pinned there with their releases.

| Repository          | Tag ruleset on `v*` | Pilot release, immutable, with `images.json` | Hub references by commit (`51aad6c`) |
|---------------------|---------------------|----------------------------------------------|--------------------------------------|
| page-classification | yes                 | yes (`v1.12.3-beta`)                         | 8 of 8 callers, 1 of 1 action steps  |
| ocr-postprocess     | yes                 | yes (`v1.15.3-beta`)                         | 8 of 8, 1 of 1                       |
| digital-convert     | yes                 | yes (`v1.4.4-beta`)                          | 8 of 8, 1 of 1                       |
| nlp-enrich          | yes                 | yes (`v1.3.3-beta`)                          | 8 of 8, 2 of 2                       |
| keyword-extract     | yes                 | yes (`v1.6.4-beta`)                          | 8 of 8, 3 of 3                       |
| translator          | yes                 | yes (`v1.7.5-beta`)                          | 8 of 8, 2 of 2                       |

**Tags without a release.** Seven `v*` tags of the pilot round exist that no GitHub Release certifies, and by
`ci_policy.md` they are not releases (older tags without a release, such as page-classification
`v1.10.0-beta`–`v1.10.4-beta` or the `v0.*` history, predate immutable releases and are not listed):
- digital-convert `v1.4.3-beta`: its tag push started no workflow run;
- keyword-extract `v1.6.3.-beta`: a mistyped tag, which started no run;
- keyword-extract `v1.6.3-beta`: its CVE gate stopped on a registry error;
- translator `v1.7.3-beta`: Trivy's own download failed;
- translator `v1.7.4-beta`: its tag push started no workflow run.
- translator `v1.7.6-beta` (11-05): created on `5b25f83`, the commit before its version bump, and pushed
  with that commit; Release Bundle 42103826703 stopped at the version gate (tag 1.7.6, CITATION 1.7.5).
  `v1.7.8-beta` carries it ([Tagging a release](#tagging-a-release)).
- translator `v1.7.7-beta` (11-06): tagged on `ec694d3`, three minutes after Docker Build & Push had failed there
  on a leftover test; Release Bundle 42200410454 stopped in the same test job. `v1.7.8-beta` carries it.

The next patch number shipped the same code each time. Some of their images were published before the failure
(translator's `:latest` pointed at the `1.7.3-beta` image until `v1.7.5-beta` replaced it on 11-04). The tag rule
refuses their deletion to everyone: its bypass list is empty, so an admin would have to disable it first, which the
organisation's audit log records.

## State on 2026-10-29

Read with the public API and the `test` trees (no admin rights needed): the rulesets with
`GET /repos/ufal/<repo>/rulesets`, the releases' `immutable` flag, and the callers in each
`.github/workflows/`. The four rulesets stranak added on 10-29 (10:18–10:19 UTC,
[#72](https://github.com/ufal/atrium-project/issues/72)) came before that day's six tags, so every pilot
release is covered. The callers' column is the pin sweep of 10-29 (12:15–12:17 UTC): every caller and
action step at the hub commit `b07090f` (`v1` then), with `require-sha-pins` on; no reference to `@v1` is
left.

| Repository          | Tag ruleset on `v*`                  | Latest release immutable, with `images.json` | Hub references by commit (`b07090f`) |
|---------------------|--------------------------------------|----------------------------------------------|--------------------------------------|
| page-classification | yes (`Protect v* Tags`, 10-19)       | yes (`v1.12.0-beta`)                         | 8 of 8 callers, 1 of 1 action steps  |
| ocr-postprocess     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.15.0-beta`)                         | 8 of 8, 1 of 1                       |
| digital-convert     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.4.0-beta`)                          | 8 of 8, 1 of 1                       |
| nlp-enrich          | yes (`Protect v* Tags`, 10-19)       | yes (`v1.3.0-beta`)                          | 8 of 8, 2 of 2                       |
| keyword-extract     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.6.0-beta`)                          | 8 of 8, 3 of 3                       |
| translator          | yes (`Protect v* Tags`, 10-29)       | yes (`v1.7.0-beta`)                          | 8 of 8, 2 of 2                       |
| hub                 | `doc-schema-v*`: **no**              | —                                            | —                                    |

An action step is a step that runs one of the hub's composite actions
(`ufal/atrium-project/.github/actions/lane-failure-issue`, #81); step 7 pins it with the callers.

Releases from before immutability was switched on stay mutable (page-classification up to
`v1.9.4-beta`, nlp-enrich up to `v1.1.0-beta`, translator up to `v1.4.0-beta`); AMČR mirrors only
the immutable ones. The six hand-made rulesets refuse update, deletion and non-fast-forward on
`refs/tags/v*`, so `tag-rules` keeps them and updates them in place.

## What the release workflows need — nothing

An immutable release refuses an asset added after it is published. All six `release.yml`
attach `openapi.json`, `openapi.json.sha256` and, where they have one, their bundle in the one
`softprops/action-gh-release` step that creates the release, and that action (v3.0.3, pinned)
creates a non-prerelease release as a **draft**, uploads the assets, then publishes it. So they
work unchanged once immutability is on. `tools/ci/workflow_lint.py` keeps it that way: it fails
a `prerelease: true` release that is not also a draft (the action publishes those first) and
any `gh release upload` or upload-release-asset step after the release exists.

**The image a release certifies (#81, decided 10-22).** A repository that has moved its image job into
`release.yml` (digital-convert first; [`ci_policy.md`](ci_policy.md), Releases) attaches `images.json` in
that same step: the reusable's `images` job reads the digest each promoted tag resolves to, and the
release job writes it out before the release exists. digital-convert released this way first
(`v1.2.2-beta`); the other five followed with their releases of 26–28 October (nlp-enrich `v1.2.0-beta`
first), and all six pilot releases of 29 October certify their images. The image job is a cross-repo
`uses:`, the one exception to "a release gate must not depend on a cross-repo `uses:` resolving at tag-push time"
(`docker_gha_roadmap.md` §3.3): only the hub's reusable builds, probes and scans the image a release must
now certify. It is adopted at `v1`, then by commit with the other callers (step 7 below). The version
guard and the OpenAPI checks stay vendored.

What changes for people: a published release cannot be edited. A mistake in a release is fixed
by the next version, never by moving its tag or replacing an asset.

## Tagging a release

A tag that misses is a version lost: the tag rule keeps it, and the fix is the next version. Three ways a tag
missed in November 2026:

| What happened                                | Example                                                                                                     | What stops it                                 |
|----------------------------------------------|-------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| The tag on a commit without the version bump | translator `v1.7.6-beta`: tagged before the bump was committed, pushed with it                              | the version gate, which then fails the run    |
| The tag on a commit whose CI is red          | translator `v1.7.7-beta`: tagged three minutes after Docker Build & Push failed on that commit              | the release's test job, which then fails      |
| A tag push that starts no run                | translator `v1.7.4-beta`, digital-convert `v1.4.3-beta`, keyword-extract `v1.6.3.-beta`; cause not recorded | nothing: the release silently does not happen |

GitHub creates no push event for tags when more than three are pushed at once, which `git push --tags` from a
checkout with stale local tags does without a word; the filters (`tags: ['v*']` in all six) and the pinned hub
commits were not the cause.

**Tag with [`scripts/tag_release.py`](../scripts/tag_release.py)**, from the tool checkout, after the release
commit is pushed:

```bash
python3 ../atrium-project/scripts/tag_release.py v1.7.8-beta            # --dry-run to only check
```

It refuses a malformed tag (`v1.6.3.-beta`), uncommitted changes, a HEAD that is not `origin/test`, a tag the
version gate would fail (the repository's own `check_version.py --require-tag`), a tag that exists on the remote,
and, with `gh`, a commit whose push runs failed or are still going (`v1.7.7-beta`; `--no-ci-check` skips that). A
tag that exists only locally was never pushed, so its version is unused: delete it with `git tag -d` and run again.
It then creates an annotated tag on HEAD and pushes that one ref. With `gh` it waits for the Release Bundle run of
the tag and prints its URL.

**When a tag started no run**, dispatch the release on the tag: *Actions → Release Bundle → Run workflow*, with the
tag chosen under "Use workflow from", or `gh workflow run release.yml --ref <tag>`. On a tag ref that run **is** the
release, not a dry run: `release.yml`'s steps test `github.ref_type == 'tag'` and the reusable's probe and publish
jobs test `startsWith(github.ref, 'refs/tags/v')`. A dry run is a dispatch on a branch.

## Order

1. **Land the hub**, then move `v1` to it (as for every hub change). Then land the tool
   repositories.
2. **Read the current state** — this is also the "before" evidence:

   ```bash
   python3 scripts/release_trust.py status
   ```

3. **Immutable releases, before the next tool release**, so that every release AMČR reviews from
   then on is immutable (report item 7 asks for this date):

   ```bash
   python3 scripts/release_trust.py immutable --dry-run   # read what will be sent
   python3 scripts/release_trust.py immutable
   ```

4. **Tag rules.** Two rulesets per repository: the release tags fixed for everyone (`v*` in the tool
   repositories, where the hand-made `Protect v* Tags` is updated in place and keeps its name; `doc-schema-v*` in
   the hub), and the tags only maintainers push (`v*`; in the hub `v1` and `doc-schema-v*`):

   ```bash
   python3 scripts/release_trust.py tag-rules --dry-run   # read what will be sent
   python3 scripts/release_trust.py tag-rules
   ```

   The hub's `v1` keeps moving with each hub change (§"Tag identity"), but only a maintainer moves it.

5. **Branch rules.** First read the names of the checks that run on `test`, then choose which to
   require. Require only checks that run on `pull_request` and need no secret, or a pull request from a fork
   never merges: in the tool repositories `pre-commit / Lint`, `workflow-lint / Verify Workflow and Caller
   Policy`, `check-drift / Verify Canonical Paradata Integration` and `build-and-push / test`; in the hub
   `pre-commit / Lint`, `workflow-lint / Verify Workflow and Caller Policy`, `Test canonical shared modules` and
   `Build the aggregate site`. Not the hub's fast lanes (`all-repos-smoke` runs on push only). A check name must
   match exactly, including the caller's job name:

   ```bash
   python3 scripts/release_trust.py checks --repo atrium-translator
   python3 scripts/release_trust.py branch-rules --repo atrium-translator --dry-run \
       --checks "check-drift / Verify Canonical Paradata Integration,workflow-lint / Verify Workflow and Caller Policy"
   ```

   This writes two rulesets: no deletion and no force push for anyone, and changes by a pull request with one
   approval and the named checks for everyone but the maintainers. Without `--checks` the second still asks for a
   reviewed pull request.

   **Check the bypass on one repository first**, one where the maintainer who releases holds Maintain only
   (nlp-enrich): after the run, `status` read with that maintainer's `gh` login must show `you: always` on
   the two maintainers' rulesets, and the web UI must name the roles Maintain and Repository admin. Then the other
   six.

6. **Tag the releases.** The first immutable ones.
7. **Pin the reusable workflows** to the commit `v1` points to, in one sweep, and commit the
   callers in each tool repository:

   ```bash
   python3 scripts/pin_hub_reusables.py --sha "$(git rev-parse 'v1^{commit}')" --check   # what would change
   python3 scripts/pin_hub_reusables.py --sha "$(git rev-parse 'v1^{commit}')"
   ```

   `^{commit}` matters if `v1` is ever an annotated tag: its own SHA names the tag object, which
   `uses:` cannot run (the script refuses one).

   Every `uses: ufal/atrium-project/.github/workflows/<name>.reusable.yml@v1` becomes
   `@<sha>  # v1`, and the two reusables that read hub files (`para-drift`, `workflow-lint`) get
   `hub-ref: <sha>` too. Every step that runs a hub composite action
   (`ufal/atrium-project/.github/actions/<name>@v1`) gets the same `@<sha>  # v1`, so no step keeps
   following the moving tag; `--require-sha-pins` refuses an action left at `@v1` as well. The linter already accepts both forms and fails a caller whose pin and
   `hub-ref` differ, so a Dependabot bump that moves only one of them turns red.
8. **The pin is mandatory from the sweep on.** The sweep also writes `require-sha-pins: true`
   into each tool repository's workflow-lint caller, so that repository's lint refuses a hub
   reusable left at `@v1`. The input defaults to false and must stay so: the hub's own callers
   (`hub-self-check.yml`) call the reusables by path, with `hub-ref: ${{ github.sha }}`, and making
   the flag the reusable's default would fail them. From then on a hub change reaches a tool repository only through a reviewed pin move
   (the same script with a new `--sha`, or a Dependabot PR). A change to the canonical shared
   files moves the copies and the pin in the same tool commit: `para-drift` reads the canonical
   files at the pin ([`docker_gha.md`](docker_gha.md), "The procedure"; red in all six on
   2026-10-28 when only the copies moved).
9. **Post the evidence**: the `status` output on #72 and #40.

## Reading the result

`status` prints, per repository, whether immutable releases are on and every ruleset with its
target, enforcement, refs, rules and bypass, e.g. (read by a maintainer with Maintain; GitHub shows the bypass
list itself only to admins):

```text
ufal/atrium-translator: immutable releases on
  ruleset 'Protect v* Tags' [tag, active] on refs/tags/v*: deletion, non_fast_forward, update; bypass: not shown; you: never
  ruleset 'ATRIUM tags only maintainers push (atrium-project#40)' [tag, active] on refs/tags/v*: creation, update, deletion, non_fast_forward; bypass: not shown; you: always
  ruleset 'ATRIUM branch history (atrium-project#40)' [branch, active] on ~DEFAULT_BRANCH, refs/heads/test: deletion, non_fast_forward; bypass: not shown; you: never
  ruleset 'ATRIUM changes by pull request (atrium-project#40)' [branch, active] on ~DEFAULT_BRANCH, refs/heads/test: pull_request; bypass: not shown; you: always
```

The script is idempotent: a ruleset is found by its name and updated in place, so re-running a
command after a change of mind replaces the ruleset rather than adding a second one.

## What the trust gate can read from a release

* **`openapi.json`** and its `.sha256`: the contract the activities are generated from (#32).
* **`.github/production-image.json`** at the tag: the first-party files the production image
  can run — its stage's code, the hub-canonical shared modules and any pinned copy of another
  repository's layer — checked by `tools/ci/image_closure.py` in every tool repository's CI.
  A diff review that covers *"only the files that go into the image we use"* (report item 7)
  can start from that list (plus the shared modules of `docs/templates/shared/MANIFEST.json`).
* **The image** itself: `docker-tool.reusable.yml` fails a probed image that has a forbidden
  distribution installed (PyMuPDF by default) before it is published.
