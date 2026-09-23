# syntax=docker/dockerfile:1.7
#
# ── ATRIUM tool-repo Dockerfile TEMPLATE ─────────────────────────────────────────────
#
# Reference shape for a tool repo's `Dockerfile`, alongside the other templates in this
# directory (`ruff.toml`, `env.example.template`, `k8s/`, `workflows/`, `skill/`).
#
# This is NOT a para-drift canonical file and is NOT vendored: every repo's Dockerfile
# differs in ways that matter (stage count, apt packages, torch index, model caches), so
# holding them byte-identical would be a lie. What IS held identical across all five is
# `shared/test_dockerfile_security_layer.py` (MANIFEST.json row 17), and that test runs
# against THIS FILE when the canonical copy is executed from the hub — via
# `hub-self-check.yml`'s "Run canonical shared-module tests" step, which runs
# `pytest .` with working-directory `docs/templates/shared`, where the test's
# `REPO_ROOT` resolves to `docs/templates/`.
#
# So this template is not documentation that drifts: the same five assertions that guard
# the five real Dockerfiles guard this one. If you change the security layer below in a
# way a tool repo could not copy, CI says so here first.
#
# Replace every <tool> placeholder. Stages beyond `base` and `api` (llm, remote, digital)
# are per-repo; see the real Dockerfiles for those.
#
# Related: docs/docker_gha.md · docs/k8s_deployment.md · atrium-project#53 (12-factor),
# #55 (HEALTHCHECK/SIGTERM), #58 ($PORT).

# Pinned by tag AND digest — see the note under the ENV block. Dependabot's `docker`
# ecosystem bumps the digest; refresh it by hand with
# `docker buildx imagetools inspect python:3.11-slim`.
FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9 AS base

# ── Provenance: build-time ARGs -> ENV, read by atrium_paradata.py ───────────────────
# CI passes ATRIUM_RUNNER_REF as `github.ref_name`. That makes this ENV layer unique per
# release tag, which the security layer below depends on — see the note there.
ARG ATRIUM_RUNNER_IMAGE=""
ARG ATRIUM_RUNNER_REPO="https://github.com/ufal/atrium-<tool>"
ARG ATRIUM_RUNNER_REF=""

ENV ATRIUM_RUNNER_IMAGE=${ATRIUM_RUNNER_IMAGE} \
    ATRIUM_RUNNER_REPO=${ATRIUM_RUNNER_REPO} \
    ATRIUM_RUNNER_REF=${ATRIUM_RUNNER_REF} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/cache/huggingface

# ── Base pin + distro security patches, applied at build time ─────────────────────────
# The base is pinned by DIGEST as well as tag. `python:3.11-slim` alone is a tag whose name
# never changes, and Dependabot only proposes an update when the reference in FROM would
# change, so even a configured `docker` ecosystem had nothing to bump. Pinned as
# `tag@sha256:…`, the `docker` entry in dependabot.example.yml opens a PR with the new
# digest whenever Docker Hub rebuilds the tag (its ignore rule holds the tag on 3.11).
#
# Before the pin the base layer was whatever Docker Hub last rebuilt, with nothing in this
# ecosystem bumping it (docker_gha_roadmap.md, H6). On 2026-09-13 that layer carried
# perl-base 5.40.1-6 with three FIXABLE CRITICAL CVEs — CVE-2026-13221, CVE-2026-42496 and
# CVE-2026-8376, all fixed in 5.40.1-6+deb13u1. The release gate in docker-tool.reusable.yml
# ("Fail the release on fixable CRITICAL vulnerabilities") blocks exactly that class, and
# because the promotion step is `if: success()`, a blocked release publishes by DIGEST
# ONLY: the `:<version>` and `:latest` tags are never applied.
#
# It cost two releases before the layer existed everywhere: translator v1.0.0-beta
# (2026-09-13, both targets) and nlp-enrich v0.20.2 (2026-09-15, run 34970419474, all
# three targets). The gate is `if: startsWith(github.ref, 'refs/tags/')`, so day-to-day
# `test` pushes never surface it — the failure appears only at a release.
#
# The digest pin does not replace the upgrade below: a pinned base is only as fresh as the
# last merged Dependabot PR, and the release gate blocks on fixable CRITICALs that Debian
# ships in between.
#
# `upgrade` rather than `install --only-upgrade <package>`, deliberately. The gate blocks
# on *fixable* CRITICALs — precisely those the distro already ships a patch for — so the
# fix that matches the gate's own definition is "apply the distro's available patches",
# not a package name that has to be edited by hand the next time a different one is
# announced.
#
# CACHE INTERACTION, which is what makes this hold rather than run once: the build uses
# `cache-from: type=gha`, so an apt layer high in the file would be served from cache
# forever and silently stop patching. It sits HERE, immediately after the ENV block that
# embeds ATRIUM_RUNNER_REF, because CI passes that as `github.ref_name` — a value unique
# to each release tag. The ENV layer therefore changes on every release, busting this
# layer with it, so every released image is scanned against a freshly patched base while
# day-to-day `test` pushes still hit the cache. Do not move this above the ENV block.
#
# One apt layer, not two: the upgrade and the install share a single `apt-get update`, so
# the package lists are fetched once and removed once. Add this repo's own build
# dependencies to the install list (build-essential, g++, libgl1, poppler-utils, git,
# wget — whatever it needs); ca-certificates is the common floor.
# Guarded by tests/test_dockerfile_security_layer.py (atrium-project#53).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Production image: install runtime requirements only. Do NOT install requirements-test.txt
# here — test dependencies enlarge the image and the Trivy surface that the release gate
# scans, for packages the service never imports.
COPY requirements.txt ./
COPY service/requirements.txt ./service/requirements.txt
RUN pip install -r requirements.txt -r service/requirements.txt

