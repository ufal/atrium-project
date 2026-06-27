# ATRIUM UFAL Pipeline — Unified Project State Review

**Date: 27 June 2026 · Scope: five `ufal` GitHub repositories**

---

## 1. Institutional Context and Project Genesis

**ATRIUM** ("Advancing fronTier Research In the arts and hUManities") is a Horizon Europe project
(Grant No. 101132163, January 2024–December 2027), coordinated by DARIAH, bridging four European
research infrastructures: DARIAH, ARIADNE, CLARIN, and OPERAS. 29 partners across 14 countries.

UFAL's (Charles University, Institute of Formal and Applied Linguistics) mandate is the technical
NLP/OCR pipeline for Czech archaeological archival documents sourced primarily from the Institutes
of Archaeology of the Czech Academy of Sciences in Prague (ARÚP) and Brno (ARÚB). The collection
spans over 1.2 million legacy archival pages dating from the 1920s: typewritten excavation reports,
handwritten field notes, site photographs, and stratigraphy drawings.

The objective is to transform these static repositories into FAIR-aligned (Findable, Accessible,
Interoperable, Reusable) data objects that can be queried, translated, and linguistically analysed
at scale — reframing cultural artifacts as computationally active datasets rather than digitised images.

A March 2026 project presentation is archived on Zenodo (`zenodo.org/records/19500212`). The CAA 2026
proceedings paper ("From Relics to Active Data") is archived at `zenodo.org/records/20813374`.

---

## 2. The Meaning-Making Pipeline

The pipeline is the project's central conceptual framework: a four-stage automated workflow that
transitions raw archival scans into structured, linguistically enriched datasets. Each stage maps
to a dedicated repository.

```
Raw scan images
      │
      ▼
[Phase A] Structural Perception       atrium-page-classification
      │   ViT/CNN → 11 content categories → routing decision
      │
      ▼
[Phase B] Deserialization + Quality   atrium-alto-postprocess
      │   ALTO XML → page split → text extraction → line-level
      │   quality scoring → Clear / Noisy / Trash / Non-text / Empty
      │
      ▼
[Phase D.1] Protected Translation     atrium-translator
      │   LINDAT NMT + Tag-and-Protect → English ALTO/XML
      │   with preserved bounding-box geometry
      │
      ▼
[Phase D.2] NLP Enrichment            atrium-nlp-enrich
          NER (NameTag 3) + morphosyntax (UDPipe 2) + keywords +
          local-LLM vocabulary mapping → TEITOK XML
```

The philosophical premise is that historical data gains meaning only when connected to modern
linguistic and structural ontologies; hence each stage explicitly annotates *provenance* and
*uncertainty* rather than silently discarding ambiguous content.

---

## 3. Distributed Repository Architecture

The project intentionally avoids a monorepo. The five repositories under `github.com/ufal` serve
distinct execution environments with incompatible dependency graphs (PyTorch vision models, CPU-bound
heuristic regex, GPU-bound LLM inference cannot coexist cleanly in a single package).

| Repository                        | Role                                      | Default branch |      Commits | Stars / Forks |
|:----------------------------------|:------------------------------------------|:--------------:|-------------:|:-------------:|
| `ufal/atrium-project`             | Planning hub, cross-repo tracker          |     `main`     |            6 |       —       |
| `ufal/atrium-page-classification` | Visual triage / CNN-ViT classifier        |     `vit`      |          266 |     5 / 2     |
| `ufal/atrium-alto-postprocess`    | OCR quality control, line categorisation  |    `master`    |          193 |     2 / 2     |
| `ufal/atrium-translator`          | XML/ALTO in-place translation             |    `master`    | 68 · 12 tags |     — / 2     |
| `ufal/atrium-nlp-enrich`          | NER, morphosyntax, LLM enrichment, TEITOK |    `master`    |          133 |     — / 2     |

All five repos were updated on 26–27 June 2026. Primary engineering maintainer: **K4TEL**
(`lutsai.k@gmail.com`); dissemination/publication: **motyc**.

**Common conventions across all repos:** MIT code licence, CC BY-NC 4.0 for paradata logs,
`CITATION.cff`, `CONTRIBUTING.md`, `[SECTION]`-style `config*.txt`, `tests/` + `pytest.ini` test suite.

**CI/CD:** All repos use reusable GitHub Actions workflows pinned to `@test`. The `agent_dev_logs/`
directory (DEVLOG timeline and issue digests) lives on the `test` branch of each repo — **not on
default branches** — and is the primary agentic work surface.

