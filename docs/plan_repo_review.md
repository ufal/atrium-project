# ATRIUM source-code review · Opus 4.8 round (2026-06-22)

> **Method.** The four tool repos were explored at the exact HEADs the prior plan
> (`atrium-project/docs/plan_repo_review.md`, 2026-06-21) measured, so this round **verifies that
> plan against live code** (file:line), folds in **live GitHub state** (releases, CI run health,
> open issues), corrects a few stale/overstated claims, and lays out a phased strategy.
> Coverage numbers are **carried** from the 2026-06-21 run on these identical HEADs (re-measure
> after Thread G); everything tagged *NEW/verified* was read directly this round.
>
> **Reviewed HEADs:** pc `c6e7f0c` · translator `91836fb` · alto `5868b0f` · nlp `6501591` · project `dbcb6e7`.

## 1. Ecosystem snapshot

| Repo                | Latest release             | Code version                                    | Live CI (test branch)                                                  | Last measured fast-suite                            |
|---------------------|----------------------------|-------------------------------------------------|------------------------------------------------------------------------|-----------------------------------------------------|
| page-classification | `v1.4.2-beta` (06-21, bot) | CITATION `1.4.2-beta` / **api.py `1.4.0-beta`** | 🟢 Docker · Security · pre-commit · CodeQL                             | 210 passed +3 env-fails; coverage TBD (torch-gated) |
| translator          | `v0.6.1` (06-17)           | CITATION/para `0.6.2` / **api.py `0.6.1`**      | 🟢 at HEAD (earlier `startup_failure` on Security, fixed by `91836fb`) | 183 passed · **52%**                                |
| alto-postprocess    | `v0.19.1` (06-21, bot)     | CITATION/para `0.19.1` ✓                        | 🟢 Security · Docker · pre-commit · CodeQL                             | 226 passed · **48%**                                |
| nlp-enrich          | `v0.14.2` (06-21, bot)     | CITATION/para `0.14.2` ✓                        | 🔴 **Shellcheck failing** · rest green                                 | 192 passed · **35%**                                |

**Open issues driving the roadmap:** `atrium-project#10` (this review) · `nlp-enrich#6` TEATER LLM
keyword extraction (Feature, 17 comments) · `nlp-enrich#7` domain NameTag NER training (Q3 milestone)
· `alto#3` categorization calibration (39 comments, very active). **No open PRs.** The pytest/coverage
lane runs **inside the Docker reusable workflow** — there is no standalone "Tests" check.

**Net since 2026-06-21:** the bot auto-released pc/alto/nlp with "ruff + pre-commit + Docker GHA
alignment"; the doc-claimed merges are confirmed present; but four genuinely **new** issues surfaced
(service-API version drift, `para_licenses` divergence, nlp ruff blocking, gitleaks unverified) and
the alto A-2 "near-blocker" is **overstated** (details below).

## 2. Per-repo state — done vs. left

### 2.1 page-classification `v1.4.2-beta` @ `c6e7f0c`
**Done (verified):** CORS wildcard-with-credentials fix (`service/api.py:53`); hardcoded category
fallback removed (`:82`, explicit `# [FIX]`); `pymupdf` declared + `fitz` imported (`:131`) so
`/predict_document` is live; new `test_inference.py`; CI fully green.

**Left to develop:**
- **P0 — `logs_stat.py` aborts the suite.** `supplementary/scripts/logs_stat.py:19` does a bare
  `import pandas`, and `:26` calls `exit(1)` when `tensorboard` is missing; `test_logs_stat.py`
  imports it at collection → in a clean CPU lane the **whole pytest session dies**, not one test.
- **P1 — version drift (V1).** `service/api.py:39` still says `version="1.4.0-beta"` while CITATION
  is `1.4.2-beta` → `/info` reports a stale version.
- **P1 — Thread G.** No root `requirements-test.txt` (only `setup/requirements-test.txt`, declaring
  just `pytest`/`pytest-cov`); missing pandas/matplotlib/sklearn/tensorboard for the fast lane.
- **P2 — registry copy.** `logs_stat.py:70` hardcodes a `REVISION_TO_BASE_MODEL` map that duplicates
  `model_registry.py` (whereas `dataset_timeline.py` imports it correctly). Note the deliberate
  *training-time* scheme comment at `logs_stat.py:29-31` — keep that semantics if centralizing.
- **P2 — PC-1.** `test_run.py` CLI smokes shell out to `run.py`→torch; mark `slow`/`requires_torch`.
- **P2 — V9.** `supplementary/scripts/img2jpeg_v3.py` exists and is README-referenced — confirm it's
  wired into a workflow vs. a leftover. (The plan's "img2jpeg removed" note was about **alto's** copy,
  a different repo — not a contradiction here.)

### 2.2 translator `v0.6.1` (code `0.6.2`) @ `91836fb`
**Done (verified):** `processors/backend.py` + `processors/chunking.py` at 100% with `test_backend.py`;
`.pre-commit-config.yaml` present; CORS hardened (`service/api.py:52`); `load_vocab.py:15-20`
XXE-hardened (`_SECURE_PARSER`, entities off / no-network / capped tree).

