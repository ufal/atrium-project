"""The Docker build cache stays off on tags, and the scan summary counts and lists (2026-11-03).

WHY THIS EXISTS. On 2026-11-03 the six tools' first runs with per-scope build caches showed two
things these tests hold:

  1. A tag build can never reuse a cache: a run restores caches only from its own ref and the
     default branch, and the default branch builds no image. Each tag build still exported one,
     for minutes (keyword-extract's `llm` 374 s), into the repository's 10 GB. Both builds in
     `docker-tool.reusable.yml` therefore pass no cache on a tag, and a per-target, per-leg one
     elsewhere.
  2. The report-only step after each Trivy scan counted CRITICAL and HIGH findings but did not
     say which they were. It now lists them; the copy in `security.reusable.yml` is the same
     script, and both are run here on a SARIF document shaped like Trivy's.

Parsed, not grepped: the comments above these steps quote the measurements.
History: docs/decisions/docker-tool-reusable.md#build-cache

Run: pytest tests/test_build_cache_and_scan_summary.py
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

_WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
_NOT_A_TAG = "!startsWith(github.ref, 'refs/tags/')"
_COUNT_STEP = "Count CRITICAL and HIGH findings in the job summary (report-only)"


def _step(workflow: str, job: str, name: str) -> dict:
    doc = yaml.safe_load((_WORKFLOWS / workflow).read_text(encoding="utf-8"))
    steps = [s for s in doc["jobs"][job]["steps"] if s.get("name") == name]
    assert len(steps) == 1, f"{workflow}: expected one step named {name!r} in {job}"
    return steps[0]


@pytest.mark.parametrize(
    ("job", "name", "leg"),
    [("docker-build-smoke", "Smoke Build", "smoke"), ("build-and-push", "Build and push", "push")],
)
def test_the_build_cache_is_scoped_and_off_on_tags(job, name, leg):
    inputs = _step("docker-tool.reusable.yml", job, name)["with"]
    cache_from, cache_to = str(inputs["cache-from"]), str(inputs["cache-to"])
    for value in (cache_from, cache_to):
        assert _NOT_A_TAG in value, f"{name}: the cache must be off on a tag, where no run can read it"
        assert f"scope={{0}}-{leg}" in value and "matrix.target" in value, (
            f"{name}: one cache per target and leg (an unscoped cache is overwritten by every build)"
        )
        assert value.rstrip("} ").endswith("|| ''"), f"{name}: on a tag the input must be empty, not another cache"
    assert "mode=min" in cache_to and "ignore-error=true" in cache_to, (
        f"{name}: mode=min (final layers only) and ignore-error (a failed export must not fail the build)"
    )


def _count_script(workflow: str, job: str) -> str:
    return _step(workflow, job, _COUNT_STEP)["run"]


def test_both_scan_summaries_run_the_same_script():
    assert _count_script("docker-tool.reusable.yml", "build-and-push") == _count_script(
        "security.reusable.yml", "image-scan"
    )


def _message(package: str, installed: str, cve: str, severity: str, fixed: str) -> str:
    return (
        f"Package: {package}\nInstalled Version: {installed}\nVulnerability {cve}\n"
        f"Severity: {severity}\nFixed Version: {fixed}\nLink: [{cve}](https://avd.aquasec.com/nvd/{cve.lower()})"
    )


def _rule(cve: str, severity: str) -> dict:
    return {"id": cve, "properties": {"tags": ["vulnerability", "security", severity]}}


def test_the_scan_summary_counts_and_lists_the_findings(tmp_path):
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Trivy",
                        "rules": [
                            _rule("CVE-2026-1", "HIGH"),
                            _rule("CVE-2026-2", "CRITICAL"),
                            _rule("CVE-2026-3", "MEDIUM"),
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "CVE-2026-1",
                        "message": {"text": _message("libssl3", "3.0.1", "CVE-2026-1", "HIGH", "3.0.2")},
                    },
                    {
                        "ruleId": "CVE-2026-2",
                        "message": {"text": _message("zlib1g", "1.2", "CVE-2026-2", "CRITICAL", "1.3")},
                    },
                    {
                        "ruleId": "CVE-2026-3",
                        "message": {"text": _message("bash", "5.2", "CVE-2026-3", "MEDIUM", "5.3")},
                    },
                ],
            }
        ],
    }
    (tmp_path / "trivy-results.sarif").write_text(json.dumps(sarif), encoding="utf-8")
    summary = tmp_path / "summary.md"
    env = {**os.environ, "IMAGE_REF": "ghcr.io/ufal/x-api@sha256:0", "GITHUB_STEP_SUMMARY": str(summary)}
    done = subprocess.run(
        ["bash", "-e", "-c", _count_script("docker-tool.reusable.yml", "build-and-push")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    text = summary.read_text(encoding="utf-8")
    assert "| CRITICAL | 1 |" in text and "| HIGH     | 1 |" in text
    rows = [
        line for line in text.splitlines() if line.startswith("| CRITICAL | CVE") or line.startswith("| HIGH | CVE")
    ]
    assert rows == [
        "| CRITICAL | CVE-2026-2 | `zlib1g` | 1.2 | 1.3 |",
        "| HIGH | CVE-2026-1 | `libssl3` | 3.0.1 | 3.0.2 |",
    ], "CRITICAL first; a MEDIUM finding is counted as neither and not listed"
