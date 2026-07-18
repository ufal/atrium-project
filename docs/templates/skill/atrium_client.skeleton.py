#!/usr/bin/env python3
"""Zero-dependency client skeleton for an ATRIUM <Tool> API (strategy §6 / Appendix B).

Copy to scripts/atrium_<verb>.py on the repo's agent-skill branch and fill in
every <placeholder>. Keep the contract intact:

  - Python 3 stdlib only (argparse, urllib.request, mimetypes, json, uuid, csv).
  - 3 retries with backoff on HTTP 502/503/504 only.
  - Long read timeout (inference/warmup is slow by design) — tune per service:
    300 s (model inference) / 900 s (pipelines) / 1800 s (LLM).
  - Exit codes: 0 success · 1 usage/input error · 2 unreachable · 3 server error.
  - Client-side size pre-check mirroring the server's MAX_UPLOAD_MB.
  - Per-item summaries to stderr; stdout stays clean for table/csv/json.

Exit codes:
    0 - success
    1 - client-side error (bad arguments, unreadable file)
    2 - server unreachable (connection refused / timeout)
    3 - server-side error (HTTP 4xx/5xx)
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_BASE_URL = os.environ.get("ATRIUM_<XX>_URL", "http://localhost:8000")
INPUT_SUFFIXES = {"<.ext>", "<.ext2>"}
MAX_UPLOAD_MB = 10  # mirrors the server's MAX_UPLOAD_MB default
RETRY_STATUS = {502, 503, 504}
RETRY_ATTEMPTS = 3
RETRY_WAIT_S = 10
TIMEOUT_S = 300  # tune per service, see module docstring


def build_multipart(fields: dict, file_field: str, file_path: Path) -> tuple[bytes, str]:
    """Encode form fields and one file as multipart/form-data using only the stdlib."""
    boundary = uuid.uuid4().hex
    lines = []
    for name, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        lines.append(b"")
        lines.append(str(value).encode())

    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    lines.append(f"--{boundary}".encode())
    lines.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'.encode())
    lines.append(f"Content-Type: {mime}".encode())
    lines.append(b"")
    lines.append(file_path.read_bytes())
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")

    body = b"\r\n".join(lines)
    return body, f"multipart/form-data; boundary={boundary}"


def http_json(url: str, data: bytes = None, content_type: str = None, timeout: int = TIMEOUT_S) -> dict:
    """POST (or GET when data is None) and decode JSON, with retry on 502/503/504."""
    last_error = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        request = urllib.request.Request(url, data=data, method="POST" if data else "GET")
        if content_type:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            if e.code in RETRY_STATUS and attempt < RETRY_ATTEMPTS:
                print(f"[retry {attempt}/{RETRY_ATTEMPTS}] HTTP {e.code}, waiting {RETRY_WAIT_S}s...", file=sys.stderr)
                time.sleep(RETRY_WAIT_S)
                last_error = f"HTTP {e.code}: {detail}"
                continue
            # <service-specific messaging: 429 → jobs/retry hint, 501 → CLI fallback, ...>
            print(f"Server error - HTTP {e.code}: {detail}", file=sys.stderr)
            sys.exit(3)
        except (urllib.error.URLError, TimeoutError) as e:
            print(
                f"Cannot reach the API at {url} ({e}).\nIs the server running? Start it with: bash scripts/server.sh",
                file=sys.stderr,
            )
            sys.exit(2)
    print(f"Server error after {RETRY_ATTEMPTS} attempts - {last_error}", file=sys.stderr)
    sys.exit(3)


def process_file(base_url: str, path: Path, **params) -> dict:
    """Pre-check, then upload one file to the primary endpoint (route by suffix
    when the service has several)."""
    if path.suffix.lower() not in INPUT_SUFFIXES:
        print(f"Skipping {path}: unsupported file type", file=sys.stderr)
        return {}
    size = path.stat().st_size
    if size > MAX_UPLOAD_MB * 1024 * 1024:
        print(f"Skipping {path}: exceeds the {MAX_UPLOAD_MB} MB server limit - <split/downscale hint>", file=sys.stderr)
        return {}
    body, content_type = build_multipart(params, file_field="file", file_path=path)
    return http_json(f"{base_url}/<primary_endpoint>", data=body, content_type=content_type)


def result_rows(path: Path, result: dict) -> list[tuple]:
    """Flatten the API response into (<col>, ...) rows for table/csv output."""
    raise NotImplementedError("<flatten the service's response shape>")


def print_table(rows: list[tuple], as_csv: bool) -> None:
    """Aligned table on stdout; use the csv module when a free-text column is emitted."""
    raise NotImplementedError("<render rows>")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="<input files description>")
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL}, env: ATRIUM_<XX>_URL)"
    )
    # <service-specific flags per strategy Appendix E>
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table", help="output format")
    parser.add_argument("--info", action="store_true", help="print service capabilities and limits, then exit")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if args.info:
        print(json.dumps(http_json(f"{base_url}/info", timeout=60), indent=2))
        return

    if not args.files:
        parser.error("no input files given (or use --info)")

    raw_results = {}
    rows = []
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        result = process_file(base_url, path)  # <pass service flags>
        if result:
            raw_results[path.name] = result
            rows.extend(result_rows(path, result))

    if not rows:
        print("No results produced.", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(raw_results, indent=2, ensure_ascii=False))
    else:
        print_table(rows, as_csv=(args.format == "csv"))


if __name__ == "__main__":
    main()
