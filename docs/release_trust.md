# Release trust — immutable releases, protected refs, pinned workflows

> **Status:** Active document (added 2026-09-30, issues [#72](https://github.com/ufal/atrium-project/issues/72)
> and [#40](https://github.com/ufal/atrium-project/issues/40)).
> **Scope:** the hub and the six tool repositories.

AMČR builds its production images from ÚFAL release tags, after its own checks: contract tests,
security and licence scans, and a diff review against the last trusted tag (report item 7,
aiscr-docs-pipeline#8). That only works if a tag means one thing, permanently. #72 states it as
an acceptance criterion: *"production release tags cannot be silently retargeted."* Three
mechanisms give it, each with a tool in this repository.

| Mechanism                                                | What it guarantees                                                                                                                                           | Tool                                                        |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Immutable releases** (six tool repos)                  | a published release, its tag and its assets never change                                                                                                     | `scripts/release_trust.py immutable`                        |
| **Tag ruleset** (six tool repos; the hub's freezes)      | a release tag `v*`, or a hub `doc-schema-v*` freeze, cannot be moved or deleted, except by a repository admin, and GitHub logs that bypass                   | `scripts/release_trust.py tag-rules`                        |
| **Branch ruleset** (all seven)                           | the default branch and `test` cannot be deleted or force-pushed; changes arrive by pull request, optionally with required checks; admins may bypass (logged) | `scripts/release_trust.py branch-rules`                     |
| **Reusable workflows pinned by commit** (six tool repos) | a moving `v1` cannot change what a repository's CI runs                                                                                                      | `scripts/pin_hub_reusables.py`, `tools/ci/workflow_lint.py` |

## Tag identity

| Name                  | Form                                                                          | Fixed?                                 |
|-----------------------|-------------------------------------------------------------------------------|----------------------------------------|
| Source release (tool) | Git tag `vX.Y.Z[-suffix]`, e.g. `v1.2.0-beta`                                 | yes: tag ruleset and immutable release |
| Image tag             | the same version without the `v`: `ghcr.io/ufal/atrium-<tool>-api:1.2.0-beta` | no: a registry tag can be pushed again |
| Image identity        | the image digest, `…-api@sha256:<64 hex>`                                     | yes                                    |
| Development channels  | images `test` and `latest`                                                    | no, by design                          |
| Hub workflow pointer  | `v1`                                                                          | no: it moves with every hub change     |
| Hub schema freezes    | `doc-schema-v*`                                                               | yes: tag ruleset                       |

Protecting a Git tag does not make an image tag immutable. A release is identified by its source
tag and commit and by the digest of each image built from it, so release evidence records all three,
and the S2 pilot names its six images by digest (`k8s_acceptance_runbook.md` §"Image identity").
`test` and `latest` are never a reproducible baseline.

**The hub is the exception.** Its `v1` is a compatibility pointer for the tool repositories'
workflow callers, not a source release, so no tag rule covers it. The tool repositories stop
following it when they call the hub's reusables by commit (step 7). The hub's genuinely fixed
references, the `doc-schema-v*` freezes, have their own rule.

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

4. **Tag rules** (`v*` in the tool repositories; `doc-schema-v*` in the hub):

   ```bash
   python3 scripts/release_trust.py tag-rules
   ```

   The hub's `v1` is not covered and keeps moving with each hub change (§"Tag identity").

5. **Branch rules.** First read the names of the checks that run on `test`, then choose which to
   require (the #40 plan names the `docker`, `para-drift`, `api-contract`, `pre-commit` and
   `security` callers in the tool repos; `hub-self-check`, `all-repos-smoke`, `codeql` and
   `pre-commit` in the hub). A check name must match exactly, including the caller's job name:

   ```bash
   python3 scripts/release_trust.py checks --repo atrium-translator
   python3 scripts/release_trust.py branch-rules --repo atrium-translator \
       --checks "check-drift / Verify Canonical Paradata Integration,workflow-lint / Verify Workflow and Caller Policy"
   ```

   Without `--checks` the ruleset still refuses deletion and force pushes and asks for a pull
   request. Admins can bypass it, so direct pushes by the maintainers keep working and are
   logged as bypasses.

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
target, enforcement, refs and rules, e.g.:

```text
ufal/atrium-translator: immutable releases on
  ruleset 'ATRIUM release tags (atrium-project#72)' [tag, active] on refs/tags/v*: update, deletion
  ruleset 'ATRIUM integration branches (atrium-project#40)' [branch, active] on ~DEFAULT_BRANCH, refs/heads/test: deletion, non_fast_forward, pull_request
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
