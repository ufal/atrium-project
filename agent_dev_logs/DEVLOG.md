# 📓 atrium-project — agent_dev_logs/DEVLOG.md (timeline index)
> _Hub/planning repo. 24 open issues. `test` = `main` = `8de7896` (2026-09-25, issue logs); tag `v1` = `c2b423a`; the 2026-09-21 divergence and its retag window are closed — `v1` carries #59/#60 and canonical file #17. Latest entry: 2026-09-25 (round 7, not yet pushed). CI green on `eec0682` (E2E pipeline smoke 35990199050, digital smoke 35990199010, fast-lane matrix 35990199041, docs site 35990199021)._
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

## 2026-09-16

- **The release gate blocked a second repo, for the same three CVEs, and the fix had never been ported.**
  `atrium-nlp-enrich` `v0.20.2` (run 34970419474) failed *"Fail the release on fixable CRITICAL
  vulnerabilities"* on **all three** matrix targets — `perl-base` 5.40.1-6 carrying CVE-2026-13221,
  CVE-2026-42496 and CVE-2026-8376, all fixed upstream in 5.40.1-6+deb13u1. Promotion is
  `if: success()`, so the release published **by digest only**: `:0.20.2` and `:latest` were never
  applied.

  The gate is `if: startsWith(github.ref, 'refs/tags/')`, which is why the identical commit `0aaff7e`
  passed on `master` and on `test` and failed only on the tag — the failure is invisible right up until
  a release. `atrium-translator` had hit this on 2026-09-13 with `v1.0.0-beta`, fixed it with a
  cache-bust-anchored `apt-get upgrade` (`Dockerfile:15-42`, naming these exact CVEs), and released
  `v1.1.0-beta` green on 09-14. `grep -rn "apt-get upgrade" atrium-*/Dockerfile` matched **translator
  alone**: the remaining four repos were each one tag away from the identical failure.

  Ported to nlp-enrich, llm-enrich, page-classification and alto-postprocess, merged into the existing
  apt layer so there is one `apt-get update` per image. `tests/test_dockerfile_security_layer.py` pins
  the two invisible properties — the layer sits below the `ATRIUM_RUNNER_REF` `ENV` (or `cache-from:
  type=gha` serves it forever and it silently stops patching) and above `USER atrium` (apt needs root)
  — and was **verified by breaking it**, twice, per this ecosystem's standard.

  Promoted to **para-drift canonical file #17** (`docs/templates/shared/MANIFEST.json`), which is #59's
  machinery doing exactly what it was built for: one manifest row plus one `ruff.toml` entry, and all
  three consumers pick it up. Made a ruff-format fixed point at line-length **100 and 120** so a missing
  exclude cannot split it into two variants the way it split `test_document_originators.py` on 08-05.
  nlp-enrich bumped `0.20.2` → `0.20.3`; the `v0.20.2` tag is left where it is.

- **`--best` cannot move to `v*.4` yet, and the reason is upstream.** All five `v*.4` revisions of
  `ufal/vit-historical-page` serve the **same** `regnety_160` checkpoint — identical 322,925,148-byte
  `model.safetensors`, `"architecture": "regnety_160"` in every `config.json` — against a correctly
  heterogeneous `v*.3` control (v1.3 `tf_efficientnetv2_m`; v2.3 ViT `hidden_size` 768; v5.3 ViT 1024,
  1,214,854,652 B). A bogus `@v9.9` is rejected, so the refs exist; they just do not hold what
  `REVISION_TO_BASE_MODEL` declares. Only `v4.4` is what its name says.

  This would have failed **silently**: `run.py --best` and the API's `version="all"` would average one
  model with itself five times, return well-formed Top-N predictions, and report "Ensemble (Average of
  5 Models)". `tests/test_best_ensemble_distinct.py` is the standing guard (static half offline, Hub
  half skipping on any transport error so it cannot flake);
  `data_scripts/unix/hf_reupload_v4_revisions.sh` is the repair — dry-run by default, and it refuses to
  push a checkpoint whose `config.json` disagrees with the registry, which is the check that was missing
  the first time.

  Also settled while here: `model_accuracies_new.csv` is **not** stale. It records a different
  namespace — the per-candidate sweep (`v7.3.1` = regnety_160) — while the published ensemble renumbered
  the five winners (`v4.3` = regnety_160). The two collide on `v1.3` and `v4.3`, and exact-key-first
  resolution is what keeps it correct. Documented in `model_registry.py` rather than "fixed".

- **The `agent-skill` branches were fetched for the first time, and three are broken as shipped.**
  `skill_drift_check.py` had never run against them (no clone had `origin/agent-skill`), which is
  #59's last unchecked box. It reports **0/5 aligned** — and once its two blind spots were closed
  (relative imports were skipped outright; package submodules and `subprocess`/shell invocations were
  unrepresentable), **seven genuinely missing files**, each verified by hand:
  nlp-enrich lacks `api_util/{document_hook,teitok_read,validate_teitok_xml}.py`; llm-enrich lacks
  `api_util/{doc_to_visual_md,layout_md}.py` — and its own `SKILL.md:130` tells the agent to run
  `api_util/xml_to_md.py`, which imports `layout_md`; page-classification's `run.py` imports
  `atrium_paradata` and `yolo_classifier`, neither on the branch.

  The mirror-image problem is now fixable too. `skill_ify.py`'s `derive()` was a pure **denylist** —
  it subtracted `TRIM_DIRS` from the whole default tree, so anything nobody named survived, and `plan`
  reported **"0 to delete" for every repo**. It now intersects against the same reachability closure,
  and `OVERLAY_DIRS`' bare `"service/frontend"` prefix (which had been protecting the dev-only
  `service/frontend-lindat/` on three branches, against §5) carries its trailing slash. Canonical
  para-drift files are deliberately exempt: they are held for ecosystem parity, not because a service
  imports them. Report: `skill_branch_report.md`.