**Left to develop:**
- **P0 — `load_vocab.py` 0%.** ~170–247 stmts of OAI-PMH/GraphQL harvesting with **no dedicated
  `test_load_vocab.py`** (only incidental hits via `test_translator.py`) — the single largest
  untested surface. Mock the network.
- **P1 — version drift (V1).** `service/api.py:43` = `0.6.1` vs CITATION/para `0.6.2`.
- **P1 — coverage cores.** `processors/identifier.py` 21% (FastText wrapper; mock `fasttext.load_model`),
  `main.py` 34% (orchestration 210-387), `para_licenses.py` 20% (resolution engine 135-189).
- **P2 — Thread G.** `requirements-test.txt` omits `fasttext-wheel, numpy, tqdm, huggingface-hub`;
  `test_main.py:9 → main → processors/identifier:1 (import fasttext)` fails collection clean.
- **P2 — F.** `CITATION.cff:5` `date-released: 2026-03-02` is ~112 days stale.

### 2.3 alto-postprocess `v0.19.1` @ `5868b0f` — *healthiest of the four*
**Done (verified):** new `test_alto_stats_create.py`/`test_page_split.py`/`test_langID_classify.py`/
`test_calibration.py`/`test_categorization_routes.py`; Qwen2.5-0.5B is the service default; the prior
`img2jpeg_v3.py` orphan is gone; CITATION `0.19.1` == para `v0.19.1`; 226 passed.

**Left to develop:**
- **A-2 — REFRAMED (was flagged near-blocker, downgrade to P2 + verify).** The plan said the default
  `PERPLEXITY_THRESHOLD_MAX = 1000.0` is "calibrated for distilgpt2." That's **incorrect** — per the
  README table (`README.md:356-358`) and `config_langID.txt:45`, **`1000.0` *is* the Qwen value**
  (distilgpt2's is `3000.0`), so the batch config is correctly Qwen-matched. The real, smaller issues:
  (a) the guard at `langID_classify.py:747` warns whenever `qwen` **and** `threshold > 500.0` — so it
  **mis-fires at the documented-correct `1000.0`**; tighten the cutoff to the real Qwen ceiling; and
  (b) confirm the **service path** (`service/text_inference.py`) uses the same calibrated threshold as
  the batch path (parity check).
- **P1 — Thread I.** `test_page_split.py` / `test_alto_stats_create.py` are subprocess CLI smokes
  (`subprocess.run([sys.executable,…])`), so `page_split.py` and `alto_stats_create.py` still read
  **0%**. Add in-process tests that import and call the functions.
- **P1 — coverage cores.** `langID_classify.py` 35% (threshold core 232-392, 617-726);
  `extract_LLM_ALTO_2_TXT.py` 0% (GLM-4v path, mock the VLM).
- **P2 — Thread G/Docs.** `requirements-test.txt` header claims "no ML models, no GPU libraries" but
  10 modules need pandas/lxml/fastapi and the repo has top-level torch imports — make the claim true or
  add the deps.
- **P2 — F.** `CITATION.cff:5` `date-released: 2026-03-02` stale.

### 2.4 nlp-enrich `v0.14.2` @ `6501591` — *lowest coverage; only red CI*
**Done (verified):** `shellcheck.yml` added; `.pre-commit-config.yaml` present; CITATION `0.14.2` ==
para `v0.14.2`, `date-released: 2026-06-21` current; new `test_keywords.py` + `test_summarize_utils.py`;
192 passed; `teitok_read.py` 100%, `flexiconv_convert.py` 90%, `rescale.py` 90%.

**Left to develop:**
- **P1 — V3 (live red).** `.github/workflows/shellcheck.yml` header says "never block a merge" (lines
  2-4) but the `ludeeus/action-shellcheck` step (`:27`) has **no `continue-on-error`** → it fails the
  job; **CI is red right now**. There's also a redundant second `actions/checkout` (`:30-31`). Make the
  action advisory (or drop it, keeping the manual `continue-on-error` step at `:36-39`).
- **P1 — N-1.** `llm_utils.py:42` top-level `import torch` aborts `test_llm_utils.py` collection on a
  CPU lane, trapping pure-logic helpers (`_should_process_line`, `validate_llm_output`,
  `get_context_window`). Guard/lazy-import + `pytest.importorskip`.
- **P1 — V6.** `.pre-commit-config.yaml` runs ruff with `--exit-non-zero-on-fix` → **blocking**,
  against the project's advisory-first policy (other repos don't). Align it.
- **P0/Feature — `#6`.** `keywords.py` 21% (extraction core 288-835); blocked on N-1 carving. The
  `LLMKeywordExtractor` + JSON-schema output is the headline feature.
- **P1 — coverage.** `summarize_nt_udp.py` 16% (largest logic block), `llm_run.py`/`vocab_manager.py`/
  `fix_teitok_bboxes.py` 0%.
- **P2 — Thread G.** `requirements-test.txt` omits `pydantic, lxml, fastapi, httpx, torch`.

## 3. Cross-repo threads (refreshed)

