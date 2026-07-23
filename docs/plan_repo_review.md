# 🧭 ATRIUM Ecosystem — Repository Review & Forward Strategy

_Maintainer: lutsai.k@gmail.com · Last reviewed: **2026-07-22** (supersedes 2026-06-24)_
_Repos: atrium-project (hub) · atrium-page-classification · atrium-alto-postprocess ·
atrium-nlp-enrich · atrium-translator · **atrium-llm-enrich** (added to scope 2026-07-22)_

## 🧭 1. Scope & method
Single hub-level record of (a) the ecosystem's architecture, (b) the standing cross-repo
workstreams, and (c) the phased roadmap. Findings are verified against the live `test`
branches (HEADs of 2026-07-22), GitHub releases/tags, and the shared reusable workflows —
not against stale snapshots. Each open item carries a `repo:file:line` pointer.

**Scope change this review:** the June edition tracked four repos. Two are now in scope:
**`atrium-llm-enrich`** (LLM stack split out of nlp-enrich; released `v0.1.0`→`v0.3.0`), and
the **hub `atrium-project` itself** (added by the issue #10 comment of 2026-07-16 —
first time the hub is a review target rather than only the review's home).
`atrium-page-classification` has effectively graduated (near-ceiling accuracy, no open code
findings) but stays in the CI federation and the release-gate rollout.

## 🏗️ 2. Ecosystem architecture (as-built)
Six repositories, **not** a monorepo and **not** git-submodules:

```
atrium-project (hub)
  ├─ docs/templates/         ruff.toml, .pre-commit-config, CONTRIBUTING, shared/*
  └─ .github/workflows/*.reusable.yml   ← called by every tool repo via `@test`
Pipeline data flow (container images over a shared volume):
  page-classification → alto-postprocess → translator → nlp-enrich → llm-enrich
```

* **CI is genuinely centralised.** Every tool repo calls the hub's reusable workflows
  (`security.reusable.yml`, `docker-tool.reusable.yml`, `para-drift.reusable.yml`,
  `skill-validate.reusable.yml`) pinned `@test`. This is the real, working federation point.
* **Shared *code* is enforced, not just copied.** `atrium_paradata.py`, `para_licenses.py`,
  and `tests/test_para_licenses.py` are byte-identical across all five tool repos and equal to
  the hub canonical `docs/templates/shared/*`; `para-drift.reusable.yml` fails any repo whose
  copy diverges (the June "copy-pasted and diverged" finding is **closed** — parity re-verified
  2026-07-22, and it held through alto's 1.0.0 → 1.1.0 bumps).
* **The LLM engine is the remaining un-enforced duplication.** `llm_utils.py`,
  `vocab_manager.py`, and `llm_run.py` exist in both nlp-enrich and llm-enrich and sit
  **outside** the para-drift guarantee. See §5.M.

## 🔄 3. Baseline reconciliation (2026-06-24 → 2026-07-22)
The June backlog is essentially executed; the 2026-07-15 and 2026-07-22 release waves shipped
it. Verified green ecosystem-wide today: **`compileall` OK ×6** and **`ruff check` (shared
config) → "All checks passed!" in all five tool repos** (llm-enrich's three June findings —
`eval_metrics.py` B905 + W292 ×2 — fixed in `v0.2.0`). The center of gravity has shifted:
**code quality is no longer the risk; release *plumbing* and cross-repo *governance* are.**

## 📊 4. Status matrix

| ID  | Item                                                          | pc | alto | nlp | translator | llm | hub |
|-----|--------------------------------------------------------------|----|------|-----|------------|-----|-----|
| F1  | API `/info` version hard-coded, drifts from `para_config`    | ✅ | ✅   | ✅  | ✅         | ✅  | —   |
| F2  | `CITATION.cff` `date-released` stale                         | ✅ | ✅   | ✅  | ✅         | ✅  | —   |
| G1  | Eager heavy imports break the no-model fast lane             | ✅ | ✅   | ✅  | ✅         | ✅  | —   |
| G2  | `requirements-test.txt` present & self-contained             | ✅ | ✅   | ✅  | ✅         | ✅  | —   |
| H1  | `para_licenses.py` converged + tested (shared suite)         | ✅ | ✅   | ✅  | ✅         | ✅  | ✅  |
| H2  | `atrium_paradata.py` byte-identical to hub canonical         | ✅ | ✅   | ✅  | ✅         | ✅  | ✅  |
| I1  | in-process CLI tests (`build_parser`/`main(argv)`)           | ✅ | ✅   | ⏳ C4 | ✅       | n/a | —   |
| COV | `fail_under` ratchet set from measured baseline              | 28 | 50   | 30  | 70         | 42  | —   |
| R1  | **Release gate blocks tag/version mismatch**                 | ✅ | ✅   | ✅  | ✅         | ✅  | —   |
| P1c | **Broad-except / silent-swallow correctness fixes**          | ✅ | ✅   | ✅  | —          | ✅  | —   |
| P2t | **Test gaps closed (engine, annotation, img2jpeg, bakeoff)** | ✅ | —    | ✅  | ✅         | ✅  | —   |
| M1  | **nlp↔llm LLM-engine governance (decision)**                 | —  | —    | ⏸️  | —          | ⏸️  | ⏸️  |
| DOC | Canonical tracker / digests reflect reality                  | —  | —    | —   | —          | —   | 🔧  |
| A1  | **API `/info` envelope: service/endpoints/limits (§4.1, #32)**| 🔧 | 🔧   | 🔧  | 🔧         | 🔧  | 🔧  |
| A2  | **API `/health` shallow+deep everywhere (§4.1, #32)**        | 🔧 | 🔧   | ✅  | 🔧         | 🔧  | 🔧  |
| A3  | **Error-code harmonization to §4.4 (4xx not 500/400, #32)**   | ✅ | 🔧   | ✅  | 🔧         | 🔧  | —   |
| A4  | **API contract test + `api-contract.reusable.yml` (#32)**     | 🔧 | 🔧   | 🔧  | 🔧         | 🔧  | 🔧  |
| A5  | **llm-enrich FastAPI service built (§4.2, #32)**             | —  | —    | —   | —          | 🔧  | —   |

Legend: ✅ closed/verified · ⏳ open · ⏸️ deferred (maintainer decision) · 🔴 open
(decision needed) · 🔧 fix prepared, pending review/merge · n/a not applicable · — out of
scope for that repo.

## 🧩 5. Workstreams

### 🔌 A — API meta-contract / OpenAPI conformance (NEW — issue #32)
**Problem.** The services diverged from the normative §4 contract of
`agent_skill_strategy.md`. Only nlp-enrich reported `service`+`limits` and had `/health`;
`/info` never listed `endpoints`; translator keyed the id as `name`, alto as `status`;
translator returned **400** (not 422) for non-XML and alto returned **500** for missing upload
metadata; upload limits / CORS defaults were inconsistent; and **llm-enrich had no HTTP
service at all**. Verified against the `test` HEADs.

**Fix — prepared as patches (all five `test` HEADs + hub).**
* **Shared helper `service/atrium_service.py`** — hub canonical
  `docs/templates/shared/atrium_service.py`, copied byte-identical into every service and now
  covered by `para-drift.reusable.yml`. Provides `read_tool_version`, `build_info` (the §4.1
  envelope, `endpoints` derived from `app.routes`), `attach_health` (shallow + `?deep=true`),
  `resolve_max_upload_mb` (with a deprecated `MAX_UPLOAD_BYTES` fallback), `add_cors`. Retires
  the four copy-pasted `_read_tool_version()`.
* **Per service:** `/info` now always carries `service`/`version`/`endpoints`/`limits`;
  `/health` added everywhere (nlp already had it); error codes harmonized to §4.4 (translator
  400→422; alto 500→422/415 + a new 413 upload guard and an `except HTTPException: raise` so
  intentional 4xx are never re-wrapped as 500); `ALLOWED_ORIGINS` default `*` everywhere (alto
  was localhost-only); `MAX_UPLOAD_MB` canonicalized.
* **llm-enrich service built (§4.2):** new `service/` with `/info`, `/health`,
  `POST /extract_keywords`, `POST /extract_keywords_text`, wrapping the **torch-free**
  `llm_client_shared` engine (OpenRouter/Ollama) — a misconfigured backend is reported
  (`ready:false` / 503), not fatal. Adds a Dockerfile `api` stage + compose `api` profile on
  :8000.
* **Enforcement:** hermetic `tests/test_api_contract.py` in every repo (asserts the /info
  envelope, /health, the advertised endpoint set, and OpenAPI 3.x validity against in-process
  `app.openapi()`), a new hub `api-contract.reusable.yml` + per-repo caller, and the
  `service/atrium_service.py` parity step added to `para-drift.reusable.yml`.
* **Scope (this round):** meta-contract only, per §4 — response bodies are **not** yet typed
  with Pydantic models; the runtime `/openapi.json` is validated but not enriched with
  per-endpoint response schemas (a candidate follow-up). Locations:
  `{pc,alto,nlp,translator,llm}/service/*.py` + `tests/test_api_contract.py`; hub
  `docs/templates/shared/atrium_service.py` + `.github/workflows/api-contract.reusable.yml`.

### 🏷️ F — Release & version hygiene — **CLOSED**
`_read_tool_version()` reads `para_config.txt [tool] version` in every service API; `para_config`
== `CITATION.cff` in all five repos; `date-released` fresh everywhere (2026-07-15 / 07-22).

### 📦 G — Dependency isolation (fast lane) — **CLOSED**
Heavy imports are lazy / test-guarded (`importorskip`); every repo has a self-contained
`requirements-test.txt` (alto's now declares pandas/numpy/lxml/tqdm + the FastAPI test stack;
llm-enrich ships its own). The shared-venv shortcut is retired — clean-venv per repo is now
possible and is the required Tier-2 method.

### 🔗 H — Shared-code provenance — **CLOSED & ENFORCED**
`para_licenses.py` (dedup resolver) + `atrium_paradata.py` are byte-identical to the hub
canonical in all five repos, with the shared `tests/test_para_licenses.py` present everywhere,
enforced by `para-drift.reusable.yml`. Note the scope boundary: **this guarantee covers only the
paradata trio, not the LLM engine (§5.M) and not the `agent-skill` branches** (which strip the
trio with the tests).

### 🧪 I — Test quality (in-process) — **NEARLY CLOSED**
pc `run.py` and alto `page_split.py` now expose `build_parser()`/`main(argv)` with in-process
tests. **One straggler (C4):** nlp `api_util/summarize_nt_udp.py` already has `build_parser()`
+ `main(argv)` (done), but `tests/test_teitok_integraion.py` still shells out for its `--help`
assertion — swap it for `from api_util.summarize_nt_udp import build_parser` +
`build_parser().format_help()` (recipe in the appendix). Low-risk, ~10-line test edit.

### 📈 COV — Coverage ratchets — **DONE (verify on next Tier-2 run)**
`.coveragerc` `fail_under` is set in every repo, each annotated with the measured 2026-07-16
baseline: pc 28, nlp 30, llm 42, alto 50 (baseline 53%), translator 70. Next Tier-2 clean-venv
run should confirm the gates still clear under the new `requirements-test.txt` files, then the
values can be ratcheted up toward the measured baselines where headroom exists.

### 🚦 R — Release-gate hardening (NEW — the P1 of this review)
**Problem.** Each repo's `release.yml` fires on any `v*` tag push and runs
`softprops/action-gh-release` **unconditionally**. The tag == `CITATION` == `para_config` check
*does* exist — in the hub's `security.reusable.yml` `version-check` job — but that runs in a
**separate** workflow, so it can only turn red *after* the release already exists. That is
exactly how two malformed tags reached publication in one week:
* alto `v1.0.0.-beta` (stray dot; CITATION clean `1.0.0-beta`) — later superseded by `v1.1.0-beta`.
* nlp `v1.16.2` (major-version jump; source `0.16.2`) — later re-tagged `v0.16.2` (2026-07-22).

**Fix — LANDED by the maintainer 2026-07-22 on all five tool repos' `test` branches.** An inline
`version-guard` job in each `release.yml` gates the release/create-release job (`needs:
version-guard`); it checks tag == `CITATION` == `para_config` and always requires the tag.
**Deliberately inline, not a hub reusable:** a release-critical gate must not depend on a
cross-repo `uses: …@test` resolving at tag-push time — that ordering gap is what broke the issue
#31 skill-validate rollout. Verified against history: blocks both prior bad tags (alto
`v1.0.0.-beta`, nlp `v1.16.2`) and source-disagreement; passes well-formed `-beta` releases with
no false positives. A DRY `release-guard.reusable.yml` remains a *future* consolidation.
* Locations: `{pc,alto,nlp,translator,llm}/.github/workflows/release.yml`; para_config path is
  `setup/para_config.txt` for pc & alto, `para_config.txt` for the other three.

### 🧬 M — nlp↔llm LLM-engine governance (NEW — P1, decision needed)
`llm_utils.py`, `vocab_manager.py`, `llm_run.py` live in **both** nlp-enrich and llm-enrich.
They are *not* under para-drift, and `llm_run.py` has already diverged (nlp's still declares
`program="nlp-enrich"` and its pre-split pipeline shape; llm-enrich's has added DU code,
`api_util/xml_to_md.py`, and the OpenRouter/Ollama remote clients through `v0.3.0`). Every
llm-enrich release widens the gap. This is a **decision**, not a mechanical fix, so it is *not*
auto-applied:

* **Recommended direction:** declare **llm-enrich canonical** for the LLM engine. It is the
  dedicated, actively-developed home; nlp-enrich's copies are legacy. Concretely — (1) stop
  describing them as "kept in sync" (they aren't); (2) in nlp-enrich, either vendor the engine
  from llm-enrich at a pinned tag or freeze its copy and mark it legacy-pipeline-only in the
  README; (3) if genuine byte-sync is ever wanted for a subset, extend `para-drift.reusable.yml`
  with a second job covering just the truly-shared files — but only *after* they are reconciled,
  or the check reddens on day one.
* **Do not** naively add the LLM files to para-drift now — they diverge, so CI would fail
  immediately. Reconcile first, or fork explicitly.
* **Status: DEFERRED (maintainer, 2026-07-22).** The engine fork stays as-is for now; revisit
  when the divergence or an OOM-parity need forces the decision.

### 🧹 P1c/P2t — Code-quality pass (NEW — LANDED this review, delivered as patches)
A source-code improvement sweep across the tool repos (patches on `claude/session-bu7f5d`,
fast lanes green, ruff clean):
* **Correctness (P1c):** alto — removed the stale duplicate `categorize_line` service fallback
  (a broken import would have served stale categorization); llm — logged the 4 silent bare
  excepts in the DU convertors; pc — tightened `service/inference.py` (narrowed types, `raise …
  from e`, `logger.exception`, logged silent ensemble skips); nlp — logged the genuinely-silent
  swallows in `run_pipeline.py`, dropped a dead `try/pass` in `keywords.py`.
* **Test gaps (P2t):** llm — added `test_llm_utils.py` + `test_llm_run.py` (the engine had none)
  + a shared `_read_image_dimensions` test; nlp — round-trip tests for the `annotation/`
  doccano↔IOB2 converters + the shared image-dims test; pc — `test_img2jpeg.py` and renamed the
  misleading `service/test_api.py` → `api_client.py`; translator — `test_bakeoff.py` locks down
  the bake-off harness plumbing (issue #4). Note: `teitok_alto.py` was already ~79% covered by
  `test_teitok_preservation.py` (a filename-heuristic false-positive), so only the uncovered
  image-header block got a targeted top-up.
* **Hygiene:** pc `.gitignore` now ignores `__pycache__` recursively (was root-anchored);
  translator design doc moved to `docs/translation-backends.md` (fixed dangling refs, plan #4).

### 📚 DOC — Documentation reality (NEW — P2)
* This file was 4 weeks and two release waves stale (it still said "Last reviewed 2026-06-24",
  omitted llm-enrich, and listed every F/G/H/I item as open). This refresh closes that.
* `10.digest.md` / `10.plan.md` refreshed on `test` (2026-07-22); `project_state_2207.md`
  replaced with the independently-corrected edition (T1/T2 already resolved by same-day
  releases; alto branch-HEAD mislabel fixed; the dangling `issue10_alignment_1307.md` citation
  dropped — that evidence file was never committed).
* **Forward-merge `test` → `main`** on the hub: `main` still lacks `project_state_2207.md` and
  the refreshed digest/plan, so default-branch readers can't see any of this. Maintainer action
  (not auto-done — `main` is not a session-designated branch).

## 🗂️ 6. Per-repository diagnostics (2026-07-22)
* **page-classification** — no open code findings; graduated. Carries the release-gate fix.
* **alto-postprocess** — F/G/H/I closed; ratchet set (50). Release-gate fix (closes the class
  that produced `v1.0.0.-beta`). No open code findings beyond the ecosystem-wide items.
* **nlp-enrich** — C4 test-swap is the only code straggler; release-gate fix (closes the class
  that produced `v1.16.2`); one half of the §5.M governance decision.
* **translator** — strongest repo; no open findings. Release-gate fix only.
* **llm-enrich** — onboarded and clean (ruff 0, own test-reqs, ratchet 42); other half of §5.M.
* **atrium-project (hub)** — first review pass. Findings so far: (a) this stale tracker [fixed];
  (b) the release-gate lives per-repo and the hub should host the future DRY reusable + a caller
  template; (c) `e2e-pipeline-smoke.yml` exists but the §8 compose scaffold (issue #18) still
  does not — fix the present-tense §8 text below.

## 🛣️ 7. Phased roadmap
* **Phase 0 — release integrity:** ✅ **DONE** — the §5.R release-gate landed on all five tool
  repos (2026-07-22); tags == CITATION == para_config by construction.
* **Phase 1 — code-quality pass:** ✅ **DONE** — §P1c correctness + §P2t test gaps (this review,
  delivered as patches). Remaining: Tier-2 clean-venv run per repo to record fresh COV baselines
  and ratchet `fail_under` upward; tick the 2026-07-16 round boxes.
* **Phase 2 — LLM-engine governance (§5.M):** ⏸️ **DEFERRED** — decide canonical home; reconcile
  or explicitly fork nlp↔llm; only then consider extending para-drift.
* **Phase 3 — ratchet & orchestrate:** raise `fail_under` toward measured baselines; build the
  §8 compose scaffold (issue #18); optional DRY `release-guard.reusable.yml`.
* **Phase 4 — blocked (documented):** gitleaks secret-scan (needs ARUB/ARUP policy sign-off +
  `GITLEAKS_LICENSE`); template exists (`secret-scan.caller.example.yml`), adopted by none.

## 🔁 8. Cross-service orchestration (Issue #18) — **still to build**
`atrium-project/compose/docker-compose.pipeline.yml` (chaining the published GHCR images
pc → alto → translator → nlp → llm over a shared `atrium_data` volume, each stage gated on the
previous via `depends_on: condition: service_completed_successfully`) **does not exist yet** —
it is issue #18 scope. `e2e-pipeline-smoke.yml` is present in the hub as the CI entry point that
will drive it once the compose file lands.

## 🛡️ 9. Drift-check — **LIVE**
`para-drift.reusable.yml` diffs each repo's `atrium_paradata.py` / `para_licenses.py` /
`tests/test_para_licenses.py` against `docs/templates/shared/*` and fails on divergence; each
repo carries a ~12-line caller. Scope boundary per §5.H / §5.M.

## 📍 10. Exact change locations (this review)
| Item                | Path                                                                    |
|---------------------|-------------------------------------------------------------------------|
| R release-gate      | `{pc,alto,nlp,translator,llm}/.github/workflows/release.yml` (+`needs`)  |
| R para_config path  | pc,alto → `setup/para_config.txt`; nlp,translator,llm → `para_config.txt`|
| I1 C4               | `nlp/tests/test_teitok_integraion.py` (subprocess `--help` → `build_parser().format_help()`) |
| M governance        | `nlp/{llm_utils,vocab_manager,llm_run}.py` ↔ `llm/{…}.py` (decision)     |
| DOC forward-merge   | hub `test` → `main` (digests, project_state_2207, this file)            |

---

# 🧪 Appendix — subprocess → in-process refactors (status)

Executed across the ecosystem; the only remaining item is nlp C4:

### C4 — nlp `summarize_nt_udp.py` + `tests/test_teitok_integraion.py`
`build_parser()` + `main(argv=None)` are **already extracted** in
`api_util/summarize_nt_udp.py`. Remaining: replace the subprocess `--help` block in the test
(the threading test below it stays):
```python
from api_util.summarize_nt_udp import build_parser

def test_cli_argparse_dpi_support():
    """summarize_nt_udp must expose --dpi and --alto-dpi."""
    help_text = build_parser().format_help()
    assert "--dpi" in help_text
    assert "--alto-dpi" in help_text
```
*(Drops `import subprocess`, the `PYTHONPATH` juggling, and the `script_path` lookup.)*

_pc `run.py` (C5) and alto `page_split.py` (C3) refactors are done; the nlp `test_api_service.py`
and `test_flexiconv_convert.py` mock-`subprocess.run` tests are correct in-process tests and were
intentionally left as-is._
