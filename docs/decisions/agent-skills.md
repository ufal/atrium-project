# Agent skills: decisions and history

> **In short.** How the ATRIUM services were wrapped as Agent Skills in July–October 2026: the decisions taken at
> planning time, the per-repository work plans (all done), the rollout order and how sub-issues were tracked. The
> current rules are in [`../agent_skill_strategy.md`](../agent_skill_strategy.md); this page is the record of how
> they came about. It names the repositories as they were then: `alto-postprocess` is now `ocr-postprocess`, and
> the keyword stage of `llm-enrich` is now `keyword-extract`.

> **Status:** history, moved here from `agent_skill_strategy.md` on 2026-11-21.

## The strategy's original header

_Issue: [ufal/atrium-project#31](https://github.com/ufal/atrium-project/issues/31) · Status: **implemented on all five `agent-skill` branches** (2026-07-18) → refinement stage (validation CI · acceptance · consistency · release); Appendices A–D promoted to [`templates/skill/`](../templates/skill/) · Date: 2026-07-17_
_Scope: normative for the `agent-skill` branches of the five service repos
(atrium-page-classification · atrium-translator · atrium-alto-postprocess ·
atrium-nlp-enrich · atrium-llm-enrich). Per-repo implementation is tracked in
sub-issues lifted from [§10](#10-per-repo-work-plans)._
_Round 2 of [#32](https://github.com/ufal/atrium-project/issues/32) (2026-09-28): the typed
contract and the spec as a release artefact — §2.2 reversed, §4.1 `openapi_sha256`, §4.4 reason
registry, new [§4.8](../agent_skill_strategy.md#48-typed-contract-and-the-spec-as-a-release-artefact-normative), §12.1._

Decisions fixed at planning time:

1. **llm-enrich gains a minimal FastAPI `service/` layer first** (mirroring nlp-enrich), so all
   five repos follow one server–client standard.
2. **Standardization covers the meta-contract only** — `GET /info`, `GET /health`, upload
   conventions, error codes, env vars, versioning. Every service **keeps its domain primary
   endpoint** (`/predict_*`, `/translate`, `/process`, `/enrich`, `/extract_keywords`).
   No breaking API changes.
3. Defaults chosen for open points: llm-enrich endpoint named `/extract_keywords` (over
   `/enrich_llm`); hosted (LINDAT) base URLs unknown → docs use `http://localhost:8000` with
   placeholders; translator's `400`→`422` alignment is a silent additive fix.

## 10. Per-repo work plans

Each subsection is self-contained and liftable verbatim into a sub-issue ([§13](#13-sub-issue-creation--tracking)).

> **Status (2026-07-18):** ✅ all §10 build items implemented and verified on the five
> `agent-skill` branches (frontmatter valid · clients `--help` clean · import closures intact ·
> `/info`+`/health` conform · no dangling refs · no false paradata claims). Two caveats noted
> inline: (i) the "default-branch pre-work" items landed on the `agent-skill` branches — carrying
> them back onto each default branch is the manual merge-forward tracked in §12.2; (ii) llm-enrich
> ships **synchronous** (async jobs is the conditional W5 fast-follow). Remaining #31 work is the
> **refinement stage** (validation CI §12.3 · contract-test audit §12.1 · acceptance · release),
> not §10.

### 10.1 atrium-page-classification — exemplar hardening

**Goal:** make the existing `agent-skill` branch fully conform to this standard, so it is a
trustworthy reference for the other four.
**Current state:** branch exists with SKILL.md, `scripts/atrium_classify.py`,
`scripts/server.sh`, trimmed tree, `small_data_samples/`. Four known defects; no `/health`;
default branch is `vit`.

- [x] Fix (a): all references say `scripts/server.sh` (SKILL.md Workflows and the client's
      error message currently say `serve.sh`).
- [x] Fix (b): remove the `atrium_paradata.py` provenance claim from SKILL.md — or wire the
      module in `service/` on the branch; default: remove the claim (§4.7).
- [x] Fix (c): drop the `frontend-lindat/` references from `service/README.md` (or restore the
      directory).
- [x] Fix (d): reconcile `service/README.md` + `frontend/script.js` documented response fields
      (`model_version`, `filename`, `thumbnail`, …) with what `service/api.py` returns.
- [x] Add `GET /health` (+`?deep=true` model-loaded probe) per §4.1 on the default branch
      (`vit`), then merge forward to `agent-skill`; extend `/info` with `service`, `endpoints`,
      `limits` keys (§4.1).
- [x] Align SKILL.md section order to §7; add the anti-pattern checklist to the branch's PR
      template or review notes.
- [x] Add the contract test (§12.1) on the default branch.

**Acceptance:** anti-pattern checklist passes; `atrium_classify.py` smoke-tested against
`small_data_samples/` via a locally started server; `/info` and `/health` conform to §4.1.

### 10.2 atrium-nlp-enrich — first full skill run (template validation)

**Goal:** create the `agent-skill` branch for the most mature service; validate the templates.
**Current state:** richest API (enrich/enrich_text/rescale + async jobs, `/info` + `/health`
already conforming), two frontends, excellent `service/README.md`. No skill layer.

- [x] Create `agent-skill` branch from the default branch head; flatten/trim per §5.
- [x] Write `SKILL.md` per §7 (`name: atrium-nlp-enrich`; domain reference = stage plan,
      keyword methods, limits).
- [x] Write `scripts/atrium_enrich.py` per §6: covers `/enrich` (file), `/enrich_text` (JSON
      lines), `--jobs` async mode (submit → poll → result, 429-aware messaging), `--info`;
      flags: `--kw-method keybert|yake|legacy|none`, `--num-keywords N`, `--zip` (workspace
      download).
- [x] Write `scripts/server.sh` per Appendix C (compose `api` profile).
- [x] Add `small_data_samples/` (a few small text-line files + a small TEITOK page + LICENSE).
- [x] Branch `README.md` per §8.
- [x] Frontends (`frontend/`, `frontend-lindat/`): API footer per §9.
- [x] Extend `/info` with the `endpoints` list (§4.1 — the one missing required field).
- [x] Afterwards (hub repo): promote Appendices A–D to `docs/templates/skill/` with any
      corrections this run surfaced.

**Acceptance:** skill installed in a clean `~/.claude/skills/` drives a full enrich round-trip
against a locally composed server using only SKILL.md instructions.

### 10.3 atrium-alto-postprocess

**Goal:** contract alignment + skill branch.
**Current state:** solid API (`/process`, `/info`), two frontends, best-in-family
`service/README.md`. No `/health`; CORS default is a localhost list; no skill layer.

- [x] Default-branch pre-work: add `GET /health` (+`?deep` → models loaded); align
      `ALLOWED_ORIGINS` default to `*` (§4.5); adopt `MAX_UPLOAD_MB` (§4.5); extend `/info`
      with `service`, `endpoints`, `limits` (currently keys the id as `"status"`).
- [x] Create `agent-skill` branch per §5 (drop `frontend-lindat/` from the branch or keep it —
      but docs must match, defect (c) rule).
- [x] `SKILL.md` per §7 (domain reference = five quality categories + `line_fields`).
- [x] `scripts/atrium_postprocess.py` per §6: `--task-type auto|alto|text`, table/csv/json of
      per-line `lang`/`quality_score`/`category`.
- [x] `scripts/server.sh`, `small_data_samples/` (1 small ALTO XML + 1 TXT), branch README.
- [x] Both frontends: API footer per §9; verify `service/README.md` against `api.py` reality.

**Acceptance:** as 10.2, with a `/process` round-trip on the ALTO sample.

### 10.4 atrium-translator — biggest documentation gap

**Goal:** bring the service up to family documentation standard, then the skill branch.
**Current state:** working API (`/translate`, `/info`) but **no frontend, no
`service/README.md`**; `MAX_UPLOAD_BYTES` naming; `400` for non-XML; no `/health`.

- [x] Default-branch pre-work:
  - [x] **Write `service/README.md`** (Appendix D): `/translate` + `/info` table, curl with
        `source_lang`/`target_lang`/`is_alto`, XML-attachment response semantics
        (`Content-Disposition`), env vars (`TRANSLATION_BACKEND`, limits), compose run.
  - [x] **Add minimal `service/frontend/`** (file picker + lang selectors + result download +
        API footer per §9), mounted like the siblings.
  - [x] Add `GET /health` (+`?deep` → backend reachability probe, e.g. LINDAT HEAD).
  - [x] `400`→`422` for non-XML uploads (§4.4); `MAX_UPLOAD_MB` with `MAX_UPLOAD_BYTES`
        fallback (§4.5); extend `/info` with `service`, `endpoints`, `limits` (currently
        `"name"`).
- [x] Create `agent-skill` branch per §5; `SKILL.md` per §7 (domain reference = ALTO vs
      metadata-XML modes, language matrix, backend selection).
- [x] `scripts/atrium_translate.py` per §6: `--source-lang` (default `auto`), `--target-lang`
      (default `en`), `--alto/--no-alto`, output translated XML to stdout or `-o FILE`.
- [x] `scripts/server.sh`, `small_data_samples/` (tiny ALTO + tiny metadata XML), branch README.

**Acceptance:** as 10.2, with a `/translate` round-trip producing valid XML from the ALTO sample.

### 10.5 atrium-llm-enrich — new service layer + skill

**Goal:** give the CLI-only repo the standard FastAPI `service/` layer (decision #1), then the
skill branch. The service can be built any time after this doc merges; only the skill branch
depends on it.
**Current state:** no HTTP surface. Entry points `llm_run.py` (local transformers/vLLM),
`openrouter_client.py` (remote), `ollama_client.py` (local Ollama) behind
`llm_client_shared.py`; reusable input parsers in `api_util/` (`teitok_read.py`,
`xml_to_md.py`, …); vocab via `vocab_manager.py`; Docker images are batch-only (no ports).

- [x] Build `service/api.py` mirroring nlp-enrich's layout:
  - `GET /info` — `service`, `version` (from `para_config.txt`), `endpoints`, available
    backends, vocabulary info (TEATER/AMCR), `limits`.
  - `GET /health` — shallow ok; `?deep=true` probes the selected backend (Ollama reachability /
    OpenRouter key present / local model loaded).
  - `POST /extract_keywords` — multipart `file` (TXT/CSV or TEITOK/ALTO XML; reuse
    `api_util/teitok_read.py` + `api_util/xml_to_md.py` for parsing); params
    `backend=openrouter|ollama|local` (default env-driven), `vocab=teater|amcr`, `top_k`.
  - `POST /extract_keywords_text` — JSON `{"lines": [...]}` sibling (§4.3).
  - Response rows: `{keyword_cs, keyword_en, category, confidence}` per line/document.
  - Dispatch to the existing clients via `llm_client_shared.py`; **keep torch out of the
    remote-only path** (the repo's established constraint).
- [x] `service/requirements.txt`, `service/README.md` (Appendix D), minimal `service/frontend/`
      with API footer (§9).
- [x] Docker: `api` stage/profile, port 8000, python:3.11-slim non-root — match siblings. Env:
      `OPENROUTER_API_KEY`, `OLLAMA_HOST`, `HF_TOKEN`, `MAX_UPLOAD_MB`, `ALLOWED_ORIGINS`.
- [x] ⚠️ LLM calls are the slowest in the family: start synchronous; adopt nlp-enrich's
      `service/jobs.py` async pattern as a fast-follow if sync proves impractical.
      _(Shipped synchronous; async jobs deferred to the W5 fast-follow. Corrected 2026-09-27
      (atrium-project#53): this note used to say "with a strict concurrency guard + `504`
      timeout", but `service/` has neither — no semaphore, no 429, no request deadline; each
      upstream call is bounded only by `LLM_TIMEOUT` × `LLM_MAX_RETRIES`, both reported in
      `/info`.)_
- [x] Then: `agent-skill` branch per §5; `SKILL.md` per §7; `scripts/atrium_keywords.py` per §6
      (`--backend`, `--vocab`, `--top-k`); `scripts/server.sh`; text samples; branch README.

**Acceptance:** as 10.2, with an `/extract_keywords_text` round-trip on sample lines against at
least one backend (Ollama or OpenRouter with a test key).

## 11. Rollout order

1. **This doc** merged into atrium-project; sub-issues created from §10 (per §13).
2. **page-classification hardening** (10.1) — small; makes the exemplar trustworthy.
3. **nlp-enrich** (10.2) — validates the templates → **promote Appendices A–D to
   `docs/templates/skill/`** in the hub repo.
4. **alto-postprocess** (10.3) and **translator pre-work** (10.4 first block) — parallelizable.
5. **translator skill branch** (10.4 rest); **llm-enrich** (10.5 — service first, skill after).
6. **`skill-validate.yml`** reusable workflow in the hub (§12.3) once ≥2 skill branches exist;
   callers wired into each repo's `agent-skill` branch.

## 13. Sub-issue creation & tracking

- One GitHub sub-issue per repo under #31, titled **`agent-skill: <repo-name>`**, body = the
  repo's §10 subsection + a pinned-commit link to this doc. Labels/milestone per project
  convention (`enhancement`, `development` · Q3 milestone).
- Implementation happens on each repo's **`agent-skill`** branch: page-classification updates
  the existing one; the others create it **from the default branch head** (translator: `master`;
  alto-postprocess: `master`; nlp-enrich: `master`; llm-enrich: `main`).
- Each implementation session is logged in that repo's working records, which its
  `docs/development.md` links.

## The skills catalog, retired 2026-11-21

`docs/skills_catalog.md` listed the six skills; its table now lives, checked against the branches, on the
site's [Agent skills](../../docs_site/agent-skills.md#the-six-skills) page. Its dated parts are kept here.

> **Names (2026-10-21):** the skills were first written for `alto-postprocess` and `llm-enrich`, whose repositories
> are archived. ocr-postprocess's skill now carries its own name; keyword-extract's and digital-convert's skills are
> new, built from the skeleton for their own endpoints (keyword-extract takes a record or plain text, not llm-enrich's
> CSV of lines). Use `ATRIUM_KW_URL` for keyword-extract; `ATRIUM_LE_URL` belonged to llm-enrich.

**The pipeline order the catalog gave** (before ARÚP's output contract of 12 November 2026; the route is now on the hub's Pipelines page):

```
scan → page-classification → ocr-postprocess (quality filter) → translator ─┐
                                                                         ├─→ nlp-enrich → keyword-extract
                                                                     (Clear lines only)
```

Route only `Clear`/`Noisy` lines from ocr-postprocess into the downstream NLP and keyword stages.

## Status and tracking, as of the 21 October sync

Implemented on five `agent-skill` branches on 2026-07-18, and on digital-convert's on 2026-10-21. Each is kept in
step with its repo's `test` branch by hand, per [`agent_skill_strategy.md`](../agent_skill_strategy.md) §12.2, with
`tools/skill_ify.py` deriving the tree and `tools/skill_drift_check.py` checking it.

**Last sync: 2026-10-21** (atrium-project#77 C), from the `test` heads of that morning. `skill_drift_check.py`
reports **6/6 aligned**; each `service/README.md` is the repo's runbook with the trimmed parts pointed at `test`,
declared in `DOCUMENTED_DIVERGENCES`. In that pass:

- every client retries a `502` only when it is not final (`RETRY_502_REASONS`), exits `1` on a usage error, and
  every `scripts/server.sh` waits for `/ready`; `skill_drift_check.py` now fails a client that retries every `502`;
- keyword-extract and digital-convert got skills of their own, replacing the llm-enrich and nlp-enrich copies;
  ocr-postprocess's skill is named `atrium-ocr-postprocess`; nlp-enrich's no longer offers keywords (they left it
  in 1.0.0);
- `skill_ify.py apply` keeps the files only the skill branch carries, and their file modes.

Treat any snapshot here as perishable: run the tool rather than trusting this line.

Refinement still open: one green `skill-validate` run per branch with the repaired callers,
live end-to-end acceptance round-trips, and release tags. The per-repo `agent-skill: <repo>`
sub-issues under #31 (§13) have **not** been created — tracking is in the hub's working records
for #31 meanwhile ([Development history](../../docs_site/development-history.md#the-working-records)).
