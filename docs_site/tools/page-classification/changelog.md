---
title: page-classification — Changelog
nav_order: 33
status: published
round: 6
issue: 57
repo: atrium-page-classification
role: changelog
---

# page-classification — Changelog

**The release history from v0.1.0 on.** The canonical entries live in the tool's
[`CONTRIBUTING.md`](https://github.com/ufal/atrium-page-classification/blob/vit/CONTRIBUTING.md#-release-history),
one table cell per release. This page gives the same history in two other shapes: a
scannable line per release, and the arcs those releases belong to.

Versions below `v1.0` were research milestones; from `v1.0.3-beta` on, each release is a
usable program, published as a GitHub pre-release with its container images.

## The five arcs

Read top to bottom, this is the project's whole story.

**1 · Finding a method that works** (`v0.1.0` → `v0.9.0`). Two approaches were tried and
abandoned, and the changelog says so in as many words: DeepDoctection layout analysis plus
a hand-written categorisation rule (`v0.1.0`, marked `[FAILED]`), then a Random Forest over
manually extracted texture and colour features (`v0.2.0`, also `[FAILED]`). `v0.5.0` is the
turn: switch to fine-tuning Hugging Face base models against a labelled page dataset.
`v0.7.0` widens that to the ViT family, `v0.9.0` to EfficientNetV2, RegNetY and DiT, and
adds cross-validation.

**2 · Picking the five** (`v0.11.0` → `v0.12.1`). A twelve-model sweep settles on RegNetY
as the leader and five models as the ensemble; result averaging, the `--best` path and a
first API draft land together. This is where the two version namespaces documented in
[Reference](reference.md#two-version-namespaces-and-where-they-collide) originate.

**3 · Becoming a program rather than a study** (`v1.0.3-beta` → `v1.4.3-beta`). Pytest
arrives; sample images are replaced with CC BY-NC 4.0-licensed ones; data-processing
scripts get their own unit tests; a Docker wrapper appears (`v1.2.1-beta`, explicitly
"draft, untested"); YOLO-cls is added to the entry point and paradata gains licence
resolution (`v1.2.0-beta`); memory-aware parallel `--best` lands (`v1.3.0-beta`); files
are reorganised into sub-directories and the source goes through LLM review
(`v1.4.0-beta`–`v1.4.3-beta`).

**4 · Joining the ecosystem** (`v1.5.0-beta` → `v1.7.5-beta`). The repository stops being
standalone. `folds_csv` replaces by-seed split selection so a model's original split can
be reproduced; the paradata template is shared across repositories; `agent_dev_logs/`
replaces issue comments. Then the `atrium_document` standard is integrated
(`v1.7.0-beta`), workflows migrate to the hub's reusable templates pinned at `@v1`
(`v1.7.2-beta`), and the release bundle gains an AST-based completeness guard
(`v1.7.1-beta`). `v1.7.4-beta` and `v1.7.5-beta` are re-vendorings of the shared
`atrium_document.py` as its contract tightened — `doc_id` inherited from the baseline
rather than re-derived, `set_source()` filling sub-keys a partial first write left unset.

**5 · Standards and service contracts** (`v1.8.0-beta`). The densest single release,
described in full below.

## v1.8.0-beta

Four things land at once, and they are independent of each other.

**The ensemble default moves to `v*.4`.** `REVISION_BEST_MODELS` now names `v1.4`–`v5.4` —
the same five base models, retrained on the CC BY-NC 4.0-only subset. The switch was held
back deliberately: for three days every `v*.4` revision on the Hub served the *same*
`regnety_160` checkpoint, so flipping the keys would have averaged one model with itself
five times, returned well-formed predictions, and still reported a five-model ensemble.
Nothing would have raised. `tests/test_best_ensemble_distinct.py` now makes that
unshippable — a static half asserting five distinct base models, and a `-m slow` half that
reads each revision's `config.json` from the Hub.

**Two ecosystem standards.** SKOS via `atrium_vocab.py` — six concept schemes, stable
`w3id.org/atrium/` URIs, advisory-only validation — exposed to this tool through
`model_registry.category_uri()`. And RO-Crate via `atrium_rocrate.py`, with deterministic
`document_crate()` and `run_crate()` builders.

**Service contracts.** `/ready` and `/health?deep=true` drain semantics; `$PORT` and `HOST`
honoured through `python -m service.api`; a published `.env.example` enforced by
`test_env_contract.py`; and `logging.basicConfig()` removed from `service/inference.py`, so
`LOG_LEVEL` takes effect.

!!! danger "Two breaking changes in this release"
    `atrium_document.schema.json` tightens `required` and adds `anyOf`/`allOf`, so records
    that validated before may now fail. And `service/frontend/script.js` no longer
    hardcodes `:8000` for every localhost origin.

## Every release

| Version         | What changed                                                                                                                                                                                                                                             |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **v1.8.0-beta** | Ensemble default → `v*.4`; SKOS and RO-Crate land; `/ready` and deep health; `.env.example`; two breaking changes (see above)                                                                                                                            |
| **v1.7.5-beta** | Re-vendored `atrium_document.py` (`set_source()` fills sub-keys a partial first write left unset); four `MagicMock` masks removed that had made test behaviour depend on pytest's collection order; CI concurrency scoped so a push cannot cancel a cron |
| **v1.7.4-beta** | `doc_id` inherited from the baseline instead of overwritten, so no stage can re-key an accreted record; per-page and whole-document upload paths share one derivation                                                                                    |
| **v1.7.3-beta** | End-to-end CI for document-JSON input/output refined and tested against the draft schema                                                                                                                                                                 |
| **v1.7.2-beta** | Workflow references repinned to the hub's `@v1` tag                                                                                                                                                                                                      |
| **v1.7.1-beta** | CI/CD hardening. The release zip now ships the nine first-party modules reached transitively, with an AST guard that fails the build if it is ever incomplete again                                                                                      |
| **v1.7.0-beta** | `atrium_document` input and output integrated; paradata template aligned with the hub                                                                                                                                                                    |
| **v1.6.0-beta** | Latest versions moved to `v*.4` for the licensed dataset; draft OpenAPI conformance                                                                                                                                                                      |
| **v1.5.1-beta** | Licence tests per the shared template; automatic version reading fixed                                                                                                                                                                                   |
| **v1.5.0-beta** | `--folds_csv` replaces by-seed selection, so an original split can be reproduced; shared paradata template; `agent_dev_logs/` introduced                                                                                                                 |
| **v1.4.3-beta** | Dataset link repointed at the licensed data                                                                                                                                                                                                              |
| **v1.4.2-beta** | Ruff applied; secret-scan removed                                                                                                                                                                                                                        |
| **v1.4.1-beta** | Second LLM review round; Docker CI alignment                                                                                                                                                                                                             |
| **v1.4.0-beta** | Files reorganised into sub-directories; source-level review edits                                                                                                                                                                                        |
| **v1.3.0-beta** | Memory-aware grouped parallel execution for `--best`; Docker wrapper and API service aligned                                                                                                                                                             |
| **v1.2.1-beta** | Docker wrapper — draft, untested                                                                                                                                                                                                                         |
| **v1.2.0-beta** | YOLO-cls added to the entry point; paradata gains model-licence resolution                                                                                                                                                                               |
| **v1.1.0-beta** | Sample images replaced with CC BY-NC 4.0-licensed ones; data-processing scripts finalised with unit tests; CLI I/O flags widened                                                                                                                         |
| **v1.0.4-beta** | Pytest for core pipeline components; CONTRIBUTING gains a testing guide and the release history                                                                                                                                                          |
| **v1.0.3-beta** | First beta of the finished program: empty `CLASS`/`SCORE` pairs in averaged output, reduced-size example results for the Prague and Brno collections, data licence for the shared page samples                                                           |
| **v0.12.1**     | Best five models fine-tuned; result averaging, `--best`, API draft, data scripts                                                                                                                                                                         |
| **v0.11.0**     | RegNetY selected as leader, five models chosen; filename-format parsing widened                                                                                                                                                                          |
| **v0.9.0**      | EfficientNetV2, RegNetY and the DiT family added; cross-validation and averaging; dataset published                                                                                                                                                      |
| **v0.7.0**      | Several ViT variants; architecture diagram                                                                                                                                                                                                               |
| **v0.5.0**      | **The turn**: switch to fine-tuning Hugging Face base models; training dataset refined; data scripts supplied                                                                                                                                            |
| **v0.2.0**      | Random Forest over hand-extracted image features — **`[FAILED]`**; first use of the labelled dataset                                                                                                                                                     |
| **v0.1.0**      | DeepDoctection OCR + layout analysis with a manual categorisation rule — **`[FAILED]`**                                                                                                                                                                  |

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `adee922`
(2026-09-23). The arcs are written here, not taken from a source. This table records
**provenance**, not a build instruction.

| Source                                  | What was taken from it                             |
|-----------------------------------------|----------------------------------------------------|
| `CONTRIBUTING.md` § `📦 Release History` | every release line and the v1.8.0-beta description |
| `CITATION.cff`                          | the current version and its release date           |
