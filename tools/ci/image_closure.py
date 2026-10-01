#!/usr/bin/env python3
"""The production image's first-party closure, held to its declaration (atrium-project#72 A.3).

#72's first acceptance criterion: *"production images contain only their intended stage plus
approved shared components."* Each tool repository declares, in `.github/production-image.json`,
what its production image (the one the AMČR pilot pins, `-api`) is made of:

    {
      "image": "ghcr.io/ufal/atrium-<tool>-api",
      "target": "api",
      "entrypoint": "service/api.py",
      "stage": "one line: the pipeline stage this image serves",
      "core": ["service/api.py", "tool_limits.py", ...],        # this stage's own code
      "vendored": {"api_util/teitok_read.py": "atrium-nlp-enrich"},  # another repo's layer, pinned
      "moving": {"keywords.py": "ufal/atrium-nlp-enrich#40"}   # reached today, leaves with that move
    }

This tool walks everything the entrypoint can execute — imports (guarded ones too: the image
carries them), relative imports, imports resolved from the entrypoint's own directory, and the
scripts a string literal or a shell script names (nlp-enrich's service runs `run_pipeline.py`,
which runs `api_*.sh`) — with the walker `tools/skill_drift_check.py` already uses, and fails on:

  * a reached first-party file that is none of core, vendored, moving or a hub-canonical shared
    component (`docs/templates/shared/MANIFEST.json`, held by para-drift) — the image grew a
    dependency nobody declared, e.g. a research module imported by the service;
  * a declared file the entrypoint no longer reaches — a stale declaration documents an image
    that does not exist (this is also how a finished move is noticed: its `moving` rows go stale);
  * a referenced first-party file that is missing — the image would fail at import;
  * a `vendored` file that no `tests/test_vendored_*.py` pins — tool-to-tool copies are
    drift-checked by their pin tests, which para-drift's `vendored-parity` job runs against the
    owner's `test` head;
  * a malformed declaration (unknown key, a path listed twice, a shared file listed as core).

`moving` rows are reported as notices: they are allowed, and they are the list of what a
repository move (nlp-enrich#40, llm-enrich#29) still has to take out of this image.

A repository without the declaration (the hub) passes with a notice. The committed tree at
`--ref` (default HEAD) is what is checked; `--worktree` snapshots the working tree instead
(tracked and untracked, .gitignore honoured) through a throwaway index, for a local run before
committing. Exit 0 clean, 1 findings, 2 usage error.

Usage:
    python tools/ci/image_closure.py --repo-root ../atrium-translator [--hub-root .] [--worktree]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import skill_drift_check as walker  # noqa: E402
from shared_manifest import load_manifest  # noqa: E402

DECLARATION = ".github/production-image.json"
REQUIRED = {"target", "entrypoint", "core"}
ALLOWED = REQUIRED | {"_comment", "image", "stage", "vendored", "moving"}
PIN_TESTS = "tests/test_vendored_"


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def worktree_tree(repo: Path) -> str:
    """A tree object of the working tree (tracked + untracked, .gitignore honoured), built in a
    throwaway index so neither the real index nor any ref moves."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(repo), *args], env=env, capture_output=True, text=True, check=True
            ).stdout.strip()

        git("read-tree", "HEAD")
        git("add", "-A")
        return git("write-tree")


def shared_components(hub_root: Path) -> set[str]:
    return {entry["dest"] for entry in load_manifest(hub_root / "docs" / "templates" / "shared" / "MANIFEST.json")}


def _paths(value, key: str, findings: Findings) -> dict[str, str]:
    """A declaration section as {path: note}: `core` is a list, `vendored`/`moving` are maps."""
    if value is None:
        return {}
    if key == "core":
        if not isinstance(value, list) or not all(isinstance(p, str) for p in value):
            findings.error(f"`{key}` must be a list of repo-relative paths")
            return {}
        return {path: "" for path in value}
    if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        findings.error(f"`{key}` must map repo-relative paths to a string")
        return {}
    return dict(value)


