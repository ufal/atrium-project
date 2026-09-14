"""tests/test_shared_manifest.py — the manifest is the one list; keep it the one list.

atrium-project#59: before `docs/templates/shared/MANIFEST.json` existed, the canonical
shared-file set was written out by hand in (at least) four places — `scripts/
revendor_shared.sh`'s three array literals, `tools/skill_drift_check.py`'s SHARED_FILES
tuple, `.github/workflows/para-drift.reusable.yml`'s sixteen `diff -u` steps, and
`docs/templates/ruff.toml`'s `[format] exclude` and `[lint.isort] known-first-party`
lists — and each addition since #51 updated some of them and not others. `#51`, `#54`
and `#55` each landed a new canonical file; by the time #59 was filed,
`tools/skill_drift_check.py`'s hand-written tuple named 5 of what para-drift already
guarded 16 of. Extending the manifest is now one edit; this file is what makes the
OTHER four places' silent falling-behind structurally impossible instead of merely
unlikely — every one of the checks below was deliberately broken (an entry removed,
a ruff.toml row deleted, a `diff -u` step reintroduced) and confirmed to fail before
being trusted, the same standard every guard built this round was held to.

Run: pytest tests/test_shared_manifest.py
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIR = REPO_ROOT / "docs" / "templates" / "shared"
MANIFEST_PATH = SHARED_DIR / "MANIFEST.json"
RUFF_TOML = REPO_ROOT / "docs" / "templates" / "ruff.toml"
PARA_DRIFT = REPO_ROOT / ".github" / "workflows" / "para-drift.reusable.yml"
REVENDOR = REPO_ROOT / "scripts" / "revendor_shared.sh"

sys.path.insert(0, str(REPO_ROOT / "tools"))
from shared_manifest import ManifestError, load_manifest  # noqa: E402


@pytest.fixture(scope="module")
def manifest_files() -> list[dict]:
    return load_manifest(MANIFEST_PATH)


def test_manifest_loads_and_validates():
    """A malformed manifest (duplicate canonical name, duplicate dest, missing
    field) must fail loudly here rather than being silently misread by one of
    the three consumers in three different ways."""
    load_manifest(MANIFEST_PATH)  # raises ManifestError on any structural defect


def test_manifest_loader_rejects_a_duplicate_dest(tmp_path):
    """Proves ManifestError actually fires, not just that the real manifest
    happens not to trigger it -- a validator with no failing fixture is
    indistinguishable from one that is not wired up (the exact standard
    tests/test_workflow_lint.py's own docstring holds every rule in this repo to).
    """
    broken = tmp_path / "MANIFEST.json"
    broken.write_text(
        '{"files": ['
        '{"canonical": "a.py", "dest": "same.py", "selftest": false, '
        '"ruff_format_exclude": true, "isort_first_party": null, "preconditions": []}, '
        '{"canonical": "b.py", "dest": "same.py", "selftest": false, '
        '"ruff_format_exclude": true, "isort_first_party": null, "preconditions": []}'
        "]}"
    )
    with pytest.raises(ManifestError, match="duplicate dest"):
        load_manifest(broken)


def test_every_shared_directory_file_is_in_the_manifest(manifest_files):
    """The directory listing is the ground truth for what exists; a file present
    on disk with no manifest row is exactly #59's original defect — a canonical
    file (docs/templates/shared/test_atrium_service.py, historically) registered
    nowhere at all. `_comment` is the manifest's own documentation, not a file.
    """
    on_disk = {p.name for p in SHARED_DIR.iterdir() if p.is_file() and p.name != "MANIFEST.json"}
    in_manifest = {entry["canonical"] for entry in manifest_files}
    missing_from_manifest = sorted(on_disk - in_manifest)
    missing_from_disk = sorted(in_manifest - on_disk)
    assert not missing_from_manifest, (
        f"docs/templates/shared/ contains file(s) with no MANIFEST.json row: "
        f"{missing_from_manifest} — every canonical file needs exactly one row, "
        f"or it is enforced nowhere (atrium-project#59)"
    )
    assert not missing_from_disk, (
        f"MANIFEST.json names file(s) not present in docs/templates/shared/: {missing_from_disk}"
    )


def _ruff_list(toml_path: Path, *keys: str) -> list[str]:
    """Read a TOML array of strings at a dotted key path (e.g. "format", "exclude")."""
    with open(toml_path, "rb") as fh:
        doc = tomllib.load(fh)
    node = doc
    for key in keys:
        node = node[key]
    return list(node)


def test_ruff_format_exclude_matches_the_manifest(manifest_files):
    expected = {entry["dest"] for entry in manifest_files if entry["ruff_format_exclude"]}
    actual = set(_ruff_list(RUFF_TOML, "format", "exclude"))
    # The hub-only catch-all glob covers docs/templates/shared/*.py directly; it is
    # not a per-file dest path and has no manifest row of its own.
    actual.discard("docs/templates/shared/*.py")
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    assert not missing, f"docs/templates/ruff.toml's [format] exclude is missing: {missing}"
    assert not extra, (
        f"docs/templates/ruff.toml's [format] exclude names {extra}, which the "
        f"manifest does not mark ruff_format_exclude: true for — either the manifest "
        f"or ruff.toml is stale"
    )


def test_ruff_known_first_party_matches_the_manifest(manifest_files):
    expected = {entry["isort_first_party"] for entry in manifest_files if entry["isort_first_party"]}
    actual = set(_ruff_list(RUFF_TOML, "lint", "isort", "known-first-party"))
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    assert not missing, f"docs/templates/ruff.toml's known-first-party is missing: {missing}"
    assert not extra, f"docs/templates/ruff.toml's known-first-party names {extra}, unknown to the manifest"


def test_para_drift_reads_the_manifest_not_a_hand_written_list():
    """Structural, not a grep for a magic number: asserts the workflow's shared-files
    step invokes tools/shared_manifest.py, and that no individual per-file `diff -u
    tool-repo/<X> hub-repo/docs/templates/shared/<X>` step survives beside it. A
    literal `diff -u` inside the step's OWN multi-line `run:` block (reading the
    loop variable, not a hardcoded filename) does not match this pattern and is not
    what this guards against — the sixteen hand-written STEPS are.
    """
    text = PARA_DRIFT.read_text()
    assert "tools/shared_manifest.py" in text, (
        "para-drift.reusable.yml no longer invokes tools/shared_manifest.py — has "
        "someone reintroduced a hand-written file list?"
    )
    hand_written_steps = re.findall(r"run:\s*diff -u tool-repo/\S+ hub-repo/docs/templates/shared/\S+", text)
    assert not hand_written_steps, (
        f"para-drift.reusable.yml has {len(hand_written_steps)} hand-written per-file "
        f"`diff -u` step(s) again, defeating the one-manifest-one-loop change "
        f"(atrium-project#59, roadmap D5): {hand_written_steps}"
    )


def test_para_drift_selftest_targets_match_the_manifest(manifest_files):
    """The workflow's --selftest branch is data-driven (`if [ "$selftest" = "1" ]`),
    so there is no per-file step name to grep for any more — instead, assert the
    manifest's own selftest: true files actually support `--selftest`, which is
    what would break silently if a canonical module's CLI changed shape.
    """
    selftest_dests = [entry["dest"] for entry in manifest_files if entry["selftest"]]
    assert selftest_dests, "no manifest entry has selftest: true — did an edit drop the flag?"
    for dest in selftest_dests:
        canonical_path = SHARED_DIR / Path(dest).name
        assert canonical_path.is_file(), f"selftest target {dest} has no canonical file at {canonical_path}"
        text = canonical_path.read_text(encoding="utf-8")
        assert "--selftest" in text, (
            f"MANIFEST.json marks {dest} selftest: true, but {canonical_path.name} "
            f"does not appear to implement --selftest any more"
        )


def test_revendor_shared_has_no_hand_written_file_list():
    """The three array literals this script used to define by hand must be GONE,
    not merely unused — a stray `declare -A SHARED_FILES=( ["x"]="y" ... )` left
    behind after switching to the manifest loader would silently win if the loader
    were ever accidentally skipped, and nobody would notice until the two disagreed.
    """
    text = REVENDOR.read_text()
    assert "tools/shared_manifest.py" in text, "scripts/revendor_shared.sh no longer loads the manifest"
    literal_entries = re.findall(r'\["[A-Za-z0-9_.]+"\]="[^"]+"', text)
    assert not literal_entries, (
        f"scripts/revendor_shared.sh still contains hand-written array entries: "
        f"{literal_entries} — SHARED_FILES/PRECONDITIONS must be populated only from "
        f"the manifest loader"
    )


# word-form counts still in use in exactly one known prose spot (page-classification's
# ruff.toml); digit-form in the hub's own. Both cited by file so a THIRD phrasing
# elsewhere is a silent miss reported nowhere — not a design goal here, just the
# current, small, known set.
_WORD_NUMBERS = {
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
}

_COUNT_PHRASE = re.compile(r"para-drift\.reusable\.yml`? requires (?:the |these )?(\d+|[a-z]+) files?", re.IGNORECASE)


def _stated_count(text: str) -> int | None:
    match = _COUNT_PHRASE.search(text)
    if not match:
        return None
    token = match.group(1)
    if token.isdigit():
        return int(token)
    return _WORD_NUMBERS.get(token.lower())


_SIBLING_ROOT = Path(os.environ.get("ATRIUM_SIBLING_ROOT", REPO_ROOT.parent))


@pytest.mark.parametrize(
    "toml_path",
    [
        RUFF_TOML,
        _SIBLING_ROOT / "atrium-page-classification" / "ruff.toml",
    ],
    ids=lambda p: str(p),
)
def test_ruff_toml_prose_count_matches_the_manifest(toml_path: Path, manifest_files):
    if not toml_path.is_file():
        pytest.skip(f"{toml_path} not present (sibling checkout absent)")
    stated = _stated_count(toml_path.read_text())
    if stated is None:
        pytest.skip(f"{toml_path} states no file count in the expected phrasing")
    assert stated == len(manifest_files), (
        f"{toml_path} says para-drift requires {stated} files, but the manifest "
        f"now lists {len(manifest_files)} — this comment is a citation of a fact "
        f"the manifest owns, and it drifted"
    )
