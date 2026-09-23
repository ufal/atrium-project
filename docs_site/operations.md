---
title: Operations
nav_order: 11
status: partial
round: 6
issue: 57
---

# Operations

Build, ship and run the services: the images and their tags, the gate a release has to pass,
what the container proves before it is published, and how to run it on Kubernetes.

!!! info "Scope"
    The build and deployment machinery is shared by all five tools. The image, probe and
    environment details below are those of page-classification and the translator.

## The deployment model

ÚFAL **builds, gates and publishes** the container images; the partner institutions **run**
them, on their own infrastructure — typically Kubernetes — next to their own data. Nothing in
the hub's CI reaches into a partner's environment: what crosses the boundary is a published
image, pulled by tag, plus the configuration each deployment sets through environment
variables. Every tool therefore behaves the same way wherever it runs, and every
deployment-specific value — endpoints, limits, allowed origins — is an environment variable
with a documented default.

## Images and tags

Every tool builds **two images from one Dockerfile** — a batch image from the `base` stage and an
HTTP-service image from the `api` stage — and publishes them to GitHub's container registry.

|                     | Batch CLI (`base` stage)                  | HTTP service (`api` stage)                    |
|---------------------|-------------------------------------------|-----------------------------------------------|
| page-classification | `ghcr.io/ufal/atrium-page-classification` | `ghcr.io/ufal/atrium-page-classification-api` |
| translator          | `ghcr.io/ufal/atrium-translator`          | `ghcr.io/ufal/atrium-translator-api`          |

The `-api` suffix is part of the **image name**, not the tag: the hub's build workflow appends
`-<stage>` to the image name for every stage except `base`.

**Which tags exist, and when they move:**

| Tag                            | Published when                                                                                              |
|--------------------------------|-------------------------------------------------------------------------------------------------------------|
| `sha-<short>`                  | every publishing build — immutable, the audit trail                                                         |
| `<version>`, e.g. `1.8.0-beta` | a `v*` git tag, **after** the release gate passes. The leading `v` is stripped                              |
| `latest`                       | the same moment, the same condition. `-beta` versions count, so `latest` is the newest release, beta or not |
| `test`                         | a push to the `test` branch — the moving pre-release channel the end-to-end tests can run against           |

**A push to `vit` or `master` publishes nothing.** Only a push to `test`, a version tag, or a
published GitHub release triggers the build-and-push job.

So a service image is always `atrium-<tool>-api:<version>`, and a batch image
`atrium-<tool>:<version>`:

```bash
docker pull ghcr.io/ufal/atrium-page-classification-api:<version>
docker pull ghcr.io/ufal/atrium-translator-api:latest
```

### Running the batch image

The batch images read from `/data/input` by default, so one mounted directory is enough:

```bash
# classify every page image under ./data/input; result tables land in ./data/output
docker run --rm -v "$PWD/data:/data" -v "$PWD/data/output:/app/result" \
    ghcr.io/ufal/atrium-page-classification:<version>

# translate every ALTO file under ./data/input into ./data/output
docker run --rm -v "$PWD/data:/data" ghcr.io/ufal/atrium-translator:<version>
```

Arguments after the image name replace the defaults listed below — any `run.py` or
`main.py` flag works. Add `-v hf-cache:/cache/huggingface` to keep downloaded models between
runs.

### What is inside each image

=== "page-classification"

    |                     | `base`                                                                                                            | `api`                                                                          |
    |---------------------|-------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
    | From                | `python:3.11-slim`                                                                                                | `base`                                                                         |
    | System packages     | `build-essential`, `g++`, `libgl1`, `libglib2.0-0`, `ca-certificates`                                             | —                                                                              |
    | PyTorch             | `torch==2.7.1`, `torchvision==0.22.1` from `TORCH_INDEX_URL` (CPU wheels by default; pass `…/whl/cu126` for CUDA) | —                                                                              |
    | Python requirements | `setup/requirements.txt`, `service/requirements.txt` and `setup/requirements-test.txt`                            | —                                                                              |
    | User                | `atrium`, uid **10001**, owning `/app`, `/cache`, `/data`                                                         | same                                                                           |
    | Entry point         | `python3 /app/entrypoint.py` — a GPU probe that `exec`s `run.py`, so the process receives signals directly        | `python -m service.api`                                                        |
    | Default arguments   | `-d /data/input --hf -rev <revision>` — classify `/data/input` with a published model                             | —                                                                              |
    | Port, signal, drain | —                                                                                                                 | `EXPOSE 8000` · `STOPSIGNAL SIGTERM` · `GRACEFUL_SHUTDOWN_S=20`                |
    | Healthcheck         | —                                                                                                                 | `python /app/service/healthcheck.py` every 30 s, 180 s start period, 3 retries |

