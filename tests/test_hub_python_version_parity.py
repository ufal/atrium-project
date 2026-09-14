"""
tests/test_hub_python_version_parity.py — the hub side of the same guard.

`atrium-translator/tests/test_python_version_parity.py` (atrium-project#64) derives its
expected Python version from its own Dockerfile and checks every `python-version:`
literal in its own `.github/workflows/*.yml` against it. That closes the loop for a
caller's OWN workflow files — but every caller-side lane backed by a hub reusable is a
bare `uses:` with no `with:` block (`grep -rn python-version .github/workflows/*.yml`
across the five tool repos finds nothing to check), so the version those lanes actually
run is whatever the REUSABLE defaults to. A hub-side change to a `workflow_call` input's
`default:`, or to a hardcoded `python-version` inside a reusable, would be invisible to
every tool repo's own parity test — the exact "guard cannot see what it is supposed to
hold" pattern atrium-project#59 names for the canonical-file set, one level down for the
Python version.

There is no Dockerfile here to anchor "what production runs" — the hub ships no image.
The anchor is instead `docker-tool.reusable.yml`'s own hardcoded `Setup Python 3.11` step,
which builds and probes the actual container images (`FROM python:3.11-slim` in all five
tool repos) and so is closest to "the thing that has to match production" that the hub
has. Every other python-version declaration in the hub, hardcoded or as a workflow_call
default, is checked against that one anchor.

TWO SHAPES, not one. A version can appear either as a literal
`python-version: "3.11"` (a step's `with:` value, or a hardcoded caller-side pin) or as a
`default: "3.11"` on the line(s) following a bare `python-version:` input-declaration key
(`workflow_call.inputs.python-version.default`). `${{ inputs.python-version }}` template
expressions are neither — they carry no digits and are correctly invisible to both
patterns. An earlier draft of this file only matched the first shape and passed with a
`default: "3.12"` planted in `pre-commit.reusable.yml`'s `workflow_call` input — silently
measuring nothing for every one of the four reusables that take the version as an input,
which is the four this guard exists to cover. Caught by deliberately breaking it before
trusting it (the standard the rest of this round holds to); the corrected two-shape
version below is what stayed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
DOCKER_TOOL = WORKFLOWS_DIR / "docker-tool.reusable.yml"

_LITERAL_RE = re.compile(r'^\s*python-version:\s*["\']?(\d+\.\d+)["\']?\s*$', re.MULTILINE)
_INPUT_KEY_RE = re.compile(r"^\s*python-version:\s*$", re.MULTILINE)
_DEFAULT_RE = re.compile(r'^\s*default:\s*["\']?(\d+\.\d+)["\']?\s*$')


def _versions_in(text: str) -> list[str]:
    """Every python-version this workflow declares, literal or as an input default.

    A `${{ inputs.python-version }}` step value carries no digits and correctly
    matches neither pattern — it is a use of the version, not a declaration of it.
    """
    found = list(_LITERAL_RE.findall(text))
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _INPUT_KEY_RE.match(line):
            for j in range(i + 1, min(i + 5, len(lines))):
                match = _DEFAULT_RE.match(lines[j])
                if match:
                    found.append(match.group(1))
                    break
    return found


def _anchor_version() -> str:
    """The version docker-tool.reusable.yml's hardcoded PR-lane setup step pins.

    This is the lane that builds and container-probes the actual published images
    (`python:3.11-slim` in all five tool repos), so it is the closest thing the hub
    has to "the version production runs" — everything else in the hub is checked
    against it, not the other way round.
    """
    versions = _versions_in(DOCKER_TOOL.read_text())
    assert versions, f"no python-version found in {DOCKER_TOOL.name}; this check needs an anchor"
    literal_only = list(_LITERAL_RE.findall(DOCKER_TOOL.read_text()))
    assert literal_only, f"{DOCKER_TOOL.name}'s own version must be a literal, not an input default"
    return literal_only[0]


def test_anchor_is_3_11():
    """Pin the anchor itself, so a silent edit to docker-tool.reusable.yml is caught
    directly rather than only by comparison to itself (which would trivially pass)."""
    assert _anchor_version() == "3.11"


@pytest.mark.parametrize(
    "workflow",
    sorted(WORKFLOWS_DIR.glob("*.yml")),
    ids=lambda p: p.name,
)
def test_hub_workflow_python_matches_the_anchor(workflow: Path):
    expected = _anchor_version()
    mismatched = [v for v in _versions_in(workflow.read_text()) if v != expected]
    assert not mismatched, (
        f"{workflow.name} declares python-version {mismatched} but "
        f"docker-tool.reusable.yml's PR lane (the one that builds and probes the "
        f"published images) is {expected}. A reusable that drifts from this is "
        f"invisible to every tool repo's own parity test (atrium-project#64)."
    )


def test_every_workflow_call_python_input_has_a_default():
    """A python-version input with no default silently inherits nothing, which
    would make test_hub_workflow_python_matches_the_anchor blind to it above."""
    offenders = []
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        text = workflow.read_text()
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not _INPUT_KEY_RE.match(line):
                continue
            has_default = any(_DEFAULT_RE.match(lines[j]) for j in range(i + 1, min(i + 5, len(lines))))
            if not has_default:
                offenders.append(f"{workflow.name}:{i + 1}")
    assert not offenders, f"python-version input(s) with no default: {offenders}"


def test_ruff_target_version_matches_the_anchor():
    """The third place the version is declared, and the only one tooling reads."""
    expected = _anchor_version().replace(".", "")
    ruff = (REPO_ROOT / "ruff.toml").read_text()
    match = re.search(r'^target-version\s*=\s*"py(\d+)"', ruff, re.MULTILINE)
    assert match, "ruff.toml has no target-version; the anchor version is then asserted by nothing"
    assert match.group(1) == expected, (
        f"ruff.toml targets py{match.group(1)}, docker-tool.reusable.yml's anchor is {_anchor_version()}"
    )
