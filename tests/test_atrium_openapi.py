"""tests/test_atrium_openapi.py — the release gate for the OpenAPI document (atrium-project#32 item 3).

Hub-only, like tests/test_atrium_service.py: every tool repo runs ``atrium_openapi.py --selftest``
through para-drift and ``tests/test_openapi_contract.py`` against its own services; this file
holds the rules themselves to account, including the ones a self-test cannot reach — a real
oasdiff binary (when one is installed), a fake one for the exit-code contract, the release
listing's failure modes and the command line.

Each rule was checked against the failure it exists for on 2026-09-28 (oasdiff v1.32.1):
without the raised severities, a removed optional response property, a renamed operationId and a
removed error status all pass ``--fail-on ERR``; without the ``anyOf`` → ``oneOf`` normalisation,
making a ``$ref`` property nullable reports every property under it as removed.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent.parent / "docs" / "templates" / "shared"
sys.path.insert(0, str(SHARED))

import atrium_openapi  # noqa: E402
from atrium_openapi import OpenAPIError, compare, normalise, select_baseline  # noqa: E402


def _spec(version="1.2.0", props=None, codes=("busy",), op_id="info", nullable=None, statuses=("200", "503")):
    props = {"a": {"type": "string"}, "b": {"type": "string"}} if props is None else props
    responses = {
        status: {
            "description": status,
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/I"}}},
        }
        for status in statuses
    }
    schemas = {
        "I": {"type": "object", "properties": dict(props), "required": sorted(props)},
        "C": {"type": "object", "properties": {"x": {"type": "string"}}},
    }
    if nullable is not None:
        schemas["I"]["properties"]["c"] = nullable
        schemas["I"]["required"] = sorted(schemas["I"]["properties"])
    return {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": version, "x-atrium-service": "atrium-test"},
        "paths": {"/info": {"get": {"operationId": op_id, "responses": responses}}},
        "components": {"schemas": schemas},
        "x-atrium-reason-codes": {code: {"description": code, "statuses": [429]} for code in codes},
    }


# ── the rules (built-in, no oasdiff) ───────────────────────────────────────────────────────


def test_bootstrap_passes_and_says_so():
    code, lines = compare(None, _spec(), "1.2.0")
    assert code == 0 and "bootstrap" in lines[0]


def test_an_unchanged_spec_is_compatible_across_versions():
    assert compare(_spec("1.2.0"), _spec("1.3.0"), "1.3.0")[0] == 0


@pytest.mark.parametrize(
    "rev",
    [
        _spec("1.3.0", props={"a": {"type": "string"}}),
        _spec("1.3.0", op_id="get_info"),
        _spec("1.3.0", statuses=("200",)),
    ],
    ids=["response-property-removed", "operation-id-renamed", "error-status-removed"],
)
def test_a_breaking_change_fails_unless_the_major_went_up(rev):
    assert compare(_spec("1.2.0"), rev, "1.3.0")[0] == 1
    assert compare(_spec("1.2.0"), rev, "2.0.0")[0] == 0


def test_zero_x_needs_one_point_zero_to_break():
    """The 2026-09-28 decision: 0.x is not a licence to break (nlp-enrich 0.22, llm-enrich 0.8)."""
    rev = _spec("0.23.0", props={"a": {"type": "string"}})
    assert compare(_spec("0.22.0"), rev, "0.23.0")[0] == 1
    assert compare(_spec("0.22.0"), rev, "1.0.0")[0] == 0


def test_a_removed_or_narrowed_reason_code_always_fails():
    assert compare(_spec(codes=("busy", "invalid_record")), _spec("2.0.0", codes=("busy",)), "2.0.0")[0] == 1
    narrowed = _spec("2.0.0")
    narrowed["x-atrium-reason-codes"]["busy"]["statuses"] = []
    assert compare(_spec(), narrowed, "2.0.0")[0] == 1
    added = _spec("1.3.0", codes=("busy", "ocr_text_layer"))
    assert compare(_spec(), added, "1.3.0")[0] == 0, "adding a code is not breaking"


def test_a_changed_service_id_always_fails():
    rev = _spec("2.0.0")
    rev["info"]["x-atrium-service"] = "atrium-other"
    code, lines = compare(_spec(), rev, "2.0.0")
    assert code == 1
    assert any("x-atrium-service-previous: 'atrium-test'" in line for line in lines), "the hint names the fix"


@pytest.mark.parametrize("version", ["1.3.0", "2.0.0"])
def test_a_declared_rename_passes_at_any_version(version):
    """atrium-project#72 (alto#56): the rename is declared by the new spec, not implied by a
    major bump; the renamed release is still held to every other rule."""
    rev = _spec(version)
    rev["info"]["x-atrium-service"] = "atrium-ocr-postprocess"
    rev["info"]["x-atrium-service-previous"] = "atrium-test"
    code, lines = compare(_spec(), rev, version)
    assert code == 0 and any("Declared rename" in line for line in lines), lines

    broken = _spec(version, props={"a": {"type": "string"}})
    broken["info"].update(rev["info"])
    assert compare(_spec(), broken, version)[0] == (0 if version == "2.0.0" else 1), "other rules still apply"


def test_a_rename_declaring_another_id_fails():
    rev = _spec("2.0.0")
    rev["info"]["x-atrium-service"] = "atrium-ocr-postprocess"
    rev["info"]["x-atrium-service-previous"] = "atrium-somebody-else"
    code, lines = compare(_spec(), rev, "2.0.0")
    assert code == 1 and any("not the baseline's id" in line for line in lines)


def test_a_kept_declaration_is_harmless_once_the_baseline_carries_the_new_id():
    base = _spec("2.0.0")
    base["info"].update({"x-atrium-service": "atrium-ocr-postprocess", "x-atrium-service-previous": "atrium-test"})
    rev = _spec("2.1.0")
    rev["info"].update(base["info"])
    rev["info"]["version"] = "2.1.0"
    assert compare(base, rev, "2.1.0")[0] == 0


def test_the_record_schema_counts_by_its_major():
    base, rev = _spec(), _spec("1.3.0")
    base["x-atrium-record-schema"] = {"schema_version": "1.0", "sha256": "a"}
    rev["x-atrium-record-schema"] = {"schema_version": "1.0", "sha256": "b"}
    code, lines = compare(base, rev, "1.3.0")
    assert code == 0 and any("within its major" in line for line in lines)
    rev["x-atrium-record-schema"]["schema_version"] = "2.0"
    assert compare(base, rev, "1.3.0")[0] == 1


def test_require_oasdiff_fails_closed_when_it_is_missing():
    code, lines = compare(_spec(), _spec("1.3.0"), "1.3.0", oasdiff="no-such-oasdiff-binary", require_oasdiff=True)
    assert code == 1 and any("not installed" in line for line in lines)


def test_normalise_reads_optional_as_nullable_and_stubs_the_record():
    spec = _spec(nullable={"anyOf": [{"$ref": "#/components/schemas/C"}, {"type": "null"}]})
    spec["components"]["schemas"]["AtriumDocument"] = {"title": "record", "properties": {"x": {}}}
    spec["components"]["schemas"]["AtriumDocument_bbox"] = {"type": "array"}
    out = normalise(spec)
    assert out["components"]["schemas"]["I"]["properties"]["c"] == {
        "oneOf": [{"$ref": "#/components/schemas/C"}, {"type": "null"}]
    }
    assert out["components"]["schemas"]["AtriumDocument"] == {"type": "object"}
    assert out["components"]["schemas"]["AtriumDocument_bbox"] == {"type": "object"}
    three = normalise({"anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "null"}]})
    assert "anyOf" in three, "only a two-branch union with null is a nullable"
    assert "anyOf" in spec["components"]["schemas"]["I"]["properties"]["c"], "the input is not mutated"


# ── oasdiff: the exit-code contract (fake) and the real rules (when installed) ─────────────


def _fake_oasdiff(tmp_path, exit_code, text="error\t[response-property-removed]\n"):
    script = tmp_path / "oasdiff"
    script.write_text(f"#!{sys.executable}\nimport sys\nprint({text!r})\nsys.exit({exit_code})\n", encoding="utf-8")
    script.chmod(0o755)
    return str(script)


def test_oasdiff_exit_1_is_a_breaking_change(tmp_path):
    fake = _fake_oasdiff(tmp_path, 1)
    code, lines = compare(_spec(), _spec("1.3.0"), "1.3.0", oasdiff=fake, require_oasdiff=True)
    assert code == 1 and any("oasdiff reports breaking" in line for line in lines)
    assert compare(_spec(), _spec("2.0.0"), "2.0.0", oasdiff=fake, require_oasdiff=True)[0] == 0


def test_oasdiff_crashing_is_an_error_not_a_pass(tmp_path):
    with pytest.raises(OpenAPIError, match="exited 3"):
        compare(_spec(), _spec("1.3.0"), "1.3.0", oasdiff=_fake_oasdiff(tmp_path, 3), require_oasdiff=True)


_REAL = shutil.which("oasdiff")


@pytest.mark.skipif(_REAL is None, reason="oasdiff is not installed (CI installs atrium_openapi.OASDIFF_VERSION)")
@pytest.mark.parametrize(
    "rev",
    [
        _spec("1.3.0", props={"a": {"type": "string"}, "b": {"type": "string"}, "x": {"type": "string"}}),
        _spec("1.3.0", nullable={"$ref": "#/components/schemas/C"}),
    ],
    ids=["property-added", "nullable-narrowed"],
)
def test_real_oasdiff_accepts_additive_changes(rev):
    base = (
        _spec()
        if "x" in rev["components"]["schemas"]["I"]["properties"]
        else _spec(nullable={"anyOf": [{"$ref": "#/components/schemas/C"}, {"type": "null"}]})
    )
    code, lines = compare(base, rev, "1.3.0", oasdiff=_REAL, require_oasdiff=True)
    assert code == 0, lines


@pytest.mark.skipif(_REAL is None, reason="oasdiff is not installed (CI installs atrium_openapi.OASDIFF_VERSION)")
def test_real_oasdiff_with_the_raised_rules_catches_what_its_defaults_miss():
    optional = _spec()
    optional["components"]["schemas"]["I"]["required"] = ["a"]
    removed = json.loads(json.dumps(optional))
    removed["components"]["schemas"]["I"]["properties"].pop("b")
    removed["info"]["version"] = "1.3.0"
    code, lines = compare(optional, removed, "1.3.0", oasdiff=_REAL, require_oasdiff=True)
    assert code == 1 and any("response-optional-property-removed" in line for line in lines), lines
    became_nullable = _spec("1.3.0", nullable={"anyOf": [{"$ref": "#/components/schemas/C"}, {"type": "null"}]})
    code, lines = compare(_spec(nullable={"$ref": "#/components/schemas/C"}), became_nullable, "1.3.0", oasdiff=_REAL)
    assert code == 1 and any("became-nullable" in line for line in lines), lines


# ── the baseline ───────────────────────────────────────────────────────────────────────────


def _release(tag, asset=True, **flags):
    assets = [{"name": "openapi.json", "browser_download_url": f"https://dl.invalid/{tag}"}] if asset else []
    return {"tag_name": tag, "draft": False, "prerelease": False, "assets": assets, **flags}


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener(listing, specs, fail=None):
    def opener(request):
        url = request.full_url
        if fail and fail in url:
            raise urllib.error.URLError("boom")
        if "/releases?" in url:
            page = int(url.rsplit("page=", 1)[1])
            return _Response(json.dumps(listing if page == 1 else []).encode())
        tag = url.rsplit("/", 1)[1]
        assert "Authorization" not in request.headers, "the asset download must not carry the token"
        return _Response(json.dumps(specs[tag]).encode())

    return opener


def test_the_baseline_is_the_highest_version_below_the_tag():
    listing = [
        _release("v1.8.0-beta"),
        _release("v1.9.0"),
        _release("v1.9.1", asset=False),
        _release("v1.10.0", draft=True),
        _release("v2.0.0", prerelease=True),
        _release("v1.7.5-beta"),
        _release("not-a-version"),
    ]
    assert select_baseline(listing, "v1.9.1")["tag_name"] == "v1.9.0"
    assert select_baseline(listing, "v1.8.1")["tag_name"] == "v1.8.0-beta", "a hotfix compares with its own line"
    assert select_baseline(listing, None)["tag_name"] == "v1.9.0", "a pull request compares with the newest"
    assert select_baseline(listing, "v1.7.5-beta") is None


def test_baseline_fetches_the_asset_without_the_token():
    specs = {"v1.9.0": _spec("1.9.0")}
    tag, spec = atrium_openapi.baseline(
        "ufal/atrium-test", "v2.0.0", token="t0ken", opener=_opener([_release("v1.9.0")], specs)
    )
    assert tag == "v1.9.0" and spec["info"]["version"] == "1.9.0"


def test_an_api_error_fails_the_gate_rather_than_passing_as_a_bootstrap():
    with pytest.raises(OpenAPIError, match="failed"):
        atrium_openapi.baseline("ufal/atrium-test", None, opener=_opener([], {}, fail="/releases"))
    assert atrium_openapi.baseline("ufal/atrium-test", None, opener=_opener([], {})) == (None, None)


# ── the command line ───────────────────────────────────────────────────────────────────────


def _cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(SHARED / "atrium_openapi.py"), *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_stamp_writes_the_asset_and_its_digest(tmp_path):
    (tmp_path / "service").mkdir()
    (tmp_path / "service" / "openapi.json").write_text(json.dumps(_spec("0.0.0")), encoding="utf-8")
    (tmp_path / "para_config.txt").write_text("[tool]\nversion = v1.4.0-beta\n", encoding="utf-8")
    proc = _cli("stamp", "--para-config", "para_config.txt", "--out-dir", "dist", cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    raw = (tmp_path / "dist" / "openapi.json").read_bytes()
    asset = json.loads(raw)
    assert asset["info"]["version"] == "1.4.0-beta"
    line = (tmp_path / "dist" / "openapi.json.sha256").read_text(encoding="utf-8")
    sha, name = line.split()
    assert name == "openapi.json" and sha == atrium_openapi.digest(asset)
    assert _cli("digest", "dist/openapi.json", cwd=tmp_path).stdout.strip() == sha
    # What a consumer runs (`sha256sum -c openapi.json.sha256`, or GitHub's asset digest): the
    # asset's own bytes hash to its line, because stamp writes the canonical form the digest
    # (and /info `openapi_sha256`) is taken of. A pretty-printed asset failed this.
    assert line == f"{hashlib.sha256(raw).hexdigest()}  openapi.json\n"
    assert raw == atrium_openapi.canonical_bytes(asset)


def test_compare_on_the_command_line_writes_a_summary_and_uses_the_para_config(tmp_path):
    (tmp_path / "base.json").write_text(json.dumps(_spec("1.2.0")), encoding="utf-8")
    (tmp_path / "rev.json").write_text(json.dumps(_spec("1.3.0", props={"a": {"type": "string"}})), encoding="utf-8")
    (tmp_path / "para_config.txt").write_text("[tool]\nversion = v1.3.0\n", encoding="utf-8")
    args = ["compare", "--base", "base.json", "--rev", "rev.json", "--para-config", "para_config.txt"]
    args += ["--oasdiff", "no-such-oasdiff-binary", "--summary", "summary.md"]
    proc = _cli(*args, cwd=tmp_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "property 'b' removed" in (tmp_path / "summary.md").read_text(encoding="utf-8")
    missing = _cli(
        "compare", "--base", "none.json", "--rev", "rev.json", "--para-config", "para_config.txt", cwd=tmp_path
    )
    assert missing.returncode == 0 and "bootstrap" in missing.stdout


def test_export_and_check_round_trip_on_a_real_app(tmp_path):
    pytest.importorskip("fastapi")
    (tmp_path / "svc.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI(version='1.0.0')\n\n@app.get('/x')\ndef x():\n    return {}\n",
        encoding="utf-8",
    )
    assert _cli("export", "--app", "svc:app", "--out", "spec.json", cwd=tmp_path).returncode == 0
    assert _cli("check", "--app", "svc:app", "--spec", "spec.json", cwd=tmp_path).returncode == 0
    stale = json.loads((tmp_path / "spec.json").read_text(encoding="utf-8"))
    stale["paths"]["/y"] = stale["paths"]["/x"]
    (tmp_path / "spec.json").write_text(json.dumps(stale), encoding="utf-8")
    proc = _cli("check", "--app", "svc:app", "--spec", "spec.json", cwd=tmp_path)
    assert proc.returncode == 1 and "/paths/~1y: removed" in proc.stderr and "Regenerate it" in proc.stderr


def test_the_selftest_passes():
    assert _cli("--selftest", cwd=SHARED).returncode == 0


# ── one oasdiff version everywhere ──────────────────────────────────────────────────────────
# The breaking-change rules (RAISED_RULES, the anyOf → oneOf normalisation) were measured
# against OASDIFF_VERSION. Eight workflows install oasdiff — the hub's own two and the six
# tool repos' release.yml — each with the version spelled out, so a bump that misses one runs
# that gate on rules nobody measured.

_HUB_ROOT = Path(__file__).resolve().parent.parent
_SIBLINGS = Path(os.environ.get("ATRIUM_SIBLING_ROOT", _HUB_ROOT.parent))
_TOOL_REPOS = (
    "atrium-page-classification",
    "atrium-ocr-postprocess",
    "atrium-nlp-enrich",
    "atrium-keyword-extract",
    "atrium-translator",
    "atrium-digital-convert",
)


@pytest.mark.parametrize(
    "workflow",
    [
        _HUB_ROOT / ".github" / "workflows" / "api-contract.reusable.yml",
        _HUB_ROOT / ".github" / "workflows" / "hub-self-check.yml",
        *(_SIBLINGS / repo / ".github" / "workflows" / "release.yml" for repo in _TOOL_REPOS),
    ],
    ids=lambda path: f"{path.parts[-4]}/{path.name}",
)
def test_every_workflow_installs_the_measured_oasdiff_version(workflow):
    if not workflow.is_file():
        pytest.skip(f"{workflow} not present (sibling checkout absent)")
    text = workflow.read_text(encoding="utf-8")
    if "oasdiff" not in text:
        pytest.skip(f"{workflow} does not install oasdiff (the typed contract is not adopted there yet)")
    versions = set(re.findall(r"OASDIFF_VERSION:\s*(\S+)", text))
    assert versions == {atrium_openapi.OASDIFF_VERSION}, (
        f"{workflow} installs oasdiff {sorted(versions)}, but atrium_openapi.py's rules were measured "
        f"against {atrium_openapi.OASDIFF_VERSION}"
    )