- **Records corrected against the trees, not the logs.** `53.plan.md`'s three §A "false claims" and its
  §C amber all verify as fixed. `58.plan.md`/`58.digest.md` said `HOST` has no CI probe;
  `docker-tool.reusable.yml:553` is one. `59.plan.md` said "Closed" of an issue that is open on GitHub.
  `35.plan.md` was stale in every bullet but one, and its last acceptance gap — *the manifest carries
  it* — closed when `docs/templates/k8s/atrium-service.deployment.yaml` gained the per-repo constraint.
  translator's DEVLOG cited two files that were never written; page-classification's claimed it had no
  digests/plans/issues while all three existed.

  Still open and **not** closable by a file change: #58's deliberate-breakage run, #62's `image-tag:
  test` dispatch and entrypoint break, the `-w /workspace` successor issue, and #55's partner
  acceptance. Drafted comments: `issue_closure_notes.md`.

- **#54 FREEZE + #51 SKOS — the follow-through, and a record that had been wrong for a week.**
  `bbc8fde` landed §A (the tightened `required`/`anyOf`/`allOf`) and §B (`atrium_rocrate.py`,
  `docs/rocrate_export.md`) at **18:56** on 2026-09-09. `54.plan.md` and `54.digest.md` were
  committed at **18:57**, still reading 🔴 NOT DONE for every row, and `DEVLOG.md` has never
  mentioned RO-Crate at all. The five tool repos followed that night, `v1` was moved, and the issue
  still carries a comment saying "nothing pushed". Everything below is what that record said was
  outstanding — plus three things it did not know.

  **The fixture pass was the live defect, and it was bigger than the list.** An invalid *baseline*
  latches and demotes each stage's own-output gate from `raise` to `warn`, so for a week the freeze
  was weakening the exact gate it exists to strengthen. §A.4 enumerated ten baselines by hand; an
  AST sweep validating **every dict literal carrying a `schema_version` key in every `test_*.py`
  across all six repos** found **twelve**, and the four extras were the interesting ones:
  `nlp-enrich/tests/test_api_service.py`'s goes through a service endpoint, and two of them
  (`alto/tests/test_document_hook.py`, `translator/tests/test_atrium_document.py`) are
  *deliberately*-invalid fixtures that were invalid for **more reasons than the one they test** —
  an inherited-defect test that passes whether or not its check still works.
  `nlp-enrich/tests/test_document_hook.py` had already named that discipline in a comment; the
  other two now follow it.

  **`atrium_rocrate.py` had zero callers.** Vendored byte-identical in six repos, registered in
  `MANIFEST.json`, drift-gated, selftested — and not imported by any pipeline, service or CLI
  entrypoint, in no `Dockerfile`, in no release bundle. §B.3 chose hub-canonical distribution and
  got it; "distributed" turned out not to mean "reachable", and the DMP's WP3 RO-Crate commitment
  was a module nothing could invoke. `run_pipeline.py --rocrate-out DIR` (alto) is the first caller,
  after the fact over records already on disk so it stays off the hot path — which is what keeps it
  from quietly reversing the PROV-O/CIDOC-CRM rejection at 1.2M-page scale. Three release bundles
  now ship it.

  **F3 was not cosmetic.** The example fixture carried four values `atrium_vocab` does not know, and
  the exporter mints a `DefinedTerm` per controlled value — so each was a published identifier for a
  concept nobody declared. Fixed, with a test that fails on the old values.

  **F5.** `derived_from` widened to string-OR-`{ref, sha256, bytes}` so a crate can name a `hasPart`
  it can verify. Additive under versioning rule 1: `add_derived_from()` still writes a bare string
  unless given a checksum, and `derived_from_ref()` is the single reader both shapes go through —
  `str()` on the object form would have named a file that does not exist. Paradata now records the
  exact commit (`GITHUB_SHA`) beside the moving `runner_ref`; it is platform-supplied, so it joins
  `_NOT_OPERATOR_KNOBS` rather than being advertised in `.env` as a knob that does nothing off-CI.
  **F6**: the hub was the only repo without a `CITATION.cff`.

  **#51's behaviour fixes, both taken.** **V-1**: `DROP_CATEGORIES` was `digital-convert`'s two
  labels only, and alto-postprocess emits a disjoint set — so on the OCR path the filter matched
  *nothing* and every garbage line reached the model. It now filters on
  `UNTRUSTWORTHY_LINE_CATEGORIES`. **This changes what the model is shown**, which is why it waited
  for an owner. The suite never caught it because every fixture used the digital-born labels;
  `"Trash"` is the one label only alto emits, so the new tests discriminate.
  **V-2**: `collect_images()` took every `os.listdir` entry, so it raised `NotADirectoryError` on
  this repo's own `small_data_samples/` — and a stray *directory* would not have raised at all, it
  would have shifted every class index out of step with `model_registry.CATEGORIES`. Silently
  mislabelled training data is the worse half. `_advise_category_drift`'s docstring had prescribed
  the exact fix and said it was not applied; it now records that it was.

  **#51 F6, and the defect it surfaced.** `enrichment.items[].teater_category_uri` carries the source
  concept's own URI, populated through `vocab_manager.concept_index()` and **never** through
  `_settings.nested_keep` — that path serialises into the model's system prompt, and a provenance
  field must not change model behaviour. Wiring it exposed **V-5**: `teater_category` holds a
  *source* label (`kostel`), not one of the eleven ATRIUM themes, and both `validate_labels` and the
  crate read it as a theme — so the exporter was minting `w3id.org/atrium/theme/kostel`, an
  ATRIUM-authored identifier for an **AMCR** concept, against `skos_strategy.md` §3. The crate now
  prefers the source URI as a term's `@id` and mints nothing. The contract question — which of the
  two the field should hold — is recorded, not decided.

  **F3 (translator), half taken.** `load_vocab.py --from-flat` rebuilds the vocabulary from
  nlp-enrich's committed artifacts instead of harvesting: the duplicate harvester stays, but
  reproducing the shipped CSV no longer requires running it. The regenerated file is the five-column
  provenance form its own writer had supported for weeks without ever being rebuilt — and is **159
  terms lighter** (24 gained, 11 retranslated), the reproducibility-vs-coverage trade V-3 names.
  Worth a second look if those terms matter; the lever is the pinned TEATER snapshot ref, not this
  path. **F8**: deleted the orphaned `fixtures/e2e/VOCAB/teater_nested_vocab.json`, which the README
  had described as removed since 2026-08-19 while the file sat on disk.

  Also: `atrium-llm-enrich/scripts/revendor_shared.sh` deleted — a hand-written 9-entry list
  omitting `atrium_rocrate.py`, `atrium_vocab.*` and three contract tests, so a clean run of it did
  not mean para-drift would pass. Exactly the drift class `MANIFEST.json` (#59) exists to kill, and
  the only local copy in the ecosystem. page-classification's `CONTRIBUTING.md` called the schema
  tightening a "breaking change" while `document_schema.md` argues at length that it is not;
  reworded to "stricter validation", which is what it is.

  `docs/templates/workflows/update_issues.sh` exported a **placeholder** token (52 bytes, with a
  literal `...` in it) that shadowed the `-z` guard four lines below, so the guard could never fire
  and a missing token surfaced as an opaque API failure. Removed. `skos_strategy.md` §7's "it should
  be revoked" **overstates it**: the file has one commit in history and the value was elided in that
  commit too — no live credential was ever committed, and there is nothing to revoke.

  Verified: hub 174 + 139; alto and page-classification green; nlp-enrich 881, llm-enrich 884,
  translator 606. `revendor_shared.sh --check` in parity across all five repos, all six committed in
  one window. `atrium_rocrate.py --selftest` clean and byte-identical across processes.
  **Still open on #54: the freeze tag** — distinct from `v1`, and a remote action.

- **#57 GH PAGES — design refreshed, nothing built** (by decision). Every premise re-verified:
  `has_pages` false on all six, no site scaffolding anywhere, corpus **223 files / ~50,900 lines /
  ~2.9 MB**. Five corrections folded into `57.plan.md` (marked ⚡): reuse **#59's `MANIFEST.json`
  pattern** for `docs/site.yml` rather than inventing a second registration convention — it landed
  after this plan was written and already solves the same problem; the **`vit` default branch is a
  prerequisite, not a footnote**, since Pages publishes from the default branch; permissions are
  tighter than recorded (`admin: false` on **all six**, `maintain: false` on the hub and llm-enrich),
  so the `actions/configure-pages` path is the only path for every repo; **the hub has no
  `CONTRIBUTING.md` of its own**, only the template the five vendor, which changes what its
  Contributing page renders; and `atrium-page-classification/README.html` (178 KB, stale, at repo
  root) needs a decision before a generator emits a competing HTML tree.

## 2026-09-18 → 2026-09-19
- **#57 GH PAGES — the first thing actually built, after two design-only rounds.** `8bdc5b4 docs:
  added GH pages` (then `05f3a8b docs fixed tables`) put `mkdocs.yml`, `PAGES_SETUP.md`, `INDEX.md`,
  **38 `docs_site/` draft shells** and seven `_generators/` scripts on the hub. Five orphan
  `gh-pages` branches were pushed, one per tool repo, each holding a static landing card
  (`index.html`, `404.html`, `assets/style.css`, `.nojekyll`, `README.md`). Pages was switched on for
  page-classification, translator and nlp-enrich the same day; **alto-postprocess got the branch but
  not the setting**, and is still dark.

## 2026-09-21
- **#57 GH PAGES — the hub's Pages was switched on against the wrong source and broke.** stranak
  enabled Pages on `atrium-llm-enrich` (`gh-pages`, green) and on `atrium-project` — the latter
  pointed at **`main` / `/docs`** with the legacy Jekyll builder. Run `35582651532` fails on a
  **Liquid syntax error** at `docs/docker_gha_roadmap.md:79`.

  The root cause is a defect class the #57 survey missed: **Jekyll renders Liquid over all markdown,
  inside fenced code blocks and inline code spans too**, so every quoted GitHub Actions expression is
  read as a template variable. Nine occurrences in two hub files (`docker_gha.md:213`;
  `docker_gha_roadmap.md:79,80,92,99,190,252,414,437`); only `:79` hard-fails, the other eight would
  render empty.

  **The red build is load-bearing and must not be "fixed" in place.** `/docs` is the hub's canonical
  internal tree; a *green* Jekyll build from it publishes `docs/arub-p_contacts.md` — five ARÚP/ARÚB
  partner email addresses — plus `plan_repo_review.md` and the 97 KB internal roadmap. The failing log
  already reaches `Rendering: arub-p_contacts.md` and dies four files later. Nothing leaked, by
  accident rather than by design. **Order: move the source off `/docs` first, escape the Liquid
  second.**

  Landed: `.github/workflows/pages.yml` (`mkdocs build --strict` on every event; `mkdocs gh-deploy
  --force --no-history` to `gh-pages` only on push to `main`; 07:00 cron), `tools/docs/requirements.txt`
  (mkdocs <2 / material <10 / pymdownx <13 — Material warns on every build that MkDocs 2.0 removes the
  plugin system this site uses), `/site/` in `.gitignore`, and
  `validation: links: anchors: warn` in `mkdocs.yml` — **without which `strict: true` never checked the
  broken anchor its own header comment cites as the reason for it**, because MkDocs defaults anchor
  validation to `info` and `--strict` promotes warnings, not info.

  **`actions/configure-pages` was ruled out on evidence.** §A.3/§G's claim that it is "the only path —
  for every repo including the hub" was **wrong when written**: its `findOrCreatePagesSite` GETs the
  existing site first and returns it, POSTing `build_type: workflow` only when that GET fails. On a
  repository already enabled as a *branch* source it is a no-op. One owner-level dropdown is what is
  needed, on the hub and on alto-postprocess.

  Also: the **40 sibling links** on the five landing cards (4 per page × `index.html` + `404.html` × 5)
  pointed at `atrium-project/tools/<short>/`, a site that did not exist — 90 hub links across the five
  branches, all 404. The sibling four now point at `https://ufal.github.io/<slug>/`, the neighbour's
  own published page. The card's own four hub links stay on the hub deliberately. `make_stubs.py`
  `pipeline_html()` is the single place this is decided.

  Corrections folded into `digests/57.digest.md` and `plans/57.plan.md`: ten claims, one wrong on its
  own terms (above), the rest overtaken. §G's `pages-stub.reusable.yml` + per-repo caller is **struck**
  — the stubs shipped as static files and a reusable has nothing to build. `docs/site.yml` is listed by
  `INDEX.md` but **has never existed**, so its "38 = 38 = 38" had two terms. All seven `_generators/`
  files are committed, contrary to `INDEX.md`'s claim they should not be. Corpus re-measured at the
  default branches: **252 markdown files, 4,581,156 B**.

  **Then the legacy build itself was fixed, rather than merely worked around.**
  `pages-build-deployment` is a built-in job, not a workflow file here, so the only two levers are
  what lives under `docs/` and where the source points. `docs/_config.yml` takes the first:
  it excludes the three sensitive/internal files, `docker_gha.md` (its one `{{version}}` resolves to
  the empty string rather than raising — the page would ship silently claiming `type=semver,pattern=`)
  and `templates/` (vendored code and «placeholder» skeletons, not documentation). Nine reviewed files
  still publish, all clean of Liquid and of any address. **No source file was edited** — the markdown
  is correct, and `{% raw %}` or entity-escaping would corrupt GitHub's own rendering of it.

  This is §F's "explicit, tested step" arriving early. `tests/test_docs_pages_exclude.py` is
  bidirectional in the #59 sense — every exclusion names a file that exists, every file under `docs/`
  is excluded or reviewed — plus two assertions that would each have caught this incident: no
  publishable file may carry a Liquid construct, none may carry a partner address. Scoped to the two
  ARÚP/ARÚB domains, **not** "any email address", per §F's own warning. All six checks were
  deliberately broken and confirmed to fail before being trusted.

  Reproduced locally on `jekyll 3.10.0` / `liquid 4.0.4`, the versions the Pages image pins:
  byte-identical error, and the fenced build exits 0 with the excluded files absent. The trap worth
  recording: the reproduction needs `jekyll-optional-front-matter`, which GitHub Pages forces on —
  without it, front-matter-less `.md` is copied as a static asset, Liquid never runs, and a plain
  `jekyll build` **passes**.

  Verified: `mkdocs build --strict` exits 0 (mkdocs 1.6.1 / material 9.7.7 / pymdownx 12.0.1);
  `workflow_lint.py` OK with `pages.yml` in scope; hub suite **164 passed, 4 skipped** (141 + the 23
  new); `ruff` clean; `make_config.py` still regenerates `mkdocs.yml` byte-identically. **Not**
  verified: any live URL — `ufal.github.io` is blocked by the authoring environment's egress proxy, so
  every claim about a serving site is read from `pages build and deployment` run conclusions, not from
  the page.

