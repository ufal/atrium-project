"""Tests for tools/ci/vendored_pins.py — the pins of tool-to-tool copies (atrium-project#82 B).

`list` feeds the blocking step of para-drift's vendored-parity job (the owner checked out at the
adopted commit), `ahead` its advisory summary. Each rule fails a purpose-built pin file, the way
tests/test_image_closure.py holds its checker.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools" / "ci"))

import vendored_pins as vp  # noqa: E402

COMMIT = "2464756ce61664469f666d3fc6bc90cfc6f02f0b"
OWNER_TEXT = b"def read():\n    return 1\n"
DIGEST = hashlib.sha256(OWNER_TEXT).hexdigest()


def pin_file(tmp_path: Path, body: str, name: str = "test_vendored_x_parity.py") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def valid(owner: str = "atrium-ocr-postprocess", commit: str = COMMIT, extra: str = "") -> str:
    return (
        "import pytest\n"
        f"ADOPTED = {{'owner': '{owner}', 'commit': '{commit}', 'release': 'v1.9.0-beta'}}\n"
        f"VENDORED = {{'text_formats.py': '{DIGEST}'}}\n" + extra
    )


def run_list(capsys, *args: str) -> tuple[int, str, str]:
    code = vp.main(["list", *args])
    out, err = capsys.readouterr()
    return code, out, err


def test_list_prints_file_owner_commit_and_release(tmp_path, capsys):
    path = pin_file(tmp_path, valid())
    code, out, _ = run_list(capsys, str(path), "--owners", "atrium-nlp-enrich atrium-ocr-postprocess")
    assert code == 0
    assert out.strip() == f"{path}\tatrium-ocr-postprocess\t{COMMIT}\tv1.9.0-beta"


def test_the_pins_are_read_without_running_the_file(tmp_path, capsys):
    path = pin_file(tmp_path, "raise SystemExit('imported')\n" + valid())
    code, out, _ = run_list(capsys, str(path))
    assert code == 0 and COMMIT in out


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (f"VENDORED = {{'a.py': '{DIGEST}'}}\n", "no ADOPTED"),
        (valid(commit="2464756"), "not a full 40-hex commit SHA"),
        (valid(commit="test"), "not a full 40-hex commit SHA"),
        (valid(owner="ufal/atrium-ocr-postprocess"), "is not a repository name"),
        (valid().replace(DIGEST, "abc"), "is not a SHA-256 digest"),
        (valid().replace(f"VENDORED = {{'text_formats.py': '{DIGEST}'}}", "VENDORED = {}"), "at least one copy"),
        (valid(extra="SOURCE = {'other.py': 'x.py'}\n"), "which VENDORED does not pin"),
        (valid(extra="VENDORED = dict(a=1)\n"), "cannot read its pins"),
    ],
)
def test_a_malformed_pin_file_fails(tmp_path, capsys, body, message):
    code, out, err = run_list(capsys, str(pin_file(tmp_path, body)))
    assert code == 1
    assert message in err
    assert out == ""


def test_an_owner_the_caller_does_not_declare_fails(tmp_path, capsys):
    code, _, err = run_list(capsys, str(pin_file(tmp_path, valid())), "--owners", "atrium-nlp-enrich")
    assert code == 1
    assert "not in the caller's vendored-from" in err


def owner_checkout(tmp_path: Path, files: dict[str, bytes]) -> Path:
    owner = tmp_path / "owner"
    for rel, data in files.items():
        (owner / rel).parent.mkdir(parents=True, exist_ok=True)
        (owner / rel).write_bytes(data)
    return owner


def test_ahead_is_silent_when_the_owner_file_still_has_the_pinned_digest(tmp_path, capsys):
    owner = owner_checkout(tmp_path, {"text_formats.py": OWNER_TEXT.replace(b"\n", b"\r\n")})
    assert vp.main(["ahead", str(pin_file(tmp_path, valid())), "--owner-dir", str(owner)]) == 0
    assert capsys.readouterr().out == ""


def test_ahead_lists_a_changed_and_a_removed_owner_file(tmp_path, capsys):
    extra = f"VENDORED = {{'text_formats.py': '{DIGEST}', 'tests/fixture.xml': '{DIGEST}'}}\n"
    extra += "SOURCE = {'tests/fixture.xml': 'data_samples/fixture.xml'}\n"
    owner = owner_checkout(tmp_path, {"text_formats.py": b"def read():\n    return 2\n"})
    path = pin_file(tmp_path, valid(extra=extra))
    code = vp.main(["ahead", str(path), "--owner-dir", str(owner), "--owner-ref", "test@abc1234"])
    out = capsys.readouterr().out.splitlines()
    assert code == 0
    assert out == [
        "| `tests/fixture.xml` | atrium-ocr-postprocess at test@abc1234 | `data_samples/fixture.xml` "
        "| removed or moved in the owner |",
        "| `text_formats.py` | atrium-ocr-postprocess at test@abc1234 | `text_formats.py` | changed in the owner |",
    ]


def test_ahead_never_fails_the_step(tmp_path, capsys):
    assert vp.main(["ahead", str(pin_file(tmp_path, "x = 1\n")), "--owner-dir", str(tmp_path)]) == 0
    assert "no ADOPTED" in capsys.readouterr().err


def test_the_workflow_checks_out_the_adopted_commit_and_keeps_the_summary_optional():
    workflow = (_HUB_ROOT / ".github" / "workflows" / "para-drift.reusable.yml").read_text(encoding="utf-8")
    job = workflow[workflow.index("  vendored-parity:") :]
    assert 'vendored_pins.py" list' in job
    assert 'fetch --quiet --depth 1 "https://github.com/ufal/$owner.git" "$commit"' in job
    assert '--branch "$REF"' not in job[: job.index("Summarise the copies")]
    summary = job[job.index("Summarise the copies") :]
    assert "# ci-optional:" in summary and "continue-on-error: true" in summary
