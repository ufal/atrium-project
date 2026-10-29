# <Tool> API service

<One-line purpose: what goes in, what comes out.> The service version is read
from `para_config.txt` `[tool]` (single source of truth, never hard-coded).

<!--
Written for the operator who runs this service (atrium-project/docs/documentation-style.md, Readers).
State facts, not their history: no issue numbers in headings or running text, no "since vX".
Link an issue only for an open problem the operator may want to follow. Delete this comment.
-->

## Start

**At a glance:**

| Image                                      | CPU / GPU                                   | Memory                                            | Volumes                         | Calls out to                                       | Ready after                                    |
|--------------------------------------------|---------------------------------------------|---------------------------------------------------|---------------------------------|----------------------------------------------------|------------------------------------------------|
| `ghcr.io/ufal/atrium-<tool>-api:<version>` | <CPU only / a CUDA GPU optional / required> | <steady-state use; the `limits.memory` that fits> | <`/cache/huggingface`, or none> | <hosts called at start and per request, or "none"> | <seconds to `/ready` 200, warm and cold cache> |

The published image first: it is what a deployment runs, and it needs no checkout.

```bash
docker run --rm -p 8000:8000 ghcr.io/ufal/atrium-<tool>-api:<version>   # the released image
curl -s http://localhost:8000/ready                                        # 200 once warm
# from a checkout:
docker compose --profile api up -d
# or in a virtual environment (development):
pip install -r <requirements files>
python -m service.<module>                  # honours PORT/HOST; default 0.0.0.0:8000
uvicorn service.<module>:app --host 0.0.0.0 --port 8000 --reload
```

<frontend note: where the demo frontend is mounted>

## Models and caches

What the service fetches or loads before it can answer, so a deployment without internet access
knows what to provide. "None" is an answer: say so when the image is self-contained.

| What            | From where                   | Revision            | Into                           | Without egress                               |
|-----------------|------------------------------|---------------------|--------------------------------|----------------------------------------------|
| <model or file> | <Hugging Face repo / URL>    | <pinned revision>   | <path; `HF_HOME` if a cache>   | <baked into the image / mount a volume / …>  |
| <remote API>    | <LINDAT / provider endpoint> | —                   | —                              | <the error a caller gets, and its `reason`>  |

## Endpoints

