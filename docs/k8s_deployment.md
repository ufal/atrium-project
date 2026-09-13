# ATRIUM Kubernetes Deployment Reference

> **Status:** Active Document (added 2026-09-07, issue #55)
> **Scope:** `atrium-translator`, `atrium-nlp-enrich`, `atrium-page-classification`,
> `atrium-alto-postprocess`, `atrium-llm-enrich` — the five `-api` images.
>
> This document is the deployment-side half of issue #55 (`HEALTHCHECK` + `SIGTERM`
> handling). The code-side half — `ServiceState`, `/ready`, `serve_lifecycle`,
> `attach_inflight_middleware` — lives in
> [`templates/shared/atrium_service.py`](templates/shared/atrium_service.py) and is
> described in `docker_gha.md` §3.4. **This file is what to hand ARÚP/ARÚB**, alongside
> [`templates/k8s/atrium-service.deployment.yaml`](templates/k8s/atrium-service.deployment.yaml)
> and the acceptance procedure in
> [`k8s_acceptance_runbook.md`](k8s_acceptance_runbook.md).

## Why this document exists — a Dockerfile `HEALTHCHECK` is invisible to Kubernetes

Issue #55 was opened on the premise that a Docker `HEALTHCHECK` directive makes `/health`
"visible to a Kubernetes liveness probe." **It does not.** The kubelet reads
`livenessProbe`/`readinessProbe`/`startupProbe` from the **pod spec** and never consults an
image's `HEALTHCHECK` at all — the two mechanisms are independent, and only Docker/Compose/
Podman ever read the latter. `HEALTHCHECK` is still worth having (it documents the probe
contract inside the image, and it is what `docker-tool.reusable.yml`'s CI smoke test in
`docker-build-smoke` actually exercises), but it does not, by itself, satisfy this issue's
Kubernetes-facing acceptance criterion. This document and the manifest template it
accompanies are the part that does.

## The two probes ATRIUM services now expose, and which one is which

As of issue #55, every `-api` image's shared `service/atrium_service.py` registers:

| Route                   | Purpose                                                      | 200 while draining?                          | Kubernetes field                     |
|-------------------------|--------------------------------------------------------------|----------------------------------------------|--------------------------------------|
| `GET /health`           | **Liveness** — "is the process alive at all"                 | **Yes, always**                              | `livenessProbe`                      |
| `GET /health?deep=true` | Deep liveness — also runs the service's own dependency check | No, once draining or if the deep check fails | (not a K8s probe target — see below) |
| `GET /ready`            | **Readiness** — "should traffic be routed here right now"    | **No — 503 the instant `SIGTERM` arrives**   | `readinessProbe`, `startupProbe`     |

The separation is deliberate and is the single most important design choice in this issue:
**a liveness probe must never fail during a graceful shutdown.** If `/health` flipped to 503
the moment a rolling restart sent `SIGTERM`, the kubelet would read that as "the process is
broken" and `SIGKILL` the pod immediately — which is exactly the "rolling restart kills
in-flight work" failure this issue exists to fix, just moved one layer up the stack. Routing
new traffic away from a draining pod is `/ready`'s job, not `/health`'s.

`?deep=true` is intentionally **not** wired to any Kubernetes probe. A dependency check
(a model file present, an upstream LLM backend reachable) can be slow or flaky in ways that
have nothing to do with whether *this* process should be restarted or de-routed; wiring it to
`livenessProbe` risks a slow-but-recovering dependency causing a restart loop, and to
`readinessProbe` risks flapping a pod in and out of service for the same reason. It remains
available for humans and dashboards via `curl .../health?deep=true`.

## Reading the manifest template

[`templates/k8s/atrium-service.deployment.yaml`](templates/k8s/atrium-service.deployment.yaml)
is a commented, parameterised `Deployment` + `Service`. The load-bearing fields, in the order
a rolling restart actually exercises them:

1. **`startupProbe` → `/ready`**, generous `failureThreshold × periodSeconds` (5 minutes by
   default). Every one of these five services warms a model (or, for translator, a remote
   backend) at startup; a short startup budget turns a slow-but-healthy first request into a
   restart loop — precisely the operational failure mode #55 exists to remove, reintroduced
   at the K8s layer if this budget is too tight.
2. **`readinessProbe` → `/ready`** — the ongoing check. `failureThreshold: 2` with a 5s
   period means roughly 10s from `SIGTERM` to the endpoint being pulled from the Service —
   see the `preStop` note below for why this is not fast enough on its own.
