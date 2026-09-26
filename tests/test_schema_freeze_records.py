"""The freeze, checked where only the hub can check it: the tag, the changelog, and real records.

WHY THIS EXISTS. The structural half of the #54 freeze -- the frozen copy is the tagged blob,
nothing declared at the freeze was removed, every change since is registered -- lives in
docs/templates/shared/test_schema_freeze.py, and is vendored so every tool repo runs it against its
own copy of the schema. Three checks cannot travel with it:

  * the TAG. Only this repository carries `doc-schema-v1`, and CI checks out one commit with no
    tags, so the check runs wherever the tag is present (a clone after `git fetch --tags`) and
    skips elsewhere. The frozen copy's pinned blob id is what binds CI to the tag.
  * the CHANGELOG. Every register entry names the date of its `## Changelog — <date>` section in
    docs/document_schema.md, which is a hub document.
  * RECORDS. "Additive" means, operationally, that every record a shipped tool writes is valid
    under the frozen schema AND the current one: a consumer that knows only the frozen contract
    can read everything the ecosystem writes, and a record written before a post-freeze change
    still validates after it. The shapes are tests/test_document_required.py's enumeration, which
    is hub-only, and validating them needs jsonschema.

The register itself is not repeated here: it is read from the shared file, so there is one.

Run: pytest tests/test_schema_freeze_records.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SHARED = _HUB_ROOT / "docs" / "templates" / "shared"
_CANONICAL_IN_REPO = "docs/templates/shared/atrium_document.schema.json"
_SCHEMA_DOC = _HUB_ROOT / "docs" / "document_schema.md"
_EXAMPLE = _HUB_ROOT / "fixtures" / "atrium_document.example.json"

# Same resolution as tests/test_fixture_schema.py: the canonical module is not an installed
# package and not importable from the repo root.
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))


def _load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The shared freeze test: FREEZES, POST_FREEZE_CHANGES and the frozen copy's locator.
_FREEZE = _load_by_path("_shared_schema_freeze", _SHARED / "test_schema_freeze.py")
#: tests/test_document_required.py: VALID_SHAPES / INVALID_SHAPES, the one enumeration of what
#: producers write and what the floor refuses.
_SHAPES = _load_by_path("_document_required_shapes", Path(__file__).with_name("test_document_required.py"))


def _schemas() -> Dict[str, Dict[str, Any]]:
    from atrium_document import load_schema

    return {"frozen": _FREEZE.load_snapshot(_FREEZE.current_freeze()), "current": load_schema()}


def _validator(schema: Dict[str, Any]):
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator(schema)


def _git(*args: str) -> Optional[str]:
    if shutil.which("git") is None:
        return None
    proc = subprocess.run(["git", *args], cwd=_HUB_ROOT, capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


# ── the tag ───────────────────────────────────────────────────────────────────


def test_the_freeze_tag_has_not_moved():
    """Where the tag is present, it still names the frozen commit and the frozen file.

    Skipped in CI, whose checkout carries no tags; run `git fetch --tags` to make it bite locally.
    """
    freeze = _FREEZE.current_freeze()
    commit = _git("rev-parse", "--verify", "--quiet", f"{freeze['tag']}^{{commit}}")
    if commit is None:
        pytest.skip(f"tag {freeze['tag']} not available here (shallow or tagless checkout)")
    assert commit == freeze["commit"], (
        f"{freeze['tag']} points at {commit}, not {freeze['commit']}. A freeze tag is never moved: "
        f"put it back, and cut a new MAJOR's tag for a new contract"
    )
    assert _git("rev-parse", f"{freeze['tag']}:{_CANONICAL_IN_REPO}") == freeze["blob"]


# ── the changelog ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("prefix", sorted(_FREEZE.POST_FREEZE_CHANGES))
def test_every_registered_change_has_its_changelog(prefix):
    date = _FREEZE.POST_FREEZE_CHANGES[prefix]["changelog"]
    heading = re.compile(r"^## Changelog — " + re.escape(date) + r"\b", re.MULTILINE)
    assert heading.search(_SCHEMA_DOC.read_text(encoding="utf-8")), (
        f"{prefix} is registered under changelog {date}, but docs/document_schema.md has no "
        f"'## Changelog — {date}' section"
    )


# ── records: what producers write meets the frozen contract ────────────────────


@pytest.mark.parametrize("label", sorted(_SHAPES.VALID_SHAPES))
def test_every_production_shape_validates_under_the_freeze_and_now(label):
    """A record a shipped tool writes is valid under the frozen schema AND the current one -- the
    check behind the 2026-09-25 changelog's "validates against both"."""
    record = _SHAPES.VALID_SHAPES[label]
    for name, schema in _schemas().items():
        errors = sorted(e.message for e in _validator(schema).iter_errors(record))
        assert not errors, f"{label!r} fails the {name} schema: {errors}"


def test_the_committed_example_validates_under_the_freeze_and_now():
    record = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    for name, schema in _schemas().items():
        errors = sorted(e.message for e in _validator(schema).iter_errors(record))
        assert not errors, f"fixtures/atrium_document.example.json fails the {name} schema: {errors}"


@pytest.mark.parametrize("label", sorted(_SHAPES.INVALID_SHAPES))
def test_the_floor_refuses_under_the_freeze_and_now(label):
    """The freeze's floor (required + anyOf + allOf) refuses the same defects in both schemas."""
    record = _SHAPES.INVALID_SHAPES[label]
    for name, schema in _schemas().items():
        assert not _validator(schema).is_valid(record), f"{label!r} validates under the {name} schema"