**Planning:** Coordinated via the org Project board (`github.com/orgs/ufal/projects/21`).

---

## 4. Phase A — Structural Perception: Page Classification

**Repository:** `ufal/atrium-page-classification` · 266 commits · MIT · 5 ★ · `vit` branch

### Function

Applies fine-tuned ViT / RegNetY / EfficientNetV2 / DiT / CLIP models to classify each incoming
scan into one of **11 content categories**: `DRAW`, `DRAW_L`, `LINE_HW`, `LINE_P`, `LINE_T`,
`PHOTO`, `PHOTO_L`, `TEXT`, `TEXT_HW`, `TEXT_P`, `TEXT_T`.

This triage prevents downstream processing waste: `PHOTO` pages bypass OCR entirely; `TEXT_HW`
routes to specialised HTR services; `TEXT_T` proceeds to typed OCR.

### Current Model State

| Model         | Variant                             |      Top-1 |  Top-3 | Notes                                   |
|:--------------|:------------------------------------|-----------:|-------:|:----------------------------------------|
| CNN (RegNetY) | `regnety_160.swag_ft_in1k` v4.3     | **99.16%** | 100.0% | Production default; parameter-efficient |
| ViT           | `vit-large-patch16-384` v5.3        |     99.12% |      — | Retained as high-accuracy alternative   |
| Ensemble      | Mean-of-softmax across top-5 models |     ~99.9% |      — | Triggered via `--best` flag             |

Training dataset (vX.3 annotation phase): **48,499 PNG images from 37,328 archival documents**,
CC BY-NC-SA 4.0, on LINDAT (`hdl.handle.net/20.500.12800/1-5959`). Fine-tuned weights on Hugging
Face: `ufal/vit-historical-page`. Split strategy: deterministic periodic sampling, 10% test ratio,
5-fold cross-validation.

Latest benchmark artefacts: `20260530-1234_BEST_5_models_TOP-1.csv` and
`20260613-1002_BEST_5_models_TOP-1.csv`.

`--parallel` flag activates memory-aware GPU scheduling for batch runs.

### Open Issues (1)

- 1 open issue (specifics not enumerated this cycle). Accuracy is near-ceiling; future work is
  integration- and deployment-oriented (ensemble ergonomics) rather than modelling.

---

## 5. Phase B/C — ALTO Post-Processing and Line Categorisation

**Repository:** `ufal/atrium-alto-postprocess` · 193 commits · MIT · 2 ★ · **Most open issues
of any product repo; conceptual heart of OCR quality control.**

### 5.1 Pipeline Stages

1. **`page_split.py`** — splits document-level ALTO XML into per-page files (prevents memory overflow on large documents)
2. **`alto_stats_create.py`** — builds per-page stats CSV via `alto-tools`
3. **Text extraction** — three backends, selected by document complexity:
   - **LayoutReader** (GPU, 1st choice) — spatial reading-order recovery, hyphenation repair
   - **alto-tools** (CPU, fast fallback)
   - **GLM-4v-9b** (GPU `gpuram48G`, generative OCR for complex layouts)
4. **`langID_classify.py`** — line-level quality + language classification (see §5.2)
5. **`langID_aggregate_STAT.py`** — page-level aggregation of line scores

All tunables live in `config_langID.txt` under `[CLASSIFY]` / `[AGGREGATE]` / `[TEXT_UTILS]`.

### 5.2 Composite Quality Score

Reading-order extraction must address multi-column layouts, stamped annotations, overlapping
marginalia, and inserted tables before scoring can proceed.

#### Score Formulation

Every line receives a **composite quality score** Q_s ∈ [0, 1]:

```
Q_s = Σᵢ wᵢ · fᵢ(xᵢ)
```

where `fᵢ(xᵢ)` normalises each raw signal `xᵢ` to [0, 1] before the weighted sum. Key weights
(from `config_langID.txt [CLASSIFY]`):

| Constant               | Weight | Signal                                  |
|:-----------------------|-------:|:----------------------------------------|
| `QS_WEIGHT_VALID_WORD` |   0.25 | Fraction of recognisable language words |
| `QS_WEIGHT_GARBAGE`    |   0.20 | Non-alphanumeric character density      |
| `QS_WEIGHT_PERPLEXITY` |   0.15 | LM uncertainty (inverted normalised)    |
| `QS_WEIGHT_WEIRD`      |   0.13 | Inverted word-weirdness ratio           |
| `QS_WEIGHT_SYMBOL`     |   0.13 | Inverted symbol density                 |

