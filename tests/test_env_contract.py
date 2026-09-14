"""The manifest and docs/k8s_deployment.md are the same environment contract in two
forms; nothing before this file cross-checked them (atrium-project#60).

WHY THIS EXISTS. `docs/templates/k8s/atrium-service.deployment.yaml`'s `env:` block and
`docs/k8s_deployment.md`'s "Environment variables" section were written by hand from the
same measurement and immediately started drifting: the 2026-09-10 inventory this issue
opened with already cited a stale manifest line range, and the "PORT ordering constraint"
premise it was built on was discharged by atrium-project#58 before the doc caught up.
A partner reading only the manifest and the doc has no way to notice either kind of
drift; this file is that way.

THE RAW-TEXT INVERSION. The house rule (`tests/test_e2e_entrypoints.py`) is to parse
workflows with `yaml.safe_load`, never grep, because PyYAML sees only executable content
and a text scan fires on the file's own prose. The manifest's environment contract runs
the other way: most of its variables live in YAML *comments*
(`# - name: HOST` / `#   value: "0.0.0.0"`), which `yaml.safe_load` silently drops. A
parser here would see only `PORT` and certify the file complete while blind to
everything the manifest documents as "how to turn this on." So this file reads the
manifest as raw text for the commented entries, and cross-checks that raw-text reading
against `yaml.safe_load` (test_the_raw_text_reader_is_not_vacuous below) rather than
trusting either method alone.

THE THREE REGISTRATIONS ALSO DRIFT SILENTLY. `scripts/revendor_shared.sh`'s own header
says adding a canonical file to `docs/templates/shared/` takes three registrations — a
`SHARED_FILES` row, a para-drift `diff -u` step, and a `ruff.toml` `[format] exclude`
row (Python files only; ruff format never touches JSON) — and that missing any one of
them is silent. Nothing before this file checked that the three registrations actually
agree; `service/healthcheck.py` sat in `SHARED_FILES` and para-drift, but missing from
`ruff.toml`'s exclude, until this file caught it.

Run: pytest tests/test_env_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_HUB_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _HUB_ROOT / "docs" / "templates" / "k8s" / "atrium-service.deployment.yaml"
_DEPLOYMENT_DOC = _HUB_ROOT / "docs" / "k8s_deployment.md"
_REVENDOR_SCRIPT = _HUB_ROOT / "scripts" / "revendor_shared.sh"
_PARA_DRIFT = _HUB_ROOT / ".github" / "workflows" / "para-drift.reusable.yml"
_RUFF_TOML = _HUB_ROOT / "docs" / "templates" / "ruff.toml"

# Manifest `env:` entries, live or commented — `- name: XXX` where XXX is an
# environment-variable-shaped identifier. This deliberately excludes `name: http` (a
# port name, no leading `-`) and `name: atrium-<tool>-api` (metadata, lowercase/hyphenated)
# without needing to scope to the env: block specifically, because no other `- name: X`
# in this file names an ALL_CAPS identifier.
_ENV_ENTRY = re.compile(r"^\s*(?P<hash>#\s*)?-\s*name:\s*([A-Z][A-Z0-9_]*)\b", re.MULTILINE)

# Table A rows: | `NAME` | default | manifest-status | description |
_TABLE_ROW = re.compile(
    r"^\|\s*`([A-Z][A-Z0-9_]*)`\s*\|[^|]*\|\s*([^|]*?)\s*\|",
    re.MULTILINE,
)

# Rows in Table A whose "In the template manifest" cell is allowed to read "—" (not
# present at all) rather than "set" or "commented" — each is documented in
# k8s_deployment.md as a deliberate absence, with a stated reason.
_DELIBERATELY_ABSENT_FROM_MANIFEST = {
    "RELOAD": "no correct value for a Deployment (k8s_deployment.md, Table A)",
    "HEALTHCHECK_PATH": "irrelevant under Kubernetes, which never reads a HEALTHCHECK",
    "MAX_UPLOAD_BYTES": "deprecated fallback; the manifest should not introduce it",
}


def _manifest_entries() -> tuple[set[str], set[str]]:
    """Return (live names, commented-out names) from the manifest's raw text."""
    live: set[str] = set()
    commented: set[str] = set()
    for match in _ENV_ENTRY.finditer(_MANIFEST.read_text(encoding="utf-8")):
        name = match.group(2)
        (commented if match.group("hash") else live).add(name)
    return live, commented


