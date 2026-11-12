"""The record schema 2.0 floor: what it accepts, and what it refuses (doc-schema-v2, atrium-project#84).

WHY THIS EXISTS. A validator change is safe only if you can name every producer it must keep
accepting, and that list is not derivable from the schema: it lives in the call sites of six
repositories. This file is that enumeration for record schema 2.0, executable. The POSITIVE cases
are the shapes the 2.0 producers write — the record builder (ocr-postprocess) from the stored
docproc of each producer, the enrichment steps, a standalone run with no seed (rule 3) — and the
NEGATIVE cases are the defects the floor exists to catch, including everything 2.0 removed.

Read it as the answer to "may I change the schema?": you may, if every positive case here still
passes and you have moved a producer to the negative list on purpose.

The 1.x shapes are kept as data in tests/document_shapes_v1.py: tests/test_schema_freeze_records.py
checks them against the frozen `doc-schema-v1` copy and their migration to 2.0. The committed
worked example is pinned by tests/test_fixture_schema.py; the E2E's half of the gate lives in
tools/e2e/e2e_assert.py.

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


#: The three keys `DocumentRecord.to_dict()` emits on every path.
_FLOOR: Dict[str, Any] = {"schema_version": "2.0", "record_type": "atrium-document", "doc_id": "CTX000000001"}

_SEED_SOURCE = {"sha512": "a" * 128, "filename": "CTX000000001.pdf", "media_type": "application/pdf"}


def _page(index: int, status: str = "text", **extra: Any) -> Dict[str, Any]:
    row = {
        "page": str(index),
        "page_index": index,
        "canvas": {"width": 595.0, "height": 842.0, "unit": "pt"},
        "content_status": status,
    }
    row.update(extra)
    return row


def _line(page: str, line: int, text: str, source: str, precision: str, **extra: Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "page": page,
        "line": line,
        "text": text,
        "block": f"p{page}-b0",
        "text_source": source,
        "bbox_precision": precision,
    }
    if precision != "absent":
        row["bbox"] = [72.0, 100.0 + 14 * line, 400.0, 112.0 + 14 * line]
    row.update(extra)
    return row


# ── the shapes 2.0 producers write ───────────────────────────────────────────
VALID_SHAPES: Dict[str, Dict[str, Any]] = {
    # The AMČR seed (atrium-project#71, H1): identity only. Valid input to every tool.
    "AMČR seed": {**_FLOOR, "source": dict(_SEED_SOURCE)},
    # The record builder on the ATR's docproc of a scanned document: block-level boxes, lines
    # derived from blocks; one page empty (D29, rule 7).
    "record builder, scanned (ATR docproc)": {
        **_FLOOR,
        "source": {**_SEED_SOURCE, "language": ["cs"], "page_count": 2, "origin": "atr"},
        "pages": [_page(1, quality_score=0.81, quality_band="Clear"), _page(2, "empty")],
        "content": {"text": "Hradiště u Horní Mezi"},
        "lines": [
            _line("1", 1, "Hradiště u Horní Mezi", "atr", "derived", categ="Clear", quality_score=0.81, lang="cs")
        ],
        "quality_summary": {
            "pages": {"total": 2, "empty": 1, "scored": 1, "mean": 0.81, "median": 0.81, "min": 0.81, "max": 0.81},
            "lines": {"total": 1, "by_categ": {"Clear": 1}},
        },
    },
    # The same on digital-convert's docproc of a born-digital PDF: measured line boxes.
    "record builder, born-digital (digital-convert docproc)": {
        **_FLOOR,
        "source": {**_SEED_SOURCE, "page_count": 1, "origin": "digital"},
        "pages": [_page(1, canvas={"width": 612.0, "height": 792.0, "unit": "pt", "user_unit": 1})],
        "content": {"text": "Zpráva o výzkumu"},
        "lines": [
            _line("1", 1, "Zpráva o výzkumu", "text-layer", "measured", categ="Clear", quality_score=0.97, lang="cs")
        ],
    },
    # A mixed document (H6, D21): exact text-layer lines on a good page linked to the ATR block that
    # contains them; ATR lines on the page that needed ATR; a figure's OCR child block.
    "record builder, mixed (both producers' lines)": {
        **_FLOOR,
        "source": {**_SEED_SOURCE, "page_count": 2, "origin": "atr"},
        "pages": [_page(1), _page(2)],
        "content": {"text": "Úvod\nPlán sondy 1"},
        "lines": [
            _line("1", 1, "Úvod", "text-layer", "measured", categ="Clear"),
            _line("2", 1, "Plán sondy 1", "atr", "derived", block="p2-b3.t0", categ="Noisy"),
        ],
    },
    # The one-off PCSS converter's docproc, an original that could not be matched: px canvas.
    "record builder, legacy PCSS (px)": {
        **_FLOOR,
        "source": {**_SEED_SOURCE, "origin": "legacy"},
        "pages": [_page(1, canvas={"width": 2480, "height": 3508, "unit": "px"})],
        "lines": [_line("1", 1, "Nálezová zpráva", "legacy", "measured", categ="Clear")],
    },
    # Rule 3: a standalone run of the builder, no seed: its own part only, no source.
    "record builder standalone (no seed)": {
        **_FLOOR,
        "pages": [_page(1)],
        "lines": [_line("1", 1, "Text", "atr", "absent")],
        "content": {"text": "Text"},
    },
    # page-classification standalone, keyed by the physical page (H2, H3).
    "page-classification standalone": {
        **_FLOOR,
        "page_categories": {"1": "TEXT"},
        "pages": [{"page_index": 1, "category": "TEXT", "category_confidence": 0.97}],
    },
    "nlp-enrich standalone (empty entities list)": {**_FLOOR, "entities": []},
    "keyword-extract statistical keywords (keywords block)": {
        **_FLOOR,
        "lines": [{"page": "1", "line": 1, "text": "Hradiště u Horní Mezi", "categ": "Clear"}],
        "keywords": {
            "document": [
                {"keyword": "hradiště", "method": "yake", "score": 1.0, "rank": 1},
                {"keyword": "horní mez", "method": "yake", "score": 0.42, "rank": 2},
            ],
            "pages": [{"page": "1", "keywords": [{"keyword": "hradiště", "method": "yake", "score": 1.0, "rank": 1}]}],
        },
    },
    "keyword-extract both kinds (keywords beside enrichment)": {
        **_FLOOR,
        "keywords": {"document": [{"keyword": "sonda", "method": "keybert", "score": 0.64, "rank": 1}], "pages": []},
        "enrichment": {
            "items": [
                {
                    "page": "1",
                    "extracted_keywords_cs": ["hradiště"],
                    "extracted_keywords_en": ["hillfort"],
                    "teater_category": "hradiště",
                    "confidence_score": 0.9,
                    "citation": "[Source: CTX000000001, Page 1]",
                }
            ]
        },
    },
    "quality summary, nothing scored": {
        **_FLOOR,
        "pages": [_page(1, "empty")],
        "quality_summary": {"pages": {"total": 1, "empty": 1, "scored": 0}, "lines": {"total": 0, "by_categ": {}}},
    },
    "merge_document_records output": {**_FLOOR, "record_type": "atrium-document-merged", "source": dict(_SEED_SOURCE)},
    # Rule 6: a newer 2.x minor's block passes a tool that vendored this schema.
    "a newer 2.x minor's block": {
        **_FLOOR,
        "schema_version": "2.1",
        "source": dict(_SEED_SOURCE),
        "newer_block": {"x": 1},
    },
}


def _with(label: str, path: tuple, value: Any) -> Dict[str, Any]:
    record = json.loads(json.dumps(VALID_SHAPES[label]))
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return record


# ── the defects the floor refuses ────────────────────────────────────────────
_SCAN = "record builder, scanned (ATR docproc)"
INVALID_SHAPES: Dict[str, Dict[str, Any]] = {
    "the two-key minimum": {"schema_version": "2.0", "doc_id": "CTX000000001"},
    # A stage that ran and wrote nothing: no source, no block.
    "a stage that contributed nothing": dict(_FLOOR),
    "record_type missing": {"schema_version": "2.0", "doc_id": "CTX000000001", "entities": []},
    # A 1.x record must be migrated before it is checked against 2.0.
    "a 1.x record": {**_FLOOR, "schema_version": "1.0", "source": dict(_SEED_SOURCE)},
    # D1, D2, D19, D26: run data, licence, forms and tables are gone.
    "run data: provenance": _with(_SCAN, ("provenance",), {"license": "CC BY-NC 4.0", "contributors": []}),
    "run data: assembled stamps": _with(_SCAN, ("assembled",), {"blocks": {"pages": {"program": "ocr-postprocess"}}}),
    "run data: derived_from": _with(_SCAN, ("derived_from",), {"teitok": "TEITOK/x.teitok.xml"}),
    "run data: regenerable": _with(_SCAN, ("regenerable",), {"markdown": {}}),
    "layout: tables": _with(_SCAN, ("tables",), []),
    "forms": _with(_SCAN, ("forms",), {}),
    "layout: content.reading_order": _with(_SCAN, ("content", "reading_order"), "ltr-columns"),
    "layout: lines[].style": _with(_SCAN, ("lines", 0, "style"), {"bold": True}),
    "layout: lines[].group_id": _with(_SCAN, ("lines", 0, "group_id"), "g1"),
    "page verdict: needs_ocr": _with(_SCAN, ("pages", 0, "needs_ocr"), True),
    "page verdict: text_layer": _with(_SCAN, ("pages", 0, "text_layer"), "digital"),
    "page verdict: ocr engine": _with(_SCAN, ("pages", 0, "ocr"), {"engine": "pero"}),
    "a sha256 on the source": _with(_SCAN, ("source", "sha256"), "b" * 64),
    # D18 rule 2: categ holds the five categories only.
    "a decode verdict as a category": _with(_SCAN, ("lines", 0, "categ"), "Garbage"),
    # H2: every page row carries its physical page number.
    "a page row without page_index": {**_FLOOR, "pages": [{"page": "1", "content_status": "text"}]},
    # D25: a box says how it was obtained; `absent` means none.
    "a box without its precision": {**_FLOOR, "lines": [{"page": "1", "line": 1, "text": "x", "bbox": [0, 0, 1, 1]}]},
    "an absent box that is there": _with(_SCAN, ("lines", 0, "bbox_precision"), "absent"),
    # D18 rule 7: an empty page has no page score.
    "a scored empty page": _with(_SCAN, ("pages", 1, "quality_score"), 0.2),
    # 2.0 numbers lines from 1 (they were 0- or 1-based in 1.x).
    "a line numbered from 0": _with(_SCAN, ("lines", 0, "line"), 0),
}


@pytest.mark.parametrize("label", sorted(VALID_SHAPES))
def test_every_shape_a_2_0_producer_writes_validates(label):
    _validate(VALID_SHAPES[label])


@pytest.mark.parametrize("label", sorted(INVALID_SHAPES))
def test_defect_shapes_are_refused(label):
    pytest.importorskip("jsonschema")
    assert not _is_valid(INVALID_SHAPES[label]), f"{label!r} validates, but the 2.0 floor exists to refuse it"


@pytest.mark.parametrize(
    "path, values",
    [
        (("source", "origin"), ("digital-born-pdf", "ABBYY-ALTO", "ocr:pero")),
        (("lines", 0, "text_source"), ("text_layer", "ocr", "")),
        (("lines", 0, "bbox_precision"), ("exact", "")),
        (("pages", 0, "content_status"), ("blank", "")),
        (("pages", 0, "canvas", "unit"), ("mm10", "inch1200")),
        (("lines", 0, "block"), ("block-3", "3")),
    ],
)
def test_the_new_fields_are_closed(path, values):
    """#84 §2: the new vocabularies are closed, so a producer's typo is refused, not stored."""
    pytest.importorskip("jsonschema")
    assert _is_valid(VALID_SHAPES[_SCAN])
    for wrong in values:
        assert not _is_valid(_with(_SCAN, path, wrong)), f"{'.'.join(map(str, path))}={wrong!r} validates"


