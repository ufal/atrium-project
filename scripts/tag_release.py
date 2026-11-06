#!/usr/bin/env python3
"""tag_release.py — tag a tool repository's release so that its Release Bundle run starts, on the right commit.

Run from a tool repository checkout (or pass --repo):

    python3 ../atrium-project/scripts/tag_release.py v1.7.8-beta

WHY THIS EXISTS (atrium-project#66, the translator, 2026-11-05). A release tag is protected and
never moved (docs/release_trust.md), so a tag that misses is a version lost. Two ways it missed:

  1. **The tag on the wrong commit.** `v1.7.6-beta` was created on `5b25f83`, before the commit
     that bumped CITATION.cff and para_config.txt, and pushed together with that commit. Release
     Bundle 42103826703 stopped at the version gate (tag 1.7.6, CITATION 1.7.5), as it should;
     the release had to move to v1.7.7-beta.
  2. **A tag push that starts no run.** translator `v1.7.4-beta` and digital-convert `v1.4.3-beta`
     (11-04) created no run at all, and keyword-extract's mistyped `v1.6.3.-beta` none either; the
     cause is not recorded. GitHub creates no push event for tags when more than three are pushed
     at once, which `git push --tags` from a checkout with stale local tags does without a word.

  3. **A tag on a commit whose CI was red.** translator `v1.7.7-beta` (11-06) was tagged three
     minutes after Docker Build & Push had failed on its commit; its release stopped in the same test
     job. The version gate passes on such a commit, so the script also reads the commit's runs.

So this script tags only what the remote branch already has, only when the release gate would
pass and the commit's push runs passed, and pushes exactly one ref:

  * the tag is `vX.Y.Z` or `vX.Y.Z-suffix` (no stray dot);
  * the working tree has no uncommitted change to tracked files;
  * HEAD is `<remote>/<branch>` after a fetch: the version bump is committed AND pushed;
  * the repository's own vendored `check_version.py --tag … --require-tag` passes — the same
    check `release.yml`'s version-guard runs, so a refusal here is a failed run avoided;
  * with `gh`, every push run of HEAD has finished and passed (`--no-ci-check` skips this; without
    `gh` it is reported as not done);
  * the tag exists neither on the remote nor, unpushed, locally (delete a local-only tag first).

Then it creates an annotated tag on HEAD and pushes `refs/tags/<tag>` alone. With the `gh` CLI it
waits for the Release Bundle run of that tag and prints its URL. When none appears, the recovery
is a dispatch of the same workflow on the tag, which is a full release, not a dry run: every
publish condition in release.yml and docker-tool.reusable.yml reads `refs/tags/v`.

    gh workflow run release.yml --ref <tag>     (or Actions → Release Bundle → Run workflow → the tag)

Exit status: 0 tagged and pushed (or, with --dry-run, would be); 1 refused; 2 usage error.
stdlib only. Tested by tests/test_tag_release.py.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

TAG_RE = re.compile(r"^v\d+\.\d+\.\d+(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$")
PARA_CONFIGS = ("para_config.txt", "setup/para_config.txt")
RELEASE_WORKFLOW = "release.yml"


class Refusal(Exception):
    """A reason not to tag; the message says what to do instead."""


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.strip()


def repo_slug(url: str) -> Optional[str]:
    """`owner/name` of a GitHub remote URL (https or ssh), or None."""
    match = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def para_config(repo: Path) -> Path:
    for name in PARA_CONFIGS:
        if (repo / name).is_file():
            return repo / name
    raise Refusal(f"no para_config.txt in {repo} (looked for {', '.join(PARA_CONFIGS)})")


def preflight(repo: Path, tag: str, remote: str, branch: str) -> str:
    """Every check before tagging; returns the commit to tag."""
    if not TAG_RE.match(tag):
        raise Refusal(f"{tag!r} is not a release tag: vX.Y.Z or vX.Y.Z-suffix, e.g. v1.7.8-beta")
    for name in ("CITATION.cff", "check_version.py"):
        if not (repo / name).is_file():
            raise Refusal(f"{repo} has no {name}: run this from a tool repository")
    pc = para_config(repo)

    dirty = git(repo, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise Refusal(f"uncommitted changes to tracked files:\n{dirty}\ncommit and push them first, then tag")

    git(repo, "fetch", "--quiet", remote, branch)
    git(repo, "fetch", "--quiet", "--tags", remote)
    head = git(repo, "rev-parse", "HEAD")
    pushed = git(repo, "rev-parse", f"{remote}/{branch}")
    if head != pushed:
        ahead = git(repo, "rev-list", "--count", f"{remote}/{branch}..HEAD")
        behind = git(repo, "rev-list", "--count", f"HEAD..{remote}/{branch}")
        raise Refusal(
            f"HEAD {head[:12]} is not {remote}/{branch} {pushed[:12]} ({ahead} ahead, {behind} behind): "
            f"push the release commit to {branch} first (or pull), then tag; a tag on an unpushed or "
            f"older commit is how v1.7.6-beta missed its version bump"
        )

    gate = subprocess.run(
        [
            sys.executable,
            "check_version.py",
            "--citation",
            "CITATION.cff",
            "--para-config",
            str(pc.relative_to(repo)),
            "--tag",
            tag,
            "--require-tag",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if gate.returncode != 0:
        raise Refusal(
            f"the release gate would fail at {head[:12]}:\n{(gate.stdout + gate.stderr).strip()}\n"
            f"bump CITATION.cff and {pc.relative_to(repo)} to {tag} in a commit, push it, then tag"
        )

    if git(repo, "ls-remote", "--tags", remote, f"refs/tags/{tag}"):
        raise Refusal(f"the tag {tag} already exists on {remote}; release tags are never moved: release the next one")
    if git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{tag}", check=False):
        raise Refusal(
            f"the tag {tag} exists only locally (it was never pushed, so the version is unused): "
            f"delete it with `git tag -d {tag}`, then run this again"
        )
    return head


#: Conclusions of a push run that make its commit unfit to release.
BAD_CONCLUSIONS = {"failure", "timed_out", "startup_failure", "action_required", "cancelled"}


def check_ci(gh: Optional[str], slug: Optional[str], sha: str) -> str:
    """Refuse a commit whose push runs failed or are still running; return what was checked.

    `v1.7.7-beta` (translator, 11-06) was tagged three minutes after Docker Build & Push had failed on
    its commit, and its Release Bundle stopped in the same test job. The release gate cannot see
    that; the commit's own runs can.
    """
    if not gh or not slug:
        return "CI not checked (gh is not installed, or the remote is not on GitHub): look at the commit's runs first"
    proc = subprocess.run(
        [
            gh,
            "run",
            "list",
            "--repo",
            slug,
            "--commit",
            sha,
            "--json",
            "name,status,conclusion,event,url",
            "--limit",
            "100",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"CI not checked (`gh run list` failed: {(proc.stderr or proc.stdout).strip()[:200]})"
    try:
        runs = [run for run in json.loads(proc.stdout or "[]") if run.get("event") == "push"]
    except json.JSONDecodeError:
        return "CI not checked (`gh run list` printed no JSON)"
    if not runs:
        return f"CI not checked: no push run of {sha[:12]} was found"
    failed = [run for run in runs if run.get("status") == "completed" and run.get("conclusion") in BAD_CONCLUSIONS]
    running = [run for run in runs if run.get("status") != "completed"]
    if failed:
        listed = "\n".join(f"  {run.get('name')}: {run.get('conclusion')} {run.get('url', '')}" for run in failed)
        raise Refusal(f"the commit {sha[:12]} has push runs that did not pass:\n{listed}\nfix them, push, then tag")
    if running:
        listed = "\n".join(f"  {run.get('name')}: {run.get('status')}" for run in running)
        raise Refusal(f"the commit {sha[:12]} still has push runs going:\n{listed}\nwait until they pass, then tag")
    return f"CI green: {len(runs)} push run(s) of {sha[:12]} passed"


def wait_for_run(gh: Optional[str], slug: Optional[str], tag: str, seconds: int) -> Optional[str]:
    """The URL of the Release Bundle run for the tag, if `gh` can see one within `seconds`."""
    if not gh or not slug or seconds <= 0:
        return None
    deadline = time.monotonic() + seconds
    while True:
        proc = subprocess.run(
            [
                gh,
                "run",
                "list",
                "--repo",
                slug,
                "--workflow",
                RELEASE_WORKFLOW,
                "--branch",
                tag,
                "--json",
                "url,status,event",
                "--limit",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            try:
                runs = json.loads(proc.stdout or "[]")
            except json.JSONDecodeError:
                runs = []
            if runs:
                return runs[0].get("url")
        if time.monotonic() >= deadline:
            return None
        time.sleep(5)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tag", help="the release tag, e.g. v1.7.8-beta")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="the tool repository (default: here)")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="test", help="the branch the release commit is on (default: test)")
    parser.add_argument("--dry-run", action="store_true", help="check everything, tag nothing")
    parser.add_argument("--wait", type=int, default=90, help="seconds to wait for the Release Bundle run (gh)")
    parser.add_argument("--no-ci-check", action="store_true", help="tag without checking the commit's push runs")
    parser.add_argument("--gh", default=shutil.which("gh"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    repo = Path(git(args.repo, "rev-parse", "--show-toplevel", check=False) or args.repo)
    try:
        head = preflight(repo, args.tag, args.remote, args.branch)
    except Refusal as exc:
        print(f"tag_release: refused: {exc}", file=sys.stderr)
        return 1

    slug = repo_slug(git(repo, "remote", "get-url", args.remote, check=False))
    if args.no_ci_check:
        print("tag_release: CI not checked (--no-ci-check)")
    else:
        try:
            print(f"tag_release: {check_ci(args.gh, slug, head)}")
        except Refusal as exc:
            print(f"tag_release: refused: {exc}", file=sys.stderr)
            return 1
    if args.dry_run:
        print(f"tag_release: would tag {head[:12]} as {args.tag} and push refs/tags/{args.tag} to {args.remote}")
        return 0

    git(repo, "tag", "-a", args.tag, "-m", args.tag, head)
    try:
        git(repo, "push", args.remote, f"refs/tags/{args.tag}")
    except Refusal as exc:
        git(repo, "tag", "-d", args.tag, check=False)
        print(f"tag_release: the push failed, the local tag is removed again: {exc}", file=sys.stderr)
        return 1
    print(f"tag_release: tagged {head[:12]} as {args.tag} and pushed that tag alone to {args.remote}")

    url = wait_for_run(args.gh, slug, args.tag, args.wait)
    if url:
        print(f"tag_release: Release Bundle run: {url}")
        return 0
    actions = f"https://github.com/{slug}/actions/workflows/{RELEASE_WORKFLOW}" if slug else "the Actions tab"
    seen = "no run seen yet" if args.gh else "gh is not installed, so the run was not checked"
    print(
        f"tag_release: {seen}. Check {actions}; if the tag started no run, dispatch the release on the tag:\n"
        f"    gh workflow run {RELEASE_WORKFLOW} --ref {args.tag}" + (f" --repo {slug}" if slug else "") + "\n"
        f"  (Actions → Release Bundle → Run workflow → {args.tag}: on a tag ref that run is the release)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