**G — fast lane is not self-contained (all 4).** Confirmed live. pc has no root
`requirements-test.txt`; the other three under-declare. Heavyweight imports (`torch`, `fasttext`,
`pandas`, `tensorboard`) crash *collection* rather than skipping. Fix per repo: pin the full
CPU-runnable set **or** lazy-import + `pytest.importorskip`. *Precondition for any honest `fail_under`.*

**H — `para_licenses.py` / `atrium_paradata.py` have diverged AND are untested (all 4) — escalated.**
`merge_effective_licenses` got the `(#12)` dedup in **alto** (`para_licenses.py:167-188`) but
translator/pc/nlp are still the **naive** union (translator `:211-215`); `LICENSE_RANK` also differs
(alto/nlp carry `glm-4`/`AGPL-3.0`, others don't). The alto `v0.17.0` release notes *explicitly* said
"these fixes should land in every copy" — propagation didn't happen. And **no repo tests the
resolution engine** (`resolve_effective_license`/`merge_effective_licenses`) at all, despite it
deciding each run's output license. Write the test suite once, replicate, then re-converge the copies.

**F — release/version hygiene.** `CITATION == para_config` holds everywhere, but **(new) `CITATION !=
service/api.py` version** in pc and translator (V1), and `date-released` is ~112 days stale in
translator + alto. Add a CONTRIBUTING post-release checklist line; better, source the API `version=`
from CITATION/para instead of a literal.

**I — subprocess-vs-import tests.** alto (`test_page_split`, `test_alto_stats_create`) and pc
(`test_run`) "have tests" that shell out and therefore contribute **0% coverage**. Keep them as thin
CLI smokes; add in-process tests for real coverage.

**CI/CD matrix.** All four carry codeql, security (Trivy+SBOM), pre-commit, scheduled-smoke, release,
docker, dependabot; gpu-inference in pc+nlp; shellcheck in nlp only. Gaps: nlp shellcheck defect (V3);
pre-commit blocking is **mixed** (pc/alto blocking, translator/nlp advisory) and nlp ruff is
off-policy blocking (V6); `fail_under` disabled everywhere (gated on G); **gitleaks/secret-scan is not
visible in any workflow (V10)** — verify the reusable `security.reusable.yml` actually runs it, and
confirm the `GITLEAKS_LICENSE` org secret, or secret scanning is silently absent.

## 4. Forward strategy (phased & prioritized)

**Phase 0 — stop the active bleed (days).**
1. nlp `shellcheck.yml` → make the `ludeeus` step `continue-on-error: true` (or remove it; the manual
   advisory step already exists) + delete the redundant checkout. *Turns the only red check green.*
2. Sync `service/api.py` `version=` to CITATION in pc (`1.4.2-beta`) and translator (`0.6.2`) —
   ideally read it from para_config/CITATION so it can't drift again.

**Phase 1 — make the fast lane honest (Thread G; unblocks gating).**
Per repo, pin a self-contained `requirements-test.txt` **or** lazy-import + `importorskip`; create
pc's root file. Guard `logs_stat.py` (V2) and `llm_utils.py` torch (N-1). Decide where the coverage
gate lives — tests run inside the Docker reusable workflow today (full deps), so either add a
lightweight standalone lane or gate inside Docker.

**Phase 2 — cover the high-value untested cores.**
Shared `para_licenses.py` test suite written once + replicated, then **re-converge** the diverged
copies (H/V4). translator `load_vocab.py` (P0, mock net), `identifier.py`, `main.py`; alto in-process
tests for `page_split`/`alto_stats_create`/`langID_classify`; nlp `summarize_nt_udp`/`keywords`.

**Phase 3 — ratchet the gates (after G).**
Re-measure baselines; set `fail_under` ~5 pts below each; flip ruff to blocking uniformly (fix the nlp
policy drift V6 first); verify gitleaks runs (V10).

**Phase 4 — release & provenance hygiene.**
CONTRIBUTING post-release checklist (bump `date-released` + code version at tag time, V8/V1); pin exact
HF revision strings in `para_config`; add `schema_version` to paradata JSON; emit a per-batch replay snapshot.

**Phase 5 — strategic horizon (track in `atrium-project`).**
nlp `#6` TEATER LLM keywords (gated on N-1 + keyword coverage; close-criterion: LLM branch ≥60% +
DK 5-doc sign-off); nlp `#7` domain NameTag NER (Q3); alto `#3` categorization calibration; a
cross-service `run_all.py` orchestration driver over the FastAPI `/info` + job endpoints.

## 5. How to verify (read-only, no push)
- Spot-check any file:line in §2–3.
- Per repo: `python -m compileall -q .` → `ruff check --config
  atrium-project/docs/templates/ruff.toml .` → install the **full** CPU dep set (not just
  `requirements-test.txt`) → `pytest -m "not slow" --cov=. --cov-report=term-missing`.
- Live CI: confirm nlp `Shellcheck` red, others green on `test`.
- Identity chain: `CITATION.cff` == `para_config` == `service/api.py` `version=` == latest tag.

---


