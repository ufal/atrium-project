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


MAINTAINERS = [
    {"actor_id": rt.MAINTAIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": "always"},
    {"actor_id": rt.ADMIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": "always"},
]


def test_release_tags_are_fixed_for_everyone_and_pushed_only_by_maintainers():
    gh = FakeGh()
    run(["tag-rules", "--repo", "atrium-translator", "--repo", "atrium-project"], gh)
    writes = gh.writes()
    assert [(m, p) for m, p, _ in writes] == [
        ("POST", "repos/ufal/atrium-translator/rulesets"),
        ("POST", "repos/ufal/atrium-translator/rulesets"),
        ("POST", "repos/ufal/atrium-project/rulesets"),
        ("POST", "repos/ufal/atrium-project/rulesets"),
    ]
    (_, _, fixed), (_, _, taggers), (_, _, hub_fixed), (_, _, hub_taggers) = writes
    # Nobody, an admin included, moves or deletes a release tag (as the hand-made rulesets of 2026-10).
    assert fixed["target"] == "tag" and fixed["conditions"]["ref_name"]["include"] == ["refs/tags/v*"]
    assert {rule["type"] for rule in fixed["rules"]} == {"update", "deletion", "non_fast_forward"}
    assert fixed["bypass_actors"] == []
    # Only the maintainers push one: a pushed `v*` tag starts a release that cannot be withdrawn.
    assert taggers["conditions"]["ref_name"]["include"] == ["refs/tags/v*"]
    assert "creation" in {rule["type"] for rule in taggers["rules"]}
    assert taggers["bypass_actors"] == MAINTAINERS
    # The hub's `v1` moves with every hub change (#72, 10-20): maintainers only, never fixed.
    assert hub_fixed["conditions"]["ref_name"]["include"] == ["refs/tags/doc-schema-v*"]
    assert hub_taggers["conditions"]["ref_name"]["include"] == ["refs/tags/v1", "refs/tags/doc-schema-v*"]


def test_the_maintainers_are_the_maintain_and_admin_roles():
    # The releases are pushed by someone with Maintain in four of the seven repositories, and a
    # bypass list cannot name a single user, so an Admin-only bypass would block them there.
    assert {actor["actor_id"] for actor in rt.MAINTAINER_BYPASS} == {rt.MAINTAIN_ROLE_ID, rt.ADMIN_ROLE_ID}
    assert rt.MAINTAIN_ROLE_ID != rt.ADMIN_ROLE_ID


def test_a_ruleset_is_updated_in_place_when_its_name_exists():
    gh = FakeGh({"repos/ufal/atrium-translator/rulesets": [{"id": 42, "name": rt.TAG_RULESET}]})
    run(["tag-rules", "--repo", "atrium-translator"], gh)
    assert [(m, p) for m, p, _ in gh.writes()] == [
        ("PUT", "repos/ufal/atrium-translator/rulesets/42"),
        ("POST", "repos/ufal/atrium-translator/rulesets"),
    ]


def test_a_hand_made_tag_ruleset_is_updated_in_place_under_its_own_name_and_not_weakened():
    gh = FakeGh({"repos/ufal/atrium-nlp-enrich/rulesets": [{"id": 9, "name": "Protect v* Tags"}]})
    run(["tag-rules", "--repo", "atrium-nlp-enrich"], gh)
    (method, path, body), (_, _, taggers) = gh.writes()
    assert (method, path) == ("PUT", "repos/ufal/atrium-nlp-enrich/rulesets/9")
    assert body["name"] == "Protect v* Tags"
    # The live rulesets refuse update, deletion and non-fast-forward with no bypass; so does the PUT.
    assert {rule["type"] for rule in body["rules"]} == {"update", "deletion", "non_fast_forward"}
    assert body["bypass_actors"] == []
    assert taggers["name"] == rt.TAGGER_RULESET


def test_branch_history_is_fixed_for_everyone():
    gh = FakeGh()
    run(["branch-rules", "--repo", "atrium-translator"], gh)
    (_, _, history), _ = gh.writes()
    assert history["name"] == rt.HISTORY_RULESET
    assert history["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH", "refs/heads/test"]
    assert {rule["type"] for rule in history["rules"]} == {"deletion", "non_fast_forward"}
    assert history["bypass_actors"] == []


def test_branch_changes_need_a_reviewed_pull_request_and_the_named_checks_except_for_maintainers():
    gh = FakeGh()
    run(["branch-rules", "--repo", "atrium-translator", "--checks", "a / b, c"], gh)
    _, (_, _, body) = gh.writes()
    assert body["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH", "refs/heads/test"]
    by_type = {rule["type"]: rule for rule in body["rules"]}
    assert {"pull_request", "required_status_checks"} == set(by_type)
    assert by_type["pull_request"]["parameters"]["required_approving_review_count"] == 1
    contexts = by_type["required_status_checks"]["parameters"]["required_status_checks"]
    assert contexts == [{"context": "a / b"}, {"context": "c"}]
    assert body["bypass_actors"] == MAINTAINERS


def test_branch_rules_without_checks_require_none():
    gh = FakeGh()
    run(["branch-rules", "--repo", "atrium-translator"], gh)
    _, (_, _, body) = gh.writes()
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
    assert "[tag, active] on refs/tags/v*: update, deletion, non_fast_forward; bypass: nobody; you: -" in out
    assert "ufal/atrium-project: immutable releases off" in out


def test_status_names_a_hidden_bypass_list_and_the_callers_own_bypass():
    hidden = dict(rt.tagger_ruleset("atrium-translator"), bypass_actors=None, current_user_can_bypass="always")
    assert rt.describe_bypass(hidden) == "not shown; you: always"
    listed = rt.describe_bypass(rt.tagger_ruleset("atrium-translator"))
    assert listed.startswith(f"RepositoryRole {rt.MAINTAIN_ROLE_ID} (always), RepositoryRole {rt.ADMIN_ROLE_ID}")


def test_a_failing_call_is_exit_1():
    def broken(args, body=None):
        return subprocess.CompletedProcess(args, 1, "", "HTTP 403: Must have admin rights")

    assert run(["tag-rules", "--repo", "atrium-translator"], broken)[0] == 1


@pytest.mark.parametrize("repo", ["atrium-someone-else"])
def test_only_the_six_repositories_are_accepted(repo):
    with pytest.raises(SystemExit):
        rt.main(["status", "--repo", repo], gh=FakeGh(), out=io.StringIO())