The garbage-density normalisation applies: `f_garbage(x) = min(x / CATEG_GARBAGE_DENSITY_HIGH, 1)`,
where `CATEG_GARBAGE_DENSITY_HIGH = 0.35` — a 35% non-alphanumeric threshold triggers maximum penalty.

Perplexity (computed by **Qwen2.5-0.5B**, the dedicated GPU worker) is capped before normalisation:
`SHORT_PPL_CAP = 850.0` for Qwen (with a wider alternative cap of 1500–2500 depending on tuning
profile); `SHORT_PPL_CAP = 2500.0` for `distilgpt2` (English-only collections). Raw perplexity
beyond the cap is clipped to prevent OCR errors from dominating clean lines nearby.

#### Boolean Penalty: Inverted-Scan Detection

A boolean penalty override `penalty_inverted` fires if **all three** conditions hold simultaneously,
invalidating the line's score entirely regardless of Q_s:

```
ROT_RATIO_INVERTED_MIN  = 0.55   (rotatable-character ratio)
WEIRD_RATIO_INVERTED_MIN = 0.35  (word-weirdness ratio)
PPL_INVERTED_MIN         = 200.0 (LM perplexity)
```

A page-level inverted-scan sweep is applied in post-processing smoothing in addition to the
per-line check.

#### Line Categories

| Category             | Threshold                                   | Handling                                                                                                                                                                                  |
|:---------------------|:--------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Trash**            | Q_s < `CATEG_TRASH_SCORE_MAX` = 0.50        | Suppressed; flagged for manual recovery                                                                                                                                                   |
| **Noisy**            | 0.50 ≤ Q_s < `CATEG_NOISY_SCORE_MAX` = 0.90 | Optional 5-line rolling-window smoothing; near-boundary clean-prose promotion if WC ≥ 4 (`CLEAN_PROSE_WC_MIN`), weird ≤ 0.08 (`CLEAN_PROSE_WEIRD_MAX`), PPL ≤ 400 (`CLEAN_PROSE_PPL_MAX`) |
| **Clear**            | Q_s ≥ 0.90                                  | Passed to downstream NLP                                                                                                                                                                  |
| **Non-text / Empty** | Structural                                  | Lines matching bureaucratic stamp regex (`123/456`, `NZ1998/01`), length < 4 chars, or alpha ratio < 30% — sequestered before LLM ingestion                                               |

#### Architecture: CPU/GPU Split

A fleet of parallelised CPU workers (up to `WORKERS_MAX = 32`) handles file I/O, FastText language
identification, and structural anomaly detection. A single GPU worker holds the Qwen2.5-0.5B model
and processes perplexity batches from a shared memory queue. This prevents VRAM OOM on large corpora
while keeping GPU utilisation high.

#### Supplementary: `infer_lang_from_diacritics()`

A model-free heuristic operating purely on diacritic density (e.g. `á č ď ě ň ř š ů ž` → Czech;
`ä ö ü ß` → German). Does not modify Q_s directly; provides a fast language signal for debug
analytics and future pipeline extensions.

### 5.3 Parameter Optimisation (Issue #5)

~30 hand-set constants govern the composite score. Issue #5 proposes replacing manual calibration
with surrogate machine-learning modelling: Random Forests, Gaussian Processes, SVMs, and XGBoost
trained to map the quality-filter performance landscape. Evaluation methodologies under consideration:
fANOVA, Shapley variance decomposition, and Local Parameter Importance analysis.

Benchmarks used for methodology validation: OpenML100, ARLBench, HPO-RL-Bench, LCBench, PD1.

### Open Issues (5 — all K4TEL, all Q1-Q2 WP4/WP5)

| #    | Title                                                                    | Type                  | Date        |
|:-----|:-------------------------------------------------------------------------|:----------------------|:------------|
| `#6` | Add starting points to the pipeline run script (resumability)            | enhancement           | 24 Jun 2026 |
| `#5` | Surrogate-model parameter importance for bool/int/float config constants | Feature · *beginning* | 24 Jun 2026 |
| `#4` | Documentation of the categorisation logic                                | documentation         | 28 May 2026 |
| `#3` | Calibration of categorisation logic against extracted-string parameters  | development           | 17 Apr 2026 |
| `#2` | Update definition of text categories and assignment logic                | development           | 13 Mar 2026 |

