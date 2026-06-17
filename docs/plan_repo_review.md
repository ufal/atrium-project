# ATRIUM source-code review — combined plan (refreshed for the next rounds)

> **Status update — 2026-06-17 (Opus 4.8 round).** The per-repo plans below were *executed* this round against the
> latest `test` commits. Each repo section now leads with **✅ Closed this round**, **🩹 Patch ready (delivered as diffs,
> not yet merged)**, and **▶ Next-round backlog**. Earlier descriptive detail is trimmed where an item is resolved.
> Reviewed heads: page-classification `046d076` · translator `f5650b8` · alto-postprocess `915dbff` · nlp-enrich `7a18dee`.
> All four fast suites green: **263 / 171 / 264 / 180 passed**. Source: [atrium-project#10](https://github.com/ufal/atrium-project/issues/10).

---

# 1/4 — `atrium-page-classification` @ `046d076`

**Repo:** page image classifier (ViT/RegNetY/EfficientNetV2/DiT, optional YOLO); CLI (`run.py`) + FastAPI `service/`.

### ✅ Closed this round
- **Single source of truth** added: `model_registry.py` (CATEGORIES, REVISION_TO_BASE_MODEL, REVISION_BEST_MODELS, MODEL_STATIC) — imported by `classifier.py`, `run.py`, `parallel_best.py`, `service/inference.py` (old F‑A1/F‑A3).
- **Shared ensemble** added: `ensemble.py` (`average_rdfs` + `average_prediction_dicts`) consumed by `parallel_best.py` and `service/inference.py` (old F‑A2/F‑S1).
- **API + YOLO + CLI tests** added: `test_service_api.py` (`/info`, DoS guards, mocked success), `test_yolo_classifier.py`, `test_run.py` (CLI smoke) (old F‑S2, §3 gaps).
- **CI config localized**: `.github/dependabot.yml`, `ruff.toml`, `.coveragerc` present; coverage Step-Summary step made non-fatal (CI green).
- **Version sync**: `CITATION.cff` → `1.4.0-beta`; CONTRIBUTING Release-History top = `v1.4.0-beta` (old F‑R1).

### 🩹 Patch ready (this round; pending merge)
- 🔴 `/predict_document` imports `fitz` but `service/requirements.txt` declared only `pdf2image` → **add `pymupdf`** (endpoint was dead in a clean install).
- Service hardening in `service/api.py`: CORS wildcard-with-credentials; `predict_image` swallows its own `HTTPException`; `content_type=None` → 500; stray `# … rest unchanged …` artifact.

### ▶ Next-round backlog
| Pri | Item                                                                                                                                          | Axis  | Note                         |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------------|-------|------------------------------|
| P1  | Deepen `ModelManager` tests (`service/inference.py` 27%) + `run.py` CLI beyond smoke (23%)                                                    | Tests | pure-logic/selection paths   |
| P2  | Remove residual registry/category copies: `service/api.py:84` fallback list, `supplementary/scripts/logs_stat.py:70`, `dataset_timeline.py:9` | Arch  | import from `model_registry` |
| P2  | Confirm/retag the GitHub release **`v1.4.0-bets`** typo; align CONTRIBUTING lint wording to Ruff                                              | Docs  | tags not in repo             |
| P2  | Decide dedicated `api` build target vs compose `--profile api`; investigate phantom `config.py`/`config-3.py` coverage warning                | CI    | low                          |

---

# 2/4 — `atrium-translator` @ `f5650b8`

**Repo:** structure-preserving translator (LINDAT NMT + Tag-and-Protect, FastText ID, UDPipe lemmas, ALTO/metadata XML). **Now CLI _and_ API** (no longer CLI-only).

### ✅ Closed this round
- **API parity achieved (the headline gap):** `service/api.py` + `service/requirements.txt` added — `/translate` + `/info`, size guard, paradata; **reuses `main.process_single_file`** (no logic duplication) (old F‑S1, F‑A2, F‑T1).
- **`main.py` orchestration tests** added (`test_main.py` → `main.py` 34%) + `test_api.py` TestClient suite (old §3 P0).
- **CI config localized**: `.github/dependabot.yml`, `ruff.toml`, `.coveragerc` present; `requirements-test.txt` carries `fastapi`+`httpx`; caller installs `service/requirements.txt`.
- README now states the dual CLI+API architecture explicitly (old F‑R3).

### 🩹 Patch ready (this round; pending merge)
- New `service/api.py`: CORS wildcard-with-credentials; `/translate` `file.filename=None` → 500.
- Version sync: `CITATION.cff` `0.5.1` → **`0.6.1`** (match `para_config v0.6.1`); README Python badge `3.8+` → **`3.11`**.

### ▶ Next-round backlog
| Pri | Item                                                                                               | Axis    | Note                   |
|-----|----------------------------------------------------------------------------------------------------|---------|------------------------|
| P1  | Test `load_vocab.py` (**0%**, OAI-PMH/GraphQL harvesting) and `para_licenses.py` (20%)             | Tests   | mock network           |
| P1  | Mock-test `_post_with_retry` (back-off/throttle) + encode the homonym single-word-lemma regression | Tests   | translator.py 76%      |
| P2  | Add `.pre-commit-config.yaml` (parity with alto/pc); set real `date-released` at tag time          | CI/Docs | currently `2026-03-02` |
| P2  | `--fast-align` proportional-alignment test suite                                                   | Tests   | only indirect coverage |

---

# 3/4 — `atrium-alto-postprocess` @ `915dbff`

**Repo:** OCR ALTO post-processor — split → stats → extract (alto-tools|LayoutReader|GLM-4v) → line classify → aggregate, + FastAPI service reusing the quality engine. **Healthiest of the four.**

### ✅ Closed this round
- **Service config-sourcing (old F‑S1):** `service/utils.py:33` now reads `PERPLEXITY_THRESHOLD_MAX` from `config_langID.txt` (default 1000.0; no more stale 5000).
- **Pipeline tests added (old §3 P0):** `test_extract_alto` (de-hyph, 0→43%), `test_run_pipeline` (33%), `test_aggregation` (35%), `test_gpu_concurrency`, `test_resume_logic`, `test_service_api` (`text_api` 76%); core `text_util_langID` 88%.
- **CI config + pre-commit:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc`, `.pre-commit-config.yaml` present; CONTRIBUTING standardized on Ruff; `httpx2` added (CI green).
- **Version sync (old F‑R1):** `CITATION.cff 0.18.0` == `para_config v0.18.0`.

### 🩹 Patch ready (this round; pending merge)
- Git-ignore `.idea/` (1 tracked file remains); fix stale `CONTRIBUTING.md:206` ("runs black, isort, flake8" → Ruff).

### ▶ Next-round backlog
| Pri | Item                                                                                                            | Axis        | Note               |
|-----|-----------------------------------------------------------------------------------------------------------------|-------------|--------------------|
| P1  | Tests for still-0% `page_split.py` (145 L) and `alto_stats_create.py` (266 L); raise `langID_classify.py` (10%) | Tests       | pure-ish, CPU-only |
| P1  | Decide `img2jpeg_v3.py` (still orphaned, 0%): wire+test, document, or remove                                    | Arch/Tree   | —                  |
| P2  | Perplexity model↔threshold coupling guard (Qwen vs distilgpt2 scale); VRAM/troubleshooting docs (GLM-4v 48 GB)  | Config/Docs | —                  |
| P2  | `git rm -r --cached .idea` after the ignore patch; confirm `data_samples/*_gpt` dirs are intended fixtures      | Tree        | —                  |

---

# 4/4 — `atrium-nlp-enrich` @ `7a18dee`

**Repo:** CSV → NLP enrichment (manifest → UDPipe → NameTag → TEITOK, + keywords + LLM) via `api_*.sh` shell + a **subprocess-spawning** FastAPI wrapper. Still the lowest-coverage repo.

### ✅ Closed this round
- **High-value tests added (old §3 P0/P1):** `test_chunk.py` (`chunk.py` 0→**86%**), `test_remote_apis.py` (`call_udpipe` 53% / `call_nametag` 56%), `test_api_service.py` (subprocess contract: `service/api.py` 59%, `enrichment.py` 63%, `jobs.py` 77%), `test_llm_utils.py` (`llm_utils.py` 0→17%).
- **CI config + dep fix:** `.github/dependabot.yml`, `ruff.toml`, `.coveragerc` present; `pydantic>=2` (and `pydantic==2.13.3` in `requirements_llm.txt`) added — CI green; CONTRIBUTING uses Ruff.

### 🩹 Patch ready (this round; pending merge)
- Version sync: `CITATION.cff 0.14.0` → **`0.14.1`** (match `para_config v0.14.1`).

### ▶ Next-round backlog
| Pri | Item                                                                                                                                        | Axis       | Note          |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------|------------|---------------|
| P0  | Continue carving testable helpers from `llm_utils.py` (17% of 676 stmts)                                                                    | Tests/Arch | models mocked |
| P1  | Cover `llm_run.py` (**0%**, 212 L), `vocab_manager.py` (15%), `summarize_nt_udp.py` (16%), `keywords.py` (19%), `fix_teitok_bboxes.py` (0%) | Tests      | —             |
| P1  | Add **`shellcheck`** (shell layer still 0% / unlinted) + a `.pre-commit-config.yaml` (parity)                                               | CI         | —             |
| P2  | Disambiguate "API" (external UDPipe/NameTag vs our FastAPI) in docs; troubleshooting/Docker quickstart; set real CITATION `date-released`   | Docs       | —             |
| P2  | Exclude/relocate `service/test_api.py` (manual client, counted as 0%)                                                                       | Tests      | cosmetic      |

---

## Cross-repo status & next-round threads

**Closed across the board this round**
1. **Version skew → synced in all four** (CITATION: pc `1.4.0-beta`, alto `0.18.0` in-repo; translator `0.6.1` & nlp `0.14.1` via this round's patches).
2. **CI config localized in all four** — `ruff.toml` / `.coveragerc` / `dependabot.yml` now present per repo (no longer template-only).
3. **Orchestration/entry points now tested** — `run.py` / `main.py` / `run_pipeline.py` and every FastAPI service have suites; services are measured.
4. **"Merged pipeline & API service" parity reached** — translator gained a service, so **all four** ship a FastAPI layer (alto = import-reuse reference; pc = shared registry/ensemble; nlp = subprocess; translator = `process_single_file` reuse).

**New common threads for the next rounds**
- **A. Service-layer hardening pattern** — CORS wildcard-with-credentials recurs (pc + translator) plus `None` content-type/filename guards; patches ready, fold into a shared checklist for any new endpoint.
- **B. `.pre-commit-config.yaml` parity** — present in pc + alto, **missing in nlp + translator**.
- **C. Coverage depth on entry/IO modules** — `load_vocab.py`, `llm_run.py`, `page_split.py`, `alto_stats_create.py`, `llm_utils.py`, `ModelManager` are the shared frontier.
- **D. `shellcheck`** for nlp's shell layer (only shell-heavy repo; still unlinted).
- **E. Ratchet the CI gates** — now that `ruff.toml`/`.coveragerc` are in every repo, consider enabling Ruff blocking + `fail_under` once counts settle.
- **F. Hygiene** — confirm/retag pc's `v1.4.0-bets` typo; set real `date-released` in nlp + translator CITATION at tag time.

**Per-repo "How to verify" (unchanged recipe):**
```bash
python -m compileall -q .
ruff check --config <atrium-project/docs/templates/ruff.toml> .
pytest -m "not slow" --cov=. --cov-report=term-missing
# services: uvicorn/compose up, hit /info + DoS guards; cross-check CITATION vs para_config vs git tag -l