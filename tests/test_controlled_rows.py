"""Tests for tools/e2e/controlled_rows.py — the line count the E2E lane's paid step gates on.

`e2e-pipeline-smoke.yml` calls keyword-extract's controlled kind (one third-party model call per
line) only on a record of at most `E2E_CONTROLLED_MAX_LINES` lines. The first version of the gate
counted `lines[]`, which is 0 for a record that holds its text in `content.text` alone, as the
chain's record can (the OCR stage runs with `SKIP_CLASSIFY=true`): the service would have sent
every line of `content.text` for the 372- and 485-row fixtures. These tests pin the count to what
the service sends.

Run: pytest tests/test_controlled_rows.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "e2e"))

from controlled_rows import rows_sent  # noqa: E402


def _line(text, categ="Clear", n=1):
    return {"page": "1", "line": n, "text": text, "categ": categ}


def test_a_record_with_lines_counts_the_lines_that_have_text():
    record = {"lines": [_line("První řádek.", n=1), _line("", n=2), _line("  ", n=3), _line("Třetí.", n=4)]}
    assert rows_sent(record) == 2


def test_a_record_with_text_in_content_only_counts_its_non_empty_lines():
    """The case the first gate got wrong: no `lines[]`, so it read 0."""
    record = {"content": {"text": "Nadpis\n\nPrvní odstavec.\n   \nDruhý odstavec.\n"}}
    assert rows_sent(record) == 3


def test_content_is_what_the_service_reads_when_every_line_is_untrustworthy():
    record = {
        "lines": [_line("xX#%", categ="Garbage"), _line("zzz", categ="Trash", n=2), _line("", categ="Empty", n=3)],
        "content": {"text": "Skutečný text.\nDruhá věta."},
    }
    assert rows_sent(record) == 2


def test_one_trusted_line_makes_the_lines_the_rows_and_the_skipped_ones_are_counted_too():
    """They are context for the service, and it drops them by category itself; the count is an upper bound."""
    record = {
        "lines": [_line("Dobrý řádek."), _line("šum", categ="Garbage", n=2)],
        "content": {"text": "a\nb\nc\nd\ne"},
    }
    assert rows_sent(record) == 2


@pytest.mark.parametrize("record", [{}, {"lines": []}, {"content": {}}, {"content": None}, {"lines": [None, "x"]}])
def test_a_record_with_no_text_is_zero(record):
    assert rows_sent(record) == 0


def test_the_script_prints_the_number(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"content": {"text": "a\nb"}}), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "e2e" / "controlled_rows.py"), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert done.stdout.strip() == "2"
