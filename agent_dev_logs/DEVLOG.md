# 📓 atrium-project — agent_dev_logs/DEVLOG.md (timeline index)
> _Hub/planning repo. 15 open issues. `test` HEAD `293b9f7` (2026-07-30), `main` `563ccd0` (2 commits behind)._
> _Per-issue detail: `digests/{id}.digest.md` · `plans/{id}.plan.md` · `issues/` exports (source of truth). Cross-repo snapshot: `digests/project_state_3007.md` (prior: `project_state_2207.md`, `project_state_1307.md`, `project_state_2706.md`)._

## 2026-03-13
- **#4 SSH Open Marketplace records** — Opened by stranak: create SSHOMP records for every tool in our workflows (UDPipe ✅, NameTag ✅, rest TBD).
- **#6 Review & summarise licenses** — Opened by stranak (review tool+model licenses, check where CC-BY-NC-SA is required). K4TEL posted the first license inventory: FastText/AMCR-vocab CC BY-NC, layoutreader CC BY-NC-SA, distilgpt2/alto-tools/GLM/Qwen2.5 Apache-2.0, ViT/EffNet/RegNet/CLIP MIT, NameTag3/CUBBITT CC BY-NC-SA, UDP2 MPL-2.0, AISCR Teater GPL-3.0.
- **#9 Paradata of outputs** — Opened by K4TEL: unified run-logging (incl. output license) across all four tool repos.

## 2026-03-15
- **#4** — Page classifier added to SSHOMP as a Suggested Tool under the `ATRIUM catalogue` keyword.
- **#9** — Translator, textline & page classifiers tested with paradata output; basic `.json` paradata in all repos via a shared `atrium_paradata.py`.
- **#10 LLM validation of source code** — Opened by K4TEL (validate every repo's source with an LLM).

## 2026-03-22
- **#10** — All projects checked with Sonnet 4.6 Extended, then re-checked with Gemini 3.

## 2026-03-25
- **#13 CAA Proceedings paper to PCJ** — Opened by K4TEL: submit a paper to the CAA2026 proceedings / PCI Archaeology; text draft posted (5000-word limit, no figures yet).

## 2026-03-26
- **#13** — Added the full project diagram, an updated report PDF with the diagram inserted, and a Zenodo submission draft.

## 2026-04-04
- **#13** — Overleaf editor invites sent to David and Dana; CAA-proceedings project + Springer extended-version project to be reformatted into CAA styles.

## 2026-04-11
- **#4** — The remaining three repositories suggested as SSHOMP tools.

## 2026-04-16
- **#4** — ALTO post-processor, NLP enrichment, translator and page classifier all uploaded as tool-or-service under the **ATRIUM catalogue** tag.

## 2026-05-13
- **#13** — motyc: proceedings deadline is **31 October 2026**.

## 2026-05-27
- **#15 Submission to IJDL** — Opened by motyc (review ASAP, link in the minutes).
- **#16 List ARUP/B data storage locations** — Opened by motyc (so ARUP/B can later remove all copies). K4TEL listed the `data_samples` dirs across repos, the LINDAT annotated dataset, thesis/presentation page samples, and the UFAL filesystem.
- **#17 Review SSHOMP workflow descriptions** — Opened by motyc.
- **#18 Docker compose + GH action wrapper for CU forks** — Opened by motyc (links the four ARUP-CAS forks).

## 2026-05-28
- **#9** — Mass→single-file paradata records merged per repo; open questions on license source, missing tool-version tag, dynamic runner reference, and a Docker-image placeholder.
- **#10** — Slated for re-examination by Opus 4.7 and Sonnet 4.6 across all four repos.
- **#17** — K4TEL posted the four marketplace tool links; motyc thanked; noted relation to #4.

## 2026-05-29
- **#9** — Detailed per-repo license breakdown: the tool-vs-model split (NameTag3/UDPipe engines MPL-2.0 but their models CC BY-NC-SA), Teater app GPL vs data CC BY-NC, and the internal-academic-use vs external-commercial-use distinction.
- **#10** — motyc: "Opus 4.8 is just out :)".
- **#16** — Posted per-repo licensed-asset tables (alto 39, nlp 34, translator 14, page-classification 84 documents) mapped to licenses from the global metadata collection.

