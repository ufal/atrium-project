"""No hub workflow may start a published image as anything but itself (issue #62, roadmap B9).

WHY THIS EXISTS. `e2e-pipeline-smoke.yml` is the ecosystem's only end-to-end lane, and
for most of its life it replaced the entrypoint on four of its five stages. One of those
overrides was load-bearing: it wrapped Stage 2 in `/bin/sh -c` so the step could
`pip install` alto-tools from a moving `refs/heads/master.zip` INSIDE the
already-published image, overriding that image's own commit pin at the moment of testing
it. Whatever that lane proved, it was not a property of the artefact we ship. That was
roadmap B9, the last live §2.1 breakage.

The other three were worse in a quieter way. Each replaced the image's real ENTRYPOINT
with a command byte-identical in effect to the ENTRYPOINT it replaced -- exact no-ops
that cost nothing at runtime and everything in assurance. The lane reported that it
never exercised a real entrypoint; in three cases it silently did. Nobody could tell the
two situations apart by reading the file, which is why the issue was sized an order of
magnitude too large.

So the property this file defends is not "the overrides are gone today" -- `git log`
records that. It is that an override cannot come back SILENTLY. The issue's own wording
is the rule: *"Remove each override where the real entrypoint can now run the stage;
where it genuinely cannot, say why in a comment rather than leaving a silent override."*
ALLOWED_OVERRIDES below is that comment, in a form CI reads.

Two checks, both structural:

  1. No step's `run:` body overrides a container entrypoint, unless the (workflow, step)
     pair is in ALLOWED_OVERRIDES with a reason.
  2. No `docker run` command installs anything at run time -- the B9 defect itself.

WHY NOT THE ISSUE'S LITERAL GREP. #62's acceptance reads
`grep -c "pip install" .github/workflows/e2e-pipeline-smoke.yml` returns 1. That count
is correct today (`:115`, `pip install -r tools/e2e/requirements.txt`, which runs on the
RUNNER) and it is still the fastest way to eyeball the file -- but as a standing check it
is brittle in both directions: it goes red the day someone adds a second legitimate
runner-side install, and it would stay green if that one line moved INTO a container
command. Check 2 encodes the property B9 was actually about, and cannot be satisfied by
accident.

WHY THE WORKFLOWS ARE PARSED, NOT GREPPED. The prose ABOVE Stages 2 and 3 explains at
length what was removed and why, and a text scan would fire on that explanation --
punishing the file for documenting itself. PyYAML drops comments, so only executable
`run:` bodies are ever examined here. (The same reason the acceptance grep still returns
zero: those comments deliberately say "entrypoint override" and never spell the flag.)

Run: pytest tests/test_e2e_entrypoints.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_HUB_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW_DIR = _HUB_ROOT / ".github" / "workflows"

# Scoped to the workflows the hub actually RUNS. `docs/templates/workflows/` holds
# caller examples for the five tool repos; they call reusables and start no containers,
# and tools/ci/workflow_lint.py already owns their policy surface.
_WORKFLOW_GLOBS = ("*.yml", "*.yaml")

# (workflow file name, step `name:`) -> why the override is unavoidable.
#
# EMPTY ON PURPOSE, and that is the point: every stage in the E2E lane now runs its
# image as built. Adding an entry is how you declare that a stage genuinely cannot --
# with a reason a reviewer can weigh -- instead of leaving the override to be discovered
# by the next person auditing the lane. If you find yourself adding one, check first
# that the image's own ENTRYPOINT is not simply what you were about to hand-write:
# three of the four this file replaced were exactly that.
ALLOWED_OVERRIDES: dict[tuple[str, str], str] = {}

# `--entrypoint` as a whole token. The negative lookbehind keeps a longer flag that
# merely ends in the same letters from matching.
_ENTRYPOINT_FLAG = re.compile(r"(?<![\w-])--entrypoint(?![\w-])")
_DOCKER_RUN = re.compile(r"(?<![\w-])docker\s+run(?![\w-])")
_RUNTIME_INSTALL = re.compile(
    r"(?<![\w-])(?:pip3?\s+install|python3?\s+-m\s+pip\s+install|apt-get\s+install|apk\s+add)"
)


def _workflow_files() -> list[Path]:
    files: list[Path] = []
    for pattern in _WORKFLOW_GLOBS:
        files.extend(sorted(_WORKFLOW_DIR.glob(pattern)))
    return files


def _logical_lines(run_body: str) -> list[str]:
    """Join shell line-continuations so one command is one string.

    Stages 3 and 4 are folded scalars (`run: >`), which YAML has already collapsed into
    a single line; Stage 5 is a literal block (`run: |`) whose `docker run` spans a dozen
    backslash-continued lines. Both have to come out the same way, or a check that reads
    one command at a time sees half of it.
    """
    joined = re.sub(r"\\\n\s*", " ", run_body)
    return [line for line in joined.splitlines() if line.strip()]


def _steps(doc: object) -> list[tuple[str, str]]:
    """Every (step name, run body) in a workflow document.

    Jobs that only `uses:` a reusable have no `steps`, and steps that only `uses:` an
    action have no `run` -- both are skipped rather than assumed away, because a
    workflow of either shape used to raise here instead of passing.
    """
    if not isinstance(doc, dict):
        return []
    out: list[tuple[str, str]] = []
    for job in (doc.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if isinstance(run, str):
                out.append((str(step.get("name") or f"<unnamed step {index}>"), run))
    return out


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_no_undeclared_entrypoint_override(path: Path) -> None:
    """A container entrypoint override must be declared in ALLOWED_OVERRIDES with a reason."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))

    offenders = [
        (name, line.strip())
        for name, run in _steps(doc)
        for line in _logical_lines(run)
        if _ENTRYPOINT_FLAG.search(line) and (path.name, name) not in ALLOWED_OVERRIDES
    ]

    assert not offenders, (
        f"{path.name} overrides a container entrypoint in "
        f"{len(offenders)} step(s) without declaring why:\n"
        + "\n".join(f"  - {name}: {line}" for name, line in offenders)
        + "\n\nThe image's own ENTRYPOINT is what this lane exists to exercise. Delete the"
        "\noverride if the real entrypoint can run the stage -- for translator, nlp-enrich"
        "\nand llm-enrich it could, and the override was reproducing it verbatim. If it"
        "\ngenuinely cannot, add the (workflow, step) pair to ALLOWED_OVERRIDES in"
        "\ntests/test_e2e_entrypoints.py with the reason. (issue #62, roadmap B9)"
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_no_install_inside_a_container_run(path: Path) -> None:
    """`docker run` must not resolve dependencies at run time -- that is the B9 defect.

    Matched per LOGICAL line, so a legitimate runner-side `pip install` elsewhere in the
    same step is not implicated: only an install in the command handed to the container
    fails here.
    """
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))

    offenders = [
        (name, line.strip())
        for name, run in _steps(doc)
        for line in _logical_lines(run)
        if _DOCKER_RUN.search(line) and _RUNTIME_INSTALL.search(line)
    ]

    assert not offenders, (
        f"{path.name} installs a dependency INSIDE a published image at run time, in "
        f"{len(offenders)} step(s):\n"
        + "\n".join(f"  - {name}: {line}" for name, line in offenders)
        + "\n\nThis is the build/release/run violation roadmap B9 recorded: the artefact"
        "\nre-resolves its own pinned dependency at the moment we test it, so the run"
        "\nproves nothing about the image we ship. Put the dependency in the image's own"
        "\nrequirements and rebuild, or vendor it as alto-postprocess did for alto-tools."
        "\nRunner-side installs are fine -- they just must not be part of a container"
        "\ncommand. (issue #62, alto-postprocess#50)"
    )


def test_the_e2e_lane_is_actually_covered() -> None:
    """The lane this file was written for must be among the files scanned.

    Without this, renaming or moving `e2e-pipeline-smoke.yml` would leave both checks
    above passing vacuously over whatever remained -- a green tick measuring nothing,
    which is the failure mode this ecosystem has already been caught by twice.
    """
    names = {path.name for path in _workflow_files()}
    assert "e2e-pipeline-smoke.yml" in names, (
        "e2e-pipeline-smoke.yml is not in .github/workflows/. If it moved, point "
        "_WORKFLOW_DIR at its new home; if it was deleted, this file has no subject."
    )

    doc = yaml.safe_load((_WORKFLOW_DIR / "e2e-pipeline-smoke.yml").read_text(encoding="utf-8"))
    stages = [name for name, _ in _steps(doc) if name.startswith("Stage ")]
    assert len(stages) == 5, f"expected five pipeline stages, found {len(stages)}: {stages}"
