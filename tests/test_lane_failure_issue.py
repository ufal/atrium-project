"""Tests for .github/actions/lane-failure-issue -- one issue per failing scheduled lane (#81).

The REST layer is a fake that keeps issues and comments in memory, so nothing reaches GitHub.
"""

from __future__ import annotations

import sys
import urllib.parse
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / ".github" / "actions" / "lane-failure-issue"))

import lane_failure_issue as lfi  # noqa: E402

REPO = "ufal/atrium-translator"


class FakeGitHub:
    def __init__(self, issues=None):
        self.issues = list(issues or [])
        self.comments = []
        self.created = []

    def __call__(self, method, path, body):
        if method == "GET":
            query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
            label, page = query["labels"][0], int(query["page"][0])
            matching = [i for i in self.issues if label in i.get("labels", [])]
            return matching[(page - 1) * 100 : page * 100]
        if path.endswith("/comments"):
            number = int(path.split("/")[-2])
            self.comments.append((number, body["body"]))
            return {"id": len(self.comments)}
        issue = {"number": 100 + len(self.created), **body}
        self.created.append(issue)
        return issue


def env(**extra):
    return {
        "GITHUB_EVENT_NAME": "schedule",
        "GITHUB_REPOSITORY": REPO,
        "GITHUB_RUN_ID": "42",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_WORKFLOW_REF": f"{REPO}/.github/workflows/lindat-daily.yml@refs/heads/test",
        "GITHUB_JOB": "lindat",
        **extra,
    }


def test_the_first_failure_opens_one_issue_with_the_lane_marker():
    gh = FakeGitHub()
    assert lfi.report(env(BODY="Look at the probe table."), gh, today="2026-10-22") == "opened #100"
    issue = gh.created[0]
    assert issue["title"] == "Scheduled lane failed: lindat-daily/lindat (2026-10-22)"
    assert issue["labels"] == ["ci"]
    assert issue["body"].startswith(f"<!-- atrium:lane-failure:{REPO}/lindat-daily/lindat -->")
    assert "https://github.com/ufal/atrium-translator/actions/runs/42" in issue["body"]
    assert "Look at the probe table." in issue["body"]


def test_a_later_failure_comments_on_the_open_issue_instead_of_opening_another():
    open_issue = {"number": 7, "labels": ["ci"], "body": lfi.marker(REPO, "lindat-daily/lindat") + "\nfailed"}
    gh = FakeGitHub([open_issue])
    assert lfi.report(env(), gh, today="2026-10-23") == "commented on #7"
    assert gh.created == []
    assert gh.comments == [
        (7, "Still failing on 2026-10-23: https://github.com/ufal/atrium-translator/actions/runs/42")
    ]


def test_another_lane_and_a_pull_request_with_the_marker_are_not_reused():
    other = {"number": 8, "labels": ["ci"], "body": lfi.marker(REPO, "scheduled-smoke/smoke")}
    pr = {"number": 9, "labels": ["ci"], "pull_request": {}, "body": lfi.marker(REPO, "lindat-daily/lindat")}
    gh = FakeGitHub([other, pr])
    assert lfi.report(env(), gh) == "opened #100"


def test_each_matrix_leg_is_its_own_lane():
    leg = {"number": 5, "labels": ["ci"], "body": lfi.marker(REPO, "all-repos-smoke/ocr-postprocess")}
    gh = FakeGitHub([leg])
    assert lfi.report(env(LANE="all-repos-smoke/nlp-enrich"), gh) == "opened #100"
    assert lfi.report(env(LANE="all-repos-smoke/ocr-postprocess"), gh) == "commented on #5"


def test_a_legacy_marker_keeps_the_open_issue_of_the_earlier_step():
    legacy = "<!-- atrium:e2e-digital-smoke-failure -->"
    gh = FakeGitHub([{"number": 3, "labels": ["ci", "pipeline"], "body": legacy}])
    result = lfi.report(env(LANE="e2e-digital-smoke", LABELS="ci,pipeline", LEGACY_MARKER=legacy), gh)
    assert result == "commented on #3"


def test_the_search_pages_through_more_than_one_hundred_open_issues():
    filler = [{"number": n, "labels": ["ci"], "body": "unrelated"} for n in range(100)]
    target = {"number": 500, "labels": ["ci"], "body": lfi.marker(REPO, "lindat-daily/lindat")}
    gh = FakeGitHub(filler + [target])
    assert lfi.report(env(), gh) == "commented on #500"


@pytest.mark.parametrize("event", ["push", "pull_request", "workflow_dispatch"])
def test_only_a_scheduled_run_reports(event):
    gh = FakeGitHub()
    assert lfi.report(env(GITHUB_EVENT_NAME=event), gh).startswith("not a scheduled run")
    assert gh.created == [] and gh.comments == []


def test_the_default_lane_is_the_workflow_file_and_the_job():
    assert lfi.default_lane(env()) == "lindat-daily/lindat"
    assert lfi.default_lane({"GITHUB_WORKFLOW": "Smoke", "GITHUB_JOB": "run"}) == "Smoke/run"


def test_main_refuses_to_run_without_a_token(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert lfi.main() == 1
    assert "no GITHUB_TOKEN" in capsys.readouterr().err
