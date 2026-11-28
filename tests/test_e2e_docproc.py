"""Tests for the E2E lanes' docproc tools (atrium-project#84): `tools/e2e/docproc_assert.py`, which checks a
docproc before the record is built from it, and `tools/e2e/alto_to_docproc.py`, which writes the scanned
lane's stand-in for the ATR from its ALTO fixtures.

Run: pytest tests/test_e2e_docproc.py
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _HUB_ROOT / "fixtures" / "e2e"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HUB_ROOT / "tools" / "e2e" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


da = _load("docproc_assert")
a2d = _load("alto_to_docproc")


def _digital():
    """A born-digital docproc as digital-convert writes it: two pages, the second for the ATR."""
    return {
        "version": "1.1",
        "pipeline": "pipeline-e2e",
        "processedAt": "2026-11-14T00:00:00Z",
        "pages": [
            {"pageNumber": 1, "width": 595, "height": 842, "needsAtr": False, "blocks": []},
            {"pageNumber": 2, "width": 595, "height": 842, "needsAtr": True, "blocks": []},
        ],
        "metadata": {"routing": {"pages": [{"page": 1, "route": "text-layer"}, {"page": 2, "route": "atr"}]}},
    }


def test_a_sound_docproc_holds():
    assert da.check(_digital(), expect_atr="2") == []


def test_every_page_is_routed_and_needs_atr_agrees():
    doc = _digital()
    doc["metadata"]["routing"]["pages"].pop()
    assert any("not in metadata.routing" in p for p in da.check(doc))
    doc = _digital()
    doc["pages"][1]["needsAtr"] = False
    assert any("disagrees" in p for p in da.check(doc))


def test_the_atrs_own_docproc_carries_no_needs_atr():
    doc = _digital()
    for page in doc["pages"]:
        del page["needsAtr"]
    doc["metadata"]["routing"]["pages"][0]["route"] = "atr"
    assert da.check(doc, expect_atr="all") == []


@pytest.mark.parametrize("key", ["run_uuid", "license", "provenance"])
def test_run_data_or_a_licence_in_docproc_fails(key):
    doc = _digital()
    doc["pages"][0]["blocks"].append({"id": "p1-b0", key: "x"})
    assert any("run data or a licence" in p for p in da.check(doc))


def test_the_expected_atr_pages_are_checked():
    assert any("expected [1, 2]" in p for p in da.check(_digital(), expect_atr="all"))
    assert any("expected []" in p for p in da.check(_digital(), expect_atr="none"))


def test_the_schema_is_applied():
    pytest.importorskip("jsonschema")
    schema = {"type": "object", "required": ["version", "sourceHash"]}
    assert any("sourceHash" in p for p in da.check(_digital(), schema=schema))


def test_the_command_says_which_check_failed(tmp_path, capsys):
    path = tmp_path / "d.docproc.json"
    path.write_text(json.dumps(_digital()), encoding="utf-8")
    assert da.main([str(path), "--expect-atr-pages", "2"]) == 0
    assert da.main([str(path), "--expect-atr-pages", "none"]) == 1
    assert "expected []" in capsys.readouterr().out


def test_the_stand_in_is_the_atrs_shape_and_current():
    """The committed stand-ins are what the tool writes from the committed ALTO (`--check`)."""
    altos = sorted((_FIXTURES / "ALTO").glob("*.alto.xml"))
    assert altos
    assert a2d.main([*map(str, altos), "--out-dir", str(_FIXTURES / "docproc"), "--check"]) == 0
    doc = a2d.convert(_FIXTURES / "ALTO" / "CTX000000003.alto.xml")
    assert doc["pipeline"].startswith("pipeline-e2e") and doc["sourceFormat"] == "pdf-scanned"
    (page,) = doc["pages"]
    assert (page["pageNumber"], page["coordinateUnit"]) == (1, "px")
    assert page["blocks"][0]["content"] == "Náčrt sondy.\n1998", "a line break per visual line (ask 7)"
    assert doc["metadata"]["routing"]["pages"] == [{"page": 1, "route": "atr", "text_layer": False}]
    assert da.check(copy.deepcopy(doc), expect_atr="all") == []


def test_a_stale_stand_in_is_reported(tmp_path):
    alto = _FIXTURES / "ALTO" / "CTX000000003.alto.xml"
    (tmp_path / "CTX000000003.atr.docproc.json").write_text("{}\n", encoding="utf-8")
    assert a2d.main([str(alto), "--out-dir", str(tmp_path), "--check"]) == 1


def test_an_empty_page_with_a_pages_entry_fails():
    """H5, D29: a page routed `empty` has no `pages[]` entry."""
    doc = _digital()
    doc["metadata"]["routing"]["pages"][1]["route"] = "empty"
    doc["pages"][1]["needsAtr"] = False
    assert any("routed 'empty' but has a pages[] entry" in p for p in da.check(doc))


def test_the_stand_in_leaves_an_empty_page_out_of_pages():
    doc = a2d.convert(_FIXTURES / "ALTO" / "CTX192601143.alto.xml")
    empty = [row["page"] for row in doc["metadata"]["routing"]["pages"] if row["route"] == "empty"]
    assert empty and not {page["pageNumber"] for page in doc["pages"]} & set(empty)
    assert da.check(doc, expect_atr="all") == []


# ── the ATR's stand-in on a mixed document (`atr_standin.py`, H6) ───────────────────────────────

ats = _load("atr_standin")


def _mixed_digital():
    """digital-convert's docproc of a three-page report: page 2 a pasted scan for the ATR."""

    def block(page, n, text, box):
        return {
            "id": f"p{page}-b{n}",
            "type": "paragraph",
            "bbox": box,
            "readingOrder": n,
            "content": text,
            "lines": [{"text": text, "bbox": box, "bboxPrecision": "measured"}],
        }

    return {
        "version": "1.1",
        "sourceFormat": "docx",
        "documentLanguage": "cs",
        "pages": [
            {
                "pageNumber": 1,
                "width": 595.3,
                "height": 841.9,
                "coordinateUnit": "pt",
                "textLayer": "digital",
                "blocks": [
                    block(1, 0, "Nálezová zpráva", [72, 70, 250, 90]),
                    block(1, 1, "Na následující straně je plán.", [72, 100, 400, 112]),
                    block(1, 2, "Strana 1", [280, 800, 320, 810]),
                ],
            },
            {
                "pageNumber": 2,
                "width": 595.3,
                "height": 841.9,
                "coordinateUnit": "pt",
                "textLayer": "none",
                "needsAtr": True,
                "needsAtrReason": "the rendered page shows text the document's text does not place there",
                "blocks": [],
            },
        ],
        "metadata": {
            "routing": {
                "pages": [
                    {"page": 1, "route": "text-layer", "text_layer": True},
                    {"page": 2, "route": "atr", "text_layer": False},
                    {"page": 3, "route": "empty", "text_layer": False},
                ]
            }
        },
    }


