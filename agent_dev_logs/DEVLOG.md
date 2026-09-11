# 📓 atrium-project — agent_dev_logs/DEVLOG.md (timeline index)
> _Hub/planning repo. 21 open issues. `test`==`main` HEAD `bbcdf58` (2026-09-09) · tag `v1` moving with it._
> _Per-issue detail: `digests/{id}.digest.md` · `plans/{id}.plan.md` · `issues/` exports (source of truth). Cross-repo snapshot: `digests/project_state_0709.md` (prior: `project_state_3007.md`, `project_state_0208.md`, `project_state_2207.md`, `project_state_1307.md`, `project_state_2706.md`)._

## 2026-03-13
- **#4 SSH Open Marketplace records** — Opened by stranak: create SSHOMP records for every tool in our workflows (UDPipe ✅,
NameTag ✅, rest TBD).
- **#6 Review & summarise licenses** — Opened by stranak (review tool+model licenses, check where CC-BY-NC-SA is required).
K4TEL posted the first license inventory: FastText/AMCR-vocab CC BY-NC, layoutreader CC BY-NC-SA,
distilgpt2/alto-tools/GLM/Qwen2.5 Apache-2.0, ViT/EffNet/RegNet/CLIP MIT, NameTag3/CUBBITT CC BY-NC-SA, UDP2 MPL-2.0,
AISCR Teater GPL-3.0.
- **#9 Paradata of outputs** — Opened by K4TEL: unified run-logging (incl. output license) across all four tool repos.

## 2026-03-15
- **#4** — Page classifier added to SSHOMP as a Suggested Tool under the `ATRIUM catalogue` keyword.
- **#9** — Translator, textline & page classifiers tested with paradata output; basic `.json` paradata in all
repos via a shared `atrium_paradata.py`.
- **#10 LLM validation of source code** — Opened by K4TEL (validate every repo's source with an LLM).

## 2026-03-22
- **#10** — All projects checked with Sonnet 4.6 Extended, then re-checked with Gemini 3.

## 2026-03-25
- **#13 CAA Proceedings paper to PCJ** — Opened by K4TEL: submit a paper to the CAA2026 proceedings / PCI Archaeology;
text draft posted (5000-word limit, no figures yet).

## 2026-03-26
- **#13** — Added the full project diagram, an updated report PDF with the diagram inserted, and a Zenodo submission draft.

## 2026-04-04
- **#13** — Overleaf editor invites sent to David and Dana; CAA-proceedings project + Springer extended-version
project to be reformatted into CAA styles.

## 2026-04-11
- **#4** — The remaining three repositories suggested as SSHOMP tools.

## 2026-04-16
- **#4** — ALTO post-processor, NLP enrichment, translator and page classifier all uploaded as tool-or-service under
the **ATRIUM catalogue** tag.

## 2026-05-13
- **#13** — motyc: proceedings deadline is **31 October 2026**.

## 2026-05-27
- **#15 Submission to IJDL** — Opened by motyc (review ASAP, link in the minutes).
- **#16 List ARUP/B data storage locations** — Opened by motyc (so ARUP/B can later remove all copies). K4TEL listed
the `data_samples` dirs across repos, the LINDAT annotated dataset, thesis/presentation page samples, and the UFAL filesystem.
- **#17 Review SSHOMP workflow descriptions** — Opened by motyc.
- **#18 Docker compose + GH action wrapper for CU forks** — Opened by motyc (links the four ARUP-CAS forks).

## 2026-05-28
- **#9** — Mass→single-file paradata records merged per repo; open questions on license source, missing tool-version
tag, dynamic runner reference, and a Docker-image placeholder.
- **#10** — Slated for re-examination by Opus 4.7 and Sonnet 4.6 across all four repos.
- **#17** — K4TEL posted the four marketplace tool links; motyc thanked; noted relation to #4.

## 2026-05-29
- **#9** — Detailed per-repo license breakdown: the tool-vs-model split (NameTag3/UDPipe engines MPL-2.0 but their
models CC BY-NC-SA), Teater app GPL vs data CC BY-NC, and the internal-academic-use vs external-commercial-use distinction.
- **#10** — motyc: "Opus 4.8 is just out :)".
- **#16** — Posted per-repo licensed-asset tables (alto 39, nlp 34, translator 14, page-classification 84 documents)
mapped to licenses from the global metadata collection.

## 2026-06-02
- **#9** — The two easy repos (translator, page-classification) updated with paradata licenses; the two multi-step
repos (alto, nlp) remain (sequential-log aggregation); alto full-pipeline commit landed.

## 2026-06-03
- **#9** — nlp-enrich commit adds licensed paradata for API scripts + keyword extraction (LLM samples to follow).

## 2026-06-08
- **#16** — Full current-state inventory of every `data_samples/` dir; alto & nlp **resolved to contain only
synthetic data**; translator still holds 16 real ARUP/B source documents; page-classification has ~245 PNGs across 11 category folders.

## 2026-06-10
- **#6** — License summary (from #9) implemented for all four repos; TODO to attach the list to the SSHOMP workflows.
- **#9** — Only nlp-enrich remains (LLM samples); all-stage merging done.
- **#18** — Opus strategy: repos are already pre-wired — `atrium_paradata.py` reads `ATRIUM_RUNNER_IMAGE/REPO/REF`,
so GHCR-published self-identifying containers are the plan.

## 2026-06-12
- **#9** — Merged paradata for nlp stages 1–4 + one keyword method; all seven checklist items marked done.
- **#10** — Plan to review each repo with Fable by 22 June.
- **#18** — Per-repo Docker drafts summarised (shared template, per-repo knobs); motyc: discuss orchestration with
rharasim, no overall wrapper needed (containers reachable via API).
- **#21 LINDAT annotated dataset release** — Opened by K4TEL: two ways to fix the licensing problem (modify old handle
vs publish new + redirect); per-file metadata fields; sample JSON/CSV; motyc OK with option 1, notes some files can't be openly published (metadata-only).

## 2026-06-14
- **#21** — Posted the 82 GB ready-to-publish `licensed_archives/` listing: `CITATION.cff`, CC BY-NC `LICENSE`,
per-document licensed CSV/JSON, cross-val folds, category ZIPs, and a `not_included` CSV for disallowed-license files.

## 2026-06-15
- **#10** — Released alto v0.17.0, page-classification v1.4.0-beta, translator v0.6.0, nlp v0.12.0 with LLM-review
edits applied (Fable was unavailable 😮‍💨).
- **#18** — translator & page-classification passed GH Actions; posted the "Align & Expand Docker + GHA" strategy
(one reusable workflow template + thin per-repo callers).

## 2026-06-16
- **#9** — Old paradata files to be replaced and `para_config` versions bumped across all four repos.
- **#10** — Defined the next review round's aspects: Docker+GHA, merged pipeline & API, per-function test coverage,
architecture, file tree, CONTRIBUTING release history, + a per-repo review plan.
- **#18** — Commit `676a1fe` lands the centralized DRY CI/CD (`ci-cd-strategy.md`, `docker-tool.reusable.yml`, caller
example, shared `.coveragerc`/`ruff.toml`, dependabot appendix); all four repos pass GHA; docs updated for rharasim to test.

