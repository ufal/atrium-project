# ATRIUM Pipeline — Unified Ecosystem State Digest

**Date: 26 June 2026 · Scope: five `ufal` GitHub repositories**

---

## Project Overview

**ATRIUM** ("Advancing fronTier Research In the arts and hUManities") is a Horizon Europe project (Grant No. 
101132163, Jan 2024–Dec 2027), coordinated by DARIAH, bridging four European research infrastructures: DARIAH, ARIADNE, 
CLARIN, and OPERAS. 29 partners across 14 countries. UFAL's (Charles University) contribution is the technical NLP/OCR
pipeline for Czech archaeological archival documents, primarily from ARÚP/ARÚB (Institute of Archaeology, Prague/Brno).

The pipeline is deliberately **not a monorepo**: `atrium-project` is the planning hub; the four product repos 
execute the actual work. Planning is tracked via the org Project board (`github.com/orgs/ufal/projects/21`). A March 
2026 project presentation is archived on Zenodo (`zenodo.org/records/19500212`).

All five repos are public, owned by `ufal`, and show "Updated Jun 26, 2026." Primary author/maintainer is **K4TEL** 
(engineering issues); **motyc** tracks dissemination/publication work.

---

## End-to-End Data Flow

Raw scanned archival images enter the pipeline and traverse four stages:

**1 → Page Classification** (`atrium-page-classification`): ViT/CNN classifies page images into 11 content categories 
(`DRAW`, `DRAW_L`, `LINE_HW`, `LINE_P`, `LINE_T`, `PHOTO`, `PHOTO_L`, `TEXT`, `TEXT_HW`, `TEXT_P`, `TEXT_T`) to route 
each page to the correct downstream OCR/processing path.

**2 → ALTO Post-Processing** (`atrium-alto-postprocess`): Splits document-level ALTO XML into pages, extracts text 
(LayoutReader / alto-tools / GLM-4v), and runs a line-level quality + language classifier (FastText langID +
Qwen2.5-0.5B perplexity) assigning each line `Clear`/`Noisy`/`Trash`/`Non-text`/`Empty`.

**3 → Translation** (`atrium-translator`): In-place XML/ALTO/AMCR metadata translation to English via the LINDAT 
Translation API, preserving spatial bounding box geometry with a dual-pass ALTO reconstruction and Tag-and-Protect controlled vocabulary.

**4 → NLP Enrichment** (`atrium-nlp-enrich`): Adds NER (NameTag 3, CNEC 2.0), morphology/syntax (UDPipe 2 → CoNLL-U), 
keywords (YAKE/KeyBERT), and optional local-LLM vocabulary mapping; emits unified TEITOK XML.

---

## Cross-Cutting Architecture

**Shared provenance logger.** Every product repo ships `atrium_paradata.py` (schema v2.0), capturing `run_id`, 
tool/repo identity, UTC timing, config snapshot, statistics, and a computed effective license resolved from components 
actually used (e.g. LINDAT CUBBITT + UDPipe resolves to CC BY-NC-SA 4.0). Component→license maps live in each repo's 
`para_config.txt`, resolved by `para_licenses.py`.

**`@test`-pinned GitHub Actions.** Repos are wired together via reusable workflows referenced at `@test`. The
`agent_dev_logs/` directory (DEVLOG timeline indexes and issue digests) lives on the `test` branch of each repo — 
**not on the default branches** (`main`/`master`/`vit`) — and was not accessible to the research agents that produced these reports.

**Common conventions across all repos:** MIT code license, CC BY-NC 4.0 for paradata logs, `CITATION.cff`, 
`CONTRIBUTING.md`, `[SECTION]`-style `config*.txt`, `tests/`+`pytest.ini` suite, acknowledgements footer (developer 
handle **K4TEL**, contact `lutsai.k@gmail.com`).

---

## Active Work-Package Milestones

Issues across all repos map to shared milestones:

