"""test_atrium_service.py — unit tests for the canonical service meta-contract (issue #55).

Canonical copy lives in the hub at ``docs/templates/shared/`` and is run in place by
``hub-self-check.yml``'s ``shared-tests`` job (``working-directory:
docs/templates/shared``), which is also why this file is **not** vendored into the five
tool repos: `scripts/revendor_shared.sh`'s ``SHARED_FILES`` manifest deliberately excludes
it, since each repo already exercises ``atrium_service.py`` indirectly through its own
``tests/test_api_contract.py``. This is the first test any of the hub's four canonical
shared modules (`atrium_document.py`, `atrium_paradata.py`, `atrium_service.py`,
`check_version.py`) has had — see `docs/docker_gha_roadmap.md` finding **E9**.

Every behavioural claim in ``atrium_service.py``'s new (issue #55) surface is covered here:
readiness before/after warmup and during drain, liveness staying 200 throughout, the deep
health precedence rules, in-flight request counting, tracked-task draining and its timeout
path, and — the load-bearing detail — that the installed signal handler CHAINS TO rather
than replaces whatever was previously registered. The full signal-delivery path (a real
``SIGTERM`` sent to a real uvicorn subprocess) cannot be exercised inside a single-process
pytest run without either forking or terminating the test process itself, so that end of
the contract was instead verified once, manually, against a live uvicorn 0.52 subprocess
(recorded in this issue's strategy write-up) — what is unit-tested here is everything up to
and including calling the captured "previous handler", which is the part a refactor could
silently break.
"""

from __future__ import annotations

import asyncio
import signal
import threading

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from atrium_service import (  # noqa: E402
    ServiceState,
    attach_health,
    attach_inflight_middleware,
    serve_lifecycle,
)

# ---------------------------------------------------------------------------------------
# attach_health — backward compatibility (no ServiceState): must be byte-identical to the
# pre-#55 behaviour, since five repos' test_health_shallow_ok and
# skill-validate.reusable.yml's live probe all assert against exactly this shape.
# ---------------------------------------------------------------------------------------


def test_health_without_state_is_unchanged():
    app = FastAPI()
    attach_health(app)
    client = TestClient(app)

    shallow = client.get("/health")
    assert shallow.status_code == 200
    assert shallow.json() == {"status": "ok"}

    deep = client.get("/health?deep=true")
    assert deep.status_code == 200
    assert deep.json() == {"status": "ok"}


def test_health_without_state_still_honours_deep_check():
    app = FastAPI()
    attach_health(app, deep_check=lambda: "backend cold")
    client = TestClient(app)

    deep = client.get("/health?deep=true")
    assert deep.status_code == 503
    assert deep.json() == {"status": "degraded", "detail": "backend cold"}
    # shallow is unaffected by a failing deep_check
    assert client.get("/health").status_code == 200


def test_no_state_means_no_ready_route():
    app = FastAPI()
    attach_health(app)
    client = TestClient(app)
    assert client.get("/ready").status_code == 404


def test_deep_check_that_raises_is_reported_degraded_not_500():
    app = FastAPI()

    def _boom():
        raise RuntimeError("boom")

    attach_health(app, deep_check=_boom)
    client = TestClient(app)
    response = client.get("/health?deep=true")
    assert response.status_code == 503
    assert "deep health check raised: boom" in response.json()["detail"]


# ---------------------------------------------------------------------------------------
# /ready and the draining semantics of /health?deep=true
# ---------------------------------------------------------------------------------------


def test_readiness_flips_warm_then_draining():
    app = FastAPI()
    state = ServiceState()
    attach_health(app, state=state)
    client = TestClient(app)

    not_warm = client.get("/ready")
    assert not_warm.status_code == 503
    assert not_warm.json()["status"] == "starting"

    state.warm = True
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    state.draining = True
    draining = client.get("/ready")
    assert draining.status_code == 503
    assert draining.json()["status"] == "draining"