COPY . .

# Non-root runtime user owning only the caches and data mountpoint. /app stays root-owned
# to enforce source immutability. uid 10001 is fixed across the ecosystem so a
# `runAsUser` in the k8s manifest (docs/templates/k8s/) matches every image.
RUN useradd --create-home --uid 10001 atrium \
    && mkdir -p /cache/huggingface /data \
    && chown -R atrium:atrium /cache /data
USER atrium

# Batch entrypoint — the one-off/admin surface (12-factor XII). The API stage overrides it.
ENTRYPOINT ["python", "run_pipeline.py"]
CMD []


# ── API surface — published as :<version>-api ────────────────────────────────────────
FROM base AS api

USER root
COPY service/requirements.txt ./service_requirements.txt
RUN pip install -r service_requirements.txt
RUN chown -R atrium:atrium /app
USER atrium

# EXPOSE tracks the DEFAULT port: it is image metadata and cannot read $PORT at runtime.
# Set PORT to move the listener, and publish with `-p <port>:<port>` to match. (#58)
EXPOSE 8000

# STOPSIGNAL is the default (SIGTERM) — declared explicitly so it is never silently
# changed by a future edit; service/api.py's lifespan (via serve_lifecycle,
# service/atrium_service.py) chains to uvicorn's own handler for it. (#55)
STOPSIGNAL SIGTERM

# PORT and HOST are read by service/api.py's __main__ block; PORT is also the port
# service/healthcheck.py probes, which is why setting it used to make the container
# permanently unhealthy — the probe moved and the listener did not. Declared here so
# `docker inspect` is self-documenting and so the probe still has a value if the code
# default ever drifts. (#58)
#
# GRACEFUL_SHUTDOWN_S carries what used to be `--timeout-graceful-shutdown 20` on the
# ENTRYPOINT line. It bounds uvicorn's wait for in-flight HTTP requests. --start-period
# on HEALTHCHECK below covers first-run model downloads; see docs/docker_gha.md §3.4 and
# docs/k8s_deployment.md for the grace-period budget this is sized against. (#55)
ENV PORT=8000 GRACEFUL_SHUTDOWN_S=20

# `python -m service.api`, NOT `python service/api.py`: a script launch puts sys.path[0]
# at /app/service with no package context, so `from .atrium_service import ...` raises
# "attempted relative import with no known parent package" before the app is built. `-m`
# keeps sys.path[0] at /app — byte for byte the environment the old
# `uvicorn service.api:app` entrypoint ran in, so every repo-root import still resolves.
# (alto-postprocess is the documented exception: its service/text_api.py has no relative
# imports and is launched as a script.) (#58)
ENTRYPOINT ["python", "-m", "service.api"]
CMD []

# A /health endpoint a Kubernetes probe cannot see is not a health check. --start-period
# must cover the slowest cold start this image has (model download + load), or a rolling
# update kills the pod before it has ever been ready. (#55)
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD ["python", "/app/service/healthcheck.py"]
