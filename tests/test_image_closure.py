"""Tests for tools/ci/image_closure.py — the production image's first-party closure (#72 A.3).

Each rule fails a purpose-built repository, the way tests/test_workflow_lint.py holds the linter:
a check that never fires is indistinguishable from one that is not wired up. The repositories are
small temporary git checkouts; the shared components come from this hub's real MANIFEST.json, so
a vendored `atrium_limits.py` counts as approved exactly as it does in the five tool repositories.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools" / "ci"))

import image_closure as ic  # noqa: E402

API = """\
import tool_limits
from atrium_limits import LimitSet
from stage_core import run
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        check=True,
        capture_output=True,
    )


def make_repo(tmp_path: Path, files: dict, declaration: dict | None, commit: bool = True) -> Path:
    repo = tmp_path / "tool"
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding="utf-8")
    if declaration is not None:
        (repo / ".github").mkdir(parents=True, exist_ok=True)
        (repo / ".github" / "production-image.json").write_text(json.dumps(declaration), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    if commit:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "fixture")
    return repo


def base_files(**extra: str) -> dict:
    files = {
        "service/api.py": API,
        "tool_limits.py": "from atrium_limits import limit\n",
        "stage_core.py": "def run():\n    return 1\n",
        "atrium_limits.py": "def limit():\n    pass\n",
        "research.py": "import numpy\n",
    }
    files.update(extra)
    return files


def declaration(**overrides) -> dict:
    data = {
        "target": "api",
        "entrypoint": "service/api.py",
        "core": ["service/api.py", "tool_limits.py", "stage_core.py"],
    }
    data.update(overrides)
    return data


def check(repo: Path, **kwargs) -> ic.Findings:
    return ic.check(repo, _HUB_ROOT, **kwargs)


def test_a_declared_image_passes_and_counts_shared_components(tmp_path):
    findings = check(make_repo(tmp_path, base_files(), declaration()))
    assert findings.errors == []
    assert any("3 core, 1 shared, 0 vendored, 0 moving" in note for note in findings.notes)


def test_an_undeclared_module_reached_from_the_entrypoint_fails(tmp_path):
    files = base_files(**{"service/api.py": API + "import research\n"})
    findings = check(make_repo(tmp_path, files, declaration()))
    assert any("`research.py` is reached" in error for error in findings.errors)


def test_a_declared_module_the_entrypoint_no_longer_reaches_fails(tmp_path):
    findings = check(make_repo(tmp_path, base_files(), declaration(core=[*declaration()["core"], "research.py"])))
    assert any("`research.py` is declared in `core`" in error for error in findings.errors)


def test_a_referenced_first_party_file_that_is_missing_fails(tmp_path):
    files = base_files(**{"service/api.py": API + "from api_util import gone\n", "api_util/present.py": ""})
    findings = check(make_repo(tmp_path, files, declaration()))
    assert any("`api_util/gone.py` is referenced" in error for error in findings.errors)


def test_a_vendored_copy_must_be_pinned_by_a_parity_test(tmp_path):
    files = base_files(**{"service/api.py": API + "import teitok_read\n", "teitok_read.py": ""})
    decl = declaration(vendored={"teitok_read.py": "atrium-nlp-enrich"})
    findings = check(make_repo(tmp_path, files, decl))
    assert any("no tests/test_vendored_*.py pins it" in error for error in findings.errors)

    files["tests/test_vendored_teitok_parity.py"] = 'VENDORED = {"teitok_read.py": "0" * 64}\n'
    assert check(make_repo(tmp_path / "pinned", files, decl)).errors == []


def test_a_moving_module_is_allowed_and_reported(tmp_path):
    files = base_files(**{"service/api.py": API + "import research\n"})
    findings = check(make_repo(tmp_path, files, declaration(moving={"research.py": "ufal/atrium-nlp-enrich#40"})))
    assert findings.errors == []
    assert any("until ufal/atrium-nlp-enrich#40 moves it out" in note for note in findings.notes)


def test_a_repository_without_a_declaration_passes_with_a_notice(tmp_path):
    findings = check(make_repo(tmp_path, base_files(), None))
    assert findings.errors == [] and any("no .github/production-image.json" in note for note in findings.notes)