## 2026-06-02
- **#9** — The two easy repos (translator, page-classification) updated with paradata licenses; the two multi-step repos (alto, nlp) remain (sequential-log aggregation); alto full-pipeline commit landed.

## 2026-06-03
- **#9** — nlp-enrich commit adds licensed paradata for API scripts + keyword extraction (LLM samples to follow).

## 2026-06-08
- **#16** — Full current-state inventory of every `data_samples/` dir; alto & nlp **resolved to contain only synthetic data**; translator still holds 16 real ARUP/B source documents; page-classification has ~245 PNGs across 11 category folders.

## 2026-06-10
- **#6** — License summary (from #9) implemented for all four repos; TODO to attach the list to the SSHOMP workflows.
- **#9** — Only nlp-enrich remains (LLM samples); all-stage merging done.
- **#18** — Opus strategy: repos are already pre-wired — `atrium_paradata.py` reads `ATRIUM_RUNNER_IMAGE/REPO/REF`, so GHCR-published self-identifying containers are the plan.

## 2026-06-12
- **#9** — Merged paradata for nlp stages 1–4 + one keyword method; all seven checklist items marked done.
- **#10** — Plan to review each repo with Fable by 22 June.
- **#18** — Per-repo Docker drafts summarised (shared template, per-repo knobs); motyc: discuss orchestration with rharasim, no overall wrapper needed (containers reachable via API).
- **#21 LINDAT annotated dataset release** — Opened by K4TEL: two ways to fix the licensing problem (modify old handle vs publish new + redirect); per-file metadata fields; sample JSON/CSV; motyc OK with option 1, notes some files can't be openly published (metadata-only).

## 2026-06-14
- **#21** — Posted the 82 GB ready-to-publish `licensed_archives/` listing: `CITATION.cff`, CC BY-NC `LICENSE`, per-document licensed CSV/JSON, cross-val folds, category ZIPs, and a `not_included` CSV for disallowed-license files.

## 2026-06-15
- **#10** — Released alto v0.17.0, page-classification v1.4.0-beta, translator v0.6.0, nlp v0.12.0 with LLM-review edits applied (Fable was unavailable 😮‍💨).
- **#18** — translator & page-classification passed GH Actions; posted the "Align & Expand Docker + GHA" strategy (one reusable workflow template + thin per-repo callers).

## 2026-06-16
- **#9** — Old paradata files to be replaced and `para_config` versions bumped across all four repos.
- **#10** — Defined the next review round's aspects: Docker+GHA, merged pipeline & API, per-function test coverage, architecture, file tree, CONTRIBUTING release history, + a per-repo review plan.
- **#18** — Commit `676a1fe` lands the centralized DRY CI/CD (`ci-cd-strategy.md`, `docker-tool.reusable.yml`, caller example, shared `.coveragerc`/`ruff.toml`, dependabot appendix); all four repos pass GHA; docs updated for rharasim to test.

## 2026-06-17
- **#10** — Combined per-repo review plan committed (`aba539e`); posted the post-review validation matrix (Tier-1 compileall/ruff + Tier-2 pytest/coverage, run pc→alto→nlp→translator).
- **#22 Document Understanding eval** — Opened by K4TEL (benchmark for document understanding — OmniDocBench?). Gemini "Deep Research" report posted; Opus 4.8 follow-up corrected its fabrications/mis-attributions, separated parsing-fidelity from semantic understanding, flagged **CHURRO/CHURRO-DS** as the real historical-doc match, and recommended an OOTB-VLM-vs-legacy-pipeline comparison first.

## 2026-06-19
- **#4** — SSHOMP tool records updated with license tables.
- **#6** — TODO to attach license lists to the marketplace workflows; new versions to be set by admins on the default tool views.
- **#21** — Major licensing discussion: 318 unpublishable files (<0.01%) removed; CC BY-NC vs BY-NC-SA debated (stranak/motyc lean to dropping SA → plain NC, citing EOSC/Open-Access policy); tombstone + "incomplete dataset" metadata text drafted; link replacements queued for arXiv/README/Zenodo. stranak already published the record; license to be swapped.
- **#22** — stranak: when running a big VLM (e.g. MiniMax-M3), contact Viktor about vLLM on the reserved Grace Hopper machine.
- **#24 LLM applications to data** — Opened by K4TEL (various local/remote LLM tasks).

