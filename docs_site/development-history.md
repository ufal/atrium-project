---
title: Development history
nav_order: 13
status: partial
round: 3
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
| `atrium-project` (hub)       | *pending — see the cross-repository chronology below*                                                                     |

## The cross-repository chronology

The hub's own `DEVLOG.md` already deduplicates the per-repository ones: work that touched
several repositories at once is recorded there and removed from theirs. That is where the
ecosystem-wide story lives — the shared-code manifest, the workflow federation, the
twelve-factor pass, the base-image CVE that blocked two releases.

This page will carry a condensed version of it. Until then it is on GitHub:
[`agent_dev_logs/DEVLOG.md`](https://github.com/ufal/atrium-project/blob/main/agent_dev_logs/DEVLOG.md).

Two episodes are already written up from the tool side, because they started there:

* **The base image that blocked a release, twice** —
  [translator → History](tools/translator/history.md#the-base-image-that-blocked-a-release).
  A floating `python:3.11-slim` tag, three CRITICAL CVEs, a gate that only runs on tags, and
  a cache-served apt layer that looks correct and patches nothing.
* **Two defects a passing test suite could not see** —
  [page-classification → History](tools/page-classification/history.md#2026-08--two-defects-the-test-suite-could-not-see).
  A numpy pin that had drifted past the Python version every image runs, and a service
  requirements file that declared no ASGI server at all.

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

| Source                                                                  | What was taken from it                   |
|-------------------------------------------------------------------------|------------------------------------------|
| `atrium-page-classification/agent_dev_logs/DEVLOG.md` @ `vit` `8415ce7` | the page-classification history page     |
| `atrium-translator/agent_dev_logs/DEVLOG.md` @ `master` `88242fe`       | the translator history page              |
| `atrium-project/agent_dev_logs/DEVLOG.md`                               | the cross-repository chronology, pending |