- **Q1-Q2 \[WP4/WP5: Mid-Project Workflow Beta Testing & Integration\]** — current center of gravity; covers the 
bulk of open engineering and dissemination work
- **Q3 \[WP8/WP7: Advanced Transnational Access & Curriculum Drafting\]** — evaluation, document understanding, domain NER training
- **Q4 \[WP3: Conclusion of Semantic Harmonization\]** — LLM applications, multi-GPU scaling, H100 deployment
- **CAA Proceedings** — publication track

---

## Per-Repository State

### `ufal/atrium-project` — Hub 🗂️

**Default branch:** `main` · 6 commits · root: `README.md` only.

Role: planning/landing repo pointing to the four product repos and the org Project board. Lists ARÚP/ARÚB data-owner 
contacts and the March 2026 Zenodo presentation. Doubles as the cross-repo infra tracker and dissemination/publication tracker.

**Open issues (14):**

- `#27` H100 node — running models on multiple GPUs *(Q4 WP3; K4TEL; 20 Jun 2026)*
- `#26` Running models larger than GPU memory using CPU *(Q4 WP3; K4TEL; 20 Jun 2026)* — flagged **blocked**
- `#24` LLM applications to data *(Q4 WP3; "a big one/beginning"; K4TEL; 19 Jun 2026)*
- `#22` Document Understanding — evaluation of out-of-the-box tools *(Q3 WP8/WP7; "a big one"; K4TEL; 17 Jun 2026)*
- `#21` LINDAT: Annotated dataset release *(Q1-Q2; documentation/help-wanted; K4TEL; 12 Jun 2026)*
- `#18` Docker composer + GH action coded as wrapper for CU repo forks *(Q1-Q2; "a big one"; motyc; 27 May 2026)* — 
the `@test` reusable-workflow/Docker integration workstream
- `#17` Review workflow descriptions in SSHOMP *(Q1-Q2; documentation; motyc; 27 May 2026)*
- `#16` List all current storage locations of ARUP/B data *(Q1-Q2; "a big one"; motyc; 27 May 2026)*
- `#15` Submission to the IJDL *(Q1-Q2; "a big one"; motyc; 27 May 2026)*
- `#13` CAA Proceedings paper submission to PCJ *(CAA Proceedings; K4TEL; 25 Mar 2026)*
- `#10` LLM validation of source code *(Q1-Q2; "a big one"; K4TEL; 15 Mar 2026)*
- `#9` Paradata of outputs — origin of the shared `atrium_paradata.py` workstream now implemented across all repos
*(Q1-Q2; "a big one"; K4TEL; 13 Mar 2026)*

