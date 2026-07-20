---
name: atrium-<tool>
description: <What it does — inputs, outputs, models.> Use this skill to <when/why an agent
  should pick it — the routing purpose in the ATRIUM pipeline>.
---

# ATRIUM <Tool Name> Skill <emoji>

This skill provides agent access to the **ATRIUM <Tool>** service — <one-line what/how>.
It follows a **server-client** design: a FastAPI server (in `service/`) performs the heavy
work, and a zero-dependency client script (`scripts/atrium_<verb>.py`) is the only thing the
agent calls directly.

## Operational Requirements ⚙️

- **Server**: a running instance is required. Default `http://localhost:8000`; override with
  `--base-url` or the `ATRIUM_<XX>_URL` environment variable.
- **Client dependencies**: none — Python 3 standard library only.
- **Server dependencies**: Docker (recommended, compose `api` profile) or a Python venv with
  `service/requirements.txt`<+ repo requirements as applicable>.
- **First launch**: <model download sizes / vocabulary sync / warmup time — minutes, not
  seconds>. Do **not** treat a slow first start as failure.
- **Limits**: <MAX_UPLOAD_MB> MB per file<, service-specific limits: line caps, page caps,
  concurrency (HTTP 429 when busy)>.

## <Domain reference: categories / languages / stages / vocabularies> <emoji>

<the tool's vocabulary as a table: categories + routing semantics (page-classification,
alto-postprocess), mode/language matrix (translator), stage plan + keyword methods
(nlp-enrich), backends + vocabulary contract (llm-enrich)>

## Workflows 🪄

### 1. Ensure the server is running

```bash
bash scripts/server.sh          # Docker (or local uvicorn fallback)
bash scripts/server.sh --gpu    # Docker with GPU            <if applicable>
bash scripts/server.sh --local  # force local uvicorn (no Docker)
```

Idempotent: exits immediately if `GET /info` already answers; waits for first-run warmup.

### 2. <Primary action>

```bash
python3 scripts/atrium_<verb>.py <input> [flags]        # main variant
python3 scripts/atrium_<verb>.py --info                 # discover capabilities
python3 scripts/atrium_<verb>.py <input> --format json  # machine-readable
<one example per major mode — cover every service-specific flag at least once,
including a small_data_samples/ file so the smoke test is copy-pasteable>
```

### 3. Interpret output

<row format; which --format for which purpose; where non-tabular outputs (XML attachments,
ZIP workspaces) land; what goes to stderr>

## Agent Guidelines 🤖

1. <model/param selection discipline>
2. <uncertainty discipline — surface top-N/scores/confidence, don't over-assert>
3. Prefer `--format json` when the result feeds further processing.
4. For full request/response schemas, fetch `GET /openapi.json` from the running server
   (Swagger UI at `/docs`).
5. Exit code `2` (unreachable): start the server (`bash scripts/server.sh`) and retry once.
   Exit code `3` (server error): the client already retried 502/503/504 3× — check
   `GET /health?deep=true` and server logs, do not loop.
6. <busy handling — HTTP 429 → async jobs / retry later, if the service has a concurrency
   guard>
7. <size-limit handling — what to split/downscale, and tell the user you did so>
8. Do not bypass the API by importing the model code directly<; server-side runs are
   paradata-logged — ONLY claim this if the service actually writes paradata on this branch
   (strategy §4.7)>.

## Acknowledgements & Citations 🙏

Developed within the [ATRIUM](https://atrium-research.eu/) project at ÚFAL, Charles
University<; data/services on [LINDAT/CLARIAH-CZ](https://lindat.cz)>. Cite `CITATION.cff`
<+ dataset handle>.
