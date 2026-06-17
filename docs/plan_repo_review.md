# Code‑Review Plan 1/4 — `atrium-page-classification`

> **Context.** This is the "next round" of LLM source validation from [atrium‑project#10](https://github.com/ufal/atrium-project/issues/10). Earlier rounds aligned Docker/CI and applied review edits (latest tag ≈ `v1.4.0-beta`). This document is a **detailed, repository‑specific review plan with concrete findings already surfaced during scoping**, organized along the six axes the issue names: Docker+CI, merged pipeline & API service, per‑function test coverage, architecture, file‑tree structure, and CONTRIBUTING.md/release history. Each section gives **current state → findings → review actions**, and the plan closes with a prioritized backlog and a verification recipe.

**Repo in one line:** historical document‑**page image classifier** (ViT / RegNetY / EfficientNetV2 / DiT, optional YOLO) exposed as a CLI (`run.py`) and a FastAPI service (`service/`), packaged via the shared ATRIUM Docker/CI template.

---

## 1. Program architecture

**Current state — module map**

| Module                                    | ~LOC      | Responsibility                                                                                                                        |
|-------------------------------------------|-----------|---------------------------------------------------------------------------------------------------------------------------------------|
| `run.py`                                  | 715       | CLI orchestrator: argparse (20+ flags), config merge, single/dir/PDF inference, train, eval, ensemble dispatch                        |
| `classifier.py`                           | 846       | `ImageClassifier` (HF `AutoModelForImageClassification` + processor), `BalancedBatchSampler`, `custom_collate`, `split_data_80_10_10` |
| `parallel_best.py`                        | 743       | Memory‑aware ensemble: `pack_models` (bin‑packing), `profile_best_models`, `merge_best`, `average_rdfs`, `run_best_models`            |
| `yolo_classifier.py`                      | 413       | `YOLOClassifier` ultralytics alternative mirroring the `ImageClassifier` API                                                          |
| `utils.py`                                | 162       | `directory_scraper`, `dataframe_results`, `collect_images`, `confusion_plot`                                                          |
| `atrium_paradata.py` / `para_licenses.py` | 390 / 218 | Shared ATRIUM provenance + license resolution (`ParadataLogger`, `resolve_effective_license`)                                         |
| `service/api.py` / `service/inference.py` | 242 / 254 | FastAPI app + `ModelManager` (lazy load, warmup, predict, ensemble)                                                                   |

**Findings**
- **F‑A1 (duplication / single source of truth):** the model registry `REVISION_TO_BASE_MODEL` / `AVAILABLE_VERSIONS` is hard‑coded in **three** places — `run.py`, `classifier.py`, `service/inference.py`. Drift risk every time a model version is added.
- **F‑A2 (logic duplication):** ensemble mean‑of‑softmax averaging is implemented **twice** — `parallel_best.average_rdfs()` and `service/inference._predict_averaged()` — with no shared code.
- **F‑A3:** the 11 category labels are repeated across modules rather than sourced from one constant.

**Review actions**
- [ ] Trace every reader of the model registry and category list; propose a single `model_registry.py` (or `setup/config.txt`‑sourced constant) imported by CLI, ensemble, and service.
- [ ] Extract one `ensemble.py` (or move `average_rdfs` to a shared util) consumed by both `parallel_best.py` and `service/inference.py`.
- [ ] Confirm config precedence (`env → CLI arg → config.txt`) is applied uniformly and documented.

---

## 2. Merged pipeline & API service

**Current state.** FastAPI app (`service/api.py`) with `GET /`, `GET /info`, `POST /predict_image`, `POST /predict_document`. It **correctly reuses** the core `ImageClassifier` (`create_dataloader` / `infer_dataloader` / `top_n_predictions`) via `sys.path` import. Security hardening already applied and marked `# REVIEW FIX`: `MAX_UPLOAD_BYTES`, `MAX_PDF_PAGES`, single CORS registration with env allow‑list, `HTTPException` re‑raised, lifespan handler replacing deprecated `on_event`.

**Findings**
- **F‑S1:** "merged" is only half‑done — the **service reuses the model class but duplicates the registry (F‑A1) and ensemble averaging (F‑A2)**. This is the core "merged pipeline and API service" weakness for this repo.
- **F‑S2:** `service/test_api.py` is a **manual client script, not a pytest suite** — the API has zero automated tests.
- **F‑S3:** `.coveragerc` (shared template) **omits `service/*`**, so service code is invisible to coverage even if tests existed — directly conflicts with the "per‑function coverage" goal for the API.
- **F‑S4:** two frontends (`frontend/`, `frontend-lindat/`) — confirm both are wired and which is canonical; check the LINDAT mount path.

**Review actions**
- [ ] Decide the "merge" target: shared registry + shared ensemble consumed by both `run.py` and the service (closes F‑A1/F‑A2/F‑S1).
- [ ] Add `fastapi.testclient` tests for all four endpoints incl. the DoS guards (oversize upload → 413, too‑many‑pages → 413, bad content‑type → 4xx) and assert `HTTPException` codes survive.
- [ ] Re‑scope `.coveragerc` to include `service/*` (or add a service‑specific coverage run).

---

## 3. Unit‑test coverage per function

**Current state.** `pytest.ini` defines a `slow` marker (GPU/network excluded by default); `tests/conftest.py` sets the Agg backend and `sys.path`. Strong existing coverage: `test_utils.py`, `test_parallel_best.py` (pure bin‑packing/merge logic), `test_averaging.py`, `test_paradata.py`, plus supplementary‑script tests (filtering, downscale, timeline, visualize, logs_stat, per_doc_split). ~2.4 K lines of tests.

**Coverage gaps (the heart of this axis)**

| Untested surface | File | Note |
|---|---|---|
| `ImageClassifier` train/load/save/from_hub | `classifier.py` | GPU/network → mark `@slow` **and** add light unit tests for pure helpers (collate, split already partly covered) |
| **`YOLOClassifier` — entirely untested** | `yolo_classifier.py` | whole alternative model path has zero tests |
| CLI parsing / config merge / dispatch | `run.py` (715 LOC) | no tests for argparse + config precedence |
| FastAPI endpoints | `service/api.py` | see F‑S2 |
| `ModelManager` | `service/inference.py` | only exercised via manual client |

**Review actions**
- [ ] Add a per‑function coverage matrix to the review (module → function → tested? slow?).
- [ ] Prioritize **pure‑logic** unit tests that need no GPU: `run.py` arg/config helpers, `ModelManager` registry/selection logic, `YOLOClassifier.build_yolo_dataset` directory layout.
- [ ] Mark genuinely GPU/network tests `@slow` so CI (`-m "not slow"`) stays green while raising real coverage.
- [ ] Consider re‑enabling `fail_under` in `.coveragerc` once the floor is known (currently disabled project‑wide).

---

## 4. Docker + GitHub Actions ("already done — to be expanded")

**Current state.** `Dockerfile` (python:3.11‑slim, CPU default + `TORCH_INDEX_URL` GPU build‑arg, torch pinned `2.7.1`, `transformers<5` to avoid meta‑device crash, non‑root `atrium` UID 10001, volumes for model/HF cache/data, entrypoint `run.py`). CI = thin `docker.yml` calling the shared `ufal/atrium-project/.github/workflows/docker-tool.reusable.yml` (test → `pytest -m "not slow" --cov`; PR‑only docker smoke build; tag/release build‑and‑push with provenance build‑args). `release.yml` zips `service/` + `setup/` + core scripts. Caller inputs: `hf-model-cache: true`, `build-targets: ["base"]`.

**Findings & expansion opportunities**
- **F‑D1:** verify a **local `ruff.toml` and `.coveragerc`** exist in the repo (the reusable workflow runs `ruff check .` and `--cov`; templates live in `atrium-project/docs/templates/` but each repo needs its own copy).
- **F‑D2:** **Dependabot not yet adopted** — the `dependabot.yml` template (weekly pip + actions, targeting `test`, ignoring torch/torchvision/transformers≥5) is the obvious next expansion.
- **F‑D3:** Ruff is **non‑blocking** (`continue-on-error`) and coverage `fail_under` is **disabled** — fine for rollout; flag as the next ratchet once clean.
- **F‑D4:** `build-targets: ["base"]` only — the API ships from the base image via a compose `--profile api`. Decide whether a dedicated `api` build target (like nlp‑enrich) is warranted, or document the profile approach.
- **F‑D5:** confirm the GPU overlay (`docker-compose.gpu.yml`) and the informational `gpu_info.py` never abort CPU‑only runs.

**Review actions:** add `.github/dependabot.yml`; confirm local `ruff.toml`/`.coveragerc`; verify the smoke‑build matrix target mapping; sanity‑check that `release.yml`'s zip contents stay in sync with the actual service entrypoints.

---

## 5. File‑tree structure

**Current state.** Clean layering: CLI → core → ensemble → service, with `supplementary/scripts/` (independent tools, own tests), `data_scripts/` (PDF→PNG, unix+windows), `setup/` (config + requirements), and git‑ignored runtime dirs (`model/`, `result/`, `checkpoint/`).

**Findings**
- **F‑T1:** `README.html` (generated artifact) is committed alongside `README.md` — decide whether to keep a generated file in VCS.
- **F‑T2:** git‑ignored `model/`, `result/`, `checkpoint/` are documented as Docker volumes but can confuse local devs — note in README.
- **F‑T3:** supplementary scripts depend on tight **CSV column‑name contracts** with the ensemble output — fragile coupling worth a contract test.
- **F‑T4:** model registry / category constants scattered (mirrors F‑A1/F‑A3).

**Review actions:** confirm `.dockerignore` excludes the runtime dirs; check no stray duplicates of `img2jpeg_v3.py` between root and `supplementary/scripts/`; verify `tests/fixtures/` (not `small_data_samples/`) holds test inputs per the CONTRIBUTING convention.

---

## 6. Documentation — CONTRIBUTING.md (release history in specific)

**Current state.** `CONTRIBUTING.md` (~283 lines): Release History, Project Contributions, Branches & Environments (`test` staging → `master` stable), Contributor Workflow, PR format, Commit conventions (`[type] description`), Code Conventions & Testing (compileall + black/isort/flake8 + the pytest matrix), Documentation Management. README has 11 sections; service docs isolated in `service/README.md`.

**Findings (release‑history focus)**
- **F‑R1:** **version skew** — `CITATION.cff` declares `version: 1.0.0` while the actual release line is `v1.4.0-beta`. CITATION must track the release.
- **F‑R2:** possible **internal inconsistency** in the Release History list ("v1.4.0‑beta" header vs a "current latest v1.3.0‑beta" mention) — reconcile against `git tag`.
- **F‑R3:** the public GitHub tag referenced in #10 is **`v1.4.0-bets`** (typo) — verify the actual tag spelling and fix/retag if needed.
- **F‑R4:** CONTRIBUTING still references black/isort/flake8 while CI standard moved to **Ruff** — align the documented toolchain.
- **F‑R5:** doc gaps — no deployment‑hardening notes, no per‑model GPU‑memory table, LLM‑generated modules not flagged.

**Review actions:** make Release History the single source of truth and cross‑check it against `git tag -l`, GitHub Releases, and `CITATION.cff`; align the documented lint toolchain with Ruff; add a short "what's LLM‑generated / must be manually verified" note.

---

## 7. Prioritized review backlog

| Pri    | Item                                                                              | Axis         | Refs             |
|--------|-----------------------------------------------------------------------------------|--------------|------------------|
| **P0** | Single source of truth for model registry + category labels                       | Arch / Merge | F‑A1, F‑A3, F‑S1 |
| **P0** | Add automated API tests (`TestClient`) incl. DoS guards                           | Tests / API  | F‑S2             |
| **P0** | Reconcile release history ↔ tags ↔ `CITATION.cff` (incl. `v1.4.0-bets` typo)      | Docs         | F‑R1‑3           |
| **P1** | De‑duplicate ensemble averaging into one shared module                            | Arch / Merge | F‑A2             |
| **P1** | Include `service/*` in coverage; add pure‑logic tests for `run.py`/`ModelManager` | Tests / CI   | F‑S3, F‑D1       |
| **P1** | Adopt `dependabot.yml`; confirm local `ruff.toml`/`.coveragerc`                   | CI           | F‑D1‑2           |
| **P2** | Tests for `yolo_classifier.py`                                                    | Tests        | §3               |
| **P2** | Align documented lint toolchain to Ruff; README runtime‑dir/GPU notes             | Docs         | F‑R4, F‑T2       |
| **P2** | Decide on dedicated `api` build target vs compose profile                         | CI           | F‑D4             |

---

## 8. How to verify (review execution recipe)

```bash
cd atrium-page-classification
python -m compileall -q .                                   # import/syntax sanity
ruff check .                                                # matches CI lint
pytest -m "not slow" --cov=. --cov-report=term-missing      # fast suite + coverage map
docker build -t apc:review .                                # Dockerfile still builds (CPU)
uvicorn service.api:app --port 8000 &                       # smoke the API
python service/test_api.py -f small_data_samples/TEXT/<img> -v v4.3 --url http://localhost:8000
git tag -l; sed -n '/version/p' CITATION.cff                # release-history cross-check
```

---

# Code‑Review Plan 2/4 — `atrium-translator`

> **Context.** Same review round as plan 1 ([atrium‑project#10](https://github.com/ufal/atrium-project/issues/10)). `atrium-translator` is the most test‑mature of the four repos but is also the **odd one out architecturally**: it is a CLI‑only pipeline with **no API service**, which makes "merged pipeline and API service" its single most important review axis. Latest release ≈ `v0.6.1`.

**Repo in one line:** structure‑preserving document **translator** (LINDAT NMT + Tag‑and‑Protect vocabulary, FastText language ID, UDPipe lemmatization, ALTO/metadata XML alignment), CLI‑only, packaged via the shared ATRIUM template.

---

## 1. Program architecture

| Module                                    | ~LOC      | Responsibility                                                                                                                                           |
|-------------------------------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `main.py`                                 | 451       | CLI orchestrator: `parse_arguments`, `_read_config`, file collection loop, URL ingestion, context‑managed `ParadataLogger`, per‑doc protected‑term tally |
| `processors/translator.py`                | 457       | `LindatTranslator`: Tag‑and‑Protect vocabulary, NMT‑safe sentinels, `_post_with_retry` (429/5xx back‑off, `LINDAT_MIN_INTERVAL_S`), fuzzy restoration    |
| `processors/lemmatizer.py`                | 169       | `LindatLemmatizer`: UDPipe2 CoNLL‑U client, `get_lemmas_with_features` (Number agreement guard)                                                          |
| `processors/chunking.py`                  | 100       | **Shared** tiered chunker (newline→sentence→clause→word→hard‑cut) used by translator **and** lemmatizer                                                  |
| `processors/identifier.py`                | 53        | `LanguageIdentifier`: FastText wrapper, ISO 639‑3→1, `en` fallback                                                                                       |
| `utils.py`                                | 388       | Hardened XML (`_SECURE_PARSER`, `_XSD_PARSER`), ALTO dual‑pass reconstruction, `_align_tokens_to_lines` / `_align_tokens_proportional`                   |
| `load_vocab.py`                           | 227       | AMCR (OAI‑PMH) + TEATER (GraphQL) vocabulary harvester                                                                                                   |
| `atrium_paradata.py` / `para_licenses.py` | 390 / 219 | Shared provenance + license resolution                                                                                                                   |

**Findings**
- **F‑A1 (good):** `chunking.py` is already a properly shared component across translator + lemmatizer — the cleanest internal reuse of the four repos. Use it as the **reference pattern** when de‑duplicating the other repos.
- **F‑A2:** `main.py` mixes many concerns (arg parsing, config, file discovery, URL download, the translation loop, paradata). Extracting the per‑file translation step into a reusable function is a prerequisite for any future API service (see §2).

**Review actions:** verify config precedence (CLI → `config.txt [DEFAULT]` → defaults) and the legacy flat‑format shim in `_read_config`; confirm the `ParadataLogger` context manager calls `finalize()` on every exit/exception path.

---

## 2. Merged pipeline & API service ⚠️ (defining axis for this repo)

**Current state.** **There is no API service.** `main.py` is a one‑shot CLI; `Dockerfile` is `ENTRYPOINT ["python","main.py"]`; `docker-compose.yml` runs the container once and exposes **no HTTP port**. Sibling repos (`page-classification`, `alto-postprocess`) ship a FastAPI `service/`.

**Finding — F‑S1 (the headline gap).** This repo is **not at API parity** with its siblings. The review must make an explicit decision:
1. **Add a parity FastAPI `service/`** (`POST /translate` for single‑doc + batch, `GET /info`, health), reusing extracted `main.py` logic — est. ~120–200 LOC + tests + a compose `api` profile + port exposure; **or**
2. **Consciously document it as CLI‑only** (batch tool, not a service) and record the rationale so the divergence is intentional, not accidental.

**Review actions:** if (1), gate it on the §1 refactor (extract the translation loop first) and mirror the security hardening already done in `page-classification`'s API (upload/size limits, single CORS, `HTTPException` passthrough, lifespan). Whichever path, update CONTRIBUTING/README so the architecture is stated explicitly.

---

## 3. Unit‑test coverage per function

**Current state.** Richest suite of the four: ~1,394 lines across 6 files + `conftest.py` + `tests/fixtures/` (`sample.alto.xml`, `sample_amcr.xml`).

**Well‑tested:** `chunking.chunk_text` (boundary priority + losslessness), `utils._align_tokens_to_lines`, `process_metadata_xml`, `process_alto_xml`, translator `_load_vocabulary` / `_restore_tags`, lemmatizer `_parse_conllu`, `ParadataLogger`.

**Coverage gaps**

| Untested / light                                | Where                                                                                                                                        | Note                                                                 |
|-------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| **`main.py` orchestration — entirely untested** | `main`, `parse_arguments`, `_build_paradata_config`, `generate_output_path`, `fetch_xml_from_url`, file loop, URL ingestion, exception paths | biggest gap; no regression net on the entry point                    |
| `_post_with_retry` network resilience           | `translator.py`                                                                                                                              | retry count / back‑off / throttle unverified (needs `requests` mock) |
| `_align_tokens_proportional` (`--fast-align`)   | `utils.py`                                                                                                                                   | only 2 indirect tests                                                |
| Homonym single‑word lemma match                 | `translator.py`                                                                                                                              | documented limitation, **no regression test**                        |
| `load_vocab.py` harvesting                      | OAI‑PMH / GraphQL                                                                                                                            | untested (needs mocks)                                               |
| `para_licenses.py` ranking                      | restrictiveness order                                                                                                                        | untested                                                             |
| `LanguageIdentifier`                            | `identifier.py`                                                                                                                              | `@slow` (FastText download) — fine, but add a mocked unit test       |

**Review actions:** add `main.py` tests with mocked translator/identifier (fixtures already exist in `conftest.py`); encode the homonym case as a regression test; mock `requests` to test `_post_with_retry`; add a focused `--fast-align` proportional‑alignment suite.

---

## 4. Docker + GitHub Actions ("already done — to be expanded")

**Current state.** `Dockerfile` python:3.11‑slim, provenance ARGs → ENV (`ATRIUM_RUNNER_*`), non‑root `atrium:10001`, `HF_HOME` cache, no torch (uses `fasttext-wheel`). `docker.yml` calls the shared reusable workflow; caller passes only `image-name`, empty `apt-packages`, no `pre-install-torch`, `build-targets: ["base"]`.

**Findings**
- **F‑D1:** **No local `ruff.toml`, `.coveragerc`, or `.github/dependabot.yml`** — yet the reusable workflow runs `ruff check .` and `--cov`. Add all three from `atrium-project/docs/templates/` (this is the most CI‑under‑configured of the four repos).
- **F‑D2:** caller pins the reusable workflow at **`@main`**, while the project's `docker.caller.example.yml` pins **`@test`** — verify all four repos reference the **same ref** to avoid divergent CI behavior.
- **F‑D3:** with `.coveragerc` absent, coverage currently measures everything (incl. `tests/`, `*paradata.py`) — adding the template `.coveragerc` will make the numbers comparable to siblings.

**Review actions:** add `ruff.toml` + `.coveragerc` + `dependabot.yml`; align the reusable‑workflow ref across repos; confirm the compose mounts (`config.txt` read‑only, `./data`) and provenance env are correct.

---

## 5. File‑tree structure

**Current state.** Clean and focused: `processors/` package, co‑located `tests/` with `fixtures/`, separated configs (`config.txt` user defaults, `para_config.txt` provenance, `amcr-fields.txt` domain XPaths). Agent found **no dead code or duplicates**.

**Findings**
- **F‑T1:** only structural gap is the **missing `service/`** (mirrors F‑S1).
- **F‑T2:** version string is duplicated across `para_config.txt`, `CITATION.cff`, and CONTRIBUTING (see §6) — candidate for a single source.

**Review actions:** confirm `.dockerignore`/`.gitignore` exclude `data_samples/{my_documents,translated_files}` and `output/`; verify `tests/fixtures/` is the only committed test data.

---

## 6. Documentation — CONTRIBUTING.md (release history in specific)

**Current state.** `CONTRIBUTING.md` has a full Release History (`v0.0.2 → v0.6.1`) with meaningful per‑version highlights (v0.6.0 security/XXE hardening, v0.5.0 dual‑pass ALTO + paradata, v0.4.x vocabulary + pytest). README sections: Features, Prerequisites, Project Structure, Usage, Logic Overview, Translation CSV Logs.

**Findings (release‑history focus)**
- **F‑R1 (version skew, 3‑way):** `CITATION.cff` = **v0.5.1** (2026‑03‑02) and `para_config.txt` = **v0.5.1**, but CONTRIBUTING lists **v0.6.1** as latest and the released tag is `v0.6.x`. Pick one source of truth and sync the other two.
- **F‑R2:** README badge says **Python 3.8+** while Docker/CI standardize on **3.11** — align the stated minimum.
- **F‑R3:** README/CONTRIBUTING should state the **CLI‑only** architecture explicitly (ties to the §2 decision).

**Review actions:** centralize the version (e.g., `para_config.txt` as the canonical source) and cross‑check against `git tag -l` + GitHub Releases + `CITATION.cff`; fix the Python‑version badge; confirm the documented lint toolchain matches Ruff.

---

## 7. Prioritized review backlog

| Pri    | Item                                                                                | Axis         | Refs       |
|--------|-------------------------------------------------------------------------------------|--------------|------------|
| **P0** | Decide API‑service parity: build FastAPI `service/` **or** document CLI‑only intent | Merge / Arch | F‑S1, F‑T1 |
| **P0** | Add `main.py` orchestration tests (mocked translator/identifier)                    | Tests        | §3         |
| **P0** | Resolve 3‑way version skew (CITATION ↔ para_config ↔ CONTRIBUTING/tags)             | Docs         | F‑R1       |
| **P1** | Add `ruff.toml` + `.coveragerc` + `dependabot.yml`; align reusable‑workflow ref     | CI           | F‑D1‑3     |
| **P1** | Mock‑test `_post_with_retry`; homonym regression test                               | Tests        | §3         |
| **P1** | If building API: extract `main.py` translation loop into a reusable function first  | Arch         | F‑A2       |
| **P2** | `--fast-align` proportional‑alignment test suite                                    | Tests        | §3         |
| **P2** | Fix Python‑version badge; state CLI‑only architecture in docs                       | Docs         | F‑R2‑3     |

---

## 8. How to verify

```bash
cd atrium-translator
python -m compileall -q .
ruff check .                                                # add ruff.toml first
pytest --cov=. --cov-report=term-missing                    # rich suite; add .coveragerc to scope
python main.py --alto tests/fixtures/sample.alto.xml ...    # CLI smoke (offline path)
git tag -l; grep -i version CITATION.cff para_config.txt    # version cross-check
```

---


# Code‑Review Plan 3/4 — `atrium-alto-postprocess`

> **Context.** Same review round ([atrium‑project#10](https://github.com/ufal/atrium-project/issues/10)). This is the **largest and most pipeline‑heavy** repo: a 5‑stage ALTO→text→quality pipeline with three interchangeable extraction back‑ends and a FastAPI service. It is also the **best example of "merged pipeline & API service"** (the service imports the core quality library wholesale), so the review focus shifts to **test coverage of the pipeline scripts** and **config/version consistency**. Latest release ≈ `v0.18.0` (pre‑release).

**Repo in one line:** OCR **ALTO post‑processor** — split → stats → extract (alto‑tools | LayoutReader | GLM‑4v) → line classify (FastText + Qwen perplexity) → aggregate, with a FastAPI service reusing the same quality engine.

---

## 1. Program architecture

| Module                                    | ~LOC      | Stage / role                                                                                                 |
|-------------------------------------------|-----------|--------------------------------------------------------------------------------------------------------------|
| `run_pipeline.py`                         | 240       | Orchestrator (5 stages); `--method {alto-tools,layoutreader,glm}`, `--skip-split`; merges per‑stage paradata |
| `page_split.py`                           | 150       | ① split multi‑page ALTO → per‑page (hardened parser)                                                         |
| `alto_stats_create.py`                    | 250       | ② `alto-tools -s` stats (ThreadPoolExecutor)                                                                 |
| `extract_ALTO_2_TXT.py`                   | 180       | ③a alto‑tools text + de‑hyphenation                                                                          |
| `extract_LytRdr_ALTO_2_TXT.py`            | 440       | ③b **default** LayoutReader/LayoutLMv3 reorder (GPU, OOM‑halving) — CC BY‑NC‑SA                              |
| `extract_LLM_ALTO_2_TXT.py`               | 270       | ③c GLM‑4v transcription (48 GB+ VRAM) — glm‑4 NC                                                             |
| `langID_classify.py`                      | 660       | ④.1 line classify: 1 GPU perplexity worker + N CPU workers via queue; resume‑capable                         |
| `langID_aggregate_STAT.py`                | 320       | ④.2 aggregate → page quality stats                                                                           |
| `text_util_langID.py`                     | 780       | **Shared core**: detectors, quality‑score formula, categorization — used by classify **and** the service     |
| `img2jpeg_v3.py`                          | 390       | standalone utility — **not called by `run_pipeline.py`**                                                     |
| `atrium_paradata.py` / `para_licenses.py` | 600 / 210 | shared provenance + license                                                                                  |

**Findings**
- **F‑A1 (clarification, not a defect):** the three `extract_*ALTO_2_TXT.py` files are **not redundant** — they are three selectable back‑ends behind `--method`. Review action is to confirm they share a common interface and don't duplicate file‑I/O/batch scaffolding, and that method selection is documented.
- **F‑A2 (strength):** `text_util_langID.py` is a clean shared library — the model for cross‑module reuse. Reference it when de‑duplicating other repos.
- **F‑A3:** `img2jpeg_v3.py` appears orphaned — confirm utility vs dead code.

**Review actions:** verify config precedence (CLI > `config_langID.txt` > defaults); confirm the `LANGID_TEXT_DIR` env handoff between extract and classify; check the GPU/CPU queue handshake in `langID_classify.py` for deadlock/timeout (600 s) handling.

---

## 2. Merged pipeline & API service ✅ (reference implementation)

**Current state.** FastAPI `service/text_api.py` (`GET /`, `GET /info`, `POST /process`). `service/text_inference.py` **imports `text_util_langID` wholesale** (detectors, `compute_quality_score`, `categorize_line`, `pre_filter_line`, `calculate_perplexity_batch`) — **no logic duplication**; falls back to legacy `utils.categorize_line` only if unavailable. `service/utils.py` provides hardened `parse_alto_xml` + LayoutReader reorder.

**Findings**
- **F‑S1 (the real risk — config drift, not code drift):** `service/utils.py` hard‑codes thresholds (e.g. `PERPLEXITY_THRESHOLD_MAX = 5000`) that **disagree with `config_langID.txt` (1000.0)**. The service can silently classify differently from the batch pipeline. The service should read thresholds from the same config.
- **F‑S2:** the service is **untested** (endpoints, model loading, fallback path) and **excluded from coverage** by the shared `.coveragerc` (`omit service/*`).
- **F‑S3:** two frontends (`frontend/` standalone, `frontend-lindat/`); confirm both target the right API base URL.

**Review actions:** make the service source all thresholds/categories from `config_langID.txt`; add `TestClient` tests for `/info` and `/process` (ALTO and TXT inputs) asserting parity with the batch classifier on a fixture; reconsider the `service/*` coverage omit.

---

## 3. Unit‑test coverage per function

**Current state.** ~247 tests in 3 files: `test_text_utils.py` (193 — the shared core, well covered), `test_alto_text_preservation.py` (20 — LayoutReader `parse_alto_xml`/`post_process_text`), `test_paradata.py` (34). `pytest.ini` has `pythonpath=.` and a `slow` marker.

**Coverage gaps (large — the pipeline scripts are essentially untested)**

| Untested                                                            | Risk   | Why it matters                            |
|---------------------------------------------------------------------|--------|-------------------------------------------|
| `extract_ALTO_2_TXT.py` (**de‑hyphenation**)                        | High   | text‑altering logic, no regression net    |
| `langID_classify.py` (GPU/CPU queue, **resume**, 600 s timeout)     | High   | most complex module, concurrency untested |
| `run_pipeline.py` (config parse, `--method` select, env override)   | High   | orchestration regressions invisible       |
| `service/text_api.py` / `text_inference.py` / `utils.py`            | High   | see §2                                    |
| `page_split.py`, `alto_stats_create.py`, `langID_aggregate_STAT.py` | Medium | parsing/aggregation untested              |
| `img2jpeg_v3.py`                                                    | Medium | untested + possibly unused                |

**Review actions:** prioritize **CPU‑only, pure‑logic** tests — de‑hyphenation, `run_pipeline` config/method selection, aggregation groupby math, resume "skip already‑done file" detection; mark GPU paths `@slow`; add the service parity test from §2.

---

## 4. Docker + GitHub Actions ("already done — to be expanded")

**Current state.** `Dockerfile` (77 lines): python:3.11‑slim, `apt build-essential g++ git wget`, pre‑install CPU torch via `TORCH_INDEX_URL`, sparse‑checkout LayoutReader `v3`, hardened FastText `lid.176.bin` download (5× retry/backoff/resume), non‑root, entrypoint `run_pipeline.py`. `docker-compose.yml` has an `api` profile (port 8000) + `gpu` overlay; `.env.example` present. `docker.yml` calls the shared reusable workflow `@main` with `apt-packages: build-essential g++`, `pre-install-torch: torch`, `requirements: requirements.txt service/requirements.txt requirements-test.txt`.

**Findings**
- **F‑D1:** **No local `ruff.toml`, `.coveragerc`, or `.github/dependabot.yml`** — add from templates (Dependabot expansion + scoped coverage).
- **F‑D2:** CONTRIBUTING claims **pre‑commit (black/isort/flake8)** but there is **no `.pre-commit-config.yaml`**, and CI standardized on **Ruff** — reconcile the toolchain (drop black/isort/flake8 wording or add the config).
- **F‑D3:** confirm reusable‑workflow ref consistency (`@main` here vs `@test` in the project example).

**Review actions:** add the three template files + a Ruff‑based `.pre-commit-config.yaml` (or remove the claim); verify the FastText download retry still succeeds offline‑cached; confirm `service/requirements.txt` torch matches the CPU pin.

---

## 5. File‑tree structure

**Current state.** Clean stage‑per‑file layout; `service/` compartmentalized; `data_samples/` mirrors every pipeline output dir (`PAGE_ALTO/`, `PAGE_TXT*/`, `DOC_LINE_CATEG*/`, `DOC_LINE_STATS*/`).

**Findings**
- **F‑T1:** `img2jpeg_v3.py` orphaned (mirrors F‑A3).
- **F‑T2:** `data_samples/` carries `*_gpt` variant dirs — confirm these are intended fixtures, not stale artifacts.
- **F‑T3:** `.idea/` committed — consider gitignoring IDE config.

**Review actions:** confirm `.dockerignore`/`.gitignore` exclude `paradata/`, `data_samples/`, `.idea/`; decide img2jpeg disposition.

---

## 6. Documentation — CONTRIBUTING.md (release history in specific)

**Current state.** README (~1099 lines) documents all 5 stages thoroughly. CONTRIBUTING (~275 lines) has a detailed Release History (`v0.18.0 → v0.1.0`, all marked PRE‑RELEASE) plus branches, PR/commit format, conventions, test commands.

**Findings (release‑history focus)**
- **F‑R1 (3‑way version mismatch):** `CITATION.cff` = **1.0.0** (2026‑03‑02), `para_config.txt` = **v0.15.5**, README/CONTRIBUTING latest = **v0.18.0**. None agree. Establish one canonical version source and sync.
- **F‑R2:** Release History is rich but every entry is "PRE‑RELEASE" — clarify the path to a stable release and which tag is current (`v0.17.0` and `v0.18.0` both referenced across #10 and the project doc).
- **F‑R3:** doc gaps — no architecture/data‑flow diagram, no troubleshooting (CUDA OOM, model‑download timeout), no compute/VRAM requirements per extraction method (esp. GLM‑4v 48 GB).

**Review actions:** sync `CITATION.cff` ↔ `para_config.txt` ↔ Release History ↔ `git tag -l`; add a per‑method VRAM/runtime note and a short troubleshooting section; ensure the main README points to `service/README.md`.

---

## 7. Prioritized review backlog

| Pri    | Item                                                                                                    | Axis           | Refs       |
|--------|---------------------------------------------------------------------------------------------------------|----------------|------------|
| **P0** | Service must read thresholds/categories from `config_langID.txt` (fix stale `PERPLEXITY_THRESHOLD_MAX`) | Merge / Config | F‑S1       |
| **P0** | Pure‑logic tests: de‑hyphenation, `run_pipeline` config/`--method`, aggregation, resume                 | Tests          | §3         |
| **P0** | Resolve 3‑way version mismatch (CITATION ↔ para_config ↔ Release History/tags)                          | Docs           | F‑R1       |
| **P1** | API `TestClient` tests + parity check; include `service/*` in coverage                                  | Tests / Merge  | F‑S2       |
| **P1** | Add `ruff.toml` + `.coveragerc` + `dependabot.yml`; reconcile pre‑commit vs Ruff                        | CI             | F‑D1‑2     |
| **P1** | Decide `img2jpeg_v3.py`: wire in, document, or remove                                                   | Arch / Tree    | F‑A3, F‑T1 |
| **P2** | Perplexity model↔threshold coupling (Qwen vs distilgpt2 scale) guard                                    | Config         | §1         |
| **P2** | GPU timeout/resume integration test (`@slow`); troubleshooting + VRAM docs                              | Tests / Docs   | F‑R3       |

---

## 8. How to verify

```bash
cd atrium-alto-postprocess
python -m compileall -q .
ruff check .                                                # add ruff.toml first
pytest -m "not slow" --cov=. --cov-report=term-missing
docker compose --profile api up --build                     # smoke the FastAPI service
curl -s localhost:8000/info | jq .                          # device/formats/categories
# parity: classify a fixture via batch pipeline vs POST /process and diff categories
grep -i version CITATION.cff para_config.txt; git tag -l    # release-history cross-check
```

---




