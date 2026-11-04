"""A Trivy DB outage costs one retry, not a release (atrium-project#72, 2026-10-29).

WHY THIS EXISTS. On 2026-10-26 the weekly image scan failed in digital-convert and keyword-extract
before scanning anything: `mirror.gcr.io/aquasec/trivy-db:2` answered 404 on a layer, and Trivy moves
to its second source (`ghcr.io`) only after an error it counts as temporary. The publishing job in
`docker-tool.reusable.yml` downloads the same DB after the images are pushed, so the same outage
during a tag would have failed the release.

Each report-only scan that downloads the DB is therefore `continue-on-error` and followed by one
retry from `ghcr.io` that is not. On 2026-11-04 Trivy's own download failed twice in one second
(exit 6, translator v1.7.3-beta), so a short pause now comes before the retry. These tests hold,
in both reusables:

  1. the first scan has an `id`, `continue-on-error: true` and `exit-code: "0"` (a failure there
     can only be Trivy failing to run, never a finding);
  2. right after it comes a pause guarded the same way, which runs only `sleep N`, and then the
     retry: guarded by `steps.<id>.outcome == 'failure'`, the same pinned action and inputs,
     `ghcr.io` as the only DB source, and not `continue-on-error`;
  3. the CVE release gate stays blocking. On 2026-11-04 it failed on a registry error, not a
     finding (keyword-extract v1.6.3-beta, `llm`), so it runs once more after a pause: the first
     gate is `continue-on-error`, the retry with the same inputs is not, and a fixable CRITICAL
     fails both.

Parsed, not grepped: the comments above these steps quote the incident.
History: docs/decisions/docker-tool-reusable.md#trivy-db-retry

Run: pytest tests/test_trivy_db_retry.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
_TRIVY = "aquasecurity/trivy-action@"
_RETRY_DB = {
    "TRIVY_DB_REPOSITORY": "ghcr.io/aquasecurity/trivy-db:2",
    "TRIVY_JAVA_DB_REPOSITORY": "ghcr.io/aquasecurity/trivy-java-db:1",
}

# (workflow file, job) holding a report-only scan that downloads the DB.
_SCANS = [
    ("docker-tool.reusable.yml", "build-and-push"),
    ("security.reusable.yml", "image-scan"),
]


def _steps(workflow: str, job: str) -> list[dict]:
    doc = yaml.safe_load((_WORKFLOWS / workflow).read_text(encoding="utf-8"))
    return doc["jobs"][job]["steps"]


def _trivy_steps(workflow: str, job: str) -> list[tuple[int, dict]]:
    return [(i, s) for i, s in enumerate(_steps(workflow, job)) if str(s.get("uses", "")).startswith(_TRIVY)]


@pytest.mark.parametrize(("workflow", "job"), _SCANS)
def test_the_first_scan_may_fail_into_the_retry(workflow, job):
    _, first = _trivy_steps(workflow, job)[0]
    assert first.get("id"), f"{workflow}: the first Trivy step needs an id for the retry's guard"
    assert first.get("continue-on-error") is True, (
        f"{workflow}: without continue-on-error a failed DB download stops the job and the retry never runs"
    )
    assert str(first["with"]["exit-code"]) == "0", (
        f"{workflow}: the scan that may fail into a retry must be report-only, or a real finding would be retried"
    )


@pytest.mark.parametrize(("workflow", "job"), _SCANS)
def test_a_guarded_pause_comes_between_the_scan_and_its_retry(workflow, job):
    steps = _steps(workflow, job)
    index, first = _trivy_steps(workflow, job)[0]
    pause = steps[index + 1]
    assert pause.get("if") == f"steps.{first['id']}.outcome == 'failure'", (
        f"{workflow}: the pause must run only when the scan failed, or every build waits"
    )
    assert re.fullmatch(r"sleep \d+", str(pause.get("run", "")).strip()), (
        f"{workflow}: the step between the scan and its retry may only pause (`sleep N`)"
    )
    assert "uses" not in pause and not pause.get("continue-on-error")


@pytest.mark.parametrize(("workflow", "job"), _SCANS)
def test_the_retry_follows_from_ghcr_and_still_fails_loudly(workflow, job):
    steps = _steps(workflow, job)
    index, first = _trivy_steps(workflow, job)[0]
    retry = steps[index + 2]
    assert retry.get("if") == f"steps.{first['id']}.outcome == 'failure'", (
        f"{workflow}: the step after the pause must be the scan's retry, guarded on the scan's outcome "
        "(outcome is the result before continue-on-error)"
    )
    assert retry["uses"] == first["uses"], f"{workflow}: the retry must run the same pinned action"
    assert retry["with"] == first["with"], f"{workflow}: the retry must scan the same image the same way"
    assert retry.get("env") == _RETRY_DB, f"{workflow}: the retry must name ghcr.io as the only DB source"
    assert not retry.get("continue-on-error"), f"{workflow}: an outage of both sources must still fail the job"


def _gate_steps() -> list[tuple[int, dict]]:
    return [
        (i, s)
        for i, s in _trivy_steps("docker-tool.reusable.yml", "build-and-push")
        if s.get("if", "").startswith("startsWith(github.ref, 'refs/tags/')")
    ]


def test_the_release_gate_stays_blocking():
    gates = _gate_steps()
    assert len(gates) == 1, "exactly one tag-guarded gate; its retry is guarded on the gate's outcome"
    index, gate = gates[0]
    assert str(gate["with"]["exit-code"]) == "1", "the gate fails on a fixable CRITICAL"
    assert gate.get("id"), "the gate needs an id for its retry's guard"
    steps = _steps("docker-tool.reusable.yml", "build-and-push")
    pause, retry = steps[index + 1], steps[index + 2]
    guard = f"steps.{gate['id']}.outcome == 'failure'"
    assert pause.get("if") == guard and re.fullmatch(r"sleep \d+", str(pause.get("run", "")).strip()), (
        "the step after the gate may only pause, and only after a failed gate"
    )
    assert retry.get("if") == guard, "the retry runs exactly when the gate failed"
    assert retry["uses"] == gate["uses"] and retry["with"] == gate["with"], (
        "the retry must be the same gate: same pinned action, same inputs, exit-code 1"
    )
    assert not retry.get("continue-on-error"), "the retry must block: a fixable CRITICAL fails both"
    assert gate.get("continue-on-error") is True, "the first gate may fail into its retry"
