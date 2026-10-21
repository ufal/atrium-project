#!/usr/bin/env python3
"""Read the pins of tool-to-tool copies, for para-drift's vendored-parity job (atrium-project#82 B).

A file one tool owns and another vendors is pinned in the consumer's
`tests/test_vendored_*_parity.py` by three module-level literals:

    ADOPTED = {"owner": "atrium-nlp-enrich", "commit": "<40 hex>", "release": "v1.1.0-beta"}
    VENDORED = {"api_util/teitok_read.py": "<sha256>", ...}   # consumer path -> digest
    SOURCE = {"tests/fixtures/x.xml": "data_samples/x.xml"}    # optional: owner path, if different

The blocking check compares the copies with the owner at `ADOPTED["commit"]`, the revision the
consumer chose, so a push to the owner never turns a consumer red. Whether the owner has moved on
since is reported separately, as advice. This module reads the literals with `ast`, importing
nothing from the consumer, and serves both steps:

    list FILE...                    one tab-separated row per pin file: file, owner, commit, release
    ahead FILE --owner-dir DIR      Markdown rows for the copies whose owner file differs from the pin
                                    (`--owner-ref test@abc1234` names the revision checked out there)

`list` checks the literals: an owner that is a repository name, a full commit SHA, a digest per
copy, SOURCE keys that are copies, and with `--owners` that every owner is one the caller declares.
Exit 0 clean, 1 findings, 2 usage error. `ahead` exits 0 whatever it finds; it reports.

Usage:
    python tools/ci/vendored_pins.py list tests/test_vendored_*_parity.py --owners "atrium-nlp-enrich"
    python tools/ci/vendored_pins.py ahead tests/test_vendored_teitok_parity.py --owner-dir ../atrium-nlp-enrich
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_OWNER = re.compile(r"[A-Za-z0-9._-]+")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_DIGEST = re.compile(r"[0-9a-f]{64}")


@dataclass
class Pins:
    path: Path
    owner: str = ""
    commit: str = ""
    release: str = ""
    vendored: dict[str, str] = field(default_factory=dict)
    source: dict[str, str] = field(default_factory=dict)

    def owner_path(self, rel: str) -> str:
        return self.source.get(rel, rel)


def _literals(tree: ast.Module, names: set[str]) -> dict[str, object]:
    """The module-level `NAME = <literal>` assignments among `names`, evaluated without running code."""
    found: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        else:
            continue
        if isinstance(target, ast.Name) and target.id in names:
            found[target.id] = ast.literal_eval(value)
    return found


def read_pins(path: Path, findings: list[str]) -> Pins:
    pins = Pins(path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        values = _literals(tree, {"ADOPTED", "VENDORED", "SOURCE"})
    except (OSError, SyntaxError, ValueError) as exc:
        findings.append(f"{path}: cannot read its pins ({exc})")
        return pins

    adopted = values.get("ADOPTED")
    if not isinstance(adopted, dict):
        findings.append(f"{path}: no ADOPTED = {{'owner': ..., 'commit': ..., 'release': ...}}")
    else:
        pins.owner = str(adopted.get("owner", ""))
        pins.commit = str(adopted.get("commit", ""))
        pins.release = str(adopted.get("release", ""))
        if not _OWNER.fullmatch(pins.owner):
            findings.append(f"{path}: ADOPTED['owner'] {pins.owner!r} is not a repository name")
        if not _COMMIT.fullmatch(pins.commit):
            findings.append(f"{path}: ADOPTED['commit'] {pins.commit!r} is not a full 40-hex commit SHA")

    vendored = values.get("VENDORED")
    if not isinstance(vendored, dict) or not vendored:
        findings.append(f"{path}: no VENDORED = {{path: sha256}} with at least one copy")
    else:
        pins.vendored = {str(k): str(v) for k, v in vendored.items()}
        for rel, digest in pins.vendored.items():
            if not _DIGEST.fullmatch(digest):
                findings.append(f"{path}: VENDORED[{rel!r}] is not a SHA-256 digest")

    source = values.get("SOURCE", {})
    if not isinstance(source, dict):
        findings.append(f"{path}: SOURCE is not a dict")
    else:
        pins.source = {str(k): str(v) for k, v in source.items()}
        for rel in pins.source:
            if rel not in pins.vendored:
                findings.append(f"{path}: SOURCE names {rel!r}, which VENDORED does not pin")
    return pins


def digest(path: Path) -> str:
    """The pin tests' digest: SHA-256 with CRLF normalised to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def ahead_rows(pins: Pins, owner_dir: Path, owner_ref: str = "") -> list[str]:
    """One Markdown row per copy whose file in `owner_dir` no longer has the pinned digest."""
    owner = f"{pins.owner} at {owner_ref}" if owner_ref else pins.owner
    rows = []
    for rel in sorted(pins.vendored):
        upstream = owner_dir / pins.owner_path(rel)
        if not upstream.is_file():
            state = "removed or moved in the owner"
        elif digest(upstream) != pins.vendored[rel]:
            state = "changed in the owner"
        else:
            continue
        rows.append(f"| `{rel}` | {owner} | `{pins.owner_path(rel)}` | {state} |")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_list = sub.add_parser("list", help="validate the pins and print file, owner, commit, release")
    p_list.add_argument("files", nargs="+", type=Path)
    p_list.add_argument("--owners", default=None, help="the owners the caller declares (vendored-from)")
    p_ahead = sub.add_parser("ahead", help="Markdown rows for copies the owner has changed since")
    p_ahead.add_argument("file", type=Path)
    p_ahead.add_argument("--owner-dir", type=Path, required=True)
    p_ahead.add_argument("--owner-ref", default="", help="the revision in --owner-dir, shown in the rows")
    args = parser.parse_args(argv)

    findings: list[str] = []
    if args.command == "ahead":
        pins = read_pins(args.file, findings)
        if findings:
            for finding in findings:
                print(f"::warning::{finding}", file=sys.stderr)
            return 0
        rows = ahead_rows(pins, args.owner_dir, args.owner_ref)
        if rows:
            print("\n".join(rows))
        return 0

    declared = set(args.owners.split()) if args.owners is not None else None
    rows = []
    for path in args.files:
        pins = read_pins(path, findings)
        if declared is not None and pins.owner and pins.owner not in declared:
            findings.append(
                f"{path}: ADOPTED['owner'] {pins.owner} is not in the caller's vendored-from ({args.owners})"
            )
        rows.append(f"{path}\t{pins.owner}\t{pins.commit}\t{pins.release}")
    if findings:
        for finding in findings:
            print(f"::error::{finding}", file=sys.stderr)
        return 1
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
