#!/usr/bin/env python3
"""atr_standin.py — the E2E's stand-in for the ATR on a mixed document (atrium-project#84, H4, H6).

When digital-convert routes some pages of a born-digital document to the ATR, the whole document goes
through the ATR with those pages forced (H4), and ocr-postprocess builds the record from the ATR's docproc
(the stored one) and digital-convert's (not stored), keeping the text layer's exact lines (H6, D21). CI
has no ATR, so this writes a docproc in the ATR's shape from digital-convert's docproc of the same file:

  * every page digital-convert lists keeps its size and unit (both producers measure the displayed
    page, D28); a page it routes `empty` is routed `empty` here too, with no `pages[]` entry (H5);
  * a text-layer page gets the ATR's own blocks, not digital-convert's: two consecutive blocks become one
    `text` block (a table stays a table), with new ids `p<page>-b<n>`, the union of their boxes, their
    text as `content` with a line break per line (ask 7) and no `lines[]`, as the ATR writes them. The
    record builder must therefore link each kept line to the ATR block that holds it, by box. A `figure`
    block with a box (a picture on the page, #84 decision 6) stays a `figure` of its own, with an
    `imageRef` as the ATR writes one; a figure without a box is left out (the ATR finds pictures on the
    rendering, the lane's checks read digital-convert's docproc for it too);
  * a forced page (`needsAtr`) is read from `--ocr-text PAGE=FILE`: a `figure` block for the page's
    picture and a `.t0` OCR child holding the file's lines, as the ATR writes figure OCR. A forced page
    without a text file comes out empty (routed `empty`);
  * the routing lists every page as `atr` (or `empty`), and echoes the forced pages with `forced` and
    `forced_reason` (digital-convert's `needsAtrReason`; ask 5, D27);
  * `pipeline` names the stand-in and `processedAt` is fixed, so the output is the same on every run.

Usage:
    python tools/e2e/atr_standin.py work/docproc/scan_page-pdf.docproc.json \\
        --ocr-text 2=fixtures/e2e/mixed/scan_page.page2.txt \\
        --out work/docproc/scan_page-pdf.atr.docproc.json

Exit 0 when written, 1 when digital-convert's docproc routes no page to the ATR (nothing to stand in
for), 2 for a usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PIPELINE = "pipeline-e2e/atrium-stand-in"
PROCESSED_AT = "2026-11-16T00:00:00Z"
RENDER_DPI = 200
#: The forced page's picture keeps this margin to the page edge, its OCR text a further one.
MARGIN = 36.0
LINE_HEIGHT = 14.0
#: digital-convert's block types the stand-in keeps as one ATR block each.
SINGLE_TYPES = ("table", "figure")


def _union(boxes: Sequence[Sequence[float]]) -> Optional[List[float]]:
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def _text(block: Dict[str, Any]) -> str:
    lines = [str(row.get("text") or "") for row in block.get("lines") or [] if isinstance(row, dict)]
    return "\n".join(lines) if lines else str(block.get("content") or "")


def _text_layer_blocks(number: int, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The ATR's blocks over digital-convert's: pairs of text blocks, tables and figures kept (see the
    docstring)."""
    groups: List[List[Dict[str, Any]]] = []
    for block in sorted(blocks, key=lambda b: int(b.get("readingOrder", 0))):
        if block.get("type") == "figure" and not block.get("bbox"):
            continue
        single = block.get("type") in SINGLE_TYPES
        if single or not groups or groups[-1][0].get("type") in SINGLE_TYPES or len(groups[-1]) == 2:
            groups.append([block])
        else:
            groups[-1].append(block)
    out: List[Dict[str, Any]] = []
    for group in groups:
        box = _union([b.get("bbox") for b in group])
        if box is None:
            continue
        entry: Dict[str, Any] = {"id": f"p{number}-b{len(out)}", "type": "text", "bbox": box, "readingOrder": len(out)}
        if group[0].get("type") == "table":
            entry["type"] = "table"
            entry["content"] = str(group[0].get("content") or "")
            if isinstance(group[0].get("cellGrid"), dict):
                entry["cellGrid"] = group[0]["cellGrid"]
        elif group[0].get("type") == "figure":
            entry["type"] = "figure"
            entry["imageRef"] = f"assets/{entry['id']}.png"
        else:
            entry["content"] = "\n".join(_text(b) for b in group)
        out.append(entry)
    return out


