"""The frozen top-level contract: what `required` now accepts, and what it refuses.

WHY THIS EXISTS. atrium-project#54 froze `atrium_document.schema.json` at 1.0 by tightening a
top-level `required` that was `["schema_version", "doc_id"]` against seventeen declared
properties -- so a stage that ran, wrote nothing, and emitted a two-key file passed every gate in
the ecosystem.

Tightening a validator is only safe if you can name every producer it must keep accepting, and
the answer is not derivable from the schema: it lives in ten call sites across five repos, each
of which emits a different subset of blocks. This file is that enumeration, executable. The
POSITIVE cases are the record shapes production code actually writes, traced from those call
sites; the NEGATIVE cases are the four defect classes the freeze exists to catch.

Read it as the answer to "may I add a key to `required`?" -- you may, if every positive case here
still passes, and you have added the producer you are about to exclude to the negative list on
purpose. A change that reds a positive case is a behaviour change to a shipped tool, not a
schema tidy-up.

The E2E's half of the same gate (validating REAL five-stage output) lives in
tools/e2e/e2e_assert.py; the committed worked example is pinned by tests/test_fixture_schema.py.

Run: pytest tests/test_document_required.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SHARED = _HUB_ROOT / "docs" / "templates" / "shared"

# Same resolution as tests/test_fixture_schema.py: the canonical module is not an installed
# package and not importable from the repo root.
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))


def _validate(record: Dict[str, Any]) -> None:
    from atrium_document import validate_document

    try:
        validate_document(record)
    except RuntimeError as exc:  # jsonschema absent -> the gate cannot run
        pytest.skip(f"jsonschema not installed: {exc}")


def _is_valid(record: Dict[str, Any]) -> bool:
    import jsonschema

    from atrium_document import load_schema

    try:
        jsonschema.validate(record, load_schema())
        return True
    except jsonschema.ValidationError:
        return False


def _stamp(*names: str) -> Dict[str, Any]:
    """An `assembled` block stamped for `names`, shaped exactly as `_stamp()` writes it."""
    return {
        "blocks": {
            n: {
                "program": "p",
                "run_id": "260909-000000",
                "paradata_ref": "",
                "updated_at": "2026-09-09T00:00:00+00:00",
            }
            for n in names
        },
        "had_baseline": False,
        "note": "Blocks reflect CONTRIBUTED steps only; a block is absent until its tool has run.",
    }


#: The five keys `DocumentRecord.to_dict()` emits on every path, with no branch that can skip one.
#: `schema_version`/`record_type` are setdefault in __init__, `doc_id` is assigned there
#: unconditionally, and `to_dict()` itself always assigns `provenance` and `assembled`.
_FLOOR: Dict[str, Any] = {
    "schema_version": "1.0",
    "record_type": "atrium-document",
    "doc_id": "CTX000000001",
    "provenance": {"license": "CC BY-NC 4.0", "license_url": "https://x", "contributors": []},
}


# ── the shapes production code actually writes ────────────────────────────────
#
# Each entry names the call site it was traced from. If you change one of those call sites so it
# emits a different shape, change it here in the same commit -- that is the whole point of the
# file.
VALID_SHAPES = {
    # alto-postprocess/page_split.py:540 -- the scanned originator. set_source() deliberately does
    # NOT stamp, so this record has no `assembled.blocks` key at all. It is the reason the schema
    # says "source OR a stamped block" rather than "a stamped block".
    "alto page_split (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "a" * 64,
            "filename": "CTX000000001.alto.xml",
            "media_type": "application/alto+xml",
            "page_count": 1,
            "origin": "ABBYY-ALTO",
        },
        "assembled": _stamp(),
    },
    # alto-postprocess/extract_ALTO_2_TXT.py:194 (and its three twins)
    "alto extract (pages + content)": {
        **_FLOOR,
        "assembled": _stamp("pages", "content"),
        "pages": [{"page": "1"}],
        "content": {"text": "Náčrt sondy."},
    },
    # alto-postprocess/classify_TEXT.py:1109
    "alto classify_TEXT (lines)": {
        **_FLOOR,
        "assembled": _stamp("lines"),
        "lines": [{"page": "1", "line": 0, "text": "Náčrt sondy.", "categ": "Clear"}],
    },
    # alto-postprocess/aggregate_STAT.py:322
    "alto aggregate_STAT (pages)": {
        **_FLOOR,
        "assembled": _stamp("pages"),
        "pages": [{"page": "1", "quality_score": 0.9, "quality_band": "Clear"}],
    },
    # page-classification/atrium_document_adapter.py:163 -- stage 1 of the scanned pipeline, and
    # it never calls set_source(). This is why `source` is NOT in the floor.
    "page-classification standalone": {
        **_FLOOR,
        "assembled": _stamp("page_categories", "pages", "derived_from"),
        "derived_from": {"classification": "CATEG/CTX000000001.csv"},
        "page_categories": {"1": "TEXT"},
        "pages": [{"page": "1", "category": "TEXT", "category_confidence": 0.98}],
    },
    # translator/main.py:414 -- add_derived_from() is unconditional inside the `with`, so a
    # standalone translator record is seven keys, not six.
    "translator standalone": {
        **_FLOOR,
        "assembled": _stamp("translations", "derived_from"),
        "derived_from": {"translated_xml": "TRANSLATED/CTX000000001.alto.xml"},
        "translations": {"source_lang": "cs", "target_lang": "en", "backend": "lindat"},
    },
    # nlp-enrich/api_util/document_hook.py:292 -- both merges are unconditional, so both blocks
    # are present even when empty. An empty list is a contribution; no key is not.
    "nlp-enrich standalone (empty entities list)": {
        **_FLOOR,
        "assembled": _stamp("entities", "pages"),
        "entities": [],
        "pages": [],
    },
    # llm-enrich/llm_client_shared.py:1190
    "llm-enrich standalone": {
        **_FLOOR,
        "assembled": _stamp("enrichment", "derived_from", "regenerable"),
        "derived_from": {"enriched": "KW_PER_DOC_LLM/CTX000000001_enriched.json"},
        "regenerable": {"markdown": {"from": "CTX000000001.document.json", "converter": "json_to_md@1.0"}},
        "enrichment": {"items": [], "summary": None, "topics": []},
    },
    # llm-enrich/api_util/digital_to_json.py:770 -- the digital-born originator, which DOES call
    # set_source() first, deliberately.
    "digital-convert originator": {
        **_FLOOR,
        "source": {"sha256": "b" * 64, "media_type": "application/pdf", "origin": "digital-born-pdf"},
        "assembled": _stamp("pages", "lines", "content", "tables"),
        "pages": [{"page": "1", "page_index": 1}],
        "lines": [{"page": "1", "line": 0, "text": "t"}],
        "content": {"text": "t"},
        "tables": [{"table_id": "t1", "page": "1"}],
    },
    # atrium_document.merge_document_records() -- record_type differs, and `blocks` may legitimately
    # be {} when every input was a source-only record. That is why minProperties lives inside the
    # anyOf branch rather than on assembled.blocks itself.
    "merge_document_records output (source-only inputs)": {
        **_FLOOR,
        "record_type": "atrium-document-merged",
        "source": {"sha256": "c" * 64},
        "assembled": {"blocks": {}, "merged_from": 2, "merged_at": "2026-09-09T00:00:00+00:00", "note": "…"},
    },
}


# ── the defect classes the freeze exists to catch ─────────────────────────────
INVALID_SHAPES = {
    # What `required` accepted before the freeze. nlp-enrich/tests/test_run_pipeline.py:156 wrote
    # literally this.
    "today's two-key minimum": {"schema_version": "1.0", "doc_id": "CTX000000001"},
    # The issue's own words: "a stage that produces nothing still validates". finalize() already
    # prints WARNING - <program> contributed no block; this promotes it to a failure.
    # Live instance: alto-postprocess/classify_TEXT.py:1109 on an empty CSV, whose hook call sits
    # outside the `if not df.empty` guard.
    "a stage that contributed nothing (no source, no stamp)": {**_FLOOR, "assembled": _stamp()},
    # A stamp is written by _stamp(), which only runs where the payload is written in the same
    # call -- so a stamp without a payload cannot come from the module. It means the record was
    # hand-built, truncated in transit, or field-filtered down to nothing.
    "stamp without payload": {**_FLOOR, "assembled": _stamp("lines")},
    "record_type missing": {
        k: v for k, v in {**_FLOOR, "assembled": _stamp("pages"), "pages": []}.items() if k != "record_type"
    },
    "provenance missing": {
        k: v for k, v in {**_FLOOR, "assembled": _stamp("pages"), "pages": []}.items() if k != "provenance"
    },
}


@pytest.mark.parametrize("label", sorted(VALID_SHAPES))
def test_every_shape_production_writes_still_validates(label):
    """A tightened `required` must not exclude a shape a shipped tool emits.

    This is the half that matters. The E2E gates validate records produced by PUBLISHED :latest
    images, and :latest only moves on a version tag -- so excluding a real producer here cannot be
    fixed from `test`; it costs a release cycle in the owning repo.
    """
    _validate(VALID_SHAPES[label])


@pytest.mark.parametrize("label", sorted(INVALID_SHAPES))
def test_defect_shapes_are_refused(label):
    pytest.importorskip("jsonschema")
    assert not _is_valid(INVALID_SHAPES[label]), (
        f"{label!r} validates, but the #54 freeze exists to refuse it -- "
        f"the top-level required/anyOf/allOf has been widened"
    )


def test_the_floor_is_what_to_dict_guarantees():
    """`required` may name only keys `DocumentRecord.to_dict()` emits unconditionally.

    Checked against the module rather than restated, so the two cannot drift: a future edit that
    makes one of these conditional has to fail here rather than in a pipeline.
    """
    from atrium_document import DocumentRecord, load_schema

    record = DocumentRecord("CTX000000001", "alto-postprocess").to_dict()
    for key in load_schema()["required"]:
        assert key in record, (
            f"schema requires {key!r} but a record that contributed nothing does not carry it -- "
            f"either to_dict() changed or required was widened past what it guarantees"
        )


def test_source_is_not_required():
    """Four of the five tools never call set_source(); one of them runs first.

    page-classification, translator, nlp-enrich and llm-enrich have no set_source() call on any
    path, and page-classification is stage 1 of the scanned pipeline. Requiring `source` would
    refuse a legitimate rule-3 standalone run of most of the ecosystem.
    """
    from atrium_document import load_schema

    assert "source" not in load_schema()["required"]


def test_committed_example_still_validates():
    """Belt and braces with tests/test_fixture_schema.py: the freeze must not orphan the example."""
    fixture = _HUB_ROOT / "fixtures" / "atrium_document.example.json"
    _validate(json.loads(fixture.read_text(encoding="utf-8")))
