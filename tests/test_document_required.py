"""The frozen top-level contract: what `required` now accepts, and what it refuses.

WHY THIS EXISTS. atrium-project#54 froze `atrium_document.schema.json` at 1.0 by tightening a
top-level `required` that was `["schema_version", "doc_id"]` against seventeen declared
properties -- so a stage that ran, wrote nothing, and emitted a two-key file passed every gate in
the ecosystem.

Tightening a validator is only safe if you can name every producer it must keep accepting, and
the answer is not derivable from the schema: it lives in the call sites across five repos, each
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


def _unstamped() -> Dict[str, Any]:
    """`assembled` as a record that only ever had set_source() carries it: no `blocks` key at all
    (checked against a real alto-postprocess page_split/text_split record)."""
    return {
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
# Each entry names the call site it was traced from, as <repo>/<file>::<function> (line numbers
# drifted with every edit of the tools; the function does not). If you change one of those call
# sites so it emits a different shape, change it here in the same commit -- that is the whole
# point of the file.
VALID_SHAPES = {
    # alto-postprocess/page_split.py::main -- the scanned originator. set_source() deliberately does
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
        "assembled": _unstamped(),
    },
    # alto-postprocess/page_split.py::main again, for --method json-keys: the same call with the
    # JSON media type and the `ocr:generic` origin.
    "alto page_split, json-keys (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "d" * 64,
            "filename": "CTX000000015.json",
            "media_type": "application/json",
            "page_count": 2,
            "origin": "ocr:generic",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/text_split.py::main -- the --method text-lines originator (atrium-alto-
    # postprocess#31): source only, like page_split; `page_count` only for formats with real pages.
    "alto text_split (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "e" * 64,
            "filename": "CTX000000012.pdf",
            "media_type": "application/pdf",
            "page_count": 1,
            "origin": "ocr:pdf-text-layer",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/text_split.py::main for a born-digital input: a `digital-born-*` origin
    # hands the positional blocks to digital-convert, so every later stage of alto-postprocess
    # holds them back and this `source` stays the record's only contribution from that repo.
    "alto text_split, born-digital (source only, no positional block)": {
        **_FLOOR,
        "source": {
            "sha256": "f" * 64,
            "filename": "CTX000000010.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital-born-docx",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/extract_ALTO_2_TXT.py::main (and its four twins: extract_LytRdr_ALTO_2_TXT,
    # extract_LLM_ALTO_2_TXT, extract_JSON_2_TXT and, for --method text-lines, extract_TEXT_2_TXT)
    "alto extract (pages + content)": {
        **_FLOOR,
        "assembled": _stamp("pages", "content"),
        "pages": [{"page": "1"}],
        "content": {"text": "Náčrt sondy."},
    },
    # alto-postprocess/classify_TEXT.py::process_document
    "alto classify_TEXT (lines)": {
        **_FLOOR,
        "assembled": _stamp("lines"),
        "lines": [{"page": "1", "line": 0, "text": "Náčrt sondy.", "categ": "Clear"}],
    },
    # alto-postprocess/aggregate_STAT.py::main
    "alto aggregate_STAT (pages)": {
        **_FLOOR,
        "assembled": _stamp("pages"),
        "pages": [{"page": "1", "quality_score": 0.9, "quality_band": "Clear"}],
    },
    # page-classification/atrium_document_adapter.py::_write_one -- stage 1 of the scanned pipeline, and
    # it never calls set_source(). This is why `source` is NOT in the floor.
    "page-classification standalone": {
        **_FLOOR,
        "assembled": _stamp("page_categories", "pages", "derived_from"),
        "derived_from": {"classification": "CATEG/CTX000000001.csv"},
        "page_categories": {"1": "TEXT"},
        "pages": [{"page": "1", "category": "TEXT", "category_confidence": 0.98}],
    },
    # translator/main.py::process_single_file -- add_derived_from() is unconditional inside the `with`, so a
    # standalone translator record is seven keys, not six.
    "translator standalone": {
        **_FLOOR,
        "assembled": _stamp("translations", "derived_from"),
        "derived_from": {"translated_xml": "TRANSLATED/CTX000000001.alto.xml"},
        "translations": {"source_lang": "cs", "target_lang": "en", "backend": "lindat"},
    },
    # nlp-enrich/api_util/document_hook.py::run_document_hook -- both merges are unconditional, so both blocks
    # are present even when empty. An empty list is a contribution; no key is not.
    "nlp-enrich standalone (empty entities list)": {
        **_FLOOR,
        "assembled": _stamp("entities", "pages"),
        "entities": [],
        "pages": [],
    },
    # llm-enrich/llm_client_shared.py::write_document_record
    "llm-enrich standalone": {
        **_FLOOR,
        "assembled": _stamp("enrichment", "derived_from", "regenerable"),
        "derived_from": {"enriched": "KW_PER_DOC_LLM/CTX000000001_enriched.json"},
        "regenerable": {"markdown": {"from": "CTX000000001.document.json", "converter": "json_to_md@1.0"}},
        "enrichment": {"items": [], "summary": None, "topics": []},
    },
    # llm-enrich/api_util/digital_to_json.py::to_record -- the digital-born originator, which DOES call
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
    # llm-enrich/api_util/digital_to_json.py::to_record for a DOCX (llm-enrich#18), trimmed from a real
    # rich.docx record: no bbox and no canvas (a DOCX has no page geometry), a counted page_count,
    # and the layout cues in lines[].style -- heading_level, and `region` for the running header and
    # the footnote. `region` was written before the schema declared it (additionalProperties: true);
    # declaring it as a closed enum is only additive because this shape still validates.
    "digital-convert originator, DOCX with layout cues": {
        **_FLOOR,
        "source": {
            "sha256": "8" * 64,
            "filename": "rich.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital-born-docx",
            "page_count": 2,
        },
        "assembled": _stamp("pages", "lines", "content", "tables"),
        "pages": [
            {"page": "1", "page_index": 1, "quality_score": 1.0, "quality_band": "Clear"},
            {"page": "2", "page_index": 2, "quality_score": 1.0, "quality_band": "Clear"},
        ],
        "lines": [
            {
                "page": "1",
                "line": 0,
                "text": "Nálezová zpráva",
                "group_id": "hdr0-0",
                "style": {"region": "page_header"},
            },
            {"page": "1", "line": 1, "text": "Hradiště u Horní Mezi", "group_id": "p0", "style": {"heading_level": 1}},
            {"page": "1", "line": 2, "text": "Sonda II", "group_id": "p1", "style": {"bold": True}},
            {
                "page": "1",
                "line": 3,
                "text": "Katalog je v archivu.",
                "group_id": "fn1",
                "style": {"region": "footnote"},
            },
            {"page": "2", "line": 0, "text": "Nálezy", "group_id": "tbl0-r0c0"},
            {"page": "2", "line": 1, "text": "Strana 2", "group_id": "ftr0-0", "style": {"region": "page_footer"}},
        ],
        "content": {
            "text": "Hradiště u Horní Mezi\n\nSonda II\n\nKatalog je v archivu.\n\nNálezy",
            "reading_order": "layout",
        },
        "tables": [
            {
                "table_id": "t0",
                "page": "2",
                "caption": "",
                "n_rows": 1,
                "n_cols": 1,
                "group_id": "tbl0",
                "cells": [{"row": 0, "col": 0, "is_header": True, "group_id": "tbl0-r0c0"}],
            }
        ],
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
    # What `required` accepted before the freeze. nlp-enrich/tests/test_run_pipeline.py (the
    # `_fake_stage` of its --document-json-out test) wrote literally this.
    "today's two-key minimum": {"schema_version": "1.0", "doc_id": "CTX000000001"},
    # The issue's own words: "a stage that produces nothing still validates". finalize() already
    # prints WARNING - <program> contributed no block; this promotes it to a failure.
    # Live instance: alto-postprocess/classify_TEXT.py::process_document on an empty CSV, whose
    # hook call sits outside the `if not df.empty` guard.
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


def test_style_region_is_a_closed_enum():
    """`lines[].style.region` (llm-enrich#18) is declared as a closed enum, so a misspelled value
    is refused instead of silently rendering as body text.

    json_to_md treats an unknown region as body, which is the safe fallback for a record written
    before the declaration -- but for a producer it would hide the typo: the running header would
    reach the model inline, and back into content.text. The freeze's rule makes the narrowing
    additive: every producer already writes one of the three values (the DOCX shape above).
    """
    pytest.importorskip("jsonschema")
    shape = json.loads(json.dumps(VALID_SHAPES["digital-convert originator, DOCX with layout cues"]))
    assert _is_valid(shape)
    for wrong in ("sidebar", "header", "Page_Header"):
        shape["lines"][0]["style"]["region"] = wrong
        assert not _is_valid(shape), f"style.region {wrong!r} validates -- the enum has been widened or dropped"


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