def _doc_chunk(section_marker: str) -> str:
    """The markdown table immediately after a section marker, up to its blank line.

    Walks LINES from the marker onward with no length cap — an earlier version sliced
    a fixed 4000-character window, which silently truncated Table B (long enough to
    sit right at that boundary) and produced a false positive: rows past the cut were
    invisible to every check below, not absent from the doc. A table growing past an
    arbitrary character budget is exactly the kind of drift this file exists to catch,
    so the reader must not itself have a budget.
    """
    text = _DEPLOYMENT_DOC.read_text(encoding="utf-8")
    start = text.index(section_marker)
    lines: list[str] = []
    started = False
    for line in text[start:].split("\n"):
        if line.strip().startswith("|"):
            started = True
            lines.append(line)
        elif started:
            break
    return "\n".join(lines)


def _table_a_status() -> dict[str, str]:
    """Table A only: `NAME -> "In the template manifest"` cell (its column 3)."""
    chunk = _doc_chunk("**Table A — common to all five**")
    rows: dict[str, str] = {}
    for line in chunk.splitlines():
        m = _TABLE_ROW.match(line)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


def _names_in_table(section_marker: str) -> set[str]:
    """Every backtick-quoted ALL_CAPS name anywhere in the table, any column.

    Table B's variable name is its SECOND column (the first is the repo name, blank on
    continuation rows), so a column-1-only parse misses everything in it.
    """
    chunk = _doc_chunk(section_marker)
    return set(re.findall(r"`([A-Z][A-Z0-9_]*)`", chunk))


def test_every_manifest_variable_is_in_the_doc():
    """Table A ∪ Table B must name every variable the manifest sets or comments out."""
    live, commented = _manifest_entries()
    manifest_names = live | commented

    table_a = _names_in_table("**Table A — common to all five**")
    table_b = _names_in_table("**Table B — per-repo operator deltas.**")
    documented = table_a | table_b

    missing = sorted(manifest_names - documented)
    assert not missing, (
        "docs/k8s_deployment.md documents nothing about these manifest variables, so a "
        f"partner reading only the doc cannot find them: {missing}"
    )


def test_every_table_a_variable_is_in_the_manifest_or_declared_absent():
    """The inverse direction: nothing in Table A may be fiction."""
    live, commented = _manifest_entries()
    manifest_names = live | commented
    table_a = _table_a_status()

    problems = []
    for name, manifest_status in table_a.items():
        in_manifest = name in manifest_names
        declared_absent = name in _DELIBERATELY_ABSENT_FROM_MANIFEST
        if not in_manifest and not declared_absent:
            problems.append(
                f"{name}: Table A but not in the manifest, and not in "
                "_DELIBERATELY_ABSENT_FROM_MANIFEST — add a reason or add it to the manifest"
            )
        if in_manifest and "—" in manifest_status and name not in _DELIBERATELY_ABSENT_FROM_MANIFEST:
            problems.append(f"{name}: Table A says '—' but the manifest names it")
    assert not problems, "\n".join(problems)


