"""Tests for tools/ci/rocrate_check.py and tools/e2e/make_seed.py (atrium-project#71).

The real validator runs in CI (hub-self-check.yml, e2e-pipeline-smoke.yml) and needs the network
for the RO-Crate context. What these tests pin is the part that is ours: which crates are built,
that each profile runs separately (Process Run Crate without inheritance), and which severities
fail the job. The validator is replaced by a script that writes the report it is given.

Run: pytest tests/test_rocrate_check.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rocrate_check = _load("rocrate_check", _HUB_ROOT / "tools" / "ci" / "rocrate_check.py")


def _fake_validator(tmp_path: Path, issues_by_profile: dict) -> list:
    """A validator command writing a report with the given issues, and logging its arguments."""
    script = tmp_path / "fake_validator.py"
    script.write_text(
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "profile = args[args.index('-p') + 1]\n"
        f"issues = json.loads({json.dumps(json.dumps(issues_by_profile))}).get(profile, [])\n"
        "out = args[args.index('-o') + 1]\n"
        "json.dump({'passed': not issues, 'issues': issues}, open(out, 'w'))\n"
        f"open({json.dumps(str(tmp_path / 'calls.log'))}, 'a').write(' '.join(args) + '\\n')\n",
        encoding="utf-8",
    )
    return [sys.executable, str(script)]


def _issue(severity: str) -> dict:
    return {"severity": severity, "check": {"identifier": "x_1.0"}, "message": "m", "violatingEntity": "./"}


def test_each_profile_runs_separately_and_process_run_crate_without_inheritance(tmp_path):
    validator = _fake_validator(tmp_path, {})
    gates = {"ro-crate-1.2": "required", "process-run-crate-0.5": "required"}
    assert rocrate_check.validate(tmp_path, gates, validator) == 0
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 2
    assert "-p ro-crate-1.2" in calls[0] and "--disable-profile-inheritance" not in calls[0]
    assert "-p process-run-crate-0.5 --disable-profile-inheritance" in calls[1]


@pytest.mark.parametrize(
    "gate, severity, failures",
    [("required", "REQUIRED", 1), ("required", "RECOMMENDED", 0), ("recommended", "RECOMMENDED", 1)],
)
def test_the_gate_decides_which_issues_fail(tmp_path, gate, severity, failures):
    validator = _fake_validator(tmp_path, {"process-run-crate-0.5": [_issue(severity)]})
    gates = {"ro-crate-1.2": "required", "process-run-crate-0.5": gate}
    assert rocrate_check.validate(tmp_path, gates, validator) == failures


def test_a_validator_that_writes_no_report_fails(tmp_path):
    gates = {"ro-crate-1.2": "required", "process-run-crate-0.5": "required"}
    assert rocrate_check.validate(tmp_path, gates, [sys.executable, "-c", "pass"]) == 2


def test_the_samples_are_four_crates_with_their_files(tmp_path):
    crates = rocrate_check.build_samples(tmp_path)
    assert [c.name for c in crates] == ["document", "run", "fragment", "service-action"]
    for crate in crates:
        assert (crate / "ro-crate-metadata.json").is_file()
    assert (tmp_path / "document" / "TEITOK" / "CTX000000001.teitok.xml").is_file()
    assert (tmp_path / "run" / "CTX000000001" / "ro-crate-metadata.json").is_file()


def test_record_mode_builds_the_fragment_under_a_stub_root(tmp_path):
    sys.path.insert(0, str(_HUB_ROOT / "docs" / "templates" / "shared"))
    import atrium_rocrate as rc

    record_path = tmp_path / "final.json"
    record_path.write_text(json.dumps(rc._sample_record()), encoding="utf-8")
    paradata = []
    for i, pd in enumerate(rc._sample_paradata()):
        path = tmp_path / f"p{i}.json"
        path.write_text(json.dumps(pd), encoding="utf-8")
        paradata.append(str(path))
    (tmp_path / "not-paradata.json").write_text("[]", encoding="utf-8")
    out = rocrate_check.build_record(record_path, paradata + [str(tmp_path / "not-paradata.json")], tmp_path / "crate")
    crate = json.loads((out / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    root = {e["@id"]: e for e in crate["@graph"]}["./"]
    assert set(rc._SAMPLE_RUN_UUIDS.values()) <= {m["@id"] for m in root["mentions"]}
    assert not [e for e in crate["@graph"] if e.get("@type") == "File"]


def test_make_seed_writes_a_valid_seed_of_its_file(tmp_path):
    pytest.importorskip("jsonschema")
    make_seed = _load("make_seed", _HUB_ROOT / "tools" / "e2e" / "make_seed.py")
    source = tmp_path / "x.pdf"
    source.write_bytes(b"%PDF-1.7")
    out = tmp_path / "seed.json"
    assert (
        make_seed.main([str(source), "--doc-id", "AMCR-F-7", "--media-type", "application/pdf", "--out", str(out)]) == 0
    )
    seed = json.loads(out.read_text(encoding="utf-8"))
    assert seed["doc_id"] == "AMCR-F-7" and seed["source"]["filename"] == "x.pdf"
    assert "origin" not in seed["source"]
