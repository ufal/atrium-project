"""How many lines keyword-extract's controlled kind would send to a paid model for a record.

The E2E lane's controlled-kind step (`e2e-pipeline-smoke.yml`) calls a third-party model once
per line, so it runs only on records small enough to cost next to nothing. The number it gates
on has to be the number the service would really send, and that is not always `len(lines)`:
the real chain's record (the OCR stage runs with `SKIP_CLASSIFY=true`) can hold its text in
`content.text` and no `lines[]` at all, and the service then sends every non-empty line of
`content.text`. Counting `lines[]` alone read 0 for such a record and let the 372- and 485-row
fixtures through, which would have been hundreds of paid calls.

The rule here follows `atrium-keyword-extract/service/api.py::_doc_from_record`:

* if some `lines[]` entry has text and a category the service trusts, its rows are the record's
  `lines[]`, and a row is sent when it has text (the service also drops rows that are too short
  or of poor quality, so this is an upper bound);
* otherwise its rows are the non-empty lines of `content.text`;
* a record with neither is the service's 422, counted as 0 here.

Usage:
    python tools/e2e/controlled_rows.py work/doc_json/4_nlp.json      # prints the number
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

_SHARED_DIR = Path(__file__).resolve().parents[2] / "docs" / "templates" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from atrium_vocab import UNTRUSTWORTHY_LINE_CATEGORIES  # noqa: E402  (needs the path above)

#: The categories keyword-extract leaves out of the document text (its `_SKIPPED_CATEGORIES`).
SKIPPED_CATEGORIES = frozenset(UNTRUSTWORTHY_LINE_CATEGORIES) | {"Empty"}


def rows_sent(record: Dict[str, Any]) -> int:
    """The most rows the controlled kind sends to the model for *record*."""
    lines = [line for line in record.get("lines") or [] if isinstance(line, dict)]
    with_text = [line for line in lines if str(line.get("text") or "").strip()]
    if any(line.get("categ") not in SKIPPED_CATEGORIES for line in with_text):
        return len(with_text)
    content = record.get("content")
    text = str(content.get("text") or "") if isinstance(content, dict) else ""
    return sum(1 for raw in text.splitlines() if raw.strip())


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    record = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    print(rows_sent(record))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
