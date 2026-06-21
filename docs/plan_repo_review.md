# ATRIUM source-code review — combined plan (refreshed for the next rounds)

> **Status update — 2026-06-21 (post Opus 4.8 round).** This refresh carries forward all backlog items
> from the 2026-06-17 Opus 4.8 review, promotes pending-merge patches to "confirm merged" tasks,
> and augments each repo section with new items derived from open GitHub issues and the strategic
> research audit document ("Architectural Optimization and End-to-End Integration of the ATRIUM NLP
> Pipeline"). A new **§5 Strategic Horizon** section covers feature-level work (TEATER LLM keywords,
> domain NER, pipeline orchestration, paradata trust chain) that exceeds the per-file code-review
> scope. Reviewed heads from prior round: page-classification `046d076` · translator `f5650b8` ·
> alto-postprocess `915dbff` · nlp-enrich `7a18dee`. Source: [atrium-project#10](https://github.com/ufal/atrium-project/issues/10).

---

# 1/4 — `atrium-page-classification`

**Repo:** page image classifier (ViT/RegNetY/EfficientNetV2/DiT, optional YOLO); CLI (`run.py`) + FastAPI `service/`.

### ✅ Closed previous round

- **Single source of truth:** `model_registry.py` added — imported by `classifier.py`, `run.py`, `parallel_best.py`, `service/inference.py`.
- **Shared ensemble:** `ensemble.py` (`average_rdfs` + `average_prediction_dicts`) consumed by `parallel_best.py` and `service/inference.py`.
- **API + YOLO + CLI tests** added: `test_service_api.py`, `test_yolo_classifier.py`, `test_run.py`.
- **CI config localized:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc` present; coverage Step-Summary step made non-fatal.
- **Version sync:** `CITATION.cff` → `1.4.0-beta`; CONTRIBUTING Release-History top = `v1.4.0-beta`.

### ⏳ Confirm merged (patches delivered last round, not yet merged)

- 🔴 **`pymupdf` missing from `service/requirements.txt`** — `/predict_document` was dead in a clean install; fix is a one-liner addition. Verify before next review.
- **Service hardening in `service/api.py`:** CORS wildcard-with-credentials; `predict_image` swallows its own `HTTPException`; `content_type=None` → 500; stray `# … rest unchanged …` artifact. Confirm all four sub-fixes are merged.

### ▶ Next-round backlog

| Pri | Item                                                                                                                                          | Axis  | Note                                                    |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------------|-------|---------------------------------------------------------|
| P1  | Deepen `ModelManager` tests (`service/inference.py` 27%) + `run.py` CLI paths beyond smoke (23%)                                              | Tests | pure-logic/model-selection paths; no GPU needed         |
| P1  | Remove residual registry/category copies: `service/api.py:84` fallback list, `supplementary/scripts/logs_stat.py:70`, `dataset_timeline.py:9` | Arch  | import from `model_registry` instead                    |
| P2  | Confirm/retag the GitHub release **`v1.4.0-bets`** typo → `v1.4.0-beta`; align CONTRIBUTING lint wording to Ruff                              | Docs  | tags not in repo yet                                    |
| P2  | Decide dedicated `api` build target vs `compose --profile api`; investigate phantom `config.py`/`config-3.py` coverage warning                | CI    | low risk, cosmetic                                      |
| P2  | Document TEXT vs TEXT_T boundary ambiguity threshold (accuracy drop below 90%, off-diagonal errors >10%) in README model notes                | Docs  | links to HF model card; DK sign-off on threshold policy |

---

# 2/4 — `atrium-translator`

**Repo:** structure-preserving translator (LINDAT NMT + Tag-and-Protect, FastText ID, UDPipe lemmas, ALTO/metadata XML). CLI and API.

### ✅ Closed previous round

- **API parity:** `service/api.py` + `service/requirements.txt` added — `/translate` + `/info`, size guard, paradata; reuses `main.process_single_file`.
- **`main.py` orchestration tests** + `test_api.py` TestClient suite.
- **CI config localized:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc`; `requirements-test.txt` carries `fastapi`+`httpx`.
- README states dual CLI+API architecture explicitly.

### ⏳ Confirm merged

- **`service/api.py` CORS wildcard-with-credentials** + `/translate` `file.filename=None` → 500. Same pattern as pc; confirm patched.
- **Version sync:** `CITATION.cff` `0.5.1` → `0.6.1`; README Python badge `3.8+` → `3.11`. Confirm applied.

### ▶ Next-round backlog

| Pri | Item                                                                                               | Axis  | Note                                                             |
|-----|----------------------------------------------------------------------------------------------------|-------|------------------------------------------------------------------|
| P1  | Test `load_vocab.py` (**0%**, 212 L — OAI-PMH/GraphQL harvesting) and `para_licenses.py` (20%)     | Tests | mock network calls; no live API needed                           |
| P1  | Mock-test `_post_with_retry` (back-off/throttle) + encode the homonym single-word-lemma regression | Tests | `translator.py` currently 76%; two distinct failure modes to pin |
| P1  | Add `.pre-commit-config.yaml` (parity with alto + pc)                                              | CI    | copy template from `atrium-project/docs/templates/`              |
| P2  | `--fast-align` proportional-alignment test suite                                                   | Tests | only indirect coverage today                                     |
| P2  | Set real `date-released` in `CITATION.cff` at tag time; add post-release checklist to CONTRIBUTING | Docs  | currently `2026-03-02` (stale)                                   |

---

# 3/4 — `atrium-alto-postprocess`

**Repo:** OCR ALTO post-processor — split → stats → extract (alto-tools|LayoutReader|GLM-4v) → line classify → aggregate, + FastAPI service. Healthiest of the four.

### ✅ Closed previous round

- **Service config-sourcing:** `service/utils.py:33` now reads `PERPLEXITY_THRESHOLD_MAX` from `config_langID.txt` (default 1000.0; no more stale 5000).
- **Pipeline tests added:** `test_extract_alto`, `test_run_pipeline`, `test_aggregation`, `test_gpu_concurrency`, `test_resume_logic`, `test_service_api`; core `text_util_langID` 88%.
- **CI config + pre-commit:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc`, `.pre-commit-config.yaml` present.
- **Version sync:** `CITATION.cff 0.18.0` == `para_config v0.18.0`.

### ⏳ Confirm merged

- **Git-ignore `.idea/`** (1 tracked file remains). Confirm `git rm --cached` applied.
- **Stale `CONTRIBUTING.md:206`** ("runs black, isort, flake8" → Ruff). Confirm updated.

### ▶ Next-round backlog

| Pri | Item                                                                                                                                                                    | Axis   | Note                                                          |
|-----|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|---------------------------------------------------------------|
| P1  | Tests for still-0% `page_split.py` (145 L) and `alto_stats_create.py` (266 L)                                                                                           | Tests  | pure-ish, CPU-only; no OCR model needed                       |
| P1  | Raise `langID_classify.py` from 10% — cover threshold-decision branches (issue #3 calibration work)                                                                     | Tests  | mock FastText + perplexity model; DK confirms boundary values |
| P1  | Decide `img2jpeg_v3.py` (orphaned, 0%, 0 imports): wire+test, document purpose, or `git rm`                                                                             | Arch   | blocks tree hygiene                                           |
| P2  | Perplexity model↔threshold coupling guard: warn/error if a non-distilgpt2 model is loaded without overriding `PPL_GARBAGE_ABSOLUTE` (Qwen vs distilgpt2 scale mismatch) | Config | surfaceable as a runtime assertion                            |
| P2  | VRAM/troubleshooting docs for GLM-4v (48 GB VRAM) and LayoutReader (separate GPU worker)                                                                                | Docs   | blocks new-user onboarding                                    |
| P2  | Confirm `data_samples/*_gpt` dirs are intentional test fixtures (not leftover scratch output)                                                                           | Tree   | add `.gitkeep` + comment if intentional                       |

---

# 4/4 — `atrium-nlp-enrich`

**Repo:** CSV → NLP enrichment (manifest → UDPipe → NameTag → TEITOK, + keywords + LLM) via `api_*.sh` shell + FastAPI wrapper. Still the lowest-coverage repo.

### ✅ Closed previous round

- **High-value tests:** `test_chunk.py` (`chunk.py` 0→86%), `test_remote_apis.py` (UDPipe 53% / NameTag 56%), `test_api_service.py` (subprocess contract; `service/api.py` 59%, `enrichment.py` 63%, `jobs.py` 77%), `test_llm_utils.py` (`llm_utils.py` 0→17%).
- **CI config:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc`; `pydantic>=2` (and `pydantic==2.13.3` in `requirements_llm.txt`).

### ⏳ Confirm merged

- **Version sync:** `CITATION.cff 0.14.0` → `0.14.1`. Confirm applied.

### ▶ Next-round backlog

| Pri | Item                                                                                                                                                                     | Axis       | Note                                                      |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|-----------------------------------------------------------|
| P0  | Continue carving testable helpers from `llm_utils.py` (17% of 676 stmts) — extract prompt-building, JSON schema assembly, and logit-processor wiring into pure functions | Tests/Arch | prerequisite for TEATER issue #6 implementation           |
| P0  | **[issue #6]** Implement TEATER LLM keyword extraction — prompt contract, JSON schema output template, thesaurus-term ranking; wire to `keywords.py` (19%)               | Feature    | see §5.1 for full scope; DK supplies thesaurus snapshot   |
| P1  | Cover `llm_run.py` (**0%**, 212 L), `vocab_manager.py` (15%), `summarize_nt_udp.py` (16%), `keywords.py` (19%), `fix_teitok_bboxes.py` (0%)                              | Tests      | all pure-ish; mock vLLM backend                           |
| P1  | Add **`shellcheck`** lint pass on `api_*.sh` shell layer + add to `.pre-commit-config.yaml`                                                                              | CI         | shell layer is completely unlinted; only shell-heavy repo |
| P1  | Add `.pre-commit-config.yaml` (parity with alto + pc)                                                                                                                    | CI         | copy template; shellcheck hook added above goes here      |
| P2  | Disambiguate "API" terminology in docs (external UDPipe/NameTag endpoints vs our own FastAPI)                                                                            | Docs       | causes confusion in issue comments                        |
| P2  | Docker quickstart / troubleshooting section in README                                                                                                                    | Docs       | no current container guidance for end-users               |
| P2  | Exclude/relocate `service/test_api.py` (manual integration client, counted as 0% by pytest)                                                                              | Tests      | cosmetic but inflates uncovered-lines count               |
| P2  | Set real `date-released` in `CITATION.cff` at tag time; add to CONTRIBUTING post-release checklist                                                                       | Docs       | —                                                         |

---

# Cross-repo status & next-round threads

## Closed across the board (previous round)

1. **Version skew → synced in all four** (`CITATION` versions aligned to `para_config` version strings in each repo).
2. **CI config localized in all four** — `ruff.toml` / `.coveragerc` / `dependabot.yml` present per repo.
3. **Orchestration/entry points tested** — `run.py` / `main.py` / `run_pipeline.py` and every FastAPI service now have suites.
4. **FastAPI parity reached** — all four repos ship a FastAPI layer (alto = import-reuse; pc = shared registry/ensemble; nlp = subprocess; translator = `process_single_file` reuse).

## Active cross-repo threads

**A. Service-layer hardening** — CORS wildcard-with-credentials pattern and `None` content-type/filename guards recur in pc and translator. Patches delivered last round; **confirm merged in both** before next review. Any new endpoint in any repo should run through the hardening checklist:
- `allow_credentials=True` requires an explicit origin list, never `"*"`.
- Every upload endpoint must guard `file.filename is None` and `content_type is None` before use.

**B. `.pre-commit-config.yaml` parity** — present in pc + alto; **missing in nlp + translator**. Target: all four repos run the same hook set (ruff-format, ruff-check, shellcheck for nlp, trailing-whitespace, end-of-file-fixer).

**C. Coverage depth on entry/IO modules** — the shared low-coverage frontier across repos:

| Module                 | Repo                | Current % | Blocker                     |
|------------------------|---------------------|-----------|-----------------------------|
| `load_vocab.py`        | translator          | 0%        | network mock needed         |
| `llm_run.py`           | nlp-enrich          | 0%        | vLLM mock needed            |
| `page_split.py`        | alto-postprocess    | 0%        | pure-ish                    |
| `alto_stats_create.py` | alto-postprocess    | 0%        | pure-ish                    |
| `llm_utils.py`         | nlp-enrich          | 17%       | carving prerequisite for #6 |
| `ModelManager`         | page-classification | 27%       | pure-logic paths            |

**D. `shellcheck` for nlp's shell layer** — `api_udpipe.sh`, `api_nametag.sh`, and related scripts are fully unlinted. Add `shellcheck` to pre-commit and CI (advisory, `continue-on-error: true` initially).

**E. Ratchet the CI gates** — now that `ruff.toml` and `.coveragerc` are in every repo, consider enabling:
- `ruff check` as a **blocking** step (currently advisory in most repos).
- `pytest --cov --fail-under=<N>` once per-repo baselines stabilise (suggest 60% for nlp-enrich, 75% for others).
- Fail fast on new `ruff` violations in PR diffs (`--diff` mode).

**F. Release hygiene** — two recurring problems:
- `v1.4.0-bets` tag typo in page-classification: retag before next public announcement.
- `date-released` stale in translator (`2026-03-02`) and nlp-enrich CITATION: add to post-release checklist in each repo's CONTRIBUTING.

---

# §5 — Strategic Horizon (feature + research milestones)

Items in this section exceed the per-file code-review scope. They are scoped from open GitHub issues and the strategic research audit. Each maps to one or more backlog entries above; this section provides rationale and sequencing context.

## §5.1 — TEATER LLM keyword extraction [`atrium-nlp-enrich` issue #6, open]

**Goal:** The locally-running LLM instance receives an input document, the TEATER topic thesaurus, and a JSON output template, then returns a filled template containing related thesaurus terms.

**Prerequisites (all must close before production wiring):**
- `llm_utils.py` P0 carving (4/4 backlog) — prompt-builder and schema-assembly must be pure functions.
- `keywords.py` P1 test coverage — existing KER pipeline tests needed as regression baseline before adding LLM branch.
- DK to supply a canonical TEATER thesaurus snapshot (format TBD: flat list, JSON-LD, or SKOS).

**Implementation outline:**
1. Add `LLMKeywordExtractor` class to `keywords.py` wrapping existing `llm_utils.py` backend.
2. Prompt contract: system prompt carries the thesaurus terms, user message carries the document chunk(s), output constrained to JSON schema via `xgrammar`/Pydantic.
3. Ranking/filtering: threshold on LLM confidence or term co-occurrence; fallback to KER if LLM call fails.
4. Paradata: log thesaurus version hash, model name/version, token counts per call in `atrium_paradata.py`.

**Milestone:** Close issue #6 when `test_keywords.py` covers the LLM branch ≥ 60% and DK signs off on a sample TEATER run against five real documents.

## §5.2 — Domain-specific NameTag NER model [`atrium-nlp-enrich` issue #7, referenced open]

**Goal:** Fine-tune a NameTag 3 model on Czech archaeological domain text (AMCR/ARÚP corpus) for entity types: `PER`, `ORG`, `LOC`, `PERIOD`, `MATERIAL`, `SITE`.

**Prerequisites:**
- ARÚP to supply annotated NER training set (DK + David Novák coordination).
- `call_nametag` coverage (currently 56%) must include the new model endpoint before wiring.
- Decide: local NameTag 3 instance or LINDAT REST API — each has different latency / offline-capability tradeoffs.

**Sequencing:** This is a multi-week ML training task; it does not block the code-review rounds but should be tracked as a separate GitHub milestone (`Q3 [WP4/WP5: NER training]`). The `atrium-nlp-enrich` pipeline already has a NameTag slot; the work is mostly data-curation + fine-tuning, not architecture change.

## §5.3 — End-to-end pipeline orchestration

**Current state:** Four independent repos are operated by chained bash scripts. The `atrium-nlp-enrich` FastAPI service provides async job queuing internally, but there is no cross-service orchestration layer.

**Scaling target:** The research audit identifies the need to transition from local multiprocessing queues to a horizontally-scalable, event-driven topology. Concrete options in scope for the project horizon:

| Option                                      | Complexity | Notes                                                           |
|---------------------------------------------|------------|-----------------------------------------------------------------|
| Shell-script glue with polling              | Low        | Current state; adequate for batch runs on a single cluster node |
| Python `asyncio` coordinator (`run_all.py`) | Medium     | Suitable for single-machine multi-GPU batch; no new infra       |
| Message queue (RabbitMQ / Redis Streams)    | High       | Enables horizontal scale; overkill unless multi-node needed     |

**Recommended next step:** Add a `run_all.py` integration driver that chains the four service calls (page-classification → alto-postprocess → nlp-enrich → translator) with retry logic and shared paradata accumulation. This can be built on top of the existing FastAPI `/info` + job endpoints without changing any repo internals.

**GitHub tracking:** Open a new issue in `atrium-project` for this integration driver; link it to the four per-repo service tests.

## §5.4 — Paradata trust chain and reproducibility

**Current state:** `atrium_paradata.py` logs tool name, version, repo URL, Python env, and a `run_id` per execution cycle. Paradata is serialized to JSON in a dedicated `paradata/` directory.

**Strategic requirement (from DARIAH/Horizon mandate):** Provenance must be sufficient for a third-party researcher to identify and re-run a specific historical pipeline configuration; quarantine all outputs if a model version is later found to produce hallucinations.

**Concrete enhancements:**

1. **TEATER thesaurus version hash** — when `keywords.py` uses LLM extraction, log the SHA-256 of the thesaurus file used (issue #6 prerequisite).
2. **Model version pinning** — `para_config.txt` in each repo should carry the exact HuggingFace revision string (not just the model name) to make paradata logs replayable.
3. **Paradata schema version** — add a `schema_version` field to the top-level paradata JSON so downstream consumers can handle format evolution gracefully.
4. **YAML reproducibility snapshot** — for each batch run, emit a companion `<run_id>_replay.yaml` that captures all config constants, model revisions, and input file hashes in a format that can be fed back to re-run the exact same configuration. This satisfies the DARIAH reproducibility requirement without requiring blockchain/ledger infrastructure.

**GitHub tracking:** This can be a single issue in `atrium-project` with sub-tasks per repo.

## §5.5 — CI/CD gates and release automation

The GitHub Actions workflow suite (`codeql.yml`, `security.yml`, `pre-commit.yml`, `scheduled-smoke.yml`, `gitleaks.yml`, `release.yml`, `image-scan.yml`, `gpu-inference.yml`) is in place across all four repos. Remaining gaps:

| Gap                                                                                                | Repo(s)    | Action                                                              |
|----------------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------|
| `GITLEAKS_LICENSE` org secret not confirmed set                                                    | All        | Verify in org settings; Gitleaks workflow silently skips without it |
| `gpu-inference.yml` self-hosted runner (`@rharasim`) not confirmed registered                      | nlp-enrich | Ping `@rharasim`; add runner health check job                       |
| GHCR published packages — confirm `image-scan.yml` has correct image path per repo                 | pc, alto   | Check `ghcr.io/ufal/<repo>` image exists before scan step           |
| `pre-commit.yml` is advisory (`continue-on-error: true`) in all four — no plan to make it blocking | All        | Revisit after coverage baselines settle; see thread E above         |

---

## Per-repo "How to verify" (unchanged recipe)

```bash
python -m compileall -q .
ruff check --config <atrium-project/docs/templates/ruff.toml> .
pytest -m "not slow" --cov=. --cov-report=term-missing
# services: uvicorn/compose up, hit /info + DoS guards
# cross-check: CITATION.cff version == para_config version == latest git tag
```