Issues #2–#5 cluster on calibrating and documenting the categorisation heuristics. #6 adds ergonomics
(resumable run points). **#5's surrogate-model approach is the right mechanism to tame this configuration
space and should be prioritised over manual constant tuning.**

---

## 6. Phase D.1 — Protected Translation

**Repository:** `ufal/atrium-translator` · 68 commits · 12 tags · MIT · `master` ·
`tool_version: v0.5.0` · **Most production-ready of the four products.**

### Function

A Python wrapper around the LINDAT Translation API restricted to XML and derivatives. Two modes:

- `--alto` — ALTO XML in-place translation
- `--xpaths` — XML metadata (AMCR/OAI-PMH/any schema)

Language detection via FastText; XML-metadata mode falls back to Czech below 0.2 confidence;
ALTO mode runs detection once per `TextBlock`.

### Tag-and-Protect Controlled Vocabulary

The core mechanism protecting archaeological terminology from NMT corruption:

1. **Vocabulary ingestion** — `load_vocab.py` harvests Czech→English pairs from AMCR OAI-PMH and
   the TEATER GraphQL API (the Thesaurus of Archaeological Terminology, a trilingual ontological
   map of ~12 domain hierarchies: theory, field methods, chronology, stratigraphy, structural
   features, materials, societal designations, etc.)

2. **Sentinel substitution** — recognised TEATER terms are replaced with alphabetic sentinels
   (`Xtermzzz<N>z` pattern; earlier underscore sentinels mangled NMT output and were replaced).
   Multi-word phrases captured via case-insensitive longest-substring matching; single words via
   UDPipe lemmatisation with singular/plural number-agreement guard.

3. **NMT translation** — surrounding prose is translated while sentinels pass through untouched.

4. **Reverse-lookup restoration** — sentinels are replaced with TEATER's target-language equivalents.

### ALTO Spatial Reconstruction

Translation alters character counts and word lengths, shattering the original ALTO bounding-box
geometry. A dual-pass reconstruction addresses this:

- **Block pass** — full `TextBlock` translation for quality
- **Line anchor pass** — per-line re-anchoring via `difflib.SequenceMatcher` with a ±50% sliding
  window, realigning translated text back into original bounding-box coordinates

XSD validation against e.g. `api.aiscr.cz/schema/amcr/2.2/amcr.xsd` follows.
Sentence-aware chunking at 4,000 chars prevents API context truncation.

### Open Issues (1)

- 1 open issue (specifics not enumerated this cycle). Primary risk area: NMT word-count mismatch
  handled by the alignment heuristic.

---

## 7. Phase D.2 — NLP Enrichment and TEITOK Output

**Repository:** `ufal/atrium-nlp-enrich` · 133 commits · MIT · **Broadest feature surface;
most resource-intensive stage.**

### Core Pipeline

```
api_1_manifest.sh
    → api_2_udp.sh      UDPipe 2 (czech-pdt-ud-2.15-241121)
                        900-word chunking with page-break injection
                        → tokenisation, lemmatisation, POS, dependency parse
                        → CoNLL-U output
    → api_3_nt.sh       NameTag 3 (nametag3-czech-cnec2.0-240830)
                        CNEC 2.0 NE tags → NE TSV
    → api_4_stats.sh    Merge to TEITOK XML
                        ALTO bbox alignment: difflib.SequenceMatcher(autojunk=False)
                        per-page PNG coordinate scaling
                        → summary_ne_counts.csv
```

Config: `config_api.txt` (`SAVE_TEITOK`, `SAVE_CONLLU_NE`, `SAVE_CSV`, `INPUT_PAGES_DIR`).

### Why TEITOK

TEITOK XML (TEI-compliant, originally from PostScriptum/EHRI) connects physical bounding-box
coordinates directly to POS metadata and translated semantics. Unlike standard archival repositories
that treat transcriptions as static descriptions, TEITOK enables queries not just for *whether* a
term exists in 1.2 million pages, but *where* it sits on a drawing and *how* it functions
syntactically in the author's sentence.

### Extra Modules

