#!/usr/bin/env python3
"""
render_alto_page.py — render one page of an ALTO XML file to a PNG image.

Purpose (hub e2e pipeline smoke, issue #18 follow-up)
-----------------------------------------------------
The e2e fixture is a single synthetic ALTO XML file. The page-classification
stage, however, consumes page IMAGES — so this script derives the image from
the same fixture instead of committing a binary PNG: a white canvas of the
ALTO <Page> dimensions with every <String> CONTENT drawn at its HPOS/VPOS.
The rendered page is what pc classifies, keeping the whole smoke test anchored
to ONE source fixture.

The classification RESULT is not asserted (a synthetic render is not a real
scan) — only the pc output interface is (see e2e_assert.py `pc`).

Usage
-----
    python3 render_alto_page.py <input.alto.xml> --out <page.png> [--page 1]
                                [--font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf]

Dependencies: Pillow (already required by page-classification).
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ALTO_NS = "{http://www.loc.gov/standards/alto/ns-v3#}"

# DejaVu Sans ships on ubuntu-latest runners and covers Czech diacritics.
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def render_page(alto_path: Path, out_path: Path, page_index: int, font_path: str) -> None:
    tree = ET.parse(alto_path)
    pages = tree.getroot().findall(f".//{ALTO_NS}Page")
    if not pages:
        raise SystemExit(f"[e2e] No <Page> elements in {alto_path}")
    if page_index < 1 or page_index > len(pages):
        raise SystemExit(f"[e2e] Page {page_index} out of range (1..{len(pages)}) in {alto_path}")

    page = pages[page_index - 1]
    width = int(float(page.get("WIDTH", "1654")))
    height = int(float(page.get("HEIGHT", "2339")))

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    drawn = 0
    for string in page.findall(f".//{ALTO_NS}String"):
        content = string.get("CONTENT", "")
        if not content:
            continue
        hpos = int(float(string.get("HPOS", "0")))
        vpos = int(float(string.get("VPOS", "0")))
        str_height = int(float(string.get("HEIGHT", "34"))) or 34
        try:
            font = ImageFont.truetype(font_path, str_height)
        except OSError:
            font = ImageFont.load_default()
        draw.text((hpos, vpos), content, fill="black", font=font)
        drawn += 1

    if drawn == 0:
        raise SystemExit(f"[e2e] Page {page_index} of {alto_path} has no non-empty <String> elements")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG")
    print(f"[e2e] Rendered page {page_index} of {alto_path.name} -> {out_path} ({width}x{height}, {drawn} strings)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("alto", type=Path, help="Input ALTO XML file.")
    parser.add_argument("--out", type=Path, required=True, help="Output PNG path.")
    parser.add_argument("--page", type=int, default=1, help="1-based page index to render (default: 1).")
    parser.add_argument("--font", type=str, default=DEFAULT_FONT, help=f"TTF font path (default: {DEFAULT_FONT}).")
    args = parser.parse_args(argv)

    render_page(args.alto, args.out, args.page, args.font)
    return 0


if __name__ == "__main__":
    sys.exit(main())