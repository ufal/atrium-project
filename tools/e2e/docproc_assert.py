#!/usr/bin/env python3
"""docproc_assert.py — the E2E checks on a docproc document (`atr/docproc-json`, atrium-project#84).

Since record schema 2.0 digital-convert writes docproc, not the record; ocr-postprocess builds the
record from it (`build_record.py`). The E2E lanes check the docproc on its own before the record is
built, against the hand-over rules of ARÚP's contract of 12 November 2026:

  * the schema: digital-convert's `schemas/docproc/document.atrium-proposal.schema.json` (#84
    comment 1's schema with asks 3 and 13), passed with `--schema` from the lane's checkout;
  * the routing lists every page, each `text-layer`, `atr` or `empty` (H5); in digital-convert's
    docproc (its pages carry `needsAtr`) a page's `needsAtr` agrees with its route `atr` (H4). The ATR's
    own docproc routes its pages `atr` and carries no `needsAtr`;
  * nothing is refused (H12): a page the converter cannot use is routed to the ATR;
  * no run data and no licence anywhere in it (D1, D2): no `run_uuid`, `provenance`, `license`;
  * `--expect-atr-pages`: `none`, `all` (every page not routed `empty`), or a comma-separated list of
    the page numbers routed `atr`.

Usage:
    python tools/e2e/docproc_assert.py work/docproc/minimal.docproc.json \\
        --schema work/digital-convert-src/schemas/docproc/document.atrium-proposal.schema.json \\
        --expect-atr-pages none

Exit 0 when every check holds, 1 when one fails (each failure is printed), 2 for a usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

ROUTES = ("text-layer", "atr", "empty")
#: Keys that would carry run data or a licence into docproc (D1, D2).
BANNED_KEYS = ("run_uuid", "provenance", "license", "license_url", "license_detail", "effective_license")


def _walk_keys(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_keys(item)


def _expected(spec: Optional[str], pages: List[int], empty: Set[int]) -> Optional[Set[int]]:
    if spec is None:
        return None
    if spec == "none":
        return set()
    if spec == "all":
        return set(pages) - empty
    return {int(part) for part in spec.split(",") if part.strip()}


def check(
    document: Dict[str, Any], schema: Optional[Dict[str, Any]] = None, expect_atr: Optional[str] = None
) -> List[str]:
    """The failures of `document` (empty when every check holds)."""
    problems: List[str] = []
    if schema is not None:
        import jsonschema  # noqa: PLC0415  (tools/e2e/requirements.txt)

        validator = jsonschema.Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
            where = "/".join(str(p) for p in error.absolute_path) or "(root)"
            problems.append(f"schema: {where}: {error.message[:200]}")

    pages = {p.get("pageNumber"): p for p in document.get("pages") or [] if isinstance(p, dict)}
    routing = ((document.get("metadata") or {}).get("routing") or {}).get("pages") or []
    routes = {row.get("page"): row.get("route") for row in routing if isinstance(row, dict)}
    numbers = sorted(n for n in set(pages) | set(routes) if isinstance(n, int))
    flags_atr = any("needsAtr" in page for page in pages.values())  # digital-convert's docproc
    if not numbers:
        problems.append("no page is listed in pages[] or in metadata.routing.pages[]")
    for number in range(1, (numbers[-1] if numbers else 0) + 1):
        if number not in routes:
            problems.append(f"page {number} is not in metadata.routing.pages[] (H5: the routing lists every page)")
        elif routes[number] not in ROUTES:
            problems.append(f"page {number} is routed {routes[number]!r}, not one of {list(ROUTES)}")
        if routes.get(number) != "empty" and number not in pages:
            problems.append(f"page {number} is routed {routes.get(number)!r} but has no pages[] entry")
        page = pages.get(number)
        if flags_atr and page is not None and bool(page.get("needsAtr")) != (routes.get(number) == "atr"):
            problems.append(
                f"page {number}: needsAtr={page.get('needsAtr')!r} disagrees with its route {routes.get(number)!r} (H4)"
            )

    banned = sorted(set(_walk_keys(document)) & set(BANNED_KEYS))
    if banned:
        problems.append(f"docproc carries run data or a licence: {banned} (D1, D2)")

    wanted = _expected(expect_atr, numbers, {n for n, route in routes.items() if route == "empty"})
    if wanted is not None:
        atr = {n for n, route in routes.items() if route == "atr"}
        if atr != wanted:
            problems.append(f"pages routed to the ATR are {sorted(atr)}, expected {sorted(wanted)}")
    return problems


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("docproc", type=Path, help="the docproc document to check")
    parser.add_argument("--schema", type=Path, default=None, help="the docproc JSON Schema to validate against")
    parser.add_argument(
        "--expect-atr-pages",
        default=None,
        help="`none`, `all`, or comma-separated page numbers that must be routed to the ATR",
    )
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.docproc.read_text(encoding="utf-8"))
        schema = json.loads(args.schema.read_text(encoding="utf-8")) if args.schema else None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"docproc_assert: {exc}", file=sys.stderr)
        return 2
    problems = check(document, schema, args.expect_atr_pages)
    for problem in problems:
        print(f"❌ {args.docproc.name}: {problem}")
    if problems:
        return 1
    routes = ((document.get("metadata") or {}).get("routing") or {}).get("pages") or []
    summary = ", ".join(f"{row.get('page')}:{row.get('route')}" for row in routes)
    print(f"✅ docproc_assert.py: {args.docproc.name} holds (routing {summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
