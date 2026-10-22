"""lane_failure_issue.py -- one open issue per failing scheduled lane (atrium-project#81).

A scheduled lane that fails opens an issue; the next failure of the same lane comments on
that issue instead of opening another. The lane is found by a marker in the issue body,
``<!-- atrium:lane-failure:<repository>/<lane> -->``, not by its title, which carries a
date. Only scheduled runs report: a push, pull request or dispatch has someone watching it,
and a permitted skip never gets here, because the calling step runs on ``failure()``.

Called by ``action.yml`` next to it, with the run's environment (``GITHUB_*``) and:

  LANE          the lane inside the repository; default ``<workflow file>/<job>``. A matrix
                leg adds its value (``all-repos-smoke/ocr-postprocess``), so each leg has its
                own issue.
  TITLE         the issue title, without the date; default ``Scheduled lane failed: <lane>``
  BODY          what to look at first (markdown), written under the run link
  LABELS        comma-separated, the first one is the search filter; default ``ci``
  LEGACY_MARKER the marker an older step of the same lane used, so its open issue is reused
  GITHUB_TOKEN  a token with ``issues: write``

Stdlib only; the REST calls go through ``api`` so the tests can replace it.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Callable, Optional

Api = Callable[[str, str, Optional[dict]], object]


def marker(repository: str, lane: str) -> str:
    return f"<!-- atrium:lane-failure:{repository}/{lane} -->"


def default_lane(env: dict) -> str:
    """``<workflow file stem>/<job>``, from ``GITHUB_WORKFLOW_REF`` (owner/repo/.github/workflows/x.yml@ref)."""
    workflow_ref = env.get("GITHUB_WORKFLOW_REF", "")
    path = workflow_ref.split("@", 1)[0]
    stem = path.rsplit("/", 1)[-1].removesuffix(".yml").removesuffix(".yaml") or env.get("GITHUB_WORKFLOW", "workflow")
    return f"{stem}/{env.get('GITHUB_JOB', 'job')}"


def github_api(token: str, base: str = "https://api.github.com") -> Api:
    def call(method: str, path: str, body: Optional[dict] = None) -> object:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"{base}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Content-Type": "application/json"} if data else {}),
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read() or b"null")

    return call


def find_open_issue(api: Api, repository: str, label: str, markers: list) -> Optional[dict]:
    """The first open issue (not a pull request) labelled ``label`` whose body holds one of ``markers``."""
    page = 1
    while True:
        query = urllib.parse.urlencode({"state": "open", "labels": label, "per_page": 100, "page": page})
        issues = api("GET", f"/repos/{repository}/issues?{query}", None) or []
        for issue in issues:
            body = issue.get("body") or ""
            if "pull_request" not in issue and any(m in body for m in markers):
                return issue
        if len(issues) < 100:
            return None
        page += 1


def report(env: dict, api: Api, today: Optional[str] = None) -> str:
    """Open or update the lane's issue; returns what was done, for the log."""
    if env.get("GITHUB_EVENT_NAME") != "schedule":
        return f"not a scheduled run ({env.get('GITHUB_EVENT_NAME')}): no issue"
    repository = env["GITHUB_REPOSITORY"]
    lane = env.get("LANE") or default_lane(env)
    labels = [label.strip() for label in (env.get("LABELS") or "ci").split(",") if label.strip()]
    today = today or datetime.date.today().isoformat()
    run_url = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{repository}/actions/runs/{env['GITHUB_RUN_ID']}"
    own = marker(repository, lane)
    markers = [own] + ([env["LEGACY_MARKER"]] if env.get("LEGACY_MARKER") else [])

    issue = find_open_issue(api, repository, labels[0], markers)
    if issue is not None:
        api(
            "POST",
            f"/repos/{repository}/issues/{issue['number']}/comments",
            {"body": f"Still failing on {today}: {run_url}"},
        )
        return f"commented on #{issue['number']}"

    title = env.get("TITLE") or f"Scheduled lane failed: {lane}"
    body = "\n".join(
        [
            own,
            f"The scheduled lane `{lane}` failed on {today}: {run_url}",
            "",
            *([env["BODY"].strip(), ""] if env.get("BODY", "").strip() else []),
            "Each later failure of this lane comments here while this issue is open. "
            "Close it when the lane is green again; the next failure then opens a new one.",
        ]
    )
    created = api(
        "POST", f"/repos/{repository}/issues", {"title": f"{title} ({today})", "body": body, "labels": labels}
    )
    return f"opened #{created['number']}"


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("::error::lane-failure-issue: no GITHUB_TOKEN", file=sys.stderr)
        return 1
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    print(f"lane-failure-issue: {report(dict(os.environ), github_api(token, api_url))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