=== "translator"

    |                     | `base`                                                                                                                                 | `api`                                                           |
    |---------------------|----------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
    | From                | `python:3.11-slim`                                                                                                                     | `base`                                                          |
    | System packages     | security upgrades only                                                                                                                 | —                                                               |
    | Python requirements | `requirements.txt`, `service/requirements.txt`                                                                                         | —                                                               |
    | User                | `atrium`, uid **10001**, owning `/cache` and `/data` only — `/app` stays root-owned on purpose, so the source is immutable at run time | same                                                            |
    | Entry point         | `python main.py`                                                                                                                       | `python -m service.api`                                         |
    | Default arguments   | `/data/input --alto --formats alto.xml --target_lang en -o /data/output`                                                               | —                                                               |
    | Port, signal, drain | —                                                                                                                                      | `EXPOSE 8000` · `STOPSIGNAL SIGTERM` · `GRACEFUL_SHUTDOWN_S=20` |
    | Healthcheck         | —                                                                                                                                      | the same `healthcheck.py`, same timings                         |

Both set `HF_HOME=/cache/huggingface`, so a mounted volume there keeps downloaded models across
container restarts.

## The release gate

A version tag does not publish an image directly. The build pushes it **by digest only**, scans it,
and promotes the version and `latest` tags afterwards — only if the scan allows:

