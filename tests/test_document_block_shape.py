"""A record whose list block is not a list of objects is refused, not crashed on (atrium-project#72).

WHY THIS EXISTS. `DocumentRecord._merge()` took ``list(record.get(name) or [])`` on trust. A
baseline whose `pages` was a string or an object became a list of characters or keys, and the merge
then failed on ``.get`` with an AttributeError: a 500 from digital-convert's service and a
traceback from its command line, found when each tool's two entry points were compared on
2026-10-29. Schema validation would refuse such a record, but the merge runs before it. The
module now raises `InvalidRecordError` (a ValueError, `reason = "invalid_record"`) before it
changes anything; the services answer it with 422 `invalid_record` (tests/test_atrium_service.py).

What still works as before: a missing, null or empty block is no rows, and a reader that only
looks (`ocr_handoff_pages`, `quality_summary`) ignores what is not a list.

Run: pytest tests/test_document_block_shape.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

_SHARED = Path(__file__).resolve().parents[1] / "docs" / "templates" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import atrium_document as ad  # noqa: E402

OCR = "alto-postprocess"


def _baseline(**blocks):
    return {"doc_id": "CTX000000042", "source": {"origin": "ABBYY-ALTO"}, **blocks}


@pytest.mark.parametrize(
    ("value", "kind"),
    [("1", "string"), ({"page": "1"}, "object"), (7, "number"), (True, "boolean")],
)
def test_a_block_that_is_not_a_list_is_refused_with_its_name_and_type(value, kind):
    baseline = _baseline(pages=value)
    doc = ad.DocumentRecord("CTX000000042", OCR, baseline=baseline)
    with pytest.raises(ad.InvalidRecordError, match=rf"'pages' block is a JSON {kind}, not a list"):
        doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}])
    assert doc.to_dict()["pages"] == value  # nothing was written
    assert "pages" not in doc.to_dict().get("assembled", {}).get("blocks", {})


def test_a_row_that_is_not_an_object_is_refused():
    doc = ad.DocumentRecord("CTX000000042", OCR, baseline=_baseline(pages=[{"page": "1"}, "2"]))
    with pytest.raises(ad.InvalidRecordError, match=r"row 1 of the record's 'pages' block is a JSON string"):
        doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}])


def test_the_error_is_a_value_error_with_the_services_reason():
    assert issubclass(ad.InvalidRecordError, ValueError)
    assert ad.InvalidRecordError.reason == "invalid_record"


@pytest.mark.parametrize("empty", [None, [], {}, ""])
def test_a_missing_or_empty_block_is_still_no_rows(empty):
    baseline = _baseline() if empty is None else _baseline(pages=empty)
    doc = ad.DocumentRecord("CTX000000042", OCR, baseline=baseline)
    doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}])
    assert doc.to_dict()["pages"] == [{"page": "1", "quality_band": "Clear"}]


def test_a_valid_block_merges_as_before():
    baseline = _baseline(pages=[{"page": "1", "quality_band": "Noisy"}, {"page": "2"}])
    kept = copy.deepcopy(baseline)
    doc = ad.DocumentRecord("CTX000000042", OCR, baseline=baseline)
    doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}, {"page": "3", "quality_band": "Clear"}])
    assert [r["page"] for r in doc.to_dict()["pages"]] == ["1", "2", "3"]
    assert doc.to_dict()["pages"][0]["quality_band"] == "Clear"
    assert baseline == kept  # the baseline handed in is never rewritten


def test_replace_page_rows_refuses_a_pages_block_that_is_not_a_list_before_it_writes():
    baseline = _baseline(pages="1", lines=[{"page": "1", "line": 0, "text": "old"}])
    doc = ad.DocumentRecord("CTX000000042", OCR, baseline=baseline)
    with pytest.raises(ad.InvalidRecordError, match=r"'pages' block is a JSON string"):
        doc.replace_page_rows("lines", ["1"], [{"page": "1", "line": 0, "text": "new"}])
    assert doc.to_dict()["lines"] == [{"page": "1", "line": 0, "text": "old"}]


def test_the_readers_that_only_look_ignore_what_is_not_a_list():
    assert ad.ocr_handoff_pages("1") == [] and ad.ocr_handoff_pages(7) == []
    assert ad.ocr_handoff_pages({"page": "1", "needs_ocr": True}) == []
    assert ad.quality_summary({"pages": 7})["pages"]["total"] == 0
