# 🧩 ATRIUM Agent-Skill Strategy — API services as LLM Agent Skills

_Issue: [ufal/atrium-project#31](https://github.com/ufal/atrium-project/issues/31) · Status: **implemented on all five `agent-skill` branches** (2026-07-18) → refinement stage (validation CI · acceptance · consistency · release); Appendices A–D promoted to [`templates/skill/`](templates/skill/) · Date: 2026-07-17_
_Scope: normative for the `agent-skill` branches of the five service repos
(atrium-page-classification · atrium-translator · atrium-alto-postprocess ·
atrium-nlp-enrich · atrium-llm-enrich). Per-repo implementation is tracked in
sub-issues lifted from [§10](#-10-per-repo-work-plans)._

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

## 🎯 1. Purpose & scope

Each ATRIUM tool already ships (or will ship) a FastAPI service. This strategy wraps every
service in an **Agent Skill**: a `SKILL.md` folder an LLM agent can install and use to drive the
tool. The pattern is **server–client**: the heavy model server keeps running as today's
`service/` FastAPI app, and the skill adds a **zero-dependency client script** that is the only
thing the agent executes. The skill lives on a dedicated **`agent-skill` branch** in each repo —
a flattened, trimmed derivative of the default branch (see [§5](#-5-agent-skill-branch-anatomy-normative)).

**Non-goals:** no breaking changes to existing endpoints or clients; no authentication layer
(services stay CORS-limited, as today); no hosted-deployment work (LINDAT URLs plug in later via
the client's `--base-url`/env override).

## 📐 2. Standards assessment

### 2.1 Agent Skills (the skill wrapper format)

The [Agent Skills open standard](https://agentskills.io) (spec:
[anthropics/skills](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md),
background: [Anthropic engineering post](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills))
is the de-facto cross-vendor format: a skill is a folder with a `SKILL.md` whose YAML
frontmatter carries `name` and `description`, plus optional scripts and reference files.
Adopted since late 2025 by Claude Code, OpenAI Codex/ChatGPT, VS Code Copilot, Google
Antigravity, Gemini CLI, and 30+ other tools — one artifact serves every agent host we care
about. Key properties we rely on:

- **`description` is the routing trigger** — hosts match tasks against it, so it must say both
  *what the tool does* and *when to use it*.
- **Progressive disclosure** — only frontmatter sits in the host's context until the skill
  activates; the body, scripts, and referenced files load on demand. Heavy reference material
  can therefore live in separate files on the branch.
- **Bundled scripts** — the skill may tell the agent to execute a script it ships. Our client
  scripts ([§6](#-6-zero-dependency-client-contract)) are exactly this.

Install targets (already proven by the page-classification example branch): `~/.claude/skills/`
(Claude Code), `~/.codex/skills/` (Codex), and an `AGENTS.md` pointer for Google Antigravity.

### 2.2 OpenAPI (the API contract)

Every ATRIUM service is FastAPI, so a complete OpenAPI 3.1 document already exists **at runtime**
at `/openapi.json` (with Swagger UI at `/docs`). Policy:

- **Do not commit static `openapi.json` snapshots.** They drift the moment `api.py` changes,
  and FastAPI regenerates the spec for free. The SKILL.md instead tells agents: *for full
  request/response schemas, fetch `GET /openapi.json` from the running server.*
- **Drift control moves to tests/CI** ([§12](#-12-maintenance--drift-control)): a contract test
  asserts the endpoint set and required `/info`/`/health` fields against in-process
  `app.openapi()`, and a skill-validation workflow checks that skill docs only reference files
  that exist.
- **Why a hand-written client at all, when agents could read OpenAPI and `curl`?** Determinism
  and economy: the client encodes multipart upload, retries, warmup patience, and exit codes
  once — instead of every agent re-deriving a correct `curl` invocation from a 100 KB spec on
  every call, with token cost and error surface to match.

## 🏗️ 3. The ATRIUM server–client skill pattern

```
 LLM agent (Claude Code / Codex / Antigravity / …)
    │  reads SKILL.md, executes:
    ▼
 scripts/atrium_<verb>.py          ← zero-dependency Python 3 stdlib client
    │  HTTP :8000 (multipart/JSON)
    ▼
 service/  FastAPI app             ← unchanged production service
    │
    ▼
 models / backends (ViT ensembles, LINDAT MT, LayoutLMv3+Qwen, UDPipe/NameTag, LLMs)
```

The `agent-skill` branch is a **flattened, trimmed derivative** of the default branch: source
modules hoisted to the repo root, development-only material removed (tests, lint configs,
supplementary data/analysis), and the skill layer added (`SKILL.md`, `scripts/`, samples).
It is kept current by **merging the default branch forward** after service changes
([§12.2](#122-branch-sync-policy)); skill-only fixes happen directly on the branch.

Precedent: the existing
[`agent-skill` branch of atrium-page-classification](https://github.com/ufal/atrium-page-classification/tree/agent-skill)
established this pattern (SKILL.md + `scripts/atrium_classify.py` + `scripts/server.sh` +
trimmed tree + `small_data_samples/`). It is the exemplar — including four defects catalogued in
[§10.1](#101-atrium-page-classification--exemplar-hardening) that the standard below turns into
explicit rules so they are fixed there and never replicated.

## 📜 4. Standardized service contract (normative)

### 4.1 Meta-endpoints — required in all five services

**`GET /info`** — service identity and capabilities. Required fields:

| Field          | Type      | Content                                                                                                  |
|----------------|-----------|----------------------------------------------------------------------------------------------------------|
| `service`      | str       | canonical tool id = repo name (e.g. `atrium-nlp-enrich`)                                                 |
| `version`      | str       | read from `para_config.txt` `[tool]` (never hard-coded)                                                  |
| `endpoints`    | list[str] | the callable API paths                                                                                   |
| `limits`       | object    | at least `max_upload_mb`; plus service-specific (`max_words`, `max_pdf_pages`, `max_concurrent_jobs`, …) |
| _capabilities_ | any       | service-specific: categories, model versions, supported formats/langs, backends                          |

Reference implementation: `atrium-nlp-enrich/service/api.py` (`info()`; note it already nails
`service` + `limits`). Current drift to harmonize: translator keys the id as `"name"`,
alto-postprocess as `"status"`; neither reports `endpoints` or `limits` today.

**`GET /health`** — liveness/readiness (today only nlp-enrich has it; required everywhere):

- Shallow (`GET /health`): cheap self-check → `{"status": "ok"}` HTTP 200, or
  `{"status": "degraded", "detail": …}` HTTP 503.
- Deep (`GET /health?deep=true`): additionally exercises the backend (model loaded / upstream
  service reachable / API key present) → 200 or 503.

Reference implementation: `atrium-nlp-enrich/service/api.py` (`health()` — dry-run + optional
HEAD checks of the LINDAT UDPipe/NameTag URLs).

### 4.2 Primary endpoints stay domain-specific

| Service             | Primary endpoint(s)                                                                                                                           | Input                            | Output                         |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|--------------------------------|
| page-classification | `POST /predict_image`, `POST /predict_document`                                                                                               | PNG/JPEG · PDF                   | JSON top-N labels (per page)   |
| translator          | `POST /translate`                                                                                                                             | ALTO/metadata XML                | translated XML attachment      |
| alto-postprocess    | `POST /process`                                                                                                                               | ALTO XML · TXT                   | JSON per-line lang/quality     |
| nlp-enrich          | `POST /enrich`, `POST /enrich_text`, `POST /rescale`, jobs API (`POST /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/result`, `DELETE /jobs/{id}`) | lines file / JSON lines / TEITOK | TEITOK XML + keywords envelope |
| llm-enrich (new)    | `POST /extract_keywords`, `POST /extract_keywords_text`                                                                                       | TXT/CSV/TEITOK/ALTO / JSON lines | JSON per-line vocab keywords   |

**No renames.** Uniformity lives in the meta-contract, not the paths. (A rejected alternative —
one `/process` everywhere — would break every existing client and frontend for cosmetic gain.)

### 4.3 Upload conventions

- File uploads: `multipart/form-data`, file field named **`file`**; tuning parameters as form
  fields or query params.
- Size limit enforced server-side against `MAX_UPLOAD_MB` → HTTP 413.
- Where input is line-oriented text, provide a `*_text` sibling endpoint accepting JSON
  (`{"lines": [...]}`) so agents can call without materializing a file (pattern:
  nlp-enrich `/enrich_text`).

### 4.4 Error codes (normative table)

| Code        | Meaning                                              | Client behavior (§6)                  |
|-------------|------------------------------------------------------|---------------------------------------|
| 413         | payload too large (`MAX_UPLOAD_MB`, `max_pdf_pages`) | report limit, suggest split/downscale |
| 415         | unsupported media type                               | report expected types                 |
| 422         | unusable/invalid input (wrong format, bad params)    | report; no retry                      |
| 429         | busy (job/concurrency limit)                         | report; caller may retry later        |
| 500         | processing failure                                   | report server detail; no blind retry  |
| 502/503/504 | not ready / warming up / proxy                       | **retry 3× with backoff**             |

Harmonization: translator currently returns **400** for non-XML uploads
(`atrium-translator/service/api.py`, `/translate` filename check) — becomes **422**. Additive:
correct clients treat any 4xx as a caller error, so nothing breaks.

### 4.5 Environment variables

| Variable          | Scope  | Standard                                                                                                                                                                                                                                |
|-------------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ALLOWED_ORIGINS` | server | CSV of CORS origins, default `*`. alto-postprocess currently defaults to a localhost list (`service/text_api.py`) — align to `*` for parity with siblings.                                                                              |
| `MAX_UPLOAD_MB`   | server | canonical upload limit. translator currently reads `MAX_UPLOAD_BYTES` (default 50 MB) — introduce `MAX_UPLOAD_MB`, keep `MAX_UPLOAD_BYTES` as a deprecated fallback for one release.                                                    |
| service-specific  | server | keep as-is: `MAX_WORDS`, `MAX_CONCURRENT_JOBS`, `API_JOB_TIMEOUT` (nlp-enrich); `TRANSLATION_BACKEND` (translator); `GPT2_MODEL_NAME`, `PERPLEXITY_THRESHOLD_MAX` (alto); `OPENROUTER_API_KEY`, `OLLAMA_HOST`, `HF_TOKEN` (llm-enrich). |
| `ATRIUM_<XX>_URL` | client | per-tool base-URL override, [§6](#-6-zero-dependency-client-contract) / [Appendix E](#appendix-e--naming-tables).                                                                                                                       |

### 4.6 Versioning

`version` is read from `para_config.txt` `[tool]` (the existing convention in all repos),
surfaced through `/info` and the FastAPI `app.version`. SKILL.md and the client never hard-code
a version; agents discover it via `--info`.

### 4.7 Provenance

Server-side paradata logging (`atrium_paradata.py`) is the tools' provenance mechanism, and the
skill pattern deliberately routes agents through the API so runs stay logged. **Rule:** skill
docs may claim paradata provenance **only if the service actually imports and writes it** on
that branch. (Generalized from exemplar defect (b): the page-classification skill branch cites
`atrium_paradata.py`, but the module is neither present nor imported there.)

## 🌿 5. `agent-skill` branch anatomy (normative)

```
SKILL.md                      # the skill contract — frontmatter + required sections (§7)
README.md                     # branch README: what this branch is + install per host (§8)
scripts/
  atrium_<verb>.py            # zero-dependency client (§6, Appendix B)
  server.sh                   # idempotent server launcher (Appendix C) — named server.sh
service/                      # the FastAPI app, unchanged from default branch
  api.py · requirements.txt · README.md · frontend*/
<source modules hoisted to repo root>   # only what service/ imports at runtime
small_data_samples/           # tiny licensed inputs for smoke tests (+ LICENSE)
setup/para_config.txt         # version source (§4.6) + setup scripts the launcher needs
Dockerfile · docker-compose*.yml        # compose `api` profile, port 8000
CITATION.cff · LICENSE · .gitignore · .dockerignore
```

Removed relative to the default branch: `tests/`, lint/CI configs (`ruff.toml`, `pytest.ini`,
`.pre-commit-config.yaml`, coverage), `supplementary/`/analysis material, dev-only frontends —
anything a *running* skill doesn't need.

**Rule (CI-checked, [§12.3](#123-skill-validation-ci-future-reusable-workflow)): every file path
referenced by `SKILL.md`, `README.md`, or `service/README.md` must exist on the branch.**
(Generalized from exemplar defects (a) `serve.sh` vs committed `server.sh`, and (c)
`frontend-lindat/` documented but absent.)

## 🔌 6. Zero-dependency client contract

The client is the only thing the agent executes. Normative spec (reference implementation:
`scripts/atrium_classify.py` on the page-classification `agent-skill` branch):

- **Python 3 stdlib only** — `argparse`, `urllib.request`, `mimetypes`, `json`, `uuid`,
  `pathlib`. No `requests`, no pip installs. Multipart bodies are hand-rolled with a
  `uuid4().hex` boundary.
- **CLI shape:** positional input file(s) · `--base-url` (default `http://localhost:8000`,
  overridable via `ATRIUM_<XX>_URL` env) · `--info` (print `GET /info` and exit) ·
  `--format table|csv|json` (default `table`) · service-specific flags (Appendix E).
- **Retries:** 3 attempts with backoff on HTTP 502/503/504 only (model warmup); no retry on
  other codes.
- **Timeouts:** short connect, long read (≥300 s) — model inference and first-call warmup are
  slow by design; a slow first call is not a failure.
- **Exit codes:** `0` success · `1` usage/input error · `2` server unreachable ·
  `3` server-side error (4xx/5xx after retries). SKILL.md's agent guidelines key off these.
- **One client per repo**, fronting all of its endpoints (precedent: `atrium_classify.py`
  routes by file suffix to `/predict_image` vs `/predict_document`; the nlp-enrich client adds
  a `--jobs` async mode over the jobs API).
- Client-side guards mirror server limits (size pre-check before upload) so agents get fast,
  actionable errors.

Skeleton in [Appendix B](#appendix-b--client-script-skeleton-spec).

## ✍️ 7. SKILL.md authoring template

Frontmatter:

- `name:` — the repo name (`atrium-<tool>`); lowercase, hyphens, ≤64 chars per spec.
- `description:` — one dense sentence covering **what it does + when to use it** (this is the
  routing trigger hosts match on). Mention input types, output, and the routing purpose.

Required body sections, in order:

1. **Operational Requirements** — server URL + `ATRIUM_<XX>_URL`; client deps = none; server
   deps (Docker or venv + `service/requirements.txt`); first-launch warmup expectations
   (model downloads, minutes not seconds — *do not treat slow first start as failure*); upload
   limits.
2. **Domain reference** — the tool's vocabulary: categories table (page-classification,
   alto-postprocess), language/format matrix (translator), stage plan + keyword methods
   (nlp-enrich), vocabularies + backends (llm-enrich).
3. **Workflows** — numbered: ① ensure server (`bash scripts/server.sh`, idempotent) ② call the
   client (copy-paste command examples covering the main variants) ③ interpret output (row
   format, when to use which `--format`).
4. **Agent Guidelines** — numbered operational rules: warmup patience; prefer `--format json`
   for downstream parsing; fetch `/openapi.json` from the live server for full schemas; exit
   code 2 → start server and retry once, exit code 3 → check server logs, don't loop;
   uncertainty discipline (surface top-N scores, don't over-assert); size-limit handling; do
   not bypass the API by importing model code directly (provenance, §4.7 permitting).
5. **Acknowledgements & Citations** — ATRIUM project, ÚFAL, LINDAT; `CITATION.cff` + dataset
   handles.

**Anti-pattern checklist** (review gate; the four exemplar defects):
- [ ] no doc references a script name that differs from the committed file (a);
- [ ] no provenance/paradata claim unless the service imports it on this branch (b);
- [ ] no reference to directories/files absent from the branch (c);
- [ ] documented response fields match what `api.py` actually returns (d).

Full skeleton in [Appendix A](#appendix-a--skillmd-skeleton).

## 📦 8. Branch README & skill installation

The branch `README.md` (distinct from the default branch's) contains: what this branch is (the
skill packaging of the tool, pointer to the default branch for development); install per host —

```bash
# Claude Code
git clone -b agent-skill https://github.com/ufal/<repo>.git ~/.claude/skills/<skill-name>
# OpenAI Codex
git clone -b agent-skill https://github.com/ufal/<repo>.git ~/.codex/skills/<skill-name>
# Google Antigravity: clone anywhere, reference SKILL.md from AGENTS.md
```

— update = `git pull` in the installed clone; and the server quick-start (`bash
scripts/server.sh`, Docker vs `--local`).

## 🖥️ 9. Frontend & documentation requirements

Concrete reading of the issue's "Frontend UI should include documentation of API usage as well
as `README.md` in the `service` directories":

- **Every `service/frontend*/index.html` gets an API section/footer** with: ① a copy-paste
  `curl` example of the primary endpoint, ② links to the running server's `/docs` (Swagger UI)
  and `/openapi.json`, ③ a link to `service/README.md` on GitHub.
- **`service/README.md` is required in every repo** (today missing only in translator),
  following the alto-postprocess/nlp-enrich standard: endpoint table · curl examples · response
  schema with field descriptions · env-var table · run instructions (uvicorn +
  `docker compose --profile api up`). Outline in [Appendix D](#appendix-d--servicereadmemd-outline).
- Both artifacts must match `api.py` reality (defect (d) rule) — checked by the contract test
  ([§12.1](#121-per-repo-contract-test)).

## 🗂️ 10. Per-repo work plans

Each subsection is self-contained and liftable verbatim into a sub-issue ([§13](#-13-sub-issue-creation--tracking)).

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
      _(Shipped synchronous with a strict concurrency guard + `504` timeout; async jobs deferred to
      the W5 fast-follow.)_
- [x] Then: `agent-skill` branch per §5; `SKILL.md` per §7; `scripts/atrium_keywords.py` per §6
      (`--backend`, `--vocab`, `--top-k`); `scripts/server.sh`; text samples; branch README.

**Acceptance:** as 10.2, with an `/extract_keywords_text` round-trip on sample lines against at
least one backend (Ollama or OpenRouter with a test key).

## 🚦 11. Rollout order

1. **This doc** merged into atrium-project; sub-issues created from §10 (per §13).
2. **page-classification hardening** (10.1) — small; makes the exemplar trustworthy.
3. **nlp-enrich** (10.2) — validates the templates → **promote Appendices A–D to
   `docs/templates/skill/`** in the hub repo.
4. **alto-postprocess** (10.3) and **translator pre-work** (10.4 first block) — parallelizable.
5. **translator skill branch** (10.4 rest); **llm-enrich** (10.5 — service first, skill after).
6. **`skill-validate.yml`** reusable workflow in the hub (§12.3) once ≥2 skill branches exist;
   callers wired into each repo's `agent-skill` branch.

## 🔄 12. Maintenance & drift control

### 12.1 Per-repo contract test

On each default branch, a test asserts against in-process `app.openapi()` (no server needed):
the endpoint set matches the documented list; `/info` returns the §4.1 required fields;
`/health` exists and returns the §4.1 shape. This guards the meta-contract without committed
spec files. (Pattern: extend the existing `tests/test_api*.py` / `tests/test_service_api.py`.)

### 12.2 Branch sync policy — **manual (interim)**

The `agent-skill` branches were hand-built as flattened/trimmed derivatives, so they do **not**
share history cleanly with their default branches. Until the skills stabilise, syncing is
**manual** (no automated forward-merge or regenerate-from-default). After any `service/` change
or release tag on the default branch, run this checklist by hand:

1. **Port the `service/` change** onto the `agent-skill` branch (cherry-pick or copy the changed
   `service/*.py` + any newly-required runtime module — remember the branch is trimmed, so a new
   import must be carried over too).
2. **Re-run the anti-pattern checklist** (§7 / each branch README "Maintenance notes"): no doc
   cites a script name that differs from the committed file; no provenance claim unless the
   service writes paradata on this branch; no reference to absent files; documented response
   fields match `api.py`.
3. **Re-run the client smoke test** on `small_data_samples/` against a locally started server
   (`bash scripts/server.sh`), and re-check `/info`+`/health` against §4.1.
4. **Let CI confirm**: the `skill-validate.yml` caller (§12.3) runs on the push and guards
   frontmatter, referenced paths, and the zero-dependency client claim.
5. **Bump the skill tag** (`skill-v<para_config version>`) so agents can pin the synced state.

Automating this (a scripted `skill-ify` transform, or an auto forward-merge action) is deferred
until the branches stop churning.

### 12.3 Skill-validation CI (reusable workflow — authored)

`skill-validate.reusable.yml` lives in atrium-project `.github/workflows/` (authored; publish to
`test`), called by a `.github/workflows/skill-validate.yml` on each repo's `agent-skill` branch
(caller template: `docs/templates/workflows/skill-validate.caller.example.yml`):

1. SKILL.md frontmatter parses; `name`/`description` constraints hold.
2. **Every file path referenced in SKILL.md / README.md / service/README.md exists on the
   branch** — would have caught exemplar defects (a) and (c).
3. The client script compiles (`python -m py_compile`) and runs `--help` in a bare
   `python:3.11-slim` container — proves the zero-dependency claim.
4. Optional: boot the app in-process, diff the documented endpoint list against
   `app.openapi()` — catches the defect (d) class.

Caller example lands in `docs/templates/workflows/skill-validate.caller.example.yml` when the
workflow does (rollout step 6).

## 🪃 13. Sub-issue creation & tracking

- One GitHub sub-issue per repo under #31, titled **`agent-skill: <repo-name>`**, body = the
  repo's §10 subsection + a pinned-commit link to this doc. Labels/milestone per project
  convention (`enhancement`, `development` · Q3 milestone).
- Implementation happens on each repo's **`agent-skill`** branch: page-classification updates
  the existing one; the others create it **from the default branch head** (translator: `master`;
  alto-postprocess: `master`; nlp-enrich: `master`; llm-enrich: `main`).
- Each implementation session logs per convention in that repo's `agent_dev_logs/`
  (`plans/`, `digests/`, DEVLOG).

---

## Appendix A — SKILL.md skeleton

```markdown
---
name: atrium-<tool>
description: <What it does — inputs, outputs, models> Use this skill to <when/why an agent
  should pick it — the routing purpose in the ATRIUM pipeline>.
---

# ATRIUM <Tool Name> Skill

This skill provides agent access to the **ATRIUM <Tool>** service — <one-line what/how>.
It follows a **server–client** design: a FastAPI server (in `service/`) performs the heavy
work, and a zero-dependency client script (`scripts/atrium_<verb>.py`) is the only thing the
agent calls directly.

## Operational Requirements

- **Server**: a running instance is required. Default `http://localhost:8000`; override with
  `--base-url` or the `ATRIUM_<XX>_URL` environment variable.
- **Client dependencies**: none — Python 3 standard library only.
- **Server dependencies**: Docker (recommended) or a Python venv with
  `service/requirements.txt`.
- **First launch**: <model download sizes / warmup time>. Do **not** treat a slow first start
  as failure.
- **Limits**: <MAX_UPLOAD_MB> MB per file<, service-specific limits>.

## <Domain reference: categories / languages / stages / vocabularies>

<table>

## Workflows

### 1. Ensure the server is running

    bash scripts/server.sh          # Docker CPU (or local uvicorn fallback)
    bash scripts/server.sh --gpu    # Docker with GPU
    bash scripts/server.sh --local  # force local uvicorn (no Docker)

Idempotent: exits immediately if `GET /info` already answers; waits for first-run warmup.

### 2. <Primary action>

    python3 scripts/atrium_<verb>.py <input> [flags]        # main variant
    python3 scripts/atrium_<verb>.py --info                 # discover capabilities
    python3 scripts/atrium_<verb>.py <input> --format json  # machine-readable

### 3. Interpret output

<row format; which --format for which purpose>

## Agent Guidelines

1. <model/param selection discipline>
2. Prefer `--format json` when the result feeds further processing.
3. For full request/response schemas, fetch `GET /openapi.json` from the running server.
4. Exit code `2` (unreachable): start the server (`bash scripts/server.sh`) and retry once.
   Exit code `3` (server error): the client already retried 502/503/504 3×; inspect server
   logs, do not loop.
5. <size-limit handling>
6. Do not bypass the API by importing the model code directly<; server-side runs are
   paradata-logged — only if true on this branch (§4.7)>.

## Acknowledgements & Citations

Developed within the [ATRIUM](https://atrium-research.eu/) project at ÚFAL, Charles
University; data on [LINDAT/CLARIAH-CZ](https://lindat.cz). Cite `CITATION.cff`<+ dataset
handle>.
```

## Appendix B — client script skeleton (spec)

```
atrium_<verb>.py
  ├─ build_multipart(fields, file_field, path) -> (bytes, content_type)   # uuid4 boundary
  ├─ http_json(url, data=None, content_type=None, timeout=300) -> dict
  │     GET when data is None, else POST; 3× retry on 502/503/504 (10 s backoff);
  │     URLError/Timeout -> exit 2; HTTPError after retries -> exit 3
  ├─ <verb>_file(base_url, path, **params)      # route by suffix if multi-endpoint;
  │                                             # client-side size pre-check (413 mirror)
  ├─ result_rows(path, response) -> [(file, …, rank, label/score, …)]     # flatten
  ├─ print_table(rows, as_csv)                  # aligned table / csv
  └─ main()                                     # argparse per §6; --info; --format;
                                                # base URL: --base-url > ATRIUM_<XX>_URL > localhost:8000
```

Argparse surface (all clients): positional `files…` · `--base-url` · `--info` ·
`--format {table,csv,json}` · service flags per Appendix E. Exit codes: 0/1/2/3 per §6.

## Appendix C — server.sh behavioral spec

Named **`server.sh`** (everywhere, including every doc that mentions it — defect (a) rule).

1. Probe `GET <base-url>/info`; if it answers → exit 0 (idempotent).
2. Else: `docker compose --profile api up -d` (default CPU; `--gpu` adds the GPU overlay
   compose file; `--local` skips Docker → run `setup/setup_api_service.sh` if present, then
   `nohup uvicorn service.<module>:app --host 0.0.0.0 --port 8000`).
3. Poll `/info` until ready; wait up to 15 min (first-run model downloads); on timeout, print
   the tail of the server log / `docker compose logs` and exit non-zero.

## Appendix D — service/README.md outline

1. Title + one-line purpose; version source (`para_config.txt`).
2. Endpoint table: method · path · purpose · params.
3. Curl examples (primary endpoint(s) + `/info`).
4. Response schema: JSON example + field-description table (must match `api.py` — defect (d)
   rule).
5. Errors: the §4.4 table with service-specific notes.
6. Configuration: env-var table (§4.5 subset).
7. Run: venv/uvicorn + `docker compose --profile api up` (+ GPU variant).
8. Frontend(s): where mounted, what they demonstrate.
9. Tests: how to run the API tests (default branch only).

## Appendix E — naming tables

Branch: **`agent-skill`** in all five repos. Skill `name:` = repo name.
Client = `atrium_<domain-verb>.py` (domain verb, not necessarily the endpoint path).
Env var = `ATRIUM_<code>_URL`.

| Repo                       | skill `name:`                | client script                   | env var         | service-specific client flags                              |
|----------------------------|------------------------------|---------------------------------|-----------------|------------------------------------------------------------|
| atrium-page-classification | `atrium-page-classification` | `scripts/atrium_classify.py`    | `ATRIUM_PC_URL` | `--version`, `--topn`                                      |
| atrium-translator          | `atrium-translator`          | `scripts/atrium_translate.py`   | `ATRIUM_TR_URL` | `--source-lang`, `--target-lang`, `--alto/--no-alto`, `-o` |
| atrium-alto-postprocess    | `atrium-alto-postprocess`    | `scripts/atrium_postprocess.py` | `ATRIUM_AP_URL` | `--task-type`                                              |
| atrium-nlp-enrich          | `atrium-nlp-enrich`          | `scripts/atrium_enrich.py`      | `ATRIUM_NE_URL` | `--kw-method`, `--num-keywords`, `--jobs`, `--zip`         |
| atrium-llm-enrich          | `atrium-llm-enrich`          | `scripts/atrium_keywords.py`    | `ATRIUM_LE_URL` | `--backend`, `--vocab`, `--top-k`                          |

Considered and rejected: `atrium_process.py` for alto-postprocess (too generic as a skill-level
verb); `atrium_llm_enrich.py` for llm-enrich (confusable with nlp-enrich's `atrium_enrich.py`);
a uniform `/process` primary endpoint everywhere (breaks existing clients for cosmetic gain);
committed `openapi.json` snapshots (drift; §2.2).

---
_Maintained in `atrium-project` next to the ecosystem record
([`plan_repo_review.md`](plan_repo_review.md)). Templates graduate to `docs/templates/skill/`
after validation (rollout step 3). Session log: `agent_dev_logs/plans/31.plan.md` ·
`agent_dev_logs/digests/31.digest.md`._
