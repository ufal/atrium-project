---
title: page-classification — History
nav_order: 34
status: published
round: 3
issue: 57
repo: atrium-page-classification
role: history
---

# page-classification — History

Why the tool is shaped the way it is, in the order it happened. Condensed from the
repository's own `DEVLOG.md`, which is itself a derived timeline index over the issue
exports, digests and plans in `agent_dev_logs/`. **Those raw records are not republished
here** — they are linked, and they remain the source of truth.

For the release-by-release view, see [Changelog](changelog.md). For the cross-repository
chronology, see [Development history](../../development-history.md).

## The shape of the record

`agent_dev_logs/` in this repository is small: one `DEVLOG.md` covering 2026-06-25 →
2026-09-07, plus a digest and plan for issue #48. The window from 2026-08-02 to 09-06 was
reconstructed from `CONTRIBUTING.md`'s release table and commit history rather than from
digests, because the digests did not exist yet — the DEVLOG says so itself, which is the
kind of self-correction worth preserving.

## 2026-06 → 08 · Retraining on the licensed dataset (#15)

The dataset had 318 pages removed for licensing reasons, and the five best models had to
be retrained without them. The question was whether that changed anything.

The path taken was to make the *split* reproducible rather than regenerate it:
`--folds_csv` reads train/dev/test assignments from an explicit CSV and excludes pages
absent from it, so a model can be retrained on the same split it originally saw. The
registry gained `REVISION_BEST_FOLDS` and the rule `splitN ↔ foldN ↔ seed 420+(N−1)`.

**The answer, measured on 2026-06-29:** `v*.4` against `v*.3` differed on **24 of 229
samples**, down from 25 — and all 24 were cases the `v*.3` ensemble already disagreed
about internally. Removing the 318 pages moved only the already-ambiguous decisions.

A real defect surfaced during the same work and is worth recording because of how it was
caught: `split_data_from_folds` crashed under pandas ≥ 3.0 on roughly 225 blank `fold1`
cells, which earlier pandas had silently coerced. `tests/test_folds_split.py` (18 tests)
was written around it.

## 2026-07 → 08 · The Agent Skill (#26)

The classifier was packaged as an Agent Skill on the `agent-skill` branch, following an
existing pattern rather than inventing one: a `SKILL.md` with frontmatter and agent
guidelines, plus a **stdlib-only client** (`scripts/atrium_classify.py`) that wraps the
already-existing FastAPI service. The two-phase workflow — check `/info`, then classify —
means the same client points at a future LINDAT-hosted endpoint by changing
`--base-url` or `ATRIUM_PC_URL` and nothing else.

Both issues closed on 2026-08-02. See [Agent skills](../../agent-skills.md).

## 2026-08 · Two defects the test suite could not see

Both are instructive, and both were found by review rather than by CI.

**The numpy pin had drifted past Python 3.12.** `setup/requirements.txt` allowed numpy
2.5.x, which requires Python 3.12, while every image and CI job here runs 3.11. `pip`
failed outright with "No matching distribution found". The hub's cross-repository audit
caught it live on 07-30; it was fixed here on 08-04 by floor-pinning numpy below 2.5 and
adding a `dependabot.yml` ignore rule so the same bump cannot recur.

**`service/requirements.txt` declared no ASGI server at all.** Six pytest and contract
dependencies, and nothing to actually serve the application. Nothing noticed, because the
test suite drives the app in-process through `TestClient` — no server needed — and CI only
*built* the image. `docker compose --profile api up api` would have died at container start
with "executable file not found" the first time anyone ran it for real.

The fix was not just the missing line. `tests/test_service_runtime_deps.py` now parses
`docker-compose.yml` and `setup_api_service.sh` for the console entry points they invoke
and asserts each is declared in an installed requirements file — so pruning that list again
fails the fast lane rather than the deployment.

## 2026-08 → 09 · Hardening, and the hub taking over the plumbing

From 08-02 onward almost all activity was infrastructure, driven by the hub's cross-repo
review passes: the shared `atrium_document.py` template re-vendored as its contract
tightened, all seven workflow references repinned from `@test` to the tagged `@v1`, and
CI concurrency scoped by `github.event_name` so a push can no longer cancel a scheduled
run.

One ordering detail from this window is invisible on inspection and worth knowing: the
Dockerfile's `apt-get upgrade` layer must sit **below** the `ENV` block that embeds
`ATRIUM_RUNNER_REF`. CI passes that as `github.ref_name`, unique per release tag, which
busts the layer on every release and only on a release. With the build using
`cache-from: type=gha`, a layer in the wrong place looks correct and patches nothing.
`tests/test_dockerfile_security_layer.py` pins the ordering — it became a canonical shared
file across the ecosystem after the base-image CVE incident that
[the translator hit first](../translator/history.md#the-base-image-that-blocked-a-release).

## 2026-09 · The one open question (#48)

`CONTRIBUTING.md` for v1.8.0-beta says the switch to the `v*.4` ensemble shipped, and it
did. What has not happened is the comparison: **no accuracy figures have been published
for the `v*.4` models**, only the 24-of-229 prediction diff above. Every number in the
README describes `v*.3`.

That is the live gap, and it is the reason [Overview](index.md#how-well-it-works) and
[Reference](reference.md#known-drift--read-this-before-trusting-a-number) both flag the
published metrics rather than simply quoting them.

## Branches, honestly

| Branch        | What it is                                                      |
|---------------|-----------------------------------------------------------------|
| **`vit`**     | the default branch and the code                                 |
| `test`        | staging; currently the same commit as `vit`                     |
| `master`      | a 46-line index pointing at the `vit` and `clip` variants       |
| `clip`        | a CLIP-based variant with its own Hugging Face repository       |
| `agent-skill` | the Agent Skill packaging (#26)                                 |
| `gh-pages`    | the landing card at `ufal.github.io/atrium-page-classification` |

`CONTRIBUTING.md` documents only `test` and `master` and instructs contributors to
"always branch from `test`". Someone who clones the default branch and reads that file
receives contradictory instructions. This is recorded rather than resolved — the branch
model belongs to the repository's own maintainers.

## The raw records

Not republished here. On GitHub:

* [`agent_dev_logs/DEVLOG.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/DEVLOG.md) — the timeline index this page condenses
* [`agent_dev_logs/digests/48.digest.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/digests/48.digest.md) — the open `v*.3` vs `v*.4` question
* [`agent_dev_logs/plans/48.plan.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/plans/48.plan.md)
* [`agent_dev_logs/issues/`](https://github.com/ufal/atrium-page-classification/tree/vit/agent_dev_logs/issues) — the verbatim issue exports

## Sources

Condensed from `ufal/atrium-page-classification/agent_dev_logs/DEVLOG.md` and
`CONTRIBUTING.md` at branch **`vit`**, commit `8415ce7` (2026-09-21). This table records
**provenance**, not a build instruction.