@pytest.mark.parametrize(
    "decl, message",
    [
        ({**declaration(), "cores": []}, "unknown key(s) ['cores']"),
        ({"target": "api", "core": []}, "lacks ['entrypoint']"),
        (declaration(core=[*declaration()["core"], "atrium_limits.py"]), "hub-canonical shared component"),
        (declaration(moving={"stage_core.py": "#40"}), "listed in both `core` and `moving`"),
        (declaration(entrypoint="service/absent.py"), "the entrypoint `service/absent.py` is not in the tree"),
    ],
)
def test_a_malformed_declaration_fails(tmp_path, decl, message):
    findings = check(make_repo(tmp_path, base_files(), decl))
    assert any(message in error for error in findings.errors), findings.errors


def test_guarded_relative_imports_are_followed(tmp_path):
    """The relative-vs-bare import pair (`from .inference` / `from inference`) sits in
    `try/except ImportError`; the image carries and runs the module either way."""
    api = API + "try:\n    from .inference import manager\nexcept ImportError:\n    from inference import manager\n"
    files = base_files(**{"service/api.py": api, "service/inference.py": "manager = None\n"})
    findings = check(make_repo(tmp_path, files, declaration()))
    assert any("`service/inference.py` is reached" in error for error in findings.errors)


def test_bare_imports_resolve_in_the_entrypoints_own_directory(tmp_path):
    """`python service/text_api.py` puts service/ first on sys.path (atrium-ocr-postprocess)."""
    files = base_files(**{"service/text_api.py": API + "import text_inference\n", "service/text_inference.py": ""})
    decl = declaration(
        entrypoint="service/text_api.py", core=["service/text_api.py", "tool_limits.py", "stage_core.py"]
    )
    findings = check(make_repo(tmp_path, files, decl))
    assert any("`service/text_inference.py` is reached" in error for error in findings.errors)


def test_a_script_the_service_runs_is_part_of_the_image(tmp_path):
    """nlp-enrich's service runs run_pipeline.py in a subprocess, named in a string literal."""
    api = API + 'PIPELINE = "run_pipeline.py"\n'
    files = base_files(**{"service/api.py": api, "run_pipeline.py": "import research\n"})
    findings = check(make_repo(tmp_path, files, declaration()))
    reached = {error.split("`")[1] for error in findings.errors if "is reached" in error}
    assert reached == {"run_pipeline.py", "research.py"}


def test_worktree_mode_checks_uncommitted_files(tmp_path):
    repo = make_repo(tmp_path, base_files(), declaration(core=[*declaration()["core"], "fresh.py"]))
    (repo / "fresh.py").write_text("", encoding="utf-8")
    (repo / "service" / "api.py").write_text(API + "import fresh\n", encoding="utf-8")
    assert any("`fresh.py` is declared" in error for error in check(repo).errors), "HEAD does not have it yet"
    assert check(repo, worktree=True).errors == []
    assert subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout


def test_the_command_line_exit_codes(tmp_path, capsys):
    repo = make_repo(tmp_path, base_files(**{"service/api.py": API + "import research\n"}), declaration())
    assert ic.main(["--repo-root", str(repo), "--hub-root", str(_HUB_ROOT)]) == 1
    assert "::error::.github/production-image.json: `research.py` is reached" in capsys.readouterr().out
    assert ic.main(["--repo-root", str(tmp_path / "nowhere")]) == 2


@pytest.mark.parametrize(
    "tool",
    [
        "atrium-page-classification",
        "atrium-ocr-postprocess",
        "atrium-translator",
        "atrium-digital-convert",
        "atrium-nlp-enrich",
        "atrium-keyword-extract",
    ],
)
def test_the_sibling_tool_repositories_hold_to_their_declarations(tool):
    """Where the tool repositories sit beside the hub (every ÚFAL working copy), their declarations
    are checked here too, on their working trees — the same check workflow-lint runs in each."""
    repo = _HUB_ROOT.parent / tool
    if not (repo / ".github" / "production-image.json").is_file():
        pytest.skip(f"no {tool} checkout with a declaration beside the hub")
    findings = ic.check(repo, _HUB_ROOT, worktree=True)
    assert findings.errors == []