1. Build and push, tagged `sha-<short>` only, with **SBOM and provenance attestations** attached
   (BuildKit's own; inspect them with `docker buildx imagetools inspect`).
2. Trivy scans the pushed digest for fixable CRITICAL and HIGH vulnerabilities and uploads the
   result to GitHub code scanning. This scan reports; it does not fail.
3. **On a tag only**, a second Trivy pass fails the job on any *fixable CRITICAL* vulnerability.
4. Only then are `<version>` and `latest` applied to the digest.

**A release blocked at step 3 still exists** — as `sha-<short>`, by digest, with its attestations and
scan results — but with no version tag and no `latest`. Nothing that pulls by tag sees it. This is
what happened to the translator's `v1.0.0-beta` in September 2026: the floating `python:3.11-slim`
base carried three fixable CRITICAL CVEs in `perl-base`, and the gate held the release back until a
rebuilt image passed. The story is told in full on
[translator → History](tools/translator/history.md#the-base-image-that-blocked-a-release).

The same incident produced the rule every Dockerfile follows and a vendored test enforces: the
`apt-get upgrade` layer must sit **below** the `ENV` line that embeds `ATRIUM_RUNNER_REF` (unique
per release tag, so it busts the layer cache on every release) and **above** `USER atrium`. With
the build cache enabled, an upgrade layer in the wrong place is served from cache, looks correct,
and patches nothing.

## What the container proves before it is published

On every pull request, every push to `test` and every version tag, the hub's build workflow starts
the `api` image and checks it from the outside:

| Check                       | Passes when                                                                                                                             |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| It becomes healthy          | Docker's own `HEALTHCHECK` reports `healthy` within 330 s                                                                               |
| It serves                   | `GET /health` answers over the published port; the `/ready` status is logged                                                            |
| It logs in the agreed shape | at least one record in the shared log format reaches stdout                                                                             |
| It stops cleanly            | `docker stop --time 30` completes inside 30 s and the exit code is `143` or `0`                                                         |
| It honours `PORT`           | started with `PORT=9000`, it becomes healthy on 9000                                                                                    |
| It honours `HOST`           | started with `HOST=127.0.0.1`, the published port must **not** answer — the container is healthy and unreachable, exactly as configured |
| It honours `LOG_LEVEL`      | started with `LOG_LEVEL=WARNING`, no INFO record appears                                                                                |

**Exit code 143 is a clean stop.** It is 128 + SIGTERM: the service caught the signal, drained and
exited. Compose and Kubernetes both display it as a non-zero exit; it is the expected value.

## Running on Kubernetes

The hub ships one reference manifest for all five services,
`docs/templates/k8s/atrium-service.deployment.yaml`; `docs/k8s_deployment.md` is the full guide.
What matters for these two services:

### Probes — three endpoints, on purpose

| Probe            | Path      | Timing                              | Why this path                                                                   |
|------------------|-----------|-------------------------------------|---------------------------------------------------------------------------------|
| `startupProbe`   | `/ready`  | every 5 s, up to 60 failures        | up to five minutes for a first-run model download before the other probes start |
| `readinessProbe` | `/ready`  | every 5 s, 2 failures, 3 s timeout  | takes a draining pod out of the Service without restarting it                   |
| `livenessProbe`  | `/health` | every 15 s, 3 failures, 5 s timeout | restarts the pod only if the process itself is wedged                           |

`/health?deep=true` is deliberately not wired to any probe: a degraded dependency is a reason to
look, not to restart.

### Shutdown, and the grace period

On `SIGTERM` the pod runs `preStop: sleep 5` (time for the endpoint removal to propagate), the
service flips `/ready` to 503 and refuses new work with 503, uvicorn drains for
`GRACEFUL_SHUTDOWN_S` (20 s), and the shared lifecycle waits up to 25 s more for in-flight work.
**5 + 20 + 25 = 50 s**, inside the manifest's `terminationGracePeriodSeconds: 60`.

A single request longer than that chain is cut — for these two services, a 50-page PDF through the
classifier, or a large ALTO file through the translator's per-chunk LINDAT calls. Raise
`GRACEFUL_SHUTDOWN_S` and `terminationGracePeriodSeconds` together.

### Sizing, storage and egress

=== "page-classification"

    * **Memory.** The service warms all five ensemble models at start — about **2.44 GB of
      weights** (`v1.4`–`v5.4`, from 213 MB to 1.21 GB each). The template's `limits.memory: 4Gi` is
      a floor, not a comfortable fit.
    * **Storage.** Weights are saved under `/app/model`. Compose mounts a `page-model` volume
      there; on Kubernetes, mount a volume at `/app/model` as well as the `/cache/huggingface`
      one, or every new pod downloads the weights again.
    * **Egress.** `huggingface.co` only — the `ufal/vit-historical-page` revisions and the base
      model configurations. No LINDAT call.
    * **Limits.** `MAX_UPLOAD_MB` defaults to **10**; a PDF is further capped at **50 pages**, which is
      hard-coded rather than configurable.

=== "translator"

    * **Memory.** Light — one FastText language-identification model. The work is remote.
    * **Egress.** The LINDAT translation API, **one retried call per text chunk** (4,000 characters);
      `huggingface.co` once at start for FastText; LINDAT's UDPipe only when a vocabulary is loaded;
      `LLM_BASE_URL` when the `openai_compatible` backend is selected. In an egress-restricted
      cluster, expect `/ready` to answer 200 while `/health?deep=true` reports the FastText download
      failure.
    * **Limits.** `MAX_UPLOAD_MB` defaults to **50**, because ALTO goes in and ALTO comes out;
      set it explicitly when deploying from the shared template, whose example value is lower.

Both services are stateless per request — each works inside its own temporary directory — so
raising `replicas` is safe. Each page-classification replica loads its own copy of the five models.

### Environment

Beyond the variables every service shares — `PORT`, `HOST`, `GRACEFUL_SHUTDOWN_S`,
`ALLOWED_ORIGINS`, `MAX_UPLOAD_MB`, `LOG_LEVEL` — **page-classification reads none**: its service
layer is configured entirely by those. The translator reads:

| Variable                                                                 | Default              | Effect                                                                                     |
|--------------------------------------------------------------------------|----------------------|--------------------------------------------------------------------------------------------|
| `TRANSLATION_BACKEND`                                                    | `lindat`             | `lindat` (CUBBITT), `openai_compatible` or `ct2`                                           |
| `TRANSLATION_URL`                                                        | LINDAT's public host | attach a self-hosted translation service; `LINDAT_BASE_URL` is accepted as an alias        |
| `UDPIPE_URL`                                                             | LINDAT's public host | lemma matching for the vocabulary                                                          |
| `LINDAT_MIN_INTERVAL_S` / `LINDAT_MAX_RETRIES` / `LINDAT_BACKOFF_BASE_S` | `0.0` / `4` / `1.0`  | rate-limits this deployment against a shared public service                                |
| `OUTPUT_MODE`                                                            | `replace`            | the default `replace` / `append` mode for `/translate`                                     |
| `AMCR_FIELDS_PATH`                                                       | `amcr-fields.txt`    | the XPath targets for metadata mode — unreadable means a 422                               |
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`                               | —                    | required by `openai_compatible`; the key belongs in a Secret                               |
| `CT2_MODEL_DIR`, `CT2_MODEL_FAMILY`, `CT2_DEVICE`, …                     | —                    | required by `ct2`; see [translator → Reference](tools/translator/reference.md#environment) |

Three settings behave in ways worth knowing before the first deployment:

* `ALLOWED_ORIGINS` **unset** means `*`; set to the **empty string**, it allows no origin at all.
  page-classification's compose file narrows it to `http://localhost:8080,http://127.0.0.1:8080`;
  the translator's does not narrow it.
* `HOST=127.0.0.1` produces a pod that is healthy and unreachable: the healthcheck probes
  `127.0.0.1` from inside and never reads `HOST`.
* An **empty** `PORT`, `GRACEFUL_SHUTDOWN_S` or `LOG_LEVEL` fails at start-up rather than falling
  back to the default.

### What the health endpoints report

|                     | page-classification               | translator                                                                                    |
|---------------------|-----------------------------------|-----------------------------------------------------------------------------------------------|
| `/health`           | 200 while the process lives       | 200 while the process lives                                                                   |
| `/health?deep=true` | 503 while draining                | 503 when the backend is not warmed, when the FastText model failed to load, or while draining |
| `/ready`            | 200 once the five models are warm | 200 once the backend is warm                                                                  |

Warm-up happens before the service accepts connections, so a client waiting for a service to
come up should treat a refused connection the same as `503 starting`, and keep polling.

## Acceptance

Two hub runbooks define "it works", and both apply to these services unchanged:

**On Kubernetes** (`docs/k8s_acceptance_runbook.md`): apply the manifest with the tool name and
version substituted; wait for the rollout; confirm `healthcheck.py` passes inside the pod; then,
with a slow request in flight, restart the deployment and confirm **the request completes** — no
in-flight request may be dropped. The slowest request shape for each: a multi-page PDF to
`POST /predict_document`, and a large ALTO file to `POST /translate`. Then prove the configuration
reaches the process: `PORT=9000`, `LOG_LEVEL=DEBUG`, an `ALLOWED_ORIGINS` value that is honoured and
one that is refused, and `MAX_UPLOAD_MB=1` answering a 2 MB upload with 413.

**As a skill** (`docs/skill_acceptance_runbook.md`): clone the `agent-skill` branch, start the
server, check `/info`, `/health` and `/health?deep=true`, run the client on the branch's sample
files — `small_data_samples/TEXT/atrium-01.png` for the classifier,
`small_data_samples/MTX201501307_anon.alto.xml` for the translator — and finally hand a fresh agent
session only the task, with no instructions, and see it succeed. See [Agent skills](agent-skills.md).

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                                                                            | What was taken from it                                        |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| `atrium-project/.github/workflows/docker-tool.reusable.yml`                                                                                                                       | image names, tag rules, the gate, the container smoke         |
| `atrium-page-classification@vit` `adee922` and `atrium-translator@master` `71feaef` — `Dockerfile`, `docker-compose*.yml`, `docker.yml`, `service/api.py`, `service/inference.py` | image contents, defaults, limits, health checks, weights path |
| `atrium-project/docs/templates/k8s/atrium-service.deployment.yaml`                                                                                                                | probes, grace period, resources                               |
| `atrium-project/docs/k8s_deployment.md`, `docs/k8s_acceptance_runbook.md`, `docs/skill_acceptance_runbook.md`                                                                     | the deployment guide and the acceptance procedures            |
| `atrium-project/docs/templates/shared/atrium_service.py`, `healthcheck.py`                                                                                                        | the shared lifecycle and probe                                |
| `atrium-page-classification/model_registry.py`                                                                                                                                    | the checkpoint sizes behind the memory figure                 |
