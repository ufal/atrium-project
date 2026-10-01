"""Build an AMČR-style seed record for a file (atrium-project#71).

AMČR writes a seed before the first ATRIUM stage: `doc_id` = its file id, and a `source` with the
Fedora digest (`sha512`), the file name and the media type. The origin is left to the tool that
reads the source. The E2E smokes start their chains from such a seed, so this script makes one
from the fixture the chain reads, with a `doc_id` unlike any file name in the chain. That is the
AMČR situation, and it is the one that forked records before atrium-project#68.

The seed is validated against `atrium_document.seed_schema()` before it is written, so a seed
this script emits is one every tool accepts as input.

Usage:
    python tools/e2e/make_seed.py fixtures/e2e/ALTO/CTX000000003.alto.xml \\
        --doc-id AMCR-F-CTX000000003 --media-type application/alto+xml --out work/seed.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# The canonical atrium_document.py lives in docs/templates/shared/, as for e2e_assert.py.
_SHARED_DIR = Path(__file__).resolve().parents[2] / "docs" / "templates" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from atrium_document import RECORD_TYPE, SCHEMA_VERSION, validate_seed  # noqa: E402  (needs the path above)


def make_seed(path: Path, doc_id: str, media_type: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """The seed of one file: its sha512 as the archive would record it, its name and media type."""
    digest = hashlib.sha512(path.read_bytes()).hexdigest()
    seed = {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "doc_id": doc_id,
        "source": {"sha512": digest, "filename": filename or path.name, "media_type": media_type},
    }
    validate_seed(seed)
    return seed


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, help="the original the seed describes")
    parser.add_argument("--doc-id", required=True, help="the archive's id for the document (AMČR: its file id)")
    parser.add_argument("--media-type", required=True, help="the original's media type, as the archive detected it")
    parser.add_argument("--filename", default=None, help="the original's name in the archive (default: the file's)")
    parser.add_argument("--out", type=Path, required=True, help="where to write the seed")
    args = parser.parse_args(argv)

    seed = make_seed(args.file, args.doc_id, args.media_type, args.filename)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"seed: {args.out} (doc_id {seed['doc_id']}, sha512 {seed['source']['sha512'][:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