def check(repo: Path, hub_root: Path, ref: str | None = None, worktree: bool = False) -> Findings:
    findings = Findings()
    declaration_path = repo / DECLARATION
    if not declaration_path.is_file():
        findings.note(f"{repo.name}: no {DECLARATION}, so no production image is declared here")
        return findings
    try:
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.error(f"{DECLARATION} is not JSON: {exc}")
        return findings
    if not isinstance(declaration, dict):
        findings.error(f"{DECLARATION} must be a JSON object")
        return findings
    missing, unknown = REQUIRED - set(declaration), set(declaration) - ALLOWED
    if missing:
        findings.error(f"{DECLARATION} lacks {sorted(missing)}")
    if unknown:
        findings.error(f"{DECLARATION} has unknown key(s) {sorted(unknown)} (allowed: {sorted(ALLOWED)})")
    if missing:
        return findings

    sections = {key: _paths(declaration.get(key), key, findings) for key in ("core", "vendored", "moving")}
    seen: dict[str, str] = {}
    for key, paths in sections.items():
        for path in paths:
            if path in seen:
                findings.error(f"`{path}` is listed in both `{seen[path]}` and `{key}`")
            seen[path] = key

    shared = shared_components(hub_root)
    for path in sorted(set(seen) & shared):
        findings.error(
            f"`{path}` is a hub-canonical shared component (MANIFEST.json); it is approved "
            f"everywhere and must not be listed in `{seen[path]}`"
        )

    tree_ref = worktree_tree(repo) if worktree else (ref or "HEAD")
    files = set(walker.tree(repo, tree_ref))
    if not files:
        findings.error(f"no files at {tree_ref!r} in {repo}")
        return findings
    entrypoint = declaration["entrypoint"]
    if entrypoint not in files:
        findings.error(f"the entrypoint `{entrypoint}` is not in the tree")
        return findings

    reached, absent = walker.closure_from(repo, tree_ref, files, {entrypoint})
    for path in sorted(absent):
        findings.error(f"`{path}` is referenced by the image's code but not in the tree: the image fails to import")
    for path in sorted(reached - shared - set(seen)):
        findings.error(
            f"`{path}` is reached from `{entrypoint}` but not declared: add it to `core` if it is this "
            f"stage's code, or take it out of the production path"
        )
    for path in sorted(set(seen) - reached):
        findings.error(f"`{path}` is declared in `{seen[path]}` but `{entrypoint}` no longer reaches it: remove it")

    pin_text = "\n".join(walker.blob(repo, tree_ref, f) for f in sorted(files) if f.startswith(PIN_TESTS))
    for path, owner in sorted(sections["vendored"].items()):
        if f'"{path}"' not in pin_text:
            findings.error(
                f"`{path}` is vendored from {owner} but no {PIN_TESTS}*.py pins it: a copy that is not "
                f"pinned is not drift-checked"
            )
    for path, issue in sorted(sections["moving"].items()):
        findings.note(f"{repo.name}: `{path}` is in the production image until {issue} moves it out")

    if not findings.errors:
        counts = {key: len(set(paths) & reached) for key, paths in sections.items()}
        findings.note(
            f"{repo.name}: {declaration.get('image', declaration['target'])} — {len(reached)} first-party files "
            f"reached from {entrypoint}: {counts['core']} core, {len(reached & shared)} shared, "
            f"{counts['vendored']} vendored, {counts['moving']} moving"
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo-root", default=".", help="the tool repository to check")
    parser.add_argument(
        "--hub-root",
        default=str(TOOLS.parent),
        help="checkout of ufal/atrium-project whose MANIFEST.json lists the shared components "
        "(default: the hub this script lives in)",
    )
    parser.add_argument("--ref", help="git ref to check (default HEAD)")
    parser.add_argument("--worktree", action="store_true", help="check the working tree instead of a ref")
    args = parser.parse_args(argv)
    if args.ref and args.worktree:
        parser.error("--ref and --worktree are exclusive")
    repo = Path(args.repo_root).resolve()
    if not (repo / ".git").exists():
        print(f"::error::{repo} is not a git checkout", file=sys.stderr)
        return 2
    try:
        findings = check(repo, Path(args.hub_root).resolve(), args.ref, args.worktree)
    except subprocess.CalledProcessError as exc:
        print(f"::error::git failed: {exc.stderr or exc}", file=sys.stderr)
        return 2
    for note in findings.notes:
        print(f"::notice::{note}")
    for error in findings.errors:
        print(f"::error::{DECLARATION}: {error}")
    if findings.errors:
        print(f"\n{len(findings.errors)} problem(s) in {repo.name}'s production image closure.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
