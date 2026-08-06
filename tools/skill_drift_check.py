#!/usr/bin/env python3
"""
skill_drift_check.py — report `agent-skill` ↔ default-branch drift (hub issue #31, strategy §12.2).

The `agent-skill` branches are trimmed derivatives of the default branches, kept current by
porting `service/` changes forward **by hand**. Three of the five branches share no git history
with their default branch at all, so `git log`/`git merge` say nothing useful about how stale a
skill branch is. This tool answers that question directly, by content.

It is the check that would have caught the 2026-07-29 re-drift in seconds: the accretion
parameters missing from three services, the absent `atrium_document.py`, the stale
`atrium_paradata.py`, and the two-minor version lag on every branch.

Checks
------
    content   common files whose content differs, minus the expected-divergence allowlist
    runtime   modules the skill branch's own `service/` imports but does not carry (the
              service would not start), plus modules the default branch's `service/` newly
              imports that a port would have to bring along
    version   `para_config.txt` `[tool] version` parity — §4.6 surfaces this through `/info`,
              so a lag here means every skill branch misreports its version
    shared    byte-parity of the para-drift-guarded shared files

Exit codes: 0 clean · 1 drift found · 2 usage error. stdlib-only, like the e2e tools.

Usage
-----
    python3 tools/skill_drift_check.py                       # all repos beside the hub
    python3 tools/skill_drift_check.py --repo atrium-translator
    python3 tools/skill_drift_check.py --test-ref origin/master --quiet
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

# Files a trimmed skill branch is *expected* to diverge on — the branch README documents
# skill installation rather than development, and the container/ignore files are retargeted.
# Everything else differing is drift worth a human's attention.
ALLOWLIST = {
    "README.md",
    "CONTRIBUTING.md",
    "Dockerfile",
    ".gitignore",
    ".dockerignore",
}
ALLOWLIST_GLOBS = ("docker-compose",)

# Guarded byte-identical by the hub's para-drift.reusable.yml.
SHARED_FILES = (
    "atrium_paradata.py",
    "atrium_document.py",
    "atrium_document.schema.json",
    "para_licenses.py",
    "service/atrium_service.py",
)

REPOS = (
    "atrium-page-classification",
    "atrium-translator",
    "atrium-alto-postprocess",
    "atrium-nlp-enrich",
    "atrium-llm-enrich",
)

_VERSION_RE = re.compile(r"^\s*version\s*=\s*(\S+)", re.M)


def git(repo: Path, *args: str) -> str:
    """Run git in `repo`; return stdout, or '' when the command fails (missing ref/path).

    Decoded leniently — some tracked blobs are binary (the KER idf pickles), and this
    tool only ever reads text out of the ones it parses.
    """
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


def tree(repo: Path, ref: str) -> dict:
    """path -> (mode, blob sha) for every file at `ref`.

    Comparing recorded SHAs rather than file contents is binary-safe, needs one git call
    per ref instead of one per file, and surfaces mode-only changes (the 100755 -> 100644
    drift on nlp-enrich) that a content diff would silently pass.
    """
    entries = {}
    for line in git(repo, "ls-tree", "-r", ref).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and len(parts) >= 3:
            entries[path] = (parts[0], parts[2])
    return entries


def blob(repo: Path, ref: str, path: str) -> str:
    return git(repo, "show", f"{ref}:{path}")


def allowlisted(path: str) -> bool:
    return path in ALLOWLIST or any(path.startswith(g) for g in ALLOWLIST_GLOBS)


def _catches_import_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    caught = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(isinstance(node, ast.Name) and node.id in {"ImportError", "ModuleNotFoundError"} for node in caught)


def _imports_of(repo: Path, ref: str, path: str) -> set:
    """Top-level module names `path` imports, excluding optional ones.

    An import guarded by `try: ... except ImportError:` is optional by construction —
    `atrium_paradata.py` degrades to `None` when `para_licenses` is absent — so counting
    it as a hard dependency would report every legitimately trimmed skill branch as broken.
    Parsed with ast rather than a regex so multi-line imports and imports mentioned inside
    strings or comments are handled correctly.
    """
    try:
        module = ast.parse(blob(repo, ref, path))
    except (SyntaxError, ValueError):
        return set()

    optional = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Try) and any(_catches_import_error(h) for h in node.handlers):
            optional.update(
                id(child)
                for stmt in node.body
                for child in ast.walk(stmt)
                if isinstance(child, (ast.Import, ast.ImportFrom))
            )

    names = set()
    for node in ast.walk(module):
        if id(node) in optional:
            continue
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names.add(node.module.split(".")[0])
    return names


def runtime_closure(repo: Path, ref: str, files: set) -> set:
    """Repo-local root modules the service needs, followed transitively.

    One level is not enough: translator's `service/api.py` never imports `atrium_document`
    itself, but the `main.py` it calls does — so a one-level scan would report the skill
    branch as complete while the ported service still fails at runtime.
    """
    root_modules = {f[:-3] for f in files if f.endswith(".py") and "/" not in f}
    pending = set()
    for path in sorted(f for f in files if f.startswith("service/") and f.endswith(".py")):
        pending |= _imports_of(repo, ref, path)

    needed, seen = set(), set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        if name not in root_modules:
            continue  # third-party or stdlib — not our problem
        needed.add(name)
        pending |= _imports_of(repo, ref, f"{name}.py") - seen
    return needed


def version_of(repo: Path, ref: str, files: set) -> str:
    for candidate in ("para_config.txt", "setup/para_config.txt"):
        if candidate in files:
            match = _VERSION_RE.search(blob(repo, ref, candidate))
            if match:
                return match.group(1)
    return "?"


def check_repo(repo: Path, test_ref: str, skill_ref: str, quiet: bool) -> list:
    """Return a list of drift findings for one repo (empty == clean)."""
    findings = []
    test_tree, skill_tree = tree(repo, test_ref), tree(repo, skill_ref)
    if not test_tree or not skill_tree:
        return [f"cannot resolve {test_ref} and/or {skill_ref} — fetch them first"]
    test_files, skill_files = set(test_tree), set(skill_tree)

    # --- content: common files that differ -----------------------------------------------
    differing, mode_only = [], []
    for path in sorted(test_files & skill_files):
        if allowlisted(path):
            continue
        (test_mode, test_sha), (skill_mode, skill_sha) = test_tree[path], skill_tree[path]
        if test_sha != skill_sha:
            differing.append(path)
        elif test_mode != skill_mode:
            mode_only.append(f"{path} ({skill_mode} vs {test_mode})")
    if differing:
        findings.append(f"{len(differing)} common file(s) differ from {test_ref}:")
        findings += [f"    {path}" for path in differing]
    if mode_only:
        findings.append("file-mode drift: " + ", ".join(mode_only))

    # --- runtime closure -----------------------------------------------------------------
    missing_now = sorted(
        name for name in runtime_closure(repo, skill_ref, skill_files) if f"{name}.py" not in skill_files
    )
    if missing_now:
        findings.append(
            "skill branch service/ needs modules it does not carry (service will not start): " + ", ".join(missing_now)
        )

    port_closure = runtime_closure(repo, test_ref, test_files)
    missing_after_port = sorted(
        name for name in port_closure if f"{name}.py" not in skill_files and name not in missing_now
    )
    if missing_after_port:
        findings.append(
            "a port of the default-branch service/ would additionally need: " + ", ".join(missing_after_port)
        )

    # --- version -------------------------------------------------------------------------
    test_version = version_of(repo, test_ref, test_files)
    skill_version = version_of(repo, skill_ref, skill_files)
    if test_version != skill_version:
        findings.append(f"version lag (§4.6, surfaced by /info): skill {skill_version} vs {test_ref} {test_version}")

    # --- shared files --------------------------------------------------------------------
    # Present on both: must be byte-identical, since para-drift guards them on the default
    # branch. Absent from the skill branch: only a defect when the service actually needs it
    # — dev-only members of the set (para_licenses.py) are legitimately trimmed by §5.
    for path in SHARED_FILES:
        on_test, on_skill = path in test_files, path in skill_files
        if on_test and on_skill:
            if test_tree[path][1] != skill_tree[path][1]:
                findings.append(f"para-drift-guarded file out of parity: {path}")
        elif on_test and (path.removesuffix(".py") in port_closure or path.startswith("service/")):
            findings.append(f"para-drift-guarded file needed by the service but absent: {path}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report agent-skill ↔ default-branch drift (strategy §12.2).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="directory holding the tool repo clones (default: the hub's parent)",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        metavar="NAME",
        help="check only this repo (repeatable; default: all five service repos)",
    )
    parser.add_argument("--test-ref", default="origin/test", help="default-branch ref (default: origin/test)")
    parser.add_argument("--skill-ref", default="origin/agent-skill", help="skill ref (default: origin/agent-skill)")
    parser.add_argument("--quiet", action="store_true", help="print only repos with drift")
    args = parser.parse_args()

    drifted = 0
    checked = 0
    for name in args.repos or REPOS:
        repo = args.repos_root / name
        if not (repo / ".git").exists():
            print(f"[skill-drift][SKIP] {name}: no clone at {repo}")
            continue
        checked += 1
        findings = check_repo(repo, args.test_ref, args.skill_ref, args.quiet)
        if findings:
            drifted += 1
            print(f"\n[skill-drift][DRIFT] {name}")
            for line in findings:
                print(f"  - {line}" if not line.startswith("    ") else line)
        elif not args.quiet:
            print(f"[skill-drift][OK]    {name}: aligned with {args.test_ref}")

    if not checked:
        print("[skill-drift][FAIL] no repo clones found — pass --repos-root", file=sys.stderr)
        return 2
    print(f"\n[skill-drift] {checked - drifted}/{checked} repos aligned")
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
