"""tests/test_env_doc_contract.py — the manifest and the doc are one contract,
checked, not just claimed (atrium-project#60).

`docs/templates/k8s/atrium-service.deployment.yaml`'s `env:` block says so itself:
*"This block and the 'Environment variables' table in docs/k8s_deployment.md are the
same contract in two forms ... a variable in one and not the other is a bug in
whichever was edited last, and atrium-project#60's CI guard (tests/test_env_contract.py)
fails on exactly that."* It does not. `tests/test_env_contract.py` — hub-local and
vendored into all five tool repos — checks a repo's `.env.example` against its own
service-layer code; it never opens `k8s_deployment.md` or the manifest, so a comment
claiming enforcement that does not exist is exactly the kind of drift #59 and #60 both
spent this round closing elsewhere. This file is the guard the sentence describes.

HUB-LOCAL, NOT VENDORED. Unlike `tests/test_env_contract.py`, this file compares two
hub-owned documents against each other and, for the Table B check, against the five
sibling repos' `.env.example` files — there is nothing repo-specific to vendor, and a
copy in each tool repo would just re-run the same hub-side comparison five times.

THREE REGIONS IN ONE `env:` BLOCK. The manifest's `env:` block is not one flat list —
it is Table A's six operator knobs, then a `# --- Backing services` marked region
(atrium-project#63's URLs), then a `# --- Secrets:` marked region (llm-enrich's key).
Table A only documents the first region; the other two are Table B's job. Treating
the whole block as "must all be in Table A" would be a false invariant — this file
checks each region against the table that actually documents it.

TABLE A'S OWN THREE-WAY STATE, NOT A FLAT MEMBERSHIP CHECK. Three of Table A's nine
rows (`RELOAD`, `HEALTHCHECK_PATH`, `MAX_UPLOAD_BYTES`) are marked "**—**" or
"**—, deliberately**" — genuinely ABSENT from the manifest by design, not merely
commented. A naive "every Table A name must be in the manifest, set or commented"
check would be wrong for exactly these three. `test_manifest_matches_table_a_state`
checks all three states — set / commented / absent — bidirectionally instead.

Run: pytest tests/test_env_doc_contract.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "templates" / "k8s" / "atrium-service.deployment.yaml"
DEPLOYMENT_DOC = REPO_ROOT / "docs" / "k8s_deployment.md"

_NAME_LINE = re.compile(r"^[ \t]*(#[ \t]*)?-[ \t]*name:[ \t]*([A-Z_][A-Z0-9_]*)", re.MULTILINE)
# [ \t]*, not \s*, between the pieces above: \s matches a newline too, so an
# EMPTY standalone "            #" comment line directly above an ACTIVE
# "            - name: X" line let the hashmark group absorb the newline and
# misread the active line below as commented. Caught only by deliberately
# uncommenting a Table A entry and confirming this test goes red — it did not,
# the first time this was written, for exactly that reason.


def _manifest_env_block() -> str:
    """The full `env:` block body, all three regions, comments included."""
    text = MANIFEST.read_text()
    match = re.search(r"\n(\s*)env:\n(.*?)\n\1\S", text, re.DOTALL)
    assert match, f"no `env:` block found in {MANIFEST.name} — this check needs one"
    return match.group(2)


def _split_regions(block: str) -> tuple[str, str, str]:
    """Table A / backing-services / secrets, in the order the manifest itself uses."""
    backing_marker = "# --- Backing services"
    secrets_marker = "# --- Secrets:"
    assert backing_marker in block, f"manifest env: block lost its {backing_marker!r} marker"
    assert secrets_marker in block, f"manifest env: block lost its {secrets_marker!r} marker"
    backing_idx = block.index(backing_marker)
    secrets_idx = block.index(secrets_marker)
    assert backing_idx < secrets_idx, "manifest env: block's regions are out of order"
    return block[:backing_idx], block[backing_idx:secrets_idx], block[secrets_idx:]


def _names_with_state(region: str) -> dict[str, bool]:
    """name -> is_active (True: a live `- name:`; False: a commented `# - name:`).

    `re.findall` returns "" (not None) for an optional group that did not
    participate in the match — unlike `Match.group()`, which is the None-returning
    API most code reaches for first. Checked here for `== ""`, not `is None`;
    the latter is trivially always false since `findall` never produces it,
    which would have silently classified every entry — PORT included — as
    commented no matter what the manifest actually says.
    """
    return {name: (hashmark == "") for hashmark, name in _NAME_LINE.findall(region)}


def _table_a_rows() -> dict[str, str]:
    """variable -> the literal 'In the template manifest' cell, from Table A."""
    doc = DEPLOYMENT_DOC.read_text()
    start_marker = "**Table A"
    end_marker = "The `RELOAD` and `HEALTHCHECK_PATH` rows exist"
    assert start_marker in doc, f"{DEPLOYMENT_DOC.name} lost its {start_marker!r} heading"
    assert end_marker in doc, f"{DEPLOYMENT_DOC.name} lost the sentence marking Table A's end"
    table_text = doc[doc.index(start_marker) : doc.index(end_marker)]
    rows: dict[str, str] = {}
    for line in table_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        name_match = re.match(r"`([A-Z_][A-Z0-9_]*)`", cells[0])
        if not name_match:
            continue  # header row, or a row whose first cell isn't a `NAME`
        rows[name_match.group(1)] = cells[2]
    assert rows, "found Table A's heading but parsed no rows out of it"
    return rows


def _table_a_state(cell: str) -> str:
    """Normalize a Table A 'In the template manifest' cell to set/commented/absent."""
    if cell == "**set**":
        return "set"
    if cell == "commented":
        return "commented"
    if cell.startswith("**—"):
        return "absent"
    raise AssertionError(f"unrecognised Table A manifest-state cell: {cell!r}")


def test_manifest_matches_table_a_state():
    """Bidirectional: every Table A row's declared state (set / commented /
    deliberately absent) must match what the manifest's Table-A region actually
    does, and the Table-A region must contain nothing Table A does not know about.
    """
    block = _manifest_env_block()
    table_a_region, _backing, _secrets = _split_regions(block)
    manifest_names = _names_with_state(table_a_region)
    table_rows = _table_a_rows()

    mismatches = []
    for name, cell in table_rows.items():
        expected = _table_a_state(cell)
        if expected == "absent":
            if name in manifest_names:
                mismatches.append(f"{name}: Table A says {cell!r} (absent) but the manifest has an entry for it")
            continue
        if name not in manifest_names:
            mismatches.append(f"{name}: Table A says {cell!r} but the manifest has no entry at all")
            continue
        actual = "set" if manifest_names[name] else "commented"
        if actual != expected:
            mismatches.append(f"{name}: Table A says {cell!r} but the manifest entry is {actual}")

    extra = sorted(set(manifest_names) - set(table_rows))
    if extra:
        mismatches.append(f"manifest's Table-A region names {extra} that Table A does not document at all")

    assert not mismatches, (
        "docs/k8s_deployment.md's Table A and the manifest's env: block (Table-A "
        "region) disagree — atrium-service.deployment.yaml's own comment says this "
        "cannot happen:\n" + "\n".join(f"  {m}" for m in mismatches)
    )


def _table_b_rows() -> list[tuple[str, list[str]]]:
    """(repo-prose-name, [variable names]) for every Table B data row, with the
    Repo column's carry-forward (a blank first cell repeats the row above's repo)
    resolved. Rows whose variable cell has no backtick-quoted name (page-
    classification's "None" row) are dropped — nothing to check them against.
    """
    doc = DEPLOYMENT_DOC.read_text()
    start_marker = "**Table B"
    end_marker = "**The manifest ships no `Secret`"
    assert start_marker in doc, f"{DEPLOYMENT_DOC.name} lost its {start_marker!r} heading"
    assert end_marker in doc, f"{DEPLOYMENT_DOC.name} lost the sentence marking Table B's end"
    table_text = doc[doc.index(start_marker) : doc.index(end_marker)]

    current_repo = None
    rows: list[tuple[str, list[str]]] = []
    for line in table_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        repo_cell, var_cell = cells[0], cells[1]
        if repo_cell.startswith("Repo"):
            continue
        # A markdown header-separator row ("---------|---------") has a non-empty
        # first cell made ENTIRELY of "-"/":" — checked on the RAW cell, not after
        # `if repo_cell:` below, because an empty first cell (a genuine carry-
        # forward continuation row) trivially satisfies `set("") <= {"-", ":"}`
        # too, which silently ate every continuation row the first time this was
        # written and tested against nothing but the header.
        if repo_cell and set(repo_cell) <= {"-", ":"}:
            continue
        if repo_cell:
            current_repo = repo_cell
        names = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", var_cell)
        if names:
            assert current_repo, f"Table B row {cells!r} has no repo (carried forward or otherwise)"
            rows.append((current_repo, names))
    assert rows, "found Table B's heading but parsed no rows out of it"
    return rows


_TABLE_B_REPO_TO_DIR = {
    "alto-postprocess": "atrium-alto-postprocess",
    "llm-enrich": "atrium-llm-enrich",
    "nlp-enrich": "atrium-nlp-enrich",
    "page-classification": "atrium-page-classification",
    "translator": "atrium-translator",
}


def _sibling_env_example(repo_dir: str) -> Path | None:
    """The named repo's .env.example, if that sibling checkout is present.

    Mirrors scripts/revendor_shared.sh's own sibling convention: siblings live
    next to the hub by default, override with ATRIUM_SIBLING_ROOT.
    """
    root = Path(os.environ.get("ATRIUM_SIBLING_ROOT", REPO_ROOT.parent))
    path = root / repo_dir / ".env.example"
    return path if path.is_file() else None


_ENV_DECLARED = re.compile(r"^#?\s*([A-Z_][A-Z0-9_]*)=", re.MULTILINE)


def test_backing_and_secret_names_are_in_table_b_or_the_repos_ledger():
    """The manifest's backing-services and secrets regions (Table B's territory,
    not Table A's) must name only variables Table B — or, failing that, the
    owning repo's own .env.example — actually documents. Catches a name added to
    the manifest with nothing anywhere telling an operator what it is.
    """
    block = _manifest_env_block()
    _table_a_region, backing_region, secrets_region = _split_regions(block)
    manifest_names = set(_names_with_state(backing_region)) | set(_names_with_state(secrets_region))

    table_b_names: set[str] = set()
    for _repo, names in _table_b_rows():
        table_b_names.update(names)

    undocumented = sorted(manifest_names - table_b_names)
    assert not undocumented, (
        f"the manifest's backing-services/secrets region names {undocumented}, which "
        f"Table B does not document at all — an operator reading only the manifest "
        f"and k8s_deployment.md cannot find out what these are"
    )


def test_table_b_names_exist_in_their_own_repos_env_example():
    """Table B is a curated subset (atrium-project#60 says so explicitly — it need
    not list everything a repo's .env.example does), but every name it DOES list
    for a repo must be a name that repo's own .env.example actually declares.
    A name here that no .env.example has is a typo or a renamed variable Table B
    never caught up with.
    """
    missing: list[str] = []
    skipped_repos: list[str] = []
    for repo, names in _table_b_rows():
        repo_dir = _TABLE_B_REPO_TO_DIR.get(repo)
        assert repo_dir, f"Table B names an unrecognised repo {repo!r}"
        env_example = _sibling_env_example(repo_dir)
        if env_example is None:
            if repo_dir not in skipped_repos:
                skipped_repos.append(repo_dir)
            continue
        declared = set(_ENV_DECLARED.findall(env_example.read_text(encoding="utf-8")))
        for name in names:
            if name not in declared:
                missing.append(f"{repo}: `{name}` is in Table B but not in {repo_dir}/.env.example")

    if skipped_repos:
        pytest.skip(
            f"sibling checkout(s) not present, cannot verify Table B against their "
            f".env.example: {sorted(skipped_repos)}"
        )
    assert not missing, "\n".join(missing)
