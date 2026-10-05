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
| **Tag ruleset** (all seven)                              | a release tag, `v1` or `doc-schema-v*` cannot be moved or deleted, except by a repository admin, and GitHub logs that bypass                                 | `scripts/release_trust.py tag-rules`                        |
| **Branch ruleset** (all seven)                           | the default branch and `test` cannot be deleted or force-pushed; changes arrive by pull request, optionally with required checks; admins may bypass (logged) | `scripts/release_trust.py branch-rules`                     |
| **Reusable workflows pinned by commit** (six tool repos) | a moving `v1` cannot change what a repository's CI runs                                                                                                      | `scripts/pin_hub_reusables.py`, `tools/ci/workflow_lint.py` |

## What the release workflows need — nothing

An immutable release refuses an asset added after it is published. All six `release.yml`
attach `openapi.json`, `openapi.json.sha256` and, where they have one, their bundle in the one
`softprops/action-gh-release` step that creates the release, and that action (v3.0.3, pinned)
creates a non-prerelease release as a **draft**, uploads the assets, then publishes it. So they
work unchanged once immutability is on. `tools/ci/workflow_lint.py` keeps it that way: it fails
a `prerelease: true` release that is not also a draft (the action publishes those first) and
any `gh release upload` or upload-release-asset step after the release exists.

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

4. **Tag rules** (`v*` in the tool repositories; `v1` and `doc-schema-v*` in the hub):

   ```bash
   python3 scripts/release_trust.py tag-rules
   ```

   Moving `v1` stays possible for repository admins; anyone else's push is refused.

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
   `hub-ref: <sha>` too. The linter already accepts both forms and fails a caller whose pin and
   `hub-ref` differ, so a Dependabot bump that moves only one of them turns red.
8. **Once all six are pinned**, make the pin mandatory: pass `--require-sha-pins` to
   `workflow_lint.py` in `workflow-lint.reusable.yml`. From then on a hub change reaches a tool
   repository only through a reviewed pin move (the same script with a new `--sha`, or a
   Dependabot PR).
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
