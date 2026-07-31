"""Tests for the canonical check_version.py (issue #18).

WHY THIS EXISTS. `check_version.py` is the release gate for all five ATRIUM tool
repos: their `release.yml` runs it with `--require-tag` before anything is
published, and `para-drift.reusable.yml` holds all six copies byte-identical to
`docs/templates/shared/check_version.py` (verified: md5 d36004d0 across the
board). So this one file decides whether a mistagged release ships.

It had no tests anywhere in the ecosystem. Its only validation was ad-hoc
command-line runs during the #18 audit -- which proved it worked that day and
preserved nothing. These tests make the negative cases permanent, and they are
the cases that matter: the gate exists to BLOCK, so a test suite that only
checks the happy path would tell us nothing about whether it still does.

Two real defects motivate specific cases below: `v1.0.0.-beta` and `v1.16.2`
both shipped before this gate existed.

Tests target the canonical source under docs/templates/shared/ -- not a vendored
copy -- because that is what para-drift propagates everywhere else.

Run: pytest tests/test_check_version.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SOURCE = Path(__file__).resolve().parents[1] / "docs" / "templates" / "shared" / "check_version.py"


def _load():
    """Import the canonical script by path (it is not an installed module)."""
    spec = importlib.util.spec_from_file_location("check_version", _SOURCE)
    assert spec and spec.loader, f"cannot load {_SOURCE}"
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_version"] = module
    spec.loader.exec_module(module)
    return module


cv = _load()


@pytest.fixture
def repo(tmp_path):
    """A minimal repo layout, version-consistent at 1.7.1-beta.

    Mirrors the real split convention: CITATION.cff carries the bare form,
    para_config.txt the `v`-prefixed one. Individual tests override either.
    """

    def _make(citation="1.7.1-beta", para="v1.7.1-beta"):
        cff = tmp_path / "CITATION.cff"
        cff.write_text(
            "cff-version: 1.2.0\n"
            'title: "ATRIUM test fixture"\n'
            f'version: "{citation}"\n'
            'date-released: "2026-07-31"\n',
            encoding="utf-8",
        )
        cfg = tmp_path / "para_config.txt"
        cfg.write_text(
            f"[tool]\nprogram = fixture\nversion = {para}\n", encoding="utf-8"
        )
        return str(cff), str(cfg)

    return _make


def run(citation, para, tag="", require_tag=False):
    """Exit code from main(), the same surface release.yml invokes."""
    argv = ["--citation", citation, "--para-config", para, "--tag", tag]
    if require_tag:
        argv.append("--require-tag")
    return cv.main(argv)


# --- the gate must PASS when everything agrees -------------------------------

def test_matching_tag_passes(repo):
    cff, cfg = repo()
    assert run(cff, cfg, tag="v1.7.1-beta", require_tag=True) == 0


def test_v_prefix_is_optional_on_both_sides(repo):
    """`v1.2.3` and `1.2.3` must compare equal, or the split convention breaks."""
    cff, cfg = repo(citation="1.7.1-beta", para="1.7.1-beta")
    assert run(cff, cfg, tag="1.7.1-beta", require_tag=True) == 0
    assert run(cff, cfg, tag="v1.7.1-beta", require_tag=True) == 0


def test_tag_optional_without_require_flag(repo):
    """Pushes and PRs have no tag; only CITATION/para_config agreement applies."""
    cff, cfg = repo()
    assert run(cff, cfg, tag="") == 0


# --- the gate must BLOCK: these are the reason it exists ---------------------

def test_stale_tag_blocks(repo):
    """Tagging v1.7.0-beta when the tree says 1.7.1-beta must not publish."""
    cff, cfg = repo()
    assert run(cff, cfg, tag="v1.7.0-beta", require_tag=True) == 1


def test_empty_tag_with_require_tag_blocks(repo):
    """The release gate itself: --require-tag and no tag is a hard failure."""
    cff, cfg = repo()
    assert run(cff, cfg, tag="", require_tag=True) == 1


def test_malformed_tag_blocks(repo):
    """`v1.7.1.-beta` -- the shape of the real `v1.0.0.-beta` that shipped."""
    cff, cfg = repo()
    assert run(cff, cfg, tag="v1.7.1.-beta", require_tag=True) == 1


def test_citation_para_mismatch_blocks_and_names_both(repo, capsys):
    """A mismatch must be actionable: the message names both files and values."""
    cff, cfg = repo(citation="1.7.1-beta", para="v1.7.0-beta")
    assert run(cff, cfg, tag="v1.7.1-beta", require_tag=True) == 1
    out = capsys.readouterr().out
    assert "1.7.1-beta" in out and "1.7.0-beta" in out
    assert "mismatch" in out.lower()


def test_mismatch_blocks_even_without_a_tag(repo):
    """Two files disagreeing is a defect on any event, tag or not."""
    cff, cfg = repo(citation="1.7.1-beta", para="v1.6.0-beta")
    assert run(cff, cfg, tag="") == 1


# --- malformed and missing inputs must fail closed, never crash --------------

def test_missing_citation_file_blocks(tmp_path, repo):
    _, cfg = repo()
    assert run(str(tmp_path / "nope.cff"), cfg, tag="v1.7.1-beta", require_tag=True) == 1


def test_citation_without_version_blocks(tmp_path, repo):
    _, cfg = repo()
    cff = tmp_path / "noversion.cff"
    cff.write_text('cff-version: 1.2.0\ntitle: "no version here"\n', encoding="utf-8")
    assert run(str(cff), cfg, tag="v1.7.1-beta", require_tag=True) == 1


def test_para_config_without_tool_section_blocks(tmp_path, repo):
    cff, _ = repo()
    cfg = tmp_path / "empty.txt"
    cfg.write_text("[other]\nkey = value\n", encoding="utf-8")
    assert run(cff, str(cfg), tag="v1.7.1-beta", require_tag=True) == 1


# --- parsing details that have bitten before ---------------------------------

def test_nested_cff_version_is_ignored(tmp_path, repo):
    """CFF nests `version:` under references/preferred-citation for CITED works.

    Those belong to someone else's software. Only the column-0 `version:` is
    this tool's, so an indented one must not be picked up -- otherwise a cited
    dependency's version could satisfy the release gate.
    """
    _, cfg = repo()
    cff = tmp_path / "nested.cff"
    cff.write_text(
        "cff-version: 1.2.0\n"
        'title: "fixture"\n'
        'version: "1.7.1-beta"\n'
        "references:\n"
        "  - type: software\n"
        '    title: "some dependency"\n'
        '    version: "9.9.9"\n',
        encoding="utf-8",
    )
    assert run(str(cff), cfg, tag="v1.7.1-beta", require_tag=True) == 0


def test_whitespace_around_tag_is_tolerated(repo):
    """github.ref_name can arrive padded; that must not fail a good release."""
    cff, cfg = repo()
    assert run(cff, cfg, tag="  v1.7.1-beta  ", require_tag=True) == 0


def test_collect_errors_reports_every_disagreement_at_once(repo):
    """One run should surface all problems, not just the first.

    Re-tagging to discover the next error one at a time is how `v1.16.2`
    happened.
    """
    cff, cfg = repo(citation="1.7.1-beta", para="v1.6.0-beta")
    errors = cv.collect_errors(cff, cfg, "v1.5.0-beta", True)
    assert len(errors) >= 2, errors


# --- each of the three comparisons must be independently load-bearing --------
#
# The tag is compared against BOTH files. When CITATION.cff and para_config.txt
# agree (the normal case) those two comparisons are redundant: either one alone
# still blocks a bad tag. That redundancy hides a broken check -- deleting the
# tag-vs-CITATION comparison passed every test above, because tag-vs-para_config
# caught the same cases.
#
# So these two tests deliberately make the files DISAGREE, which is the only
# situation where each comparison is observable on its own, and assert on the
# specific error rather than just the exit code.

def test_tag_vs_citation_comparison_is_load_bearing(repo):
    """Tag agrees with para_config but not CITATION.cff -> its own error."""
    cff, cfg = repo(citation="1.7.1-beta", para="v1.6.0-beta")
    errors = cv.collect_errors(cff, cfg, "v1.6.0-beta", True)
    assert any("tag v1.6.0-beta" in e and "1.7.1-beta" in e for e in errors), errors


def test_tag_vs_para_config_comparison_is_load_bearing(repo):
    """Tag agrees with CITATION.cff but not para_config.txt -> its own error."""
    cff, cfg = repo(citation="1.7.1-beta", para="v1.6.0-beta")
    errors = cv.collect_errors(cff, cfg, "v1.7.1-beta", True)
    assert any("tag v1.7.1-beta" in e and "1.6.0-beta" in e for e in errors), errors
