---
title: Development history
nav_order: 13
status: partial
round: 5
issue: 57
---

# Development history

How the ecosystem got here, across all six repositories.

## Per-repository histories

Each tool's own history page condenses that repository's `DEVLOG.md` — the decisions, the
defects worth remembering, and what is still open — and links the raw records rather than
republishing them.

| Repository                   | History page                                                                                                              |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `atrium-page-classification` | **[page-classification → History](tools/page-classification/history.md)**                                                 |
| `atrium-alto-postprocess`    | *pending — [`DEVLOG.md`](https://github.com/ufal/atrium-alto-postprocess/blob/master/agent_dev_logs/DEVLOG.md) on GitHub* |
| `atrium-translator`          | **[translator → History](tools/translator/history.md)**                                                                   |
| `atrium-nlp-enrich`          | *pending — [`DEVLOG.md`](https://github.com/ufal/atrium-nlp-enrich/blob/master/agent_dev_logs/DEVLOG.md) on GitHub*       |
| `atrium-llm-enrich`          | *pending — [`DEVLOG.md`](https://github.com/ufal/atrium-llm-enrich/blob/main/agent_dev_logs/DEVLOG.md) on GitHub*         |
| `atrium-project` (hub)       | **[the cross-repository chronology](#the-cross-repository-chronology)**, below                                            |

## The cross-repository chronology

The hub's `DEVLOG.md` is the timeline of work done in or through the hub — the shared code, the CI
federation, the contracts every tool now meets — with the per-issue detail in its `digests/` and
`plans/`. What follows is that timeline condensed to what shaped **page-classification** and the
**translator**. Dates are the DEVLOG's; a commit is cited where one carries the change.

!!! info "Scope"
    Work that concerns only the other three tools, the project's papers, the data-storage
    inventory, the document-understanding benchmark and the large-model GPU experiments is left to
    those tools' sections. So is `atrium-llm-enrich`'s arrival as the sixth repository in early
    July.

### March → mid-June 2026 · one run logger, one licence rule

Before any CI existed, the hub's first shared code was the run logger, and its first public output
was the tools' catalogue entries.

| When          | What happened                                                                                                                                                                                                             | Why it matters here                                                                                                                                                                              |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 03-13 → 06-12 | One `atrium_paradata.py` shared by every repository (03-15); single-file run records (05-28); a licence resolved per run, **the translator and page-classification first** (06-02); every checklist item done by 06-12    | every run of either tool has recorded its effective licence since. The `ATRIUM_RUNNER_IMAGE` / `_REPO` / `_REF` variables it reads are what later made the published containers self-identifying |
| 03-15 → 07-12 | SSH Open Marketplace records: the page classifier first (03-15), all four tool records live with licence tables by 07-12                                                                                                  | the tools' first public registration. The workflow records are still parked on a marketplace-side error                                                                                          |
| 03-15 → 06-26 | The LLM code-review rounds begin (#10). Review-edited releases on 06-15 — page-classification `v1.4.0-beta`, translator `v0.6.0`; the 06-21 round finds `/info` version drift and a diverged, untested `para_licenses.py` | the umbrella both later hardening rounds ran under                                                                                                                                               |

### Mid-June → mid-July · the workflow federation

One reusable workflow, a thin caller in every repository, and a guard that the shared files stay
byte-identical.

| When          | What happened                                                                                                                                                                                                                                              | Why it matters here                                                                                                                    |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| 06-15 → 06-16 | "One reusable workflow template plus thin per-repo callers" is proposed once the translator and page-classification pass GitHub Actions first; `676a1fe` lands `docker-tool.reusable.yml`, the caller example and the shared `.coveragerc` and `ruff.toml` | the start of every CI file both tools run today                                                                                        |
| 06-25 → 06-27 | `agent_dev_logs/` created in every repository, seeded from the issue history (#29); the first cross-repository snapshot; an end-to-end smoke test proposed, because no issue yet tracked pipeline-wide regressions                                         | the records this page condenses, and the origin of [W6](pipelines.md#w6--e2e-smoke-the-integration-contract)                           |
| 07-12         | `paradata-drift` becomes `para-drift.reusable.yml`, with licence-parity checks on by default: the shared licence files are diffed byte-for-byte against the hub's `docs/templates/shared/`                                                                 | the mechanism that, extended file by file, holds all 17 vendored files in both tools today ([Architecture](ecosystem/architecture.md)) |

### 17 → 31 July · a service contract, agent skills, the record, and `v1`

| When          | What happened                                                                                                                                                                                                                                                                                                                                                                                                                     | Why it matters here                                                                                                                                                     |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 07-17 → 07-22 | The agent-skill standard is written and rolled out to five `agent-skill` branches, with **page-classification as the hardened exemplar** — four defects fixed, `/health` and `/info` added. The translator gets its first `service/README.md`, frontend and `/health`, and 422 instead of 400 for bad input. Every first `skill-validate` run failed with "0 jobs": the callers were pushed before the reusable they call existed | the [Agent skills](agent-skills.md) both tools ship — and the start of a pattern: skill branches drift from the default branch and are re-audited (07-29, 09-09, 09-16) |
| 07-23         | The shared `service/atrium_service.py`, the `/info` envelope and `/health` everywhere, harmonised error codes, `api-contract.reusable.yml` and a hermetic contract test per repository — landed the same day. The remaining "0 jobs" failures were a malformed hub reusable, and page-classification's caller was named `api-contract.ym;`                                                                                        | the first hub-owned *runtime* module in both services                                                                                                                   |
| 07-25 → 08-04 | The document record: `document_schema.md` (07-25); `atrium_document` integrated as a draft everywhere, page-classification `v1.7.0-beta` and translator `v0.10.0` among them (07-26); the module and its schema promoted into the shared set under para-drift; formats settled 08-01                                                                                                                                              | the [record](ecosystem/document-contract.md) both tools accrete onto. Its decision thread is `atrium-llm-enrich#13`, not the hub's #13                                  |
| 07-30         | A full GitHub Actions and Docker audit. **page-classification's `release.yml` shipped `run.py` without the nine modules it imports**; the E2E's last stage had skipped silently every night behind a misnamed secret while the run reported success; `check_version.py` vendored; the image scan moved onto the immutable digest                                                                                                  | the release bundle both tools publish, and the version gate on every tag                                                                                                |
| 07-31         | **Tag `v1` created** and referenced from every caller; `test` merged into each default branch; releases cut, page-classification `v1.7.2-beta` and translator `v0.10.2` among them                                                                                                                                                                                                                                                | the pin both tools' CI still uses                                                                                                                                       |

### August · end to end, the partner border, two hardening rounds

| When          | What happened                                                                                                                                                                                                                                                                                                                                                            | Why it matters here                                                                                                                        |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| 08-01         | The E2E rewritten to thread one record through all five stages                                                                                                                                                                                                                                                                                                           | [W6](pipelines.md#w6--e2e-smoke-the-integration-contract) as it runs today                                                                 |
| 08-02         | The ruling that this project's CI must not reach into partner environments: the handoff is a Docker image, built in the partners' own fork and run on their own Kubernetes                                                                                                                                                                                               | why [Operations](operations.md) is written as a handoff                                                                                    |
| 08-05 → 08-06 | "The 08-06 round": five P0 defects, each invisible to the repository that owned it. Found while fixing them: **the translator's `service/api.py` omitted `backend`, so every real `/translate` upload returned HTTP 500** — uncaught because every test mocked the pipeline. `canonical_doc_id()` and `validate_document()` put on every write path                      | the translator service in [W4](pipelines.md#w4--containerised-service--api-workflow); schema validation on every record either tool writes |
| 08-18 → 08-19 | "The 08-19 round": nine findings, six of them mechanisms that were present, green, and checking something other than the thing that mattered — among them a concurrency rule that let a push silently cancel a scheduled run, now a check in `workflow_lint.py`. `v1` moved to `f54983e`; shared-code parity verified by blob hash rather than by para-drift's own badge | the lint both tools' workflows pass                                                                                                        |

### 3 → 16 September · twelve-factor, Kubernetes, SKOS, RO-Crate, the manifest

| When          | What happened                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Why it matters here                                                                                                                                                                                                                    |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 09-04 → 09-08 | The SKOS registry `atrium_vocab.py` and its schema, vendored into every tool; publication under an ATRIUM namespace deferred to an external project (#51)                                                                                                                                                                                                                                                                                                                                                                                                                                       | [SKOS](contracts/skos.md) — and why no ATRIUM URI resolves yet                                                                                                                                                                         |
| 09-06 → 09-07 | #55: `/ready` separate from `/health`, `ServiceState`, a graceful SIGTERM drain, `healthcheck.py`, the Kubernetes template and deployment guide; `docker-build-smoke` now *runs* the image it builds — the first CI job in the ecosystem to start one of these containers. Measuring the repositories also found that four of five services, these two included, had **no runnable API image**, only a compose override on the batch image                                                                                                                                                      | the `-api` images, probes and shutdown behaviour in [Operations](operations.md)                                                                                                                                                        |
| 09-09         | #54: the schema tightened and `atrium_rocrate.py` added (`bbc8fde`); the follow-through found the exporter had no callers                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | [RO-Crate export](contracts/rocrate.md), still run by hand                                                                                                                                                                             |
| 09-11 → 09-14 | #62 retires the E2E's entrypoint overrides; #58 makes every service honour `$PORT`; #59 replaces the hand-kept shared-file lists with one `MANIFEST.json`. (The DEVLOG has no entry for these days; the dates come from the #53 and #59 digests.)                                                                                                                                                                                                                                                                                                                                               | the manifest behind [Architecture](ecosystem/architecture.md)                                                                                                                                                                          |
| 09-13 → 09-16 | **The base-image CVE.** The translator's `v1.0.0-beta` release was blocked by three CRITICAL CVEs in the floating `python:3.11-slim` (09-13) and released as `v1.1.0-beta` once patched (09-14); the same gate then blocked a second repository, the fix was ported to the other four, and its test became canonical file #17 (09-16). The same day, all five `v*.4` revisions of `ufal/vit-historical-page` were found to serve one checkpoint, and the `agent-skill` branches were fetched for the first time: 0 of 5 aligned, page-classification's missing two modules its `run.py` imports | [translator → The base image that blocked a release](tools/translator/history.md#the-base-image-that-blocked-a-release); [page-classification → The canonical ensemble](tools/page-classification/reference.md#the-canonical-ensemble) |

### 16 → 23 September · this site

| When          | What happened                                                                                                                                                                                                                                                                                                                                          | Why it matters here                         |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| 09-16 → 09-21 | The site designed and first built: `mkdocs.yml`, 38 draft pages, a landing card per repository. Switching the hub's Pages on against the wrong source failed on Liquid — and a green build would have published a file that was never meant to be public. `pages.yml` now builds with `mkdocs build --strict`, and all six sites serve from `gh-pages` | why this site builds from `docs_site/` only |
| 09-21 → 09-23 | The verdict on the drafts: "no new information available" — 34 of 38 re-sliced documentation already public elsewhere. The rule since: publish what exists nowhere else. The page-classification and translator sections, then the hub's static pages, written against the code, with the drift each found                                             | this page, and the ones it links to         |

## What the record keeps repeating

The same four lessons recur across six months of entries, in different words each time:

1. **Measure live state; do not assert it.** A record that says what is deployed, released or
   passing goes stale within hours of the commit that changes it. The corrections that recur most
   in the DEVLOG are claims "derived rather than measured".
2. **Trust a guard only after watching it fail.** New checks are broken deliberately before they
   are believed — which is how several turned out never to have been able to fire.
3. **Green is not the same as checked.** The stage that skipped every night while the run passed;
   the tests that mocked away the one call that failed in production; the concurrency rule that
   cancelled runs without reporting a failure.
4. **One manifest instead of many hand-kept lists.** `MANIFEST.json` replaced fourteen enumerations
   of the shared files; the next canonical file cost one manifest row and one `ruff.toml` entry.

## Why the raw records are not published here

`agent_dev_logs/` across the six repositories holds 24 issue digests, 24 plans, 23 verbatim
issue exports, six `project_state_*` snapshots and six `DEVLOG.md` timelines. They stay in
their repositories and on GitHub, for two reasons:

1. **Volume.** Publishing them would multiply this site's page count several times over with
   material written for a different audience.
2. **Content.** Several issue exports are open memos addressed to named individuals, and some
   snapshots carry personal addresses. Publishing the set wholesale is a disclosure problem as
   well as a volume one.

The history pages are therefore **condensed and written**, with every raw record linked. A
derived page cannot drift from its source; a hand-written one is a second thing to remember —
which is exactly what happened to page-classification's own `DEVLOG.md` header, and why these
pages cite the commit they were written from.

## Sources

Condensed from each repository's `agent_dev_logs/DEVLOG.md` at the refs each history page
names. This table records **provenance**, not a build instruction.

| Source                                                                  | What was taken from it                                     |
|-------------------------------------------------------------------------|------------------------------------------------------------|
| `atrium-page-classification/agent_dev_logs/DEVLOG.md` @ `vit` `8415ce7` | the page-classification history page                       |
| `atrium-translator/agent_dev_logs/DEVLOG.md` @ `master` `88242fe`       | the translator history page                                |
| `atrium-project/agent_dev_logs/DEVLOG.md` @ `test` `88bc1a6`            | the cross-repository chronology, and the four lessons      |
| `atrium-project/agent_dev_logs/digests/{53,59}.digest.md`               | the 09-11 → 09-14 landings, which the DEVLOG does not date |
| `git show` of `676a1fe`, `bbc8fde`, `f54983e` in the hub                | the commit dates cited                                     |
