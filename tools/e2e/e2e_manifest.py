"""Record which images an E2E run used, by digest (atrium-project#81 B.3, #77).

The E2E lanes pull images by moving tags (`latest`, `test`, a version). A tag says nothing about
which build ran, so a green run could not name the set of images that passed together. This
script records it: for each image the run referenced, the digest the runner pulled, the image's
creation time and the source ref it was built from (`ATRIUM_RUNNER_REF`, set at build time), and
the version the service reported at `/info` when the lane saved that answer. The result is
`e2e-manifest.json`, uploaded as an artifact, and a table in the job summary. The manifest of a
green run at a version tag is the candidate set AMČR approves for the pilot (`docs_site/pilot.md`).

It reports and never fails the run: an image the run did not pull is recorded as not pulled.

Usage (inside a lane, after the stages):
    python tools/e2e/e2e_manifest.py --lane pipeline --tag latest --status success \\
        --image ghcr.io/ufal/atrium-page-classification:latest \\
        --info ghcr.io/ufal/atrium-keyword-extract-api:latest=work/keywords_stat_info.json \\
        --out work/e2e-manifest.json --summary "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

_ENV_KEYS = {"ATRIUM_RUNNER_REF": "source_ref", "ATRIUM_RUNNER_IMAGE": "runner_image"}


def docker_inspect(ref: str) -> Optional[dict]:
    """`docker image inspect` of one local image, or None when the runner does not have it."""
    try:
        done = subprocess.run(["docker", "image", "inspect", ref], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    try:
        found = json.loads(done.stdout)
    except json.JSONDecodeError:
        return None
    return found[0] if found else None


def _repository(ref: str) -> str:
    """`ghcr.io/ufal/x:tag` or `ghcr.io/ufal/x@sha256:…` → `ghcr.io/ufal/x`."""
    name = ref.split("@", 1)[0]
    last = name.rsplit("/", 1)[-1]
    return name[: len(name) - len(last)] + last.split(":", 1)[0]


def entry(ref: str, inspected: Optional[dict], info: Optional[dict] = None) -> dict:
    """One manifest row for an image reference."""
    row: Dict[str, Optional[str]] = {"image": ref, "pulled": inspected is not None}
    if inspected is None:
        return row
    repository = _repository(ref)
    digests = [d for d in inspected.get("RepoDigests") or [] if _repository(d) == repository]
    row["digest"] = digests[0].split("@", 1)[1] if digests else None
    row["created"] = inspected.get("Created")
    env = dict(item.split("=", 1) for item in (inspected.get("Config") or {}).get("Env") or [] if "=" in item)
    for key, field in _ENV_KEYS.items():
        row[field] = env.get(key) or None
    if info is not None:
        row["info_version"] = info.get("version")
    return row


def build(
    refs: List[str],
    infos: Dict[str, Path],
    lane: str,
    tag: str,
    status: str,
    inspect: Optional[Callable[[str], Optional[dict]]] = None,
    environ: Optional[Dict[str, str]] = None,
) -> dict:
    """The whole manifest: the run's identity and one row per image, in the order given."""
    inspect = inspect or docker_inspect
    env = os.environ if environ is None else environ
    rows = []
    for ref in refs:
        info = None
        path = infos.get(ref)
        if path is not None and path.is_file():
            try:
                info = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                info = None
        rows.append(entry(ref, inspect(ref), info))
    run = None
    if env.get("GITHUB_RUN_ID"):
        run = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{env.get('GITHUB_REPOSITORY')}/actions/runs/{env['GITHUB_RUN_ID']}"
    return {
        "lane": lane,
        "image_tag": tag,
        "status": status,
        "run": run,
        "hub_commit": env.get("GITHUB_SHA"),
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "images": rows,
    }


def summary(manifest: dict) -> str:
    """The job-summary table."""
    lines = [
        f"### Images of this run ({manifest['lane']}, tag `{manifest['image_tag']}`, {manifest['status']})",
        "",
        "| Image | Digest | Source ref | `/info` version |",
        "|---|---|---|---|",
    ]
    for row in manifest["images"]:
        if not row["pulled"]:
            lines.append(f"| `{row['image']}` | not pulled | — | — |")
            continue
        digest = f"`{row['digest']}`" if row.get("digest") else "no registry digest"
        lines.append(
            f"| `{row['image']}` | {digest} | {row.get('source_ref') or '—'} | {row.get('info_version') or '—'} |"
        )
    lines += ["", "The set as JSON: the `e2e-manifest` artifact of this run."]
    return "\n".join(lines) + "\n"


def _info_arg(value: str) -> tuple:
    ref, sep, path = value.rpartition("=")
    if not sep or not ref:
        raise argparse.ArgumentTypeError(f"--info wants IMAGE=PATH, got {value!r}")
    return ref, Path(path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--lane", required=True, help="which E2E lane (pipeline, digital)")
    parser.add_argument("--tag", required=True, help="the image tag the run asked for")
    parser.add_argument("--status", default="unknown", help="the job status so far (job.status)")
    parser.add_argument("--image", action="append", default=[], required=True, help="an image reference; repeat")
    parser.add_argument("--info", action="append", default=[], type=_info_arg, help="IMAGE=PATH of a saved /info")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=None, help="append the table here ($GITHUB_STEP_SUMMARY)")
    args = parser.parse_args(argv)

    manifest = build(args.image, dict(args.info), args.lane, args.tag, args.status)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    table = summary(manifest)
    if args.summary is not None:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(table)
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