def test_liveness_stays_200_while_draining():
    """The single most important assertion in this file: a liveness probe that fails
    during a graceful shutdown causes the orchestrator to SIGKILL the pod before the
    drain finishes, which defeats the entire point of issue #55."""
    app = FastAPI()
    state = ServiceState()
    state.warm = True
    state.draining = True
    attach_health(app, state=state)
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_deep_health_reports_draining_with_operator_fields():
    app = FastAPI()
    state = ServiceState()
    state.warm = True
    state.draining = True
    state.in_flight = 3
    attach_health(app, state=state)
    client = TestClient(app)

    response = client.get("/health?deep=true")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["detail"] == "shutting down"
    assert body["draining"] is True
    assert body["in_flight"] == 3


def test_draining_takes_precedence_over_a_passing_deep_check():
    app = FastAPI()
    state = ServiceState()
    state.warm = True
    state.draining = True
    attach_health(app, deep_check=lambda: None, state=state)  # deep_check says "healthy"
    client = TestClient(app)

    response = client.get("/health?deep=true")
    assert response.status_code == 503
    assert response.json()["detail"] == "shutting down"


def test_deep_health_with_state_but_not_draining_still_runs_deep_check():
    app = FastAPI()
    state = ServiceState()
    state.warm = True
    attach_health(app, deep_check=lambda: "backend cold", state=state)
    client = TestClient(app)

    response = client.get("/health?deep=true")
    assert response.status_code == 503
    body = response.json()
    assert body["detail"] == "backend cold"
    assert body["draining"] is False


# ---------------------------------------------------------------------------------------
# attach_inflight_middleware
# ---------------------------------------------------------------------------------------


def test_inflight_middleware_counts_concurrent_requests():
    app = FastAPI()
    state = ServiceState()
    attach_inflight_middleware(app, state)
    release = threading.Event()
    seen_inflight = {}

    @app.get("/slow")
    def slow():
        seen_inflight["during"] = state.in_flight
        release.wait(timeout=2)
        return {"ok": True}

    client = TestClient(app)
    # TestClient's default pool runs the request synchronously on a worker thread; start
    # it in a background thread so this test can observe the counter mid-request.
    import threading as _threading

    holder = {}

    def _do_request():
        holder["response"] = client.get("/slow")

    thread = _threading.Thread(target=_do_request)
    thread.start()
    try:
        for _ in range(200):  # poll rather than sleep a fixed guess
            if "during" in seen_inflight:
                break
            import time

            time.sleep(0.01)
        assert seen_inflight.get("during") == 1
    finally:
        release.set()
        thread.join(timeout=2)

    assert holder["response"].status_code == 200
    assert state.in_flight == 0


# ---------------------------------------------------------------------------------------
# ServiceState.track / wait_drained
# ---------------------------------------------------------------------------------------


def test_track_and_wait_drained_waits_for_detached_work():
    async def _run():
        state = ServiceState()
        finished = {"v": False}

        async def _bg():
            await asyncio.sleep(0.1)
            finished["v"] = True

        state.track(_bg())
        drained = await state.wait_drained(timeout=1.0)
        assert drained is True
        assert finished["v"] is True

    asyncio.run(_run())


def test_wait_drained_reports_false_on_timeout():
    async def _run():
        state = ServiceState()

        async def _slow_bg():
            await asyncio.sleep(2.0)

        task = state.track(_slow_bg())
        drained = await state.wait_drained(timeout=0.05)
        assert drained is False
        task.cancel()  # avoid an "unretrieved exception" warning after the test process exits
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(_run())


def test_wait_drained_is_immediate_noop_with_nothing_tracked():
    async def _run():
        state = ServiceState()
        import time

        start = time.monotonic()
        drained = await state.wait_drained(timeout=5.0)
        elapsed = time.monotonic() - start
        assert drained is True
        assert elapsed < 0.5, "a service with nothing to drain must not wait out the budget"

    asyncio.run(_run())