The newest issues (#24/#26/#27) push toward heavier local-LLM inference and multi-GPU/H100 deployment. #18 
(Docker/GH-action wrapper) and #9 (paradata) are the two cross-repo infrastructure anchors.

---

### `ufal/atrium-translator` — XML/ALTO In-Place Translation 🌐

**Default branch:** `master` · 68 commits, 12 tags · MIT · 2 forks. Latest paradata `tool_version`: `v0.5.0`.
**Most production-ready of the four products.**

**Current state:** LINDAT Translation API wrapper restricted to XML and derivatives. Two modes: ALTO XML (`--alto`) 
and XML Metadata (`--xpaths`, AMCR/OAI-PMH/any schema). Language detection via FastText (XML-metadata fallback to 
Czech below 0.2 confidence; ALTO detection once per `TextBlock`). Optional Tag-and-Protect controlled vocabulary: 
multi-word phrase pass + single-word UDPipe-lemma pass with singular/plural number-agreement guard; alphabetic 
sentinel form `Xtermzzz<N>z` (after underscore sentinels mangled NMT output). ALTO dual-pass reconstruction: 
block translation for quality + per-line anchors, realigned via `difflib.SequenceMatcher` with ±50% window. 
XSD validation against e.g. `api.aiscr.cz/schema/amcr/2.2/amcr.xsd`. Sentence-aware chunking at 4,000 chars. 
`load_vocab.py` harvests Czech→English pairs from AMCR OAI-PMH and TEATER GraphQL.

**Open workstreams:** 1 open issue (specifics not enumerated this cycle). Primary risk areas: NMT word-count
mismatch handled by the alignment heuristic.

---

### `ufal/atrium-page-classification` — Historical Page-Image Classification 🪧

**Default branch:** `vit` (non-standard; `clip` branch also exists) · 266 commits (most commits of any product repo) · 
MIT · 5 stars, 2 forks. **Technically the most mature/accurate component.**

**Current state:** Fine-tunes ViT / RegNetY / EfficientNetV2 / DiT / CLIP base models for 11-category page routing. 
Default released model **`v4.3` = `regnety_160.swag_ft_in1k`** (Top-1 **99.16%**, Top-3 **100.0%**); `v5.3` 
(`vit-large-patch16-384`) scores Top-1 **99.12%**. Latest data annotation phase (vX.3): **48,499 PNG images 
from 37,328 archival documents**, CC BY-NC-SA 4.0, on LINDAT (`hdl.handle.net/20.500.12800/1-5959`); fine-tuned 
weights on HF `ufal/vit-historical-page`. Deterministic periodic-sampling split (10% test_ratio, randomized offset, 
5-fold cross-validation). New `--best` ensemble engine (mean-of-softmax across the 5 best models; `--parallel` 
memory-aware GPU scheduling). Latest benchmark artifacts: `20260530-1234_BEST_5_models_TOP-1.csv` 
and `20260613-1002_BEST_5_models_TOP-1.csv`.

**Open workstreams:** 1 open issue (specifics not enumerated this cycle). Near-ceiling accuracy means future work 
is integration- and deployment-oriented (ensemble ergonomics) rather than core modeling.

---

### `ufal/atrium-alto-postprocess` — OCR/ALTO Post-Processing & Line Categorization 📄

**Default branch:** `master` · 193 commits · MIT · 2 stars, 2 forks. **Conceptual heart of OCR quality control; 
most open issues of any product repo.**

**Current state:** 4-stage pipeline —
1. `page_split.py` splits document ALTO into per-page XML
2. `alto_stats_create.py` builds page-stats CSV via alto-tools
3. Text extraction: **LayoutReader** (GPU, reading-order + hyphenation repair, 1st choice) / **alto-tools** (CPU, 
fast) / **GLM-4v-9b** (GPU `gpuram48G`, generative OCR)
4. `langID_classify.py` line classifier (FastText langID + **Qwen2.5-0.5B** perplexity; English-only collections 
can swap `distilgpt2`) → `langID_aggregate_STAT.py` page aggregation

The composite **quality_score** is a weight-normalized sum of 10 signals — e.g. `QS_WEIGHT_VALID_WORD=0.25`, 
`QS_WEIGHT_GARBAGE=0.20`, `QS_WEIGHT_PERPLEXITY=0.15` — with routing thresholds (`CATEG_TRASH_SCORE_MAX=0.50`, 
`CATEG_NOISY_SCORE_MAX=0.90`), an inverted-scan rotation penalty (`ROT_RATIO_INVERTED_MIN=0.55`), Czech archaeology 
metadata-marker bypasses, short-perplexity cap (`SHORT_PPL_CAP=850.0` for Qwen / `2500.0` for distilgpt2), and post-processing 
smoothing (header/footer dedup, rolling 5-line window, page-level inverted-scan sweep). All tunables live in `config_langID.txt` 
under `[CLASSIFY]`/`[AGGREGATE]`/`[TEXT_UTILS]`.

Perplexity is the core OCR-quality signal: OCR errors (e.g. `"th3 qvick br0wn f0x"`) produce anomalously high perplexity 
relative to the baseline LM, triggering the `Trash`/`Noisy` path. Structural detectors and smoothing guards differentiate 
true OCR noise from archaic historical nomenclature (which may also elevate perplexity).

**Open issues (5, all K4TEL, all Q1-Q2 WP4/WP5):**

- `#6` Add starting points to the pipeline run script *(development/enhancement; 24 Jun 2026)*
- `#5` By small model, work out existing parameter importance for bool/int/float config constants *(Feature; "beginning"; 
24 Jun 2026)* — hyperparameter/surrogate-model auto-tuning for the ~30 hand-set QS weights and thresholds
- `#4` Documentation of the categorization logic *(documentation/question; 28 May 2026)*
- `#3` Calibration of the categorization logic applied to extracted-string parameters *(development; 17 Apr 2026)*
- `#2` Update definition of text categories and their assignment logic *(development; 13 Mar 2026)*

Issues #2–#5 cluster squarely on calibrating and documenting the categorization heuristics — appropriate for a component
governed by dozens of hand-set constants. #6 adds pipeline ergonomics (resumable run points).

---

### `ufal/atrium-nlp-enrich` — NLP Enrichment & TEITOK Output 🏷

**Default branch:** `master` · 133 commits · MIT · 2 forks. **Broadest feature surface; most resource-intensive stage.**

**Current state:** Consumes `text`-column CSVs from alto-postprocess; produces TEITOK XML (TEI-compliant, 
the pipeline's flagship output) plus CoNLL-U and NE TSV. Core pipeline:

- `api_1_manifest.sh` → `api_2_udp.sh` (**UDPipe 2**, model `czech-pdt-ud-2.15-241121`, 900-word chunking with 
page-break injection) → `api_3_nt.sh` (**NameTag 3**, model `nametag3-czech-cnec2.0-240830`, CNEC 2.0 tags) → 
- `api_4_stats.sh` (merge to TEITOK with ALTO bbox alignment via `difflib.SequenceMatcher autojunk=False`, 
per-page PNG coordinate scaling, `summary_ne_counts.csv`)

Config `config_api.txt` (`SAVE_TEITOK`, `SAVE_CONLLU_NE`, `SAVE_CSV`, `INPUT_PAGES_DIR` scaling).

**EXTRA modules:**
- Keyword extraction: legacy KER / YAKE (default) / KeyBERT; configured in `kw_config.txt`. 
YAKE is unsupervised/statistical; KeyBERT uses Transformer sentence embeddings + cosine similarity for semantic
precision at higher computational cost.
- **`flexiconv`** adapter for non-ALTO inputs (PAGE XML / hOCR / plain text)
- **Local-LLM semantic enrichment** (`llm_run.py` + `vocab_manager.py`): constrained JSON decoding over a TEATER/AMCR 
vocabulary, two backends — `transformers`+BnB 4-bit single-GPU (≤31B) and `vllm`+xgrammar multi-GPU (≥70B, 
Automatic Prefix Caching). Default model `qwen-3.6-27b-it`; registry extends to `qwen3-235b-a22b-fp8`, `deepseek-v3`, 
`llama4-maverick`. README documents a graveyard of archived/unsuccessful model runs (Mistral Nemo 12B, Aya Expanse 8B, 
Bielik 11B v3.0, LLaMA 3.1-8B, Ministral 3–14B, early Qwen3-8B/Qwen2.5-7B; evaluation notes in issue #6). Abort sidecar
`*_enriched.abort.json` fires after 10 consecutive inference errors.

**Open issues (6, all K4TEL):**

- `#11` NameTag3 multilingual base instead of per-language NER model choice *(development/enhancement; Q1-Q2; 21 Jun 2026)*
- `#10` Add flexiconv-supported input options (any text-containing format) *(Feature; "a big one"; Q1-Q2; 28 May 2026)*
- `#9` TEITOK output: image-files dependence handling *(Task; development; Q1-Q2; 28 May 2026)*
- `#8` Add API service to be wrapped up *(Feature; development; Q1-Q2; 28 May 2026)* — aligns with hub #18
- `#7` NER — Training of domain-specific NameTag model *(Task; "a big one/beginning"; Q3 WP8/WP7; 11 May 2026)*
- `#6` Extract keywords from user-defined "vocabulary" using LLM request (TEATER topics) *(Feature; "a big one"; 
Q1-Q2; 17 Apr 2026)* — holds model-evaluation notes referenced throughout the README

---

## Key Bottlenecks & Risk Areas

**Hardware / LLM inference.** The most pronounced current bottleneck. Modern LLMs require tens to hundreds of GB of VRAM; 
even a 70B model at fp16 needs ~140 GB. Hub #26 (CPU offloading) is flagged **blocked**. CPU offloading via PCIe 
(~100 GB/s) is an order of magnitude slower than GPU HBM (~2–3 TB/s), creating severe throughput penalties for 
large-scale document runs. Near-term mitigations: 4-bit/8-bit quantization (already deployed in the 
`transformers`+BnB backend) and vLLM with tensor-parallel-size 8 on the H100 8-GPU node (hub #27). 
Data-sovereignty requirements mandate local/cluster inference throughout — commercial cloud is not an option.

**Calibration debt in alto-postprocess.** ~30 hand-set constants govern the composite quality score. Issues #2–#5 
address this systematically; #5's surrogate-model parameter-importance approach is the right mechanism to tame 
this configuration space and should be prioritized.

**Documentation gaps.** Alto-postprocess #4 (categorization-logic docs) and hub #17 (SSHOMP workflow descriptions) 
are both prerequisites for the publication milestones (IJDL #15, CAA/PCJ #13).

---

## Priority Action Map

The following cross-repo items are highest leverage, ordered by blocking impact:

1. **Hub #18** (Docker + reusable GH-action wrapper) — unblocks the `@test`-pinned CI plumbing that ties all four 
products together; prerequisite for Q1-Q2 integration milestone.
2. **nlp-enrich #8** (wrap pipeline as API service) — aligns with #18 and is the integration surface for downstream consumers.
3. **Alto-postprocess #5** (surrogate-model parameter importance) — tames the 30-constant calibration surface; feeds #3 and #2.
4. **Alto-postprocess #4 + Hub #17** (documentation) — unblocks IJDL (#15) and PCJ/CAA (#13) publication submissions.
5. **Hub #26/#27** (CPU offload + H100 multi-GPU) — required for Q4 LLM scaling; #26 is currently blocked and needs 
an architectural decision (vLLM `cpu_offload_gb` + UVA backend is the recommended path based on prior research).

---

## Source & Reliability Notes

All per-repo state above is sourced from retrievable public `ufal` GitHub pages: rendered READMEs on default branches 
(`main`/`master`/`vit`), live Issues lists with milestones/labels/authors/dates, and the org repositories page. 
Config constants, model names/versions, accuracy figures, dataset sizes, and issue numbers/dates are quoted from those pages.

The `test`-branch `agent_dev_logs/DEVLOG.md` timeline indexes and `digests/` are **not present on any default branch** 
and were not accessible to the research agents that produced the source documents. No DEVLOG or digest content is included here.

---

# Issues to consider adding: 

Based on the digest, here are suggested new issues grouped by repo, targeting gaps not covered by existing open issues:

### `ufal/atrium-project` (hub)

**`[Feature]` End-to-end integration smoke test across all four pipeline stages**
No issue tracks a pipeline-wide regression test. A minimal fixture (single-page ALTO → postprocess → translate → enrich → TEITOK) run in CI would catch cross-repo interface breakage early, especially given the `@test`-pinned reusable workflow architecture. Prerequisite: #18 (Docker wrapper). Milestone: *Q1-Q2*.

### `ufal/atrium-nlp-enrich`

**`[Task]` TEITOK output XML schema validation step**
`atrium-translator` performs XSD validation; `atrium-nlp-enrich` produces TEITOK XML but has no equivalent validation gate. A schema-conformance check at the end of `api_4_stats.sh` would catch malformed output before it reaches downstream consumers or the LINDAT dataset release. Milestone: *Q1-Q2*.
