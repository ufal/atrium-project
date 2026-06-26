# 🏛️ ATRIUM Federated Pipeline — State of the `ufal` Repositories Report

**Report date: 26 June 2026** · Scope: five `ufal` GitHub repositories of the ATRIUM digital-humanities pipeline

> ⚠️ **CRITICAL ACCESS CAVEAT (read first):** The specific artifacts this task targeted — the `agent_dev_logs/DEVLOG.md` timeline-index files and the `agent_dev_logs/digests/` issue-thread digests on the **`test` branch** of each repo — **could NOT be retrieved with the available tools, and could not even be confirmed to exist.** The research/fetch environment only permits fetching URLs that have first appeared in a search result; the GitHub raw-file endpoints (`raw.githubusercontent.com/ufal/<repo>/test/agent_dev_logs/DEVLOG.md`), the codeload tarball, the GitHub Contents API (`api.github.com/.../contents/agent_dev_logs?ref=test`), the jsDelivr CDN mirror, and the `tree/test/` and `/branches` GitHub UI pages were all blocked by this gate (not by GitHub) and never surfaced via search. A dedicated retrieval subagent confirmed the same limitation. **Nothing below is invented from those DEVLOG/digest files.** Everything reported is drawn from sources that *were* retrievable: each repo's rendered GitHub home page (default-branch README + root file tree + commit/tag counts) and each repo's open-issues list with milestones. Wherever the report touches the `test` branch or `agent_dev_logs`, it is explicitly flagged as **unverified / inaccessible**. The default branches checked (`main`/`master`/`vit`) do **not** contain an `agent_dev_logs/` directory at their root; the directory presumably lives only on the `test` branch, which I was unable to read.

---

## TL;DR

- **The ATRIUM `ufal` pipeline is a live, actively-developed (commits dated 26 June 2026), four-product + one-hub federated system** that turns scanned archaeological documents (chiefly Czech ARÚP/ARÚB archives) into FAIR, enriched, interoperable digital-humanities output: page-image classification → ALTO OCR post-processing/line-quality filtering → NLP enrichment (NER, UDPipe, keywords, LLM vocabulary mapping, TEITOK XML) → in-place XML/ALTO translation, all bound by a shared `atrium_paradata.py` provenance logger and reusable GitHub Actions workflows.
- **The requested deliverable — per-repo `agent_dev_logs/DEVLOG.md` and `digests/` on the `test` branch — was inaccessible with the available tooling and could not be confirmed to exist;** this report therefore reconstructs each repo's *current state and active workstreams* from the verifiable READMEs and open GitHub issues/milestones rather than from the dev logs themselves.
- **All five repos are public, owned by `ufal`, and were last updated 26 June 2026.** Their default branches are `atrium-project=main` (6 commits), `atrium-translator=master` (68 commits, 12 tags), `atrium-page-classification=vit` (266 commits), `atrium-alto-postprocess=master` (193 commits), `atrium-nlp-enrich=master` (133 commits). Active work is organized under shared work-package milestones, with the bulk of open issues sitting in **"Q1-Q2 [WP4 / WP5: Mid-Project Workflow Beta Testing & Integration]"** and a forward-looking **"Q4 [WP3: Conclusion of Semantic Harmonization]"**.

---

## 🌍 Big-Picture Summary — the ATRIUM Federated Pipeline

**ATRIUM** ("Advancing fronTier Research In the arts and hUManities") is an EU-funded project (Horizon Europe Grant Agreement No. 101132163; CORDIS `cordis.europa.eu/project/id/101132163`), running **1 January 2024 – 31 December 2027 (48 months)**, coordinated by **DARIAH** and bridging four leading European research infrastructures: **DARIAH** (arts & humanities), **ARIADNE** (archaeology), **CLARIN** (language technologies), and **OPERAS** (open scholarly communication). Per the CLARIN fact sheet, the consortium comprises **29 partners (including 12 affiliated entities) across 14 countries**. The stated goal is to deliver **interoperable, reusable, FAIR-compliant workflows** across the research data lifecycle, with archaeological data as the deepest test case.

