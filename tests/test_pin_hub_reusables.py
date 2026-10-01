"""Tests for scripts/pin_hub_reusables.py — the sweep that pins every hub reusable to a commit.

The sweep's output must pass tools/ci/workflow_lint.py, including `--require-sha-pins`, and keep
every comment of the callers it rewrites. Synthetic callers cover the shapes the tool repos use
(a bare `uses:`, a job with a `with:` block before or after `secrets:`, a reusable that takes
`hub-ref` and one that does not); where the tool repos sit beside the hub, their real callers
are swept too, as copies.
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "scripts"))
sys.path.insert(0, str(_HUB_ROOT / "tools" / "ci"))

import pin_hub_reusables as pin  # noqa: E402
import workflow_lint as wl  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"

CALLERS = {
    "para-drift.yml": """\
name: Paradata Canonical Drift
on: push
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
permissions:
  contents: read   # least privilege
jobs:
  check-drift:
    uses: ufal/atrium-project/.github/workflows/para-drift.reusable.yml@v1
""",
    "workflow-lint.yml": """\
name: Workflow Lint
on: push
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
permissions:
  contents: read
jobs:
  workflow-lint:
    uses: ufal/atrium-project/.github/workflows/workflow-lint.reusable.yml@v1
    with:
      # keep this comment
      offline: true
""",
    "security.yml": """\
name: Security
on: push
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
permissions:
  contents: read
  security-events: write
jobs:
  scan:
    permissions:
      contents: read
      packages: read
      security-events: write
    uses: ufal/atrium-project/.github/workflows/security.reusable.yml@v1
    # No `secrets:` block (#18).
    with:
      image-ref: ghcr.io/ufal/atrium-example:latest
""",
}


def _repo(tmp_path: Path, name: str = "atrium-example", callers: dict | None = None) -> Path:
    workflows = tmp_path / name / ".github" / "workflows"
    workflows.mkdir(parents=True)
    for file, text in (callers or CALLERS).items():
        (workflows / file).write_text(text, encoding="utf-8")
    return tmp_path / name


def _run(*args: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = pin.main(list(args))
    return rc, buf.getvalue()


def _lint(repo: Path, *extra: str) -> tuple[int, str]:
    buf = io.StringIO()
    args = ["--repo-root", str(repo), "--hub-root", str(_HUB_ROOT), "--offline", "--repo-name", f"ufal/{repo.name}"]
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = wl.main(args + list(extra))
    return rc, buf.getvalue()


def test_every_caller_is_pinned_with_its_channel_and_hub_ref(tmp_path):
    repo = _repo(tmp_path)
    rc, out = _run("--sha", SHA, "--root", str(tmp_path), "--repo", repo.name)
    assert rc == 0 and "3 hub-reusable callers" in out
    for path in (repo / ".github" / "workflows").iterdir():
        text = path.read_text(encoding="utf-8")
        assert f"@{SHA}  # v1" in text and "@v1\n" not in text
        job = next(iter(yaml.safe_load(text)["jobs"].values()))
        takes = pin.takes_hub_ref(job["uses"].split("ufal/atrium-project/")[1].split("@")[0], _HUB_ROOT)
        assert (job.get("with") or {}).get("hub-ref") == (SHA if takes else None), path.name
    assert "# keep this comment" in (repo / ".github" / "workflows" / "workflow-lint.yml").read_text()
    assert "# No `secrets:` block (#18)." in (repo / ".github" / "workflows" / "security.yml").read_text()


def test_the_swept_callers_pass_the_linter_even_when_it_requires_pins(tmp_path):
    repo = _repo(tmp_path)
    assert _lint(repo, "--require-sha-pins")[0] == 1, "unpinned callers must fail the strict lint"
    _run("--sha", SHA, "--root", str(tmp_path), "--repo", repo.name)
    rc, out = _lint(repo, "--require-sha-pins")
    assert rc == 0, out


def test_a_second_sweep_changes_nothing_and_a_new_commit_moves_every_pin(tmp_path):
    repo = _repo(tmp_path)
    _run("--sha", SHA, "--root", str(tmp_path), "--repo", repo.name)
    before = {p.name: p.read_text() for p in (repo / ".github" / "workflows").iterdir()}
    assert _run("--sha", SHA, "--root", str(tmp_path), "--repo", repo.name, "--check")[0] == 0
    other = "f" * 40
    assert _run("--sha", other, "--root", str(tmp_path), "--repo", repo.name, "--check")[0] == 1
    assert {p.name: p.read_text() for p in (repo / ".github" / "workflows").iterdir()} == before, "--check wrote"
    _run("--sha", other, "--root", str(tmp_path), "--repo", repo.name)
    texts = [p.read_text() for p in (repo / ".github" / "workflows").iterdir()]
    assert all(SHA not in text and other in text for text in texts)
    assert sum(text.count("hub-ref:") for text in texts) == 2, "hub-ref updated in place, never added twice"


def test_a_short_sha_is_a_usage_error(tmp_path):
    assert _run("--sha", "0123abc", "--root", str(tmp_path))[0] == 2


def test_an_annotated_tag_object_is_refused_and_its_commit_accepted(tmp_path):
    """`git rev-parse v1` names the tag object when `v1` is annotated; `uses:` needs the commit."""
    hub = tmp_path / "hub"
    hub.mkdir()
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(hub), *args], check=True, capture_output=True, text=True, env={**os.environ, **env}
        ).stdout.strip()

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "hub")
    git("tag", "-a", "v1", "-m", "channel")
    tag_object, commit = git("rev-parse", "v1"), git("rev-parse", "v1^{commit}")
    assert tag_object != commit
    repo = _repo(tmp_path / "tools")
    args = ("--root", str(repo.parent), "--repo", repo.name, "--hub-root", str(hub), "--check")
    rc, out = _run("--sha", tag_object, *args)
    assert rc == 2 and "tag object" in out and commit[:12] in out
    rc, out = _run("--sha", commit, *args)
    assert rc == 1 and "3 hub-reusable callers" in out and "not a commit" not in out, out  # accepted, then checked


@pytest.mark.parametrize("tool", pin.REPOS)
def test_the_real_callers_of_a_sibling_tool_repo(tmp_path, tool):
    """Where the tool repos sit beside the hub, sweep a COPY of their callers and lint it strictly."""
    source = _HUB_ROOT.parent / tool / ".github" / "workflows"
    if not source.is_dir():
        pytest.skip(f"no {tool} checkout beside the hub")
    target = tmp_path / tool / ".github"
    shutil.copytree(source, target / "workflows")
    for extra in ("dependabot.yml",):
        if (source.parent / extra).is_file():
            shutil.copy(source.parent / extra, target / extra)
    rc, out = _run("--sha", SHA, "--root", str(tmp_path), "--repo", tool)
    assert rc == 0 and "7 hub-reusable callers" in out, out
    rc, out = _lint(tmp_path / tool, "--require-sha-pins")
    assert rc == 0, out