3. **`lifecycle.preStop: sleep 5`** — verified empirically (this issue's strategy write-up):
   uvicorn stops accepting new TCP connections within milliseconds of receiving `SIGTERM`,
   well before `kube-proxy` has had a chance to notice the readiness flip and remove the pod
   from the Service's endpoint list. Without a `preStop` delay, a rolling restart drops
   requests that were already routed here **even with perfectly correct in-app `SIGTERM`
   handling** — this is a distinct failure mode from anything code inside the container can
   fix, because the container's socket closing and the Service's endpoint list updating are
   two independently-timed things. `preStop` runs *before* the container receives `SIGTERM`,
   buying the propagation time the readiness flip needs.
4. **`terminationGracePeriodSeconds: 60`** — must exceed the `preStop` delay **plus** the
   container's own graceful-shutdown budget (`GRACEFUL_SHUTDOWN_S`, see "Configuring the
   port and bind address" below) **plus** `serve_lifecycle`'s
   `drain_timeout` (see `atrium_service.py`): `5 + 20 + 25 = 50`, with the manifest's `60`
   giving 10s of headroom. The kubelet `SIGKILL`s at this deadline no matter what the
   process is doing; size it to the slowest legitimate in-flight request a repo expects —
   translator's per-chunk LINDAT calls and llm-enrich's per-line LLM calls are the two
   services most likely to need this widened, since a single request there can
   legitimately run for minutes (see "Known limits" below — this default protects a
   *typical* request, it does not make every possible request-duration safe).
5. **`livenessProbe` → `/health`**, deliberately looser than readiness (15s period, 3
   failures) — it exists to catch a truly wedged process, not to participate in routing.

## Configuring the port and bind address

The manifest's `env:` block sets `PORT`, and all five images honour it — `service/api.py`'s
`__main__` block (alto-postprocess: `service/text_api.py`) reads `PORT`, `HOST`,
`GRACEFUL_SHUTDOWN_S` and `RELOAD` from the environment, with the manifest's values as
defaults. Until atrium-project#58 this was true of alto-postprocess only: the other four
baked `--port 8000` into an exec-form `ENTRYPOINT`, where no shell exists to expand a
variable, so the declared setting did nothing.

| Variable              | Default   | Effect                                                                                                                                                          |
|-----------------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PORT`                | `8000`    | The port the service binds **and** the port `service/healthcheck.py` probes.                                                                                    |
| `HOST`                | `0.0.0.0` | The bind address. See the warning below before changing it.                                                                                                     |
| `GRACEFUL_SHUTDOWN_S` | `20`      | uvicorn's bound on waiting for in-flight requests, formerly the `--timeout-graceful-shutdown` CLI flag. Raise it together with `terminationGracePeriodSeconds`. |
| `RELOAD`              | `false`   | Filesystem-watching auto-reload. A development convenience; never set it in a deployment.                                                                       |

**To run on a different port, change two fields, not one.** `PORT` in the `env:` block and
`containerPort` in the `ports:` block must agree — `PORT` is what the process binds,
`containerPort` is what Kubernetes records. The three probes reference the port by *name*
(`port: http`), so they follow `containerPort` automatically and cannot drift from it; that
is the only reason changing the port is a two-line edit rather than a five-line one.

> ⚠️ **`HOST=127.0.0.1` produces a container that reports healthy and serves nobody.**
> `service/healthcheck.py` always probes `127.0.0.1` by design — a health probe should
> interrogate the local process, not the published interface — and it never reads `HOST`.
> So a loopback bind passes every liveness and readiness check while being unreachable from
> outside the pod. This is the one value in the table above whose failure mode is silent;
> leave `HOST` at `0.0.0.0` unless you have a specific reason not to.

The four variables above are what the port-and-bind discussion needs. The section below is
the full operator-facing contract across all five services — including the three
(`ALLOWED_ORIGINS`, `MAX_UPLOAD_MB`, `LOG_LEVEL`) whose effective default depends on *how* you
started the container, and the one service this manifest cannot deploy unmodified.

## Environment variables — one contract, and the defaults that disagree with it

Every service reads all of these identically. The manifest sets one and comments the rest —
"In the template manifest" below is set / commented / **—** (not present at all, on purpose).
Each repo's own `.env.example` is the complete ledger this table is drawn down from; its layout
is fixed by [`templates/env.example.template`](templates/env.example.template). A variable
named in one place and not the other is a bug in whichever was edited last —
atrium-project#60's CI guard (`tests/test_env_contract.py`, both hub-local and vendored into
each of the five repos) fails on exactly that.

**Table A — common to all five**

| Variable              | Code default  | In the template manifest | What it does / why you would change it                                                                                                                                                            |
|-----------------------|---------------|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PORT`                | `8000`        | **set**                  | The port the process binds **and** the port `service/healthcheck.py` probes. Change `containerPort` in the same edit.                                                                             |
| `HOST`                | `0.0.0.0`     | commented                | Bind address. ⚠️ `127.0.0.1` yields a pod that reports healthy and serves nobody — see the warning above.                                                                                         |
| `GRACEFUL_SHUTDOWN_S` | `20`          | commented                | uvicorn's bound on waiting for in-flight requests. Raise it together with `terminationGracePeriodSeconds`.                                                                                        |
| `ALLOWED_ORIGINS`     | `*`           | commented                | CSV of CORS origins. `*` is every origin. An **empty** value is not the same as omitting it — see the callout below.                                                                              |
| `MAX_UPLOAD_MB`       | *per service* | commented                | Canonical upload limit. There is no shared number — see the table below.                                                                                                                          |
| `LOG_LEVEL`           | `INFO`        | commented                | Root logger level for the entrypoint. All five honour it identically (atrium-project#61); `tests/test_logging_contract.py` is vendored in each repo and fails if one drifts.                      |
| `RELOAD`              | `false`       | **—, deliberately**      | uvicorn filesystem auto-reload. There is no correct value for a Deployment, so there is no commented entry to uncomment by accident.                                                              |
| `HEALTHCHECK_PATH`    | `/health`     | **—**                    | The path the container's own `HEALTHCHECK` probes. Kubernetes does not read a `HEALTHCHECK` (see this document's opening section), so it is irrelevant here — change it only alongside the route. |
| `MAX_UPLOAD_BYTES`    | —             | **—**                    | **Deprecated.** A byte-valued fallback that loses to `MAX_UPLOAD_MB` whenever both are set. Do not introduce it.                                                                                  |

The `RELOAD` and `HEALTHCHECK_PATH` rows exist so their absence from the manifest reads as a
decision, not an omission.

**Two defaults, and which one applies to you.** Every value in the *Code default* column above
is what you get in Kubernetes. Three of them are not what you get under `docker compose`, and
each difference runs the same direction — compose supplies the safer value, and Kubernetes
silently gets the raw one:

| Variable                                                | Code default — Kubernetes gets this                                         | Compose default                                                                                                                                                                       | Consequence                                                                                                                                                                                                            |
|---------------------------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ALLOWED_ORIGINS`                                       | `*` — every origin                                                          | alto-postprocess `http://localhost:8080,http://localhost:5500`; page-classification `http://localhost:8080,http://127.0.0.1:8080`; llm-enrich / nlp-enrich / translator: not narrowed | A Kubernetes deployment that omits this serves CORS to anything. Set it explicitly. (`localhost` and `127.0.0.1` are *different* origins to a browser, which is why the two compose defaults are not interchangeable.) |
| `OLLAMA_HOST` (llm-enrich)                              | `http://localhost:11434` — the **pod's own** loopback, where no Ollama runs | `http://host.docker.internal:11434`                                                                                                                                                   | Omitting it in Kubernetes does not fall back to the working compose value — it gives a URL that cannot reach an Ollama anywhere. Point it at the Ollama Service's DNS name.                                            |
| `MAX_CONCURRENT_JOBS`, `DEFAULT_KW_METHOD` (nlp-enrich) | `2` / `keybert`                                                             | the same values, passed through `.env`                                                                                                                                                | Under Kubernetes these behave normally and can be changed via the `env:` block; under `docker compose` prior to atrium-project#60 they could not be changed from `.env` at all.                                        |

> ⚠️ **`value: ""` is not the same as omitting the entry.** In an `env:` block,
> `- name: ALLOWED_ORIGINS` / `value: ""` parses to an *empty* origin list and blocks every
> browser request; omitting the entry gives you `*`. `PORT`, `GRACEFUL_SHUTDOWN_S` and
> `LOG_LEVEL` are worse — an empty value raises at startup and the pod crash-loops on
> `startupProbe`. To leave a variable at its default, delete the entry; do not blank it.

**`MAX_UPLOAD_MB` — what the five services share is the variable name and the resolver, not the
number.** The limit is a property of what each service ingests:

| Repo                | `MAX_UPLOAD_MB` | Set at                   | Why this number                                           |
|---------------------|-----------------|--------------------------|-----------------------------------------------------------|
| translator          | `50`            | `service/api.py:55`      | highest — ALTO XML in, ALTO XML out                       |
| alto-postprocess    | `25`            | `service/text_api.py:82` | ALTO XML for a whole scanned volume                       |
| llm-enrich          | `10`            | `service/api.py:46`      | a CSV of lines                                            |
| page-classification | `10`            | `service/api.py:56`      | a multi-page PDF                                          |
| nlp-enrich          | `5`             | `service/api.py:43`      | lowest — a 5 MB CSV is already at the `MAX_WORDS` ceiling |

The manifest's commented `MAX_UPLOAD_MB: "10"` is llm-enrich's and page-classification's
number. Uncommenting it as-is silently *raises* nlp-enrich's limit 2× and *lowers*
alto-postprocess's 2.5× and translator's 5×.

**Table B — per-repo operator deltas.** Operator-facing only; each repo's `.env.example` is the
complete ledger, and what is here is what a deployment legitimately sets.

| Repo                | Variable                                                                 | Default                   | Why an operator sets it                                                                                                                                                                                                                                                                             |
|---------------------|--------------------------------------------------------------------------|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| alto-postprocess    | `MODEL_DIR`                                                              | `<repo>/models`           | Point at a mounted PVC instead of the image layer — this is the knob that turns the crash-on-model-load-failure in *Known limits* into a fixable condition.                                                                                                                                         |
|                     | `LANGID_CONFIG`                                                          | `<repo>/setup/config.txt` | Language-ID config, when mounted from a ConfigMap.                                                                                                                                                                                                                                                  |
|                     | `DOCUMENT_JSON_DIR`                                                      | *(none)*                  | Where `document.json` output is written.                                                                                                                                                                                                                                                            |
| llm-enrich          | `LLM_BACKEND`                                                            | `openrouter`              | `openrouter` or `ollama`; decides which block below applies.                                                                                                                                                                                                                                        |
|                     | `OPENROUTER_API_KEY`                                                     | —                         | **Required, secret** — raises at startup when empty.                                                                                                                                                                                                                                                |
|                     | `OPENROUTER_MODEL`                                                       | —                         | **Required** — raises at startup when empty.                                                                                                                                                                                                                                                        |
|                     | `OLLAMA_HOST` / `OLLAMA_MODEL`                                           | see callout / —           | Ollama backend; `OLLAMA_MODEL` **required** for it.                                                                                                                                                                                                                                                 |
|                     | `LLM_TIMEOUT` / `LLM_MAX_RETRIES`                                        | `300` / `3`               | Per-call read timeout and retries; a cut-off call costs the whole enrichment.                                                                                                                                                                                                                       |
| nlp-enrich          | `UDPIPE_URL` / `NAMETAG_URL`                                             | LINDAT public hosts       | Attach a self-hosted UDPipe 2 / NameTag 3 (atrium-project#63).                                                                                                                                                                                                                                      |
|                     | `MAX_CONCURRENT_JOBS`                                                    | `2`                       | Bounds real CPU (each job is a subprocess) and shields the shared LINDAT endpoints.                                                                                                                                                                                                                 |
|                     | `API_JOB_TIMEOUT`                                                        | `600`                     | Seconds a single job may run before it is killed.                                                                                                                                                                                                                                                   |
|                     | `MAX_WORDS` / `MAX_RESCALE_DIM`                                          | `30000` / `100000`        | Synchronous-request caps.                                                                                                                                                                                                                                                                           |
|                     | `API_JOBS_ROOT`                                                          | `<repo>/TEMP/api_jobs`    | Point at an `emptyDir`/PVC with room for concurrent jobs, not the container filesystem.                                                                                                                                                                                                             |
| page-classification | —                                                                        | —                         | **None.** Its service layer reads nothing beyond Table A: `service/inference.py`, `service/document_json.py` and `service/api_client.py` contain no environment reads, and the batch CLI is configured through argparse and `config.txt`. A short entry here means few deployment knobs, not a gap. |
| translator          | `TRANSLATION_BACKEND`                                                    | `lindat`                  | `lindat` (CUBBITT) or `openai_compatible`.                                                                                                                                                                                                                                                          |
|                     | `TRANSLATION_URL`                                                        | LINDAT public host        | Attach a self-hosted translation service (atrium-project#63). `LINDAT_BASE_URL` is an accepted alias and **loses** when both are set.                                                                                                                                                               |
|                     | `UDPIPE_URL`                                                             | LINDAT public host        | Vocabulary lemma matching — deliberately the same name nlp-enrich uses for the same service.                                                                                                                                                                                                        |
|                     | `LINDAT_MIN_INTERVAL_S` / `LINDAT_MAX_RETRIES` / `LINDAT_BACKOFF_BASE_S` | `0.0` / `4` / `1.0`       | Rate-limits *this deployment* against a shared public service.                                                                                                                                                                                                                                      |
|                     | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`                               | —                         | Only when `TRANSLATION_BACKEND=openai_compatible`. `LLM_API_KEY` is a **secret**.                                                                                                                                                                                                                   |

**The manifest ships no `Secret`, no `secretKeyRef` and no `envFrom` — deliberately.** A
reference manifest that carried a key-shaped placeholder is a reference manifest someone
eventually commits a real key into. The commented `secretKeyRef` stanza in the `env:` block
shows the shape; creating the `Secret` is your step.


## Known limits — read before promising ARÚP/ARÚB more than this delivers

- **A synchronous request that outlives the whole shutdown chain is still cut short.**
  `GRACEFUL_SHUTDOWN_S` and `terminationGracePeriodSeconds` are finite by
  necessity — this issue makes the *typical* in-flight request safe across a rolling
  restart, it does not make every possible one safe regardless of duration. Four of the
  five services process a request synchronously within the HTTP request/response cycle
  itself (page-classification's multi-page PDF loop, alto-postprocess's per-file
  inference, translator's per-chunk LINDAT calls, llm-enrich's per-line LLM calls,
  nlp-enrich's own synchronous `/enrich`/`/enrich_text`/`/rescale`); a request that runs
  longer than the container's grace period is still forcibly cut when the kubelet
  `SIGKILL`s. Raise `terminationGracePeriodSeconds` **and** the Dockerfile's
  `--timeout-graceful-shutdown` together for a deployment expecting unusually large
  inputs — this manifest's defaults are a reasonable baseline, not a guarantee.
- **nlp-enrich's job queue is in-memory** (`service/jobs.py`). `serve_lifecycle`'s drain
  waits for a *tracked* job to finish before the process exits (issue #55 fixes the
  "job killed mid-flight" failure specifically), but a job's **record** does not survive a
  restart — a client polling `/jobs/{id}` after a rolling restart gets 404, not "completed
  during the restart that just happened." Durable job storage is out of scope for #55
  (tracked separately under #53's factors IV/VI); do not represent this manifest as making
  the job API safe to poll across a restart.
- **`replicas: 1` is the template default**, not a recommendation to stay at one. Raising it
  is safe for the four request/response services (translator, page-classification,
  alto-postprocess, llm-enrich) once ARÚP/ARÚB's own load-balancing is in place; nlp-enrich's
  in-memory job store means a client's poll can land on a *different* replica than the one
  running its job, which reads as 404 rather than "still running" — the same limitation as
  above, just visible sooner under >1 replica.
- **This manifest is a starting point, not a finished production spec.** It has no
  `NetworkPolicy`, no `PodDisruptionBudget`, no `HorizontalPodAutoscaler`, no image-pull
  secret for GHCR if the images are private, and no node-affinity/GPU scheduling for the
  services that benefit from a GPU. Those are ARÚP/ARÚB's own cluster's concerns and
  deliberately left out rather than guessed at.
- **alto-postprocess's lifespan raises on model-load failure**
  (`service/text_api.py:63-65`), so a misconfigured alto pod crash-loops on `startupProbe`
  rather than starting and reporting unready. This is correct, intentional behaviour (a
  service that cannot load its models should not silently sit "not ready" forever) — worth
  knowing so a crash-loop on this one service specifically is read as a config problem, not
  a regression in this manifest.
- **The reference manifest cannot deploy llm-enrich unmodified.** `service/api.py:128-134`
  raises at startup when `OPENROUTER_API_KEY` or `OPENROUTER_MODEL` is empty (and `:150`
  likewise for `OLLAMA_MODEL` on the ollama backend), so an llm-enrich pod applied straight
  from this template crash-loops on `startupProbe` — and it will look exactly like a probe
  defect in the acceptance runbook unless the key is supplied first. Create a `Secret` out of
  band and uncomment the `secretKeyRef` stanza. This is the one repo of the five where
  "substitute `<tool>` and `<version>`, then apply" is not the whole procedure (see "What to
  change per repo" below).

## What to change per repo

Replace `<tool>` and `<version>` in the manifest with the real image
(`ghcr.io/ufal/atrium-nlp-enrich:v1.2.0-api`, etc. — see `docker_gha.md` §3.1–3.2 for the
naming/tag-channel conventions), and size `resources.limits.memory` against the model(s) that
repo actually loads. Everything else in the manifest is identical across all five services —
that uniformity is the point: one reference contract, applied five times, rather than five
independently-negotiated deployment specs — **with one exception**: llm-enrich additionally
needs the `Secret` described in "Known limits" above before it will start at all.
