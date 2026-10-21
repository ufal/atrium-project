"""Tests for tools/e2e/e2e_manifest.py — the images an E2E run used, by digest (#81 B.3, #77).

The inspector is injected, so no Docker daemon is needed: each test hands `build` the
`docker image inspect` object a runner would have returned.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools" / "e2e"))

import e2e_manifest as em  # noqa: E402

PC = "ghcr.io/ufal/atrium-page-classification:1.9.5-beta"
KW = "ghcr.io/ufal/atrium-keyword-extract-api:1.4.0-beta"
DIGEST = "sha256:" + "a" * 64


def inspected(repository: str, ref: str = "v1.9.5-beta") -> dict:
    return {
        "RepoDigests": [f"ghcr.io/ufal/other@sha256:{'b' * 64}", f"{repository}@{DIGEST}"],
        "Created": "2026-10-19T12:00:00Z",
        "Config": {"Env": ["PATH=/usr/bin", f"ATRIUM_RUNNER_REF={ref}", f"ATRIUM_RUNNER_IMAGE={repository}"]},
    }


def test_a_pulled_image_is_recorded_by_its_own_digest_and_source_ref():
    row = em.entry(PC, inspected("ghcr.io/ufal/atrium-page-classification"))
    assert row == {
        "image": PC,
        "pulled": True,
        "digest": DIGEST,
        "created": "2026-10-19T12:00:00Z",
        "source_ref": "v1.9.5-beta",
        "runner_image": "ghcr.io/ufal/atrium-page-classification",
    }


def test_an_image_the_run_did_not_pull_is_recorded_as_such():
    assert em.entry(PC, None) == {"image": PC, "pulled": False}


def test_a_local_build_has_no_registry_digest():
    row = em.entry(PC, {"RepoDigests": [], "Config": {"Env": []}})
    assert row["digest"] is None and row["source_ref"] is None


def test_the_info_version_is_read_from_the_saved_answer(tmp_path):
    info = tmp_path / "info.json"
    info.write_text(json.dumps({"name": "keyword-extract", "version": "1.4.0-beta"}), encoding="utf-8")
    images = {PC: inspected("ghcr.io/ufal/atrium-page-classification"), KW: None}
    manifest = em.build(
        [PC, KW],
        {KW: info},
        "pipeline",
        "1.9.5-beta",
        "success",
        inspect=images.get,
        environ={"GITHUB_RUN_ID": "7", "GITHUB_REPOSITORY": "ufal/atrium-project", "GITHUB_SHA": "c" * 40},
    )
    assert manifest["run"] == "https://github.com/ufal/atrium-project/actions/runs/7"
    assert manifest["hub_commit"] == "c" * 40
    assert [row["pulled"] for row in manifest["images"]] == [True, False]
    assert "info_version" not in manifest["images"][1]  # not pulled: nothing else is recorded


def test_the_summary_names_every_image(tmp_path):
    manifest = em.build([PC, KW], {}, "pipeline", "latest", "failure", inspect=lambda ref: None, environ={})
    table = em.summary(manifest)
    assert "failure" in table
    assert f"| `{PC}` | not pulled |" in table and f"| `{KW}` | not pulled |" in table


def test_main_writes_the_manifest_and_appends_the_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "docker_inspect", lambda ref: inspected("ghcr.io/ufal/atrium-page-classification"))
    summary = tmp_path / "summary.md"
    summary.write_text("before\n", encoding="utf-8")
    out = tmp_path / "work" / "e2e-manifest.json"
    code = em.main(
        ["--lane", "pipeline", "--tag", "latest", "--image", PC, "--out", str(out), "--summary", str(summary)]
    )
    assert code == 0
    assert json.loads(out.read_text(encoding="utf-8"))["images"][0]["digest"] == DIGEST
    assert summary.read_text(encoding="utf-8").startswith("before\n### Images of this run")


def test_both_lanes_record_their_images_whatever_the_outcome():
    yaml = __import__("pytest").importorskip("yaml")
    for lane, images in (("pipeline", 5), ("digital", 2)):
        workflow = yaml.safe_load((_HUB_ROOT / ".github" / "workflows" / f"e2e-{lane}-smoke.yml").read_text("utf-8"))
        steps = [step for job in workflow["jobs"].values() for step in job["steps"]]
        record = [s for s in steps if "tools/e2e/e2e_manifest.py" in s.get("run", "")]
        upload = [s for s in steps if "e2e-manifest" in str((s.get("with") or {}).get("name", ""))]
        assert len(record) == 1 and record[0].get("if") == "always()", lane
        assert record[0]["run"].count("--image ") == images, lane
        assert len(upload) == 1 and upload[0].get("if") == "always()", lane