| Module                   | Notes                                                                                                                                                        |
|:-------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Keyword extraction**   | Legacy KER / YAKE (default, unsupervised/statistical) / KeyBERT (Transformer embeddings + cosine similarity, higher compute) — configured in `kw_config.txt` |
| **`flexiconv` adapter**  | Non-ALTO input formats: PAGE XML / hOCR / plain text                                                                                                         |
| **Local-LLM enrichment** | `llm_run.py` + `vocab_manager.py`; see §8                                                                                                                    |

### Open Issues (6 — all K4TEL)

| #     | Title                                                              | Type                       | Milestone  | Date        |
|:------|:-------------------------------------------------------------------|:---------------------------|:-----------|:------------|
| `#11` | NameTag3 multilingual base model option                            | enhancement                | Q1-Q2      | 21 Jun 2026 |
| `#10` | Add flexiconv-supported input options (any text-containing format) | Feature · *big one*        | Q1-Q2      | 28 May 2026 |
| `#9`  | TEITOK output: image-files dependence handling                     | Task                       | Q1-Q2      | 28 May 2026 |
| `#8`  | Add API service wrapper                                            | Feature                    | Q1-Q2      | 28 May 2026 |
| `#7`  | Domain-specific NameTag model training (Czech archaeology)         | Task · *big one/beginning* | Q3 WP8/WP7 | 11 May 2026 |
| `#6`  | LLM keyword extraction from TEATER vocabulary                      | Feature · *big one*        | Q1-Q2      | 17 Apr 2026 |

---

## 8. Local LLM Deployment

Historical archaeological records stress-test linguistic models: morphological degradation, field
abbreviations, no modern syntactic standardisation. Standard NER frequently misses archival semantics.

### Inference Backends

**`transformers` + BitsAndBytes 4-bit** — single-GPU up to ~31B parameters.  
**`vllm` + xgrammar multi-GPU** — tensor-parallel-size 8, Automatic Prefix Caching; ≥70B parameters.

Default model: **`qwen-3.6-27b-it`** (Qwen 2.5 27B Instruct). Extended registry:
`qwen3-235b-a22b-fp8`, `deepseek-v3`, `llama4-maverick`.

### Model Evaluation Summary

| Model                                  | Params         | Context  | Czech / Archaeological Assessment                                                                                                        |
|:---------------------------------------|:---------------|:---------|:-----------------------------------------------------------------------------------------------------------------------------------------|
| **Qwen 2.5 Instruct**                  | 14B / 7B / 27B | 32k–128k | Preferred. Trained on 36T tokens; native morphological handling across 119 languages; reliable structured JSON extraction against TEATER |
| Mistral NeMo                           | 12B            | 128k     | Strong long-context ingestion; archived/unsuccessful                                                                                     |
| Bielik v2.3                            | 11B            | 8k       | Targeted West Slavic (PL/CZ) transfer; archived                                                                                          |
| Llama 3.1                              | 8B             | 128k     | Prompt-sensitive; archived                                                                                                               |
| Gemma 3-12B, Qwen2.5-14B AWQ, Qwen3-8B | various        | —        | Misclassified form-label fields (e.g. "Druh nálezu"); hallucinated on ambiguous abbreviations ("Kultura Z.") → archived                  |

**Graveyard:** Mistral Nemo 12B, Aya Expanse 8B, Bielik 11B v3.0, LLaMA 3.1-8B, Ministral 3–14B,
early Qwen3-8B/Qwen2.5-7B. Evaluation notes in `atrium-nlp-enrich` issue #6.

### Design Principles

- **Targeted vocabulary injection** via semantic similarity search (lightweight embeddings), feeding
  only relevant TEATER subsections rather than bulk dumps that dilute attention.
- **Sliding context window** respecting structural page boundaries to prevent semantic
  cross-contamination between unrelated excavation reports.
- **Token logit masking** to guarantee JSON schema conformance at the inference level, eliminating
  parsing failures and self-repair loops.
- **Abort sidecar** (`*_enriched.abort.json`) fires after 10 consecutive inference errors.

### Hardware Bottleneck (Issues #26/#27)

