# <Tool> API service <emoji>

<One-line purpose: what goes in, what comes out.> The service version is read
from `para_config.txt` `[tool]` (single source of truth, never hard-coded).

## Quick start

```bash
pip install -r <requirements files>
uvicorn service.<module>:app --host 0.0.0.0 --port 8000
# or:
docker compose --profile api up -d
```

<frontend note: where the demo frontend is mounted>

## Endpoints

| Method | Path        | Purpose                                                                        |
|--------|-------------|--------------------------------------------------------------------------------|
| GET    | `/info`     | service identity + capabilities: `service`, `version`, `endpoints`, `limits`, <capabilities> |
| GET    | `/health`   | liveness probe; `?deep=true` additionally <backend/model probe> (503 on fail)  |
| POST   | `/<primary>`| <domain endpoint(s), one row each, with params>                                |

### `POST /<primary>` (<multipart form / JSON>)

| Field | Default | Notes |
|-------|---------|-------|
| `file` | *required* | <accepted suffixes, field named `file`> |
| <param> | <default> | <meaning> |

```bash
curl -X POST "http://localhost:8000/<primary>" -F "file=@<sample>" <-F params>
curl -s http://localhost:8000/info
```

### Response schema

```json
<real example response — copy from an actual server run>
```

| Field | Type | Description |
|-------|------|-------------|
| <field> | <type> | <meaning — MUST match what api.py actually returns (defect-d rule)> |

## Errors

| Code        | Meaning                                                  |
|-------------|----------------------------------------------------------|
| 413         | payload too large (`MAX_UPLOAD_MB`<, service caps>)      |
| 415         | unsupported media type                                   |
| 422         | unusable/invalid input                                   |
| 429         | busy (concurrency limit) — retry later                   |
| 500         | processing failure                                       |
| 502/503/504 | not ready / warming up / upstream — **clients retry 3×** |

<drop rows that cannot occur for this service; add service-specific notes>

## Configuration (environment)

| Variable          | Default | Meaning                     |
|-------------------|---------|-----------------------------|
| `MAX_UPLOAD_MB`   | <n>     | canonical upload limit      |
| `ALLOWED_ORIGINS` | `*`     | CSV of CORS origins         |
| <service vars>    | <…>     | <…>                         |

## How it works

<2–6 sentences: what the endpoint drives internally, concurrency/timeout
behavior, provenance (paradata) if actually written>

## Frontend(s)

<where mounted, what they demonstrate; every frontend carries the §9 API
footer: curl example + /docs + /openapi.json + this README>

## Tests

<how to run the API tests; on skill branches point at the development branch
that carries tests/>