## 2026-06-20
- **#21** — motyc proposed Description-field text (318 files, accessible under conditions at digiarchiv, GitHub repo for full pipeline).
- **#26 Run models larger than GPU memory via CPU** — Opened by K4TEL (explore unified-memory mechanism).
- **#27 H100 multi-GPU runs** — Opened by K4TEL (MiniMax-M3 FP8 ~440 GB on a single multi-GPU node).

## 2026-06-21
- **#6** — Admins to update default tool versions; license tables added to each SSHOMP description.
- **#10** — Opus 4.8 review round: new findings — `/info` version drift, `para_licenses.py` diverged + zero tests, nlp ruff blocking, secret-scanning unverified; posted a phased strategy.
- **#18** — Further GHA-integration strategy (Codecov gate bug, `@main` vs `@test` pin drift, action version floor, per-repo P0/P1/P2); all four repos released as vX.Y.Z+1 passing ruff/pre-commit.
- **#26** — Opus recommendation: vLLM `cpu_offload_gb` (UVA zero-copy) over Ollama layer-split or raw CUDA UVM — memory-only offload keeps CPU cores free for the existing queue.
- **#27** — Opus recommendation: 8×80 GB H100 SXM5, vLLM/SGLang tensor-parallel-size 8 + expert-parallel + fp8 KV cache, capped `max-model-len`; support is brand-new (use nightly/Docker).

## 2026-06-22
- **#21** — kosarko, stranak and motyc debate whether the corrected dataset record even needs the 318-files warning (agreed it belongs on the *models*/tombstone, while keeping it discoverable via the `not_included` CSV).

## 2026-06-23
- **#10** — `docs/plan_repo_review.md` declared the canonical plan to execute across the whole ecosystem.
- **#13** — Handle/DOI to be replaced in the Overleaf bibliography (marked DONE).
- **#15** — Dataset reference to be replaced in the post-review IJDL edit; arXiv preprint to be updated.
- **#16** — #21 designated the canonical "where licensed samples are shared" reference; motyc: keep open until end of project.
- **#21** — Links updated in both arXiv papers, the README, and the Zenodo DOI (one un-editable spot remains: the official CU MFF thesis record).

## 2026-06-24
- **#21** — kosarko refined the Description wording (bolded "318 files" claim to fact-check); K4TEL confirmed the 318 count via `wc -l` on the CSVs; stranak proposed keeping the original dataset (restricted, incl. the 318 files) **plus** a CC-only derived subset, linked together.

## 2026-06-25
- **#15** — arXiv `2606.07558` updated with the new dataset link (references only).
- **#16** — Both arXiv versions (`2507.21114`, `2606.07558`) updated with the new dataset licensing link.
- **#29 Add `agent_dev_logs` directory per repo** — Opened by K4TEL (this initiative): per-repo markdown dev logs on `test`, seeded from issue history, replacing agent work-documentation in issue comments.

## 2026-06-26
- **#10** — Opus 4.8 follow-ups consolidated: nlp shellcheck RED, `/info` version drift in pc + translator APIs, `para_licenses.py` dedup landed only in alto (divergent elsewhere, zero tests everywhere), nlp ruff blocking against the advisory-first policy, secret scanning unverified; `docs/plan_repo_review.md` re-confirmed as the single source of truth for the 5-phase remediation.
- **#18** — Opening task list checked off — ✅ docker builds on new tags/releases, ✅ test-set coverage for new commits + report generation, ✅ pip dependency updates. **Proposal**: an end-to-end integration smoke test (single-page ALTO → postprocess → translate → enrich → TEITOK) run in CI — no issue tracks pipeline-wide regression yet.

## 2026-06-27
- Cross-repo state digest **`digests/project_state_2706.md`** committed: distributed architecture, per-phase repo state, bottlenecks/risks, priority action map, and the test-branch HEAD table; all five repos' `test` branches updated the same day.

## 2026-06-28
- **#18** — Caller workflows renamed to the `.caller.example.yml` suffix (`4340a21`); `security.caller.example.yml` dropped.

## 2026-06-29
- **#24** — Proposed spinning the LLM subtasks into a separate repository.