def _forced_blocks(number: int, width: float, height: float, lines: List[str]) -> List[Dict[str, Any]]:
    figure = f"p{number}-b0"
    child = f"{figure}.t0"
    top = MARGIN * 2
    return [
        {
            "id": figure,
            "type": "figure",
            "bbox": [MARGIN, MARGIN, width - MARGIN, height - MARGIN],
            "readingOrder": 0,
            "imageRef": f"assets/{figure}.png",
            "children": [child],
        },
        {
            "id": child,
            "type": "text",
            "bbox": [MARGIN * 2, top, width - MARGIN * 2, min(height - MARGIN * 2, top + LINE_HEIGHT * len(lines))],
            "readingOrder": 1,
            "parent": figure,
            "content": "\n".join(lines),
        },
    ]


def standin(digital: Dict[str, Any], ocr: Dict[int, List[str]]) -> Dict[str, Any]:
    """The ATR-shaped docproc of a mixed document (see the module docstring)."""
    pages = {p["pageNumber"]: p for p in digital.get("pages") or [] if isinstance(p, dict)}
    routing = [
        r for r in ((digital.get("metadata") or {}).get("routing") or {}).get("pages") or [] if isinstance(r, dict)
    ]
    out_pages: List[Dict[str, Any]] = []
    out_routing: List[Dict[str, Any]] = []
    for row in sorted(routing, key=lambda r: r["page"]):
        number = row["page"]
        page = pages.get(number)
        if row.get("route") == "empty" or page is None:
            out_routing.append({"page": number, "route": "empty", "text_layer": False})
            continue
        width, height = float(page.get("width") or 0), float(page.get("height") or 0)
        forced = bool(page.get("needsAtr"))
        if forced:
            lines = [line for line in ocr.get(number, []) if line.strip()]
            blocks = _forced_blocks(number, width, height, lines) if lines and width and height else []
        else:
            blocks = _text_layer_blocks(number, [b for b in page.get("blocks") or [] if isinstance(b, dict)])
        entry: Dict[str, Any] = {"page": number, "route": "atr" if blocks else "empty", "text_layer": not forced}
        if forced:
            entry["forced"] = True
            entry["forced_reason"] = str(page.get("needsAtrReason") or "forced by the caller")
        out_routing.append(entry)
        if blocks:
            out_page: Dict[str, Any] = {"pageNumber": number, "width": width, "height": height}
            out_page["coordinateUnit"] = page.get("coordinateUnit") or "pt"
            out_page["renderDpi"] = RENDER_DPI
            if page.get("userUnit"):
                out_page["userUnit"] = page["userUnit"]
            out_page["blocks"] = blocks
            out_pages.append(out_page)
    used = any(not pages[r["page"]].get("needsAtr") for r in out_routing if r["route"] == "atr" and r["page"] in pages)
    document: Dict[str, Any] = {
        "version": "1.0",
        "pipeline": PIPELINE,
        "processedAt": PROCESSED_AT,
        "sourceFormat": "pdf-digital" if used else "pdf-scanned",
        "pages": out_pages,
        "metadata": {"routing": {"pages": out_routing}},
    }
    if digital.get("documentLanguage"):
        document["documentLanguage"] = digital["documentLanguage"]
    return document


def _ocr_arg(value: str):
    page, _, path = value.partition("=")
    if not page.isdigit() or not path:
        raise argparse.ArgumentTypeError(f"expected PAGE=FILE, got {value!r}")
    return int(page), Path(path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("docproc", type=Path, help="digital-convert's docproc of the document")
    parser.add_argument(
        "--ocr-text", type=_ocr_arg, action="append", default=[], metavar="PAGE=FILE", help="a forced page's OCR text"
    )
    parser.add_argument("--out", type=Path, required=True, help="the ATR-shaped docproc to write")
    args = parser.parse_args(argv)
    try:
        digital = json.loads(args.docproc.read_text(encoding="utf-8"))
        ocr = {page: path.read_text(encoding="utf-8").splitlines() for page, path in args.ocr_text}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"atr_standin: {exc}", file=sys.stderr)
        return 2
    if not any(isinstance(p, dict) and p.get("needsAtr") for p in digital.get("pages") or []):
        print(f"atr_standin: {args.docproc} routes no page to the ATR: there is no mixed document", file=sys.stderr)
        return 1
    document = standin(digital, ocr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    forced = [r["page"] for r in document["metadata"]["routing"]["pages"] if r.get("forced")]
    print(f"wrote {args.out} (forced pages {forced})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
