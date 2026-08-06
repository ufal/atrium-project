"""Tests for tools/ci/workflow_lint.py — the linter that gates every caller in the
ecosystem and, until now, had none.

Why this file exists (issue #18 / #10, W5): `workflow_lint.py` is ~400 lines gating
38 caller jobs across six repos, and it shipped a crash. `permissions: read-all` is a
legal GitHub shorthand; the merge `{**doc_perms, **job_perms}` assumed both were
mappings and raised `TypeError: 'str' object is not a mapping`, so the linter died
instead of reporting — taking every later check down with it. A linter that fails
open is worse than no linter, because the green tick is read as "checked".

Two properties every test here is built around:

  1. Each rule FAILS a purpose-built broken fixture. A rule that never fires on
     anything is indistinguishable from a rule that is not wired up — the exact
     failure mode `test_check_version.py` was written to avoid.
  2. Breaking ONE rule does not mask the others. `main()` accumulates findings
     rather than returning at the first error, and `test_one_break_does_not_mask_others`
     pins that, because the ordering of checks is an implementation detail nobody
     should have to know to trust the output.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools" / "ci"))

import workflow_lint as wl  # noqa: E402

# ── helpers ──────────────────────────────────────────────────────────────────

def write_workflow(root: Path, name: str, body: str) -> Path:
    d = root / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def write_template(root: Path, name: str, body: str) -> Path:
    d = root / "docs" / "templates" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def run_lint(root: Path) -> tuple[int, str]:
    """Run the linter against `root`, resolving callees from the real hub."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = wl.main(["--repo-root", str(root), "--hub-root", str(_HUB_ROOT), "--offline"])
    return rc, buf.getvalue()


#: A caller with nothing wrong with it — the baseline every test perturbs.
CLEAN_CALLER = """\
name: Clean
on: push
concurrency:
  group: clean-${{ github.ref }}
permissions:
  contents: read
jobs:
  drift:
    uses: ufal/atrium-project/.github/workflows/para-drift.reusable.yml@v1
"""


def test_clean_caller_passes(tmp_path):
    """The baseline must pass, or every negative test below proves nothing."""
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── the crash that motivated this file ───────────────────────────────────────

@pytest.mark.parametrize("shorthand", ["read-all", "write-all"])
def test_permissions_shorthand_does_not_crash(tmp_path, shorthand):
    """`permissions: <string>` is legal YAML for GitHub and must not raise.

    Regression test for `TypeError: 'str' object is not a mapping`.
    """
    write_workflow(tmp_path, "x.yml", CLEAN_CALLER.replace("permissions:\n  contents: read", f"permissions: {shorthand}"))
    rc, out = run_lint(tmp_path)  # must not raise
    assert rc == 0, out


def test_read_all_does_not_satisfy_a_write_scope(tmp_path):
    """`read-all` grants read everywhere and write nowhere.

    Silently treating it as sufficient for `packages: write` would reintroduce the
    startup_failure class the permission check exists to prevent.
    """
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
concurrency:
  group: x
permissions: read-all
jobs:
  build:
    uses: ufal/atrium-project/.github/workflows/docker-tool.reusable.yml@v1
    with:
      image-name: ufal/example
""")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "packages" in out


def test_write_all_satisfies_every_scope(tmp_path):
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
concurrency:
  group: x
permissions: write-all
jobs:
  build:
    uses: ufal/atrium-project/.github/workflows/docker-tool.reusable.yml@v1
    with:
      image-name: ufal/example
""")
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── W5's new rules, one broken fixture each ──────────────────────────────────

def test_caller_example_without_uses_is_rejected(tmp_path):
    """W1's clobber signature: a `*.caller.example.yml` that calls nothing.

    `docker.caller.example.yml` was overwritten by a dependabot config and no check
    noticed, because `check_duplicate_names` skips files with no `name:` key.
    """
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    write_template(tmp_path, "thing.caller.example.yml", "version: 2\nupdates: []\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "no `uses:`" in out


def test_caller_example_with_uses_is_accepted(tmp_path):
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    write_template(tmp_path, "thing.caller.example.yml", CLEAN_CALLER)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


@pytest.mark.parametrize("ref", ["test", "main", "v2-beta"])
def test_non_v1_hub_ref_is_rejected(tmp_path, ref):
    """A branch pin makes hub changes reach a repo without anyone adopting them."""
    write_workflow(tmp_path, "x.yml", CLEAN_CALLER.replace("@v1", f"@{ref}"))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert f"@{ref}" in out


def test_missing_timeout_minutes_is_rejected(tmp_path):
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
concurrency:
  group: x
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "timeout-minutes" in out


def test_missing_concurrency_is_rejected(tmp_path):
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "concurrency" in out


def test_reusable_workflow_is_exempt_from_concurrency(tmp_path):
    """A callee must NOT set a concurrency group: the caller owns it, and one here
    would collapse five repos' builds into a single queue."""
    write_workflow(tmp_path, "r.reusable.yml", """\
name: R
on:
  workflow_call:
permissions:
  contents: read
jobs:
  work:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""")
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_missing_permissions_is_rejected(tmp_path):
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
concurrency:
  group: x
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "permissions" in out


def test_missing_required_input_is_rejected(tmp_path):
    """`skill-validate.reusable.yml` declares `client-script: required: true`."""
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
concurrency:
  group: x
permissions:
  contents: read
jobs:
  skill:
    uses: ufal/atrium-project/.github/workflows/skill-validate.reusable.yml@v1
""")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "client-script" in out


# ── the property that makes the output trustworthy ───────────────────────────

def test_one_break_does_not_mask_others(tmp_path):
    """Findings accumulate: three independent defects are all reported at once.

    If the linter returned at the first error, a maintainer would fix one defect,
    re-run, find another, and learn to distrust a clean run after a fix.
    """
    write_workflow(tmp_path, "x.yml", """\
name: X
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""")
    write_template(tmp_path, "bad.caller.example.yml", "version: 2\nupdates: []\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "timeout-minutes" in out
    assert "concurrency" in out
    assert "permissions" in out
    assert "no `uses:`" in out


def test_hub_itself_passes_its_own_linter():
    """The hub must satisfy the rules it publishes. This is the check that would
    have caught the `docker.caller.example.yml` clobber on the commit that made it."""
    rc, out = run_lint(_HUB_ROOT)
    assert rc == 0, out