## 2026-07-01
- **#24** — `atrium-llm-enrich` built out end to end under `K4TEL/` per `plans/24.plan.md`: engine byte-identical from nlp-enrich, OpenRouter/Ollama/local (transformers/vLLM/BnB) backends behind `llm_client_shared.py`, rewritten multi-stage Dockerfile, 8 GHA workflows + dependabot, compose files, tests.

## 2026-07-02
- **#24** — Draft repo announced in the issue thread ("created a draft repo").

## 2026-07-03
- **#24** — Review pass over the 4 new modules; client tests (`29ae7d8`); repo **transferred `K4TEL` → `ufal`**; suite at 47 tests at review time.

## 2026-07-06
- **#22** — [`opendatalab/MinerU`](https://github.com/opendatalab/mineru) flagged as an open-source parser candidate producing Markdown (relevant to the Markdown-bridge route).

## 2026-07-12
- **#18** — Cross-cutting template bugs all **fixed on HEAD**: the Codecov secrets-context gate, the action-version floor (versions bumped in the yml files), and the caller renames; `paradata-drift` renamed **`para-drift.reusable.yml`** with **license-parity steps by default** (`para_licenses.py` / `tests/test_para_licenses.py` diffed against `docs/templates/shared/`); `docs/docker_gha.md` refreshed. Remaining: translator pilot caller verification, rharasim end-to-end run, and the pipeline-wide smoke test.
- **#22** — Benchmark-harness primitives landed in `ufal/atrium-llm-enrich` (`f2ec956`): `eval_metrics.py` (CER/WER, normalized edit distance, entity F1 aligned to CNEC/TEATER, optional TEDS) + `sample_stratify.py` (quality-stratified page sampling from alto per-page stats, 80/10/10 manifest). Tier thresholds remain uncalibrated placeholders pending real-corpus calibration.
- **#24** — llm-enrich suite at **83 tests** (license test `83d7480` + client tests since the 07-03 review); the real per-`MODEL_KEY` licensing pass with DanaKriv still pending (hub #9 precedent); repo-side follow-ups now tracked in [`ufal/atrium-llm-enrich#8`](https://github.com/ufal/atrium-llm-enrich/issues/8) (opened today).
- **#4** — Digest rewritten (the previous file was a stray copy of the *translator* #4 digest): all four SSHOMP tool records live with license tables; the workflow-records item stays parked on the marketplace 500 error.
- **agent_dev_logs** — Full cross-repo digest/plan refinement pass: 27 files refreshed against live issue exports + repo HEADs across all six repos (residual-staleness audit clean); per-repo DEVLOG timeline indexes refreshed (this file included). Known gap: `atrium-nlp-enrich` **#11** has no issue-log export yet.

## 2026-07-17
- **#31** — Opened (AGENT SKILL — API service as installable skill per repo); strategy session: all six repos surveyed, exemplar `agent-skill` branch dissected (4 defects catalogued), normative standard authored as `docs/agentskillstrategy.md`; `plans/31.plan.md` + `digests/31.digest.md` committed.

## 2026-07-18
- **#31** — **Full rollout executed across all five service repos** (working branches `claude/issue-31-strategy-execution-bkq69f`, pending review/push): page-classification exemplar hardened (§10.1 — 4 defects fixed, `/health` added, `/info` meta-contract, 415 alignment); nlp-enrich first full skill run (§10.2 — SKILL.md, `atrium_enrich.py` with sync/jobs/stdin/zip modes, `server.sh`, samples, branch README, 2 frontend API footers, `/info` endpoints); alto-postprocess (§10.3 — **missing `process_alto`/`process_text_file` implemented** (the `/process` endpoint was calling nonexistent methods — hermetic tests masked it via `create=True`), `/health`, CORS `*`, `MAX_UPLOAD_MB`, skill layer); translator (§10.4 — first `service/README.md`, first `service/frontend/`, `/health`, 400→422, `MAX_UPLOAD_MB` with deprecated-fallback, skill layer); llm-enrich (§10.5 — new torch-free `service/api.py` (`/extract_keywords[_text]`, `/info`, `/health`), Docker `api` stage/profile, 8 passing contract tests, skill layer; `backend=local` stays CLI-only → 501). Hub: Appendices A–D promoted to `docs/templates/skill/` with 6 corrections from the run; `skill-validate.reusable.yml` + caller example added (§12.3 checks 1–3). Deferred: branch trims (`tests/`, CI configs, `data_samples/` — blocked in-session, exact `git rm` lists in the session report), sub-issue creation (§13), smoke runs against live servers.
- **#31** — Maintainer (k4tel) landed the missing-file backfill and the trim/refinement pass directly on all five `agent-skill` branches (11:52–13:5x UTC), then (17:35 UTC) pushed `skill-validate.reusable.yml` to hub `test`/`main` and a `.github/workflows/skill-validate.yml` caller to each `agent-skill` branch — landed byte-identical to what was authored/delivered. Hub also received `docs/agent_skill_strategy.md`, `docs/skills_catalog.md`, `docs/skill_acceptance_runbook.md` (renamed with underscores from the delivered hyphenated originals) and the refined `31.digest.md`/`31.plan.md`, with all 35 §10 checkboxes marked `[x]`.

