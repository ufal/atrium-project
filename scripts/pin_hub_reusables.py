#!/usr/bin/env python3
"""pin_hub_reusables.py — pin every tool repo's hub reusables to one commit of `v1`.

atrium-project#40 F / #72 E.2: *"every `uses:` line that points to this repository names a
commit."* A caller at `@v1` runs whatever the tag points to today; a caller at
`@<40-char sha>  # v1` runs that commit until someone moves the pin in a reviewed change.
Two reusables (para-drift, workflow-lint) also check the hub out a second time, at their
`hub-ref` input, to read the files they enforce, so a pinned caller passes the same commit
there; `tools/ci/workflow_lint.py` fails a caller whose two refs differ.

This script rewrites the callers in the sibling checkouts in one sweep:

* every `uses: ufal/atrium-project/.github/workflows/<file>@<ref>` becomes
  `uses: ufal/atrium-project/.github/workflows/<file>@<sha>  # v1`;
* where that reusable declares a `hub-ref` input, the job gets `hub-ref: <sha>` in its `with:`
  block (created when the job has none, updated when it has one).

Line-based on purpose: the callers are documentation as much as configuration, and a YAML
round trip would drop their comments. Run it after the hub commit is on `test` and `v1` has
moved to it, with that commit::

    python3 scripts/pin_hub_reusables.py --sha "$(git rev-parse 'v1^{commit}')"          # rewrite
    python3 scripts/pin_hub_reusables.py --sha "$(git rev-parse 'v1^{commit}')" --check  # verify, write nothing

(`^{commit}`: an annotated tag's own SHA is not a commit, and `uses:` needs the commit.)

then commit the callers in each tool repo and, once all six are pinned, run the linter with
`--require-sha-pins` (workflow-lint.reusable.yml). Re-running with the same commit changes
nothing; with a new commit it moves every pin together. Exit 0: nothing (left) to change;
1: `--check` found callers to change; 2: usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent
REPOS = (
    "atrium-page-classification",
    "atrium-ocr-postprocess",
    "atrium-nlp-enrich",
    "atrium-keyword-extract",
    "atrium-translator",
    "atrium-digital-convert",
)
CHANNEL = "v1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(
    r"^(?P<indent>\s*)(?P<dash>-\s+)?uses:\s*ufal/atrium-project/(?P<callee>\.github/workflows/[^@\s]+)@(?P<ref>\S+)"
    r"(?P<rest>.*)$"
)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def takes_hub_ref(callee: str, hub_root: Path) -> bool:
    path = hub_root / callee
    if not path.is_file():
        return False
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    trigger = doc.get(True) or doc.get("on") or {}
    return "hub-ref" in ((trigger.get("workflow_call") or {}).get("inputs") or {})


def _set_hub_ref(lines: list[str], uses_at: int, key_indent: int, sha: str) -> None:
    """Give the job whose `uses:` is at ``uses_at`` a `hub-ref: <sha>` in its `with:` block."""
    start = uses_at
    while start > 0 and not (_is_content(lines[start - 1]) and _indent(lines[start - 1]) < key_indent):
        start -= 1
    end = uses_at + 1
    while end < len(lines) and not (_is_content(lines[end]) and _indent(lines[end]) < key_indent):
        end += 1
    pad = " " * key_indent
    for at in range(start, end):
        if lines[at].rstrip() == f"{pad}with:":
            block_end = at + 1
            while block_end < end and (not _is_content(lines[block_end]) or _indent(lines[block_end]) > key_indent):
                block_end += 1
            for inner in range(at + 1, block_end):
                if re.match(rf"^{pad}\s+hub-ref:", lines[inner]):
                    lines[inner] = re.sub(r"hub-ref:.*$", f"hub-ref: {sha}", lines[inner])
                    return
            lines.insert(at + 1, f"{pad}  hub-ref: {sha}")
            return
    lines[uses_at + 1 : uses_at + 1] = [f"{pad}with:", f"{pad}  hub-ref: {sha}"]


def pin_text(text: str, sha: str, hub_root: Path) -> tuple[str, int]:
    """``(new text, callers pinned)`` for one workflow file."""
    lines = text.split("\n")
    count = 0
    at = 0
    while at < len(lines):
        match = USES_RE.match(lines[at])
        if not match or match["dash"]:  # a step's `- uses:` is an action, never a reusable workflow
            at += 1
            continue
        indent, callee = match["indent"], match["callee"]
        lines[at] = f"{indent}uses: ufal/atrium-project/{callee}@{sha}  # {CHANNEL}"
        count += 1
        if takes_hub_ref(callee, hub_root):
            before = len(lines)
            _set_hub_ref(lines, at, len(indent), sha)
            at += len(lines) - before
        at += 1
    return "\n".join(lines), count


def workflow_files(repo: Path) -> list[Path]:
    directory = repo / ".github" / "workflows"
    return sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sha", required=True, help=f"the 40-character hub commit `{CHANNEL}` points to")
    parser.add_argument(
        "--root", type=Path, default=HUB_ROOT.parent, help="where the tool repos sit (default: beside the hub)"
    )
    parser.add_argument("--repo", action="append", help="only this tool repo (repeatable)")
    parser.add_argument("--hub-root", type=Path, default=HUB_ROOT, help="the hub checkout the reusables are read from")
    parser.add_argument(
        "--check", action="store_true", help="report callers that are not pinned to --sha; write nothing"
    )
    args = parser.parse_args(argv)

    if not SHA_RE.match(args.sha):
        print(f"--sha must be a full 40-character commit, not {args.sha!r}", file=sys.stderr)
        return 2
    known = subprocess.run(
        ["git", "-C", str(args.hub_root), "rev-parse", "--verify", "--quiet", f"{args.sha}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if known.returncode != 0:
        print(f"warning: {args.sha[:12]} is not a commit of {args.hub_root}; fetch the hub first", file=sys.stderr)
    elif known.stdout.strip() != args.sha:
        print(
            f"--sha {args.sha[:12]} is a tag object, not a commit; pass its commit ({known.stdout.strip()[:12]}), "
            "e.g. \"$(git rev-parse 'v1^{commit}')\"",
            file=sys.stderr,
        )
        return 2

    changed = pinned = 0
    for name in args.repo or REPOS:
        repo = args.root / name
        if not repo.is_dir():
            print(f"skip: no {repo}", file=sys.stderr)
            continue
        for path in workflow_files(repo):
            text = path.read_text(encoding="utf-8")
            new, count = pin_text(text, args.sha, args.hub_root)
            pinned += count
            if new == text:
                continue
            changed += 1
            rel = path.relative_to(args.root)
            if args.check:
                print(f"not pinned to {args.sha[:12]}: {rel}")
            else:
                path.write_text(new, encoding="utf-8")
                print(f"pinned: {rel}")

    verb = "to change" if args.check else "changed"
    print(f"{pinned} hub-reusable callers at {args.sha[:12]} ({CHANNEL}); {changed} file(s) {verb}.")
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
