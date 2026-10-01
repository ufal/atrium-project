"""Build ATRIUM's RO-Crates and check them with the RO-Crate validator (atrium-project#71).

The pilot baseline agreed with AMČR is RO-Crate 1.2 with Process Run Crate 0.5. That is the
newest pair the validator (`roc-validator`, pinned in tools/ci/requirements-rocrate.txt) checks.
This script is the one place it runs. The validator stays out of every tool repository:
`atrium_rocrate.py` is stdlib-only and drift-gated by byte comparison, so its conformance is
checked here, in the hub's CI, against real output.

Each crate is validated TWICE, once per profile, never in one merged run:

  * `ro-crate-1.2`: the specification;
  * `process-run-crate-0.5 --disable-profile-inheritance`: the profile. roc-validator declares
    it a profile of RO-Crate **1.1**, and with inheritance on, it would demand the descriptor's
    `conformsTo` be 1.1.

Every issue is printed (a GitHub annotation in CI). A profile's GATE decides which ones fail the
job: `required` fails on a MUST only, `recommended` on a SHOULD as well.

Two modes:

  * `--samples DIR`, for the hub self-check. Builds the module's sample document crate (with
    its files in place), the run crate (with its nested crate and paradata file), the record
    fragment under a stub root, and a service's CreateAction under a stub root. The profile is
    gated at SHOULD, to prove the builder can meet it; RO-Crate 1.2 at MUST, since its remaining
    SHOULDs are the host's to meet (a `publisher`, say).
  * `--record FINAL --paradata P…`, for the E2E. Builds the fragment of the final record, which
    is what AMČR embeds in its record crate, from the record and every stage's paradata file.
    The fragment is wrapped in a stub root and both profiles are gated at MUST, since real runs
    may lack a SHOULD (no ATRIUM_RUN_AGENT, an image without a recorded tag).

Usage:
    python tools/ci/rocrate_check.py --samples "$RUNNER_TEMP/crates"
    python tools/ci/rocrate_check.py --record work/doc_json/5_llm.json \\
        --paradata work/paradata/*.json --out work/crate
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_SHARED_DIR = Path(__file__).resolve().parents[2] / "docs" / "templates" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import atrium_rocrate as rc  # noqa: E402  (needs the path above)

#: (profile id, extra validator arguments). The PRC run disables inheritance; see the docstring.
PROFILES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("ro-crate-1.2", ()),
    ("process-run-crate-0.5", ("--disable-profile-inheritance",)),
)

#: Severities in the validator's report, weakest first.
_SEVERITY_RANK = {"OPTIONAL": 0, "RECOMMENDED": 1, "REQUIRED": 2}
_GATE_RANK = {"required": 2, "recommended": 1}


def _annotate(level: str, message: str) -> None:
    """A GitHub annotation in CI, a plain line elsewhere."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::{}::{}".format(level, message.replace("\n", " ")))
    else:
        print("{}: {}".format(level.upper(), message))


