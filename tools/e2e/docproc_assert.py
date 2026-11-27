#!/usr/bin/env python3
"""docproc_assert.py — the E2E checks on a docproc document (`atr/docproc-json`, atrium-project#84).

Since record schema 2.0 digital-convert writes docproc, not the record; ocr-postprocess builds the
record from it (`build_record.py`). The E2E lanes check the docproc on its own before the record is
built, against the hand-over rules of ARÚP's contract of 12 November 2026:

  * the schema: digital-convert's `schemas/docproc/document.atrium-proposal.schema.json` (#84
    comment 1's schema with asks 3 and 13), passed with `--schema` from the lane's checkout;
  * the routing lists every page, each `text-layer`, `atr` or `empty`, and a page routed `empty` has no
    `pages[]` entry (H5, D29); in digital-convert's
    docproc (its pages carry `needsAtr`) a page's `needsAtr` agrees with its route `atr` (H4). The ATR's
    own docproc routes its pages `atr` and carries no `needsAtr`; its echo of the forced pages (`forced`,
    ask 5) must name exactly the pages it was forced to read (`--expect-forced`);
  * nothing is refused (H12): a page the converter cannot use is routed to the ATR;
  * no run data and no licence anywhere in it (D1, D2): no `run_uuid`, `provenance`, `license`;
  * a routing entry says nothing of what the page shows: no `graphics` or `tables` (#84 decision 6, ask 14
    withdrawn);
  * `--expect-atr-pages`: `none`, `all` (every page not routed `empty`), or a comma-separated list of
    the page numbers routed `atr`;
  * `--expect-graphics-pages` with `--graphics-pages-from FILE`: `none` or a comma-separated list of the
    pages that show graphics, as digital-convert hands them over with the run (`graphics_pages` in
    `/reformat`'s answer or in `--graphics-pages-out`'s file; #84 decisions 4 and 6): with the forced
    pages, the pages for page-classification.

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
#: What a page shows is a run hand-over, not docproc (#84 decision 6: ask 14 withdrawn).
WITHDRAWN_ROUTING_KEYS = ("graphics", "tables")


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
    document: Dict[str, Any],
    schema: Optional[Dict[str, Any]] = None,
    expect_atr: Optional[str] = None,
    expect_forced: Optional[str] = None,
    expect_graphics: Optional[str] = None,
    graphics_pages: Optional[List[int]] = None,
) -> List[str]:
    """The failures of `document` (empty when every check holds). `graphics_pages` is digital-convert's
    hand-over, checked against `expect_graphics`."""
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
        if routes.get(number) == "empty" and number in pages:
            problems.append(f"page {number} is routed 'empty' but has a pages[] entry (H5: an empty page has none)")
        page = pages.get(number)
        if flags_atr and page is not None and bool(page.get("needsAtr")) != (routes.get(number) == "atr"):
            problems.append(
                f"page {number}: needsAtr={page.get('needsAtr')!r} disagrees with its route {routes.get(number)!r} (H4)"
            )

    banned = sorted(set(_walk_keys(document)) & set(BANNED_KEYS))
    if banned:
        problems.append(f"docproc carries run data or a licence: {banned} (D1, D2)")
    for row in routing:
        withdrawn = sorted(set(row) & set(WITHDRAWN_ROUTING_KEYS)) if isinstance(row, dict) else []
        if withdrawn:
            problems.append(
                f"page {row.get('page')}: routing carries {withdrawn}: what a page shows is handed over with "
                "the run, not written into docproc (#84 decision 6)"
            )

    wanted = _expected(expect_atr, numbers, {n for n, route in routes.items() if route == "empty"})
    if wanted is not None:
        atr = {n for n, route in routes.items() if route == "atr"}
        if atr != wanted:
            problems.append(f"pages routed to the ATR are {sorted(atr)}, expected {sorted(wanted)}")
    forced_wanted = _expected(expect_forced, numbers, set())
    if forced_wanted is not None:
        forced = {row.get("page") for row in routing if isinstance(row, dict) and row.get("forced") is True}
        if forced != forced_wanted:
            problems.append(f"the routing echoes forced pages {sorted(forced)}, expected {sorted(forced_wanted)} (D27)")
    graphics_wanted = _expected(expect_graphics, numbers, set())
    if graphics_wanted is not None:
        if graphics_pages is None:
            problems.append("--expect-graphics-pages needs the hand-over (--graphics-pages-from)")
        else:
            shown = set(graphics_pages)
            if shown != graphics_wanted:
                problems.append(
                    f"pages showing graphics are {sorted(shown)}, expected {sorted(graphics_wanted)} (#84 decision 4)"
                )
            beyond = sorted(n for n in shown if n not in numbers)
            if beyond:
                problems.append(f"graphics_pages names page(s) {beyond} that the docproc does not list")
    return problems


def read_graphics_pages(path: Path) -> List[int]:
    """`graphics_pages` from digital-convert's hand-over: `--graphics-pages-out`'s file or a `/reformat`
    answer (both carry it at the top level)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = data.get("graphics_pages") if isinstance(data, dict) else None
    if not isinstance(pages, list) or not all(isinstance(n, int) and not isinstance(n, bool) for n in pages):
        raise ValueError(f"{path}: no `graphics_pages` list of page numbers")
    return pages


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("docproc", type=Path, help="the docproc document to check")
    parser.add_argument("--schema", type=Path, default=None, help="the docproc JSON Schema to validate against")
    parser.add_argument(
        "--expect-atr-pages",
        default=None,
        help="`none`, `all`, or comma-separated page numbers that must be routed to the ATR",
    )
    parser.add_argument(
        "--expect-forced",
        default=None,
        help="the ATR's docproc: `none` or comma-separated page numbers its routing must echo as forced (ask 5)",
    )
    parser.add_argument(
        "--expect-graphics-pages",
        default=None,
        help="`none` or comma-separated page numbers that show graphics, as digital-convert hands them over "
        "(with --graphics-pages-from; #84 decision 4)",
    )
    parser.add_argument(
        "--graphics-pages-from",
        type=Path,
        default=None,
        help="digital-convert's hand-over: its --graphics-pages-out file or a /reformat answer (`graphics_pages`)",
    )
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.docproc.read_text(encoding="utf-8"))
        schema = json.loads(args.schema.read_text(encoding="utf-8")) if args.schema else None
        shown = read_graphics_pages(args.graphics_pages_from) if args.graphics_pages_from else None
    except (OSError, ValueError) as exc:
        print(f"docproc_assert: {exc}", file=sys.stderr)
        return 2
    problems = check(document, schema, args.expect_atr_pages, args.expect_forced, args.expect_graphics_pages, shown)
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
