"""tools/shared_manifest.py — the one place that reads docs/templates/shared/MANIFEST.json.

atrium-project#59: before this existed, the canonical shared-file set was written out by
hand in three places — this script's own array literals, tools/skill_drift_check.py's
SHARED_FILES tuple, and para-drift.reusable.yml's `diff -u` steps — plus a fourth,
`ruff.toml`'s `[format] exclude` list, that nothing programmatic read at all. Each addition
since #51 updated some of them and not others, which is the exact failure #59 exists to
close: a guardrail cannot see what it is supposed to hold. This module is the manifest's
one reader; `scripts/revendor_shared.sh` and `tools/skill_drift_check.py` both import it
(or, for the bash script, invoke this file as a CLI) instead of parsing the JSON twice in
two different languages with two different bugs.

Consumers:
  - scripts/revendor_shared.sh: `python3 tools/shared_manifest.py --tsv MANIFEST.json`
    prints one row per file (canonical, dest, selftest, precondition) for a bash
    `while read` loop — bash cannot import a Python module, so a thin CLI is the bridge.
  - tools/skill_drift_check.py: `from shared_manifest import load_manifest`
  - tests/test_shared_manifest.py: same import, to check the manifest against the
    directory listing, ruff.toml, and para-drift.reusable.yml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ManifestError(Exception):
    """The manifest itself is malformed in a way none of its readers can recover from."""


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Return the manifest's `files` list, validated just enough that every consumer
    can trust the shape without re-checking it.
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestError(f"{path}: no non-empty 'files' list")

    seen_canonical: set[str] = set()
    seen_dest: set[str] = set()
    required = {"canonical", "dest", "selftest", "ruff_format_exclude", "isort_first_party", "preconditions"}
    for entry in files:
        missing = required - set(entry)
        if missing:
            raise ManifestError(f"{path}: entry {entry.get('canonical', entry)!r} missing field(s): {missing}")
        canonical = entry["canonical"]
        dest = entry["dest"]
        if canonical in seen_canonical:
            raise ManifestError(f"{path}: duplicate canonical filename {canonical!r}")
        if dest in seen_dest:
            raise ManifestError(f"{path}: duplicate dest path {dest!r}")
        seen_canonical.add(canonical)
        seen_dest.add(dest)
        preconditions = entry["preconditions"]
        if not isinstance(preconditions, list):
            raise ManifestError(f"{path}: {canonical!r}'s preconditions must be a list")

    return files


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to MANIFEST.json")
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="print canonical\\tdest\\tselftest(0/1)\\tprecondition, one row per file, for shell consumption",
    )
    args = parser.parse_args(argv)

    try:
        files = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.tsv:
        for entry in files:
            preconditions = entry["preconditions"]
            if len(preconditions) > 1:
                # revendor_shared.sh's PRECONDITIONS map only ever plumbed ONE path
                # through per file (a scalar, not a list) -- a manifest entry that
                # needs more than one is a real gap in that script's loader, not
                # something this CLI should silently truncate to the first.
                print(
                    f"ERROR: {entry['canonical']!r} declares {len(preconditions)} preconditions; "
                    f"revendor_shared.sh only reads the first one",
                    file=sys.stderr,
                )
                return 1
            precondition = preconditions[0] if preconditions else ""
            selftest = "1" if entry["selftest"] else "0"
            print(f"{entry['canonical']}\t{entry['dest']}\t{selftest}\t{precondition}")
    else:
        json.dump(files, sys.stdout, indent=2)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
