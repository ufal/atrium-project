#!/usr/bin/env python3
"""keep_native_assert.py — an office document's forced page keeps its own text (atrium-project#84 R8).

An office page with no running text that shows an object goes to the ATR, and the whole document with it
(decision 3); the record builder keeps the page's own lines beside the ATR's (keep-native, R4). The E2E's
mixed DOCX (digital-convert's `scan_page.docx`) has a scan on page 2 with its caption in a text box over
it, and the ATR stand-in reads the scan from `fixtures/e2e/mixed/scan_page.page2.txt`. The record's page 2
must hold both: the caption as a native line (`text_source: text-layer`) and the stand-in's reading of
the scan (`text_source: atr`). A merge that took the ATR's lines only would drop the caption; one that
counted the caption as covering the scan's OCR block would drop the scan's text, the text the page went to
the ATR for.

Usage:
    python tools/e2e/keep_native_assert.py work/records/scan_page-docx-mixed/AMCR-F-scan_page-docx.document.json

Exit 0 when both are there, 1 when one is missing (printed), 2 for a usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

#: The caption of the scan on scan_page.docx's page 2 (digital-convert's `make_fixtures.SCAN_CAPTION`).
CAPTION_PREFIX = "Obr. 2:"
#: The first line the ATR stand-in reads from the scan (fixtures/e2e/mixed/scan_page.page2.txt).
ATR_TEXT = "Plán sondy S1"


def problems(record: Dict[str, Any], page: int = 2, caption: str = CAPTION_PREFIX, atr: str = ATR_TEXT) -> List[str]:
    """What the record's forced page lacks (empty when it keeps both)."""
    labels = {
        str(row.get("page", row.get("page_index")))
        for row in record.get("pages") or []
        if row.get("page_index") == page
    }
    lines = [line for line in record.get("lines") or [] if str(line.get("page")) in labels]
    found: List[str] = []
    if not any(
        line.get("text_source") == "text-layer" and str(line.get("text", "")).startswith(caption) for line in lines
    ):
        found.append(
            f"page {page}: no native line starting {caption!r} (text_source text-layer): the caption was dropped"
        )
    if not any(line.get("text_source") == "atr" and atr in str(line.get("text", "")) for line in lines):
        found.append(f"page {page}: no ATR line holding {atr!r} (text_source atr): the scan's reading was dropped")
    return found


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("record", type=Path, help="the record built from the mixed office document")
    parser.add_argument("--page", type=int, default=2, help="the forced page's index (default 2)")
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"keep_native_assert: {exc}", file=sys.stderr)
        return 2
    found = problems(record, args.page)
    for problem in found:
        print(f"❌ {args.record.name}: {problem}")
    if found:
        return 1
    print(f"✅ keep_native_assert.py: page {args.page} keeps its caption beside the ATR's reading of the scan (R8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
