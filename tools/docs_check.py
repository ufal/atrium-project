#!/usr/bin/env python3
"""
docs_check.py — can a reader of a tool repository's documentation get where the links say
(hub issue #79, E)?

The documentation overhaul moves and renames sections across six repositories, and GitHub keeps
U+FE0F in a heading's anchor, so a heading like "⚙️ Configuration" gets an id no hand-written link
matches. This tool reads a repository's tracked Markdown and reports what a reader would hit:

Checks
------
    emoji      a heading with a decorative emoji (an error: docs/documentation-style.md rule 3)
    links      a relative link to a file that does not exist, or to an anchor that no heading of
               its target produces under GitHub's rules (errors)
    map        README.md without a "Documentation" heading or without a link to the style guide
               (errors)
    length     README.md over 250 lines (a warning)

`agent_dev_logs/` is skipped: dev logs are not reader documentation; so are the hub's
`docs/templates/`, whose links point into a tool repository. So is the Markdown under
`data_samples/` other than its README: converted sample documents are data.

Exit codes: 0 no errors (warnings allowed) · 1 an error found · 2 usage error. stdlib-only, like
runbook_check.py.

Usage
-----
    python3 tools/docs_check.py                               # the six repos beside the hub
    python3 tools/docs_check.py --repo atrium-ocr-postprocess
    python3 tools/docs_check.py --ref origin/test --quiet
"""

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

REPOS = (
    "atrium-page-classification",
    "atrium-ocr-postprocess",
    "atrium-translator",
    "atrium-nlp-enrich",
    "atrium-keyword-extract",
    "atrium-digital-convert",
)

#: Not reader documentation: dev logs, and the hub's templates (their links point into a tool repo).
SKIP_DIRS = ("agent_dev_logs/", "docs/templates/")
#: Markdown that is data, not documentation: converted sample documents (their README is checked).
DATA_DIRS = ("data_samples/",)
README_MAX_LINES = 250
GUIDE = "documentation-style.md"

_EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff\u2300-\u23ff\ufe0f\u200d\u24c2\u3030\u303d]")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_REF_DEF = re.compile(r"^\s{0,3}\[(?!\^)[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$")  # not a footnote `[^x]:`
_HTML_ANCHOR = re.compile(r"<a\s+[^>]*(?:id|name)=\"([^\"]+)\"", re.IGNORECASE)
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def strip_code(line: str) -> str:
    """The line without its inline code spans (links inside backticks are not links)."""
    return re.sub(r"(`+)(?:(?!\1).)*\1", "", line)


def heading_text(raw: str) -> str:
    """A heading's text as GitHub renders it, before the anchor rules apply."""
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return text.replace("`", "")


def github_anchor(text: str) -> str:
    """GitHub's heading id: lower case; letters, marks, numbers, `_`, `-` and spaces kept; spaces → `-`.

    U+FE0F (a variation selector) is a mark, so it survives while the emoji before it does not:
    "⚙️ Configuration" → "\\ufe0f-configuration".
    """
    kept = []
    for ch in text.lower():
        category = unicodedata.category(ch)
        if ch in " -" or category[0] in "LMN" or category == "Pc":
            kept.append(ch)
    return "".join(kept).replace(" ", "-")


def scan(text: str):
    """(headings as (line, level, text), links as (line, target), explicit anchors) outside fences."""
    headings, links, anchors, fence = [], [], set(), None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif stripped.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        anchors.update(_HTML_ANCHOR.findall(line))
        match = _HEADING.match(line)
        if match:
            headings.append((number, len(match.group(1)), match.group(2)))
        code_free = strip_code(line)
        links.extend((number, target) for target in _LINK.findall(code_free))
        ref = _REF_DEF.match(code_free)
        if ref:
            links.append((number, ref.group(1)))
    return headings, links, anchors


def anchors_of(text: str) -> set:
    """Every fragment a link may name in this Markdown text, with GitHub's `-1`, `-2` suffixes."""
    headings, _links, explicit = scan(text)
    seen, ids = {}, set(explicit)
    for _number, _level, raw in headings:
        base = github_anchor(heading_text(raw))
        count = seen.get(base, 0)
        ids.add(base if count == 0 else f"{base}-{count}")
        seen[base] = count + 1
    return {anchor.lower() for anchor in ids}


class Tree:
    """A repository's files: tracked and untracked-but-not-ignored in the working tree, or those of a ref."""

    def __init__(self, repo: Path, ref: str = None):
        self.repo, self.ref = repo, ref
        if ref is None:
            cmd = ["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard"]
        else:
            cmd = ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"cannot list {repo}")
        self.files = set(proc.stdout.splitlines())
        self.dirs = {str(parent) for name in self.files for parent in PurePosixPath(name).parents}

    def read(self, name: str) -> str:
        if self.ref is None:
            return (self.repo / name).read_text(encoding="utf-8", errors="replace")
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "show", f"{self.ref}:{name}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout

    def markdown(self) -> list:
        return sorted(
            n
            for n in self.files
            if n.endswith(".md")
            and not n.startswith(SKIP_DIRS)
            and not (n.startswith(DATA_DIRS) and PurePosixPath(n).name != "README.md")
        )


def resolve(source: str, target: str):
    """The repository path a relative link points at, or None when it leaves the repository."""
    parts = []
    for part in (PurePosixPath(source).parent / target).parts:
        if part == "..":
            if not parts:
                return None
            parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def check_file(tree: Tree, name: str, cache: dict) -> tuple:
    """(errors, warnings) of one Markdown file."""
    errors, warnings = [], []
    text = tree.read(name)
    headings, links, _anchors = scan(text)
    for number, _level, raw in headings:
        if _EMOJI.search(raw):
            errors.append(f"{name}:{number}: emoji in heading {raw!r}")
    for number, target in links:
        if _EXTERNAL.match(target):
            continue
        path, _, fragment = target.partition("#")
        path = unquote(path)
        if path:
            resolved = resolve(name, path)
            if resolved is None:
                continue  # outside the repository (a sibling checkout): not this repository's to check
            if resolved not in tree.files and resolved.rstrip("/") not in tree.dirs:
                errors.append(f"{name}:{number}: link to a missing file: {target}")
                continue
        else:
            resolved = name
        if fragment and resolved.endswith(".md") and resolved in tree.files:
            if resolved not in cache:
                cache[resolved] = anchors_of(tree.read(resolved))
            if unquote(fragment).lower() not in cache[resolved]:
                errors.append(f"{name}:{number}: no heading for the anchor in {target}")
    if name == "README.md":
        lines = len(text.splitlines())
        if lines > README_MAX_LINES:
            warnings.append(f"README.md: {lines} lines (guideline: about {README_MAX_LINES})")
        if not any("documentation" in heading_text(raw).lower() for _n, _l, raw in headings):
            errors.append("README.md: no 'Documentation' section (the documentation map)")
        if GUIDE not in text:
            errors.append(f"README.md: no link to the documentation style guide ({GUIDE})")
    return errors, warnings


def check_repo(repo: Path, ref: str = None) -> tuple:
    tree = Tree(repo, ref)
    errors, warnings, cache = [], [], {}
    for name in tree.markdown():
        file_errors, file_warnings = check_file(tree, name, cache)
        errors += file_errors
        warnings += file_warnings
    return errors, warnings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the six tool repositories' Markdown for broken links, anchors and headings (#79).",
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
        help="check only this repo (repeatable; default: the six tool repos)",
    )
    parser.add_argument("--ref", default=None, help="read the files at this ref, not the working tree")
    parser.add_argument("--quiet", action="store_true", help="print only repos with errors")
    args = parser.parse_args(argv)

    checked = failing = 0
    for name in args.repos or REPOS:
        repo = args.repos_root / name
        if not repo.is_dir():
            print(f"[docs][SKIP] {name}: no clone at {repo}")
            continue
        try:
            errors, warnings = check_repo(repo, args.ref)
        except RuntimeError as exc:
            print(f"[docs] {name}: {exc}", file=sys.stderr)
            return 2
        checked += 1
        where = f"{name}@{args.ref}" if args.ref else name
        if errors:
            failing += 1
            print(f"\n[docs][ERROR] {where}: {len(errors)} error(s), {len(warnings)} warning(s)")
            for line in errors + [f"warning: {w}" for w in warnings]:
                print(f"  - {line}")
        elif not args.quiet:
            note = f" ({len(warnings)} warning(s): {'; '.join(warnings)})" if warnings else ""
            print(f"[docs][OK]    {where}{note}")

    if not checked:
        print("[docs] no repository checked", file=sys.stderr)
        return 2
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
