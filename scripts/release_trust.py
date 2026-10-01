#!/usr/bin/env python3
"""release_trust.py — immutable releases and protected refs in the six ATRIUM repositories.

atrium-project#40 (A′, E) and #72 E.1: AMČR builds its production images from release tags it
has reviewed, so *"production release tags cannot be silently retargeted"*. That is a matter of
repository settings, not of code, and this script applies them through the GitHub CLI (`gh`,
authenticated as a repository admin) so that they are the same in every repository and can be
read back as evidence:

    status        read-only: immutable releases and rulesets, per repository
    checks        read-only: the check-run names on a branch head, to choose required checks
    immutable     turn immutable releases on (the six tool repositories)
    tag-rules     release tags: no update, no deletion (tool repos `v*`; hub `v1`, `doc-schema-v*`)
    branch-rules  default branch and `test`: no deletion, no force push, changes through a pull
                  request; `--checks` adds required status checks

Every changing command takes `--dry-run` (print each API call and its body, change nothing) and
`--repo NAME` (repeatable; default: all six, or the six tool repositories for `immutable`).
Re-running is safe: a ruleset is found by its name and updated in place.

Repository admins may bypass the rulesets (logged by GitHub as a bypass, so not silent), which
keeps the maintainers' direct pushes to `test` and the planned moves of `v1` possible. An
immutable release cannot be changed by anyone; softprops/action-gh-release v3 in the six
`release.yml` already attaches the assets while the release is a draft, which is what an
immutable release requires (`tools/ci/workflow_lint.py` keeps it that way).

The order, and what to post as evidence, are in docs/release_trust.md.

Examples::

    python3 scripts/release_trust.py status
    python3 scripts/release_trust.py immutable --dry-run
    python3 scripts/release_trust.py checks --repo atrium-translator --branch test
    python3 scripts/release_trust.py branch-rules --repo atrium-translator \\
        --checks "build / Test & Coverage,check-drift / Verify Canonical Paradata Integration"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional

OWNER = "ufal"
HUB = "atrium-project"
TOOLS = (
    "atrium-page-classification",
    "atrium-ocr-postprocess",
    "atrium-translator",
    "atrium-nlp-enrich",
    "atrium-keyword-extract",
    "atrium-digital-convert",
)
ALL = (HUB, *TOOLS)

#: The built-in repository role "Admin" as a ruleset bypass actor.
ADMIN_BYPASS = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]

TAG_RULESET = "ATRIUM release tags (atrium-project#72)"
BRANCH_RULESET = "ATRIUM integration branches (atrium-project#40)"

Gh = Callable[[List[str], Optional[str]], subprocess.CompletedProcess]


def run_gh(args: List[str], body: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], input=body, capture_output=True, text=True)


def tag_patterns(repo: str) -> List[str]:
    """The tags a release is built from: `v*` in a tool repo; the channel and the freezes in the hub."""
    if repo == HUB:
        return ["refs/tags/v1", "refs/tags/doc-schema-v*"]
    return ["refs/tags/v*"]


def tag_ruleset(repo: str) -> Dict[str, Any]:
    return {
        "name": TAG_RULESET,
        "target": "tag",
        "enforcement": "active",
        "bypass_actors": ADMIN_BYPASS,
        "conditions": {"ref_name": {"include": tag_patterns(repo), "exclude": []}},
        # Creation stays open: a release starts with a pushed tag. Moving (retargeting) or
        # deleting one is refused to everyone but the bypass actors.
        "rules": [{"type": "update"}, {"type": "deletion"}],
    }


def branch_ruleset(checks: List[str]) -> Dict[str, Any]:
    rules: List[Dict[str, Any]] = [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 0,
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_review_thread_resolution": False,
                "allowed_merge_methods": ["merge", "squash", "rebase"],
            },
        },
    ]
    if checks:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "required_status_checks": [{"context": context} for context in checks],
                },
            }
        )
    return {
        "name": BRANCH_RULESET,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": ADMIN_BYPASS,
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH", "refs/heads/test"], "exclude": []}},
        "rules": rules,
    }


class Client:
    """`gh api` calls, or their printout with `dry_run`."""

    def __init__(self, gh: Gh = run_gh, dry_run: bool = False, out=sys.stdout) -> None:
        self.gh, self.dry_run, self.out = gh, dry_run, out

    def get(self, path: str) -> Optional[Any]:
        """The decoded JSON of a GET, or None for a 404 (a setting that is off)."""
        result = self.gh(["api", path], None)
        if result.returncode != 0:
            if "404" in (result.stderr or "") or "Not Found" in (result.stderr or ""):
                return None
            raise RuntimeError(f"GET {path}: {(result.stderr or '').strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def send(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> None:
        payload = json.dumps(body, indent=2) if body is not None else None
        if self.dry_run:
            print(f"[dry-run] {method} {path}" + (f"\n{payload}" if payload else ""), file=self.out)
            return
        args = ["api", "--method", method, path]
        if payload is not None:
            args += ["--input", "-"]
        result = self.gh(args, payload)
        if result.returncode != 0:
            raise RuntimeError(f"{method} {path}: {(result.stderr or '').strip()}")
        print(f"{method} {path}: ok", file=self.out)


def upsert_ruleset(client: Client, repo: str, body: Dict[str, Any]) -> None:
    rulesets = client.get(f"repos/{OWNER}/{repo}/rulesets") or []
    existing = next((r["id"] for r in rulesets if r.get("name") == body["name"]), None)
    if existing is None:
        client.send("POST", f"repos/{OWNER}/{repo}/rulesets", body)
    else:
        client.send("PUT", f"repos/{OWNER}/{repo}/rulesets/{existing}", body)


def status(client: Client, repos: List[str]) -> None:
    for repo in repos:
        immutable = client.get(f"repos/{OWNER}/{repo}/immutable-releases")
        state = "on" if immutable and immutable.get("enabled") else "off"
        print(f"{OWNER}/{repo}: immutable releases {state}", file=client.out)
        for ruleset in client.get(f"repos/{OWNER}/{repo}/rulesets") or []:
            detail = client.get(f"repos/{OWNER}/{repo}/rulesets/{ruleset['id']}") or ruleset
            refs = ((detail.get("conditions") or {}).get("ref_name") or {}).get("include") or []
            rules = ", ".join(rule["type"] for rule in detail.get("rules") or [])
            print(
                f"  ruleset {detail.get('name')!r} [{detail.get('target')}, {detail.get('enforcement')}] "
                f"on {', '.join(refs) or '-'}: {rules or '-'}",
                file=client.out,
            )


def checks(client: Client, repo: str, branch: str) -> None:
    runs = client.get(f"repos/{OWNER}/{repo}/commits/{branch}/check-runs?per_page=100") or {}
    for name in sorted({run["name"] for run in runs.get("check_runs") or []}):
        print(name, file=client.out)


def main(argv: Optional[List[str]] = None, gh: Gh = run_gh, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["status", "checks", "immutable", "tag-rules", "branch-rules"])
    parser.add_argument("--repo", action="append", choices=ALL, help="only this repository (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="print the API calls, change nothing")
    parser.add_argument("--branch", default="test", help="`checks`: the branch whose head is read (default: test)")
    parser.add_argument(
        "--checks",
        default="",
        help="`branch-rules`: comma-separated check names to require (read them with `checks` first)",
    )
    args = parser.parse_args(argv)
    client = Client(gh, args.dry_run, out)
    try:
        if args.command == "status":
            status(client, args.repo or list(ALL))
        elif args.command == "checks":
            for repo in args.repo or list(ALL):
                print(f"# {OWNER}/{repo} @ {args.branch}", file=out)
                checks(client, repo, args.branch)
        elif args.command == "immutable":
            for repo in args.repo or list(TOOLS):
                client.send("PUT", f"repos/{OWNER}/{repo}/immutable-releases")
        elif args.command == "tag-rules":
            for repo in args.repo or list(ALL):
                upsert_ruleset(client, repo, tag_ruleset(repo))
        elif args.command == "branch-rules":
            required = [name.strip() for name in args.checks.split(",") if name.strip()]
            for repo in args.repo or list(ALL):
                upsert_ruleset(client, repo, branch_ruleset(required))
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"release_trust: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