The `ufal` (Institute of Formal and Applied Linguistics, Charles University) contribution is the **technical NLP/OCR pipeline** for archival documents. Per the **hub repo (`ufal/atrium-project`) README**, the project is deliberately **not a monorepo**: `atrium-project` is "Repository backing the Project for planning in ATRIUM" and explicitly states "the actual products are in other repositories," linking the four product repos. Planning is tracked in the GitHub org Project board (`github.com/orgs/ufal/projects/21`). The README lists ARÚP/ARÚB (Institute of Archaeology, Prague/Brno) contacts as the data-owner stakeholders for result updates (krivankova@arup.cas.cz, krofta@arup.cas.cz, lecbychova@arub.cz, novak@arup.cas.cz, spacil@arub.cz). A March 2026 project presentation is archived on Zenodo (`zenodo.org/records/19500212`).

**The end-to-end data flow across the four product repos:**

1. **`atrium-page-classification`** 🪧 — classifies historical page **images** (PNG from scanned PDFs) into 11 content categories (`DRAW`, `DRAW_L`, `LINE_HW`, `LINE_P`, `LINE_T`, `PHOTO`, `PHOTO_L`, `TEXT`, `TEXT_HW`, `TEXT_P`, `TEXT_T`) to route each page to the right downstream OCR/processing pipeline.
2. **`atrium-alto-postprocess`** 📄 — splits document-level **ALTO XML** into pages, extracts text (LayoutReader / alto-tools / GLM-4v LLM), and runs a line-level **quality + language classifier** (FastText langID + Qwen2.5-0.5B perplexity) assigning each line `Clear`/`Noisy`/`Trash`/`Non-text`/`Empty`.
3. **`atrium-nlp-enrich`** 🏷 — takes the extracted text CSVs and adds **NER (NameTag 3, CNEC 2.0), morphology/syntax (UDPipe 2 → CoNLL-U), keywords (legacy KER / YAKE / KeyBERT), and optional local-LLM vocabulary mapping**, emitting unified **TEITOK XML** with bounding boxes.
4. **`atrium-translator`** 🌐 — performs **in-place translation** of XML/ALTO/AMCR metadata into English via the LINDAT Translation API, with a Tag-and-Protect controlled-vocabulary strategy (UDPipe lemmatisation) and a dual-pass ALTO reconstruction that preserves spatial `String` layout.

