"""Which pages page-classification classifies (atrium-project#84 decision 4; shared
`atrium_page_selection`): the forced pages, in either producer's docproc, and the pages with figure
blocks (decision 6).

Run: pytest tests/test_page_selection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SHARED = Path(__file__).resolve().parents[1] / "docs" / "templates" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import atrium_page_selection as sel  # noqa: E402


def _page(number, *types, needs_atr=False):
    page = {
        "pageNumber": number,
        "blocks": [{"id": f"p{number}-b{i}", "type": t, "readingOrder": i} for i, t in enumerate(types)],
    }
    if needs_atr:
        page["needsAtr"] = True
    return page


def digital_convert():
    """digital-convert's docproc: page 2 forced, page 3 shows a photo, page 4 is text only."""
    return {
        "version": "1.0",
        "pages": [_page(1, "paragraph"), _page(2, needs_atr=True), _page(3, "paragraph", "figure"), _page(4, "table")],
        "metadata": {
            "routing": {
                "pages": [
                    {"page": 1, "route": "text-layer"},
                    {"page": 2, "route": "atr"},
                    {"page": 3, "route": "text-layer"},
                    {"page": 4, "route": "text-layer"},
                    {"page": 5, "route": "empty"},
                ]
            }
        },
    }


def atr(echo=True):
    """The ATR's docproc of the same document: every page routed `atr`, page 2 echoed as forced."""
    routing = [{"page": n, "route": "atr"} for n in (1, 2, 3, 4)]
    if echo:
        routing[1].update(forced=True, forced_reason="no text layer")
    return {
        "version": "1.0",
        "pipeline": "pipeline-e2e",
        "pages": [_page(1, "text"), _page(2, "figure", "text"), _page(3, "text", "image"), _page(4, "table")],
        "metadata": {"routing": {"pages": routing}},
    }


def test_digital_converts_forced_pages_come_from_needs_atr_and_route():
    assert sel.forced_pages(digital_convert()) == [2]


def test_the_atrs_forced_pages_are_the_echo_not_its_routes():
    assert sel.forced_pages(atr()) == [2]
    assert sel.forced_pages(atr(echo=False)) == []


def test_figure_pages_read_figure_image_and_chart_blocks():
    assert sel.figure_pages(digital_convert()) == [3]
    assert sel.figure_pages(atr()) == [2, 3]


def test_the_selection_is_forced_and_figure_pages():
    assert sel.select_pages(digital_convert()) == [2, 3]
    assert sel.select_pages(atr()) == [2, 3]
    assert sel.select_pages_of([digital_convert(), atr(echo=False)]) == [2, 3]


def test_a_rule_has_a_statement_and_an_unknown_rule_fails():
    assert "not selected" in sel.rule_statement(sel.FORCED_AND_FIGURES)
    assert set(sel.RULES) == {"forced+figures", "explicit", "all"}
    with pytest.raises(ValueError):
        sel.rule_statement("graphics")


def test_the_pages_as_page_classification_takes_them():
    assert sel.as_page_list([3, 2, 3]) == "2,3"