## 2026-06-17
- **#10** — Combined per-repo review plan committed (`aba539e`); posted the post-review validation matrix
(Tier-1 compileall/ruff + Tier-2 pytest/coverage, run pc→alto→nlp→translator).
- **#22 Document Understanding eval** — Opened by K4TEL (benchmark for document understanding — OmniDocBench?).
Gemini "Deep Research" report posted; Opus 4.8 follow-up corrected its fabrications/mis-attributions, separated
parsing-fidelity from semantic understanding, flagged **CHURRO/CHURRO-DS** as the real historical-doc match, and
recommended an OOTB-VLM-vs-legacy-pipeline comparison first.

## 2026-06-19
- **#4** — SSHOMP tool records updated with license tables.
- **#6** — TODO to attach license lists to the marketplace workflows; new versions to be set by admins on the default tool views.
- **#21** — Major licensing discussion: 318 unpublishable files (<0.01%) removed; CC BY-NC vs BY-NC-SA debated
(stranak/motyc lean to dropping SA → plain NC, citing EOSC/Open-Access policy); tombstone + "incomplete dataset"
metadata text drafted; link replacements queued for arXiv/README/Zenodo. stranak already published the record; license to be swapped.
- **#22** — stranak: when running a big VLM (e.g. MiniMax-M3), contact Viktor about vLLM on the reserved Grace Hopper machine.
- **#24 LLM applications to data** — Opened by K4TEL (various local/remote LLM tasks).

## 2026-06-20
- **#21** — motyc proposed Description-field text (318 files, accessible under conditions at digiarchiv,
GitHub repo for full pipeline).
- **#26 Run models larger than GPU memory via CPU** — Opened by K4TEL (explore unified-memory mechanism).
- **#27 H100 multi-GPU runs** — Opened by K4TEL (MiniMax-M3 FP8 ~440 GB on a single multi-GPU node).

## 2026-06-21
- **#6** — Admins to update default tool versions; license tables added to each SSHOMP description.
- **#10** — Opus 4.8 review round: new findings — `/info` version drift, `para_licenses.py` diverged + zero tests,
nlp ruff blocking, secret-scanning unverified; posted a phased strategy.
- **#18** — Further GHA-integration strategy (Codecov gate bug, `@main` vs `@test` pin drift, action version floor,
per-repo P0/P1/P2); all four repos released as vX.Y.Z+1 passing ruff/pre-commit.
- **#26** — Opus recommendation: vLLM `cpu_offload_gb` (UVA zero-copy) over Ollama layer-split or raw CUDA UVM —
memory-only offload keeps CPU cores free for the existing queue.
- **#27** — Opus recommendation: 8×80 GB H100 SXM5, vLLM/SGLang tensor-parallel-size 8 + expert-parallel + fp8 KV
cache, capped `max-model-len`; support is brand-new (use nightly/Docker).

## 2026-06-22
- **#21** — kosarko, stranak and motyc debate whether the corrected dataset record even needs the 318-files warning
(agreed it belongs on the *models*/tombstone, while keeping it discoverable via the `not_included` CSV).

## 2026-06-23
- **#10** — `docs/plan_repo_review.md` declared the canonical plan to execute across the whole ecosystem.
- **#13** — Handle/DOI to be replaced in the Overleaf bibliography (marked DONE).
- **#15** — Dataset reference to be replaced in the post-review IJDL edit; arXiv preprint to be updated.
- **#16** — #21 designated the canonical "where licensed samples are shared" reference; motyc: keep open until end of project.
- **#21** — Links updated in both arXiv papers, the README, and the Zenodo DOI (one un-editable spot remains: the
official CU MFF thesis record).

## 2026-06-24
- **#21** — kosarko refined the Description wording (bolded "318 files" claim to fact-check); K4TEL confirmed the
318 count via `wc -l` on the CSVs; stranak proposed keeping the original dataset (restricted, incl. the 318 files)
**plus** a CC-only derived subset, linked together.

## 2026-06-25
- **#15** — arXiv `2606.07558` updated with the new dataset link (references only).
- **#16** — Both arXiv versions (`2507.21114`, `2606.07558`) updated with the new dataset licensing link.
- **#29 Add `agent_dev_logs` directory per repo** — Opened by K4TEL (this initiative): per-repo markdown dev logs on
`test`, seeded from issue history, replacing agent work-documentation in issue comments.

## 2026-06-26
- **#10** — Opus 4.8 follow-ups consolidated: nlp shellcheck RED, `/info` version drift in pc + translator APIs,
`para_licenses.py` dedup landed only in alto (divergent elsewhere, zero tests everywhere), nlp ruff blocking against
the advisory-first policy, secret scanning unverified; `docs/plan_repo_review.md` re-confirmed as the single source
of truth for the 5-phase remediation.
- **#18** — Opening task list checked off — ✅ docker builds on new tags/releases, ✅ test-set coverage for new commits +
report generation, ✅ pip dependency updates. **Proposal**: an end-to-end integration smoke test (single-page ALTO →
postprocess → translate → enrich → TEITOK) run in CI — no issue tracks pipeline-wide regression yet.

## 2026-06-27
- Cross-repo state digest **`digests/project_state_2706.md`** committed: distributed architecture, per-phase repo
state, bottlenecks/risks, priority action map, and the test-branch HEAD table; all five repos' `test` branches updated the same day.

## 2026-06-28
- **#18** — Caller workflows renamed to the `.caller.example.yml` suffix (`4340a21`); `security.caller.example.yml` dropped.

## 2026-06-29
- **#24** — Proposed spinning the LLM subtasks into a separate repository.

## 2026-07-01
- **#24** — `atrium-llm-enrich` built out end to end under `K4TEL/` per `plans/24.plan.md`: engine byte-identical
from nlp-enrich, OpenRouter/Ollama/local (transformers/vLLM/BnB) backends behind `llm_client_shared.py`, rewritten
multi-stage Dockerfile, 8 GHA workflows + dependabot, compose files, tests.

## 2026-07-02
- **#24** — Draft repo announced in the issue thread ("created a draft repo").

## 2026-07-03
- **#24** — Review pass over the 4 new modules; client tests (`29ae7d8`); repo **transferred `K4TEL` → `ufal`**;
suite at 47 tests at review time.

## 2026-07-06
- **#22** — [`opendatalab/MinerU`](https://github.com/opendatalab/mineru) flagged as an open-source parser candidate producing Markdown (relevant
to the Markdown-bridge route).