- **#57 GH PAGES — the Pages folder moved from `/docs` to `/ (root)`, and the fence went inert.**
  Run `35612083327` reports `Source: /github/workspace/.` and **`Configuration file: none`**. Jekyll
  reads the `_config.yml` beside its source, so `docs/_config.yml` — merged that morning — stopped
  being consulted the instant the dropdown changed. Bypassed, not broken.

  **The blast radius went from 13 files plus `templates/` to every tracked file**, including all 79 of
  `agent_dev_logs/`, which `57.plan.md` §E says are never published and which hold 49 issue exports,
  several of them open memos to named individuals. Files carrying an email address went from 2 to
  **5** — `digests/project_state_1307.md`, `digests/project_state_2706.md` and
  `issues/2026-06-12.21.issue.open.md` were never in the docs-scoped fence's reach. Files carrying a
  Liquid construct went from 2 to **9**.

  **One of those nine is `PAGES_SETUP.md:66`, written earlier the same day**, which quotes the failing
  Liquid expression verbatim in a fenced block. Documenting the error reproduced it. Recorded plainly
  rather than quietly fixed: the corpus is *about* CI, so it is full of `${{ … }}`, and under a Jekyll
  build every markdown file in it is a loaded gun.

  **The real lesson is about scope, not about one more exclusion.** A fence pinned to one folder is a
  fence only while that folder is the source, and the source is a repository setting that changes
  without a commit, a review or a notification. So: `_config.yml` at the repository root is written to
  be correct under the wider setting; `docs/_config.yml` is kept for the narrower one; neither depends
  on the other; and `tests/test_pages_exclude.py` (renamed from `test_docs_pages_exclude.py`) checks
  both, because the next move of that dropdown will not announce itself either.

  The root fence excludes `agent_dev_logs`, `docs`, `docs_site`, `INDEX.md`, `PAGES_SETUP.md`,
  `fixtures`, `tests`, `tools`, `scripts`, `mkdocs.yml`, `ruff.toml` — Jekyll skips `.`/`_` entries on
  its own. **`README.md` is the only file published**, and `jekyll-readme-index` makes it the site
  index, so <https://ufal.github.io/atrium-project/> serves something true at last and the **20
  hub-root links** on the five stub cards resolve. The 40 deep `…/tools/<name>/` links still need the
  real site.

  The guard now compares against `git ls-files` rather than the filesystem — the Pages builder sees a
  fresh clone, so gitignored build output (`site/`, `stubs/`) is not there. It caught that itself on
  its first run, which is the cheapest possible evidence that a bidirectional check earns its keep.

  Verified against `main` at `ffa3053` by `git archive` into a scratch tree: `jekyll 3.10.0` /
  `liquid 4.0.4` with the plugin set github-pages forces reproduces the failure, and the same build
  with the root fence exits 0 with `README.md` → `index.html` as the *entire* output — zero addresses,
  zero `agent_dev_logs/`, zero `docs/`, zero vendored code. Five deliberate breaks of the new guard
  (drop `agent_dev_logs` from the list, add a tracked top-level file, put Liquid in `README.md`, put a
  partner address in `README.md`, delete the fence) each fail as designed.

