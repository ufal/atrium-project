# ATRIUM UFAL Pipeline — Unified Project State Review

**Date: 13 July 2026 · Scope: six `ufal` GitHub repositories**

_Supersedes `project_state_2706.md` (27 June 2026). Mutable facts below (versions, releases, CI,
issues, validation results) were re-verified this cycle against the live `test`-branch checkouts
(HEADs of 2026-07-12/13), GitHub releases/Actions, and the repos' `gh2md` issue exports; the
detailed evidence base is `digests/issue10_alignment_1307.md`. Stable context (institutional
framing, model benchmarks, score formulation) is carried forward from the 27-06 review._

---

## 1. Institutional Context and Project Genesis

**ATRIUM** ("Advancing fronTier Research In the arts and hUManities") is a Horizon Europe project
(Grant No. 101132163, January 2024–December 2027), coordinated by DARIAH, bridging four European
research infrastructures: DARIAH, ARIADNE, CLARIN, and OPERAS. 29 partners across 14 countries.

UFAL's (Charles University, Institute of Formal and Applied Linguistics) mandate is the technical
NLP/OCR pipeline for Czech archaeological archival documents sourced primarily from the Institutes
of Archaeology of the Czech Academy of Sciences in Prague (ARÚP) and Brno (ARÚB): over 1.2 million
legacy archival pages from the 1920s onward — typewritten excavation reports, handwritten field
notes, site photographs, stratigraphy drawings.

