---
title: page-classification — History
nav_order: 34
status: published
round: 6
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

## 2026-06 → 08 · Retraining on the licensed dataset (#15)

The dataset had 318 pages removed for licensing reasons, and the five best models had to
be retrained without them. The question was whether that changed anything.

The path taken was to make the *split* reproducible rather than regenerate it:
`--folds_csv` reads train/dev/test assignments from an explicit CSV and excludes pages
absent from it, so a model can be retrained on the same split it originally saw. The
registry gained `REVISION_BEST_FOLDS` and the rule `splitN ↔ foldN ↔ seed 420+(N−1)`.

**The answer, measured on 2026-06-29:** run page by page on a 229-page sample, the
`v*.4` ensemble disagreed with `v*.3` on **24 pages** — and all 24 were pages on which
the `v*.3` models already disagreed among themselves. Removing the 318 pages moved only
decisions that were ambiguous to begin with.

The same work made `split_data_from_folds` robust to pandas 3.0, which no longer coerces
blank fold cells silently; `tests/test_folds_split.py` covers the split.

## 2026-07 → 08 · The Agent Skill (#26)

The classifier was packaged as an Agent Skill on the `agent-skill` branch, following an
existing pattern rather than inventing one: a `SKILL.md` with frontmatter and agent
guidelines, plus a **stdlib-only client** (`scripts/atrium_classify.py`) that wraps the
already-existing FastAPI service. The two-phase workflow — check `/info`, then classify —
means the same client points at any hosted endpoint by changing `--base-url` or
`ATRIUM_PC_URL` and nothing else.

Both issues closed on 2026-08-02. See [Agent skills](../../agent-skills.md).

## 2026-08 · Guarding the install and the runtime

Two dependency rules date from this month, and each exists because of a failure that the
test suite could not see on its own.

**numpy stays below 2.5.** numpy 2.5 requires Python 3.12, while every image and CI job
here runs 3.11, so a floating pin breaks the install. `setup/requirements.txt` pins
numpy below 2.5 and `dependabot.yml` ignores the bump, so the same upgrade cannot arrive
by pull request.

**The service's requirements must include its server.** The test suite drives the
application in-process through `TestClient`, which needs no ASGI server, so a missing
`uvicorn` would only show when a container started. `tests/test_service_runtime_deps.py`
parses `docker-compose.yml` and `setup_api_service.sh` for the console entry points they
invoke and asserts each is declared in an installed requirements file — so pruning that
list fails the fast lane rather than the deployment.

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

## 2026-09 · The ensemble moves to `v*.4` (#48)

Release **v1.8.0-beta** switched the canonical ensemble — `--best`, and the service's
`version=all` — from `v*.3` to the retrained `v*.4` generation. The switch is one dict in
`model_registry.py`, and it was held back until the Hub was right: for three days all five
`v*.4` revisions served the same `regnety_160` checkpoint, so flipping the keys would
have averaged one model with itself five times while still reporting a five-model
ensemble. The revisions were re-uploaded and checked — five distinct architectures, five
distinct checkpoint sizes — before the switch, and `tests/test_best_ensemble_distinct.py`
reads each revision's configuration from the Hub so the same mistake cannot ship.

The published accuracy tables describe `v*.3`; the retraining comparison above is the
measurement that connects the two generations.

## Branches

| Branch        | What it is                                                      |
|---------------|-----------------------------------------------------------------|
| **`vit`**     | the default branch and the code                                 |
| `test`        | the integration branch that changes are staged on               |
| `master`      | a short index pointing at the `vit` and `clip` variants         |
| `clip`        | a CLIP-based variant with its own Hugging Face repository       |
| `agent-skill` | the Agent Skill packaging (#26)                                 |
| `gh-pages`    | the landing card at `ufal.github.io/atrium-page-classification` |

The `vit` and `clip` names are model families, not development stages: the repository
began as a comparison of the two approaches.

## The raw records

Not republished here. On GitHub:

* [`agent_dev_logs/DEVLOG.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/DEVLOG.md) — the timeline index this page condenses
* [`agent_dev_logs/digests/48.digest.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/digests/48.digest.md) — the `v*.3` vs `v*.4` comparison
* [`agent_dev_logs/plans/48.plan.md`](https://github.com/ufal/atrium-page-classification/blob/vit/agent_dev_logs/plans/48.plan.md)

## Sources

Condensed from `ufal/atrium-page-classification` at branch **`vit`**, commit `adee922`
(2026-09-23). This table records **provenance**, not a build instruction.

| Source                                                    | What was taken from it                                                                                                                |
|-----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `agent_dev_logs/DEVLOG.md`                                | the timeline from 2026-06-25 to 2026-09-07; the window from 2026-08-02 is reconstructed from `CONTRIBUTING.md` and the commit history |
| `CONTRIBUTING.md` § Release History                       | the v1.8.0-beta ensemble switch                                                                                                       |
| `model_registry.py`                                       | the re-upload check that preceded the switch                                                                                          |
| `agent_dev_logs/digests/48.digest.md`, `plans/48.plan.md` | the `v*.3` / `v*.4` comparison                                                                                                        |