## 2026-09-21 (later)
- **#57 GH Pages — the infrastructure finished, and the content became the problem.** Re-measured from
  every repository's `pages build and deployment` runs rather than from prose: **all six sites serve,
  all six sources are `gh-pages` / `/ (root)`, every build green.** The hub's
  [run 35614832294](https://github.com/ufal/atrium-project/actions/runs/35614832294) (14:50 UTC,
  `head_branch: gh-pages`) publishes `f9d77d1`, *"Deployed ec06086 with MkDocs version: 1.6.1"*, 87
  files, written by `pages.yml` exactly as designed. Both owner-level dropdowns the plan listed as
  outstanding are done.

  **Two records were wrong and are corrected rather than overwritten.** `atrium-alto-postprocess` was
  never "off, never built" — its `pages-build-deployment` workflow dates from 2026-09-19 08:22 UTC
  with three successful runs, i.e. it was enabled alongside its siblings and the claim was wrong when
  written. And `agent_dev_logs/` holds **23** issue exports, not 49; the full count is 24 digests, 24
  plans, 23 exports, 6 `project_state_*` snapshots, `DEVLOG.md` and `agent_skill_branch_plan.md` = 79.

  That is three editions running in which a hand-written per-repository state table went stale within
  hours. The lesson is the same shape as the fence lesson above: **stop asserting live infrastructure
  state in prose.** Read it from the Actions API at the moment it is needed.

- **#57 — the maintainer's verdict on what shipped: "no new information available."** Correct, and
  structural rather than a gap round 3 would have closed. Counted against the 38 shells' own
  `## Sources` tables: **34 of 38 pages are a second copy of something already published** — 25
  re-slice a tool `README.md`, 6 re-slice a hub `docs/*.md` that is already public on `main`, 3
  re-slice `CONTRIBUTING.md` / `DEVLOG.md` / the hub `README.md`. Four carry new writing.

  A mirror rebuilt on a cron can only tie its source or lag it; there is no state in which the reader
  is better off on the mirror. And the split makes the big manuals worse — the five READMEs are
  36–90 KB operator documents whose value is that one Ctrl-F covers the tool.

  Noted before it shipped: `docs_site/ecosystem/architecture.md` declared its sources as
  `digests/project_state_2706.md` and `project_state_1307.md` — **two of the files the fence exists to
  exclude**, both carrying a personal address. The aggregate design was arranged, by its own source
  table, to route content around the fence.

- **`PAGES_STRATEGY.md` added** — the replacement design. One rule: *the hub publishes what is true
  across repositories; anything true within one stays there and is linked to.* Site goes **38 pages →
  12**, eleven of which are writing that exists nowhere today. `pipelines.md` leads: the end-to-end
  narrative for both branches, including why the born-digital branch is two stages and not six
  (origin-consistency refusing `pages`/`lines` writes; `needs_ocr: true` as the single re-authorisation
  that lets two originators coexist) — reasoning that currently lives **only in the header comment of
  `e2e-digital-smoke.yml`**. Then `external-tools.md`, ~40 entries scoped by measured reference counts
  (Hugging Face 54, LINDAT 14, `w3id.org` 10, AMCR 8). §B (the assembler) and §G
  (`pages-stub.reusable.yml`) of `57.plan.md` are retired; the assembler existed only to manufacture
  the mirror.

  **De-duplication, measured before it was designed:** `CONTRIBUTING.md` is *not* duplicated — five
  files, five distinct checksums, 32,455–112,176 B, sharing a ~9 KB skeleton and four short identical
  sections and then diverging into real per-repo content. Collapsing them into one shared page would
  delete information. What is genuinely shared is `docs/templates/shared/`, whose concepts the hub now
  documents once and transcludes with `pymdownx.snippets` rather than re-splitting.

- **The fences are discharged.** With the Pages source on `gh-pages`, the legacy Jekyll builder no
  longer runs over `main`, so `_config.yml`, `docs/_config.yml` and `tests/test_pages_exclude.py`
  guard nothing. They were load-bearing exactly while they were needed — run 35612083327 is the proof
  — and §H's ordering constraint ("never delete the fence before the dropdown moves") is satisfied by
  the dropdown having moved. The removal is specified in `PAGES_STRATEGY.md` §8.1 with the caveat
  stated once: if anyone points Pages back at `main`, the root publishes unguarded.

  **The removal pass was verified in a scratch clone before being written down**, because deleting
  `docs_site/tools/**` alone fails the build: `mkdocs.yml`'s `nav:` still names all 25 pages and
  `strict: true` turns each into an error — *"Aborted with 25 warnings in strict mode!"* — which fails
  `pages.yml` and stops the deploy entirely. With the `- Tools:` nav block removed in the same commit:
  `mkdocs build --strict` green, `pytest tests/` **111 passed, 22 skipped**, and nothing under
  `.github/` or `scripts/` referencing any deleted file.

## 2026-09-21 (round 3) — the site gets its first real content

- **#57 — ten written tool pages replace the mirror.** `docs_site/tools/page-classification/**`
  and `docs_site/tools/translator/**`, five pages each (`index · guide · reference · changelog ·
  history`), plus the `- Tools:` nav block restored in `mkdocs.yml` for **those two repositories
  only** — under `strict: true` a nav entry with no file is a build failure, so a section may not
  be listed before its pages exist. `nav_order` keeps the round-2 scheme (30–34 and 50–54), which
  leaves 40–44 and 60–74 reserved.

  **The assembler is retired, not deferred.** §B of `57.plan.md` existed to slice each tool
  `README.md` into site pages at build time; that is precisely the mirror the maintainer rejected.
  Every `<!-- ASSEMBLER: -->` marker is gone from the pages that were written, and each page's
  `## Sources` table now records **provenance** — what was read, at which commit — rather than a
  build instruction.

- **The bar each page had to clear, and how it was met.** *A reader is better off here than on the
  README.* Three things earn that, and the shells had none: cross-repository facts the tool
  repository cannot state about itself (block ownership, what reads its output and what does not),
  values read out of the code rather than the prose, and named drift where the two disagree.

  The drift is the strongest evidence these are not mirrors: **30 items for page-classification,
  23 for the translator**, each verified against the source at a named commit and each reported on
  the page as a "Known drift" section. Among them — `v4.2`/`v5.2` accuracies swapped between a
  README table and the prose discussing it; `--file_format` documented as `jpeg` while the config
  ships `png`; `service/README.md`'s `/predict_image` example showing two fields that
  `response_model` filters out and never returns; the translator's README defaulting
  `--source_lang` to `cs` while the shipped `config.txt` says `auto`; a paradata example three
  versions stale, resolving to the wrong licence, with two markdown links pasted inside JSON
  string literals.