# ---------------------------------------------------------------------------------------
# serve_lifecycle — the load-bearing signal-chaining contract
# ---------------------------------------------------------------------------------------


def test_serve_lifecycle_chains_to_previous_handler_rather_than_replacing_it():
    """Pins the exact failure mode a careless rewrite could reintroduce: installing a
    handler that does not call through to whatever was there before (e.g. uvicorn's own
    Server.handle_exit) silently breaks graceful shutdown, because uvicorn never learns
    that should_exit ought to become True."""

    async def _run():
        state = ServiceState()
        previous_handler_called_with = []

        def _fake_previous_handler(signum, frame):
            previous_handler_called_with.append(signum)

        original = signal.signal(signal.SIGTERM, _fake_previous_handler)
        try:
            async with serve_lifecycle(state, drain_timeout=1.0):
                # By now serve_lifecycle has installed its own handler and captured
                # _fake_previous_handler as "previous". Simulate the OS delivering
                # SIGTERM by invoking the currently-installed handler directly — this
                # test must not send a real signal to the pytest process itself.
                current_handler = signal.getsignal(signal.SIGTERM)
                assert current_handler is not _fake_previous_handler, (
                    "serve_lifecycle must install its own handler, not leave the previous one in place unwrapped"
                )
                current_handler(signal.SIGTERM, None)
                assert state.draining is True
                assert previous_handler_called_with == [signal.SIGTERM], (
                    "the previously-registered handler was not called — this is exactly "
                    "the bug that would break uvicorn's own graceful shutdown, since "
                    "uvicorn would never observe should_exit=True"
                )
        finally:
            signal.signal(signal.SIGTERM, original)

    asyncio.run(_run())


def test_serve_lifecycle_restores_the_original_handler_on_exit():
    async def _run():
        state = ServiceState()

        def _sentinel(signum, frame):
            pass

        original = signal.signal(signal.SIGTERM, _sentinel)
        try:
            async with serve_lifecycle(state, drain_timeout=1.0):
                assert signal.getsignal(signal.SIGTERM) is not _sentinel
            assert signal.getsignal(signal.SIGTERM) is _sentinel, (
                "serve_lifecycle must restore whatever was registered before it, so a "
                "non-uvicorn caller (e.g. this test) is not left with a leaked handler"
            )
        finally:
            signal.signal(signal.SIGTERM, original)

    asyncio.run(_run())


def test_serve_lifecycle_waits_for_tracked_work_before_the_wrapped_block_returns():
    async def _run():
        state = ServiceState()
        finished_before_exit = {"v": None}

        async def _bg():
            await asyncio.sleep(0.1)
            finished_before_exit["v"] = True

        async with serve_lifecycle(state, drain_timeout=1.0):
            state.track(_bg())
            # the body of the `async with` returns immediately; the wait happens in
            # serve_lifecycle's own __aexit__, driven by the "yield" below completing —
            # nothing to assert here, this block only sets up the tracked task.

        assert finished_before_exit["v"] is True, (
            "serve_lifecycle's exit must await tracked work before letting shutdown "
            "proceed — this is the mechanism that prevents issue #55's 'a rolling "
            "restart kills in-flight work' for detached jobs"
        )

    asyncio.run(_run())


def test_serve_lifecycle_is_a_noop_wrapper_off_the_main_thread():
    """serve_lifecycle must not attempt signal.signal() off the main thread (it would
    raise ValueError) — mirrors uvicorn's own capture_signals() guard, and is what keeps
    this safe to use under TestClient/pytest worker threads."""
    errors = []

    def _worker():
        async def _run():
            state = ServiceState()
            try:
                async with serve_lifecycle(state, drain_timeout=0.5):
                    pass
            except Exception as exc:  # pragma: no cover - failure path only
                errors.append(exc)

        asyncio.run(_run())

    thread = threading.Thread(target=_worker)
    thread.start()
    thread.join(timeout=5)
    assert not errors, f"serve_lifecycle raised off the main thread: {errors}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