## 2026-07-12
- **#18** — Cross-cutting template bugs all **fixed on HEAD**: the Codecov secrets-context gate, the action-version
floor (versions bumped in the yml files), and the caller renames; `paradata-drift` renamed **`para-drift.reusable.yml`**
with **license-parity steps by default** (`para_licenses.py` / `tests/test_para_licenses.py` diffed against
`docs/templates/shared/`); `docs/docker_gha.md` refreshed. Remaining: translator pilot caller verification, rharasim
end-to-end run, and the pipeline-wide smoke test.
- **#22** — Benchmark-harness primitives landed in `ufal/atrium-llm-enrich` (`f2ec956`): `eval_metrics.py` (CER/WER,
normalized edit distance, entity F1 aligned to CNEC/TEATER, optional TEDS) + `sample_stratify.py` (quality-stratified
page sampling from alto per-page stats, 80/10/10 manifest). Tier thresholds remain uncalibrated placeholders pending real-corpus calibration.
- **#24** — llm-enrich suite at **83 tests** (license test `83d7480` + client tests since the 07-03 review); the real
per-`MODEL_KEY` licensing pass with DanaKriv still pending (hub #9 precedent); repo-side follow-ups now tracked in
[`ufal/atrium-llm-enrich#8`](https://github.com/ufal/atrium-llm-enrich/issues/8) (opened today).
- **#4** — Digest rewritten (the previous file was a stray copy of the *translator* #4 digest): all four SSHOMP tool
records live with license tables; the workflow-records item stays parked on the marketplace 500 error.
- **agent_dev_logs** — Full cross-repo digest/plan refinement pass: 27 files refreshed against live issue exports +
repo HEADs across all six repos (residual-staleness audit clean); per-repo DEVLOG timeline indexes refreshed (this
file included). Known gap: `atrium-nlp-enrich` **#11** has no issue-log export yet.

## 2026-07-17
- **#31** — Opened (AGENT SKILL — API service as installable skill per repo); strategy session: all six repos surveyed,
exemplar `agent-skill` branch dissected (4 defects catalogued), normative standard authored as `docs/agentskillstrategy.md`;
`plans/31.plan.md` + `digests/31.digest.md` committed.

## 2026-07-18
- **#31** — **Full rollout executed across all five service repos** (working branches `claude/issue-31-strategy-execution-bkq69f`,
pending review/push): page-classification exemplar hardened (§10.1 — 4 defects fixed, `/health` added, `/info` meta-contract,
415 alignment); nlp-enrich first full skill run (§10.2 — SKILL.md, `atrium_enrich.py` with sync/jobs/stdin/zip modes,
`server.sh`, samples, branch README, 2 frontend API footers, `/info` endpoints); alto-postprocess (§10.3 — **missing
`process_alto`/`process_text_file` implemented** (the `/process` endpoint was calling nonexistent methods — hermetic
tests masked it via `create=True`), `/health`, CORS `*`, `MAX_UPLOAD_MB`, skill layer); translator (§10.4 — first
`service/README.md`, first `service/frontend/`, `/health`, 400→422, `MAX_UPLOAD_MB` with deprecated-fallback, skill
layer); llm-enrich (§10.5 — new torch-free `service/api.py` (`/extract_keywords[_text]`, `/info`, `/health`), Docker
`api` stage/profile, 8 passing contract tests, skill layer; `backend=local` stays CLI-only → 501). Hub: Appendices
A–D promoted to `docs/templates/skill/` with 6 corrections from the run; `skill-validate.reusable.yml` + caller
example added (§12.3 checks 1–3). Deferred: branch trims (`tests/`, CI configs, `data_samples/` — blocked in-session,
exact `git rm` lists in the session report), sub-issue creation (§13), smoke runs against live servers.
- **#31** — Maintainer (k4tel) landed the missing-file backfill and the trim/refinement pass directly on all five
`agent-skill` branches (11:52–13:5x UTC), then (17:35 UTC) pushed `skill-validate.reusable.yml` to hub `test`/`main`
and a `.github/workflows/skill-validate.yml` caller to each `agent-skill` branch — landed byte-identical to what
was authored/delivered. Hub also received `docs/agent_skill_strategy.md`, `docs/skills_catalog.md`,
`docs/skill_acceptance_runbook.md` (renamed with underscores from the delivered hyphenated originals) and the
refined `31.digest.md`/`31.plan.md`, with all 35 §10 checkboxes marked `[x]`.

## 2026-07-20
- **#31 (verification pass)** — Checked live state against hub `main`/`test` (`33b79c0`) and all 5 `agent-skill`
HEADs via the GitHub API. Confirmed: CI infra landed correctly, but **every first CI run failed with 0 jobs** —
the 5 caller pushes (~11:5x UTC 07-18) predated the reusable workflow's landing on `test` (17:35 UTC same day), so
`uses: …@test` didn't resolve; no branch has re-pushed since, so CI has never run against working infra. Also
found and fixed: `docs/templates/skill/` was missing 4 of 5 template files (only `atrium_client.skeleton.py` landed);
`docs/templates/workflows/skill-validate.caller.example.yml` and `.gitignore` were absent from the hub; the doc renames
(adding underscores) left `digest.md`/`plan.md` cross-links pointing at 404s. Confirmed still open:
`atrium-page-classification@vit` (default branch) has not received the §10.1 `/health`/`/info` fixes — they exist
only on `agent-skill` (the §12.2 manual merge-forward is outstanding); `atrium-llm-enrich@main` still has no contract
test; no version tags exist. Could not verify or create GitHub sub-issues (§13) — `list_issues`/`create_issue` return
`403 Resource not accessible by integration` for this session's GitHub App on every repo tried. Also could not trigger
CI reruns (`403` on `rerun_workflow_run`).

## 2026-07-22
- **#31 (finalization pass)** — Residual meta-contract drift closed on all five `agent-skill` branches and **pushed**:
page-classification lost its residual test tooling (`setup/requirements-test.txt` + its two Dockerfile refs);
nlp-enrich gained `415` for unsupported uploads, exemplar CORS and API-usage footers on **both** frontends;
alto-postprocess got `415`, client-fault `500`→`422`/`415`, a unified `/static`→`/frontend` mount and a
**frontend response-schema fix** (both variants still rendered the old `{type, cleaned_lines, raw_text}` shape
against the real `/process` response); translator narrowed CORS to `GET/POST`; llm-enrich a SKILL.md typo; hub
fixed two stale doc links. The 07-18 "0 jobs" timing failure is gone — `skill-validate` green from run #2/#3 on every branch.
- **#10** — `digests/project_state_2207.md` committed, then independently re-verified the same day (corrected edition):
**T1** (alto's malformed `v1.0.0.-beta`) and **T2** (llm-enrich stale `date-released`) had already self-resolved via
same-day `v1.1.0-beta` / `v0.3.0` releases the write-up hadn't caught; **T3** (nlp release tagged `v1.16.2` against
source `0.16.2`) confirmed open; new **T5**: the digest cadence cannot keep pace with the release cadence, so any
"latest release" table is a lower bound. nlp re-published the release correctly as **`v0.16.2`** (13:51Z) the same afternoon.
- **#22** — Feedback from Alfie on the whole DU pipeline: Markdown over HTML+CSS as the LLM-facing format (token efficiency,
training exposure), layout-aware PDF extraction over raw text pulls, python-docx/Pandoc for DOCX (watch embedded tables +
tracked changes), a per-document metadata header (YAML frontmatter or JSON sidecar) as the backbone of a "roadmap-then-retrieve"
index, and inline JSON/CSV for merged-cell tables. Confirms the direction of `atrium-llm-enrich` #10/#11.

