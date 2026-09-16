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

# tools/ is this script's own directory when run as `python3 tools/skill_ify.py`; inserted
# explicitly too, so importing this module from elsewhere still finds its neighbour. The
# reachability answer has exactly one implementation, in skill_drift_check.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared_manifest import load_manifest  # noqa: E402
from skill_drift_check import runtime_closure  # noqa: E402

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "docs" / "templates" / "shared" / "MANIFEST.json"


def _canonical_dests() -> set:
    """Tool-repo paths of the para-drift canonical files, from the single manifest (#59)."""
    try:
        return {entry["dest"] for entry in load_manifest(_MANIFEST_PATH)}
    except (OSError, ValueError):  # running against a checkout without the manifest
        return set()


# §5 "Removed relative to the default branch" — anything a *running* skill does not need.
TRIM_DIRS = (
    "tests/",
    # §5 names "dev-only frontends" for removal. The LINDAT frontend is the deployment-
    # specific one; service/frontend/ is the skill's own and is overlay-protected above.
    # It survived on three branches only because OVERLAY_DIRS' bare "service/frontend"
    # prefix matched it -- see the note there.
    "service/frontend-lindat/",
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
# The trailing slash on service/frontend/ is load-bearing. As a bare prefix it also matched
# `service/frontend-lindat/`, so the dev-only LINDAT frontends were treated as protected
# overlay and survived on three branches despite §5 naming "dev-only frontends" for removal.
OVERLAY_DIRS = ("scripts/", "small_data_samples/", "service/frontend/")
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
    test_tree = tree(repo, test_ref)
    derived = {path: sha for path, sha in test_tree.items() if not is_trimmed(path) and not is_overlay(path)}

    # ALLOWLIST pass (2026-09-16). Everything above is a DENYLIST: it starts from the whole
    # default-branch tree and subtracts TRIM_DIRS/TRIM_FILES, so any file nobody thought to
    # name survives -- which is why `run.py` (46 KB) and `parallel_best.py` (24 KB, imported
    # only by run.py) sat on the page-classification skill branch, and why `plan` reported
    # "0 to delete" for every repo. skill_drift_check.runtime_closure already computed the
    # answer; the two tools sat in the same directory and did not talk.
    #
    # A .py file is kept only if the service, the §6 client, or the branch's own docs
    # reference it, transitively. That last clause is what keeps `run.py`: README.md and
    # service/README.md document `python3 run.py --hf -rev vX.3` in backticks, so it IS
    # reachable and the two tools agree. Delete those doc lines and both agree it should go
    # -- which is the honest order of operations, since dropping a documented file would
    # otherwise turn skill-validate's referenced-path step red.
    keep = runtime_closure(repo, test_ref, set(test_tree), universe=set(test_tree))
    # para-drift's canonical files are held for ECOSYSTEM parity, not because this service
    # imports them -- `atrium_vocab.py` is reached only through a try/except ImportError in
    # model_registry.py, so the closure correctly calls it unreachable. Trimming it anyway
    # would set this tool against docs/templates/shared/MANIFEST.json, and
    # skill_drift_check's shared-files block already tolerates a canonical file being absent
    # from a skill branch when the service does not need it. Leave that call to a human.
    canonical = _canonical_dests()
    derived = {
        path: sha
        for path, sha in derived.items()
        if not path.endswith(".py") or path in keep or path in canonical or path.startswith(("service/", "scripts/"))
    }

    for path, sha in tree(repo, skill_ref).items():
        if is_trimmed(path):
            continue
        # Overlay wins outright; anything else SKILL-AUTHORED is carried across untouched.
        # The test is `not in test_tree` (skill-authored), not `not in derived`: the latter
        # also resurrected every file the allowlist had just trimmed, which is why `plan`
        # still said "0 to delete" after the allowlist landed. This matches what this
        # function's docstring always claimed -- "files the skill branch carries that the
        # DEFAULT BRANCH does not are kept".
        if is_overlay(path) or path not in test_tree:
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
