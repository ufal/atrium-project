"""The record's one line key (`$defs/line_key`) and its check (atrium-project#84, round 8).

`lines[]` rows are keyed by `page` and `line`; an `entities[]` or `enrichment.items[]` row names its
line by the same pair, and `validate_document()` refuses a reference to a line the record does not
have (`line_key_problems()`). A record without `lines[]` has no line to name and is not checked.

Run: pytest tests/test_document_line_key.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

_SHARED = Path(__file__).resolve().parents[1] / "docs" / "templates" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

jsonschema = pytest.importorskip("jsonschema")

from atrium_document import line_key_problems, migrate_document, validate_document  # noqa: E402

_RECORD: Dict[str, Any] = {
    "schema_version": "2.0",
    "record_type": "atrium-document",
    "doc_id": "CTX000000001",
    "source": {"sha512": "a" * 128, "origin": "atr"},
    "pages": [{"page": "1", "page_index": 1, "content_status": "text"}],
    "lines": [
        {"page": "1", "line": 1, "text": "Hradiště u Horní Mezi", "text_source": "atr", "bbox_precision": "absent"},
        {"page": "1", "line": 2, "text": "Praha", "text_source": "atr", "bbox_precision": "absent"},
    ],
    "entities": [{"surface": "Praha", "page": "1", "line": 2, "char_span": [0, 5]}],
    "enrichment": {"items": [{"page": "1", "line": 1, "extracted_keywords_cs": ["hradiště"]}, {"page": "1"}]},
}


def _with(path: tuple, value: Any) -> Dict[str, Any]:
    record = copy.deepcopy(_RECORD)
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return record


def test_references_that_resolve_pass():
    assert line_key_problems(_RECORD) == []
    validate_document(_RECORD)


@pytest.mark.parametrize(
    "path, value",
    [
        (("entities", 0, "line"), 3),
        (("entities", 0, "page"), "2"),
        (("enrichment", "items", 0, "line"), 9),
    ],
    ids=["entity line", "entity page", "enrichment item line"],
)
def test_a_reference_to_a_missing_line_is_refused(path, value):
    record = _with(path, value)
    assert len(line_key_problems(record)) == 1
    with pytest.raises(jsonschema.ValidationError, match="name no lines"):
        validate_document(record)


def test_keys_compare_as_merge_block_compares_them():
    """An integer page names the row of its label, as `_key_value` aligns rows."""
    assert line_key_problems(_with(("entities", 0, "page"), 1)) == []


@pytest.mark.parametrize(
    "path, value",
    [
        (("entities", 0, "line"), 0),
        (("enrichment", "items", 0, "line"), 0),
        (("enrichment", "items", 1), {"line": 1}),
        (("enrichment", "items", 1), {"page": None, "line": 1}),
    ],
    ids=["entity line 0", "enrichment line 0", "enrichment line without its page", "enrichment line, null page"],
)
def test_the_schema_holds_the_key_shape(path, value):
    with pytest.raises(jsonschema.ValidationError):
        validate_document(_with(path, value))


def test_a_record_without_lines_has_nothing_to_resolve():
    record = {k: v for k, v in copy.deepcopy(_RECORD).items() if k not in ("lines", "pages")}
    assert line_key_problems(record) == []
    validate_document(record)


def test_an_item_without_a_line_is_not_a_reference():
    record = _with(("enrichment", "items"), [{"page": None, "summary_hint": "document level"}])
    assert line_key_problems(record) == []


def test_migration_keeps_references_with_their_lines():
    """1.x: a page numbered from 0 shifts its lines, entities and enrichment items alike; a 1.x
    `line` of 0 on a page numbered from 1 meant "unknown" and goes."""
    v1 = {
        "schema_version": "1.0",
        "record_type": "atrium-document",
        "doc_id": "CTX000000002",
        "lines": [
            {"page": "1", "line": 0, "text": "a"},
            {"page": "1", "line": 1, "text": "b"},
            {"page": "2", "line": 1, "text": "c"},
        ],
        "entities": [
            {"surface": "a", "page": "1", "line": 0, "char_span": [0, 1]},
            {"surface": "c", "page": "2", "line": 0, "char_span": [0, 1]},
        ],
        "enrichment": {"items": [{"page": "1", "line": 1}, {"page": "2", "line": 0}]},
    }
    migrated = migrate_document(v1)
    assert [(e["page"], e.get("line")) for e in migrated["entities"]] == [("1", 1), ("2", None)]
    assert [(i["page"], i.get("line")) for i in migrated["enrichment"]["items"]] == [("1", 2), ("2", None)]
    assert line_key_problems(migrated) == []
    assert v1["entities"][0]["line"] == 0, "the migration works on a copy"
