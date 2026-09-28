"""tests/test_atrium_service.py — unit tests for the canonical service meta-contract (issue #55).

Lives in the hub's own ``tests/`` (moved here from ``docs/templates/shared/`` by
atrium-project#59) and is run by the ordinary ``pytest tests/`` invocation in
``hub-self-check.yml``'s ``shared-tests`` job — no separate working-directory step
needed any more. It is **not** vendored into the five tool repos, and never was:
``docs/templates/shared/MANIFEST.json`` — the single list `scripts/revendor_shared.sh`,
`tools/skill_drift_check.py` and `para-drift.reusable.yml` all read (atrium-project#59)
— has no entry for it, since each tool repo already exercises ``atrium_service.py``
indirectly through its own ``tests/test_api_contract.py``. Before #59, that exclusion
was merely implicit (nothing enumerated this file at all, canonical or not — a
registered-nowhere state two other issues' plans flagged as an orphan); now it is a
file that lives outside the vendored directory entirely, which is the more honest
shape for something meant to be hub-only from the start. This is the first test any
of the hub's four canonical shared modules (`atrium_document.py`, `atrium_paradata.py`,
`atrium_service.py`, `check_version.py`) has had — see `docs/docker_gha_roadmap.md`
finding **E9**.

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
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# atrium_service.py is the canonical copy under docs/templates/shared/, not a hub-root
# module -- this file used to sit BESIDE it (before #59 moved this test into tests/),
# which is how a bare `from atrium_service import ...` resolved with no path setup at
# all. Same pattern tests/test_workflow_lint.py already uses for tools/ci/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docs" / "templates" / "shared"))

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


# ---------------------------------------------------------------------------------------
# atrium-project#53 (factor III) + #32 item 2: the harmonised error body, the limits
# contract in /info, and the bounded readers. These are generation-1 additions: opt-in,
# so every existing caller of build_info()/add_cors() is unchanged. The one deliberate
# behaviour change is resolve_max_upload_mb(): a malformed value now fails at startup,
# naming the variable, where it used to be ignored silently.
# ---------------------------------------------------------------------------------------

from fastapi import File, HTTPException, Request, UploadFile  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import atrium_limits  # noqa: E402  (same docs/templates/shared/ path as atrium_service)
from atrium_service import (  # noqa: E402
    REASON_CODES,
    AtriumHTTPError,
    add_cors,
    attach_error_handlers,
    build_info,
    busy,
    check_body_size,
    error_body,
    read_upload_bounded,
    resolve_max_upload_mb,
)


def _limit_env(suffix: str) -> str:
    return "_".join(("ATRIUM", "SERVICE", "TEST", suffix))


class _Body(BaseModel):
    n: int


def _error_app() -> FastAPI:
    app = FastAPI()
    attach_error_handlers(app)
    pages = atrium_limits.limit(_limit_env("PAGES"), 3, unit="pages", key="max_test_pages")

    @app.get("/plain")
    def plain():
        raise HTTPException(status_code=422, detail="Filename has no usable document id.")

    @app.get("/structured")
    def structured():
        raise HTTPException(status_code=400, detail={"why": "structured"})

    @app.get("/busy")
    def is_busy():
        raise busy(retry_after_s=7)

    @app.get("/pages/{n}")
    def over_pages(n: int):
        pages.check(n, detail=f"The PDF has {n} pages; the limit is {pages.get()} (MAX_TEST_PAGES).")
        return {"ok": True}

    @app.get("/timeout")
    def timed_out():
        spec = atrium_limits.limit(_limit_env("TIMEOUT"), 600, unit="s", status=504)
        raise spec.exceeded(None, detail="Pipeline execution timed out.")

    @app.post("/validated")
    def validated(body: _Body):
        return body

    @app.post("/sized")
    async def sized(request: Request):
        await check_body_size(request, 0.001, label="Body")
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("an unexpected failure")

    return app


def test_error_body_rejects_an_unregistered_reason():
    assert error_body(413, "x", "limit_exceeded") == {"status": 413, "reason": "limit_exceeded", "detail": "x"}
    with pytest.raises(ValueError):
        error_body(400, "x", "made_up")
    with pytest.raises(ValueError):
        AtriumHTTPError(400, "x", reason="made_up")
    assert set(REASON_CODES) >= {"limit_exceeded", "busy"}


def test_every_http_error_gets_the_envelope_with_its_detail_string_unchanged():
    client = TestClient(_error_app())
    r = client.get("/plain")
    assert r.status_code == 422
    assert r.json() == {"status": 422, "reason": None, "detail": "Filename has no usable document id."}
    r = client.get("/structured")
    assert r.json() == {"status": 400, "reason": None, "detail": "Bad Request", "errors": {"why": "structured"}}


def test_router_404_and_405_are_wrapped_too():
    client = TestClient(_error_app())
    r = client.get("/no-such-route")
    assert r.status_code == 404 and r.json() == {"status": 404, "reason": None, "detail": "Not Found"}
    r = client.post("/plain")
    assert r.status_code == 405 and r.json()["reason"] is None and r.json()["status"] == 405


def test_busy_is_429_with_retry_after():
    r = TestClient(_error_app()).get("/busy")
    assert r.status_code == 429
    assert r.headers["retry-after"] == "7"
    assert r.json()["reason"] == "busy"


def test_limit_exceeded_carries_its_status_and_the_limit(monkeypatch):
    monkeypatch.delenv(_limit_env("PAGES"), raising=False)
    client = TestClient(_error_app())
    assert client.get("/pages/3").status_code == 200
    r = client.get("/pages/4")
    assert r.status_code == 413
    assert r.json() == {
        "status": 413,
        "reason": "limit_exceeded",
        "detail": "The PDF has 4 pages; the limit is 3 (MAX_TEST_PAGES).",
        "limit": {"key": "max_test_pages", "env": _limit_env("PAGES"), "value": 3, "observed": 4, "unit": "pages"},
    }
    r = client.get("/timeout")
    assert r.status_code == 504 and r.json()["reason"] == "limit_exceeded"
    assert r.json()["limit"]["observed"] is None


def test_validation_errors_keep_a_string_detail_and_list_the_problems():
    r = TestClient(_error_app()).post("/validated", json={"n": "not a number"})
    assert r.status_code == 422
    body = r.json()
    assert body["reason"] is None and isinstance(body["detail"], str)
    assert body["detail"].startswith("Request validation failed: n:")
    assert isinstance(body["errors"], list) and body["errors"][0]["loc"][-1] == "n"


def test_check_body_size_refuses_an_oversized_json_body():
    client = TestClient(_error_app())
    assert client.post("/sized", content=b"{}").status_code == 200
    r = client.post("/sized", content=b"x" * 5000)
    assert r.status_code == 413 and r.json()["limit"]["key"] == "max_upload_mb"
    assert r.json()["detail"] == "Body too large: over 0.001 MB (MAX_UPLOAD_MB)."


def test_uncaught_exception_is_a_json_500():
    r = TestClient(_error_app(), raise_server_exceptions=False).get("/boom")
    assert r.status_code == 500
    assert r.json() == {"status": 500, "reason": None, "detail": "Internal server error."}


def test_read_upload_bounded_refuses_past_the_limit():
    app = FastAPI()
    attach_error_handlers(app)

    @app.post("/up")
    async def up(file: UploadFile = File(...)):
        data = await read_upload_bounded(file, 1.0, label="File")
        return {"size": len(data)}

    client = TestClient(app)
    exact = b"a" * (1024 * 1024)
    assert client.post("/up", files={"file": ("a.bin", exact)}).json() == {"size": len(exact)}
    r = client.post("/up", files={"file": ("a.bin", exact + b"b")})
    assert r.status_code == 413
    assert r.json()["detail"] == "File too large: over 1 MB (MAX_UPLOAD_MB)."
    assert r.json()["limit"]["observed"] == 1.0


def test_build_info_accepts_a_limit_set_and_adds_limits_meta(monkeypatch):
    monkeypatch.delenv("MAX_UPLOAD_MB", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_BYTES", raising=False)
    monkeypatch.setenv(_limit_env("DPI"), "150")
    limits = atrium_limits.LimitSet(
        atrium_limits.upload_limit(10),
        atrium_limits.limit(_limit_env("DPI"), 300, unit="dpi", key="pdf_render_dpi"),
    )
    app = FastAPI(version="1.2.3")
    info = build_info(app, "atrium-test", limits, categories=["a"])
    assert info["limits"] == {"max_upload_mb": 10.0, "pdf_render_dpi": 150}
    assert info["limits_meta"]["pdf_render_dpi"] == {
        "env": _limit_env("DPI"),
        "unit": "dpi",
        "default": 300,
        "source": "env",
    }
    assert info["limits_meta"]["max_upload_mb"]["env"] == "MAX_UPLOAD_MB"
    assert info["categories"] == ["a"]


def test_build_info_with_a_plain_dict_is_unchanged():
    info = build_info(FastAPI(), "atrium-test", {"max_upload_mb": 5.0})
    assert info["limits"] == {"max_upload_mb": 5.0}
    assert "limits_meta" not in info


def test_resolve_max_upload_mb_is_strict(monkeypatch):
    monkeypatch.delenv("MAX_UPLOAD_BYTES", raising=False)
    monkeypatch.setenv("MAX_UPLOAD_MB", "12.5")
    assert resolve_max_upload_mb(10) == 12.5
    monkeypatch.setenv("MAX_UPLOAD_MB", " ")
    assert resolve_max_upload_mb(10) == 10.0
    monkeypatch.setenv("MAX_UPLOAD_MB", "ten")
    with pytest.raises(atrium_limits.LimitConfigError, match="MAX_UPLOAD_MB"):
        resolve_max_upload_mb(10)
    monkeypatch.delenv("MAX_UPLOAD_MB")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024))
    assert resolve_max_upload_mb(10) == 2.0


def test_cors_exposes_retry_after_and_the_limits_header():
    app = FastAPI()
    add_cors(app)

    @app.get("/x")
    def x():
        return {}

    r = TestClient(app).get("/x", headers={"Origin": "https://example.org"})
    exposed = {h.strip().lower() for h in r.headers.get("access-control-expose-headers", "").split(",")}
    assert {"retry-after", "x-atrium-limits-applied"} <= exposed


# ---------------------------------------------------------------------------------------
# atrium-project#32 round 2 (generation 3): the typed contract. The reason registry and
# its statuses, the error responses every route declares, the finished spec (the record
# schema, the registry, the service id, no FastAPI 422 body), the /info digest and the
# record parser. None of it changes a byte a service sends: the models document, they do
# not filter.
# ---------------------------------------------------------------------------------------

from typing import Any, Dict, Optional  # noqa: E402

from pydantic import Field  # noqa: E402

import atrium_document  # noqa: E402
import atrium_openapi  # noqa: E402
from atrium_service import (  # noqa: E402
    REASON_STATUSES,
    AtriumDocument,
    CreateAction,
    ErrorBody,
    InfoBase,
    LimitNote,
    attach_openapi_contract,
    error_responses,
    openapi_digest,
    operation_id,
    parse_record_part,
)

#: Every reason code ever published, in the order it was registered. A code may be ADDED to
#: REASON_CODES; one listed here may never leave it (§4.4: "a published code is never renamed
#: or removed"). This is the hub-side half of that rule; atrium_openapi.py compare is the
#: release-side half, against the previous release's spec.
PUBLISHED_REASON_CODES = (
    "limit_exceeded",  # #53, 2026-09-27
    "busy",  # #53, 2026-09-27
    "unsupported_media_type",  # #32 round 2
    "invalid_record",  # #32 round 2 (#67 R1's seed path)
    "ocr_text_layer",  # #32 round 2 (atrium-llm-enrich#10 W6, raised by api-digital)
)


def test_no_published_reason_code_is_ever_removed():
    assert set(PUBLISHED_REASON_CODES) <= set(REASON_CODES), set(PUBLISHED_REASON_CODES) - set(REASON_CODES)


def test_every_code_has_its_statuses_and_limit_exceeded_follows_atrium_limits():
    assert set(REASON_STATUSES) == set(REASON_CODES)
    assert REASON_STATUSES["limit_exceeded"] == tuple(atrium_limits.LIMIT_STATUSES)
    assert REASON_STATUSES["busy"] == (429,)


def test_a_code_is_refused_with_a_status_it_is_not_registered_for():
    assert error_body(415, "x", "unsupported_media_type", accepted=[".xml"])["accepted"] == [".xml"]
    with pytest.raises(ValueError, match="sent with HTTP"):
        error_body(400, "x", "unsupported_media_type")
    with pytest.raises(ValueError, match="sent with HTTP"):
        AtriumHTTPError(500, "x", reason="invalid_record")
    assert AtriumHTTPError(422, "x", reason="ocr_text_layer").reason == "ocr_text_layer"


def test_error_responses_are_fresh_dicts_and_429_documents_retry_after():
    first, second = error_responses(422, 429), error_responses(422, 429)
    assert first[422]["model"] is ErrorBody and first[422] is not second[422]
    assert first[429]["headers"] is not second[429]["headers"]
    assert first[429]["headers"]["Retry-After"]["schema"] == {"type": "integer"}
    assert "invalid_record" in first[422]["description"]


class _ExtractResponse(BaseModel):
    doc_id: str
    document_json: Optional[AtriumDocument] = Field(description="the record")
    paradata: Optional[CreateAction]
    limits_applied: list[LimitNote]


def _contract_app() -> FastAPI:
    app = FastAPI(
        title="contract",
        version="1.2.3",
        responses=error_responses(422, 500),
        generate_unique_id_function=operation_id,
        root_path_in_servers=False,
    )
    attach_error_handlers(app)
    attach_health(app, state=ServiceState())
    attach_openapi_contract(app, "atrium-test")

    @app.get("/info", response_model=None, responses={200: {"model": InfoBase}})
    def info() -> Dict[str, Any]:
        return build_info(app, "atrium-test", atrium_limits.LimitSet(atrium_limits.upload_limit(5)))

    @app.post(
        "/extract",
        response_model=None,
        responses={200: {"model": _ExtractResponse}, **error_responses(413, 415)},
    )
    async def extract(
        file: UploadFile = File(...),
        document_json: UploadFile = File(None, json_schema_extra={"contentMediaType": "application/json"}),
    ):
        raise AtriumHTTPError(415, "no", reason="unsupported_media_type", accepted=[".txt"])

    @app.get("/noparams", response_model=None, responses={200: {"model": InfoBase}})
    def noparams() -> Dict[str, Any]:
        return {}

    return app


def _refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value
            else:
                yield from _refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _refs(item)


def test_the_finished_spec_publishes_the_contract():
    spec = _contract_app().openapi()
    schemas = spec["components"]["schemas"]
    assert not {"HTTPValidationError", "ValidationError"} & set(schemas)
    assert not [name for name in schemas if name.endswith(("-Input", "-Output"))]
    extract = spec["paths"]["/extract"]["post"]
    assert extract["operationId"] == "extract"
    assert extract["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/_ExtractResponse"
    }
    for status in ("413", "415", "422", "500"):
        assert extract["responses"][status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorBody"
        }
    assert "422" not in spec["paths"]["/noparams"]["get"]["responses"], "no parameters, no body: no 422"
    assert "422" not in spec["paths"]["/ready"]["get"]["responses"]
    assert "422" in spec["paths"]["/health"]["get"]["responses"], "/health takes ?deep="
    assert spec["paths"]["/health"]["get"]["responses"]["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthBody"
    }
    assert spec["info"]["x-atrium-service"] == "atrium-test"
    assert set(spec["x-atrium-reason-codes"]) == set(REASON_CODES)
    assert spec["x-atrium-reason-codes"]["unsupported_media_type"]["statuses"] == [415]
    assert "servers" not in spec


def test_the_record_component_is_the_vendored_schema_with_its_defs_hoisted():
    spec = _contract_app().openapi()
    schemas = spec["components"]["schemas"]
    record = atrium_document.load_schema()
    assert schemas["AtriumDocument"]["title"] == record["title"]
    assert not {"$schema", "$id", "$defs"} & set(schemas["AtriumDocument"])
    for name in record["$defs"]:
        assert f"AtriumDocument_{name}" in schemas
    assert spec["x-atrium-record-schema"] == {
        "schema_version": atrium_document.SCHEMA_VERSION,
        "sha256": atrium_openapi.digest(record),
    }
    for ref in _refs(spec):
        assert ref.startswith("#/components/schemas/") and ref.rsplit("/", 1)[-1] in schemas, ref


def test_the_finished_spec_is_valid_openapi():
    validator = pytest.importorskip("openapi_spec_validator")
    validator.validate(_contract_app().openapi())


def test_info_reports_the_digest_of_the_served_spec():
    client = TestClient(_contract_app())
    served = client.get("/openapi.json").json()
    assert client.get("/info").json()["openapi_sha256"] == atrium_openapi.digest(served)


def test_openapi_digest_is_none_rather_than_an_error():
    app = FastAPI()

    def broken():
        raise RuntimeError("cannot build")

    app.openapi = broken
    assert openapi_digest(app) is None


def test_responses_and_errors_conform_to_the_published_schema():
    pytest.importorskip("jsonschema")
    app = _contract_app()
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    atrium_openapi.validate_response(spec, "/info", "get", 200, client.get("/info").json())
    atrium_openapi.validate_response(spec, "/health", "get", 200, client.get("/health").json())
    refused = client.post("/extract", files={"file": ("a.bin", b"x")})
    assert refused.status_code == 415
    assert refused.json() == {"status": 415, "reason": "unsupported_media_type", "detail": "no", "accepted": [".txt"]}
    atrium_openapi.validate_response(spec, "/extract", "post", 415, refused.json())
    import jsonschema

    with pytest.raises(jsonschema.ValidationError):
        atrium_openapi.validate_response(spec, "/extract", "post", 415, {"status": "415", "detail": 1})


def test_parse_record_part_opens_what_opens_and_refuses_the_rest():
    assert parse_record_part(None) is None
    assert parse_record_part(b"") is None and parse_record_part(b"  \n") is None
    assert parse_record_part(b'{"doc_id": "C-1", "source": {"sha512": "0"}}') == {
        "doc_id": "C-1",
        "source": {"sha512": "0"},
    }
    assert parse_record_part('﻿{"schema_version": "1.0"}') == {"schema_version": "1.0"}
    assert parse_record_part({"doc_id": "x"}) == {"doc_id": "x"}
    for raw, message in (
        (b"{not json", "not valid JSON"),
        (b"[1, 2]", "not an object"),
        (b"\xff\xfe\x00", "not UTF-8"),
        (b'{"schema_version": "9.0"}', "reads up to 1.x"),
        (b'{"schema_version": "one"}', "not a version"),
        (["a"], "not an object"),
    ):
        with pytest.raises(AtriumHTTPError) as excinfo:
            parse_record_part(raw, label="document_record")
        assert excinfo.value.status_code == 422 and excinfo.value.reason == "invalid_record"
        assert message in excinfo.value.detail and "document_record" in excinfo.value.detail


def test_parse_record_part_accepts_a_record_the_schema_would_reject():
    """A schema-invalid baseline is the tool's to report (document_json_schema_error), not a refusal."""
    assert parse_record_part(b'{"schema_version": "1.0", "doc_id": 7}') == {"schema_version": "1.0", "doc_id": 7}


def test_a_record_part_parse_record_part_accepts_is_one_load_document_reads(tmp_path):
    """The services write the part's bytes as sent and open them with atrium_document.load_document,
    so every record the gate lets through must load there too: a UTF-8 byte-order mark used to pass
    the gate and fail the load ("Unexpected UTF-8 BOM"), a 500 after the whole upload was processed."""
    raw = b"\xef\xbb\xbf" + b'{"doc_id": "C-1", "source": {"sha512": "0"}}'
    assert parse_record_part(raw) == {"doc_id": "C-1", "source": {"sha512": "0"}}
    path = tmp_path / "C-1.document.json"
    path.write_bytes(raw)
    assert atrium_document.load_document(str(path))["doc_id"] == "C-1"


def test_models_allow_extra_members_so_additions_are_not_breaking():
    for model in (ErrorBody, InfoBase, LimitNote, CreateAction):
        assert model.model_json_schema().get("additionalProperties") is True, model.__name__
    schema = CreateAction.model_json_schema(by_alias=True)
    assert {"@id", "@type", "object", "startTime", "actionStatus"} <= set(schema["properties"])
