"""Tests for the pin check of scripts/revendor_shared.sh (atrium-project#72, 2026-10-28).

para-drift diffs a tool's vendored copies against the hub at the commit the tool pins (its
`hub-ref`), not against the hub checkout the copies came from. On 2026-10-28 the copies moved to
`5a996d3` while every caller still pinned `18f0668`, and para-drift went red in all six tools;
`revendor_shared.sh --check` had said they were in parity. The script now reads each tool's pins
(`scripts/pin_hub_reusables.py --print-pins`) and fails when the canonical files at a pinned
commit are not the ones in the checkout.

Self-contained: a scratch hub (the script, the pin reader, the manifest reader and the canonical
files) with two commits, and one scratch tool repository holding the second commit's copies.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from shared_manifest import load_manifest  # noqa: E402

TOOL = "atrium-example"
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.org",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.org",
}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def scratch(tmp_path):
    """(hub, sibling root, the commit before the change, the commit after it)."""
    if shutil.which("git") is None or shutil.which("bash") is None:
        pytest.skip("git and bash are needed")
    hub = tmp_path / "atrium-project"
    for rel in ("scripts/revendor_shared.sh", "scripts/pin_hub_reusables.py", "tools/shared_manifest.py"):
        (hub / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, hub / rel)
    shutil.copytree(REPO_ROOT / "docs" / "templates" / "shared", hub / "docs" / "templates" / "shared")
    _git(hub, "init", "-q")
    _git(hub, "add", "-A")
    _git(hub, "commit", "-q", "-m", "before")
    before = _git(hub, "rev-parse", "HEAD")
    changed = hub / "docs" / "templates" / "shared" / "atrium_rocrate.py"
    changed.write_text(changed.read_text(encoding="utf-8") + "\n# a later edit\n", encoding="utf-8")
    _git(hub, "commit", "-q", "-am", "after")
    after = _git(hub, "rev-parse", "HEAD")

    siblings = tmp_path / "siblings"
    tool = siblings / TOOL
    for entry in load_manifest(hub / "docs" / "templates" / "shared" / "MANIFEST.json"):
        dest = tool / entry["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hub / "docs" / "templates" / "shared" / entry["canonical"], dest)
        for precondition in entry.get("preconditions") or []:
            (tool / precondition).touch()
    return hub, siblings, before, after


def _pin(siblings: Path, sha: str) -> None:
    workflows = siblings / TOOL / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "para-drift.yml").write_text(
        "name: Paradata Canonical Drift\n"
        "on: push\n"
        "jobs:\n"
        "  check-drift:\n"
        f"    uses: ufal/atrium-project/.github/workflows/para-drift.reusable.yml@{sha}  # v1\n"
        "    with:\n"
        f"      hub-ref: {sha}\n",
        encoding="utf-8",
    )


def _check(hub: Path, siblings: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(hub / "scripts" / "revendor_shared.sh"), "--check", "--root", str(siblings), "--repo", TOOL],
        capture_output=True,
        text=True,
        check=False,
    )


def test_copies_pinned_to_their_own_commit_pass(scratch):
    hub, siblings, _before, after = scratch
    _pin(siblings, after)
    run = _check(hub, siblings)
    assert run.returncode == 0, run.stdout + run.stderr
    assert f"ok    {TOOL} @ {after[:12]}" in run.stdout


def test_copies_newer_than_the_pin_fail_and_name_the_command(scratch):
    hub, siblings, before, _after = scratch
    _pin(siblings, before)
    run = _check(hub, siblings)
    assert run.returncode == 1
    assert f"STALE {TOOL} @ {before[:12]}" in run.stdout
    assert "pin_hub_reusables.py --sha" in run.stdout


def test_a_pin_the_hub_does_not_have_fails(scratch):
    hub, siblings, _before, _after = scratch
    _pin(siblings, "0" * 40)
    run = _check(hub, siblings)
    assert run.returncode == 1
    assert "which this checkout does not have" in run.stdout