70B @ fp16 requires ~140 GB VRAM. Hub #26 (CPU offloading) is flagged **blocked**. PCIe bandwidth
(~100 GB/s) is an order of magnitude slower than GPU HBM (~2–3 TB/s), creating severe throughput
penalties. Recommended path: **vLLM `cpu_offload_gb` with UVA backend** (single-GPU nodes);
**tensor-parallel-size 8 on the H100 8-GPU node** for ≥70B (hub #27). Commercial cloud is ruled
out by data-sovereignty requirements.

---

## 9. Cross-Cutting Architecture

### Shared Provenance Logger

Every product repo ships **`atrium_paradata.py`** (schema v2.0). For every document processed,
the module records:

- Unique cryptographic `run_id`
- Tool / repo identity and internal URLs
- UTC timestamps
- Config snapshot (e.g. `llm_config.txt` at execution time)
- Line-level execution faults (skipped entities documented, not deleted)
- **Computed effective licence** — dynamically derived from the specific combination of tools used
  (e.g. LINDAT CUBBITT + UDPipe resolves to CC BY-NC-SA 4.0). Component→licence maps in each
  repo's `para_config.txt`, resolved by `para_licenses.py`.

Paradata output goes to `<OUTPUT_DIR>/paradata/`. This ensures scientific reproducibility: future
researchers can trace exactly why a specific historical line was excluded from the final dataset.

The architecture intentionally avoids heavyweight ontological standards (W3C PROV-O, CIDOC-CRM,
JSON-LD) during raw extraction, favouring a flat JSON log that doesn't cripple throughput on a
1.2-million-page corpus.

---

## 10. Active Work-Package Milestones

| Milestone                                                              | Scope                                                  | Status                        |
|:-----------------------------------------------------------------------|:-------------------------------------------------------|:------------------------------|
| **Q1-Q2 \[WP4/WP5\]** Mid-Project Workflow Beta Testing & Integration  | Bulk of open engineering and dissemination work        | **Current centre of gravity** |
| **Q3 \[WP8/WP7\]** Advanced Transnational Access & Curriculum Drafting | Document understanding evaluation, domain NER training | Upcoming                      |
| **Q4 \[WP3\]** Conclusion of Semantic Harmonisation                    | LLM applications, multi-GPU scaling, H100 deployment   | Future                        |
| **CAA Proceedings**                                                    | PCJ submission #13                                     | Active                        |

---

## 11. `ufal/atrium-project` — Hub Open Issues (14)

| #     | Title                                                                       | Milestone  | Owner | Date        |
|:------|:----------------------------------------------------------------------------|:-----------|:------|:------------|
| `#27` | H100 node — running models on multiple GPUs                                 | Q4 WP3     | K4TEL | 20 Jun 2026 |
| `#26` | Running models larger than GPU memory (CPU offload) — **BLOCKED**           | Q4 WP3     | K4TEL | 20 Jun 2026 |
| `#24` | LLM applications to data (*big one / beginning*)                            | Q4 WP3     | K4TEL | 19 Jun 2026 |
| `#22` | Document Understanding — evaluation of out-of-the-box tools (*big one*)     | Q3 WP8/WP7 | K4TEL | 17 Jun 2026 |
| `#21` | LINDAT: Annotated dataset release                                           | Q1-Q2      | K4TEL | 12 Jun 2026 |
| `#18` | Docker composer + GH Action wrapper for CU repo forks (*big one*)           | Q1-Q2      | motyc | 27 May 2026 |
| `#17` | Review workflow descriptions in SSHOMP                                      | Q1-Q2      | motyc | 27 May 2026 |
| `#16` | List all current storage locations of ARÚP/B data (*big one*)               | Q1-Q2      | motyc | 27 May 2026 |
| `#15` | Submission to IJDL (*big one*)                                              | Q1-Q2      | motyc | 27 May 2026 |
| `#13` | CAA Proceedings paper submission to PCJ                                     | CAA        | K4TEL | 25 Mar 2026 |
| `#10` | LLM validation of source code (*big one*)                                   | Q1-Q2      | K4TEL | 15 Mar 2026 |
| `#9`  | Paradata of outputs — origin of `atrium_paradata.py` workstream (*big one*) | Q1-Q2      | K4TEL | 13 Mar 2026 |

---

## 12. Key Bottlenecks and Risk Areas

**Hardware / LLM inference** — The most pronounced current bottleneck. Hub #26 is **blocked**.
4-bit/8-bit quantisation (already deployed in the `transformers`+BnB backend) and vLLM tensor-parallel
on H100 (hub #27) are the near-term mitigations.

**Calibration debt in alto-postprocess** — ~30 hand-set constants govern the composite quality score.
Issues #2–#5 address this systematically. #5 (surrogate-model parameter importance) is the right
mechanism to tame this configuration space.

**Documentation gaps** — Alto-postprocess #4 (categorisation-logic docs) and hub #17 (SSHOMP workflow
descriptions) are prerequisites for the IJDL (#15) and CAA/PCJ (#13) publication milestones.

**`@test`-branch visibility** — The DEVLOG timeline indexes and issue digests live exclusively on the
`test` branch of each repo. Research agents working only from default branches lack this context.

---

## 13. Priority Action Map

Ordered by blocking impact:

1. **Hub #18** — Docker + reusable GH-Action wrapper: unblocks the `@test`-pinned CI plumbing tying
   all four products together; prerequisite for Q1-Q2 integration milestone.
2. **nlp-enrich #8** — Wrap pipeline as API service: aligns with #18; integration surface for
   downstream consumers.
3. **Alto-postprocess #5** — Surrogate-model parameter importance: tames the 30-constant calibration
   surface; feeds #3 and #2.
4. **Alto-postprocess #4 + Hub #17** — Documentation: unblocks IJDL (#15) and PCJ/CAA (#13) submissions.
5. **Hub #26/#27** — CPU offload + H100 multi-GPU: required for Q4 LLM scaling; #26 is blocked;
   recommended path is vLLM `cpu_offload_gb` + UVA backend.

---

## 14. Suggested New Issues

Based on the combined review, two gaps are not covered by any existing open issue:

### `ufal/atrium-project` — End-to-end integration smoke test

**`[Feature]`** No issue tracks a pipeline-wide regression test. A minimal fixture (single-page ALTO
→ postprocess → translate → enrich → TEITOK) run in CI would catch cross-repo interface breakage
early, especially given the `@test`-pinned reusable workflow architecture.
*Prerequisite: #18 (Docker wrapper). Milestone: Q1-Q2.*

### `ufal/atrium-nlp-enrich` — TEITOK output XML schema validation

**`[Task]`** `atrium-translator` performs XSD validation; `atrium-nlp-enrich` produces TEITOK XML
but has no equivalent validation gate. A schema-conformance check at the end of `api_4_stats.sh`
would catch malformed output before it reaches downstream consumers or the LINDAT dataset release.
*Milestone: Q1-Q2.*

---

## 15. Test Branch State (27 June 2026)

All five repos have an active `test` branch updated on 27 June 2026 by K4TEL. The per-repo state
in §§4–7 and §11 documents only default-branch content; `test`-branch issue digests and DEVLOG
entries are not reflected here.

| Repository                        | `test` HEAD SHA | Commit message                             | Date       |
|:----------------------------------|:----------------|:-------------------------------------------|:-----------|
| `ufal/atrium-project`             | (not retrieved) | —                                          | 2026-06-27 |
| `ufal/atrium-translator`          | `40ff9be`       | "update issue #4 digest and plan"          | 2026-06-27 |
| `ufal/atrium-page-classification` | `6911d21`       | "docs update"                              | 2026-06-27 |
| `ufal/atrium-alto-postprocess`    | `32038a1`       | "update issue #5 digest and plan extended" | 2026-06-27 |
| `ufal/atrium-nlp-enrich`          | `9ffaa57`       | "update issue #8 digest and plan"          | 2026-06-27 |

To retrieve `test`-branch HEAD details programmatically:

```bash
repos=(atrium-project atrium-translator atrium-page-classification atrium-alto-postprocess atrium-nlp-enrich)
for repo in "${repos[@]}"; do
  echo "=== $repo ==="
  git ls-remote "https://github.com/ufal/$repo.git" | grep "refs/heads/test"
done
```

---

## Appendix: Key External References

| Resource                        | URI                                     |
|:--------------------------------|:----------------------------------------|
| CORDIS project fact sheet       | `cordis.europa.eu/project/id/101132163` |
| ATRIUM project site             | `atrium-research.eu`                    |
| CAA proceedings paper (Zenodo)  | `zenodo.org/records/20813374`           |
| March 2026 project presentation | `zenodo.org/records/19500212`           |
| LINDAT annotation dataset       | `hdl.handle.net/20.500.12800/1-5959`    |
| HuggingFace fine-tuned weights  | `hf.co/ufal/vit-historical-page`        |
| TEATER thesaurus                | `teater.aiscr.cz`                       |
| AMCR XSD schema                 | `api.aiscr.cz/schema/amcr/2.2/amcr.xsd` |
| Org Project board               | `github.com/orgs/ufal/projects/21`      |
