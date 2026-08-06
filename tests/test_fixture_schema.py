"""The committed example record must validate against the canonical schema (issue #10).

WHY THIS EXISTS. `fixtures/atrium_document.example.json` is what a maintainer reads
to learn the record format, and what `docs/document_schema.md` points at. Until now
**nothing** in CI validated it — the D4 finding is that `validate_document()` had zero
call sites anywhere, in any repo or in the hub's own E2E, so neither this fixture nor
real pipeline output was ever checked against
`docs/templates/shared/atrium_document.schema.json`.

It validates today; that was verified by hand during the review, which proves it was
true on one afternoon and preserves nothing. This test is the difference: the schema
and its worked example can no longer drift apart silently, in either direction — an
additive schema change that forgets the example, or an example edited to show a field
the schema does not allow.

The E2E's half of the same gate (validating REAL five-stage output) lives in
tools/e2e/e2e_assert.py; see tests/test_e2e_assert.py.

Run: pytest tests/test_fixture_schema.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SHARED = _HUB_ROOT / "docs" / "templates" / "shared"
_FIXTURE = _HUB_ROOT / "fixtures" / "atrium_document.example.json"

# The canonical module is not an installed package and not importable from the repo
# root, so the directory holding it goes on sys.path -- the same resolution the
# `shared-tests` job gets for free by running pytest from inside that directory.
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))


def _validate_document():
    """Imported lazily so a missing jsonschema skips rather than errors at collection."""
    from atrium_document import validate_document

    return validate_document


def test_example_fixture_exists():
    assert _FIXTURE.is_file(), f"{_FIXTURE} is the record format's worked example; it must exist"


def test_example_fixture_validates_against_the_canonical_schema():
    record = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    try:
        _validate_document()(record)
    except RuntimeError as exc:  # jsonschema absent -> the gate cannot run
        pytest.skip(f"jsonschema not installed: {exc}")


def test_example_fixture_carries_the_blocks_the_e2e_asserts():
    """The fixture doubles as the shape tools/e2e/e2e_assert.py checks for.

    A fixture that validates but omits, say, `translations` would let the E2E's
    assertions be "verified" against an example that cannot exercise them.
    """
    record = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for block in ("page_categories", "pages", "content", "entities", "translations", "enrichment"):
        assert block in record, f"example record is missing the {block!r} block"
    stamped = record.get("assembled", {}).get("blocks", {})
    assert "enrichment" in stamped, (
        "assembled.blocks must record enrichment's originating program -- that stamp is what "
        "e2e_assert.py uses to tell 'llm-enrich contributed' from 'the key happens to be there'"
    )


def test_schema_version_matches_the_module():
    """A record whose schema_version disagrees with the module is a versioning bug (rule 2)."""
    from atrium_document import SCHEMA_VERSION

    record = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert record["schema_version"] == SCHEMA_VERSION
