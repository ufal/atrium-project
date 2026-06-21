# ATRIUM source-code review — combined plan (refreshed for the next rounds)

> **Status update — 2026-06-21 (live `test`-branch HEAD round).** The four `test` branches were
> cloned at their current HEADs and the suites were **executed locally** for this refresh — coverage
> numbers below are measured, not carried over. Several prior-round "confirm merged" items are now
> **verified merged**; several P1 backlog items are **closed**; and a handful of **new findings**
> surfaced from running the suites in a clean CPU-only environment (the realistic CI lane).
>
> **Reviewed heads (this round):**
> - page-classification `c6e7f0c` — "update GHA workflows and test coverage of inference"
> - translator `91836fb` — "fix security GHA"
> - alto-postprocess `5868b0f` — "docs update and Qwen as default for service API"
> - nlp-enrich `6501591` — "fix shellcheck GHA"
>
> **Measured fast-suite results (CPU-only, `-m "not slow"`):**
> - translator **183 passed** · TOTAL coverage **52%**
> - alto-postprocess **226 passed** · TOTAL coverage **48%**
> - nlp-enrich **192 passed** · TOTAL coverage **35%** (excl. one torch-gated test, see N-1)
> - page-classification **210 passed** + 3 env-only failures · core modules green (see PC-1)
>
> Source: [atrium-project#10](https://github.com/ufal/atrium-project/issues/10).

---

## ⚠️ New cross-cutting finding this round — the "clean-CI lane" is not actually clean

Running each suite in a fresh venv with only `requirements-test.txt` installed revealed that the
fast lane is **not self-contained** in three of the four repos. Tests fail *at collection time* on
missing imports that `requirements-test.txt` does not declare. This is a CI-correctness issue: a
green badge today depends on the developer's pre-existing environment, not on the declared test deps.

| Repo                | `requirements-test.txt` declares                     | Actually needed at collection                        | Gap                                                                                      |
|---------------------|------------------------------------------------------|------------------------------------------------------|------------------------------------------------------------------------------------------|
| translator          | lxml, requests, fastapi, pytest, httpx2, multipart   | **+ fasttext-wheel, numpy, tqdm, huggingface-hub**   | `test_api.py` / `test_main.py` import `main` → `processors/identifier` → `fasttext`      |
| alto-postprocess    | **pytest, pytest-cov only** ("no ML models, no GPU") | **+ pandas, lxml, pillow, fasttext, fastapi, httpx** | header comment claims no ML deps, but 10 test modules need pandas/lxml/fastapi to import |
| nlp-enrich          | pytest, pytest-cov, requests                         | **+ pydantic, lxml, fastapi, httpx, torch**          | `test_llm_utils.py` → `llm_utils` → `import torch` (heavyweight)                         |
| page-classification | (no `requirements-test.txt` at all)                  | matplotlib, sklearn, tensorboard, torch              | suite aborts entirely if `tensorboard` missing (see PC-2)                                |

**Recommended fix (one shared pattern):** each repo's `requirements-test.txt` should pin the full
set needed to *collect and run the non-slow lane on CPU*, OR the heavyweight imports (torch, fasttext)
should be guarded so the modules import lazily and the tests `pytest.importorskip(...)` instead of
crashing collection. This is now thread **G** below.

---

# 1/4 — `atrium-page-classification` @ `c6e7f0c`

**Repo:** page image classifier (ViT/RegNetY/EfficientNetV2/DiT, optional YOLO); CLI (`run.py`) + FastAPI `service/`.

### ✅ Verified merged / closed this round

- 🔴 **`pymupdf` blocker — FIXED.** `service/requirements.txt` now declares `pymupdf`; `service/api.py:131` imports `fitz`. `/predict_document` is no longer dead in a clean install.
- **Service hardening — MERGED.** `service/api.py:53` now reads `allow_credentials=ALLOWED_ORIGINS != ["*"]` — the CORS wildcard-with-credentials defect is resolved.
- **Hardcoded category fallback removed.** `service/api.py:82` carries an explicit `# [FIX]: Removed the hardcoded fallback list` — the prior P1 registry-duplication item is closed for this file.
- **`v1.4.0-bets` typo question is moot** — repo advanced to `v1.4.2-beta` (CITATION `1.4.2-beta`, CONTRIBUTING release history top = `v1.4.2-beta`, `date-released: 2026-06-20`). Commit message confirms "secret-scan removed, Docker GH actions alignment."
- **New `test_inference.py`** added (HEAD commit: "test coverage of inference").

### ▶ Next-round backlog

| Pri  | Item                                                                                                                                                                                                                                                                               | Axis             | Note                                                                                |
|------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|-------------------------------------------------------------------------------------|
| PC-1 | **3 `test_run.py` CLI smoke tests fail without torch** — they shell out to `run.py`, which imports `classifier.py` → `torch`. In a torch-less lane the subprocess exits non-zero and the assertions flip. Either mark these `slow`/`requires_torch` or stub the import             | Tests/CI         | env-only today, but a real CI without torch would show red                          |
| PC-2 | **`supplementary/scripts/logs_stat.py:26` calls `exit(1)` at import** when `tensorboard` is absent; `test_logs_stat.py` imports it at collection → **the entire pytest session aborts**, not just one module. Replace bare `exit(1)` with a guarded import + `pytest.importorskip` | Tests/Robustness | highest-leverage fix: one missing optional dep currently takes down the whole suite |
| P1   | Deepen `ModelManager`/`service/inference.py` and `parallel_best.py` coverage — both read 0% in the CPU lane only because torch-gated; confirm real numbers in a GPU/torch CI and raise the genuinely-uncovered branches                                                            | Tests            | needs torch lane to measure                                                         |
| P2   | Add a `requirements-test.txt` (the only repo without one) pinning matplotlib, scikit-learn, tensorboard so the fast lane is reproducible                                                                                                                                           | CI               | see thread G                                                                        |
| P2   | Residual registry copies: re-audit `supplementary/scripts/logs_stat.py` and `dataset_timeline.py` for category lists now that the `service/api.py` copy is gone                                                                                                                    | Arch             | import from `model_registry`                                                        |
| P2   | Document TEXT vs TEXT_T boundary ambiguity (accuracy <90%, off-diagonal >10%) in README model notes                                                                                                                                                                                | Docs             | DK sign-off on threshold policy                                                     |

---

# 2/4 — `atrium-translator` @ `91836fb`

**Repo:** structure-preserving translator (LINDAT NMT + Tag-and-Protect, FastText ID, UDPipe lemmas, ALTO/metadata XML). CLI + API.

### ✅ Verified merged / closed this round

- **CORS hardening — MERGED.** `service/api.py:52` = `allow_credentials=ALLOWED_ORIGINS != ["*"]`.
- **Version sync — DONE.** CITATION `0.6.2` == para_config `v0.6.2`.
- **`processors/backend.py` is new and at 100%** + `processors/chunking.py` 100% — the multi-backend translation layer landed with full unit coverage. New `test_backend.py` present.
- **`.pre-commit-config.yaml` present** — the prior thread-B gap (missing in translator) is closed.
- **183 passed** (was 171), `processors/translator.py` at **79%**, `utils.py` **84%**.

### ▶ Next-round backlog

| Pri | Item                                                                                                                                                                                                                   | Axis  | Note                                      |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------|-------------------------------------------|
| P0  | **`load_vocab.py` STILL 0%** (170 stmts, OAI-PMH/GraphQL harvesting). No dedicated `test_load_vocab.py` exists — the only reference is incidental in `test_translator.py`. Single largest untested surface in the repo | Tests | mock the network; top priority            |
| P1  | **`para_licenses.py` still 20%** (lines 135-189 = the resolution engine, untested)                                                                                                                                     | Tests | shared with other repos — see thread H    |
| P1  | `processors/identifier.py` **21%** (FastText wrapper) — mock `fasttext.load_model`, test the language-decision branch                                                                                                  | Tests | new low point now that backend.py is done |
| P1  | `main.py` **34%** — orchestration paths 210-387 uncovered; encode the homonym single-word-lemma regression here                                                                                                        | Tests |                                           |
| P2  | Mock-test `_post_with_retry` back-off/throttle in `translator.py` (lines 433-449 uncovered)                                                                                                                            | Tests |                                           |
| P2  | Add `fasttext-wheel`, `numpy`, `tqdm` to `requirements-test.txt` (collection fails without them)                                                                                                                       | CI    | thread G                                  |
| P2  | **`date-released: 2026-03-02` is stale** in CITATION; set real value at tag time                                                                                                                                       | Docs  | only repo besides alto still stale        |

---

# 3/4 — `atrium-alto-postprocess` @ `5868b0f`

**Repo:** OCR ALTO post-processor — split → stats → extract (alto-tools|LayoutReader|GLM-4v|Qwen) → line classify → aggregate, + FastAPI service. Healthiest of the four.

### ✅ Verified merged / closed this round

- **`img2jpeg_v3.py` orphan — REMOVED.** No longer in the tree anywhere; the prior P1 "wire/document/remove" decision was resolved by removal.
- **Version sync — DONE.** CITATION `0.19.1` == para_config `v0.19.1`.
- **New test modules landed:** `test_alto_stats_create.py`, `test_page_split.py`, `test_langID_classify.py`, `test_calibration.py`, `test_categorization_routes.py` — directly targeting the prior-round 0% modules.
- **226 passed**; `text_util_langID.py` at **84%**.
- **Qwen2.5-0.5B is now the service-default perplexity model** (`service/text_inference.py:99`, env-overridable via `GPT2_MODEL_NAME`).

### ▶ Next-round backlog

| Pri | Item                                                                                                                                                                                                                                                                                                                                                                                                                     | Axis               | Note                                                                    |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|-------------------------------------------------------------------------|
| A-1 | **`test_page_split.py` and `test_alto_stats_create.py` are subprocess CLI smoke tests** — they spawn the script via `subprocess.run([sys.executable, ...])`, so coverage.py never sees the executed lines and both modules **still read 0%** despite "having tests." Add in-process tests that `import` the module and call its functions for real coverage                                                              | Tests              | the tests assert the CLI contract but exercise no importable logic      |
| A-2 | 🟠 **Qwen-default raises the perplexity-coupling risk to urgent.** Default model changed to `Qwen/Qwen2.5-0.5B` but `PERPLEXITY_THRESHOLD_MAX` default is still `1000.0` (calibrated for distilgpt2's scale). Qwen and distilgpt2 produce perplexities on different scales — the threshold is now silently mis-coupled unless overridden. Add a runtime guard that warns/errors if model and threshold scale don't match | Config/Correctness | promoted from P2 to near-blocker because the default flipped this round |
| P1  | Raise `langID_classify.py` from **35%** — lines 232-392 and 617-726 (the threshold-decision core, issue #3 calibration) still uncovered despite the new test file                                                                                                                                                                                                                                                        | Tests              | mock FastText + Qwen; DK confirms boundary values                       |
| P1  | `alto_stats_create.py` **0%** and `page_split.py` **0%** — fold the in-process tests from A-1 here                                                                                                                                                                                                                                                                                                                       | Tests              | CPU-only, pure-ish                                                      |
| P1  | `extract_LLM_ALTO_2_TXT.py` **0%** (137 stmts) — the GLM-4v extraction path has no coverage                                                                                                                                                                                                                                                                                                                              | Tests              | mock the VLM call                                                       |
| P2  | **Fix `requirements-test.txt` header** — it claims "no ML models, no GPU libraries" but 10 modules need pandas/lxml/fastapi to import. Either add them or make the claim true                                                                                                                                                                                                                                            | CI/Docs            | thread G; misleading as written                                         |
| P2  | VRAM/troubleshooting docs: GLM-4v (48 GB) vs Qwen2.5-0.5B (small) vs LayoutReader — now that Qwen is default, document the model-selection matrix                                                                                                                                                                                                                                                                        | Docs               | HEAD already did a "docs update"; extend it                             |

---

# 4/4 — `atrium-nlp-enrich` @ `6501591`

**Repo:** CSV → NLP enrichment (manifest → UDPipe → NameTag → TEITOK, + keywords + LLM) via `api_*.sh` shell + FastAPI wrapper. Still the lowest-coverage repo.

### ✅ Verified merged / closed this round

- **`shellcheck.yml` workflow added** — the prior thread-D gap is closed (shell layer now linted in CI).
- **`.pre-commit-config.yaml` present** — thread-B gap closed.
- **Version sync — DONE.** CITATION `0.14.2` == para_config `v0.14.2`; `date-released: 2026-06-21` (current).
- **New `test_keywords.py` + `test_summarize_utils.py`** added; `192 passed`.
- `api_util/teitok_alto.py` **80%**, `teitok_read.py` **100%**, `chunk.py` **86%**, `flexiconv_convert.py` **90%**, `service/rescale.py` **90%**.

### ▶ Next-round backlog

| Pri | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                | Axis       | Note                                                |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|-----------------------------------------------------|
| N-1 | **`test_llm_utils.py` aborts collection without `torch`** — `llm_utils.py:42` does a top-level `import torch`, so the unit test can't run in a CPU lane and `llm_utils.py` measured **0%** here (was reported 17%). Guard the torch import or `importorskip` so the pure-logic helpers (`_should_process_line`, `validate_llm_output`, `get_context_window`) are testable without torch                                                             | Tests/Arch | prerequisite for issue #6; also a thread-G instance |
| N-2 | **`shellcheck.yml` has a structural defect.** It runs `ludeeus/action-shellcheck` (scandir `.`) as a **blocking** first step, *then* a second `actions/checkout` + a manual `continue-on-error: true` shellcheck. The header comment says "never block a merge," but the first action is not `continue-on-error` and will fail the job on any finding. Also the second checkout is redundant. Make the action step `continue-on-error` or remove it | CI         | the workflow does the opposite of its stated intent |
| P0  | **[issue #6, open]** TEATER LLM keyword extraction — depends on N-1 carving. `keywords.py` is **21%** (lines 288-835 uncovered = the extraction core). Implement prompt contract + JSON-schema output, wire to existing KER baseline                                                                                                                                                                                                                | Feature    | DK supplies thesaurus snapshot; see §5.1            |
| P1  | Still-0% modules: `llm_run.py` (212 stmts), `vocab_manager.py` (144 stmts), `fix_teitok_bboxes.py` (74 stmts)                                                                                                                                                                                                                                                                                                                                       | Tests      | mock vLLM backend                                   |
| P1  | `summarize_nt_udp.py` **16%** (269 of 320 stmts uncovered) — largest untested logic block in the repo                                                                                                                                                                                                                                                                                                                                               | Tests      | pure-ish CoNLL-U processing                         |
| P2  | `service/test_api.py` (manual integration client) still counted as 0% by coverage — exclude via `.coveragerc` `omit`                                                                                                                                                                                                                                                                                                                                | Tests      | cosmetic, inflates miss count                       |
| P2  | Add `pydantic`, `lxml`, `fastapi`, `httpx` to `requirements-test.txt`                                                                                                                                                                                                                                                                                                                                                                               | CI         | thread G                                            |

---

# Cross-repo status & next-round threads

## Closed / verified across the board this round

1. **`.pre-commit-config.yaml` parity — ACHIEVED.** Present in all four repos now (was missing in nlp + translator last round). Thread B closed.
2. **`shellcheck` for nlp's shell layer — LANDED** (workflow present, though see N-2 for the config defect). Thread D substantially closed.
3. **Version sync holds** in all four (CITATION == para_config version string in each).
4. **CORS wildcard-with-credentials — MERGED** in both pc and translator. Prior thread-A patches confirmed.

## Active cross-repo threads

**G. (NEW, highest priority) Make the fast test lane self-contained.** Three of four repos fail
collection in a clean env because `requirements-test.txt` under-declares deps, and heavyweight
imports (`torch`, `fasttext`) crash collection rather than skipping. Two acceptable fixes, pick one
per repo: (a) pin the full CPU-runnable dep set in `requirements-test.txt`, or (b) make the
heavyweight imports lazy and have the tests `pytest.importorskip("torch")`. Page-classification needs
a `requirements-test.txt` created from scratch. This blocks any honest `--fail-under` gate (thread E).

**H. `para_licenses.py` coverage frontier.** The computed-license resolution engine (most-restrictive-wins)
is **20%** in translator and similarly low elsewhere; it's a ported, near-identical module across
repos. Write the test suite once against the shared logic and replicate — high value, low effort,
no mocking of models or network required.

**I. Subprocess-vs-import test pattern.** alto-postprocess (A-1) and page-classification (`test_run.py`)
both have "tests" that shell out to a script as a subprocess. These verify the CLI contract but
contribute **zero coverage** and can't pinpoint failures. Where the goal is coverage, add in-process
tests that import and call functions; keep the subprocess test only as a thin CLI-smoke layer.

**J. Coverage depth on entry/IO modules (refreshed measured numbers).**

| Module                      | Repo       | Measured % (this round) | Note                          |
|-----------------------------|------------|-------------------------|-------------------------------|
| `load_vocab.py`             | translator | **0%**                  | no dedicated test at all — P0 |
| `llm_run.py`                | nlp-enrich | **0%**                  | vLLM mock                     |
| `vocab_manager.py`          | nlp-enrich | **0%**                  |                               |
| `fix_teitok_bboxes.py`      | nlp-enrich | **0%**                  |                               |
| `alto_stats_create.py`      | alto       | **0%**                  | subprocess-only test (A-1)    |
| `page_split.py`             | alto       | **0%**                  | subprocess-only test (A-1)    |
| `extract_LLM_ALTO_2_TXT.py` | alto       | **0%**                  | GLM-4v path                   |
| `summarize_nt_udp.py`       | nlp-enrich | **16%**                 | largest logic block           |
| `keywords.py`               | nlp-enrich | **21%**                 | issue #6 prerequisite         |
| `langID_classify.py`        | alto       | **35%**                 | issue #3 calibration          |
| `main.py`                   | translator | **34%**                 | orchestration                 |

**E. Ratchet CI gates** — unchanged in intent, but **gated on thread G**: a `--fail-under` gate is
meaningless while the suite can't collect in CI's own environment. Sequence: fix G first, establish
measured baselines (translator ~52%, alto ~48%, nlp ~35%, pc TBD under torch), then set `fail_under`
~5 points below baseline per repo and make `ruff check` blocking.

**F. Release hygiene** — `date-released` is current in pc (`2026-06-20`) and nlp (`2026-06-21`) but
**still stale** in translator and alto (`2026-03-02`). Add a post-release checklist line to those two
CONTRIBUTING files. The `v1.4.0-bets` tag concern is retired (pc moved to `v1.4.2-beta`).

---

# §5 — Strategic Horizon (feature + research milestones)

Unchanged in structure from the prior refresh; status notes updated against this round's findings.

## §5.1 — TEATER LLM keyword extraction [`atrium-nlp-enrich` issue #6, open]

**Status:** still open, still "In Progress" on the ATRIUM project board. The blocking prerequisite is
now sharper: **N-1** (decouple `llm_utils.py` from a top-level torch import) must land before the
pure-logic helpers can be unit-tested, and `keywords.py` is only **21%** covered. Implementation
outline unchanged: `LLMKeywordExtractor` wrapping the existing backend, thesaurus in the system
prompt, JSON-schema-constrained output via xgrammar/Pydantic, KER fallback, paradata logging of the
thesaurus version hash. **Close criterion:** `test_keywords.py` covers the LLM branch ≥ 60% and DK
signs off on a five-document sample run.

## §5.2 — Domain-specific NameTag NER model [`atrium-nlp-enrich` issue #7]

**Status:** unchanged — a multi-week ML training task tracked as a separate milestone, not blocking
code-review rounds. `call_nametag.py` is at **56%**; cover the new model endpoint before wiring.
Decision still open: local NameTag 3 instance vs LINDAT REST (latency/offline tradeoff).

## §5.3 — End-to-end pipeline orchestration

**Status:** no cross-service orchestration layer landed this round. Recommendation stands: add a
`run_all.py` integration driver chaining page-classification → alto-postprocess → nlp-enrich →
translator over the existing FastAPI `/info` + job endpoints, with retry logic and shared paradata
accumulation. Open a tracking issue in `atrium-project`.

## §5.4 — Paradata trust chain and reproducibility

**Status:** `para_config.txt` now carries a `version` field per repo (verified), a step toward
replayable provenance. Remaining: pin exact HF revision strings (not just model names) in
`para_config.txt`; add a `schema_version` field to the paradata JSON; emit a `<run_id>_replay.yaml`
snapshot per batch. With **Qwen now the alto default**, model-revision pinning is more important —
paradata must record which perplexity model produced a given line's quality routing.

## §5.5 — CI/CD gates and release automation

**Status this round:** the workflow suite is present in all four repos (`codeql`, `security`,
`pre-commit`, `scheduled-smoke`, `release`, `docker`, plus `gpu-inference` in pc + nlp and
`shellcheck` in nlp). Note: **`secret-scan`/gitleaks was folded into `security.yml`** (pc commit
message confirms "secret-scan removed"). Remaining gaps:

| Gap                                                         | Repo(s)                   | Action                                                      |
|-------------------------------------------------------------|---------------------------|-------------------------------------------------------------|
| `shellcheck.yml` blocking-vs-advisory defect (N-2)          | nlp                       | make the action step `continue-on-error`                    |
| `GITLEAKS_LICENSE` org secret confirmation                  | all                       | verify in org settings (gitleaks silently skips without it) |
| `gpu-inference.yml` self-hosted runner (`@rharasim`) health | pc, nlp                   | add a runner health-check job                               |
| Fast lane not reproducible in CI (thread G)                 | translator, alto, nlp, pc | precondition for `fail_under`                               |

---

## Per-repo "How to verify" (updated recipe — install the FULL test deps, not just `requirements-test.txt`)

```bash
python -m compileall -q .
ruff check --config <atrium-project/docs/templates/ruff.toml> .

# NOTE (thread G): requirements-test.txt currently under-declares deps in 3/4 repos.
# Until fixed, install the real CPU set explicitly, e.g.:
#   translator:  + fasttext-wheel numpy tqdm huggingface-hub
#   alto:        + pandas lxml pillow fasttext fastapi httpx
#   nlp:         + pydantic lxml fastapi httpx   (torch for test_llm_utils)
#   pc:          + matplotlib scikit-learn tensorboard   (torch for inference/yolo/classifier)

pytest -m "not slow" --cov=. --cov-report=term-missing
# services: uvicorn/compose up, hit /info + DoS guards
# cross-check: CITATION.cff version == para_config version == latest git tag
```