def test_the_raw_text_reader_is_not_vacuous():
    """Confirm the two reading methods actually disagree the way this file assumes.

    Without this, a change that broke the raw-text regex (renamed the manifest, changed
    its comment indentation) would leave both tests above passing vacuously — green
    because nothing was found on either side, not because the contract held. See
    tests/test_e2e_entrypoints.py's `test_the_e2e_lane_is_actually_covered` for the same
    idiom against a different subject.
    """
    assert _MANIFEST.exists(), f"{_MANIFEST} not found — did it move?"

    doc = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
    live_via_yaml = {e["name"] for e in doc["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert live_via_yaml == {"PORT"}, (
        f"expected yaml.safe_load to see exactly one live env var (PORT), saw {live_via_yaml} "
        "— if this changed on purpose, the raw-text reader still has to account for it"
    )

    live, commented = _manifest_entries()
    assert live == live_via_yaml, (
        f"the raw-text reader and yaml.safe_load disagree on LIVE entries: raw={live} yaml={live_via_yaml}"
    )
    assert len(commented) >= 6, (
        f"the raw-text reader found only {len(commented)} commented-out env entries "
        "(expected >= 6) — PyYAML cannot see these at all, so if this count dropped to "
        "zero the manifest's documented-but-off variables became invisible to every "
        "check in this file, not just this one"
    )


def _shared_files_from_revendor_script() -> set[str]:
    text = _REVENDOR_SCRIPT.read_text(encoding="utf-8")
    start = text.index("declare -A SHARED_FILES=(")
    block = text[start : text.index("\n)", start)]
    return set(re.findall(r'\["([A-Za-z0-9_.]+)"\]=', block))


def _para_drift_targets() -> set[str]:
    text = _PARA_DRIFT.read_text(encoding="utf-8")
    return set(re.findall(r"hub-repo/docs/templates/shared/([A-Za-z0-9_./]+)", text))


def _ruff_exclude_basenames() -> set[str]:
    """Basenames named specifically in [format] exclude, excluding the catch-all glob.

    Matched by the section HEADER at the start of a line, not any mention of the string
    "[format]" — this file's own comments (:6, :13) talk about the section by name
    before it exists, and a plain substring search finds those first.
    """
    text = _RUFF_TOML.read_text(encoding="utf-8")
    header = re.search(r"^\[format\]\s*$", text, re.MULTILINE)
    assert header, "docs/templates/ruff.toml has no [format] section header"
    start = text.index("exclude = [", header.end())
    end = text.index("\n]", start)
    entries = re.findall(r'"([^"*]+\.(?:py|json))"', text[start:end])
    return {Path(e).name for e in entries}


def test_the_three_shared_file_registrations_agree():
    """scripts/revendor_shared.sh's own promise: three registrations, kept in step.

    Missing any one is silent (its header's own words) — this is what makes that true
    rather than aspirational. atrium_rocrate.py was in SHARED_FILES and absent from
    para-drift for its first four days; this fails on exactly that shape of gap.
    """
    shared_files = _shared_files_from_revendor_script()
    para_drift = _para_drift_targets()
    ruff_names = _ruff_exclude_basenames()

    only_in_shared_files = shared_files - para_drift
    only_in_para_drift = para_drift - shared_files
    assert not only_in_shared_files, f"in SHARED_FILES but has no para-drift diff step: {sorted(only_in_shared_files)}"
    assert not only_in_para_drift, (
        f"has a para-drift diff step but is not in SHARED_FILES: {sorted(only_in_para_drift)}"
    )

    # Only .py files need a [format] exclude row — ruff format never touches .json.
    shared_py_files = {n for n in shared_files if n.endswith(".py")}
    only_in_shared_files = shared_py_files - ruff_names
    assert not only_in_shared_files, (
        "in SHARED_FILES (as a .py file) but not in docs/templates/ruff.toml's [format] "
        f"exclude, so `ruff format` will reflow the vendored copy to whichever repo's "
        f"line-length committed it last: {sorted(only_in_shared_files)}"
    )


def test_the_registration_check_is_not_vacuous():
    shared_files = _shared_files_from_revendor_script()
    assert len(shared_files) >= 10, (
        f"only found {len(shared_files)} SHARED_FILES entries — the parser may have broken against a script edit"
    )
    assert "atrium_service.py" in shared_files
    assert "test_logging_contract.py" in shared_files
