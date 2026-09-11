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

A fuller environment-variable reference across all five services is tracked separately in
atrium-project#60; this section covers only what the manifest itself exposes.


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

## What to change per repo

Replace `<tool>` and `<version>` in the manifest with the real image
(`ghcr.io/ufal/atrium-nlp-enrich:v1.2.0-api`, etc. — see `docker_gha.md` §3.1–3.2 for the
naming/tag-channel conventions), and size `resources.limits.memory` against the model(s) that
repo actually loads. Everything else in the manifest is identical across all five services —
that uniformity is the point: one reference contract, applied five times, rather than five
independently-negotiated deployment specs.
