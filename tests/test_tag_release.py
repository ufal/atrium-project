"""Tests for scripts/tag_release.py — a release tag lands on the pushed commit whose versions it names (#66).

Each case builds a throwaway tool repository with a bare `origin`, the hub's canonical
check_version.py and a CITATION.cff / para_config.txt pair, then runs the script against it.
The refusals are the failure modes of 4–5 November: a tag before its version bump (translator
v1.7.6-beta), a commit not yet pushed, a stray dot (keyword-extract v1.6.3.-beta), a tag that
already exists. The success case checks that exactly one ref, the tag, reaches the remote.

Run: pytest tests/test_tag_release.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "scripts"))

import tag_release as tr  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.org",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.org",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _git(cwd: Path, *args: str) -> str:
    env = {**os.environ, **_ENV}
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout.strip()


def _versions(repo: Path, version: str) -> None:
    (repo / "CITATION.cff").write_text(f'cff-version: 1.2.0\nversion: "{version}"\n', encoding="utf-8")
    (repo / "para_config.txt").write_text(f"[tool]\nprogram = demo\nversion = v{version}\n", encoding="utf-8")


@pytest.fixture
def tool(tmp_path, monkeypatch):
    for key, value in _ENV.items():
        monkeypatch.setenv(key, value)
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "-q", "-b", "test", str(origin))
    repo = tmp_path / "tool"
    _git(tmp_path, "clone", "-q", str(origin), str(repo))
    _git(repo, "checkout", "-q", "-b", "test")
    shutil.copy(_HUB_ROOT / "docs" / "templates" / "shared" / "check_version.py", repo / "check_version.py")
    _versions(repo, "1.0.0-beta")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "v1.0.0-beta")
    _git(repo, "push", "-q", "origin", "test")
    return repo, origin


def _run(repo: Path, tag: str, *extra: str) -> int:
    return tr.main([tag, "--repo", str(repo), "--gh", "", "--wait", "0", *extra])


def _remote_refs(origin: Path) -> list[str]:
    return sorted(line.split()[1] for line in _git(origin, "show-ref").splitlines())


def test_a_clean_pushed_bumped_commit_is_tagged_and_only_the_tag_is_pushed(tool, capsys):
    repo, origin = tool
    before = _remote_refs(origin)
    assert _run(repo, "v1.0.0-beta") == 0
    after = _remote_refs(origin)
    assert sorted(set(after) - set(before)) == ["refs/tags/v1.0.0-beta"]
    assert _git(origin, "rev-parse", "v1.0.0-beta^{commit}") == _git(repo, "rev-parse", "HEAD")
    assert _git(origin, "cat-file", "-t", "v1.0.0-beta") == "tag"  # annotated
    assert "gh workflow run release.yml --ref v1.0.0-beta" in capsys.readouterr().out


def test_a_tag_before_its_version_bump_is_refused(tool, capsys):
    """The v1.7.6-beta case: the release commit still declares the previous version."""
    repo, origin = tool
    assert _run(repo, "v1.0.1-beta") == 1
    assert "release gate would fail" in capsys.readouterr().err
    assert "refs/tags/v1.0.1-beta" not in _remote_refs(origin)


def test_a_bump_committed_but_not_pushed_is_refused(tool, capsys):
    repo, origin = tool
    _versions(repo, "1.0.1-beta")
    _git(repo, "commit", "-q", "-am", "v1.0.1-beta")
    assert _run(repo, "v1.0.1-beta") == 1
    assert "1 ahead" in capsys.readouterr().err
    assert "refs/tags/v1.0.1-beta" not in _remote_refs(origin)
    _git(repo, "push", "-q", "origin", "test")
    assert _run(repo, "v1.0.1-beta") == 0


def test_uncommitted_changes_are_refused(tool, capsys):
    repo, _ = tool
    _versions(repo, "1.0.1-beta")
    assert _run(repo, "v1.0.1-beta") == 1
    assert "uncommitted changes" in capsys.readouterr().err


@pytest.mark.parametrize("bad", ["v1.6.3.-beta", "1.0.0-beta", "v1.0", "v1.0.0-"])
def test_a_malformed_tag_is_refused(tool, bad, capsys):
    repo, _ = tool
    assert _run(repo, bad) == 1
    assert "is not a release tag" in capsys.readouterr().err


def test_an_existing_tag_is_refused(tool, capsys):
    repo, _ = tool
    assert _run(repo, "v1.0.0-beta") == 0
    _git(repo, "tag", "-d", "v1.0.0-beta")
    assert _run(repo, "v1.0.0-beta") == 1
    assert "already exists" in capsys.readouterr().err


def test_a_dry_run_tags_nothing(tool, capsys):
    repo, origin = tool
    before = _remote_refs(origin)
    assert _run(repo, "v1.0.0-beta", "--dry-run") == 0
    assert _remote_refs(origin) == before
    assert not _git(repo, "tag", "--list")
    assert "would tag" in capsys.readouterr().out


def test_the_para_config_under_setup_is_found(tool):
    """ocr-postprocess and page-classification keep it in setup/."""
    repo, _ = tool
    (repo / "setup").mkdir()
    _git(repo, "mv", "para_config.txt", "setup/para_config.txt")
    _git(repo, "commit", "-q", "-m", "move")
    _git(repo, "push", "-q", "origin", "test")
    assert _run(repo, "v1.0.0-beta") == 0


@pytest.mark.parametrize(
    "url, slug",
    [
        ("https://github.com/ufal/atrium-translator.git", "ufal/atrium-translator"),
        ("git@github.com:ufal/atrium-translator.git", "ufal/atrium-translator"),
        ("https://github.com/ufal/atrium-project", "ufal/atrium-project"),
        ("/tmp/origin.git", None),
    ],
)
def test_the_repository_slug_comes_from_the_remote(url, slug):
    assert tr.repo_slug(url) == slug


# ── The commit's own CI (`check_ci`): v1.7.7-beta was tagged on a commit whose Docker Build had failed ──


def _fake_gh(tmp_path: Path, monkeypatch, runs: list[dict]) -> str:
    """A `gh` stand-in: `run list --commit` prints `runs`; every other call prints an empty list."""
    import json

    monkeypatch.setenv("FAKE_GH_RUNS", json.dumps(runs))
    script = tmp_path / "gh"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "print(os.environ['FAKE_GH_RUNS'] if '--commit' in sys.argv else '[]')\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def _push_run(name: str, conclusion: str | None, status: str = "completed") -> dict:
    return {"name": name, "status": status, "conclusion": conclusion, "event": "push", "url": f"https://x/{name}"}


def test_a_commit_with_a_failed_push_run_is_refused(tool, tmp_path, monkeypatch, capsys):
    repo, origin = tool
    gh = _fake_gh(
        tmp_path, monkeypatch, [_push_run("pre-commit", "success"), _push_run("Docker Build & Push", "failure")]
    )
    monkeypatch.setattr(tr, "repo_slug", lambda url: "ufal/demo")
    assert tr.main(["v1.0.0-beta", "--repo", str(repo), "--gh", gh, "--wait", "0"]) == 1
    err = capsys.readouterr().err
    assert "did not pass" in err and "Docker Build & Push: failure" in err
    assert "refs/tags/v1.0.0-beta" not in _remote_refs(origin)


def test_a_commit_with_a_running_push_run_is_refused(tool, tmp_path, monkeypatch, capsys):
    repo, _ = tool
    gh = _fake_gh(tmp_path, monkeypatch, [_push_run("Docker Build & Push", None, status="in_progress")])
    monkeypatch.setattr(tr, "repo_slug", lambda url: "ufal/demo")
    assert tr.main(["v1.0.0-beta", "--repo", str(repo), "--gh", gh, "--wait", "0"]) == 1
    assert "still has push runs going" in capsys.readouterr().err


def test_a_commit_whose_push_runs_passed_is_tagged(tool, tmp_path, monkeypatch, capsys):
    repo, origin = tool
    runs = [
        _push_run("pre-commit", "success"),
        _push_run("Docker Build & Push", "success"),
        _push_run("Lint", "skipped"),
    ]
    gh = _fake_gh(tmp_path, monkeypatch, runs)
    monkeypatch.setattr(tr, "repo_slug", lambda url: "ufal/demo")
    assert tr.main(["v1.0.0-beta", "--repo", str(repo), "--gh", gh, "--wait", "0"]) == 0
    assert "CI green: 3 push run(s)" in capsys.readouterr().out
    assert "refs/tags/v1.0.0-beta" in _remote_refs(origin)


def test_no_ci_check_tags_despite_a_red_run(tool, tmp_path, monkeypatch, capsys):
    repo, origin = tool
    gh = _fake_gh(tmp_path, monkeypatch, [_push_run("Docker Build & Push", "failure")])
    monkeypatch.setattr(tr, "repo_slug", lambda url: "ufal/demo")
    assert tr.main(["v1.0.0-beta", "--repo", str(repo), "--gh", gh, "--wait", "0", "--no-ci-check"]) == 0
    assert "CI not checked (--no-ci-check)" in capsys.readouterr().out
    assert "refs/tags/v1.0.0-beta" in _remote_refs(origin)


def test_without_gh_the_ci_check_is_reported_as_not_done(tool, capsys):
    repo, _ = tool
    assert _run(repo, "v1.0.0-beta", "--dry-run") == 0
    assert "CI not checked" in capsys.readouterr().out


def test_a_tag_that_exists_only_locally_is_explained(tool, capsys):
    """A version tagged locally and never pushed is unused: delete the tag, not the version."""
    repo, origin = tool
    _git(repo, "tag", "v1.0.0-beta")
    assert _run(repo, "v1.0.0-beta") == 1
    err = capsys.readouterr().err
    assert "exists only locally" in err and "git tag -d v1.0.0-beta" in err
    _git(repo, "tag", "-d", "v1.0.0-beta")
    assert _run(repo, "v1.0.0-beta") == 0