The objective is to transform these static repositories into FAIR-aligned data objects that can be
queried, translated, and linguistically analysed at scale. A March 2026 project presentation is
archived on Zenodo (`zenodo.org/records/19500212`); the CAA 2026 proceedings paper ("From Relics
to Active Data") at `zenodo.org/records/20813374`.

---

## 2. The Meaning-Making Pipeline

Five tool stages now map to five product repositories (the LLM stage was spun out of nlp-enrich
this cycle — see §8):

```
Raw scan images
      │
      ▼
[Phase A]   Structural Perception      atrium-page-classification
      │     ViT/CNN → 11 content categories → routing decision
      ▼
[Phase B/C] Deserialization + Quality  atrium-alto-postprocess
      │     ALTO XML → page split → text extraction → line-level
      │     quality scoring → Clear / Noisy / Trash / Non-text / Empty
      ▼
[Phase D.1] Protected Translation      atrium-translator
      │     LINDAT NMT + Tag-and-Protect → English ALTO/XML
      │     with preserved bounding-box geometry
      ▼
[Phase D.2] NLP Enrichment             atrium-nlp-enrich
      │     NER (NameTag 3 multilingual) + morphosyntax (UDPipe 2)
      │     + keywords → TEITOK XML
      ▼
[Phase D.3] LLM Semantic Enrichment    atrium-llm-enrich   ← NEW this cycle
            local (transformers / vLLM) or remote (OpenRouter / Ollama)
            → TEATER/AMCR vocabulary mapping, CZ/EN keyword pairs,
            thematic category + confidence
```

Each stage explicitly annotates *provenance* and *uncertainty* rather than silently discarding
ambiguous content.

---

## 3. Distributed Repository Architecture

Six repositories under `github.com/ufal` — intentionally **not** a monorepo and **not**
git-submodules; execution environments have incompatible dependency graphs.

| Repository                        | Role                                       | Default branch | Version (CITATION) | Latest release       |
|:-----------------------------------|:--------------------------------------------|:--------------:|:-------------------:|:---------------------|
| `ufal/atrium-project`             | Planning hub, templates, reusable CI       |     `main`     |          —          | —                    |
| `ufal/atrium-page-classification` | Visual triage / CNN-ViT classifier         |     `vit`      |    `1.5.1-beta`     | v1.5.1-beta · 07-12  |
| `ufal/atrium-alto-postprocess`    | OCR quality control, line categorisation   |    `master`    |      `0.20.2`       | v0.20.2 · 07-12      |
| `ufal/atrium-translator`          | XML/ALTO in-place translation              |    `master`    |       `0.8.1`       | v0.8.1 · 07-12       |
| `ufal/atrium-nlp-enrich`          | NER, morphosyntax, keywords, TEITOK        |    `master`    |      `0.16.1`       | v0.16.0 · 06-28 ⚠️   |
| `ufal/atrium-llm-enrich`          | LLM semantic enrichment (local + remote)   |     `main`     |       `0.1.0`       | none yet ⚠️          |

⚠️ nlp code is one patch ahead of its latest tag (recurring pattern); llm-enrich is pre-release
(22 commits since ~2026-07-01). Releases are cut automatically by the shared `release.yml` caller.

Primary engineering maintainer: **K4TEL** (`lutsai.k@gmail.com`); dissemination/publication:
**motyc**. Planning coordinated via the org Project board (`github.com/orgs/ufal/projects/21`).

**Common conventions (all product repos, verified this cycle):** MIT code licence, CC BY-NC 4.0
paradata logs, `CITATION.cff`, `CONTRIBUTING.md`, `[SECTION]`-style `config*.txt`, `tests/` +
`pytest.ini` (`slow` marker splits the fast lane from model/GPU/network tests), root `ruff.toml`
(hub template as floor, documented per-repo supersets), `agent_dev_logs/` on the `test` branch
(DEVLOG, issue exports, digests, plans) as the primary agentic work surface.

### CI/CD federation (expanded this cycle)

Every product repo calls the hub's reusable workflows pinned `@test` and now carries the full
caller set — verified identical across all five:

- `security.yml` → `security.reusable.yml` (version consistency vs. CITATION/tag)
- `docker.yml` → `docker-tool.reusable.yml` — image build **plus the CI fast test lane**
  (`pytest -m "not slow" --cov`, `docker-tool.reusable.yml:84`)
- `para-drift.yml` → `para-drift.reusable.yml` — **new**: strict `diff` of the shared
  `atrium_paradata.py` / `para_licenses.py` / `tests/test_para_licenses.py` against the hub
  canonical (`docs/templates/shared/*`); fails on any divergence
- `codeql.yml`, `pre-commit.yml` (ruff advisory `--fix` + shellcheck), `release.yml`,
  `scheduled-smoke.yml` (`pytest -m slow`, model-cache aware)
- `gpu-inference.yml` on `runs-on: [self-hosted, gpu]` — pc, nlp, llm-enrich (the June review
  listed GPU CI as blocked; the self-hosted runner unblocked it)
- `shellcheck.yml` — nlp only; green since 2026-06-22 (latest run 2026-07-12 `success`)

Secret scanning: hub template ready (`docs/templates/workflows/secret-scan.caller.example.yml`,
gitleaks-action v3 + `GITLEAKS_LICENSE` note) but adopted by no repo — pending ARUB/ARUP policy
sign-off.

---

## 4. Phase A — Structural Perception: Page Classification

**Repository:** `ufal/atrium-page-classification` · MIT · `vit` branch · v1.5.1-beta

### Function

Fine-tuned ViT / RegNetY / EfficientNetV2 / DiT / CLIP models classify each scan into one of
**11 content categories** (`DRAW`, `DRAW_L`, `LINE_HW`, `LINE_P`, `LINE_T`, `PHOTO`, `PHOTO_L`,
`TEXT`, `TEXT_HW`, `TEXT_P`, `TEXT_T`), routing pages to the appropriate downstream track
(`PHOTO` bypasses OCR; `TEXT_HW` → HTR; `TEXT_T` → typed OCR).

### Model state (vX.3 annotation phase baseline)

| Model         | Variant                             |      Top-1 |  Top-3 | Notes                                    |
|:---------------|:-------------------------------------|-----------:|-------:|:------------------------------------------|
| CNN (RegNetY) | `regnety_160.swag_ft_in1k` v4.3     | **99.16%** | 100.0% | Production default; parameter-efficient  |
| ViT           | `vit-large-patch16-384` v5.3        |     99.12% |      — | High-accuracy alternative                |
| Ensemble      | Mean-of-softmax across top-5 models |     ~99.9% |      — | `--best` flag                            |

Training data: 48,499 PNG images / 37,328 documents, CC BY-NC-SA 4.0, LINDAT
(`hdl.handle.net/20.500.12800/1-5959`); weights on HF `ufal/vit-historical-page`.
`--parallel` activates memory-aware GPU scheduling.

### Engineering state (verified 13-07)

`run.py` was refactored this cycle: heavy imports (numpy/pandas/sklearn/torch chain) deferred
into `main()`, `build_parser()`/`main(argv)` extracted (`run.py:825/:978`) — `import run` is now
dependency-free, and the former subprocess smoke tests run in-process. Fast lane: **251 passed,
6 skipped in 10.5 s** from `setup/requirements-test.txt` (torch-dependent modules self-guard via
`importorskip`). Ruff: 0 findings. API version served from `para_config.txt` via
`_read_tool_version()` (`service/api.py:28`).

### Open issues (2)

| #     | Title                                                                       | Opened     |
|:------|:------------------------------------------------------------------------------|:-----------|
| `#15` | Retrain 5 best models on the new dataset with N-318 pages                    | 2026-06-25 |
| `#26` | Agent-skill branch for page classifier prediction (uwebasr-skill pattern)    | 2026-07-12 |

Accuracy is near-ceiling; work is integration- and deployment-oriented.

---

## 5. Phase B/C — ALTO Post-Processing and Line Categorisation

**Repository:** `ufal/atrium-alto-postprocess` · MIT · `master` · v0.20.2 ·
**Most open issues of any product repo; conceptual heart of OCR quality control.**

### Pipeline stages

1. `page_split.py` — document-level ALTO → per-page files (now with `main(argv)` in-process CLI)
2. `alto_stats_create.py` — per-page stats CSV via `alto-tools`
3. Text extraction, three backends by document complexity: **LayoutReader** (GPU, reading-order
   recovery), **alto-tools** (CPU fallback), **GLM-4v-9b** (GPU `gpuram48G`, generative OCR)
4. `langID_classify.py` — line-level quality + language classification
5. `langID_aggregate_STAT.py` — page-level aggregation

Tunables in `config_langID.txt` under `[CLASSIFY]` / `[AGGREGATE]` / `[TEXT_UTILS]`.

### Composite quality score (unchanged mechanism)

Every line receives Q_s ∈ [0, 1] as a weighted sum of normalised signals — valid-word fraction
(0.25), garbage density (0.20, `f(x) = min(x / 0.35, 1)`), inverted LM perplexity (0.15,
Qwen2.5-0.5B GPU worker, capped), word-weirdness (0.13), symbol density (0.13) — with a boolean
`penalty_inverted` override (rotatable-char ≥ 0.55 ∧ weird ≥ 0.35 ∧ PPL ≥ 200) and a page-level
inverted-scan sweep. Categories: **Trash** (< 0.50), **Noisy** (0.50–0.90, rolling-window
smoothing + clean-prose promotion), **Clear** (≥ 0.90), **Non-text/Empty** (structural regex /
length / alpha-ratio gates). CPU fleet (≤ 32 workers) + single GPU perplexity worker over a
shared queue.

### Engineering state (verified 13-07)

Fast lane: **350 passed, 3 skipped in 8.3 s** — but `requirements-test.txt` under-declares
(pytest/pytest-cov only; clean venv hits 13 collection errors on missing pandas/lxml — the one
open Thread-G straggler among the original four repos). Ruff: 0 findings (documented "B"-rules
superset over the hub template). `text_api.py:44` serves the config-derived version.

### Open issues (5 — calibration cluster)

| #    | Title                                                                     | Opened     |
|:-----|:----------------------------------------------------------------------------|:-----------|
| `#6` | Add starting points to the pipeline run script (resumability)              | 2026-06-24 |
| `#5` | Surrogate-model parameter importance for config constants                  | 2026-06-24 |
| `#4` | Documentation of the categorisation logic                                  | 2026-05-28 |
| `#3` | Calibration of categorisation logic against extracted-string parameters    | 2026-04-17 |
| `#2` | Update definition of text categories and assignment logic                  | 2026-03-13 |

`#5` (surrogate modelling of the ~30-constant space — RF/GP/SVM/XGBoost, fANOVA/Shapley/LPI)
remains the right mechanism to tame this configuration space; `#4` documentation is a publication
prerequisite (hub #13/#15).

---

## 6. Phase D.1 — Protected Translation

**Repository:** `ufal/atrium-translator` · MIT · `master` · v0.8.1 ·
**Most production-ready product; strongest test suite.**

### Function

Python wrapper around the LINDAT Translation API restricted to XML and derivatives: `--alto`
(ALTO in-place) and `--xpaths` (XML metadata — AMCR/OAI-PMH/any schema). FastText language
detection (per-`TextBlock` in ALTO mode; Czech fallback below 0.2 confidence in metadata mode).

### Tag-and-Protect controlled vocabulary (unchanged mechanism)

1. `load_vocab.py` harvests CZ→EN pairs from AMCR OAI-PMH + the TEATER GraphQL thesaurus
   (~12 domain hierarchies).
2. Sentinel substitution (`Xtermzzz<N>z`), longest-substring phrase matching, UDPipe
   lemmatisation with number-agreement guard.
3. NMT translates prose; sentinels pass through.
4. Reverse-lookup restoration to TEATER target-language equivalents.

ALTO spatial reconstruction: block pass for quality + per-line re-anchoring via
`difflib.SequenceMatcher` (±50 % window); XSD validation (e.g. `amcr.xsd`); sentence-aware
4,000-char chunking.

### Engineering state (verified 13-07)

Fast lane: **303 passed in 4.5 s**, fully self-contained (`requirements.txt` +
`requirements-test.txt`) — the reference implementation of the Thread-G goal. `load_vocab` went
from 0 % coverage (June finding) to a dedicated 35-test module (`tests/test_load_vocab.py`).
Ruff: 0 findings. 16-file test suite spanning alignment, backends (incl. CT2 and LLM),
content preservation, edge cases, paradata.

### Open issues (1)

| #    | Title                         | Opened     |
|:-----|:--------------------------------|:-----------|
| `#4` | Translation base model to use | 2026-06-20 |

---

## 7. Phase D.2 — NLP Enrichment and TEITOK Output

**Repository:** `ufal/atrium-nlp-enrich` · MIT · `master` · v0.16.1 (code) / v0.16.0 (release)

### Core pipeline

```
api_1_manifest.sh
    → api_2_udp.sh      UDPipe 2 (czech-pdt-ud-2.15) · 900-word chunking
                        with page-break injection → CoNLL-U
    → api_3_nt.sh       NameTag 3 — multilingual base model (onto tagset)
                        since v0.16.0, replacing the Czech-only CNEC default
    → api_4_stats.sh    Merge to TEITOK XML · ALTO bbox alignment
                        (difflib, autojunk=False) · per-page PNG scaling
                        → summary_ne_counts.csv
```

TEITOK XML connects bounding-box coordinates to POS metadata and translated semantics — queries
for *where* a term sits on a page and *how* it functions syntactically. Extra modules: keyword
extraction (KER / YAKE / KeyBERT via `kw_config.txt`), `flexiconv` adapter (PAGE XML / hOCR /
plain text), `/rescale` API entry point (since v0.14.3).

### Engineering state (verified 13-07)

Fast lane: **236 passed, 4 skipped in 1.7 s**; `tests/test_llm_utils.py` guards the torch chain
with `importorskip`. Ruff: 0 findings; pre-commit ruff is advisory (`--fix`), matching the
ecosystem policy. Shellcheck CI green since 2026-06-22. Remaining test-quality item: the
subprocess `--help` block in `tests/test_teitok_integraion.py` (extract `build_parser()` from
`api_util/summarize_nt_udp.py`). Note: the local-LLM modules (`llm_run.py`, `llm_utils.py`,
`vocab_manager.py`) still live here as the twin of the new llm-enrich repo — see §8 governance.

### Open issues (5)

| #     | Title                                                              | Opened     |
|:------|:---------------------------------------------------------------------|:-----------|
| `#10` | Add flexiconv-supported input options (any text-containing format) | 2026-05-28 |
| `#9`  | TEITOK output: image-files dependence handling                     | 2026-05-28 |
| `#8`  | Add API service wrapper                                            | 2026-05-28 |
| `#7`  | Domain-specific NameTag model training (Czech archaeology)         | 2026-05-11 |
| `#6`  | LLM keyword extraction from TEATER vocabulary                      | 2026-04-17 |

(`#11` NameTag3 multilingual — closed by v0.16.0 this cycle.)

---

## 8. Phase D.3 — LLM Semantic Enrichment ← NEW REPOSITORY

**Repository:** `ufal/atrium-llm-enrich` · MIT · `main` · v0.1.0 (unreleased) · 22 commits ·
created ~2026-07-01, spun out of nlp-enrich per hub issue **#24** ("LLM applications to data").

### Function

Runs an LLM over digitized archival text — locally or as a service — mapping each line or
document onto the controlled TEATER/AMCR archaeological vocabulary: Czech/English keyword pairs
plus a thematic category with confidence score.

### Backends

| Backend                        | Scale / use                                                    |
|:--------------------------------|:-----------------------------------------------------------------|
| `transformers` + BnB 4-bit     | single-GPU, up to ~31B params                                  |
| `vLLM` + xgrammar              | multi-GPU (tensor-parallel 8), Automatic Prefix Caching, ≥70B  |
| OpenRouter (`openrouter_client.py`) | remote inference — **new** capability vs. the nlp-era stack |
| Ollama (`ollama_client.py`)    | lightweight local — **new**                                    |

`llm_client_shared.py` lets the remote/lightweight backends share logic with the local engine
**without importing torch**. Design principles carried over: targeted vocabulary injection via
embedding similarity, sliding context window respecting page boundaries, token logit masking for
JSON schema conformance, abort sidecar after 10 consecutive inference errors. Default model
lineage (Qwen 2.5 Instruct family preferred; evaluation graveyard in nlp-enrich #6) unchanged.

### Governance note (the cycle's main structural risk)

The engine files are **deliberate copies** of nlp-enrich's (README: "kept deliberately in sync
rather than cross-repo-refactored"). Verified 13-07: `llm_utils.py` / `vocab_manager.py` are
byte-identical twins, but **`llm_run.py` has already diverged**, and none of these are covered by
the `para-drift` check that enforces the paradata trio. Either extend the drift check or declare
one repo canonical before divergence compounds — this is P1 in the issue-#10 plan.

### Engineering state (verified 13-07)

Wired into all shared conventions (full CI caller set incl. para-drift and gpu-inference;
paradata trio byte-identical to hub canonical; `para_config` == CITATION). Gaps: **no
`requirements-test.txt`** (83 fast tests pass only in a pre-provisioned venv), **3 ruff
findings** (`eval_metrics.py:144` B905 + W292 ×2 — the only findings in the ecosystem), no
tagged release yet.

### Open issues (1)

| #    | Title                                                | Opened     |
|:-----|:--------------------------------------------------------|:-----------|
| `#8` | LLM applications to data — initialization of repository | 2026-07-12 |

---

## 9. Cross-Cutting Architecture

### Shared provenance (paradata)

Every product repo ships `atrium_paradata.py` (schema v2.0, 598 lines): cryptographic `run_id`,
tool/repo identity, UTC timestamps, config snapshot, line-level execution faults, and the
**computed effective licence** resolved by `para_licenses.py` from component→licence maps in
`para_config.txt`. Output to `<OUTPUT_DIR>/paradata/`. Flat JSON by design (no PROV-O/CIDOC-CRM
overhead at 1.2 M-page scale).

**New this cycle — "canonical drop-in + CI drift-check" is fully operational:** the hub holds
canonical copies under `docs/templates/shared/` (`atrium_paradata.py`, `para_licenses.py`,
`test_para_licenses.py`); all five product repos carry byte-identical copies (sha256-verified)
and a `para-drift.yml` CI caller that fails on divergence. The June review's "copy-pasted and
diverged" finding is closed; the licence-resolution engine went from zero tests to a shared
suite present in every repo.

### Validation matrix (re-run 13-07, local)

| Repo               | compileall | ruff        | fast lane (`-m "not slow"`)   | self-contained deps                    |
|:--------------------|:----------:|:------------:|:-------------------------------|:-----------------------------------------|
| page-classification | OK         | 0 findings  | 251 ✅ / 6 skip / 10.5 s       | ✅ `setup/requirements-test.txt`         |
| alto-postprocess    | OK         | 0 findings  | 350 ✅ / 3 skip / 8.3 s        | ❌ pandas, lxml undeclared               |
| nlp-enrich          | OK         | 0 findings  | 236 ✅ / 4 skip / 1.7 s        | ✅                                       |
| translator          | OK         | 0 findings  | 303 ✅ / 4.5 s                 | ✅                                       |
| llm-enrich          | OK         | 3 findings  | 83 ✅ / 0.3 s                  | ❌ no `requirements-test.txt`            |
| project (hub)       | OK         | clean       | —                              | —                                        |

Coverage gates (`fail_under`) remain unset ecosystem-wide (alto `.coveragerc:14` commented out) —
the next ratchet once fast-lane baselines are recorded.

---

## 10. Active Work-Package Milestones

| Milestone                                                              | Scope                                                  | Status                        |
|:-------------------------------------------------------------------------|:----------------------------------------------------------|:---------------------------------|
| **Q1-Q2 \[WP4/WP5\]** Mid-Project Workflow Beta Testing & Integration  | Bulk of open engineering and dissemination work        | **Current centre of gravity** |
| **Q3 \[WP8/WP7\]** Advanced Transnational Access & Curriculum Drafting | Document understanding evaluation, domain NER training | Upcoming                      |
| **Q4 \[WP3\]** Conclusion of Semantic Harmonisation                    | LLM applications, multi-GPU scaling, H100 deployment   | Started early — llm-enrich (#24) is Q4 work pulled forward |
| **CAA Proceedings**                                                    | PCJ submission #13                                     | Active                        |

---

## 11. `ufal/atrium-project` — Hub Open Issues (14)

| #     | Title                                                                       | Milestone  | Owner |
|:------|:-------------------------------------------------------------------------------|:-----------|:------|
| `#27` | H100 node — running models on multiple GPUs                                 | Q4 WP3     | K4TEL |
| `#26` | Running models larger than GPU memory (CPU offload) — **BLOCKED**           | Q4 WP3     | K4TEL |
| `#24` | LLM applications to data (*big one*) — spawned `atrium-llm-enrich`          | Q4 WP3     | K4TEL |
| `#22` | Document Understanding — evaluation of out-of-the-box tools (*big one*)     | Q3 WP8/WP7 | K4TEL |
| `#21` | LINDAT: Annotated dataset release                                           | Q1-Q2      | K4TEL |
| `#18` | Docker composer + GH Action wrapper for CU repo forks (*big one*)           | Q1-Q2      | motyc |
| `#17` | Review workflow descriptions in SSHOMP                                      | Q1-Q2      | motyc |
| `#16` | List all current storage locations of ARÚP/B data (*big one*)               | Q1-Q2      | motyc |
| `#15` | Submission to IJDL (*big one*)                                              | Q1-Q2      | motyc |
| `#13` | CAA Proceedings paper submission to PCJ                                     | CAA        | K4TEL |
| `#10` | LLM validation of source code (*big one*) — audit + doc refresh this cycle  | Q1-Q2      | K4TEL |
| `#9`  | Paradata of outputs — origin of the paradata workstream (*big one*)         | Q1-Q2      | K4TEL |
| `#6`  | Review and summarise licences for tools + models (*big one*)                | Q1-Q2      | K4TEL |
| `#4`  | SSH Open Marketplace records for all tools                                  | Q1-Q2      | motyc |

---

## 12. Key Bottlenecks and Risk Areas

**Hardware / LLM inference** — still the most pronounced bottleneck. Hub #26 (CPU offload)
remains **blocked**; PCIe (~100 GB/s) vs. GPU HBM (~2–3 TB/s) makes naive offload an order of
magnitude too slow. Near-term path: vLLM `cpu_offload_gb` + UVA backend (single-GPU nodes);
tensor-parallel 8 on the H100 node for ≥70B (hub #27). Partial mitigation shipped this cycle:
llm-enrich's **OpenRouter remote backend** sidesteps local VRAM for suitable workloads (subject
to data-sovereignty constraints per document class).

**Untracked LLM-module duplication (new)** — nlp-enrich ↔ llm-enrich twins sit outside the
para-drift enforcement; `llm_run.py` has already diverged. The para_licenses history shows how
this failure mode plays out if unmanaged.

**Calibration debt in alto-postprocess** — ~30 hand-set constants; issues #2–#5, with #5
(surrogate-model importance) as the lever.

**Documentation lag** — execution now outpaces the planning documents (the June state review
went stale within two weeks; nlp Shellcheck was reported RED after it had gone green).
Alto #4 and hub #17 remain publication prerequisites for #15/#13.

**`test`-branch visibility** — `agent_dev_logs/` (DEVLOG, digests, plans, issue exports) lives
only on `test` branches; agents working from default branches lack this context.

---

## 13. Priority Action Map

Ordered by blocking impact (aligned with the refreshed issue-#10 plan):

1. **Onboard llm-enrich to the review cycle** — `requirements-test.txt`, fix 3 ruff findings,
   add to `docs/plan_repo_review.md` scope, first tagged release.
2. **Decide LLM-module governance** (nlp ↔ llm twins): extend para-drift or declare a canonical
   home — before divergence compounds.
3. **Hub #18** — pipeline compose / GH-Action wrapper: the cross-repo
   `docker-compose.pipeline.yml` scaffold described in June still does not exist; prerequisite
   for the Q1-Q2 integration milestone and any end-to-end smoke test.
4. **Close the last Thread-G/I1 stragglers** — alto test-dep declarations; nlp
   `summarize_nt_udp` `build_parser()`; then ratchet `fail_under` from measured baselines.
5. **Alto #5 → #3 → #2/#4** — surrogate-model calibration feeding the categorisation-logic
   documentation; unblocks IJDL (#15) and PCJ/CAA (#13).
6. **Hub #26/#27** — CPU offload + H100 multi-GPU for Q4 scaling.

---

## 14. Suggested New Issues

Carried forward from 27-06 (still uncovered) plus one new gap:

1. **`atrium-project` — end-to-end integration smoke test** `[Feature]`: single-page fixture
   through pc → alto → translate → nlp → llm → TEITOK in CI; catches cross-repo interface
   breakage. Prerequisite: #18. Milestone: Q1-Q2.
2. **`atrium-nlp-enrich` — TEITOK output XML schema validation** `[Task]`: translator validates
   against XSD; nlp-enrich still has no equivalent gate at the end of `api_4_stats.sh`.
   Milestone: Q1-Q2.
3. **NEW: `atrium-project` — LLM-module drift check** `[Task]`: extend `para-drift.reusable.yml`
   (or add a sibling) to cover the nlp ↔ llm shared engine files, per the §8 governance decision.
   Milestone: Q1-Q2.

---

## 15. Test Branch State (13 July 2026)

Remote `refs/heads/test` HEADs, verified via `git ls-remote` this cycle:

| Repository                        | `test` HEAD | Last commit message                             | Date       |
|:-----------------------------------|:------------|:---------------------------------------------------|:-----------|
| `ufal/atrium-project`             | `eeebe0c`   | "docs DEVLOG update and issue logs update"      | 2026-07-12 |
| `ufal/atrium-page-classification` | `41b96c2`   | "fix formatting"                                | 2026-07-12 |
| `ufal/atrium-alto-postprocess`    | `ebfc2e7`   | "update page split and its test - LLM review"   | 2026-07-13 |
| `ufal/atrium-nlp-enrich`          | `30f6c02`   | "update issue logs and docs DEVLOG"             | 2026-07-12 |
| `ufal/atrium-translator`          | `a342dd7`   | "update vocab load test"                        | 2026-07-13 |
| `ufal/atrium-llm-enrich`          | `6201785`   | "docs update DEVLOG"                            | 2026-07-12 |

---

## Appendix: Key External References

| Resource                        | URI                                     |
|:----------------------------------|:--------------------------------------------|
| CORDIS project fact sheet       | `cordis.europa.eu/project/id/101132163` |
| ATRIUM project site             | `atrium-research.eu`                    |
| CAA proceedings paper (Zenodo)  | `zenodo.org/records/20813374`           |
| March 2026 project presentation | `zenodo.org/records/19500212`           |
| LINDAT annotation dataset       | `hdl.handle.net/20.500.12800/1-5959`    |
| HuggingFace fine-tuned weights  | `hf.co/ufal/vit-historical-page`        |
| TEATER thesaurus                | `teater.aiscr.cz`                       |
| AMCR XSD schema                 | `api.aiscr.cz/schema/amcr/2.2/amcr.xsd` |
| Org Project board               | `github.com/orgs/ufal/projects/21`      |
