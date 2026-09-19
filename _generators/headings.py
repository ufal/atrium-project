"""Fence-aware markdown heading extraction.

This is deliberately the same rule 57.plan.md B.2 specifies for the assembler:
a line that looks like a heading inside a ``` fence is NOT a heading. The corpus
has 218 such lines, and at split depth they cost docs/agent_skill_strategy.md
five phantom `##` and three phantom `###`. A generator that used a bare regex
would write source pointers to sections that do not exist.
"""

from __future__ import annotations

import pathlib
import re

H = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def headings(path: pathlib.Path, level: int = 2) -> list[tuple[str, int]]:
    """Return [(heading_text_without_hashes, byte_size_of_section)] at `level`."""
    if not path.exists():
        return []
    lines = path.read_text(errors="replace").split("\n")
    in_fence = False
    found: list[tuple[str, int]] = []  # (text, start_line)
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = H.match(line)
        if m and len(m.group(1)) == level:
            found.append((m.group(2), i))
    out = []
    for n, (text, start) in enumerate(found):
        end = found[n + 1][1] if n + 1 < len(found) else len(lines)
        size = sum(len(_l) + 1 for _l in lines[start:end])
        out.append((text, size))
    return out


def phantom_count(path: pathlib.Path, level: int = 2) -> int:
    """How many headings a NAIVE regex would have found that are really fenced."""
    if not path.exists():
        return 0
    text = path.read_text(errors="replace")
    naive = len([ll for ll in text.split("\n") if H.match(ll) and len(H.match(ll).group(1)) == level])
    return naive - len(headings(path, level))