## 2026-07-20
- **#31 (verification pass)** — Checked live state against hub `main`/`test` (`33b79c0`) and all 5 `agent-skill` HEADs via the GitHub API. Confirmed: CI infra landed correctly, but **every first CI run failed with 0 jobs** — the 5 caller pushes (~11:5x UTC 07-18) predated the reusable workflow's landing on `test` (17:35 UTC same day), so `uses: …@test` didn't resolve; no branch has re-pushed since, so CI has never run against working infra. Also found and fixed: `docs/templates/skill/` was missing 4 of 5 template files (only `atrium_client.skeleton.py` landed); `docs/templates/workflows/skill-validate.caller.example.yml` and `.gitignore` were absent from the hub; the doc renames (adding underscores) left `digest.md`/`plan.md` cross-links pointing at 404s. Confirmed still open: `atrium-page-classification@vit` (default branch) has not received the §10.1 `/health`/`/info` fixes — they exist only on `agent-skill` (the §12.2 manual merge-forward is outstanding); `atrium-llm-enrich@main` still has no contract test; no version tags exist. Could not verify or create GitHub sub-issues (§13) — `list_issues`/`create_issue` return `403 Resource not accessible by integration` for this session's GitHub App on every repo tried. Also could not trigger CI reruns (`403` on `rerun_workflow_run`).

## 2026-07-22
- **#31 (finalization pass)** — Residual meta-contract drift closed on all five `agent-skill` branches and **pushed**: page-classification lost its residual test tooling (`setup/requirements-test.txt` + its two Dockerfile refs); nlp-enrich gained `415` for unsupported uploads, exemplar CORS and API-usage footers on **both** frontends; alto-postprocess got `415`, client-fault `500`→`422`/`415`, a unified `/static`→`/frontend` mount and a **frontend response-schema fix** (both variants still rendered the old `{type, cleaned_lines, raw_text}` shape against the real `/process` response); translator narrowed CORS to `GET/POST`; llm-enrich a SKILL.md typo; hub fixed two stale doc links. The 07-18 "0 jobs" timing failure is gone — `skill-validate` green from run #2/#3 on every branch.
- **#10** — `digests/project_state_2207.md` committed, then independently re-verified the same day (corrected edition): **T1** (alto's malformed `v1.0.0.-beta`) and **T2** (llm-enrich stale `date-released`) had already self-resolved via same-day `v1.1.0-beta` / `v0.3.0` releases the write-up hadn't caught; **T3** (nlp release tagged `v1.16.2` against source `0.16.2`) confirmed open; new **T5**: the digest cadence cannot keep pace with the release cadence, so any "latest release" table is a lower bound. nlp re-published the release correctly as **`v0.16.2`** (13:51Z) the same afternoon.
- **#22** — Feedback from Alfie on the whole DU pipeline: Markdown over HTML+CSS as the LLM-facing format (token efficiency, training exposure), layout-aware PDF extraction over raw text pulls, python-docx/Pandoc for DOCX (watch embedded tables + tracked changes), a per-document metadata header (YAML frontmatter or JSON sidecar) as the backbone of a "roadmap-then-retrieve" index, and inline JSON/CSV for merged-cell tables. Confirms the direction of `atrium-llm-enrich` #10/#11.

