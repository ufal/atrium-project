"""tools/runbook_check.py — the runbook outline of the six service READMEs (issue #77, A.2).

Run: pytest tests/test_runbook_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import runbook_check as rc  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "docs" / "templates" / "skill" / "serviceREADME.template.md"

GOOD = """# Tool API service

## Quick start 🚀

```bash
docker run --rm -p 8000:8000 ghcr.io/ufal/atrium-tool-api:1.0.0
## not a heading: inside a fence
```

## Models and caches

None: the image is self-contained.

## Errors

| Code | `reason`         | Meaning          | What to do                 |
|------|------------------|------------------|----------------------------|
| 413  | `limit_exceeded` | over `a \\| b`   | raise `MAX_UPLOAD_MB`      |
| 502  | `null`           | `x | y` produced nothing | fix the input `detail` names |

## Partial results

`limits_applied`.

## Known limits (issue #77)

- none known.
"""


def test_a_readme_with_the_five_sections_and_a_fix_on_every_row_passes():
    assert rc.check_text(GOOD) == []


def test_each_missing_section_is_named():
    text = "# Tool\n\n## Endpoints\n\nnothing\n"
    assert rc.check_text(text) == [
        "no '## Start' section",
        "no '## Models and caches' section",
        "no '## Errors' section",
        "no '## Partial results' section",
        "no '## Known limits' section",
    ]


def test_an_error_table_without_the_fix_column_is_a_gap():
    text = GOOD.replace(" What to do                 |", "").replace("----------------------------|", "")
    text = text.replace(" raise `MAX_UPLOAD_MB`      |", "").replace(" fix the input `detail` names |", "")
    assert rc.check_text(text) == ["the error table has no 'What to do' column"]


def test_an_error_row_with_an_empty_fix_is_named():
    text = GOOD.replace("raise `MAX_UPLOAD_MB`", "                     ")
    assert rc.check_text(text) == ["error row '413 | `limit_exceeded`' has no 'What to do'"]


def test_headings_are_compared_without_emoji_or_a_bracketed_suffix():
    assert rc.heading_key("## Quick start 🚀") == "quick start"
    assert rc.heading_key("## Errors (issue #41)") == "errors"
    assert rc.heading_key("## Models and caches") == "models and caches"


def test_the_template_itself_follows_the_outline():
    """The template is what every README copies: it must pass its own check."""
    assert rc.check_text(TEMPLATE.read_text(encoding="utf-8")) == []


def test_the_cli_reports_a_gap_and_a_missing_readme(tmp_path, capsys):
    good = tmp_path / "atrium-good" / "service"
    good.mkdir(parents=True)
    (good / "README.md").write_text(GOOD, encoding="utf-8")
    (tmp_path / "atrium-empty").mkdir()

    code = rc.main(["--repos-root", str(tmp_path), "--repo", "atrium-good", "--repo", "atrium-empty"])

    out = capsys.readouterr().out
    assert code == 1
    assert "[runbook][OK]  atrium-good" in out
    assert "[runbook][GAP] atrium-empty" in out and "no service/README.md" in out
    assert "1/2 READMEs follow the runbook outline" in out


def test_the_cli_without_any_clone_is_a_usage_error(tmp_path):
    assert rc.main(["--repos-root", str(tmp_path / "nowhere")]) == 2
