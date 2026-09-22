---
title: translator — History
nav_order: 54
status: published
round: 3
issue: 57
repo: atrium-translator
role: history
---

# translator — History

Why the tool is shaped the way it is, in the order it happened. Condensed from the
repository's own `DEVLOG.md`, itself a derived timeline index over the issue exports,
digests and plans in `agent_dev_logs/`. **Those raw records are not republished here** —
they are linked, and they remain the source of truth.

For the release-by-release view, see [Changelog](changelog.md). For the cross-repository
chronology, see [Development history](../../development-history.md).

## 2026-06 · Choosing a translation model, and never finishing the choice (#4)

The repository opened with one question: which base model should do the translating? A
candidate comparison was posted within a day — CUBBITT as the incumbent baseline, against
Cohere Command A, GLM-5.2, MADLAD-400, NLLB-200, Tower+, Opus-MT and the commercial APIs —
scored on language coverage, licence and cost. EuroLLM was added as a self-hostable option
and the whole thing was written up as a phased plan with a full licensing recipe.

What came out of it is the architecture rather than an answer: a pluggable
`TranslationBackend` protocol with `lindat` and `openai_compatible` registered, and a
CTranslate2 scaffold deliberately left unregistered so that importing the module never
pulls in heavyweight dependencies.

**The bake-off that was supposed to settle it has never been run.** `eval/bakeoff.py`
exists and is complete; its own test file states outright that the live comparison has
never executed, and the issue plan still lists it as pending. The design phases closed;
the measurement phase did not. That is why
[Overview](index.md#how-well-it-translates-unknown-and-that-is-the-honest-answer) says
plainly that no quality metric exists rather than quoting one from the design document.

## 2026-06 → 07 · Making ALTO output structurally honest

The hard problem in this tool is not translation, it is that ALTO stores text *spatially*.
Each `TextLine` holds a sequence of `String` elements and each `String` carries one token
plus its position on the page. Translating line by line loses cross-line context and
produces poor output; translating the block produces fluent text and discards the structure
that has to be preserved.

The resolution — the **dual-pass reconstruction** described in
[Reference](reference.md#alto-dual-pass-reconstruction) — is to do both and use the second
pass only as a ruler. It is the single most consequential design decision in the repository,
and it is the reason 7.3 % of output boxes no longer hold exactly one word: the word-to-box
correspondence in a translated ALTO is *manufactured by the bucketing*, not observed.

That fact is what later settled the `append` question. A per-`String` English alternative
would not be an alternative reading of that word — it would be whichever token the bucketing
happened to land there. So `append` labels the block instead.

`v0.8.0` then moved the API calls from per-block to per-page, which is where the reduction
from ~3,288 calls to ~158 on the 79-page sample comes from.

## 2026-07 → 09 · Twelve-factor work, none of it visible on GitHub

Between 2026-09-07 and 09-12 a run of commits landed against hub issues that have no
counterpart in this repository's own tracker — the `api` Dockerfile stage so a runnable API
image exists to publish; `atrium_rocrate.py` vendored under drift control; `$PORT` honoured
rather than baked into the entrypoint; `TRANSLATION_URL` and `UDPIPE_URL` made attachable;
the first `.env.example`; and the logging contract (one `basicConfig`, in `__main__` only).

This is worth recording because the repository's issue list does not show it. Someone
reading only the two open issues here would conclude nothing happened in that window.

## The base image that blocked a release

On 2026-09-13 a release was stopped by something the build *inherited* rather than anything
it contained.

`python:3.11-slim` is a floating tag and nothing in this ecosystem bumps it — no repository
declares a `docker` Dependabot ecosystem — so the base layer is whatever Docker Hub last
rebuilt. On that day it carried `perl-base` 5.40.1-6 with three fixable CRITICAL CVEs
(CVE-2026-13221, CVE-2026-42496, CVE-2026-8376), all already fixed upstream.

The hub's release gate blocks exactly that class. And because the promotion step runs
`if: success()`, **a blocked release still publishes — by digest only, with no `:<version>`
and no `:latest` tag.** That is what happened to `v1.0.0-beta`, on both matrix targets.

Two things made it hard to see, and both generalise:

* **The gate only runs on tags.** The identical commit passes on `master` and on `test`.
  The failure appears at the worst possible moment and never during development.
* **A cache-served apt layer looks correct and patches nothing.** The build uses
  `cache-from: type=gha`, so the `apt-get upgrade` has to sit *below* the `ENV` block
  embedding `ATRIUM_RUNNER_REF` — CI passes that as `github.ref_name`, unique per release
  tag, which busts the layer on every release and only on a release.

`v1.1.0-beta` released green on 2026-09-14 with the fix. **This repository was the only one
that had it**, and two days later `atrium-nlp-enrich` hit the identical three CVEs for the
identical reason. The layer has since been ported to the remaining four repositories and
`tests/test_dockerfile_security_layer.py` promoted to a canonical shared file, so a
repository that loses the ordering goes red *before* a release rather than during one.

## 2026-09-13 · Five contracts that were announced but inert

A production-readiness review, not a filed issue, found five defects that the test suite
could not see because each lived somewhere it was structurally not looking. They are
tabulated in [Changelog → v1.0.0-beta](changelog.md#v100-beta--the-release-where-five-contracts-became-real);
what is worth drawing out here is the pattern.

Each one was a *declared* behaviour that no test exercised end to end. The retry limits were
read and then clamped away. The upload limit was checked after the read it was supposed to
prevent. The exit codes existed in the documentation and nowhere in the control flow. The
release zip was assembled by a list nobody had re-derived from the imports. In each case the
documentation was correct about the intent and wrong about the system.

The fix in each case was a guard, and each guard was confirmed by reintroducing the defect
and watching it go red — which is the standard this ecosystem holds itself to and the reason
these are recorded rather than quietly patched.

The same round closed the live-backend gap `scheduled-smoke.yml` had been naming in its own
docstring since August, moved the last 3.12 CI lane to 3.11, verified that `.env` actually
reaches the container by rendering `docker compose config` (the previous file silently
dropped `LOG_LEVEL`, `ALLOWED_ORIGINS` and `MAX_UPLOAD_MB`), and — the DEVLOG's own words —
the README "finally documents Docker, the API, the environment and deployment, having
contained none of them."

## What is still open

* **#4 — the backend bake-off.** Unchanged in scope since August. The harness is written,
  the metrics are chosen, the runs have not happened.
* **#46 — the replace/append work** shipped in `v1.1.0-beta`; what remains is the release
  state and the experiment against real AMCR data with `--xsd`, to settle whether the schema
  permits the repeated element.

## Branches

| Branch        | What it is                                                                                                                         |
|---------------|------------------------------------------------------------------------------------------------------------------------------------|
| **`master`**  | the default branch and the code                                                                                                    |
| `test`        | staging; currently the same commit as `master`                                                                                     |
| `main`        | **stale and divergent** — not the default branch, despite the name                                                                 |
| `agent-skill` | a reduced repackaging for coding agents, with a `SKILL.md`, a stdlib-only client and a web frontend that exists on no other branch |
| `gh-pages`    | the landing card at `ufal.github.io/atrium-translator`                                                                             |

## The raw records

Not republished here. On GitHub:

* [`agent_dev_logs/DEVLOG.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/DEVLOG.md) — the timeline index this page condenses
* [`agent_dev_logs/digests/4.digest.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/digests/4.digest.md) · [`46.digest.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/digests/46.digest.md)
* [`agent_dev_logs/plans/`](https://github.com/ufal/atrium-translator/tree/master/agent_dev_logs/plans) and [`issues/`](https://github.com/ufal/atrium-translator/tree/master/agent_dev_logs/issues) — the plans and the verbatim issue exports
* [`docs/translation-backends.md`](https://github.com/ufal/atrium-translator/blob/master/docs/translation-backends.md) — the nine-candidate comparison behind #4

## Sources

Condensed from `ufal/atrium-translator/agent_dev_logs/DEVLOG.md`, `digests/4.digest.md`,
`digests/46.digest.md` and `CONTRIBUTING.md` at branch **`master`**, commit `88242fe`
(2026-09-21). This table records **provenance**, not a build instruction.
