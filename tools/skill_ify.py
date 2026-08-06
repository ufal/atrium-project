#!/usr/bin/env python3
"""
skill_ify.py — derive the trimmed `agent-skill` tree from a default-branch ref
(hub issue #31, strategy §5 branch anatomy / §12.2 branch sync).

§12.2 has been deferring "a scripted skill-ify transform" since the standard was written,
on the grounds that the branches were still churning. The cost of not having it is the
periodic hand-audit that keeps rediscovering the same drift, so this is that transform —
deliberately advisory: it prints or materializes a tree, and never commits or pushes.
The maintainer still lands the result, per §12.2's manual policy.

The skill branch is the default branch, minus development-only material (§5), plus the
skill overlay (SKILL.md, the client, samples, branch README) which lives only on the skill
branch and is carried across untouched.

Subcommands
-----------
    plan    print the add/update/delete delta between the derived tree and the current
            `agent-skill` branch — the review artifact
    apply   materialize the derived tree into a directory, to diff or commit by hand

Exit codes: 0 success (plan: 0 whether or not there is a delta) · 2 usage error.
stdlib-only, like the e2e tools.

Usage
-----
    python3 tools/skill_ify.py plan  --repo ../atrium-translator
    python3 tools/skill_ify.py apply --repo ../atrium-translator --into /tmp/translator-skill
"""

import argparse
import subprocess
import sys
from pathlib import Path

# §5 "Removed relative to the default branch" — anything a *running* skill does not need.
TRIM_DIRS = (
    "tests/",
    "data_samples/",
    "agent_dev_logs/",
    "tools/",
    "supplementary/",
    "result/",
    "eval/",
    "annotation/",
    "paradata/",
    "data_scripts/",
)
TRIM_FILES = (
    "ruff.toml",
    "pytest.ini",
    ".pre-commit-config.yaml",
    ".coveragerc",
    "requirements-test.txt",
    "CONTRIBUTING.md",
    "conftest.py",
)
# Root-level test scaffolding that lives outside tests/ (translator's atrium_test_support.py).
TRIM_SUFFIXES = ("_test_support.py",)
TRIM_PREFIXES = ("test_",)
# The skill branch keeps exactly one workflow: its own validation caller (§12.3).
KEEP_WORKFLOW = ".github/workflows/skill-validate.yml"

# Paths authored on the skill branch — never derived from the default branch, always
# carried across as-is even when the default branch has a file of the same name.
OVERLAY_DIRS = ("scripts/", "small_data_samples/", "service/frontend")
OVERLAY_FILES = ("SKILL.md", "README.md", "service/README.md", KEEP_WORKFLOW)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


def tree(repo: Path, ref: str) -> dict:
    """path -> blob sha at `ref`."""
    entries = {}
    for line in git(repo, "ls-tree", "-r", ref).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and len(parts) >= 3:
            entries[path] = parts[2]
    return entries


def is_overlay(path: str) -> bool:
    return path in OVERLAY_FILES or path.startswith(OVERLAY_DIRS)


def is_trimmed(path: str) -> bool:
    if path.startswith(".github/"):
        return path != KEEP_WORKFLOW
    if path.startswith(TRIM_DIRS) or path in TRIM_FILES:
        return True
    name = path.rsplit("/", 1)[-1]
    return name.endswith(TRIM_SUFFIXES) or name.startswith(TRIM_PREFIXES)


def derive(repo: Path, test_ref: str, skill_ref: str) -> dict:
    """The tree the skill branch *should* have: trimmed default branch + skill overlay.

    Files the skill branch carries that the default branch does not are kept, not dropped.
    They are there deliberately — the branch README, `service/README.md`, runtime modules
    added to close the import closure, and alto's slimmed `text_util_langID.py`. Retiring
    one of those is a human decision (§12.2), so the transform proposes deleting only what
    the §5 trim list names.
    """
    derived = {path: sha for path, sha in tree(repo, test_ref).items() if not is_trimmed(path) and not is_overlay(path)}
    for path, sha in tree(repo, skill_ref).items():
        if is_trimmed(path):
            continue
        # Overlay wins outright; anything else skill-only is carried across untouched.
        if is_overlay(path) or path not in derived:
            derived[path] = sha
    return derived


def cmd_plan(repo: Path, test_ref: str, skill_ref: str) -> int:
    derived = derive(repo, test_ref, skill_ref)
    current = tree(repo, skill_ref)
    if not derived or not current:
        print(f"[skill-ify][FAIL] cannot resolve {test_ref} / {skill_ref} in {repo}", file=sys.stderr)
        return 2

    added = sorted(set(derived) - set(current))
    removed = sorted(set(current) - set(derived))
    updated = sorted(p for p in set(derived) & set(current) if derived[p] != current[p])

    print(f"[skill-ify] {repo.name}: {skill_ref} vs trimmed({test_ref}) + overlay")
    for label, paths in (("add", added), ("update", updated), ("delete", removed)):
        for path in paths:
            print(f"  {label:6} {path}")
    if not (added or updated or removed):
        print("  (no delta — the skill branch already matches the derived tree)")
    print(
        f"\n[skill-ify] {len(added)} to add, {len(updated)} to update, {len(removed)} to delete."
        "\n[skill-ify] Advisory only — review and land by hand (§12.2)."
    )
    return 0


def cmd_apply(repo: Path, test_ref: str, skill_ref: str, into: Path) -> int:
    derived = derive(repo, test_ref, skill_ref)
    if not derived:
        print(f"[skill-ify][FAIL] cannot resolve {test_ref} in {repo}", file=sys.stderr)
        return 2
    if into.exists() and any(into.iterdir()):
        print(f"[skill-ify][FAIL] {into} exists and is not empty", file=sys.stderr)
        return 2

    skill_paths = set(tree(repo, skill_ref))
    for path, _ in sorted(derived.items()):
        source_ref = skill_ref if is_overlay(path) and path in skill_paths else test_ref
        blob = subprocess.run(["git", "-C", str(repo), "show", f"{source_ref}:{path}"], capture_output=True)
        if blob.returncode != 0:
            print(f"[skill-ify][WARN] could not read {source_ref}:{path}", file=sys.stderr)
            continue
        target = into / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob.stdout)

    print(f"[skill-ify] wrote {len(derived)} files to {into}")
    print(f"[skill-ify] diff against the branch with:\n  diff -r {into} <a checkout of {skill_ref}>")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive the trimmed agent-skill tree from a default-branch ref (§5/§12.2).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=("plan", "apply"))
    parser.add_argument("--repo", type=Path, required=True, help="path to the tool repo clone")
    parser.add_argument("--test-ref", default="origin/test", help="default-branch ref (default: origin/test)")
    parser.add_argument("--skill-ref", default="origin/agent-skill", help="skill ref (default: origin/agent-skill)")
    parser.add_argument("--into", type=Path, help="output directory (apply only)")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"[skill-ify][FAIL] {repo} is not a git clone", file=sys.stderr)
        return 2

    if args.command == "plan":
        return cmd_plan(repo, args.test_ref, args.skill_ref)
    if not args.into:
        print("[skill-ify][FAIL] apply requires --into DIR", file=sys.stderr)
        return 2
    return cmd_apply(repo, args.test_ref, args.skill_ref, args.into.resolve())


if __name__ == "__main__":
    sys.exit(main())
