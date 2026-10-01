"""Tests for scripts/release_trust.py — the repository settings behind #72's release trust.

The script only calls the GitHub CLI; here `gh` is a recorder, so what is tested is exactly what
would be sent: the API paths, the ruleset bodies, idempotence by ruleset name, and that
`--dry-run` sends nothing that changes a repository.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "scripts"))

import release_trust as rt  # noqa: E402


class FakeGh:
    """Answers GETs from `responses` (path -> JSON, or None for a 404) and records every call."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def __call__(self, args, body=None):
        self.calls.append((args, json.loads(body) if body else None))
        if args[:2] == ["api", "--method"]:
            return subprocess.CompletedProcess(args, 0, "{}", "")
        answer = self.responses.get(args[1], [])
        if answer is None:
            return subprocess.CompletedProcess(args, 1, "", "gh: Not Found (HTTP 404)")
        return subprocess.CompletedProcess(args, 0, json.dumps(answer), "")

    def writes(self):
        return [(args[2], args[3], body) for args, body in self.calls if args[:2] == ["api", "--method"]]


def run(argv, gh):
    out = io.StringIO()
    return rt.main(argv, gh=gh, out=out), out.getvalue()


def test_immutable_releases_go_on_in_the_six_tool_repositories_only():
    gh = FakeGh()
    assert run(["immutable"], gh)[0] == 0
    assert [(m, p) for m, p, _ in gh.writes()] == [
        ("PUT", f"repos/ufal/{repo}/immutable-releases") for repo in rt.TOOLS
    ]


def test_release_tags_are_protected_from_update_and_deletion_but_not_creation():
    gh = FakeGh()
    run(["tag-rules", "--repo", "atrium-translator", "--repo", "atrium-project"], gh)
    (_, tool_path, tool), (_, hub_path, hub) = gh.writes()
    assert tool_path == "repos/ufal/atrium-translator/rulesets"
    assert tool["target"] == "tag" and tool["conditions"]["ref_name"]["include"] == ["refs/tags/v*"]
    assert {rule["type"] for rule in tool["rules"]} == {"update", "deletion"}
    assert hub["conditions"]["ref_name"]["include"] == ["refs/tags/v1", "refs/tags/doc-schema-v*"]
    assert tool["bypass_actors"] == [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]


def test_a_ruleset_is_updated_in_place_when_its_name_exists():
    gh = FakeGh({"repos/ufal/atrium-translator/rulesets": [{"id": 42, "name": rt.TAG_RULESET}]})
    run(["tag-rules", "--repo", "atrium-translator"], gh)
    assert [(m, p) for m, p, _ in gh.writes()] == [("PUT", "repos/ufal/atrium-translator/rulesets/42")]


def test_branch_rules_require_pull_requests_and_the_named_checks():
    gh = FakeGh()
    run(["branch-rules", "--repo", "atrium-translator", "--checks", "a / b, c"], gh)
    ((_, _, body),) = gh.writes()
    assert body["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH", "refs/heads/test"]
    by_type = {rule["type"]: rule for rule in body["rules"]}
    assert {"deletion", "non_fast_forward", "pull_request", "required_status_checks"} == set(by_type)
    contexts = by_type["required_status_checks"]["parameters"]["required_status_checks"]
    assert contexts == [{"context": "a / b"}, {"context": "c"}]


def test_branch_rules_without_checks_require_none():
    gh = FakeGh()
    run(["branch-rules", "--repo", "atrium-translator"], gh)
    ((_, _, body),) = gh.writes()
    assert "required_status_checks" not in {rule["type"] for rule in body["rules"]}


def test_dry_run_prints_and_writes_nothing():
    gh = FakeGh()
    code, out = run(["immutable", "--dry-run", "--repo", "atrium-translator"], gh)
    assert code == 0 and gh.writes() == []
    assert "[dry-run] PUT repos/ufal/atrium-translator/immutable-releases" in out


def test_status_reads_immutability_and_rulesets():
    gh = FakeGh(
        {
            "repos/ufal/atrium-translator/immutable-releases": {"enabled": True, "enforced_by_owner": False},
            "repos/ufal/atrium-translator/rulesets": [{"id": 7, "name": rt.TAG_RULESET}],
            "repos/ufal/atrium-translator/rulesets/7": rt.tag_ruleset("atrium-translator"),
            "repos/ufal/atrium-project/immutable-releases": None,
        }
    )
    code, out = run(["status", "--repo", "atrium-translator", "--repo", "atrium-project"], gh)
    assert code == 0 and gh.writes() == []
    assert "ufal/atrium-translator: immutable releases on" in out
    assert "[tag, active] on refs/tags/v*: update, deletion" in out
    assert "ufal/atrium-project: immutable releases off" in out


def test_a_failing_call_is_exit_1():
    def broken(args, body=None):
        return subprocess.CompletedProcess(args, 1, "", "HTTP 403: Must have admin rights")

    assert run(["tag-rules", "--repo", "atrium-translator"], broken)[0] == 1


@pytest.mark.parametrize("repo", ["atrium-someone-else"])
def test_only_the_six_repositories_are_accepted(repo):
    with pytest.raises(SystemExit):
        rt.main(["status", "--repo", repo], gh=FakeGh(), out=io.StringIO())