## 2026-07-23
- **#32 Opened — "API services per repo should be standardized"** (K4TEL): the five `service/` dirs up for review,
**OpenAPI** to be followed. Audit of the `test` HEADs against `agent_skill_strategy.md` §4 found only nlp-enrich
reporting `service`+`limits` with a `/health`; no service listed `endpoints`; translator keyed the id as `name`,
alto as `status`; translator returned 400 (not 422) for non-XML, alto **500** for missing upload metadata; llm-enrich
had **no service at all**.
- **#32** — **Implemented and landed the same day** on all five `test` HEADs + the hub: shared `service/atrium_service.py`
(hub canonical, byte-identical copies, guarded by `para-drift`) providing
`build_info`/`attach_health`/`resolve_max_upload_mb`/`add_cors`; `/info` envelope + `/health` (shallow + `?deep=true`)
everywhere; §4.4 error codes harmonized (translator 400→422, alto 500→4xx + a 413 guard); canonical
`MAX_UPLOAD_MB`/`ALLOWED_ORIGINS`; a **new torch-free llm-enrich `service/`** (`/extract_keywords`, `/extract_keywords_text`)
with a Docker `api` stage and compose profile; hermetic `tests/test_api_contract.py` per repo + hub `api-contract.reusable.yml`;
`plan_repo_review.md` §5.A. A gap-closing pass then traced every "0 jobs" api-contract failure to a **malformed hub reusable**
(duplicated `name:`/`on:`/`jobs:` tail — not the `uses:@test` timing first assumed) and found four more defects: pc's caller
filename `api-contract.ym;`, empty `requirements-test.txt` in pc + alto, the module-skip→`pytest` exit-5 false failure, and
llm-enrich's `service/requirements.txt` committed as `service/atriumllmenrich__service__requirements.txt`.
- **#18** — `HF_TOKEN` and `OPENROUTER_KEY` added as repo secrets in llm-enrich and page-classification.

## 2026-07-24
- **#31** — "The OpenAPI meta-contract integration (#32) is effectively complete across the ecosystem"; the
#32 contract was ported onto all five `agent-skill` branches, each re-validating green.
- Hub — digests + plans refreshed for **#13**, **#31** and **#32**.

## 2026-07-25

* **Release wave — "OpenAPI standards draft + GHA release edit"**: translator `v0.9.0`, page-classification `v1.6.0-beta`
(+ `vX.4` licensed-dataset models), nlp-enrich `v0.17.0`, alto-postprocess `v1.2.0-beta` → `v1.2.1-beta` (Dockerfile
requirements fix), llm-enrich `v0.4.0` (+ PDF/DOCX→Markdown converter drafts).
* Hub — cross-repo document-handling draft added; schema docs renamed (`docs/document_schema.md`, `docs/paradata_schema.md`);
the E2E smoke fixed for alto's refactored `langID` filenames.

## 2026-07-26

* **`atrium_document` JSON input/output integrated as a draft across the whole pipeline**: alto `v1.3.0-beta`,
nlp `v0.18.0`, page-classification `v1.7.0-beta`, translator `v0.10.0`. The hub promotes `atrium_document.py` +
`atrium_document.schema.json` into `docs/templates/shared/` and adds a `para-drift` parity step for them, so the
document schema is now enforced the same way the paradata trio is.

## 2026-07-27

* **#18** — `GH2MD_READ_ACCESS` added to the hub secrets for issue retrieval. GPT-High's per-repo secret-scoping
plan posted: hub = coordination/release + issue-log regeneration only, llm-enrich = `OPENROUTER_KEY`/`HF_TOKEN`
(the only place external models are called), page-classification = `HF_TOKEN` only; the local `update_issues.sh`
to become a repo-owned workflow that
opens a docs-refresh PR instead of carrying a personal token in a shell script. Draft `issue-log-refresh.yml` added.
* E2E data sample refreshed from alto-postprocess.

## 2026-07-28