| Method | Path         | Purpose                                                                                                                                                                                  |
|--------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET    | `/info`      | service identity + capabilities: `service`, `version`, `endpoints`, `limits`, `limits_meta`, <capabilities>                                                                              |
| GET    | `/health`    | liveness probe; 200 always, even mid-shutdown. `?deep=true` additionally <backend/model probe> (503 on fail or while draining)                                                           |
| GET    | `/ready`     | readiness probe (issue #55): 503 until warm, 200 while serving, 503 the instant a shutdown signal arrives — this is the Kubernetes `readinessProbe`/`startupProbe` target, not `/health` |
| POST   | `/<primary>` | <domain endpoint(s), one row each, with params>                                                                                                                                          |

### `POST /<primary>` (<multipart form / JSON>)

| Field   | Default    | Notes                                   |
|---------|------------|-----------------------------------------|
| `file`  | *required* | <accepted suffixes, field named `file`> |
| <param> | <default>  | <meaning>                               |

```bash
curl -X POST "http://localhost:8000/<primary>" -F "file=@<sample>" <-F params>
curl -s http://localhost:8000/info
```

### Response schema

```json
<real example response — copy from an actual server run>
```

| Field   | Type   | Description                                              |
|---------|--------|----------------------------------------------------------|
| <field> | <type> | <meaning — MUST match what the service actually returns> |

## Errors

Every error has one JSON body (hub `docs/agent_skill_strategy.md` §4.4):
`{"status": <int>, "reason": <registered code or null>, "detail": "<text>"}`, plus `limit`
for `reason: "limit_exceeded"` (`key`, `env`, `value`, `observed`, `unit`), `accepted` for
`reason: "unsupported_media_type"`, `errors` for validation problems and, where the service has
one, an informational `cause` (unregistered; branch on `reason`). The registered codes and their
statuses are listed in the spec's `x-atrium-reason-codes` (see [OpenAPI](#openapi-the-typed-contract)).

| Code    | `reason`                        | Meaning                                                                                                                                                              | What to do                                                             |
|---------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| 413     | `limit_exceeded`                | request content over a limit (see [Limits](#limits))                                                                                                                 | split the input, or raise the setting `limit.env` names                |
| 415     | `unsupported_media_type`        | a type this endpoint does not read; `accepted` lists what it reads                                                                                                   | convert to a type in `accepted`                                        |
| 422     | `invalid_record`                | the `document_json` record cannot be opened (not JSON, not an object, a newer `schema_version` major), or a block this service adds rows to is not a list of objects | send the record the previous stage wrote; update this service if newer |
| 422     | `null` / `limit_exceeded`       | unusable/invalid input; or a parameter / per-input budget over its limit                                                                                             | fix the field `errors` names, or raise the setting `limit.env` names   |
| 429     | `busy`                          | every slot or queue place taken — retry after `Retry-After` seconds                                                                                                  | retry after `Retry-After`; add replicas if it persists                 |
| 500     | `null`                          | processing failure                                                                                                                                                   | report it with `detail` and the request id                             |
| 502     | `upstream_unavailable`          | a backing service did not answer after this service's retries — **clients retry 3× with backoff**                                                                    | retry; if it persists, check the service `detail` names                |
| 502     | `null`                          | the run produced nothing (`detail` names the cause) — no retry: it fails the same way again                                                                          | fix the input `detail` names; do not retry unchanged                   |
| 503/504 | `null` / `limit_exceeded` (504) | not ready / warming up / an upstream time limit — **clients retry 3×**                                                                                               | wait for `/ready`; for 504, raise the time limit `limit.env` names     |

<drop rows that cannot occur for this service; add service-specific notes. Every row keeps a
"What to do" cell: `tools/runbook_check.py` in the hub checks it.>

## Limits

Every limit this service has is a setting, reported with its
current value in `/info` `limits` (and the variable that sets it in `limits_meta`). Over a
limit, the service refuses with `reason: "limit_exceeded"` or processes the input in full;
where a limit shapes a result, the response's `limits_applied` says so (and the paradata).
`tests/test_api_contract.py` checks this table against `tool_limits.py` and `/info`.

| Key (`/info`)   | Variable                              | Default | Unit   | Over the limit                                                              |
|-----------------|---------------------------------------|---------|--------|-----------------------------------------------------------------------------|
| `max_upload_mb` | `MAX_UPLOAD_MB`                       | <n>     | MB     | 413 `limit_exceeded`                                                        |
| `<key>`         | `<VARIABLE>`                          | <n>     | <unit> | <413/422/504 `limit_exceeded`, or processed in full with a `<effect>` note> |
| `<derived>`     | — (derived from `<VARIABLE>`/<model>) | —       | <unit> | <…>                                                                         |

Platform limits (not settings): <libxml2 without `huge_tree` / Starlette multipart defaults / …, or "none">.

## Partial results

When a response is 200 but not everything was done, it says so; a caller must read these before
using the result.

- `limits_applied`: each limit that shaped the result (`limit`, `effect`, `count`), as in the
  paradata.
- `partial` (where the service has stages or batches): <which part, what the caller gets for it,
  and the field that counts it>.
- <the tool's own statuses and what each means for the caller>.

## Known limits

What the service does not do well, in one line each, with a link to the detail. Users read this
before they trust a result.

- <limit> — <consequence>; see <link>.

## Configuration (environment)

| Variable              | Default   | Meaning                                                                 |
|-----------------------|-----------|-------------------------------------------------------------------------|
| `PORT`                | `8000`    | port the service **binds**, and the one `service/healthcheck.py` probes |
| `HOST`                | `0.0.0.0` | bind address; see the note below                                        |
| `GRACEFUL_SHUTDOWN_S` | `20`      | seconds uvicorn waits for in-flight requests on shutdown                |
| `RELOAD`              | `false`   | filesystem auto-reload — development only, never in a deployment        |
| `LOG_LEVEL`           | `INFO`    | root logger level for the `python -m service.<module>` start path       |
| `MAX_UPLOAD_MB`       | <n>       | canonical upload limit                                                  |
| `ALLOWED_ORIGINS`     | `*`       | CSV of CORS origins                                                     |
| <service vars>        | <…>       | operator-facing only — the complete ledger is `.env.example`            |

The first five rows are the ecosystem-wide contract and are identical in all six services:
copy them verbatim rather than rewording per repo. They
are read by `service/<module>.py`'s `__main__` block, which is what the `api` image's
`ENTRYPOINT` runs.

> **Note:** `HOST=127.0.0.1` yields a container that reports **healthy** and serves nobody:
> `service/healthcheck.py` always probes loopback by design and never reads `HOST`, so a
> loopback bind passes every probe while being unreachable from outside the container.

This table is the deployment-facing **subset**. The complete ledger — every variable this
image reads, including the algorithmic ones a deployment never touches — is
[`.env.example`](../.env.example) at the repo root, whose layout is fixed by
[`docs/templates/env.example.template`](https://github.com/ufal/atrium-project/blob/main/docs/templates/env.example.template)
in the hub. The cross-service operator reference is the hub's `docs/k8s_deployment.md`.

## How it works

<2–6 sentences: what the endpoint drives internally, concurrency and timeout
behaviour, provenance (paradata) if actually written>

## Frontend(s)

<where mounted, what they demonstrate; every frontend carries the API footer
(hub `docs/agent_skill_strategy.md` §9): curl example + /docs + /openapi.json + this README>

## OpenAPI (the typed contract)

The service's OpenAPI document is committed as [`service/openapi.json`](openapi.json) and
attached to every release as `openapi.json` with its `openapi.json.sha256` (hub
`docs/agent_skill_strategy.md` §4.8). Every request and response field is typed, every error
response is the error body above, and a returned record is typed by the vendored record schema
(`AtriumDocument`). `GET /info` reports `openapi_sha256`, the digest of the spec the running
image serves.

- **After an API change**, regenerate and commit it:
  `python atrium_openapi.py export --app <module>:app --out service/openapi.json`
  <`--prepare tests.openapi_contract_data:prepare` if the app needs a stub to import>.
  `tests/test_openapi_contract.py` fails while it is stale.
- **Compatibility.** Each release compares its spec with the previous release's: a breaking
  change fails the release unless the major version went up (for 0.x, that means 1.0), and a
  removed reason code always fails.
- **fastapi and pydantic are pinned** exactly (<the requirement files>): bump both by hand and
  regenerate.

## Tests

<how to run the API tests; on skill branches point at the development branch
that carries tests/>
