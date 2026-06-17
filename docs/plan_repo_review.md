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