* **alto-postprocess `v1.4.0-beta**` — per-line categorisation calibration requested by the data providers,
contributed by **david-spacil** (PR #32; first contribution from outside the core team).
* Hub — CSV fixture headers aligned with alto-postprocess.

## 2026-07-29

* **#31 (re-audit)** — `test` had moved on since 07-24 (the #13 document accretion wired into llm-enrich,
translator and alto `service/`, two minor bumps per repo), so the skill branches had **re-drifted**. §12.3
**step 4 implemented** as two passes — **4a** static and zero-dependency (documented `GET /x` vs route
decorators/mounts), **4b** boots the app and asserts the §4.1 `/info` envelope, `/health`, documented
endpoints and spec validity, import-skipping the model-heavy repos with a CI *warning* so a skip cannot
read as a pass. `skill_drift_check.py` + `skill_ify.py` written; strategy doc §3/§5/§12.2/§12.3 updated;
maintainer landed the reusable, the doc and all five callers byte-identical. **nlp-enrich content aligned**
(`1a8ff2c`, drift 22 → 3 files) after the audit found its service runtime is reached by **subprocess, not import**,
and had gone stale: a preflight demanding an `analyze.py` that exists on no branch, `config_api.txt` pinning the
**older NameTag model** (`nametag3-czech-cnec2.0-240830` vs test's `nametag3-multilingual-onto-260521`), and
`yake`/`keybert`/`sentence-transformers` imported but undeclared. All five `skill-validate` runs green (pc #5,
alto #5, nlp #7, translator #4, llm #4).
* First wave of the GHA/Docker overhaul pushed across the five tool repos.

## 2026-07-30

* **#18 — full GHA + Docker audit landed and verified.** Real defects fixed: page-classification's `release.yml`
shipped `run.py` without the **9 first-party modules it imports transitively** (plus a dependency-free closure guard
so a broken bundle fails the release); the hub E2E gated stage 5 on a secret that never existed (`OPENROUTER_API_KEY`
vs the real `OPENROUTER_KEY`) so **the `llm` stage skipped silently every night while the run reported success**; two
committed `.caller.yml` workflows that called nothing; llm-enrich's `api-contract` triggering on a `master` branch it
does not have; and three fatal defects in `issue-log-refresh.yml` (reads `GITHUB_ACCESS_TOKEN` not `GH_TOKEN`, `output_path`
is positional, needs `pull-requests: write`). Coverage gaps closed: PR triggers aligned to push triggers in all five repos,
GPU crons removed (no GPU runner exists, so **no `slow`-marked test had ever run**), smoke-failure notifications ported
to llm-enrich + nlp-enrich, and the container scan moved inside `build-and-push` addressed by **immutable digest** so
it can no longer race the image it scans. Structural: `secrets: inherit` eliminated from all 10 callers, ~200 lines
of duplicated version-guard collapsed into one vendored `docs/templates/shared/check_version.py` held byte-identical
by `para-drift`, `timeout-minutes` on 45 runner jobs (was 0 of 53) and concurrency groups on 33 workflows,
SBOM/provenance via buildkit attestations, every action on a single major, lint blocking in all five repos, and
the three missing caller examples added. Two regressions along the way, both fixed: `docker.yml` `startup_failure`
in all five repos (a reusable's permissions are **capped by the calling job's grant**, so the new `security-events: write`
had to be granted caller-side) and llm-enrich's `build-targets` briefly lost, which would have published an
entrypoint-less `base` image. **Verified**: nightly E2E
run [`30515547822`](https://www.google.com/search?q=https://github.com/ufal/atrium-project/actions/runs/30515547822)
exercised all five stages for real (~4 min), `para-drift` holds byte-identically across all five repos, concurrency
cancellation observed live. **Open**: the release path has never run (five tag-gated guards unexercised — pilot with
translator), the `@v1` reusable pin + branch protection, `codeql`/`pre-commit` reusables deferred behind that pin,
the GPU runner, and the Trivy `exit-code: 0` / gitleaks policy calls.
* **agent_dev_logs** — Timeline index and cross-repo state refreshed against live repo/CI state
(`digests/project_state_3007.md`). New findings that pass surfaced: page-classification's `test` **Docker Build &
Publish is red** (a dependabot `numpy>=2.5.1` bump against the pinned Python 3.11), its `service/requirements.txt`
no longer carries the service runtime (no `uvicorn`), the hub's `skill_drift_check.py`/`skill_ify.py` landed under
`docs/templates/skill/` while every citation points at `tools/`, and `issue-log-refresh.yml` has still never run.

## 2026-07-31

* **#18 Docker compose + GH action wrapper for CU forks** — Added tag `v1` to the `atrium-project` repository
and referenced this tag everywhere in other repositories, including `agent-skill` branches. CI hardening was
essentially completed, and the `test` branch was successfully merged to default in the five tool repositories.
Final releases were cut across the tool repositories (`v1.7.2-beta`, `v1.4.1-beta`, `v0.18.1`, `v0.5.0`, `v0.10.2`).
Remaining work includes branch protection on the hub's `main`/`test` branches and addressing the external GPU runner.

## 2026-08-01

* **#10 LLM validation of source code** — Added a TODO to review the JSON-based pipelines, the adaptation to the
`atrium_document` standard, and the current GHA workflows set in each repository.
* **#18 Docker compose + GH action wrapper for CU forks** — The E2E pipeline smoke test (`e2e-pipeline-smoke.yml`)
was rewritten by Sonnet to thread a document JSON through all five stages for real validation. Fixes were
successfully implemented for Stage 1's wrong input type, container-vs-runner permission mismatches, Stage 2's ALTO
config and missing stats dependency, Stage 3's baseline positional arguments, Stage 4's document-identity accretion
bug, and Stage 5's image and entrypoint issues. Contract bugs in `e2e_assert.py` were fixed, and the fixture was
switched back to the documented `CTX000000003`. A second E2E GHA script was added to run JSON-based (`e2e-pipeline-smoke.yml`)
and default pipelines (`all-repos-smoke.yml`) in parallel.
* **#22 Document Understanding - evaluation of out-of-the-box tools** — Referenced a relevant comment regarding
the document schema data format pipeline from issue #24.
* **#24 LLM applications to data** — Preliminary decisions were made regarding the data formats for the LLM processing
layers. The JSON format will contain all possible document information from prior processing steps. The MD(+HTML-CSS)
format will contain textual content, simplified table layouts, and figure regions without strict visual alignment.
The TEITOK XML format will contain visually correct XML elements that can be rendered on top of page images, including
NLP enrichment by default. A TODO was added to ensure JSON-2-MD and TEITOK-2-MD pipelines work correctly with fully
enriched JSONs and complex XMLs.
* **#31 AGENT SKILL - based on API service for each repo** — A TODO was added to make sure test and `agent-skill`
branches contain APIs accepting JSON inputs according to the `atrium_document` standard.
* **#32 API services per repo should be standartized - OpenAPI** — A duplicate TODO was noted to ensure test and
`agent-skill` branches contain APIs accepting JSON inputs according to the `atrium_document` standard.

## 2026-08-02

* **#40 CI/CD: Enforce Branch Protection (GH) & Enable GPU Runner (GHA)** — Opened by K4TEL: two infrastructure
gaps remain after the GHA/Docker hardening — an external GPU runner for `pytest -m slow`, and branch-protection
rules on the hub's `main`/`test`. @motyc pushes back on the GPU half same day: UFAL-profile GH Actions must not be
wired to any ARUP/B environment — the border is a Docker image built in ARUP/B's own fork and run on their
Kubernetes cluster, not live GPU access from this CI. If GPU testing is needed at all, it has to come from outside
this infrastructure; @stranak points at Metacentrum (`metavo.metacentrum.cz`, application-gated) as the e-INFRA.cz
GPU grid, and @motyc adds CERIT's n8n-agents/Galaxy services as possible helpers. Branch protection stays with
@stranak. **Both tasks remain open as of 09-07.**

## 2026-08-03 – 2026-08-04

* Hub template (`atrium_document.py`/`.schema.json`) iterated four more times (`542ab8f`, `8998ee9`, `6bc32eb`,
`db5a00f`, `72fc55f`, `ba7a264`) as the shared JSON contract kept growing.
* **`docs/docker_gha_roadmap.md` added** (`c159101`) — a full, documentation-only audit of the post-07-30 GHA/Docker
state against issue #18, explicitly deferring any code change to a later round. Three finding classes: **live
breakages** (B1–B9 — two API images with no ASGI server declared anywhere so they cannot start; every suffixed
compose `image:` reference asking for the wrong tag shape; a paradata self-report naming a GHCR tag that was never
published; the E2E's own no-secret fallback path guaranteed to fail its own assertion; llm-enrich's unbuilt `api`
Dockerfile stage referenced by compose anyway; all five composes bind-mounting a `data/` directory that exists in
no repo; a GPU-overlay doc/script mismatch between `.yml` and `.yaml`; alto's production entrypoint using the
filesystem-watching dev reloader; E2E silently patching `alto-tools` at runtime inside the published image);
**enforcement gaps** (E1–E11 — the hub's own self-check doesn't check the hub's own reusable-linter changes;
`workflow_lint.py` has zero tests and crashes on the legal `permissions: read-all` shorthand; the linter has no
rule for `timeout-minutes`/`concurrency`/workflow-level `permissions`/action-version floors; a second, unlinted
`@test`-pinned copy of `skill-validate.caller.example.yml` sits beside the linted `@v1` one; `all-repos-smoke.yml`
runs the full untagged pytest suite — including the model/network lane — on a GPU-less hosted runner and omits
llm-enrich from its own matrix); and **~1,020 lines of still-uncollapsed duplication** across
`release.yml`/`scheduled-smoke.yml`/`gpu-inference.yml`/`shellcheck.yml` (D1–D4), each with real per-repo drift
already present (translator alone runs Python 3.12 in its smoke job against 3.11 everywhere else; alto owns the
ecosystem's only real GPU test and has no GPU workflow, while nlp/llm each have one that can collect zero tests).
Four decisions declared settled for the eventual execution round: retire `test` and protect the default branch
(the two are now byte-identical mirrors in all six repos, doubling CI spend for no protection); make the GPU lane
runner-agnostic; collapse all four duplicated workflow families; and treat `:edge` images plus supply-chain/image
hygiene as in scope alongside that collapse.
* **Spot-checked 2026-09-07: B1 and B2 are now fixed** (in nlp-enrich, via a fix explicitly cited to "atrium-project#10,
G3" rather than to this roadmap directly) — see the 08-06 entry below. The roadmap's four "settled decisions"
(retire `test`, GPU-agnostic lane, collapse the four families, `:edge`/hygiene) have **not** been executed as a
dedicated wave; `test` and default remain parallel, byte-identical, both-CI'd branches in all six repos as of 09-07.

## 2026-08-05 – 2026-08-06

* **Issue #10 — "the 08-06 round."** A fresh LLM-review pass finds and fixes five P0s, each invisible to the repo
that owned it: alto's `/process` endpoint merging a `result["lines"]` no code path actually returns, writing a
hardcoded one-page stub; the same endpoint re-keying records via a lower-cased `Path.stem`; llm-enrich's remote
CLIs doing the identical re-keying on `.teitok.xml`, discarding every upstream block; nlp-enrich's
`teitok-schema.yml` red on its only run; page-classification's Dependabot `numpy` guard added and reverted five
minutes later. Found while fixing: **translator's `service/api.py` omitted `backend` entirely, so every real
`/translate` upload returned HTTP 500** — uncaught because every existing test mocked the pipeline. Two hub-built
mechanisms with ~0% adoption — `canonical_doc_id()` and `validate_document()` (the Layer D gate, documented as
normative, enforced nowhere) — are put on every production write path; `test_document_originators.py`, cited
elsewhere as the thing that pins this, **did not exist in the hub** until this round vendored and enforced it ×5.
* Digest+plan for #10 refreshed twice against the landed fixes (`4013f29`, `c69dd21`, `d5cb5d0`); GHA
self-check/example-workflow fixes (`b3badb9`, `a286615`, `324541b`); ruff formatting (`5b4e189`, `9701dc9`).

## 2026-08-18 – 2026-08-19

* **Issue #10 — "the 08-19 round."** Nine findings, six of them mechanisms that were present, green, and checking
something other than the thing that mattered. Correctness: `set_source()` silently discarded a new sub-key
(`origin`) whenever the baseline's `source` block already existed but was partial — reintroducing, through a
different door, the exact permanent-abstention bug the 08-06 round had just removed from alto; fixed so an absent
key is additive while a written key stays immutable. Gates that could not fire: every workflow's `concurrency`
group was keyed only by `${{ github.ref }}`, so a scheduled run and a push run on the same ref shared a group and
`cancel-in-progress` let the push silently kill the scheduled one with no failure reported — on 08-19 this
cancelled an `all-repos-smoke` run **eleven seconds** before a push run started; fixed as a **new check in
`tools/ci/workflow_lint.py`** (scope by `github.event_name` or disable `cancel-in-progress`) rather than a one-off
hand-edit, and it now runs on every push in all six repos. `sys.modules` poisoning removed from pc's test suite (four
files stubbing `atrium_document`); stale action-major pins restored ecosystem-wide.
* **Two corrections to the round's own work**, recorded with the same discipline the 08-06 edition used on itself:
a review pass that ran the new linter against tool-repo checkouts ~5 hours stale concluded five repos would go red
the moment `v1` moved (11 false findings — the compliance commits had actually landed 09:07–09:15 UTC, `v1` moved
at 09:37); and a second pass inferred nlp-enrich's `:test` GHCR tag was absent from a lightweight tag's *current*
target alone, when job-step evidence and a live anonymous probe both said otherwise. Both traced to the same root:
"a claim about live state was derived rather than measured."
* **`v1` tag moved** to `f54983e` at 09:37 UTC, carrying the widened `build-and-push` gate that admits `push` to
`refs/heads/test` — unblocking the publish sequence the 07-30 round had left waiting. Coverage floors raised
(alto 59→61); `service/*` genuinely dropped from alto's and translator's coverage `omit` lists. Dependabot bump
merged (`f54983e`, actions group ×5); issue #10 digest+plan refreshed after the round (`7673a37`).
* **State at end of round**: all six repos green, shared-code parity 40/40 pairs verified by direct blob hash (not
by trusting `para-drift`'s own badge). Open per the round's own accounting: the publish sequence still needed one
more `test` push to prove `:test` resolves under the new gate; no release wave yet (all five tool-repo versions
unchanged since 08-06, so `:latest` still described pre-round images); `e2e-digital-smoke.yml` at 7 runs / 7
failures, never reaching an assert step; `issue-log-refresh.yml` had quietly failed twice already (08-10, 08-17) on
an exhaustive `permissions:` block that zeroed out `issues:` and 403'd its own failure handler.

## 2026-09-03 – 2026-09-04

* `issue-log-refresh.yml` **finally runs and succeeds** — twice, via PR #52 (`bc55fe4`, "docs: refresh issue logs
via gh2md"), pulling in a full `gh2md` export including **closed** issues for the first time (`agent_dev_logs/issues/*.issue.closed.md`).
The workflow's own first attempt at opening this as a PR (`docs/issue-log-update` branch) had itself failed
(run #129) before the merge succeeded.
* **Reversed the same day**: `dbaa44e` ("removing closed issues and reformat for pre-commit") deletes every
`*.issue.closed.md` file the automation just added and reformats the rest — closed-issue exports are not the
convention this directory follows (per #29, only open issues get a living export here) and pre-commit's formatting
rules didn't match gh2md's raw output.
* **#51 Request DARIAH Vocabs Service Namespace** — Opened by K4TEL: publishing the harmonised AMCR+TEATER
vocabulary as SKOS needs a namespace first; `vocab_sources.py` already captures the AMCR `skos:exactMatch` URIs
but nothing exports them yet. @motyc defers it same day: a commencing SKOSification project for AMCR/TEATER led by
@petrpajdla already exists on an **18-month** timeline; acquiring a namespace is not trivial, and this issue should
not become blocking — current vocabulary IDs will become PID references to the published SKOS version once that
project lands. Using SKOS as an internal alignment framework now remains desirable and unblocked.

## 2026-09-06

* **#53 Follow best practices in all repos - `12 Factor` rules** — Opened by K4TEL: apply the twelve-factor
methodology across all six repos (codebase, dependencies, config, backing services, build/release/run, stateless
processes, port binding, concurrency, disposability, dev/prod parity, logs, admin processes). No response yet as
of 09-07; likely successor framing to the ad-hoc lettered findings issue #10's rounds have been accumulating.
* `issue-log-refresh.yml` **removed entirely** (`3ea60ff`, 281 lines) — after running successfully exactly once
(09-04), the automation is abandoned in favor of the pre-existing manual `gh2md` + `update_issues.sh` flow; the
same day's commits (`211a89d`, `21216f3`) are manual issue-log refreshes.

## 2026-09-07

* **State**: 21 open issues (#4, #6, #10, #13, #15, #16, #17, #18, #21, #22, #24, #26, #27, #31, #32, #40, #51,
#53, #54, #55, #56 — the last three opened 09-07 and missing from this line until the 09-07 #55 round below).
`test` and `main` both at `7f50741`; tag `v1` moves with every push that carries it forward. `@v1` reusable
pin confirmed live across all five tool repos' workflows. `e2e-pipeline-smoke.yml` (the JSON five-stage pipeline)
is robustly green — 112 runs, one failure since 08-19. `e2e-digital-smoke.yml` remains **red on every one of 19
runs since 08-06**, auto-tracked via bot-opened issue #49 (7 "still failing" comments so far); the root cause has
moved from "image never resolves" (pre-08-18) to a genuine content defect: the pipeline now runs cleanly through
digital-convert and the llm-enrich stage, schema-validates, and keeps `doc_id` stable across both stages, then
fails the final assertion with `AssertionError: 'enrichment' block missing from llm-enrich stage` — the CLI/remote
image path the workflow drives does not populate the block that `/enrich`'s API path does. Full detail:
`digests/project_state_0709.md`.

* **#55 Add `HEALTHCHECK` and `SIGTERM` handling to all five tool-repo services** — Opened by K4TEL as a
sub-issue of #53, carving out factor **IX. Disposability** with its own acceptance criterion ("ARÚP/ARÚB confirm
the images run cleanly on their Kubernetes"). Implemented the same day across all six repos, **local and
unpushed**: 53 files. Both stated defects were real (zero `HEALTHCHECK`, zero `SIGTERM` handling anywhere), and
measuring the repos turned up **three more that blocked the acceptance criterion regardless**. First,
**Kubernetes never reads a Docker `HEALTHCHECK`** — the kubelet's probes are pod-spec fields, so the directive
alone could not make `/health` "visible to a Kubernetes liveness probe"; the partner-facing half had to be a
probe contract plus a reference manifest (`docs/k8s_deployment.md`,
`docs/templates/k8s/atrium-service.deployment.yaml`). Second, **four of five services had no runnable API image
at all** — only nlp-enrich published one; alto, translator and pc reached FastAPI solely through a compose
`entrypoint:` override on the *batch* image, and llm-enrich's `api` stage was declared but excluded from
`build-targets` (roadmap **B5**) — so with the handoff boundary fixed at "a Docker image, run at ARUP/B's own
Kubernetes" (#40, motyc), there was nothing for the partner to pull. Third, **three services blocked the event
loop** during inference, and uvicorn's SIGTERM handler is an event-loop callback, so
`--timeout-graceful-shutdown` had nothing to measure until those moved to `asyncio.to_thread`.
* **The fix that matches the issue's own sentence.** "A rolling restart kills in-flight work" was literally
true of nlp-enrich's `POST /jobs`: it returned `queued` and left the job in a bare `asyncio.create_task(...)`
with the result discarded, so uvicorn saw zero in-flight requests and exited mid-job — a defect no
in-flight-request counter and no graceful-shutdown timeout can reach. Jobs now register with
`ServiceState.track()`, which the drain awaits; verified against a **real uvicorn 0.52 subprocess sent a real
SIGTERM**, which ran the tracked job to completion before exiting. The same test settled that the installed
handler must **chain to** uvicorn's own `Server.handle_exit` rather than replace it, and that a clean exit is
**143** (128+SIGTERM), not 0 — uvicorn re-raises the captured signal on purpose.
* **New canonical surface**: `ServiceState` / `attach_inflight_middleware` / `serve_lifecycle` / an extended
`attach_health` in `docs/templates/shared/atrium_service.py`, plus a new `healthcheck.py` (stdlib `urllib` —
no image ships `curl`, and only alto ships `wget`). Additive and backward-compatible; shallow `/health` stays
byte-identical, which is what leaves the five `test_health_shallow_ok` copies and
`skill-validate.reusable.yml`'s live probe untouched. Readiness moved to a **separate `/ready`** deliberately:
a liveness probe that fails while draining gets the pod SIGKILLed before the drain finishes. Also the first
tests any of the four canonical shared modules has ever had (17; roadmap **E9**), and
`docker-build-smoke` now optionally **runs** the image it builds (`load: true` + a new `probe-targets` input) —
the first thing in this ecosystem's CI to ever start one of these containers (roadmap **B9**).
* **Two record corrections found in passing.** Roadmap **B8** (alto's `uvicorn --reload` in production) was
**already fixed** in code and had been described as open in six documents; recorded in
`docker_gha_roadmap.md` §8 per that file's convention. And `digests/55.digest.md`'s own pointer to "hub #56 and
the standing partner ask ... in the workplan's §7" was doubly wrong — **#56 is DOG/Switchboard registration**
and no "workplan" document exists in this repo — so #55's acceptance had no tracked vehicle until
`docs/k8s_acceptance_runbook.md`. Scope grew well past the issue's "days of work" estimate and past the Q3
milestone's 2026-09-30 due date; the milestone move is part of the GitHub-side follow-up, not a surprise for
later. Full detail: `digests/55.digest.md` · `plans/55.plan.md`.

---
_Timeline index refreshed 2026-09-07 against live `test`/`main` HEAD, the current release/CI/issue state of all
six repos (including direct CI-log inspection of the failing `e2e-digital-smoke.yml` run and its tracking issue
#49), and `docs/docker_gha_roadmap.md`. Nothing removed from the issues themselves (per #29); this file is a
derived reading aid in `agent_dev_logs/`._

## 2026-09-08

- **#51 SKOSification of internal data — DARIAH Vocabs standards** — split the issue in two and
  acted on the half that was never blocked. The namespace request stays deferred to @petrpajdla's
  18-month project per @motyc; the internal SKOS alignment he called "definitely desirable" is
  built. New hub-canonical `docs/templates/shared/atrium_vocab.py` (+ `.schema.json`) declares the
  six ATRIUM-authored label sets — page categories, line categories, quality bands, coarse entity
  types, CNEC codes, harmonisation themes — that previously lived in four repos in four different
  forms; vendored to all five tool repos and enforced by `para-drift.reusable.yml`.
  `vocab_build.py --skos` emits `union.skos.ttl` (5,594 concepts / 55,188 triples) using the
  sources' own URIs, so ATRIUM mints nothing that would later need migrating. `vocab_sources.py`
  stops discarding `closeMatch`/`broadMatch`/`relatedMatch`, and harvests TEATER's AAT citations as
  `dcterms:source` rather than as mappings. `vocab_manager.resolve_pid()` makes `entities[].pid`
  fillable for the first time since schema 1.0. Strategy: [`../docs/skos_strategy.md`](../docs/skos_strategy.md).
  Three defects recorded there, one of them live: `DROP_CATEGORIES` matches nothing on the OCR path
  because `lines[].categ`'s two originators emit disjoint label sets (V-1, documented not fixed —
  it changes what the model reads).

## 2026-09-09

- **#31 AGENT SKILL — API service per repo** — re-aligned all five `agent-skill` branches with
  their `test` branches and repaired the validation CI. The previous sync (2026-09-08) was real;
  `test` moved the same morning with the #51 SKOS work and dependency pins, putting
  `skill_drift_check.py` back to **0/5 aligned** within a day. Ported everything it flagged —
  including `atrium_document.schema.json`, whose one #51 blob was missing from all five — and
  newly vendored `atrium_vocab.py` + `atrium_vocab.schema.json`, absent from every skill branch
  because each importer guards with `try/except ImportError` and so degraded in silence. Now
  **5/5 aligned**, with three reviewed divergences declared in the tool rather than remembered.

  Three defects surfaced that no check was looking for. **(1)** All five `skill-validate` callers
  passed only `client-script`, so `app-import` fell back to `service.api` — wrong for
  alto-postprocess (`service.text_api`), whose step 4b had import-skipped on *every* run behind
  the `::warning::` that exists to stop a skip reading as a pass — and `primary-endpoints` fell
  back to `""`, disabling the primary-endpoint assertions in both 4a and 4b everywhere. The hub's
  caller template already carried both; `31.digest.md`/`31.plan.md` recorded the situation
  backwards, asserting the template was stale and the callers correct. **(2)** alto's skill-branch
  API container could not start: `service/text_api.py` imported `atrium_document` at line 21 with
  only `service/` ever added to `sys.path`, so `python service/text_api.py` — the compose `api`
  entrypoint — died at `ModuleNotFoundError`. Reproduced, then fixed by the port. **(3)** The
  issue-#55 container contract was gone from all five: no `HEALTHCHECK`, no `STOPSIGNAL`, no
  `--timeout-graceful-shutdown`, while `service/healthcheck.py` shipped inert on four branches,
  was missing outright on nlp-enrich (the cause of that repo's red run), and nlp-enrich's
  `service/README.md` documented the behaviour as live throughout. The `Dockerfile` /
  `docker-compose*` content allowlist is what hid it.

  Also: translator and llm-enrich now actually mount the `/frontend` their READMEs had advertised
  for six weeks, via an `.exists()`-guarded block that is a no-op elsewhere and so forward-merges
  to the default branches; llm-enrich's page, which had been left behind by the service redesign
  and answered 422 on every text submission, is rewritten against the live envelope.
  `skill_drift_check.py` gained a missing-`service/`-file check (it had called nlp-enrich clean
  while CI failed on exactly that), an issue-#55 container-contract check, and
  `DOCUMENTED_DIVERGENCES`. Strategy §5's claim that CI catches a false `/frontend` mount is
  corrected — it cannot, and did not. Full detail: `digests/31.digest.md` · `plans/31.plan.md`.

## 2026-09-11

- **#62 Build, release, run — retire the E2E entrypoint overrides** (with
  [alto#50](https://github.com/ufal/atrium-alto-postprocess/issues/50)) — roadmap **B9** closed, the
  last live §2.1 breakage and the sharpest build/release/run violation in the register: *a release
  artefact that re-resolves its own pinned dependency at run time.* Local and unpushed: 8 files
  across three repos.

  **The finding that resized the issue by an order of magnitude.** B9's second sentence — "E2E
  overrides every image's `--entrypoint`, so no Dockerfile ENTRYPOINT is ever exercised anywhere in
  CI" — is true as written and reads like a workflow rewrite. **Three of the four overrides were
  exact no-ops**: each replaced the image's real `ENTRYPOINT` with a command byte-identical in
  effect to the `ENTRYPOINT` it replaced. They cost nothing at runtime and everything in assurance —
  the lane *reported* that it never exercised a real entrypoint, and in three cases it silently did,
  with nothing in the file distinguishing them from Stage 2, which was doing real harm. Stage 1 had
  been running with no override for the life of the workflow and was the proof all along.

  **The expensive half had already landed.** alto#50 (`6ddabf7`) retired `alto-tools` rather than
  re-pinning it — the two code paths this ecosystem used are vendored into `alto_tools.py`,
  attributed in the README's "Vendored code 📦" section and `LICENSES/alto-tools-Apache-2.0.txt`,
  with the layoutreader clone pinned by commit in the same pass — and hub `6ba4807` dropped the
  Stage 2 `/bin/sh` shim, the `pip install` and the `PATH` re-export. Run
  [#130](https://github.com/ufal/atrium-project/actions/runs/34567086963) is green on that, Stage 2
  executing in 56 s. So this round is the three deletions, the arguments they expose, a guard, and
  the rider nobody owned. **Both `62.digest.md` and `62.plan.md` were a day stale and described a
  file two commits gone — every line number in the issue body (`:245`, `:272`, `:274`, `:289`,
  `:311`, `:336`) now points at something else.** Both refreshed against `test` HEAD.

- **The check the "they're no-ops, just delete them" framing would have skipped.** This lane defaults
  to `image-tag: latest` — **the last RELEASE of each tool, not `test`**, as the workflow's own
  header note is emphatic about. So reading `Dockerfile` on `test` proves nothing about what the lane
  will pull, and the deletions are only sound if the *published* images carry the entrypoints being
  fallen back on. Verified at each repo's newest release tag before landing: translator **v0.10.5**
  `["python", "main.py"]`, nlp-enrich **v0.20.1** `["python", "run_pipeline.py"]`, llm-enrich
  **v0.6.3** `["python"]` (`remote`). All three match. That was the single way this could have broken.

- **The trap that is invisible to every static check.** With the interpreter forced as the entrypoint,
  `main.py` was argv[1] *to Python*; without it, `ENTRYPOINT ["python", "main.py"]` already supplies
  the script, so leaving `main.py` in the command passes it as an argument *to* `main.py`. Stages 3
  and 4 drop the script name with the override; Stage 5 **keeps** `openrouter_client.py`, because
  llm-enrich's `remote` entrypoint is the bare interpreter and the script really is its first
  argument. All five commands were rendered as the shell will see them to confirm the
  arguments-only shape — reading the YAML is not enough, and the E2E run remains the real proof.

- **New guard: `tests/test_e2e_entrypoints.py`** (29 tests; hub suite 81 → 110), picked up for free
  by `hub-self-check.yml`'s existing `shared-tests` job. Asserts that no step's `run:` body overrides
  a container entrypoint unless the `(workflow, step)` pair is declared in an `ALLOWED_OVERRIDES` map
  *with a reason* — the issue's own "say why in a comment rather than leaving a silent override",
  with CI behind it — and that no `docker run` installs a dependency at run time, matched per logical
  line so a legitimate runner-side install in the same step is not implicated. **Parsed, not
  grepped**, so the comment blocks explaining the removal are not themselves offences. Deliberately
  *structural* rather than the issue's literal `grep -c "pip install" == 1`, which is brittle in both
  directions: red the day a second legitimate runner-side install appears, green if that one line
  ever moved *into* a container command. Both checks were confirmed **red** against purpose-built
  breakage — including the verbatim historical Stage 2 shim — before being trusted.

  A trap the issue sets for itself, recorded because it will catch the next person: `grep -c --
  "--entrypoint"` counts **comments**. Prose explaining the removal breaks the acceptance criterion.
  Both the existing Stage 2 block and the new Stage 3 block say *"entrypoint override"* and never
  spell the flag; the acceptance greps return **0** and **1**.

- **The orphaned rider, closed by fixing it.** K4TEL's comment on #62 named the bullet nobody could
  satisfy — "every `git+` requirement in the ecosystem carries an explicit ref" covers `flexiconv` in
  nlp-enrich and llm-enrich, *"which can't be fixed from this repo and have no issue in either.
  Either open two one-liners or strike the bullet."* Both framings accept the work not getting done;
  taken as a third option since both repos were in hand. Both now pin `@v0.3.10` — a published tag
  rather than a bare SHA so the intent stays readable — with the resolution recorded beside it
  (`a982b88f…`; `main` is ahead at `a4f0fd9…`, untagged), the way `workflow_lint.py` already requires
  for action SHAs. An ecosystem-wide sweep for `git+` / `git clone` now returns those two pinned
  lines and nothing else: **factor II is green.** Blast radius stated rather than assumed — no
  Dockerfile installs either file, only llm-enrich's `scheduled-smoke.yml` does and behind a
  `|| echo` fallback, and both repos' `test_flexiconv_convert.py` *skip* when the tool is absent, so
  llm-enrich's nightly is the only place a bad pin would ever surface.

- **The successor finding, named and not folded in.** Every stage still runs the image's *interpreter*
  against a *fresh checkout* (`-w /workspace/work/atrium-<tool>-main`) rather than the image's `/app`,
  so a source change that never reached the published image still passes E2E — same class as B9, other
  axis, arguably larger. It is also **why the entrypoint overrides looked harmless for so long**: with
  `-w` pointing at the checkout, the forced interpreter and the real entrypoint resolved the same
  relative script, so nothing ever misbehaved. This round is a prerequisite for closing it rather than
  a partial fix (once `-w` goes, `ENTRYPOINT ["python", "main.py"]` resolves `/app/main.py`, the
  desired end state), and it needs its own issue. Whether the lane should instead migrate onto
  `docker-build-smoke`'s proven `load: true` + `probe-targets` mechanism (#55) stays undecided.

  Still open: the E2E dispatch at both `latest` and `test`, which is the one thing no local check can
  supply; a deliberate `ENTRYPOINT` break to confirm the lane is now sensitive to what it claims to
  test; and closing alto#50 (🟢 since 2026-09-11) on GitHub. Full detail:
  `digests/62.digest.md` · `plans/62.plan.md` · `docs/docker_gha_roadmap.md` §9.
