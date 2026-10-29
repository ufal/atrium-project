"""A Trivy DB outage costs one retry, not a release (atrium-project#72, 2026-10-29).

WHY THIS EXISTS. On 2026-10-26 the weekly image scan failed in digital-convert and keyword-extract
before scanning anything: `mirror.gcr.io/aquasec/trivy-db:2` answered 404 on a layer, and Trivy moves
to its second source (`ghcr.io`) only after an error it counts as temporary. The publishing job in
`docker-tool.reusable.yml` downloads the same DB after the images are pushed, so the same outage
during a tag would have failed the release.

Each report-only scan that downloads the DB is therefore `continue-on-error` and followed by one
retry from `ghcr.io` that is not. These tests hold, in both reusables:

  1. the first scan has an `id`, `continue-on-error: true` and `exit-code: "0"` (a failure there
     can only be Trivy failing to run, never a finding);
  2. the step right after it is the retry: guarded by `steps.<id>.outcome == 'failure'`, the same
     pinned action and inputs, `ghcr.io` as the only DB source, and not `continue-on-error`;
  3. the CVE release gate stays as it was: one blocking scan, no `continue-on-error`.

Parsed, not grepped: the comments above these steps quote the incident.
History: docs/decisions/docker-tool-reusable.md#trivy-db-retry

Run: pytest tests/test_trivy_db_retry.py
"""

from __future__ import annotations

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
def test_the_retry_follows_from_ghcr_and_still_fails_loudly(workflow, job):
    steps = _steps(workflow, job)
    index, first = _trivy_steps(workflow, job)[0]
    retry = steps[index + 1]
    assert retry.get("if") == f"steps.{first['id']}.outcome == 'failure'", (
        f"{workflow}: the step after the scan must be its retry, guarded on the scan's outcome "
        "(outcome is the result before continue-on-error)"
    )
    assert retry["uses"] == first["uses"], f"{workflow}: the retry must run the same pinned action"
    assert retry["with"] == first["with"], f"{workflow}: the retry must scan the same image the same way"
    assert retry.get("env") == _RETRY_DB, f"{workflow}: the retry must name ghcr.io as the only DB source"
    assert not retry.get("continue-on-error"), f"{workflow}: an outage of both sources must still fail the job"


def test_the_release_gate_is_unchanged():
    gates = [
        s
        for _, s in _trivy_steps("docker-tool.reusable.yml", "build-and-push")
        if s.get("if", "").startswith("startsWith(github.ref, 'refs/tags/')")
    ]
    assert len(gates) == 1, "exactly one blocking scan, on tags"
    gate = gates[0]
    assert str(gate["with"]["exit-code"]) == "1"
    assert not gate.get("continue-on-error"), "the CVE release gate must stay blocking"