## 2026-07-23
- **#32 Opened — "API services per repo should be standardized"** (K4TEL): the five `service/` dirs up for review, **OpenAPI** to be followed. Audit of the `test` HEADs against `agent_skill_strategy.md` §4 found only nlp-enrich reporting `service`+`limits` with a `/health`; no service listed `endpoints`; translator keyed the id as `name`, alto as `status`; translator returned 400 (not 422) for non-XML, alto **500** for missing upload metadata; llm-enrich had **no service at all**.
- **#32** — **Implemented and landed the same day** on all five `test` HEADs + the hub: shared `service/atrium_service.py` (hub canonical, byte-identical copies, guarded by `para-drift`) providing `build_info`/`attach_health`/`resolve_max_upload_mb`/`add_cors`; `/info` envelope + `/health` (shallow + `?deep=true`) everywhere; §4.4 error codes harmonized (translator 400→422, alto 500→4xx + a 413 guard); canonical `MAX_UPLOAD_MB`/`ALLOWED_ORIGINS`; a **new torch-free llm-enrich `service/`** (`/extract_keywords`, `/extract_keywords_text`) with a Docker `api` stage and compose profile; hermetic `tests/test_api_contract.py` per repo + hub `api-contract.reusable.yml`; `plan_repo_review.md` §5.A. A gap-closing pass then traced every "0 jobs" api-contract failure to a **malformed hub reusable** (duplicated `name:`/`on:`/`jobs:` tail — not the `uses:@test` timing first assumed) and found four more defects: pc's caller filename `api-contract.ym;`, empty `requirements-test.txt` in pc + alto, the module-skip→`pytest` exit-5 false failure, and llm-enrich's `service/requirements.txt` committed as `service/atriumllmenrich__service__requirements.txt`.
- **#18** — `HF_TOKEN` and `OPENROUTER_KEY` added as repo secrets in llm-enrich and page-classification.

## 2026-07-24
- **#31** — "The OpenAPI meta-contract integration (#32) is effectively complete across the ecosystem"; the #32 contract was ported onto all five `agent-skill` branches, each re-validating green.
- Hub — digests + plans refreshed for **#13**, **#31** and **#32**.

## 2026-07-25
- **Release wave — "OpenAPI standards draft + GHA release edit"**: translator `v0.9.0`, page-classification `v1.6.0-beta` (+ `vX.4` licensed-dataset models), nlp-enrich `v0.17.0`, alto-postprocess `v1.2.0-beta` → `v1.2.1-beta` (Dockerfile requirements fix), llm-enrich `v0.4.0` (+ PDF/DOCX→Markdown converter drafts).
- Hub — cross-repo document-handling draft added; schema docs renamed (`docs/document_schema.md`, `docs/paradata_schema.md`); the E2E smoke fixed for alto's refactored `langID` filenames.

## 2026-07-26
- **`atrium_document` JSON input/output integrated as a draft across the whole pipeline**: alto `v1.3.0-beta`, nlp `v0.18.0`, page-classification `v1.7.0-beta`, translator `v0.10.0`. The hub promotes `atrium_document.py` + `atrium_document.schema.json` into `docs/templates/shared/` and adds a `para-drift` parity step for them, so the document schema is now enforced the same way the paradata trio is.

## 2026-07-27
- **#18** — `GH2MD_READ_ACCESS` added to the hub secrets for issue retrieval. GPT-High's per-repo secret-scoping plan posted: hub = coordination/release + issue-log regeneration only, llm-enrich = `OPENROUTER_KEY`/`HF_TOKEN` (the only place external models are called), page-classification = `HF_TOKEN` only; the local `update_issues.sh` to become a repo-owned workflow that opens a docs-refresh PR instead of carrying a personal token in a shell script. Draft `issue-log-refresh.yml` added.
- E2E data sample refreshed from alto-postprocess.

