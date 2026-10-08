# 🧩 ATRIUM Agent-Skill Strategy — API services as LLM Agent Skills

> **Repository names (2026-10-01).** This document predates the repository moves of atrium-project#72 and
> uses the names of its time: `alto-postprocess` is now `ocr-postprocess`; `llm-enrich` split into
> `keyword-extract` (its keyword stage, with the keyword extraction of `nlp-enrich`) and `digital-convert`
> (the born-digital converter). The old repositories are superseded and kept as history. Read the names below through that map;
> the current ones are in [`docs_site/ecosystem/repository-map.md`](../docs_site/ecosystem/repository-map.md).

_Issue: [ufal/atrium-project#31](https://github.com/ufal/atrium-project/issues/31) · Status: **implemented on all five `agent-skill` branches** (2026-07-18) → refinement stage (validation CI · acceptance · consistency · release); Appendices A–D promoted to [`templates/skill/`](templates/skill/) · Date: 2026-07-17_
_Scope: normative for the `agent-skill` branches of the five service repos
(atrium-page-classification · atrium-translator · atrium-alto-postprocess ·
atrium-nlp-enrich · atrium-llm-enrich). Per-repo implementation is tracked in
sub-issues lifted from [§10](#-10-per-repo-work-plans)._
_Round 2 of [#32](https://github.com/ufal/atrium-project/issues/32) (2026-09-28): the typed
contract and the spec as a release artefact — §2.2 reversed, §4.1 `openapi_sha256`, §4.4 reason
registry, new [§4.8](#48-typed-contract-and-the-spec-as-a-release-artefact-normative), §12.1._

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

- **The spec is committed and released** (atrium-project#32 round 2, 2026-09-28; this
  reverses the 07-23 rule "do not commit static `openapi.json` snapshots"). Each service commits
  `service/openapi.json`, generated from the app; `tests/test_openapi_contract.py` fails while it
  is stale, and every release attaches it as `openapi.json` with `openapi.json.sha256` and
  compares it with the previous release's
  ([§4.8](#48-typed-contract-and-the-spec-as-a-release-artefact-normative)). The AMČR pipeline
  generates its Temporal activities' clients from the spec attached to the release it trusts,
  and reads the live `/openapi.json` only to check that a deployed image matches that release.
  The 07-23 objection — the snapshot drifts the moment `api.py` changes — is answered by the
  freshness test: drift is a red build, not a stale file.
- The SKILL.md still tells agents: *for full request/response schemas, fetch
  `GET /openapi.json` from the running server* — which is now the same document as the release's.
- **Drift control lives in tests/CI** ([§12](#-12-maintenance--drift-control)): the contract
  tests assert the endpoint set, the required `/info`/`/health` fields and the committed spec
  against in-process `app.openapi()`, and a skill-validation workflow checks that skill docs only
  reference files that exist.
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
It is kept current by **porting default-branch `service/` changes forward by hand** — for three
of the five repos the branches share no history, so there is nothing to merge
([§12.2](#122-branch-sync-policy--manual-landing-scripted-diagnosis)); skill-only fixes happen
directly on the branch.

Precedent: the existing
[`agent-skill` branch of atrium-page-classification](https://github.com/ufal/atrium-page-classification/tree/agent-skill)
established this pattern (SKILL.md + `scripts/atrium_classify.py` + `scripts/server.sh` +
trimmed tree + `small_data_samples/`). It is the exemplar — including four defects catalogued in
[§10.1](#101-atrium-page-classification--exemplar-hardening) that the standard below turns into
explicit rules so they are fixed there and never replicated.

## 📜 4. Standardized service contract (normative)

### 4.1 Meta-endpoints — required in all five services

**`GET /info`** — service identity and capabilities. Required fields:

| Field            | Type      | Content                                                                                                                  |
|------------------|-----------|--------------------------------------------------------------------------------------------------------------------------|
| `service`        | str       | canonical tool id = repo name (e.g. `atrium-nlp-enrich`)                                                                 |
| `version`        | str       | read from `para_config.txt` `[tool]` (never hard-coded)                                                                  |
| `endpoints`      | list[str] | the callable API paths                                                                                                   |
| `limits`         | object    | **every** limit of the service (§4.5), `{key: effective value}`; at least `max_upload_mb`                                |
| `limits_meta`    | object    | per limit: the environment variable `env` that sets it, `unit`, `default`, `source` (`env`/`config`/`default`/`derived`) |
| `openapi_sha256` | str       | sha256 of the process's OpenAPI document in canonical form — the release's `openapi.json.sha256` for its image (§4.8)    |
| _capabilities_   | any       | service-specific: categories, model versions, supported formats/langs, backends                                          |

`limits` keys are the environment variable in lower case (`MAX_PDF_PAGES` → `max_pdf_pages`),
except where an older key is kept stable; `limits_meta` is the authority for which variable
sets which key. A **derived** limit (computed from settings or from the model, e.g. a token
window) is reported with `env: null` and `derived_from`. Both maps come from the repo's
`tool_limits.py` `LimitSet` (`atrium_limits.py`, atrium-project#53), so what `/info` reports is
what the code enforces.

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

| Service             | Primary endpoint(s)                                                                                                                           | Input                                                                                                  | Output                         |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------|
| page-classification | `POST /predict_image`, `POST /predict_document`                                                                                               | PNG/JPEG · PDF                                                                                         | JSON top-N labels (per page)   |
| translator          | `POST /translate`                                                                                                                             | ALTO/metadata XML                                                                                      | translated XML attachment      |
| alto-postprocess    | `POST /process`                                                                                                                               | ALTO XML · TXT · JSON · any text-bearing document (`task_type=document`: PDF, DOCX, PAGE XML, hOCR, …) | JSON per-line lang/quality     |
| nlp-enrich          | `POST /enrich`, `POST /enrich_text`, `POST /rescale`, jobs API (`POST /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/result`, `DELETE /jobs/{id}`) | lines file (+ ALTO) / JSON lines / converted TEITOK                                                    | TEITOK XML + keywords envelope |
| llm-enrich (new)    | `POST /extract_keywords`, `POST /extract_keywords_text`                                                                                       | TXT/MD/CSV/TEITOK / JSON lines                                                                         | JSON per-line vocab keywords   |

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

| Code        | Meaning                                                                                                                                                                                                                                                                                                                                                                      | Client behavior (§6)                                   |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| 413         | the request content is over a limit (`reason: limit_exceeded`: upload, pages, words, tokens, pixels)                                                                                                                                                                                                                                                                         | report the limit; split the input or raise the setting |
| 415         | unsupported media type (`reason: unsupported_media_type`, with `accepted`)                                                                                                                                                                                                                                                                                                   | report expected types                                  |
| 422         | unusable/invalid input (wrong format, bad params); `reason: invalid_record` for a record that cannot be opened, `ocr_text_layer` for a PDF whose text layer is an earlier OCR run's, `source_digest_mismatch` for a seed whose `source.sha512` is not the uploaded file's; also `reason: limit_exceeded` when a parameter or a per-input processing budget is over its limit | report; no retry                                       |
| 429         | busy (`reason: busy`: every slot or queue place is taken), with `Retry-After`                                                                                                                                                                                                                                                                                                | retry after `Retry-After` seconds                      |
| 500         | processing failure                                                                                                                                                                                                                                                                                                                                                           | report server detail; no blind retry                   |
| 501         | this deployment cannot read the input: a reader's optional dependency is not installed (alto-postprocess `dependency_missing`)                                                                                                                                                                                                                                               | report; the operator installs it                       |
| 502/503/504 | not ready / warming up / proxy; 504 with `reason: limit_exceeded` is a time limit that depends on an upstream service                                                                                                                                                                                                                                                        | **retry 3× with backoff**                              |

**Error body (atrium-project#32 item 2, landed with #53).** Every error a service returns —
`HTTPException`, the router's 404/405, request validation, an uncaught failure — has one
JSON shape, installed by `atrium_service.attach_error_handlers(app)`:

```json
{"status": 413, "reason": "limit_exceeded", "detail": "The PDF has 73 pages; the limit is 50 (MAX_PDF_PAGES).",
 "limit": {"key": "max_pdf_pages", "env": "MAX_PDF_PAGES", "value": 50, "observed": 73, "unit": "pages"}}
```

- `status` is the HTTP status as an integer. It exists only on error bodies; the string
  `status` of `/health`, `/ready`, a job resource or alto-postprocess's `/info` is another field.
- `reason` is a **registered** code (`atrium_service.REASON_CODES`) or `null` when no code is
  registered for the cause yet. A published code is never renamed or removed; a new cause gets a
  new code. Each code may be sent only with its statuses (`REASON_STATUSES`, enforced by
  `error_body()` and `AtriumHTTPError`), and the registry is published in every spec as
  `x-atrium-reason-codes` (§4.8), where `atrium_openapi.py compare` fails a release that drops
  one:

  | `reason`                 | Statuses      | Since     | Sent for                                                                                                                                                                                                               |
  |--------------------------|---------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
  | `limit_exceeded`         | 413, 422, 504 | #53       | an input over a limit; the body's `limit` names it                                                                                                                                                                     |
  | `busy`                   | 429           | #53       | every slot or queue place taken; `Retry-After`                                                                                                                                                                         |
  | `unsupported_media_type` | 415           | #32 rnd 2 | a type the endpoint does not read; the body's `accepted` lists what it reads                                                                                                                                           |
  | `invalid_record`         | 422           | #32 rnd 2 | the record sent with the request cannot be opened (not UTF-8 JSON, not an object, a newer `schema_version` major) — a record that opens but does not validate is accepted and reported in `document_json_schema_error` |
  | `ocr_text_layer`         | 422           | #32 rnd 2 | a PDF whose text layer is an earlier OCR run's (llm-enrich#10 W6; raised by `api-digital`)                                                                                                                             |
  | `source_digest_mismatch` | 422           | dc#2      | the seed's `source.sha512` is not the uploaded file's digest, checked before anything is read (atrium-digital-convert#2; raised by `api-digital`)                                                                      |

- `detail` is always a human-readable string — the same text as before the envelope existed, so
  a client reading `detail` needs no change. Structured data goes into extra members: `limit`
  (for `limit_exceeded`), `errors` (the validation problems, or a non-string `HTTPException`
  detail), `accepted` (for `unsupported_media_type`) and `cause` — a finer, **unregistered**
  cause such as alto-postprocess's reader codes (`image_needs_ocr`, `corrupt`, …), informational
  and free to change; a client branches on `reason`, never on `cause`.
- The status of a `limit_exceeded` refusal follows its cause: **413** request content too large,
  **422** a parameter or a per-input processing budget, **504** a time limit that depends on an
  upstream service. `busy` is always **429**; a draining replica's 503 keeps `reason: null`.

Harmonization (atrium-project#32 round 2, before the first release that attaches a spec): every
media-type refusal is **415** `unsupported_media_type` — it was 400 in alto-postprocess and
page-classification and 422 in llm-enrich, nlp-enrich and the translator. alto-postprocess's
`dependency_missing` moves from 400 to **501**. Caller errors that ended in the blanket 500 are
422 now: a record that cannot be opened (`invalid_record`, in all five), a malformed CSV/TEITOK
(llm-enrich) or JSON upload (alto-postprocess), an unreadable image or PDF and an unknown model
`version` (page-classification), an unknown `task_type` (alto-postprocess, which read it as
`text`). A client that treats any 4xx as a caller error is unaffected.

### 4.5 Environment variables

The normative artifacts are `docs/templates/env.example.template` (the layout every repo's
`.env.example` follows) and each repo's own `.env.example` (the complete ledger — every
variable the api image reads, at its code default). This section states the *rules* those
artifacts implement; it does not enumerate variables, and a variable named here and absent
there is a bug in this section. atrium-project#60's CI guard (`tests/test_env_contract.py`,
hub-local and vendored into all five tool repos) is what keeps that true.

| Variable          | Scope  | Standard                                                                                                                                                                                                                                                                                                                          |
|-------------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ALLOWED_ORIGINS` | server | CSV of CORS origins, code default `*`. Compose files may supply a narrower default of their own for local development; Kubernetes never reads one, so the k8s-facing reference (`docs/k8s_deployment.md`) always states the code default.                                                                                         |
| `MAX_UPLOAD_MB`   | server | canonical upload limit, resolved by `atrium_service.resolve_max_upload_mb`. **The number is per-service, not shared** — alto-postprocess 25, llm-enrich 10, nlp-enrich 5, page-classification 10, translator 50 (see `docs/k8s_deployment.md`). `MAX_UPLOAD_BYTES` remains a deprecated fallback and loses whenever both are set. |
| service-specific  | server | keep as-is; enumerated per repo in that repo's `.env.example` §5 ("Service knobs — operator") and in `docs/k8s_deployment.md`'s Table B.                                                                                                                                                                                          |
| **limits**        | server | **every limit is a setting** (atrium-project#53, below): declared once in the repo's `tool_limits.py`, tagged `[limit]` in `.env.example`, listed in the service README's `## Limits` table and in `docs/k8s_deployment.md`'s Table B, and reported in `/info` (§4.1).                                                            |
| `ATRIUM_<XX>_URL` | client | per-tool base-URL override, [§6](#-6-zero-dependency-client-contract) / [Appendix E](#appendix-e--naming-tables).                                                                                                                                                                                                                 |

**What counts as a limit (atrium-project#53, factor III).** A *limit* is a value that
(a) refuses an input; (b) cuts, samples or splits an input or a prompt; (c) caps an output; or
(d) bounds the time or the retries of one request. AMČR's pipeline splits large documents
itself and calls the services from its own workers, so each one must be a setting it can read
(`/info`) and change (the environment):

- **Declared with `atrium_limits.py`** (canonical, standard library only, at the repo root so
  the CLIs use the same declaration): `limit("NAME", default, unit=…)` in the repo's
  `tool_limits.py`. A malformed value fails at startup, naming the variable. Library code and
  CLIs import `atrium_limits`, never the FastAPI-bound `service/atrium_service.py`.
- **Over a limit, the service refuses** with `reason: limit_exceeded` (§4.4), **or processes the
  input in full.** It never cuts an input quietly.
- **Where a limit shapes a result without refusing it**, the run records a note in
  `limits_applied` — `{limit, value, effect, count, detail}`, `effect` ∈ `sampled`, `split`,
  `trimmed`, `skipped`, `stopped` (published; never renamed) — in its paradata
  (`docs/paradata_schema.md`) and in the response (a top-level `limits_applied` list in a JSON
  response; the `X-Atrium-Limits-Applied` header where the response is not JSON).
- **Not limits**, and so not in `/info` `limits`: algorithmic thresholds (alto-postprocess's
  `ATRIUM_TEXT_UTILS_*`, the translator's `LANG_ID_MIN_CONFIDENCE`); batch sizes that do not
  change the result; bounds on a request parameter (those belong in the OpenAPI schema, #32);
  lifecycle settings (`GRACEFUL_SHUTDOWN_S`, the drain wait, the health-probe timeout).
- **Platform limits** — libxml2 without `huge_tree`, Starlette's multipart defaults, the csv
  field size — are listed in the README's `## Limits` table but are not settings.

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

### 4.8 Typed contract and the spec as a release artefact (normative)

atrium-project#32 round 2 (2026-09-28), K4TEL's three additions to David Motyčka's 09-26 request,
accepted 09-27. Implemented in `docs/templates/shared/atrium_service.py` (gen 3),
`atrium_openapi.py` and `test_openapi_contract.py`, vendored into all five repos.

**Typed responses.** Every primary endpoint's JSON 200 is a named model (`$ref`), and so is
`/info` (an `InfoBase` subclass). Routes **document** their responses —
`response_model=None, responses={200: {"model": X}, **error_responses(…)}` — so the bytes sent
are what the handler builds; each repo's `tests/test_api_contract.py` validates real responses
against the **published** schema (`atrium_openapi.validate_response`). page-classification's
`/predict_image`, which already filtered through `response_model`, keeps it. Rules:

- a field the handler always sends has no default (required, nullable where it can be null);
  one it sends only sometimes defaults to `None` — oasdiff rates removing a required response
  property as breaking, and `compare` raises the optional case to the same level;
- **no enums in responses**: a value is an open string whose known values are in its
  description, so a new value never breaks a client generated from an older spec. Request
  parameters use enums only where the handler already refuses unknown values (alto's
  `task_type`, nlp's `kw_method`/`lang`/`format`, the translator's `response_format`) — the
  translator's `output_mode` stays a string, since the handler accepts any case and falls back;
- every model allows extra members, so an additive field is not breaking;
- a returned record is typed **by reference**: the `AtriumDocument` component is the vendored
  `atrium_document.schema.json` (its `$defs` hoisted as `AtriumDocument_<name>`), recorded as
  `x-atrium-record-schema` (`schema_version`, `sha256`). A record in a **request** stays untyped
  (a binary part with `contentMediaType: application/json`, or a free-form object), because a
  #67 R1 seed (`doc_id`, `source`) fails the full schema and must stay valid input. Every tool
  opens a sent record through `parse_record_part()` (§4.4 `invalid_record`) and names it
  `document_json`, in and out (alto-postprocess keeps `document_record` / `document_json_out`
  as deprecated aliases);
- every primary response declares an optional `paradata: CreateAction` (#67 §E), and since
  atrium-project#71 every successful response fills it: the call's Process Run Crate
  `CreateAction`, from `atrium_rocrate.create_action()`, whose `@id` is the `run_uuid` the call
  stamped into the record it returned (`docs/rocrate_export.md` §5). An error body carries none.

**Declared errors.** `FastAPI(responses=error_responses(422, 500), generate_unique_id_function=
operation_id, root_path_in_servers=False)` and `attach_openapi_contract(app, SERVICE)` in every
service: each error status is `ErrorBody` (FastAPI's `HTTPValidationError`, which is not what is
sent, is gone), each route adds the statuses it can refuse with (a 429 documents `Retry-After`),
and `/health`/`/ready` keep their own 503 bodies.

**A stable spec.** operationIds are the handler names (a renamed handler is a renamed client
method, and `compare` fails it); no component is split into `-Input`/`-Output`; nothing read
from the environment reaches the spec (the test perturbs every `[limit]` variable and each
repo's `ENV_PERTURB`); `fastapi==0.141.1` and `pydantic==2.13.5` are pinned **exactly** in every
file a lane or an image installs them from, dependabot ignores both, and a bump regenerates the
spec in the same commit.

**Files per repo.** `service/openapi.json` (committed, generated:
`python atrium_openapi.py export --app <mod>:app`); `atrium_openapi.py` at the root — also a
**runtime companion** of `service/atrium_service.py`, which imports it lazily to finish and
digest the spec, so it ships in every image and release bundle, like `atrium_document.py`;
`tests/test_openapi_contract.py` (vendored) and `tests/openapi_contract_data.py` (per repo:
`SERVICES`, `ENV_PERTURB`, `PIN_FILES`, `PREPARE` — page-classification's stubs the torch-bound
model manager). A repo with two HTTP services lists both (none has two today: digital-convert's
planned `api-digital` became its one service, with one `service/openapi.json`).

**Release.** `release.yml` (all five): `atrium_openapi.py check` (the committed spec is what the
tag's code generates) → `stamp` (`info.version` = the release version; `openapi.json` +
`openapi.json.sha256`) → `baseline` (the highest release below the tag that carries the asset;
none is the bootstrap, which passes; an API error fails) → `compare --require-oasdiff`
(oasdiff `v1.32.1`). **A breaking change fails unless the major version went up** — 0.x
included, so a 0.x tool needs 1.0 — and **a removed reason code, a changed
`x-atrium-service` or a record schema change without a `schema_version` major always fail**.
The one exception is a declared rename (#72): a changed `x-atrium-service` passes when the new
spec's `info.x-atrium-service-previous` equals the baseline's id, which
`attach_openapi_contract(app, SERVICE, previous="<old id>")` writes and the repo's
`tests/openapi_contract_data.py` entry names as `service_previous`.
The assets are attached in the step that creates the release (an immutable release refuses
later uploads, #40), and `workflow_dispatch` is the dry run that proves the gate before a tag is
spent. The gate runs the vendored script, not a cross-repo `uses:` (docker_gha_roadmap §3.3).

**CI.** `api-contract.reusable.yml` runs the canonical test too (and no longer reads pytest's
exit 5 as a failure, 07-23 defect 4), and its `openapi-compat` job compares the committed spec
with the latest release's on every push, so a breaking change shows on the PR that makes it.
`docker-tool.reusable.yml`'s container smoke checks that the served `/openapi.json` is the
committed spec and that `/info` `openapi_sha256` is its digest — the check AMČR runs against a
deployed image, and the container-level proof for page-classification. Both skip in a repo that
has not adopted the contract yet.

## 🌿 5. `agent-skill` branch anatomy (normative)

```
SKILL.md                      # the skill contract — frontmatter + required sections (§7)
README.md                     # branch README: what this branch is + install per host (§8)
scripts/
  atrium_<verb>.py            # zero-dependency client (§6, Appendix B)
  server.sh                   # idempotent server launcher (Appendix C) — named server.sh
service/                      # the FastAPI app, unchanged from default branch
  api.py · atrium_service.py · requirements.txt · README.md · frontend*/
<source modules hoisted to repo root>   # the service's full transitive import closure
  atrium_paradata.py · atrium_document.py · atrium_document.schema.json · …
small_data_samples/           # tiny licensed inputs for smoke tests (+ LICENSE)
setup/para_config.txt         # version source (§4.6) + setup scripts the launcher needs
Dockerfile · docker-compose*.yml        # compose `api` profile, port 8000
CITATION.cff · LICENSE · .gitignore · .dockerignore
```

Removed relative to the default branch: `tests/` (including stray `test_*.py` outside it),
lint/CI configs (`ruff.toml`, `pytest.ini`, `.pre-commit-config.yaml`, coverage),
`supplementary/`/analysis material, dev-only frontends, and every `.github/workflows/` file
except the `skill-validate.yml` caller — anything a *running* skill doesn't need.

**Rule: the hoisted set is the service's _transitive_ import closure, not just what
`service/*.py` names directly.** A one-level reading is what left `atrium_document.py` off all
five branches in the 2026-07-29 re-drift: translator's `service/api.py` never imports it, but
the `main.py` it calls does. `tools/skill_drift_check.py` computes the closure — imports guarded
by `try: … except ImportError:` are optional and do not count (that is how `para_licenses.py`
stays legitimately trimmed).

**Rule (CI-checked, [§12.3](#123-skill-validation-ci-reusable-workflow--authored)): every file path
referenced by `SKILL.md`, `README.md`, or `service/README.md` must exist on the branch, and every
endpoint they advertise as `GET /x` / `POST /x` must be one the service actually serves.**
(Generalized from exemplar defects (a) `serve.sh` vs committed `server.sh`, and (c)
`frontend-lindat/` documented but absent.)

**What that rule does _not_ cover — static mounts.** An earlier revision of this section claimed
the endpoint half had caught llm-enrich's and translator's branch READMEs advertising a frontend
"mounted at `/frontend`" that neither `service/api.py` mounted. It had not, and could not: step 2
skips `/`-rooted tokens as absolute paths, and step 4's `GET /x` pattern deliberately ignores a
bare backticked `/frontend`, because that same form also names Claude Code slash-commands. The
claim was false for six weeks and CI stayed green throughout; it was found by reading
`app.mount()` calls, not by a check. Both branches now carry the mount (2026-09-09), written as a
guarded no-op so the same code is safe on any branch:

```python
_frontend_dir = Path(__file__).resolve().parent / "frontend"
if _frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
```

Because it turns itself off where the directory is absent, this is forward-mergeable to the
default branch rather than a permanent skill-branch fork — which is the shape any §9 frontend
change should take. A mount is still not something `skill-validate` verifies. What guards it
is `tools/skill_drift_check.py`, which compares `service/api.py` byte-for-byte: a mount added or
dropped on one branch and not the other surfaces there as content drift, and the deliberate case
is recorded in that tool's `DOCUMENTED_DIVERGENCES` table with the reason.

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
      _(Shipped synchronous; async jobs deferred to the W5 fast-follow. Corrected 2026-09-27
      (atrium-project#53): this note used to say "with a strict concurrency guard + `504`
      timeout", but `service/` has neither — no semaphore, no 429, no request deadline; each
      upstream call is bounded only by `LLM_TIMEOUT` × `LLM_MAX_RETRIES`, both reported in
      `/info`.)_
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
`/health` exists and returns the §4.1 shape. (Pattern: extend the existing `tests/test_api*.py`
/ `tests/test_service_api.py`.) Since atrium-project#32 round 2 the vendored
`tests/test_openapi_contract.py` also holds the **committed** `service/openapi.json` to the app
— current, typed, environment-independent, generated by the pinned fastapi and pydantic — and
`tests/test_api_contract.py` validates real responses against it (§4.8).

### 12.2 Branch sync policy — **manual landing, scripted diagnosis**

The `agent-skill` branches were hand-built as flattened/trimmed derivatives, so they do **not**
share history cleanly with their default branches — for alto-postprocess, nlp-enrich and
page-classification there is **no merge base at all**, so `git merge` is not available and
"how stale is this branch?" cannot be answered from `git log`. Landing therefore stays
**manual**. Diagnosing no longer is; two hub tools do that part:

- **`tools/skill_drift_check.py`** — the standing tripwire. Compares `agent-skill` against the
  default branch by content: differing common files (minus an expected-divergence allowlist),
  file-mode drift, the transitive runtime closure the branch is missing, `para_config.txt`
  version lag, and byte-parity of the para-drift-guarded shared files. Exit 1 on drift, so it
  can gate a release. Run it *before* deciding anything.
- **`tools/skill_ify.py`** — derives what the branch tree *should* be (trimmed default branch +
  the skill overlay) and prints the add/update/delete plan, or materializes the tree with
  `apply --into DIR` to diff by hand. Advisory by design: it never commits, never pushes, and
  never proposes deleting a skill-authored file — retiring one (alto's forked
  `text_util_langID.py`, say) is a human decision.

After any `service/` change or release tag on the default branch, run this checklist by hand:

1. **Port the `service/` change** onto the `agent-skill` branch (cherry-pick or copy the changed
   `service/*.py` + any newly-required runtime module — remember the branch is trimmed, so a new
   import must be carried over too, transitively: run `skill_drift_check.py` rather than reading
   the import lines by eye).
2. **Re-run the anti-pattern checklist** (§7 / each branch README "Maintenance notes"): no doc
   cites a script name that differs from the committed file; no provenance claim unless the
   service writes paradata on this branch; no reference to absent files; documented response
   fields match `api.py`.
3. **Re-run the client smoke test** on `small_data_samples/` against a locally started server
   (`bash scripts/server.sh`), and re-check `/info`+`/health` against §4.1.
4. **Let CI confirm**: the `skill-validate.yml` caller (§12.3) runs on the push and guards
   frontmatter, referenced paths, the zero-dependency client claim, and the endpoint/`/info`
   contract.
5. **Bump the skill tag** (`skill-v<para_config version>`) so agents can pin the synced state.
6. **Re-run `skill_drift_check.py`** — it must exit 0 before the sync counts as done.

Fully automating the *landing* (an auto forward-merge action) stays deferred: with three
branches sharing no history there is nothing to merge, and the trim decisions need a human.

### 12.3 Skill-validation CI (reusable workflow — authored)

`skill-validate.reusable.yml` lives in atrium-project `.github/workflows/` (authored; publish to
`test`), called by a `.github/workflows/skill-validate.yml` on each repo's `agent-skill` branch
(caller template: `docs/templates/workflows/skill-validate.caller.example.yml`):

1. SKILL.md frontmatter parses; `name`/`description` constraints hold.
2. **Every file path referenced in SKILL.md / README.md / service/README.md exists on the
   branch** — would have caught exemplar defects (a) and (c).
3. The client script compiles (`python -m py_compile`) and runs `--help` in a bare
   `python:3.11-slim` container — proves the zero-dependency claim.
4. **The endpoint contract** — implemented, in two passes, because the skill branches carry no
   `tests/` and so have no contract test to fall back on:
   - **4a (static, zero-dependency, never skips)**: every endpoint the docs advertise as
     `GET /x` / `POST /x` is declared by a route decorator or mount in `service/*.py`, and every
     §4.2 primary endpoint is present. A bare backticked `` `/x` `` is deliberately *not* read as
     an endpoint claim — the branch READMEs use that form for the Claude Code slash-command name
     (`/atrium-llm-enrich`) and for static mounts.
   - **4b (live)**: boots the app in-process and asserts the §4.1 `/info` envelope
     (`service` == repo id, `version` == `app.version`, advertised endpoints are real routes,
     `limits.max_upload_mb`), the `/health` shape, the documented endpoints against
     `app.openapi()["paths"]`, and OpenAPI spec validity. Import-skips on the model-heavy repos
     exactly as `api-contract.reusable.yml` does, emitting a CI **warning** so a skip is never
     mistaken for a pass — 4a is what keeps the check honest there.

   Callers pass `app-import` and `primary-endpoints`; use the same values as that repo's
   default-branch `tests/test_api_contract.py`, so both branches assert one contract.

Caller example: `docs/templates/workflows/skill-validate.caller.example.yml` (carries the
per-repo parameter table).

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
  `ATRIUM_<XX>_URL` is *inbound* — where the client finds this service. It is
  unrelated to the *outbound* backing-service variables (`UDPIPE_URL`,
  `NAMETAG_URL`, `TRANSLATION_URL`, `KOREKTOR_URL`, atrium-project#63), which
  say where this service finds the third-party APIs it calls. The two are
  orthogonal; neither replaces the other.
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
5. Errors: the §4.4 table with its `reason` column and service-specific notes.
6. Configuration: the shared seven-row contract copied verbatim from
   `docs/templates/skill/serviceREADME.template.md`, plus this service's operator-facing
   variables, plus a pointer to the repo's `.env.example` (the complete ledger — layout per
   `docs/templates/env.example.template`).
7. Run: venv/uvicorn + `docker compose --profile api up` (+ GPU variant).
8. Frontend(s): where mounted, what they demonstrate.
9. Tests: how to run the API tests (default branch only).
10. OpenAPI: where the committed spec is, how to regenerate it, the release comparison and the
    fastapi/pydantic pins (§4.8).

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
a uniform `/process` primary endpoint everywhere (breaks existing clients for cosmetic gain).
Committed `openapi.json` snapshots were rejected on 07-23 (drift) and adopted on 2026-09-28 with
a freshness test that turns the drift into a red build (§2.2, §4.8).

---
_Maintained in `atrium-project` next to the ecosystem record
([`plan_repo_review.md`](plan_repo_review.md)). Templates graduate to `docs/templates/skill/`
after validation (rollout step 3). Session log: `agent_dev_logs/plans/31.plan.md` ·
`agent_dev_logs/digests/31.digest.md`._
