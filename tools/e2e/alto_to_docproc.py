#!/usr/bin/env python3
"""alto_to_docproc.py — the E2E's stand-in for the ATR: a docproc in the ATR's shape from an ALTO fixture.

The scanned lane of e2e-pipeline-smoke.yml needs what the ATR writes for a scanned document since
ARÚP's contract of 12 November 2026: a docproc (`atr/docproc-json`, #84 comment 1's schema), from which
ocr-postprocess builds the record. CI has no ATR, so this writes one from the lane's ALTO fixture, the
same file the page image is rendered from (tools/e2e/render_alto_page.py): the page's text and boxes
agree with what page-classification sees.

It is a FIXTURE tool, not the converter of D31 (PCSS ALTO into docproc, unassigned in the contract):

  * one docproc page per ALTO `Page` (`PHYSICAL_IMG_NR`, else the page's position), in px, the ALTO's
    unit (`coordinateUnit: px`);
  * one `text` block per `TextBlock`, in document order (`readingOrder`), its id `p<page>-b<n>`, its box
    the block's, its `content` the lines joined by a line break, one per visual line (ask 7), so the
    record gets visual lines, not one-unit blocks (D18 rule 5);
  * the routing lists every page as `atr` (H5), a page with no text block as `empty`;
  * `processedAt` is fixed (the schema requires it; a fixture must not change on every run).

Usage:
    python tools/e2e/alto_to_docproc.py fixtures/e2e/ALTO/CTX000000003.alto.xml \\
        --out fixtures/e2e/docproc/CTX000000003.atr.docproc.json
    python tools/e2e/alto_to_docproc.py fixtures/e2e/ALTO/*.alto.xml --out-dir fixtures/e2e/docproc
    python tools/e2e/alto_to_docproc.py ... --check     # the committed files are what this writes

Exit 0 when written (or, with --check, when every file is current), 1 when --check finds a stale one.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

#: The fixed `processedAt` of every fixture written here.
PROCESSED_AT = "2026-11-14T00:00:00Z"
PIPELINE = "pipeline-e2e/atrium-stand-in"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(node: ET.Element, name: str) -> List[ET.Element]:
    return [child for child in node.iter() if _local(child.tag) == name]


def _num(node: ET.Element, attr: str) -> float:
    return float(node.get(attr) or 0)


def _line_text(line: ET.Element) -> str:
    words = [s.get("CONTENT") or "" for s in line if _local(s.tag) == "String"]
    return " ".join(w for w in words if w)


def convert(alto_path: Path) -> Dict[str, Any]:
    """The docproc document for one ALTO file (see the module docstring)."""
    root = ET.parse(alto_path).getroot()
    pages: List[Dict[str, Any]] = []
    routing: List[Dict[str, Any]] = []
    languages: Counter = Counter()
    for position, page in enumerate(_children(root, "Page"), start=1):
        number = int(page.get("PHYSICAL_IMG_NR") or position)
        blocks: List[Dict[str, Any]] = []
        for block in _children(page, "TextBlock"):
            lines = [_line_text(line) for line in block if _local(line.tag) == "TextLine"]
            lines = [text for text in lines if text.strip()]
            if not lines:
                continue
            x, y = _num(block, "HPOS"), _num(block, "VPOS")
            entry: Dict[str, Any] = {
                "id": f"p{number}-b{len(blocks)}",
                "type": "text",
                "bbox": [x, y, x + _num(block, "WIDTH"), y + _num(block, "HEIGHT")],
                "readingOrder": len(blocks),
                "content": "\n".join(lines),
            }
            lang = (block.get("LANG") or "")[:2].lower()
            if len(lang) == 2 and lang.isalpha():
                entry["language"] = lang
                languages[lang] += len(lines)
            blocks.append(entry)
        pages.append(
            {
                "pageNumber": number,
                "width": _num(page, "WIDTH"),
                "height": _num(page, "HEIGHT"),
                "coordinateUnit": "px",
                "blocks": blocks,
            }
        )
        routing.append({"page": number, "route": "atr" if blocks else "empty", "text_layer": False})
    if not pages:
        raise ValueError(f"{alto_path}: no ALTO Page")
    document: Dict[str, Any] = {
        "version": "1.0",
        "pipeline": PIPELINE,
        "processedAt": PROCESSED_AT,
        "sourceFormat": "pdf-scanned",
        "pages": pages,
        "metadata": {"routing": {"pages": routing}},
    }
    if languages:
        document["documentLanguage"] = languages.most_common(1)[0][0]
    return document


def _target(alto: Path, out: Optional[Path], out_dir: Optional[Path]) -> Path:
    if out is not None:
        return out
    stem = alto.name[: -len(".alto.xml")] if alto.name.endswith(".alto.xml") else alto.stem
    return (out_dir or alto.parent) / f"{stem}.atr.docproc.json"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("alto", nargs="+", type=Path, help="ALTO fixture(s)")
    parser.add_argument("--out", type=Path, default=None, help="the docproc to write (one ALTO only)")
    parser.add_argument("--out-dir", type=Path, default=None, help="where <id>.atr.docproc.json goes")
    parser.add_argument("--check", action="store_true", help="write nothing; fail when a file is not current")
    args = parser.parse_args(argv)
    if args.out is not None and len(args.alto) != 1:
        parser.error("--out takes one ALTO file")
    stale = 0
    for alto in args.alto:
        target = _target(alto, args.out, args.out_dir)
        text = json.dumps(convert(alto), ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != text:
                print(f"STALE: {target} is not what {alto} gives (re-run without --check)")
                stale += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
