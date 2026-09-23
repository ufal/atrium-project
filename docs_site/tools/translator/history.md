---
title: translator — History
nav_order: 54
status: published
round: 6
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

## 2026-06 · Choosing a translation model (#4)

The repository opened with one question: which base model should do the translating? A
candidate comparison was posted within a day — CUBBITT as the incumbent baseline, against
Cohere Command A, GLM-5.2, MADLAD-400, NLLB-200, Tower+, Opus-MT and the commercial APIs —
scored on language coverage, licence and cost. EuroLLM was added as a self-hostable option
and the whole thing was written up as a phased plan with a full licensing recipe.

What came out of it is an architecture rather than a single answer: a pluggable
`TranslationBackend` protocol with `lindat` and `openai_compatible` registered, and a
CTranslate2 backend for self-hosted models whose heavy dependencies load only when it is
first used. The choice between candidate models is left to measurement — the
`eval/bakeoff.py` harness described in
[Overview → Evaluating translation quality](index.md#evaluating-translation-quality) — so
that CUBBITT can stay the default until another backend is shown to do better on this
material.

## 2026-06 → 07 · Making ALTO output structurally honest

The hard problem in this tool is not translation, it is that ALTO stores text *spatially*.
Each `TextLine` holds a sequence of `String` elements and each `String` carries one token
plus its position on the page. Translating line by line loses cross-line context and
produces poor output; translating the block produces fluent text and discards the structure
that has to be preserved.

The resolution — the **dual-pass reconstruction** described in
[Reference](reference.md#alto-dual-pass-reconstruction) — is to do both and use the second
pass only as a ruler. It is the single most consequential design decision in the repository,
and it is the reason some output boxes end up empty or holding several words: the word-to-box
correspondence in a translated ALTO is *manufactured by the bucketing*, not observed.

That fact is what later settled the `append` question. A per-`String` English alternative
would not be an alternative reading of that word — it would be whichever token the bucketing
happened to land there. So `append` labels the block instead.

`v0.8.0` then moved the API calls from per-block to per-page batches, which cut the number of
calls by roughly a factor of twenty.

## 2026-09 · Twelve-factor work, driven from the hub

Between 2026-09-07 and 09-12 a run of commits landed against hub issues rather than this
repository's own tracker — the `api` Dockerfile stage so a runnable API image exists to
publish; `atrium_rocrate.py` vendored under drift control; `$PORT` honoured rather than
baked into the entrypoint; `TRANSLATION_URL` and `UDPIPE_URL` made attachable; the first
`.env.example`; and the logging contract (one `basicConfig`, in `__main__` only). The same
work landed in every tool at once, which is why it is tracked centrally; see
[Development history](../../development-history.md).

## The base image that blocked a release

On 2026-09-13 a release was stopped by something the build *inherited* rather than anything
it contained.

`python:3.11-slim` is a floating tag, and at the time no repository in the ecosystem declared
a `docker` Dependabot ecosystem to bump it — so the base layer was whatever Docker Hub last
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
reaches the container by rendering `docker compose config`, and brought Docker, the API,
the environment and deployment into the README.

## Branches

| Branch        | What it is                                                                                                                         |
|---------------|------------------------------------------------------------------------------------------------------------------------------------|
| **`master`**  | the default branch and the code                                                                                                    |
| `test`        | the integration branch that changes are staged on                                                                                  |
| `main`        | the repository's initial commit — not the default branch, and not used for development                                             |
| `agent-skill` | a reduced repackaging for coding agents, with a `SKILL.md`, a stdlib-only client and a web frontend that exists on no other branch |
| `gh-pages`    | the landing card at `ufal.github.io/atrium-translator`                                                                             |

## The raw records

Not republished here. On GitHub:

* [`agent_dev_logs/DEVLOG.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/DEVLOG.md) — the timeline index this page condenses
* [`agent_dev_logs/digests/4.digest.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/digests/4.digest.md) — the backend choice · [`46.digest.md`](https://github.com/ufal/atrium-translator/blob/master/agent_dev_logs/digests/46.digest.md) — replace/append
* [`agent_dev_logs/plans/`](https://github.com/ufal/atrium-translator/tree/master/agent_dev_logs/plans) and [`issues/`](https://github.com/ufal/atrium-translator/tree/master/agent_dev_logs/issues) — the plans and the verbatim issue exports
* [`docs/translation-backends.md`](https://github.com/ufal/atrium-translator/blob/master/docs/translation-backends.md) — the nine-candidate comparison behind #4

## Sources

Condensed from `ufal/atrium-translator` at branch **`master`**, commit `71feaef`
(2026-09-23). This table records **provenance**, not a build instruction.

| Source                                                  | What was taken from it                                        |
|---------------------------------------------------------|---------------------------------------------------------------|
| `agent_dev_logs/DEVLOG.md`                              | the timeline, the base-image incident, the v1.0.0-beta review |
| `agent_dev_logs/digests/4.digest.md`, `plans/4.plan.md` | the backend candidates and the resulting architecture         |
| `agent_dev_logs/digests/46.digest.md`                   | the replace/append decision and the batching change           |
| `CONTRIBUTING.md` § Release History                     | release dates and contents                                    |
| `docs/translation-backends.md`                          | the candidate comparison                                      |