def validate(crate_dir: Path, gates: Dict[str, str], validator: Sequence[str]) -> int:
    """Validate one crate directory against every profile; return the number of gating issues."""
    failures = 0
    for profile, extra in PROFILES:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            cmd = [
                *validator,
                "validate",
                "-p",
                profile,
                *extra,
                "-l",
                "recommended",
                "--no-paging",
                "-f",
                "json",
                "-o",
                str(report_path),
                str(crate_dir),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if not report_path.is_file():
                _annotate(
                    "error",
                    "{} / {}: the validator wrote no report:\n{}".format(crate_dir.name, profile, proc.stderr[-2000:]),
                )
                failures += 1
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
        gate = _GATE_RANK[gates[profile]]
        gating = 0
        for issue in report.get("issues") or []:
            severity = str(issue.get("severity") or "REQUIRED").upper()
            check = issue.get("check")
            check_id = check.get("identifier") if isinstance(check, dict) else check
            where = issue.get("violatingEntity") or ""
            line = "{} / {} [{}] {}: {} {}".format(
                crate_dir.name, profile, severity, check_id, issue.get("message"), where
            )
            if _SEVERITY_RANK.get(severity, 2) >= gate:
                gating += 1
                _annotate("error", line)
            else:
                _annotate("warning", line)
        print("{} / {}: {} issue(s) at or above {}".format(crate_dir.name, profile, gating, gates[profile]))
        failures += gating
    return failures


def build_samples(out: Path) -> List[Path]:
    """The module's own crates, each a directory with its files in place."""
    record = rc._sample_record()
    paradata = rc._sample_paradata()
    license_url = record["provenance"]["license_url"]
    dirs: List[Path] = []

    doc = out / "document"
    for path in record["derived_from"].values():
        target = doc / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n" if path.endswith(".json") else "<TEI/>\n", encoding="utf-8")
    rc.write_crate(rc.document_crate(record, paradata=paradata, data_dir=str(doc)), str(doc))
    dirs.append(doc)

    run = out / "run"
    (run / "paradata").mkdir(parents=True, exist_ok=True)
    (run / "paradata" / "run.json").write_text("{}\n", encoding="utf-8")
    rc.write_crate(rc.document_crate(record, paradata=paradata), str(run / record["doc_id"]))
    stage = dict(paradata[0], order=1)
    run_record = {
        "run_id": stage["run_id"],
        "run_uuid": "urn:uuid:0e1d2c3b-4a59-4687-9a0b-1c2d3e4f5a6b",
        "run_agent": stage["run_agent"],
        "start_time": stage["start_time"],
        "end_time": stage["end_time"],
        "license": record["provenance"]["license"],
        "license_url": license_url,
        "pipeline_stages": [stage],
    }
    rc.write_crate(
        rc.run_crate([record], run_paradata=run_record, paradata_refs=["paradata/run.json"], data_dir=str(run)),
        str(run),
    )
    dirs.append(run)

    fragment = out / "fragment"
    rc.write_crate(
        rc.wrap_fragment(
            rc.document_crate(record, paradata=paradata, fragment=True),
            name="ATRIUM record fragment (stub root)",
            description="The sample record's fragment under a stub root.",
            license=license_url,
            date_published="2026-07-24",
        ),
        str(fragment),
    )
    dirs.append(fragment)

    action = rc.create_action(
        paradata[0],
        inputs=[
            rc.file_entity("page.alto.xml", b"<alto/>", media_type="application/alto+xml"),
            rc.record_entity("C-1"),
        ],
        outputs=rc.block_entities(["lines", "pages"]),
    )
    problems = rc.action_problems(action)
    if problems:
        raise SystemExit("the sample CreateAction breaks the shared contract: " + "; ".join(problems))
    service = out / "service-action"
    rc.write_crate(
        rc.wrap_fragment(
            rc.action_fragment(action),
            name="One service call (stub root)",
            description="A service's CreateAction, as AMČR embeds it.",
            license=license_url,
            date_published="2026-07-24",
        ),
        str(service),
    )
    dirs.append(service)
    return dirs


def _paradata_records(paths: Sequence[str]) -> List[dict]:
    """The paradata records among `paths`: JSON objects with a `program` or `pipeline`."""
    records = []
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _annotate("warning", "{}: not a JSON file, skipped".format(path))
            continue
        if isinstance(data, dict) and (data.get("program") or data.get("pipeline")):
            records.append(data)
    return records


def build_record(record_path: Path, paradata: Sequence[str], out: Path) -> Path:
    """The fragment of a real record, under a stub root."""
    record = json.loads(record_path.read_text(encoding="utf-8"))
    provenance = record.get("provenance") or {}
    fragment = rc.document_crate(record, paradata=_paradata_records(paradata), fragment=True)
    crate = rc.wrap_fragment(
        fragment,
        name="ATRIUM record fragment {} (stub root)".format(record.get("doc_id") or ""),
        description="The fragment of the E2E's final record under a stub root, as AMČR's record crate embeds it.",
        license=str(provenance.get("license_url") or provenance.get("license") or "unspecified"),
        date_published=rc._date_published(record),
    )
    rc.write_crate(crate, str(out))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--samples", metavar="DIR", type=Path, help="build and check the module's sample crates")
    mode.add_argument("--record", metavar="RECORD", type=Path, help="build and check one record's fragment")
    parser.add_argument(
        "--paradata", nargs="*", default=[], metavar="JSON", help="with --record: every stage's paradata"
    )
    parser.add_argument("--out", type=Path, default=None, help="with --record: where to write the crate")
    parser.add_argument(
        "--validator",
        default="rocrate-validator",
        help="the validator command (default: rocrate-validator, from tools/ci/requirements-rocrate.txt)",
    )
    args = parser.parse_args(argv)

    validator = shlex.split(args.validator)
    if not shutil.which(validator[0]):
        raise SystemExit("{} not found: pip install -r tools/ci/requirements-rocrate.txt".format(validator[0]))

    if args.samples:
        crates = build_samples(args.samples)
        gates = {"ro-crate-1.2": "required", "process-run-crate-0.5": "recommended"}
    else:
        out = args.out or Path(tempfile.mkdtemp(prefix="atrium-crate-"))
        crates = [build_record(args.record, args.paradata, out)]
        gates = {"ro-crate-1.2": "required", "process-run-crate-0.5": "required"}

    failures = sum(validate(crate, gates, validator) for crate in crates)
    if failures:
        print("❌ {} gating validator issue(s) across {} crate(s)".format(failures, len(crates)))
        return 1
    print("✅ {} crate(s) conform to RO-Crate 1.2 and Process Run Crate 0.5".format(len(crates)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
