#!/usr/bin/env python3
"""
runbook_check.py — is each service's `service/README.md` a runbook an operator can follow
(hub issue #77, A.2)?

AMČR colleagues run the six services themselves in the S2 pilot, from the READMEs alone. The
outline (`docs/templates/skill/serviceREADME.template.md`, strategy Appendix D) gives every
service README five runbook sections; this tool checks that they are there and that the error
table says what to do about each error.

Checks
------
    sections   the five level-2 headings: Start ("Quick start" counts), Models and caches,
               Errors, Partial results, Known limits. An emoji or a "(issue #55)" after the
               heading text does not matter
    fix        the first table under "Errors" has a "What to do" column, and no row leaves it
               empty

Exit codes: 0 every repo passes · 1 a gap found · 2 usage error. stdlib-only, like the e2e tools.

Usage
-----
    python3 tools/runbook_check.py                          # the six repos beside the hub
    python3 tools/runbook_check.py --repo atrium-translator
    python3 tools/runbook_check.py --ref origin/test         # a ref instead of the working tree
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPOS = (
    "atrium-page-classification",
    "atrium-ocr-postprocess",
    "atrium-translator",
    "atrium-nlp-enrich",
    "atrium-keyword-extract",
    "atrium-digital-convert",
)

README = "service/README.md"

#: The five runbook sections, each with the heading texts that satisfy it (lower case).
SECTIONS = (
    ("Start", ("start", "quick start")),
    ("Models and caches", ("models and caches",)),
    ("Errors", ("errors",)),
    ("Partial results", ("partial results",)),
    ("Known limits", ("known limits",)),
)

FIX_COLUMN = "what to do"


def heading_key(line: str) -> str:
    """The comparable text of a `## ` heading: no emoji, no "(…)" suffix, lower case."""
    text = line[3:].strip()
    text = re.sub(r"\s*\(.*\)\s*$", "", text)
    text = re.sub(r"[^\w\s&-]", "", text)
    return " ".join(text.split()).lower()


def sections_of(text: str) -> dict:
    """Level-2 headings → the lines under each, up to the next level-2 heading."""
    sections, current, fence = {}, None, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            current = heading_key(line)
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _cells(row: str) -> list:
    """A Markdown table row's cells; `\\|` and pipes inside backticks stay in the cell."""
    cells, cell, code, i = [], "", False, 0
    body = row.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cell += "|"
            i += 2
            continue
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            cells.append(cell.strip())
            cell = ""
        else:
            cell += ch
        i += 1
    cells.append(cell.strip())
    return cells


def first_table(lines: list) -> list:
    """The first Markdown table in ``lines``, as lists of cells (separator row dropped)."""
    rows, started = [], False
    for line in lines:
        if line.lstrip().startswith("|"):
            started = True
            cells = _cells(line)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
        elif started:
            break
    return rows


def check_text(text: str) -> list:
    """The gaps of one README's text; empty when it passes."""
    gaps = []
    sections = sections_of(text)
    for name, keys in SECTIONS:
        if not any(key in sections for key in keys):
            gaps.append(f"no '## {name}' section")
    errors = sections.get("errors")
    if errors is None:
        return gaps
    table = first_table(errors)
    if not table:
        gaps.append("'## Errors' has no table")
        return gaps
    header = [c.lower() for c in table[0]]
    if FIX_COLUMN not in header:
        gaps.append("the error table has no 'What to do' column")
        return gaps
    col = header.index(FIX_COLUMN)
    for row in table[1:]:
        if col >= len(row) or not row[col]:
            gaps.append(f"error row '{' | '.join(row[:2])}' has no 'What to do'")
    return gaps


def read_readme(repo: Path, ref: str = None):
    """The README's text, from the working tree or from ``ref``; None when it is absent."""
    if ref is None:
        path = repo / README
        return path.read_text(encoding="utf-8") if path.is_file() else None
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{README}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout if proc.returncode == 0 else None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the six service READMEs against the runbook outline (#77).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="directory holding the tool repo clones (default: the hub's parent)",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        metavar="NAME",
        help="check only this repo (repeatable; default: all six service repos)",
    )
    parser.add_argument("--ref", default=None, help="read the README at this ref, not the working tree")
    parser.add_argument("--quiet", action="store_true", help="print only repos with gaps")
    args = parser.parse_args(argv)

    checked = failing = 0
    for name in args.repos or REPOS:
        repo = args.repos_root / name
        if not repo.is_dir():
            print(f"[runbook][SKIP] {name}: no clone at {repo}")
            continue
        checked += 1
        text = read_readme(repo, args.ref)
        where = f"{name}@{args.ref}" if args.ref else name
        gaps = [f"no {README}"] if text is None else check_text(text)
        if gaps:
            failing += 1
            print(f"\n[runbook][GAP] {where}")
            for gap in gaps:
                print(f"  - {gap}")
        elif not args.quiet:
            print(f"[runbook][OK]  {where}")

    if not checked:
        print("[runbook][FAIL] no repo clones found — pass --repos-root", file=sys.stderr)
        return 2
    print(f"\n[runbook] {checked - failing}/{checked} READMEs follow the runbook outline")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
