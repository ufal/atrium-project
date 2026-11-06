#!/usr/bin/env python3
"""release_trust.py — immutable releases and protected refs in the six ATRIUM repositories.

atrium-project#40 (A′, E) and #72 E.1: AMČR builds its production images from release tags it
has reviewed, so *"production release tags cannot be silently retargeted"*. That is a matter of
repository settings, not of code, and this script applies them through the GitHub CLI (`gh`,
authenticated as a repository admin) so that they are the same in every repository and can be
read back as evidence:

    status        read-only: immutable releases and rulesets (with their bypass), per repository
    checks        read-only: the check-run names on a branch head, to choose required checks
    immutable     turn immutable releases on (the six tool repositories)
    tag-rules     two tag rulesets: release tags can never be moved or deleted, by anyone (tool
                  repos `v*`; hub `doc-schema-v*`); and only maintainers create, move or delete
                  them (tool repos `v*`; hub `v1` and `doc-schema-v*`)
    branch-rules  two branch rulesets on the default branch and `test`: nobody deletes or
                  force-pushes them; and everyone but the maintainers changes them through a pull
                  request with one approval, plus the status checks named in `--checks`

Every changing command takes `--dry-run` (print each API call and its body, change nothing) and
`--repo NAME` (repeatable; default: all seven — the hub and the six tool repositories — or the six
tool repositories for `immutable`).
Re-running is safe: a ruleset is found by its name and updated in place.

"Maintainers" are the repository roles Maintain and Admin. A ruleset's bypass list can name roles,
teams, apps or deploy keys, but no single user, and the maintainer who pushes and tags the releases
holds Maintain, not Admin, in four of the seven repositories, so an Admin-only bypass would stop
the releases there. Their direct pushes stay possible, and GitHub reports each one as a bypass in
the push output. The no-bypass rulesets hold for admins too: an admin who has to break one disables
the ruleset first, which the organisation's audit log records. The hub's `v1` moves with every hub
change, so it is in the maintainers-only ruleset, not the no-bypass one; the tool repositories call
the reusables by commit (`pin_hub_reusables.py`), so a move does not reach them. An immutable
release cannot be changed by anyone; softprops/action-gh-release v3 in the six `release.yml`
already attaches the assets while the release is a draft, which is what an immutable release
requires (`tools/ci/workflow_lint.py` keeps it that way).

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

#: The built-in repository roles Maintain and Admin as ruleset bypass actors. GitHub's web UI names
#: the role behind each id; check it, and `current_user_can_bypass`, with `status` after the first run.
MAINTAIN_ROLE_ID = 2
ADMIN_ROLE_ID = 5
MAINTAINER_BYPASS = [
    {"actor_id": MAINTAIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": "always"},
    {"actor_id": ADMIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": "always"},
]
#: The bypass list of a rule nobody may break, as in the tag rulesets created by hand in 2026-10.
NO_BYPASS: List[Dict[str, Any]] = []

#: Rules for a ref nobody may delete or rewrite.
FIXED_REF_RULES = [{"type": "update"}, {"type": "deletion"}, {"type": "non_fast_forward"}]
#: Rules for a ref only the bypass actors may create, move or delete.
MAINTAINER_REF_RULES = [{"type": "creation"}, {"type": "update"}, {"type": "deletion"}, {"type": "non_fast_forward"}]
#: Approvals a pull request needs from someone other than its author before it merges.
REQUIRED_APPROVALS = 1

TAG_RULESET = "ATRIUM release tags (atrium-project#72)"
# Tag rulesets created by hand before this script was run (page-classification and nlp-enrich on
# 2026-10-19, the other four on 2026-10-29). `tag-rules` updates such a ruleset in place, under its
# own name, rather than adding a second one beside it.
TAG_RULESET_ALIASES = ("Protect v* Tags",)
TAGGER_RULESET = "ATRIUM tags only maintainers push (atrium-project#40)"
HISTORY_RULESET = "ATRIUM branch history (atrium-project#40)"
BRANCH_RULESET = "ATRIUM changes by pull request (atrium-project#40)"
BRANCHES = ["~DEFAULT_BRANCH", "refs/heads/test"]

Gh = Callable[[List[str], Optional[str]], subprocess.CompletedProcess]


def run_gh(args: List[str], body: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], input=body, capture_output=True, text=True)


def tag_patterns(repo: str) -> List[str]:
    """The tags that must never move: `v*` in a tool repo; the schema freezes in the hub.

    The hub's `v1` is deliberately not here (motyc, #72, 2026-10-20): it is the moving pointer the
    tool repositories' callers follow, not a source release.
    """
    if repo == HUB:
        return ["refs/tags/doc-schema-v*"]
    return ["refs/tags/v*"]


def tagger_patterns(repo: str) -> List[str]:
    """The tags only maintainers push: a tool's release tags; the hub's `v1` and schema freezes.

    A pushed `v*` tag starts a release, and an immutable release cannot be withdrawn.
    """
    if repo == HUB:
        return ["refs/tags/v1", "refs/tags/doc-schema-v*"]
    return ["refs/tags/v*"]


def ruleset(
    name: str, target: str, include: List[str], rules: List[Dict[str, Any]], bypass: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "name": name,
        "target": target,
        "enforcement": "active",
        "bypass_actors": bypass,
        "conditions": {"ref_name": {"include": include, "exclude": []}},
        "rules": rules,
    }


def tag_ruleset(repo: str) -> Dict[str, Any]:
    """A release tag (or a hub schema freeze) is never moved or deleted, by anyone."""
    return ruleset(TAG_RULESET, "tag", tag_patterns(repo), FIXED_REF_RULES, NO_BYPASS)


def tagger_ruleset(repo: str) -> Dict[str, Any]:
    """Only the maintainers create, move or delete these tags; rules in other rulesets still apply."""
    return ruleset(TAGGER_RULESET, "tag", tagger_patterns(repo), MAINTAINER_REF_RULES, MAINTAINER_BYPASS)


def history_ruleset() -> Dict[str, Any]:
    """Nobody deletes or force-pushes the default branch or `test`: pinned commits stay reachable."""
    return ruleset(HISTORY_RULESET, "branch", BRANCHES, [{"type": "deletion"}, {"type": "non_fast_forward"}], NO_BYPASS)


def branch_ruleset(checks: List[str]) -> Dict[str, Any]:
    """Everyone but the maintainers changes the two branches by a reviewed pull request."""
    rules: List[Dict[str, Any]] = [
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": REQUIRED_APPROVALS,
                "dismiss_stale_reviews_on_push": True,
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
    return ruleset(BRANCH_RULESET, "branch", BRANCHES, rules, MAINTAINER_BYPASS)


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


def upsert_ruleset(client: Client, repo: str, body: Dict[str, Any], aliases: tuple = ()) -> None:
    """Create the ruleset, or update the one with its name (or an alias, keeping that name)."""
    rulesets = client.get(f"repos/{OWNER}/{repo}/rulesets") or []
    names = (body["name"], *aliases)
    existing = next((r for r in rulesets if r.get("name") in names), None)
    if existing is None:
        client.send("POST", f"repos/{OWNER}/{repo}/rulesets", body)
    else:
        client.send("PUT", f"repos/{OWNER}/{repo}/rulesets/{existing['id']}", dict(body, name=existing["name"]))


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
                f"on {', '.join(refs) or '-'}: {rules or '-'}; bypass: {describe_bypass(detail)}",
                file=client.out,
            )


def describe_bypass(detail: Dict[str, Any]) -> str:
    """The bypass list as GitHub returns it, and whether the caller may bypass.

    GitHub returns `bypass_actors` only to someone who may edit the ruleset (an admin), so a
    maintainer reads "not shown" but still learns from `current_user_can_bypass` whether the
    bypass reaches them: `always` is what a maintainer must read on the maintainers' rulesets.
    """
    actors = detail.get("bypass_actors")
    if actors is None:
        listed = "not shown"
    elif not actors:
        listed = "nobody"
    else:
        listed = ", ".join(
            f"{actor.get('actor_type')} {actor.get('actor_id')} ({actor.get('bypass_mode')})" for actor in actors
        )
    return f"{listed}; you: {detail.get('current_user_can_bypass', '-')}"


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
                upsert_ruleset(client, repo, tag_ruleset(repo), TAG_RULESET_ALIASES)
                upsert_ruleset(client, repo, tagger_ruleset(repo))
        elif args.command == "branch-rules":
            required = [name.strip() for name in args.checks.split(",") if name.strip()]
            for repo in args.repo or list(ALL):
                upsert_ruleset(client, repo, history_ruleset())
                upsert_ruleset(client, repo, branch_ruleset(required))
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"release_trust: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