**Cross-cutting architecture (verifiable from the product READMEs):**
- **Shared provenance logger.** Every product repo ships `atrium_paradata.py`, described in `atrium-translator` as "shared across all ATRIUM pipeline repositories." It writes structured JSON paradata (schema_version `2.0`) capturing tool/repo/run_id, UTC timing, config snapshot, statistics, and a **computed effective license** resolved from the components actually used (e.g. a translator run using LINDAT CUBBITT + UDPipe models resolves to **CC BY-NC-SA 4.0**). Component→license maps live in each repo's `para_config.txt`, resolved by `para_licenses.py`.
- **Reusable, `@test`-pinned GitHub Actions.** The task context (and the hub issue #18 "Docker composer + GH action coded as wrapper for CU repo forks," and translator paradata fields `ATRIUM_RUNNER_REPO`/`ATRIUM_RUNNER_REF`/`ATRIUM_RUNNER_IMAGE`) indicate the repos are wired together via reusable workflows referenced at `@test` rather than a monorepo. *(The `@test` pin and the `agent_dev_logs` that live on the `test` branch could not be directly inspected — see top caveat.)*
- **Common conventions.** All repos use **emoji-rich Markdown READMEs**, MIT code license, CC BY-NC 4.0 for paradata logs, `CITATION.cff`, `CONTRIBUTING.md`, a `[SECTION]`-style `config*.txt`, a `tests/`+`pytest.ini` suite, and an **acknowledgements footer** ("Developed by UFAL · Funded by ATRIUM · Shared by ATRIUM & UFAL"; repo contact **lutsai.k@gmail.com**, developer handle **K4TEL**).

---

## 🔑 Key Findings

- **`agent_dev_logs/DEVLOG.md` and `digests/` on `test` were not retrievable and not confirmed to exist.** No DEVLOG timeline entry, digest filename, or digest body is reported here, because none could be read. The default branches (`main`/`master`/`vit`) carry no root-level `agent_dev_logs/` directory.
- **The pipeline is current and active:** all five repos show "Updated Jun 26, 2026" on the org repositories page. Commit depth signals maturity ordering: page-classification (266 commits) > alto-postprocess (193) > nlp-enrich (133) > translator (68, 12 tags) > project hub (6).
- **Work is milestone-driven.** Open issues across repos map to shared work-package milestones: **"Q1-Q2 [WP4 / WP5: Mid-Project Workflow Beta Testing & Integration]"** (the current center of gravity), **"Q3 [WP8 / WP7: Advanced Transnational Access & Curriculum Drafting]"**, **"Q4 [WP3: Conclusion of Semantic Harmonization]"**, plus a publication-track **"CAA Proceedings"** milestone.
- **Primary author/maintainer is `K4TEL`** (opens most product-repo issues; repo contact lutsai.k@gmail.com); **`motyc`** opens the hub's planning/publication issues (data-location, SSHOMP workflow review, IJDL/PCJ paper submissions).
- **The four products are genuinely interoperable**, sharing `atrium_paradata.py`, the CSV `text`-column handoff (alto-postprocess → nlp-enrich), ALTO bounding-box reuse, and TEITOK XML as the unified DH output, with `flexiconv` as the universal input adapter for non-ALTO formats.

---

## 📚 Per-Repository Details

> For each repo: default branch & size, current state (from README), and open/in-progress workstreams (from the live Issues list with milestones). **`test`-branch `agent_dev_logs` contents are inaccessible for every repo — flagged inline.**

### 1️⃣ `ufal/atrium-project` — the HUB 🗂️
- **Default branch:** `main` · **6 commits** · 0 forks, 4 watchers · root contains only `README.md`.
- **Role:** Planning/landing repo for the whole `ufal` ATRIUM effort; points to the four product repos and the org Project board (`projects/21`). Lists ARÚP/ARÚB data-owner contacts and the March 2026 Zenodo presentation.
- **`agent_dev_logs` on `test`:** ⚠️ **Inaccessible / unverified** (not present on `main`; could not read `test`).
- **Open / in-progress workstreams (14 open issues; mix of engineering and dissemination):**
  - `#27` **H100 node — running models on multiple GPUs** (Feature; *Q4 WP3*; K4TEL, 20 Jun 2026)
  - `#26` **Running models larger than GPU memory using CPU** (Feature; *Q4 WP3*; K4TEL, 20 Jun 2026)
  - `#24` **LLM applications to data** (Feature; "a big one"/"beginning"; *Q4 WP3*; K4TEL, 19 Jun 2026)
  - `#22` **Document Understanding — evaluation of out-of-the-box tools** (Feature; "a big one"; *Q3 WP8/WP7*; K4TEL, 17 Jun 2026)
  - `#21` **LINDAT: Annotated dataset release** (Task; documentation/help-wanted; *Q1-Q2 WP4/WP5*; K4TEL, 12 Jun 2026)
  - `#18` **Docker composer + GH action coded as wrapper for CU repo forks** (Feature; "a big one"; *Q1-Q2*; motyc, 27 May 2026) — *the reusable-workflow/Docker integration workstream*
  - `#17` **Review workflow descriptions in SSHOMP** (Task; documentation; *Q1-Q2*; motyc, 27 May 2026)
  - `#16` **List all current storage locations of ARUP/B data** (Task; "a big one"; *Q1-Q2*; motyc, 27 May 2026)
  - `#15` **Submission to the IJDL** (Task; "a big one"; *Q1-Q2*; motyc, 27 May 2026)
  - `#13` **CAA Proceedings paper submission to PCJ** (Task; *CAA Proceedings* milestone; K4TEL, 25 Mar 2026)
  - `#10` **LLM validation of source code** (Task; "a big one"; *Q1-Q2*; K4TEL, 15 Mar 2026)
  - `#9` **Paradata of outputs (logs of program run)** (Task; "a big one"; *Q1-Q2*; K4TEL, 13 Mar 2026) — *origin of the shared `atrium_paradata.py` workstream now implemented across all repos*
- **Reading:** the hub doubles as the dissemination/publication tracker (IJDL, PCJ/CAA Proceedings, LINDAT dataset release) **and** the cross-repo infra tracker (Docker/GH-action wrapper #18, paradata #9). The newest issues (#24/#26/#27) push toward heavier local-LLM inference and multi-GPU/H100 deployment under the Q4 WP3 milestone.

### 2️⃣ `ufal/atrium-translator` — XML/ALTO in-place translation 🌐
- **Default branch:** `master` · **68 commits, 12 tags** · MIT · 2 forks. Latest paradata `tool_version` example in README: `v0.5.0`.
- **Current state (mature, well-documented):** A LINDAT Translation API wrapper restricted to XML and derivatives. Two modes: **ALTO XML** (`--alto`) and **XML Metadata** (`--xpaths`, AMCR/OAI-PMH/any schema). Detects source language via FastText (XML-metadata fallback to Czech below 0.2 confidence; ALTO detection once per `TextBlock`). Optional **Tag-and-Protect** controlled vocabulary (multi-word phrase pass + single-word UDPipe-lemma pass with a singular/plural number-agreement guard; alphabetic sentinel form `Xtermzzz<N>z` after underscore sentinels mangled NMT output). **ALTO dual-pass reconstruction** (block translation for quality + per-line anchors, realigned via `difflib.SequenceMatcher` with ±50% window). XSD validation against e.g. `api.aiscr.cz/schema/amcr/2.2/amcr.xsd`. Sentence-aware chunking at 4,000 chars. `load_vocab.py` harvests Czech→English pairs from AMCR OAI-PMH (`api.aiscr.cz/2.2/oai?set=heslo`) and TEATER GraphQL (`teater.aiscr.cz/api/graphql`).
- **`agent_dev_logs` on `test`:** ⚠️ **Inaccessible / unverified** (root of `master` has no `agent_dev_logs/`; it has a separate `paradata/` dir for example JSON logs).
- **Open / in-progress workstreams:** the org page lists **1 open issue** for this repo; its specific number/title was not individually retrievable in this session. **Completed/landed (from README):** dual-pass ALTO realignment, Tag-and-Protect with alphabetic sentinels, config-file support with `formats=alto.xml` auto-enabling ALTO mode, paradata schema 2.0 with computed license resolution.
- **Reading:** the most production-ready of the products (12 tagged releases, schema-2.0 paradata, XSD validation). Active surface is small; primary risk areas are per-block API cost (1+N calls per TextBlock) and NMT word-count mismatch handled by the alignment heuristic.

### 3️⃣ `ufal/atrium-page-classification` — historical page-image classification 🪧
- **Default branch:** `vit` (non-standard; `clip` branch also exists) · **266 commits** (most active repo) · MIT · 5 stars, 2 forks.
- **Current state (research-grade, extensively benchmarked):** Fine-tunes ViT / RegNetY / EfficientNetV2 / DiT base models for 11-category page routing. Default released model **`v4.3` = `regnety_160.swag_ft_in1k`** (Top-1 **99.16%**), with `v5.3` (`vit-large-patch16-384`) scoring the single best Top-1 **99.12%** (README accuracy table; v4.3 reaches Top-3 100.0%). Latest data annotation phase (`vX.3`): **48,499 PNG images from 37,328 archival documents**, CC BY-NC-SA 4.0, hosted on LINDAT (`hdl.handle.net/20.500.12800/1-5959`); fine-tuned weights on HF `ufal/vit-historical-page`. Deterministic periodic-sampling split (10% test_ratio) with randomized offset and 5-fold cross-validation. New `--best` ensemble engine (mean-of-softmax across the 5 best models, in-program averaging; `--parallel` memory-aware GPU scheduling; `--save-intermediates`, `--no-average-best`). Standardized CLI for data-prep and supplementary scripts. Latest dated artifact in README: `20260530-1234_BEST_5_models_TOP-1.csv` (30 May 2026) and `20260613-1002_BEST_5_models_TOP-1.csv` (13 Jun 2026).
- **Library note flagged in README:** targets **`transformers` 4.x**; on `transformers` 5.x the timm-based RegNetY `v4.3`/EfficientNetV2 `v1.3` builders break on the `meta` device (no meta kernel for `torch.unique`/`.item()`).
- **`agent_dev_logs` on `test`:** ⚠️ **Inaccessible / unverified** (not on `vit`; could not read `test`).
- **Open / in-progress workstreams:** org page shows **1 open issue** (number/title not individually retrievable this session). **Landed:** in-program `--best` ensemble averaging, parallel GPU engine, RegNetY/EffNetV2/DiT base-model sweep, paradata logging (`atrium_paradata.py`).
- **Reading:** technically the most mature/accurate component; near-ceiling accuracy means future work is integration- and deployment-oriented (ensemble ergonomics, `transformers` 5.x compatibility) rather than core modeling.

### 4️⃣ `ufal/atrium-alto-postprocess` — OCR/ALTO post-processing & line categorization 📄
- **Default branch:** `master` · **193 commits** · MIT · 2 stars, 2 forks.
- **Current state (deep, heavily-parameterized quality engine):** 4-stage pipeline — (1) `page_split.py` splits document ALTO into per-page XML; (2) `alto_stats_create.py` builds page-stats CSV via alto-tools; (3) text extraction with three backends — **LayoutReader** (GPU, reading-order + hyphenation repair, 1st choice), **alto-tools** (CPU, fast), **GLM-4v-9b** (GPU `gpuram48G`, generative OCR); (4) `langID_classify.py` line classifier (FastText langID + **Qwen2.5-0.5B** perplexity; English-only collections can swap `distilgpt2`) assigning `Clear`/`Noisy`/`Trash`/`Non-text`/`Empty`, then `langID_aggregate_STAT.py` page aggregation. The composite **quality_score** is a weight-normalized sum of 10 signals (config constants e.g. `QS_WEIGHT_VALID_WORD=0.25`, `QS_WEIGHT_GARBAGE=0.20`, `QS_WEIGHT_PERPLEXITY=0.15`; routing thresholds `CATEG_TRASH_SCORE_MAX=0.50`, `CATEG_NOISY_SCORE_MAX=0.90`) with documented overrides, an inverted-scan rotation penalty (`ROT_RATIO_INVERTED_MIN=0.55`), Czech-archaeology metadata-marker bypasses, short-perplexity cap (`SHORT_PPL_CAP=850.0` for Qwen / `2500.0` for distilgpt2), and post-processing smoothing (header/footer dedup, rolling 5-line window, page-level inverted-scan sweep). All tunables in `config_langID.txt` (`[CLASSIFY]`/`[AGGREGATE]`/`[TEXT_UTILS]`). Example artifacts `arup_page_stats_SHORT.csv`, `arub_page_stats_SHORT.csv`, `test_alto_stats.csv`.
- **`agent_dev_logs` on `test`:** ⚠️ **Inaccessible / unverified** (not on `master`; has separate `paradata/` dir).
- **Open / in-progress workstreams (5 open issues, all by K4TEL, all *Q1-Q2 WP4/WP5* except as noted):**
  - `#6` **Add starting points to the pipeline run script** (Task; development/enhancement; 24 Jun 2026)
  - `#5` **By small model, work out existing-parameter importance for bool/int/float config constants** (Feature; "beginning"; 24 Jun 2026) — *i.e. auto-tuning the many QS weights/thresholds above*
  - `#4` **Documentation of the categorization logic** (Task; documentation/question; 28 May 2026)
  - `#3` **Calibration of the categorization logic applied to extracted-string parameters** (Task; development; 17 Apr 2026)
  - `#2` **Update definition of text categories and their assignment logic** (Task; development; 13 Mar 2026)
- **Reading:** the conceptual heart of OCR quality control. Open issues cluster squarely on **calibrating and documenting the categorization heuristics** (#2/#3/#4/#5) and on pipeline ergonomics (#6 resumable starting points) — appropriate for a component whose behavior is governed by dozens of hand-set constants. *(Note: the org page and the issues sidebar reported slightly different open-issue counts — "5 issues" header vs. issues #2–#6 listed; treat the count as ~5.)*

### 5️⃣ `ufal/atrium-nlp-enrich` — NLP enrichment & TEITOK output 🏷
- **Default branch:** `master` · **133 commits** · MIT · 2 forks.
- **Current state (broadest feature surface):** Follow-up to alto-postprocess; consumes the `text`-column CSVs and produces **TEITOK XML** (TEI-compliant, the primary unified output) plus CoNLL-U and NE TSV. Pipeline: `api_1_manifest.sh` → `api_2_udp.sh` (**UDPipe 2**, model `czech-pdt-ud-2.15-241121`, 900-word chunking with page-break injection) → `api_3_nt.sh` (**NameTag 3**, model `nametag3-czech-cnec2.0-240830`, CNEC 2.0 tags) → `api_4_stats.sh` (merge to TEITOK with ALTO bbox alignment via `difflib.SequenceMatcher autojunk=False`, per-page PNG coordinate scaling, `summary_ne_counts.csv`). Config `config_api.txt` (`SAVE_TEITOK`, `SAVE_CONLLU_NE`, `SAVE_CSV`, `INPUT_PAGES_DIR` scaling). **EXTRA modules:** keyword extraction with three backends (legacy KER / YAKE default / KeyBERT) configured in `kw_config.txt`; **`flexiconv`** adapter for non-ALTO inputs (PAGE XML/hOCR/plain); and an advanced **local-LLM semantic enrichment** stage (`llm_run.py` + `vocab_manager.py`) with constrained JSON decoding over a TEATER/AMCR vocabulary, two backends (`transformers`+BnB 4-bit single-GPU ≤31B; `vllm`+xgrammar multi-GPU ≥70B with Automatic Prefix Caching). Extensive model registry (default `qwen-3.6-27b-it`; up to `qwen3-235b-a22b-fp8`, `deepseek-v3`, `llama4-maverick`). README documents successful, pending, and **archived/unsuccessful** model runs (Mistral Nemo 12B, Aya Expanse 8B, Bielik 11B v3.0, LLaMA 3.1-8B, Ministral 3-14B, early Qwen3-8B/Qwen2.5-7B — "evaluation notes in issue #6"). Abort sidecar `*_enriched.abort.json` after 10 consecutive inference errors. Runtime logs `<YYMMDD-HHmmss>_nlp-enrich.json` (a 2026-01-15 example appears in README).
- **`agent_dev_logs` on `test`:** ⚠️ **Inaccessible / unverified** (not on `master`; has separate `paradata/` dir).
- **Open / in-progress workstreams (6 open issues, all by K4TEL):**
  - `#11` **NameTag3 multilingual base instead of per-language NER model choice** (Task; development/enhancement; *Q1-Q2*; 21 Jun 2026)
  - `#10` **Add flexiconv-supported input options (any text-containing format)** (Feature; "a big one"; *Q1-Q2*; 28 May 2026)
  - `#9` **TEITOK output: image-files dependence handling** (Task; development; *Q1-Q2*; 28 May 2026)
  - `#8` **Add API service to be wrapped up** (Feature; development; *Q1-Q2*; 28 May 2026)
  - `#7` **NER — Training of domain-specific NameTag model** (Task; "a big one"/"beginning"; *Q3 WP8/WP7*; 11 May 2026)
  - `#6` **Extract keywords from user-defined "vocabulary" using LLM request (TEATER topics)** (Feature; "a big one"; *Q1-Q2*; 17 Apr 2026) — *the LLM semantic-enrichment workstream; holds the model-evaluation notes referenced in the README's archived-models list*
- **Reading:** the integration nexus that produces the project's flagship TEITOK output. Active work spans multilingual NER (#11), broader input coverage via flexiconv (#10), TEITOK image-dependency robustness (#9), exposing the pipeline as a wrapped API service (#8, aligning with hub #18), and a forward-looking domain-specific NameTag training effort (#7, Q3). The LLM keyword/vocabulary feature (#6) is the most experimentation-heavy area, with a documented graveyard of rejected models.

---

## ✅ Recommendations

**Staged next steps to actually obtain the `agent_dev_logs` deliverable (the part this run could not complete):**

1. **Run an authenticated/unrestricted GitHub fetch.** From any environment without the "URL must appear in a prior search result" gate, hit, per repo:
   - `git ls-remote --heads https://github.com/ufal/<repo>` → confirm whether a `test` branch exists.
   - `https://api.github.com/repos/ufal/<repo>/contents/agent_dev_logs?ref=test` → list DEVLOG + `digests/` filenames and `download_url`s.
   - `https://raw.githubusercontent.com/ufal/<repo>/test/agent_dev_logs/DEVLOG.md` → retrieve verbatim timeline.
   - Fallback: `https://codeload.github.com/ufal/<repo>/tar.gz/refs/heads/test` (unpacks to `<repo>-test/`).
   **Threshold that changes the plan:** if `git ls-remote` returns no `test` ref for a repo, treat that repo's `agent_dev_logs` request as *non-existent*, not merely inaccessible, and report accordingly.

2. **Once the DEVLOGs are in hand, re-issue this report** mapping each open issue above to its DEVLOG/digest entry, and **preserve the concrete artifacts the digests contain** (commit SHAs, exact dates, config constants) — this report already captures the config constants and issue numbers/dates that the digests most likely reference, so the merge will be straightforward.

3. **For the pipeline owners (K4TEL / motyc), based on the verifiable issue backlog:** prioritize the two cross-cutting integration items that unblock the others — hub **#18** (Docker + reusable GH-action wrapper, the `@test` plumbing) and nlp-enrich **#8** (wrap pipeline as an API service); both are prerequisites for the "Mid-Project Workflow Beta Testing & Integration" (Q1-Q2) milestone the majority of issues sit under. The alto-postprocess calibration cluster (#2–#5) is the highest-leverage *quality* work, and #5's "small-model parameter-importance" idea is the right mechanism to tame its ~30 hand-set constants.

4. **Documentation debt is explicit and worth clearing now:** alto-postprocess #4 (categorization-logic docs) and hub #17 (SSHOMP workflow descriptions) are both open documentation tasks that directly support the dissemination milestones (IJDL #15, CAA/PCJ #13) — closing them feeds the publications.

---

## ⚠️ Caveats

- **The core requested artifacts were not retrieved.** No `agent_dev_logs/DEVLOG.md` body, no `digests/` filenames, and no digest contents are reported for ANY of the five repos, because the `test`-branch raw/API/tarball/CDN endpoints were all blocked by the fetch environment's allowlist gate and the GitHub `tree/test` UI is robots-disallowed. A dedicated retrieval subagent independently hit the same wall. The **existence** of a `test` branch and an `agent_dev_logs/` directory **could not be confirmed** for any repo — the directory is absent from every default branch (`main`/`master`/`vit`) root.
- **What IS reliable:** everything in the per-repo "current state" and "open workstreams" sections is sourced from retrievable, primary `ufal` GitHub pages — the rendered READMEs (default branch), the live Issues lists with milestones/labels/authors/dates, and the org repositories page (commit/tag counts, "Updated Jun 26, 2026"). Config constants, model names/versions, accuracy figures, dataset sizes, and issue numbers/dates are quoted from those pages.
- **Branch mismatch.** READMEs and issues reflect each repo's **default** branch (`main`/`master`/`vit`), not the **`test`** branch the task targeted. The `test` branch may differ (it is where the `@test`-pinned reusable workflows and `agent_dev_logs` presumably live). Treat all per-repo specifics as default-branch state unless re-verified on `test`.
- **Open-issue counts have minor inconsistencies** between the org repositories page and individual issue sidebars (e.g. atrium-alto-postprocess "5 issues" header vs. issues #2–#6; atrium-translator/atrium-page-classification each show "1 issue" whose specifics were not individually enumerable this session). Counts are approximate; issue numbers/titles quoted are verbatim where listed.
- **No speculation was added:** forward-looking issue titles (e.g. hub #24/#26/#27 on LLM/GPU scaling, nlp-enrich #7 domain NameTag training) are reported as *open/planned*, not as completed work.

---

*Provenance footer 🧾 — Sources read (all public, owned by `ufal`), report compiled 26 June 2026:*
- `github.com/ufal/atrium-project` (README on `main`; Issues list #9–#27) · `github.com/orgs/ufal/repositories` (org listing, commit/tag counts, update dates) · `github.com/orgs/ufal/projects/21` (referenced)
- `github.com/ufal/atrium-translator` (README on `master`) · `github.com/ufal/atrium-page-classification` (README on `vit`) · `github.com/ufal/atrium-alto-postprocess` (README on `master`; Issues #2–#6) · `github.com/ufal/atrium-nlp-enrich` (README on `master`; Issues #6–#11)
- ATRIUM project context: CORDIS `cordis.europa.eu/project/id/101132163`; `dariah.eu`, `clarin.eu`, `operas-eu.org`, `ariadne-research-infrastructure.eu`, `atrium-research.eu`.
- **NOT read (inaccessible, flagged throughout):** `raw.githubusercontent.com/ufal/<repo>/test/agent_dev_logs/DEVLOG.md`, `api.github.com/.../contents/agent_dev_logs?ref=test`, `codeload.github.com/.../test`, jsDelivr `gh/ufal/<repo>@test`, and all `tree/test/` and `/branches` UI pages — for every one of the five repositories. The `test`-branch `agent_dev_logs` timeline indexes and digests were therefore **not** incorporated and are **not** fabricated.*