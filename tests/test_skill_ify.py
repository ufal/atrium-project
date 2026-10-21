"""Tests for tools/skill_ify.py's `apply`: the materialized tree holds what `derive` decided (#77 C)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools"))

import skill_ify  # noqa: E402


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _commit(repo: Path, files: dict, message: str) -> None:
    for path, text in files.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path):
    """A repository whose `test` branch is the tool and whose `agent-skill` branch adds the skill."""
    root = tmp_path / "tool"
    root.mkdir()
    _git(root, "init", "-q", "-b", "test")
    (root / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (root / "run.sh").chmod(0o755)
    _commit(root, {"README.md": "test readme\n", "service/api.py": "app = None\n", "tests/test_x.py": "\n"}, "tool")
    _git(root, "checkout", "-q", "-b", "agent-skill")
    _commit(
        root,
        {"README.md": "skill readme\n", "SKILL.md": "---\nname: tool\n---\n", "extra.txt": "skill only\n"},
        "skill",
    )
    return root


def test_apply_writes_skill_only_files_and_the_overlay(repo, tmp_path):
    into = tmp_path / "out"
    assert skill_ify.cmd_apply(repo, "test", "agent-skill", into) == 0
    assert (into / "extra.txt").read_text(encoding="utf-8") == "skill only\n"
    assert (into / "README.md").read_text(encoding="utf-8") == "skill readme\n"
    assert (into / "SKILL.md").is_file() and (into / "service" / "api.py").is_file()
    assert not (into / "tests").exists()


def test_apply_keeps_the_executable_bit(repo, tmp_path):
    into = tmp_path / "out"
    assert skill_ify.cmd_apply(repo, "test", "agent-skill", into) == 0
    assert (into / "run.sh").stat().st_mode & 0o111
    assert not (into / "service" / "api.py").stat().st_mode & 0o111
