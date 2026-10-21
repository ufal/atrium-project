"""tools/docs_check.py — links, anchors and headings of the tool repositories' docs (issue #79, E).

Run: pytest tests/test_docs_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import docs_check as dc  # noqa: E402

GOOD_README = """# atrium-tool: lines from pages

What it does.

## Quick start

```bash
# a comment, not a heading
curl --fail-with-body -sS localhost:8000/info
```

## Configuration ⚙️

See [the service](service/README.md#errors) and [below](#documentation).

## Documentation

| To | Read |
|----|------|
| operate it | [service/README.md](service/README.md) |

Style: [documentation-style.md](https://github.com/ufal/atrium-project/blob/main/docs/documentation-style.md).

[^n]: a footnote, not a link definition.
"""


def _repo(tmp_path: Path, files: dict) -> Path:
    repo = tmp_path / "atrium-tool"
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    return repo


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [
        ("Configuration", "configuration"),
        ("⚙️ Configuration", "️-configuration"),  # the emoji goes, its U+FE0F stays
        ("Step 4: Classify (text) quality & language", "step-4-classify-text-quality--language"),
        ("`OUTPUT_DIR/paradata/` — run logs", "output_dirparadata--run-logs"),
        ("[Linked](x.md) title", "linked-title"),
    ],
)
def test_github_anchor(heading, anchor):
    assert dc.github_anchor(dc.heading_text(heading)) == anchor


def test_duplicate_headings_get_numbered_anchors():
    assert {"usage", "usage-1", "usage-2"} <= dc.anchors_of("## Usage\n\n## Usage\n\n## Usage\n")


def test_a_clean_repository_passes(tmp_path):
    repo = _repo(tmp_path, {"README.md": GOOD_README.replace(" ⚙️", ""), "service/README.md": "# API\n\n## Errors\n"})
    errors, warnings = dc.check_repo(repo)
    assert errors == [] and warnings == []


def test_emoji_headings_are_errors_but_fenced_lines_are_not(tmp_path):
    repo = _repo(tmp_path, {"README.md": GOOD_README, "service/README.md": "# API\n\n## Errors\n"})
    errors, _ = dc.check_repo(repo)
    assert errors == ["README.md:12: emoji in heading 'Configuration ⚙️'"]


def test_broken_links_and_anchors(tmp_path):
    readme = GOOD_README.replace(" ⚙️", "") + (
        "\n[gone](docs/missing.md) · [no such section](service/README.md#limits) · "
        "[old emoji anchor](#-quick-start) · [fine](#quick-start) · [web](https://example.org/x.md)\n"
    )
    repo = _repo(tmp_path, {"README.md": readme, "service/README.md": "# API\n\n## Errors\n"})
    errors, _ = dc.check_repo(repo)
    assert any("missing file: docs/missing.md" in e for e in errors)
    assert any("anchor in service/README.md#limits" in e for e in errors)
    assert any("anchor in #-quick-start" in e for e in errors)
    assert len(errors) == 3


def test_a_readme_without_a_map_or_guide_link(tmp_path):
    repo = _repo(tmp_path, {"README.md": "# atrium-tool\n\n## Usage\n\nText.\n"})
    errors, _ = dc.check_repo(repo)
    assert "README.md: no 'Documentation' section (the documentation map)" in errors
    assert any("documentation-style.md" in e for e in errors)


def test_a_long_readme_is_a_warning(tmp_path):
    long_readme = GOOD_README.replace(" ⚙️", "") + "\nline\n" * 260
    repo = _repo(tmp_path, {"README.md": long_readme, "service/README.md": "# API\n\n## Errors\n"})
    errors, warnings = dc.check_repo(repo)
    assert errors == [] and warnings and "lines" in warnings[0]


def test_dev_logs_and_sample_documents_are_not_checked(tmp_path):
    repo = _repo(
        tmp_path,
        {
            "README.md": GOOD_README.replace(" ⚙️", ""),
            "service/README.md": "# API\n\n## Errors\n",
            "agent_dev_logs/DEVLOG.md": "## 📓 log\n[x](nowhere.md)\n",
            "data_samples/TEXT/doc.md": "# 📄 A converted report\n[plan](plan.pdf)\n",
            "data_samples/README.md": "# Samples\n",
        },
    )
    assert dc.check_repo(repo) == ([], [])


def test_main_exit_codes(tmp_path, capsys):
    clean = _repo(tmp_path, {"README.md": GOOD_README.replace(" ⚙️", ""), "service/README.md": "# API\n\n## Errors\n"})
    assert dc.main(["--repos-root", str(tmp_path), "--repo", clean.name]) == 0
    (clean / "README.md").write_text("# atrium-tool\n", encoding="utf-8")
    assert dc.main(["--repos-root", str(tmp_path), "--repo", clean.name]) == 1
    assert dc.main(["--repos-root", str(tmp_path / "none"), "--repo", "atrium-x"]) == 2