def test_a_statistical_keyword_carries_its_method_score_and_rank():
    """Every statistical keyword says how it was found (atrium-project#73)."""
    pytest.importorskip("jsonschema")
    shape = json.loads(json.dumps(VALID_SHAPES["keyword-extract statistical keywords (keywords block)"]))
    assert _is_valid(shape)
    for field in ("keyword", "method", "score", "rank"):
        broken = json.loads(json.dumps(shape))
        del broken["keywords"]["pages"][0]["keywords"][0][field]
        assert not _is_valid(broken), f"a page keyword without {field!r} validates"
    for field, wrong in (("rank", 0), ("rank", 1.5), ("keyword", ""), ("score", "high")):
        broken = json.loads(json.dumps(shape))
        broken["keywords"]["document"][0][field] = wrong
        assert not _is_valid(broken), f"keyword {field}={wrong!r} validates"
    del shape["keywords"]["pages"]
    assert not _is_valid(shape), "a keywords block without `pages` validates"


def test_the_quality_summary_is_numbers():
    """`quality_summary` counts and averages; a statistic outside [0, 1] or a count below 0 is refused."""
    pytest.importorskip("jsonschema")
    shape = json.loads(json.dumps(VALID_SHAPES[_SCAN]))
    for path, wrong in (
        (("pages", "mean"), 1.5),
        (("pages", "total"), -1),
        (("pages", "empty"), -1),
        (("lines", "by_categ"), {"Clear": -2}),
    ):
        broken = json.loads(json.dumps(shape))
        broken["quality_summary"][path[0]][path[1]] = wrong
        assert not _is_valid(broken), f"quality_summary.{'.'.join(path)}={wrong!r} validates"


def test_the_floor_is_what_to_dict_guarantees():
    """`required` may name only keys `DocumentRecord.to_dict()` emits unconditionally."""
    from atrium_document import DocumentRecord, load_schema

    record = DocumentRecord("CTX000000001", "ocr-postprocess").to_dict()
    for key in load_schema()["required"]:
        assert key in record, f"schema requires {key!r} but a record that contributed nothing does not carry it"


def test_source_is_not_required():
    """Rule 3: a tool run with no seed and no baseline emits its own part, and most tools never call
    set_source(). The seed profile is what requires the archive's sha512 (atrium-project#71)."""
    from atrium_document import load_schema, seed_schema

    assert "source" not in load_schema()["required"]
    assert seed_schema()["properties"]["source"]["required"] == ["sha512", "filename", "media_type"]


def test_committed_example_still_validates():
    """Belt and braces with tests/test_fixture_schema.py."""
    fixture = _HUB_ROOT / "fixtures" / "atrium_document.example.json"
    _validate(json.loads(fixture.read_text(encoding="utf-8")))
