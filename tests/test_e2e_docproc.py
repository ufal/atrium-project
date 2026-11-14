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