- **Two facts the tool repositories cannot publish about themselves, now stated once.**
  `page-classification → alto-postprocess is a human routing decision, not a file handoff` — alto
  never reads `page_categories`. And **no repository reads `TRANSLATED/`**: the translator is a
  terminal branch whose output persists as `derived_from.translated_xml` and is read by nothing.
  `docs_site/pipelines.md` draws both layers — the file DAG that fans out from alto and stops at
  the translator, and the linear record-accretion chain — as the corpus's **first two Mermaid
  diagrams**.

- **Two honest absences, stated rather than papered over.** There are **no published accuracy
  figures for the `v*.4` ensemble** that `--best` has averaged since v1.8.0-beta; every number in
  page-classification's README describes `v*.3`, and the only `v*.4` measurement is a 24-of-229
  prediction diff (#48). And **no BLEU, chrF or COMET number exists anywhere in the translator
  repository** — `eval/bakeoff.py` is a complete harness that has never been run (#4). Both are on
  the page, in an admonition, rather than left for a reader to infer from silence.

- **`fixtures/e2e/README.md`'s truncated section reconstructed.** The file stops mid-sentence at
  "`langID_classify.py` hard-requires CUDA". The explanation, recovered from the workflow itself:
  the E2E alto config sets `SKIP_CLASSIFY = true` because GitHub-hosted runners have no GPU, and
  the hub commits that stage's real output as `DOC_LINE_CATEG/CTX000000003.csv` so stages 4 and 5
  have something to read. It is now written out in `pipelines.md` §W6, with the reconstruction
  labelled as such.

- **`PAGES_STRATEGY.md` has never existed.** It is cited as the authoritative replacement design by
  `PAGES_SETUP.md`, by this file, by `digests/57.digest.md` and by `plans/57.plan.md` — with
  `§`-references (§§1–4, §7 A6, §8.1, §3) that point nowhere. It is in no commit. The 12-page
  design survives only as the entry above it in this log. `PAGES_SETUP.md` now says so at the top
  instead of deferring to it; writing the file is not this round's work, but pretending the
  citations resolve was making three documents wrong at once.

- **`INDEX.md` rewritten and `PAGES_SETUP.md` corrected.** Both still described 38 shells, live
  `_config.yml` fences and a `tests/test_pages_exclude.py` that `f47bf54` had already deleted. The
  same lesson as the three stale state tables before them: a hand-maintained inventory goes stale
  within hours of the commit that invalidates it, so `INDEX.md` now states the check
  (`nav` ↔ `docs_site/`, **23 ↔ 23**, enforced by the build) rather than a count that has to be
  re-typed.

- **Verified.** `mkdocs build --strict` **exits 0** over 23 pages on mkdocs 1.6.1 /
  mkdocs-material 9.7.7 / pymdown-extensions 12.0.1 — and it earned its keep immediately, catching
  **eight** cross-page anchor links whose slugs were guessed rather than computed (`·` and `—`
  each collapse to a doubled hyphen under `pymdownx.slugs.slugify`, which no amount of careful
  typing gets right). `pytest tests/` **111 passed, 22 skipped**, unchanged.
  `workflow_lint.py --offline` **OK**. The built `site/` carries no `ASSEMBLER` marker and no
  draft-shell admonition under `tools/`, and no reference to `arub-p_contacts`.

## 2026-09-22 → 2026-09-23 (round 4) — the static half of the site

- **#57 — the nine remaining hub shells written**, plus the portal: `ecosystem/repository-map`,
  `ecosystem/architecture`, `ecosystem/document-contract`, `contracts/schemas`, `contracts/skos`,
  `contracts/rocrate`, `agent-skills`, `operations`, `contributing-standards`, and `index.md`. **No
  page on the site is a round-2 shell any more.** Each is the page-classification + translator view
  of a contract whose normative text is in the hub's `docs/` — so it links to that text rather than
  condensing it, which was how round 2 produced six pages of re-sliced hub documents. The other
  three tools appear as identity rows only (role, default branch, owned blocks, landing page).

- **Round 3 had shipped two factual errors, now corrected line by line.** Both tool guides named
  the service image `ghcr.io/ufal/atrium-<tool>:<version>-api`. `docker-tool.reusable.yml` appends
  `-<stage>` to the image **name**, so the registry holds `atrium-<tool>-api:<version>` — and the
  version tag has no leading `v`. The wrong form came from the compose files, the Kubernetes
  template, `k8s_deployment.md` and both service READMEs, which all write it; it names a tag that is
  never published. And page-classification's overview repeated the hub schema's claim that the tool
  reads its label list from the filesystem at run time — true only for `--train`/`--eval`, which
  write no record; inference uses `model_registry.CATEGORIES`. Both were caught by reading the code
  this round's pages cite, not by review.

- **The translator's records under-state their licence, and it was run, not inferred.** Driving the
  shared `atrium_document.py` and `atrium_paradata.py` with the translator's own sequence of calls
  and its `para_config.txt`: `process_single_file()` attaches the licence block (`main.py:511`)
  before `lindat_cubbitt` is logged (`:675`, after the first success). The first record of every run
  therefore carries **no translator components** with an explicit `--source_lang` — the E2E's case —
  and only FastText's CC BY-NC 4.0 with `auto`; from the second file on it is correctly CC BY-NC-SA
  4.0. The HTTP service logs components after the call, so every service record under-states.
  page-classification has the mirror image: its CLI records resolve to MIT, its service records —
  written with no paradata logger — fall back to CC BY-NC 4.0 with a `license_note`. The worked
  example on the contract page is that run's output, validated with `jsonschema`, and it resolves to
  **MIT, determined by `vit_models` alone**, while describing a CC BY-NC-SA translation. The same
  licence flows into the RO-Crate: the exporter was run on the same record for the mapping table.

- **What a crate loses, measured.** `page_categories` becomes `DefinedTerm`s under the concept URIs
  but loses which page carries which label and every `category_confidence`; `translations`' contents
  (language pair, backend, output mode) are not mapped at all; both tools' `derived_from` values
  arrive as a bare filename and a run-wide CSV. And neither tool calls the exporter — it is a
  reader, run by hand.

- **Status tables in hub documents that the code contradicts.** `skos_strategy.md` marks F2 (filter
  `collect_images()` to directories) and F3 (`load_vocab.py --from-flat`, a 5-column 4,952-row
  vocabulary) as done 2026-09-16; neither is in `vit` @ `8c98a3d` or `master` @ `88242fe`, and V-3
  says the translator's harvester has no `main()` while it has one. Recorded on the SKOS page with
  both sides quoted — the same pattern as the three stale state tables before it: a hand-maintained
  status goes stale faster than anyone re-reads it.

- **The page-classification Agent Skill cannot start its service through Docker.** Its `server.sh`
  runs `docker compose -f docker-compose.yml up -d` with no `--profile api`, so only the batch service
  starts; `--gpu` passes the overlay alone; `--local` calls a setup script whose paths are relative
  to `setup/`; and the branch `Dockerfile` copies a `setup/requirements-test.txt` the branch does
  not contain. The translator's `server.sh` works — naming the service activates its profile. The
  hub's `server.template.sh` already does all four right; the branch predates it.

- **Formatting adopted from the maintainer.** Round 3's files came back from `b717aab` changed in
  table alignment only. The rule, reverse-engineered and checked against that commit — pad every
  column to its longest cell by character count, one space each side, dashes = width + 2 —
  reproduces 13 of the 14 reformatted files byte-for-byte; the 14th differs only in one table the
  formatter skipped. Applied to every file this round, including tables indented inside content tabs.

- **Not changed, flagged.** `mkdocs.yml`'s `copyright:` and every landing card say "MIT licensed";
  the hub has no `LICENSE` or `CITATION.cff`. The licence statement is the maintainer's to make.

- **Verified.** `mkdocs build --strict` exits 0 over 23 pages on the first pass, every anchor
  resolving; `nav` ↔ `docs_site/` 23 ↔ 23; `pytest tests/` 141 passed, 4 skipped (111 / 22 before —
  more dependencies installed here, no test changed); `workflow_lint.py --offline` OK. The built
  site greps clean for the personal contact address, the partner-contacts file, maintainer handles,
  token prefixes, the grant number and internal secret names. The 17 vendored shared files were
  re-verified byte-identical in both tools at their current heads.

## 2026-09-23 (round 5) — the designed sections filled

- **#57 — the three pages that still carried "pending" placeholders are written**, scoped to
  page-classification and the translator. `pipelines.md` gains W5 (Agent-Skill), W7 (vocabulary
  harvesting, the translator's half), W12 (the annotation round trip, page-classification's half)
  and W13 (RO-Crate export); "the remaining nine" becomes "the remaining five", all of which belong
  to the other three tools. `external-tools.md`'s "Still to write" block becomes real entries for
  everything the two tools depend on — the metadata standards they vendor, CoNLL-U, PDF
  rasterisation, the classifier's ML stack, the translator's other back-ends and metrics, the CI
  and runtime infrastructure, the institutions, and the DMP standards deliberately not implemented.
  `development-history.md` gets the cross-repository chronology, condensed from this file into six
  eras, and the four lessons it keeps repeating.

- **Every inferred behaviour was run, on copies, before it was published.** `sort.sh` reads its CSV
  by position — a wider CSV turns the rest of the row into a nested label folder — creates label
  folders for pages it then cannot find, and rejects a zero-padded page number as invalid octal.
  `filtering.py` refuses the annotation format (`CLASS`) and drops, rather than relabels, a page
  moved between folders. The shipped `small_data_samples/` cannot be trained on with the shipped
  config: its `LICENSE` file is listed as a category and `collect_images()` raises. `pdf2png.sh`
  deletes each PDF it converts and skips `.PDF`. The README's `downscale.py` and
  `result_analysis.sh` invocations fail on their flags. On the translator side, `load_vocab.py`'s
  TEATER `exportAll` path is a stub that returns nothing, the committed vocabulary is still the
  2-column file the harvester no longer writes, and the CTranslate2 scaffold's default compute type
  `int4` is rejected by CTranslate2 4.8.2. In the shared `para_licenses.py`, SPDX spellings such as
  `CC0-1.0` and `cc-by-sa-4.0` are unrecognised, and an unrecognised licence becomes the run's
  effective licence with no URL and both restriction flags false.

- **Four round-3 statements corrected, line by line.** page-classification's `--train` resolves to
  **CC BY-NC 4.0**, the value `para_config.txt` declares — not the README's CC BY-NC-SA 4.0, which
  round 3 repeated on `pipelines.md` W8 and on the tool's overview and reference pages;
  `amcr-inputs.txt` holds 15 URLs, not 16; OAI-PMH is named by all three repositories that use it,
  not by none; UDPipe's model names carry a `-241121` suffix.

- **Two things could not be checked from here, and the pages say so.** AIS CR's own site and the
  LINDAT dataset record were unreachable, so the AIS CR entry states only the hosts the code relies
  on, and the dataset's published licence is left as the README / `LICENSE` / `para_config.txt`
  disagreement it is.

- **Verified.** `mkdocs build --strict` exits 0 with no warnings; `nav` ↔ `docs_site/` 23 ↔ 23;
  every markdown table on the three pages renders as a table; `pytest tests/` 141 passed, 4 skipped;
  `workflow_lint.py --offline` OK. The built site greps clean for the personal contact address, the
  partner-contacts file, maintainer handles, token prefixes, the grant number, internal secret
  names, CI run IDs, and cluster paths and hostnames.

## 2026-09-23 (round 6) — the site states only what stays true

- **#57 — all 23 pages rewritten to a durable bar**, still scoped to page-classification and the
  translator. The maintainer's TODO asks for "static, unchangeable claims"; rounds 3–5 had held
  every page to "values verified against code, and named drift where the two disagree", which
  published audit material that goes stale within days — two tool "Known drift" lists (20 and 17
  items), the agent-skills drift table, the contributing-standards "Contradictions" section, the
  schemas "What the schema says that the code does not", the rocrate "What a crate cannot yet
  say", "Written so far / round N" admonitions, dated counts, and SHAs and `file:NN` references
  in prose. All of it was stripped from the published pages and **relocated, not deleted**:
  `agent_dev_logs/digests/57.findings.md` groups every finding by the repository that owns the
  fix, each re-checked against the current heads and marked open, resolved-at-SHA or unverified.
  It sits outside `docs_site/`, so MkDocs never publishes it. `INDEX.md`'s bar changes with it:
  a page must now also *stay true until the tool changes*.

- **Lasting content the pages lacked was written in their place.** page-classification: how a
  prediction is made (resize → normalise → softmax → Top-N; `--best` averages each model's Top-N
  probabilities, `--average` averages fold weights), label naming and what each category suggests
  doing next, preparing input and the `<doc>[-_]<page>.png` convention, reading the output with
  real rows from a committed `v4.3` result table, the `vX.Y` revision scheme, YOLO-cls and CLIP,
  `curl` examples, how to cite. Translator: how a translation is made, metadata (AMCR) mode step
  by step (secure parser, namespace discovery through OAI-PMH envelopes, per-field detection,
  idempotent `append`), vocabulary protection (Tag-and-Protect for `lindat`, prompt glossary for
  LLM back-ends — and none for the ct2 NMT families), language identification and pair discovery,
  a dual-pass Mermaid diagram, a code map, design limits. Hub: "How the ecosystem works" with a
  diagram on the portal, a workflow index on Pipelines, a glossary of terms on External tools,
  the deployment model and a batch-image quick start on Operations, "Anatomy of a tool" on
  Architecture, the record's life cycle and how its licence is computed on the document
  contract, release steps and a shared-code rule on Contributing standards, a Turtle concept and
  an RO-Crate excerpt produced by the real exporter.

- **Re-read at the current heads, and five things had moved.** page-classification `vit` is at
  `adee922` (the pages cited `8415ce7` / `8c98a3d`): `a95c6c6` reworked `pdf2png.sh`, `sort.sh`
  and `filtering.py`, so the round-5 data-script findings are resolved at source; the README now
  gives the dataset licence as CC BY-NC 4.0 everywhere. The translator `master` is at `71feaef`
  (pages cited `88242fe`): `ct2` is registered — the Reference's `--backend` row still said only
  `lindat` / `openai_compatible`. The translator's first-record licence ordering is **still**
  open at `71feaef`, so the document-contract worked example no longer displays the translator
  record's licence; the page states the rule, and the defect is in the register.

- **One site defect, found by building rather than reading.** Both tool index pages carry the
  `atrium-pipeline` strip as `markdown="0"` raw HTML with `href="../<tool>/index.md"`. MkDocs
  rewrites `.md` links only in Markdown-generated HTML, so the built pages linked to
  `…/tools/<tool>/index.md`, which does not exist — and `--strict` cannot see it. Now
  `../<tool>/`. Two smaller ones: page-classification's history linked an `agent_dev_logs/issues/`
  the repository does not have; `external-tools.md` pointed at a Known-drift item (handle
  `1-5959`) the list never contained.

- **Verified.** `mkdocs build --strict` exits 0 with no warnings over 23 pages, `nav` ↔
  `docs_site/` 23 ↔ 23; 128 of 128 markdown tables render as tables; seven Mermaid diagrams
  render; the pipeline-strip links resolve; the body sweep for time-bound wording leaves only
  tool names, settled history and behaviour; the built site greps clean for e-mail addresses,
  handles, token prefixes, the grant number and run IDs. `pytest tests/` 141 passed, 4 skipped;
  `workflow_lint.py --offline` OK — no code changed.

## 2026-09-23 — TEITOK format 2 reaches the hub (nlp-enrich #9/#10/#28, Stage 5)

* `fixtures/atrium_document.example.json`: TEITOK references are the file-local ids nlp-enrich's format-2
writer emits (`teitok_surface` `facs-1`/`facs-2`, `teitok_ref` `s-3`/`n-5`); `docs/document_schema.md`
documents them (local to `<doc_id>.teitok.xml`, plain strings, `teitok_surface` only for ALTO pages).
* `e2e-pipeline-smoke.yml`: nlp-enrich runs with `SAVE_TEITOK=true`, the failure artefact includes the TEITOK
file, and `tools/e2e/e2e_assert.py --teitok-dir` checks that the document's `.teitok.xml` exists, is TEI with
tokens, and contains every `<surface id>` / `teitok_ref` the record points at. Entity refs are strict for
`version="teitok-2"` files and only reported for older ones, so the lane stays green on released images.
Tests in `tests/test_e2e_assert.py`.
* Not touched, on purpose: `docs/templates/shared/atrium_vocab.py` (byte-identical in five tool repos; its
authority `teitok_alto.py _CNEC_TO_CONLL` still exists, now an alias of nlp-enrich's `ner_types.CNEC_TO_CONLL`
and pinned equal by nlp-enrich's `tests/test_ner_types.py`) and `docs_site/external-tools.md` (nlp/llm entries
belong to a later #57 round). Branch `claude/inspiring-cerf-2gdtd1`, local, awaiting review.

## 2026-09-24 — TEITOK round 4 (nlp-enrich #38); the hub's `13.*` logs were another repo's

* **The `13` mix-up.** `agent_dev_logs/digests/13.digest.md` and `plans/13.plan.md` held the data-format strategy of
**atrium-llm-enrich #13** ("The intermediate steps — data format to use"), while hub **#13** is the CAA Proceedings
paper. The 2026-09-23 "Current state summary" about TEITOK ids and the E2E check was posted on hub #13 for the same
reason. The pair is rewritten for the CAA paper (deadline 2026-10-31); the design content moved to llm-enrich's own
#13 logs; moving the misposted comment is a user action. Earlier lines of this file that say "#13" in the data-format
sense — 2026-07-24 ("digests + plans refreshed for #13"), 2026-07-29 ("the #13 document accretion") and the
2026-09-23 Stage-5 entry — mean atrium-llm-enrich #13.
* **nlp-enrich v0.21.0** (TEITOK format 2) is tagged and published, so `:latest` now writes format 2; the E2E, which
last ran on 09-23, has not run on it yet. Its `--teitok-dir` check is strict for exactly `version="teitok-2"`, which
the round-4 plan keeps. _(It ran after the push, 2026-09-24: run 35990199050, green — next entry.)_
* **Round-4 findings that touch the hub:** `docs_site/pipelines.md` W11 misdescribes flexiconv (it converts *into*
TEITOK, in nlp-enrich and llm-enrich only); `docs_site/external-tools.md` attributes TEI/TEITOK and flexiconv to the
wrong tools and has no TEITOK/flexi* entries; `docs/document_schema.md` needs `teitok_surface` for converted layout
documents, a note that `lines[].teitok_ref` is not written yet, and the record-vs-TEITOK bbox units;
`tools/e2e/e2e_assert.py` accepts a reference that matches any element id and does not check pages.
* **Small corrections:** `digests/24.digest.md` / `plans/24.plan.md` (llm-enrich no longer carries `teitok_alto.py`;
plan title), `digests/53.digest.md` (pin line), `plans/54.plan.md` (#13 references name atrium-llm-enrich). The
`13`, `24` and `53` files are on `test` as `d006088` (with the tables re-padded); `plans/54.plan.md` is not yet. _(`plans/54.plan.md` landed in `eec0682`; `d006088` had also written #54's plan over `plans/53.plan.md` — restored in round 5.)_
* **Round 4 implemented the same day (delivered as files, then pushed as `eec0682`).**
  * `tools/e2e/e2e_assert.py` `assert_teitok`: for a `teitok-2` file an `entities[].teitok_ref` must name a `<name>`
    and a `lines[].teitok_ref` an `<s>` (`wrong_kind`), and `entities[].page` must equal the `<pb n>` in force where
    the `<name>` starts (`wrong_page`) — the check that would have caught nlp-enrich's page defect; older files keep
    report-only refs; the legacy `</n>` close tag is repaired before parsing. Four new tests in
    `tests/test_e2e_assert.py`; a real stage-4 record + TEITOK pair from nlp-enrich's round 4 passes.
  * Docs: `docs_site/pipelines.md` (W11 in both tables: flexiconv converts *into* TEITOK, in nlp-enrich and
    llm-enrich), `docs_site/external-tools.md` (TEITOK writer/readers, flexiconv's licence, pin and owner),
    `docs/document_schema.md` (`teitok_surface` for converted layouts, `entities[].page` = the page of the `<pb>` in
    force, `lines[].teitok_ref` not written yet, record bbox units vs TEITOK boxes), `docs/agent_skill_strategy.md`
    (llm-enrich accepts no ALTO; nlp-enrich takes a lines file + ALTO or a converted TEITOK), `docs/docker_gha_roadmap.md`
    (H2: the VCS pins are closed, the hub's unpinned tooling installs remain).
  * `pytest tests/`: 169 passed; `mkdocs build --strict` and `tools/ci/workflow_lint.py --offline` clean.
  * Still the user's: move the misposted 09-23 comment from hub #13 to atrium-llm-enrich #13; dispatch the E2E on the
    released nlp-enrich image (the first format-2 run) and again once the round-4 change set is released. _(The first format-2 run happened on the push: 35990199050. The #13 note was left where it is, by decision.)_

## 2026-09-24 (later) — round 4 pushed and green; round 5: format docs, ALTO-only pages fixed, dev logs

* **Pushed.** `eec0682` on `test` and `main`, and `v1` moved to it. On it: the E2E pipeline smoke (35990199050, the
first run on TEITOK format 2, with the stricter `assert_teitok`: CTX000000003, 1/1 references resolved), the digital-born
smoke (35990199010), the cross-repo fast-lane matrix (35990199041), the docs site (35990199021) — all green. The tool
repos' round 4: nlp `8003051`, llm `951db5e` (+ `08dff48`), alto `fb72526` (+ #31 Phase 4 up to `2e2794d`).
* **Round 5 in the hub (docs only).** alto-postprocess was described as ALTO-only; now `docs_site/pipelines.md` (W1 note,
W11 with both format-adaptation routes, Sources row), `index.md` (diagram edge, card), `ecosystem/repository-map.md`
(role, per-format origins, Sources), `external-tools.md` (ALTO v3-only splitter caveat, links to alto-postprocess's
*Formats and their standards* and nlp-enrich's TEITOK sections, Sources), `_generators/repos.py` (tagline, role — the
regenerated alto landing card is not pushed), `docs/document_schema.md` (the bare `pdf` prefix the table lacked, the
origins alto-postprocess records, the `digital-born-*` kinds nobody originates yet), `docs/agent_skill_strategy.md` and
`docs/k8s_deployment.md` (alto inputs). `pytest tests/` 169 passed, `mkdocs build --strict` clean.
* **Dev logs.** Milestones relabelled on 2026-09-08 put into every pair that still had the old label (#4, #6, #10,
#15, #16, #17, #18, #21, #22, #32, #40, #51, #56). Threads recorded that the pairs had missed: #4 (the WP4 deliverable,
the five owned SSHOMP records), #6 (licence template, repos needing updates; licences added since), #18 (execute or
retire `docs/docker_gha_roadmap.md`), #21 (dataset re-published as hdl 1-5959), #22 (`bench_compare.py`, SDG, Alfie's
comment; the "re-integration already built" claim corrected), **#24 (the 2026-08-01 three-format decision and its
JSON-2-MD / TEITOK-2-MD TODO)**, #32 (JSON inputs on `test` and `agent-skill`; two of five gap fixes in the tree),
#51 (09-17 status, V-5), #53 (09-15/09-16 status; **plan restored** from `c6a8ce5` — `d006088` had overwritten it with
#54's), #54 (freeze tag still not cut), #55, #57, #58. **New pair: #66** (Galaxy).

## 2026-09-25 (round 7) — workflow narratives, landing cards, SSHOMP and Galaxy preparation

* **Inputs re-read.** All six repositories at their `test` heads (hub `8de7896`, pc `adee922`, alto `a584b7d`,
translator `524d627`, nlp `53e60c5`, llm `8831399`); every repository's issue exports (regenerated 09:21) checked
against the live API — the newest comments are K4TEL's on #4 (05:54: `j9fqxo` submitted, all five tool records
updated) and #57 (05:43). The SSH Open Marketplace record pages read anonymously: the four approved tool versions
(`106106`–`106124`) still carry the July texts plus one diagram each; `j9fqxo` and `0xSpVP` v`106039` are not public.
The marketplace API and every Galaxy site are blocked from this session; Galaxy was read through its GitHub sources.
* **#57 — Workflows section** (`docs_site/workflows/`, six pages). An overview with the fixed narrative shape, the two
depths and the field table (narrative → SSHOMP workflow record → Galaxy `.ga` → Workflow RO-Crate); full narratives
for page-classification and the translator, each with a Galaxy sheet; stable-core narratives for alto-postprocess,
nlp-enrich and llm-enrich, written from their release tags (`v1.5.1-beta`, `v0.21.0`, `v0.7.0`) with a *Scope* box.
`external-tools.md` gains SSH Open Marketplace, TaDiRAH, Galaxy, WorkflowHub and two glossary terms; the portal,
Pipelines, both tool overviews and the repository map link the new pages; `mkdocs.yml` nav has the new group.
* **#57 — landing cards.** `_generators/repos.py` gets `docs_path` per repository (tool section where one exists,
workflow page otherwise) and `make_stubs.py` uses it; nlp-enrich's chips become Python 3.11 and YAKE · KeyBERT. The
regenerated `gh-pages` files differ from the deployed ones only in the intended lines (alto: tagline, role, links;
nlp: chips, links; llm: links; pc/translator: date and README wording).
* **#4.** Digest and plan refreshed for the 09-25 submissions; `13eHAZ` decided → rebuild (B5 re-cut from the
translator narrative, durable wording); new Appendix C (page-classifier workflow record) and Appendix D (phrases in the
submitted texts that will date, with durable replacements).
* **#17.** Digest and plan rewritten: `0xSpVP` v`106039` (11 steps) submitted 09-24, awaiting moderation; the check to
run once it is public; relating `13eHAZ` and the new pc workflow record to it.
* **#66.** Digest and plan rewritten from the Galaxy research: DARIAH's `atrium-galaxy-tools` already pairs an
ATRIUM Galaxy workflow with its SSHOMP narrative (`IrpmkB`); ssh.usegalaxy.eu is a usegalaxy.eu subdomain with no MT,
UDPipe/NameTag, keyword, language-ID or OCR-QC tool; `alto` and `tei` datatypes exist, `conllu` does not; custom
containers run there. Seven questions for M. A. Greenwood (which server, which route, containers vs conda, network and
models, GPU, `.ga` metadata, access). The planned `docs_site/operations/galaxy.md` is replaced by the Galaxy sheets.
* **#57 digest / plan / findings.** Digest status and ⏳ Open rewritten (the fences and mirror were already gone); a
round-7 block with the remaining work at the top of the plan; `57.findings.md` gains round-7 lines and first sections
for alto-postprocess, nlp-enrich and llm-enrich.
* **Verified.** `mkdocs build --strict` exits 0 with no warnings (mkdocs 1.6.1, mkdocs-material 9.7.7,
pymdown-extensions 12.1); `nav` ↔ `docs_site/` 29 ↔ 29; 152 of 152 markdown tables render as tables; 7 Mermaid
diagrams; no built link to a missing tool section; no e-mail address or maintainer handle in the built site; the
time-bound-wording sweep is clean on the new pages; tables re-padded by the maintainer's rule; `ruff check
_generators/` clean; `pytest tests/` 154 passed, 2 skipped (HEAD export: 152 passed, 4 skipped — the two extra skips
need a git checkout); `workflow_lint.py --offline` OK.
* **Not pushed.** Hub files and the regenerated `gh-pages` cards are delivered as files; pushing is the user's step.

## 2026-09-25 — atrium-alto-postprocess#31 Phase 5: the cross-repo follow-ups

* **`KNOWN_PIPELINE_SUFFIXES`** (canonical `atrium_document.py` and the client skeleton's mirror): the single-dot inputs
  alto-postprocess's text-lines method reads (`.pdf .docx .docm .dotx .odt .ods .odp .xlsx .xlsm .pptx .pptm .epub .rtf
  .html .htm .xhtml .hocr .tei .jsonl .ndjson .tsv .tab .markdown .mdown .text .log .srt .vtt .eml .mbox .mbx .zip`);
  compression wrappers deliberately not (`x.txt.gz` would become `x.txt`). `scan.2019.pdf` is now `scan.2019`, not
  `scan`. **Decided with K4TEL:** this also turns `CTX01.scan.pdf` into `CTX01.scan` (it was `CTX01` by the first-dot
  fallback), so page-classification's two tests that pinned that change in the same re-vendor. Tests: canonical_doc_id
  cases and a skeleton-mirror check in `tests/test_document_record_doc_id.py`. Swapped into all five tool repos in-session:
  alto-postprocess, llm-enrich, nlp-enrich and translator unchanged; page-classification only the two tests above.
* **`tests/test_document_required.py`:** call sites named `<repo>/<file>::<function>` instead of line numbers (five had
  drifted); new shapes: json-keys `page_split`, `text_split` (OCR and born-digital, source only), and the text-lines
  extractor as the fifth extract twin; source-only records carry `assembled` without `blocks`, as the tools write it.
* **V-1:** the F1 row said "done 2026-09-16", but llm-enrich still filtered `{Garbage, Inverted}` and the pinning test did
  not exist. Fixed in llm-enrich now; `skos_strategy.md` §6/§7, `document_schema.md`, the canonical `atrium_vocab.py`
  comments and the schema's `categ` description agree.
* **`ORIGIN_ORIGINATORS`:** the `digital-born…` prefix stays by decision; `document_schema.md` says why (a §1a change
  for all repos; alto-postprocess's `SOURCE_ORIGIN_BY_KIND` is the per-site answer).
* Hub `pytest tests/` 184 passed, 1 skipped; shared tests 158 passed, 2 skipped; `ruff` clean. **Next (the user's):**
  merge, retag `v1`, re-vendor `atrium_document.py`, `atrium_document.schema.json` and `atrium_vocab.py` into the five
  tool repos together with page-classification's two tests. Not pushed: files delivered in chat.