## 2026-07-28
- **alto-postprocess `v1.4.0-beta`** — per-line categorisation calibration requested by the data providers, contributed by **david-spacil** (PR #32; first contribution from outside the core team).
- Hub — CSV fixture headers aligned with alto-postprocess.

## 2026-07-29
- **#31 (re-audit)** — `test` had moved on since 07-24 (the #13 document accretion wired into llm-enrich, translator and alto `service/`, two minor bumps per repo), so the skill branches had **re-drifted**. §12.3 **step 4 implemented** as two passes — **4a** static and zero-dependency (documented `GET /x` vs route decorators/mounts), **4b** boots the app and asserts the §4.1 `/info` envelope, `/health`, documented endpoints and spec validity, import-skipping the model-heavy repos with a CI *warning* so a skip cannot read as a pass. `skill_drift_check.py` + `skill_ify.py` written; strategy doc §3/§5/§12.2/§12.3 updated; maintainer landed the reusable, the doc and all five callers byte-identical. **nlp-enrich content aligned** (`1a8ff2c`, drift 22 → 3 files) after the audit found its service runtime is reached by **subprocess, not import**, and had gone stale: a preflight demanding an `analyze.py` that exists on no branch, `config_api.txt` pinning the **older NameTag model** (`nametag3-czech-cnec2.0-240830` vs test's `nametag3-multilingual-onto-260521`), and `yake`/`keybert`/`sentence-transformers` imported but undeclared. All five `skill-validate` runs green (pc #5, alto #5, nlp #7, translator #4, llm #4).
- First wave of the GHA/Docker overhaul pushed across the five tool repos.

## 2026-07-30
- **#18 — full GHA + Docker audit landed and verified.** Real defects fixed: page-classification's `release.yml` shipped `run.py` without the **9 first-party modules it imports transitively** (plus a dependency-free closure guard so a broken bundle fails the release); the hub E2E gated stage 5 on a secret that never existed (`OPENROUTER_API_KEY` vs the real `OPENROUTER_KEY`) so **the `llm` stage skipped silently every night while the run reported success**; two committed `.caller.yml` workflows that called nothing; llm-enrich's `api-contract` triggering on a `master` branch it does not have; and three fatal defects in `issue-log-refresh.yml` (reads `GITHUB_ACCESS_TOKEN` not `GH_TOKEN`, `output_path` is positional, needs `pull-requests: write`). Coverage gaps closed: PR triggers aligned to push triggers in all five repos, GPU crons removed (no GPU runner exists, so **no `slow`-marked test had ever run**), smoke-failure notifications ported to llm-enrich + nlp-enrich, and the container scan moved inside `build-and-push` addressed by **immutable digest** so it can no longer race the image it scans. Structural: `secrets: inherit` eliminated from all 10 callers, ~200 lines of duplicated version-guard collapsed into one vendored `docs/templates/shared/check_version.py` held byte-identical by `para-drift`, `timeout-minutes` on 45 runner jobs (was 0 of 53) and concurrency groups on 33 workflows, SBOM/provenance via buildkit attestations, every action on a single major, lint blocking in all five repos, and the three missing caller examples added. Two regressions along the way, both fixed: `docker.yml` `startup_failure` in all five repos (a reusable's permissions are **capped by the calling job's grant**, so the new `security-events: write` had to be granted caller-side) and llm-enrich's `build-targets` briefly lost, which would have published an entrypoint-less `base` image. **Verified**: nightly E2E run [`30515547822`](https://github.com/ufal/atrium-project/actions/runs/30515547822) exercised all five stages for real (~4 min), `para-drift` holds byte-identically across all five repos, concurrency cancellation observed live. **Open**: the release path has never run (five tag-gated guards unexercised — pilot with translator), the `@v1` reusable pin + branch protection, `codeql`/`pre-commit` reusables deferred behind that pin, the GPU runner, and the Trivy `exit-code: 0` / gitleaks policy calls.
- **agent_dev_logs** — Timeline index and cross-repo state refreshed against live repo/CI state (`digests/project_state_3007.md`). New findings that pass surfaced: page-classification's `test` **Docker Build & Publish is red** (a dependabot `numpy>=2.5.1` bump against the pinned Python 3.11), its `service/requirements.txt` no longer carries the service runtime (no `uvicorn`), the hub's `skill_drift_check.py`/`skill_ify.py` landed under `docs/templates/skill/` while every citation points at `tools/`, and `issue-log-refresh.yml` has still never run.

---
_Timeline index refreshed 2026-07-30 against live `test`/default HEADs, the release/CI state of all six repos, and the issue exports regenerated the same morning. Nothing removed from the issues themselves (per #29); this file is a derived reading aid in `agent_dev_logs/`._