def test_the_stand_in_has_the_atrs_own_blocks_and_echoes_the_force():
    doc = ats.standin(_mixed_digital(), {2: ["Plán sondy S1", "M 1:50"]})
    assert doc["pipeline"].startswith("pipeline-e2e") and doc["sourceFormat"] == "pdf-digital"
    page1, page2 = doc["pages"]
    assert [b["id"] for b in page1["blocks"]] == ["p1-b0", "p1-b1"], "two text blocks become one ATR block"
    assert page1["blocks"][0]["content"] == "Nálezová zpráva\nNa následující straně je plán."
    assert page1["blocks"][0]["bbox"] == [72, 70, 400, 112]
    assert all("lines" not in b for b in page1["blocks"]), "the ATR writes no block lines"
    assert (page1["width"], page1["height"], page1["coordinateUnit"]) == (595.3, 841.9, "pt")
    figure, child = page2["blocks"]
    assert (figure["type"], child["id"], child["parent"]) == ("figure", "p2-b0.t0", "p2-b0")
    assert child["content"] == "Plán sondy S1\nM 1:50"
    assert doc["metadata"]["routing"]["pages"] == [
        {"page": 1, "route": "atr", "text_layer": True},
        {
            "page": 2,
            "route": "atr",
            "text_layer": False,
            "forced": True,
            "forced_reason": "the rendered page shows text the document's text does not place there",
        },
        {"page": 3, "route": "empty", "text_layer": False},
    ]
    assert da.check(doc, expect_atr="all", expect_forced="2") == []


