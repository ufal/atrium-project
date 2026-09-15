#!/usr/bin/env bash
# Start the ATRIUM <Tool> API server and wait until it is READY (strategy Appendix C).
#
# Copy to scripts/server.sh (that exact name — every doc must reference the
# committed filename) and fill in every <placeholder>. Behavior contract:
#   1. Probe GET <base-url>/ready; answered 200 → exit 0 (idempotent).
#   2. Else start: docker compose (api profile) by default; --gpu adds the GPU
#      overlay where one exists; --local runs uvicorn in the repo's venv,
#      provisioning it with the repo's actual setup script first.
#   3. Poll /ready up to 15 min (first-run downloads); on timeout print where
#      the logs are and exit non-zero.
#
# Polls /ready, not /info (issue #55): /info answers 200 the moment the FastAPI
# process is up, whether or not model/backend warmup has finished, so a caller
# racing this script against a slow first-run download used to get a "healthy"
# server that 503s on its first real request. /ready is gated on the service's
# own warm-up flag (docs/templates/shared/atrium_service.py) specifically so
# this wait means "actually ready to serve", not just "a port is listening".
#
# Usage:
#   bash scripts/server.sh            # Docker, or local uvicorn fallback
#   bash scripts/server.sh --gpu     # <only if the repo has a GPU overlay>
#   bash scripts/server.sh --local    # skip Docker, run uvicorn directly
#
# Environment:
#   ATRIUM_<XX>_PORT  - port to serve on (default: 8000)
#   ATRIUM_<XX>_URL   - health-check target (default: http://localhost:$PORT)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${ATRIUM_<XX>_PORT:-8000}"
BASE_URL="${ATRIUM_<XX>_URL:-http://localhost:${PORT}}"
HEALTH_URL="${BASE_URL}/ready"
MODE="auto"

for arg in "$@"; do
    case "$arg" in
        --gpu)   MODE="gpu" ;;
        --local) MODE="local" ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ API already healthy at ${BASE_URL}"
    exit 0
fi

cd "$REPO_ROOT"

start_docker() {
    echo "🐳 Starting via docker compose ($*)..."
    docker compose "$@" --profile api up -d      # <or: docker compose up -d api>
}

# Resolve the GPU overlay flags at runtime instead of hardcoding an extension: three of
# the five ATRIUM repos use docker-compose.yml/.gpu.yml, two use .yaml/.gpu.yaml, and a
# copy of this template that assumes one extension silently fails --gpu in the other two
# (atrium-project docker_gha_roadmap.md B7). Never globs recursively, so a subdirectory
# compose file for an unrelated deployment (e.g. an annotation/ campaign stack) is never
# picked up here -- only the repo-root files this script itself cd'd into (see cd
# "$REPO_ROOT" above) are candidates.
gpu_compose_args() {
    # Populates the global GPU_COMPOSE_ARGS array in-process (not via a
    # < <(...) process substitution) so that the `exit 1` below actually stops
    # this script instead of only killing a subshell and silently falling
    # through to `docker compose up` with no -f flags at all.
    local base="" ext overlay
    for ext in yml yaml; do
        if [ -f "docker-compose.${ext}" ]; then
            base="docker-compose.${ext}"
            break
        fi
    done
    if [ -z "$base" ]; then
        echo "No docker-compose.yml or docker-compose.yaml at the repo root; cannot start." >&2
        exit 1
    fi
    overlay="docker-compose.gpu.${base##*.}"
    if [ ! -f "$overlay" ]; then
        echo "No GPU overlay (${overlay}) in this repo -- --gpu is not available here." >&2
        exit 1
    fi
    GPU_COMPOSE_ARGS=(-f "$base" -f "$overlay")
}

start_local() {
    echo "🐍 Starting local uvicorn server..."
    if [ ! -d "<venv-dir>" ]; then
        echo "No venv found - provisioning..."
        bash "<setup-script-or-inline-venv-provisioning>"
    fi
    # shellcheck disable=SC1091
    source "<venv-dir>/bin/activate"
    nohup uvicorn "service.<module>:app" --host 0.0.0.0 --port "$PORT" > api_server.log 2>&1 &
    echo "Server PID: $! (logs: api_server.log)"
}

case "$MODE" in
    gpu)
        gpu_compose_args
        start_docker "${GPU_COMPOSE_ARGS[@]}"
        ;;
    local) start_local ;;
    auto)
        if command -v docker > /dev/null 2>&1 && docker info > /dev/null 2>&1; then
            start_docker
        else
            start_local
        fi
        ;;
esac

echo "⏳ Waiting for ${HEALTH_URL} (<first-run downloads note> may take several minutes)..."
DEADLINE=$((SECONDS + 900))
until curl -sf "$HEALTH_URL" > /dev/null 2>&1; do
    if [ "$SECONDS" -ge "$DEADLINE" ]; then
        echo "❌ Server did not become healthy within 15 minutes." >&2
        echo "   Check: api_server.log (local) or 'docker compose --profile api logs' (Docker)." >&2
        exit 1
    fi
    sleep 5
done

echo "✅ API healthy at ${BASE_URL}"