def test_the_stand_in_keeps_a_text_layer_pages_figure():
    """#84 decision 6: a picture on a text-layer page is a `figure` block in digital-convert's docproc; the
    ATR's docproc has it too (its own, with an `imageRef`), so page-classification reads the page."""
    digital = _mixed_digital()
    digital["pages"][0]["blocks"].insert(
        2, {"id": "p1-b3", "type": "figure", "bbox": [72, 200, 300, 400], "readingOrder": 3, "confidence": 1.0}
    )
    digital["pages"][0]["blocks"].append({"id": "p1-b4", "type": "figure", "readingOrder": 4, "confidence": 1.0})
    doc = ats.standin(digital, {2: ["Plán sondy S1"]})
    blocks = doc["pages"][0]["blocks"]
    assert [(b["id"], b["type"]) for b in blocks] == [("p1-b0", "text"), ("p1-b1", "text"), ("p1-b2", "figure")]
    assert blocks[2]["bbox"] == [72, 200, 300, 400] and blocks[2]["imageRef"] == "assets/p1-b2.png"
    assert blocks[1]["content"] == "Strana 1", "a figure ends the text pair before it"
    assert da.check(doc, expect_atr="all", expect_forced="2", expect_figures="1,2") == []


def test_a_forced_page_without_ocr_text_comes_out_empty():
    doc = ats.standin(_mixed_digital(), {})
    assert [p["pageNumber"] for p in doc["pages"]] == [1]
    assert doc["metadata"]["routing"]["pages"][1] == {
        "page": 2,
        "route": "empty",
        "text_layer": False,
        "forced": True,
        "forced_reason": "the rendered page shows text the document's text does not place there",
    }


def test_the_stand_in_refuses_a_document_with_no_page_for_the_atr(tmp_path, capsys):
    digital = _mixed_digital()
    del digital["pages"][1]
    del digital["metadata"]["routing"]["pages"][1]
    path = tmp_path / "d.docproc.json"
    path.write_text(json.dumps(digital), encoding="utf-8")
    assert ats.main([str(path), "--out", str(tmp_path / "out.json")]) == 1
    assert "no mixed document" in capsys.readouterr().err


def test_the_expected_forced_pages_are_checked():
    doc = ats.standin(_mixed_digital(), {2: ["Plán"]})
    assert any("forced pages [2], expected []" in p for p in da.check(doc, expect_forced="none"))


def test_the_pages_with_figure_blocks_are_checked(tmp_path):
    """#84 decisions 4 and 6: what a page shows is its blocks; the pages with a `figure` block are, with
    the forced pages, the pages for page-classification."""
    doc = _digital()
    doc["pages"][1]["blocks"] = [{"id": "p2-b0", "type": "figure", "bbox": [0, 0, 595, 842], "readingOrder": 0}]
    assert da.check(doc, expect_figures="2") == []
    assert any("figure blocks are [2], expected []" in p for p in da.check(doc, expect_figures="none"))
    docproc = tmp_path / "d.docproc.json"
    docproc.write_text(json.dumps(doc), encoding="utf-8")
    assert da.main([str(docproc), "--expect-figure-pages", "2"]) == 0
    assert da.main([str(docproc), "--expect-figure-pages", "1"]) == 1


def test_digital_converts_figure_block_holds_no_picture():
    """Answer 12: digital-convert's figure block (its docproc has no `pipeline`) has a box and nothing of
    the picture: no `lines`, `content` or `imageRef`. The ATR's may carry an `imageRef`."""
    doc = _digital()
    figure = {"id": "p2-b0", "type": "figure", "bbox": [0, 0, 595, 842], "readingOrder": 0, "imageRef": "assets/x.png"}
    doc["pages"][1]["blocks"] = [figure]
    assert da.check(doc) == [], "the ATR's docproc"
    del doc["pipeline"]
    assert any("carries ['imageRef']" in p for p in da.check(doc))


def test_a_routing_entry_that_says_what_a_page_shows_fails():
    """Ask 14 is withdrawn (#84 decision 6): `graphics` and `tables` stay out of docproc."""
    doc = _digital()
    doc["metadata"]["routing"]["pages"][1].update(graphics=1, tables=0)
    assert any("routing carries ['graphics', 'tables']" in p for p in da.check(doc))
