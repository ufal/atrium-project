"""Tests for tools/ci/workflow_lint.py — the linter that gates every caller in the
ecosystem and, until now, had none.

Why this file exists (issue #18 / #10, W5): `workflow_lint.py` is ~400 lines gating
38 caller jobs across six repos, and it shipped a crash. `permissions: read-all` is a
legal GitHub shorthand; the merge `{**doc_perms, **job_perms}` assumed both were
mappings and raised `TypeError: 'str' object is not a mapping`, so the linter died
instead of reporting — taking every later check down with it. A linter that fails
open is worse than no linter, because the green tick is read as "checked".

Two properties every test here is built around:

  1. Each rule FAILS a purpose-built broken fixture. A rule that never fires on
     anything is indistinguishable from a rule that is not wired up — the exact
     failure mode `test_check_version.py` was written to avoid.
  2. Breaking ONE rule does not mask the others. `main()` accumulates findings
     rather than returning at the first error, and `test_one_break_does_not_mask_others`
     pins that, because the ordering of checks is an implementation detail nobody
     should have to know to trust the output.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools" / "ci"))

import workflow_lint as wl  # noqa: E402

# ── helpers ──────────────────────────────────────────────────────────────────


def write_workflow(root: Path, name: str, body: str) -> Path:
    d = root / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def write_template(root: Path, name: str, body: str) -> Path:
    d = root / "docs" / "templates" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def run_lint(root: Path, *extra: str) -> tuple[int, str]:
    """Run the linter against `root`, resolving callees from the real hub.

    `--repo-name` is always passed, so a fixture never depends on whatever
    GITHUB_REPOSITORY the machine running the tests happens to export.
    """
    buf = io.StringIO()
    args = ["--repo-root", str(root), "--hub-root", str(_HUB_ROOT), "--offline"]
    if "--repo-name" not in extra:
        args += ["--repo-name", "ufal/atrium-example"]
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = wl.main(args + list(extra))
    return rc, buf.getvalue()


def write_compose(root: Path, name: str, body: str) -> Path:
    p = root / name
    p.write_text(body, encoding="utf-8")
    return p


def write_gitkeep(root: Path, directory: str = "data") -> None:
    d = root / directory
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitkeep").write_text("", encoding="utf-8")


#: A caller with nothing wrong with it — the baseline every test perturbs.
CLEAN_CALLER = """\
name: Clean
on: push
concurrency:
  group: clean-${{ github.ref }}
permissions:
  contents: read
jobs:
  drift:
    uses: ufal/atrium-project/.github/workflows/para-drift.reusable.yml@v1
"""


def test_clean_caller_passes(tmp_path):
    """The baseline must pass, or every negative test below proves nothing."""
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── the crash that motivated this file ───────────────────────────────────────


@pytest.mark.parametrize("shorthand", ["read-all", "write-all"])
def test_permissions_shorthand_does_not_crash(tmp_path, shorthand):
    """`permissions: <string>` is legal YAML for GitHub and must not raise.

    Regression test for `TypeError: 'str' object is not a mapping`.
    """
    write_workflow(
        tmp_path, "x.yml", CLEAN_CALLER.replace("permissions:\n  contents: read", f"permissions: {shorthand}")
    )
    rc, out = run_lint(tmp_path)  # must not raise
    assert rc == 0, out


def test_read_all_does_not_satisfy_a_write_scope(tmp_path):
    """`read-all` grants read everywhere and write nowhere.

    Silently treating it as sufficient for `packages: write` would reintroduce the
    startup_failure class the permission check exists to prevent.
    """
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x
permissions: read-all
jobs:
  build:
    uses: ufal/atrium-project/.github/workflows/docker-tool.reusable.yml@v1
    with:
      image-name: ufal/example
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "packages" in out


def test_write_all_satisfies_every_scope(tmp_path):
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x
permissions: write-all
jobs:
  build:
    uses: ufal/atrium-project/.github/workflows/docker-tool.reusable.yml@v1
    with:
      image-name: ufal/example
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── W5's new rules, one broken fixture each ──────────────────────────────────


def test_caller_example_without_uses_is_rejected(tmp_path):
    """W1's clobber signature: a `*.caller.example.yml` that calls nothing.

    `docker.caller.example.yml` was overwritten by a dependabot config and no check
    noticed, because `check_duplicate_names` skips files with no `name:` key.
    """
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    write_template(tmp_path, "thing.caller.example.yml", "version: 2\nupdates: []\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "no `uses:`" in out


def test_caller_example_with_uses_is_accepted(tmp_path):
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    write_template(tmp_path, "thing.caller.example.yml", CLEAN_CALLER)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


@pytest.mark.parametrize("ref", ["test", "main", "v2-beta"])
def test_non_v1_hub_ref_is_rejected(tmp_path, ref):
    """A branch pin makes hub changes reach a repo without anyone adopting them."""
    write_workflow(tmp_path, "x.yml", CLEAN_CALLER.replace("@v1", f"@{ref}"))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert f"@{ref}" in out


# ── commit pins (atrium-project#40 F, #72 E.2) ──────────────────────────────

_SHA = "0123456789abcdef0123456789abcdef01234567"
_PINNED = CLEAN_CALLER.replace("para-drift.reusable.yml@v1", f"para-drift.reusable.yml@{_SHA}  # v1")


def test_a_commit_pin_with_its_channel_and_matching_hub_ref_passes(tmp_path):
    write_workflow(tmp_path, "x.yml", _PINNED + f"    with:\n      hub-ref: {_SHA}\n")
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_a_commit_pin_whose_callee_takes_no_hub_ref_needs_only_the_comment(tmp_path):
    caller = CLEAN_CALLER.replace("para-drift.reusable.yml@v1", f"codeql.reusable.yml@{_SHA}  # v1")
    write_workflow(
        tmp_path, "x.yml", caller.replace("contents: read", "contents: read\n  security-events: write\n  actions: read")
    )
    rc, out = run_lint(tmp_path)
    assert "hub-ref" not in out and "comment" not in out, out


def test_a_commit_pin_without_hub_ref_reads_the_files_at_the_moving_tag(tmp_path):
    write_workflow(tmp_path, "x.yml", _PINNED)
    rc, out = run_lint(tmp_path)
    assert rc == 1 and f"pass `hub-ref: {_SHA}`" in out


def test_a_commit_pin_with_another_hub_ref_is_rejected(tmp_path):
    write_workflow(tmp_path, "x.yml", _PINNED + "    with:\n      hub-ref: " + "f" * 40 + "\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1 and "reads the hub at hub-ref" in out


@pytest.mark.parametrize("comment", ["", "  # v2", "  # main"])
def test_a_commit_pin_must_name_its_channel(tmp_path, comment):
    caller = CLEAN_CALLER.replace("para-drift.reusable.yml@v1", f"para-drift.reusable.yml@{_SHA}{comment}")
    write_workflow(tmp_path, "x.yml", caller + f"    with:\n      hub-ref: {_SHA}\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1 and "without a '# v1' comment" in out


def test_v1_with_another_hub_ref_is_rejected(tmp_path):
    write_workflow(tmp_path, "x.yml", CLEAN_CALLER + "    with:\n      hub-ref: test\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1 and "hub-ref 'test'" in out


def test_require_sha_pins_refuses_v1(tmp_path):
    write_workflow(tmp_path, "x.yml", CLEAN_CALLER)
    assert run_lint(tmp_path)[0] == 0
    rc, out = run_lint(tmp_path, "--require-sha-pins")
    assert rc == 1 and "pin it to a commit of v1" in out


# ── release assets and immutable releases (atrium-project#40 E, #72) ─────────

_RELEASE = """\
name: Release
on:
  push:
    tags: ['v*']
concurrency:
  group: release-${{ github.ref }}
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: softprops/action-gh-release@efb35369e0ad2afab669f228072c1b0d510eae64  # v3.0.3
        with:
          files: dist/openapi.json
%s"""


@pytest.mark.parametrize(
    "extra, ok",
    [
        ("", True),
        ("          prerelease: true\n          draft: true\n", True),
        ("          prerelease: true\n", False),
    ],
    ids=["draft-first-by-default", "prerelease-as-draft", "prerelease-published-first"],
)
def test_a_prerelease_must_be_created_as_a_draft(tmp_path, extra, ok):
    write_workflow(tmp_path, "release.yml", _RELEASE % extra)
    rc, out = run_lint(tmp_path)
    assert (rc == 0) is ok, out
    assert ok or "publishes a prerelease before uploading its assets" in out


def test_an_asset_uploaded_after_the_release_is_rejected(tmp_path):
    later = '      - run: gh release upload "$GITHUB_REF_NAME" dist/bundle.zip\n'
    write_workflow(tmp_path, "release.yml", _RELEASE % "" + later)
    rc, out = run_lint(tmp_path)
    assert rc == 1 and "uploads a release asset after the release exists" in out


def test_missing_timeout_minutes_is_rejected(tmp_path):
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "timeout-minutes" in out


def test_missing_concurrency_is_rejected(tmp_path):
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "concurrency" in out


# ── a scheduled run a push can cancel (issue atrium-project#10) ──────────────
#
# The presence check above passed on all-repos-smoke.yml the whole time it was
# cancelling its own nightly: the block was there, its VALUE was wrong. Run #32 died
# eleven seconds before a push run started, and a cancelled run reports no failure --
# so the nightly stopped producing a signal without ever going red.

_SCHEDULED = """\
name: Nightly
on:
  push:
    branches: [test]
  schedule:
    - cron: "0 3 * * *"
concurrency:
  group: %s
  cancel-in-progress: %s
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
"""


def test_scheduled_workflow_cancelled_by_a_push_is_rejected(tmp_path):
    """A ref-keyed group plus cancel-in-progress means the push wins and the cron loses."""
    write_workflow(tmp_path, "x.yml", _SCHEDULED % ("nightly-${{ github.ref }}", "true"))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "cancel the scheduled run" in out


def test_scheduled_workflow_may_cancel_when_the_group_scopes_the_event(tmp_path):
    """Remedy 1 — event-scoping. Push de-duplication is worth keeping on a busy branch;
    it just must not reach across events into the scheduled run."""
    write_workflow(
        tmp_path,
        "x.yml",
        _SCHEDULED % ("nightly-${{ github.event_name }}-${{ github.ref }}", "true"),
    )
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_scheduled_workflow_may_decline_to_cancel(tmp_path):
    """Remedy 2 — right for heavy, infrequent jobs whose runs are never redundant."""
    write_workflow(tmp_path, "x.yml", _SCHEDULED % ("nightly-${{ github.ref }}", "false"))
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_a_cancel_expression_is_not_treated_as_false(tmp_path):
    """`${{ !startsWith(github.ref, 'refs/tags/') }}` is how security.yml spells "never
    cancel a tag build". It is true for every other ref -- scheduled runs included -- so
    reading it as a safe default is exactly the misreading this check exists to stop."""
    write_workflow(
        tmp_path,
        "x.yml",
        _SCHEDULED % ("nightly-${{ github.ref }}", "${{ !startsWith(github.ref, 'refs/tags/') }}"),
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "cancel the scheduled run" in out


def test_unscheduled_workflow_may_cancel_freely(tmp_path):
    """The rule is about scheduled runs only: a push/PR workflow SHOULD cancel supersedes."""
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_reusable_workflow_is_exempt_from_concurrency(tmp_path):
    """A callee must NOT set a concurrency group: the caller owns it, and one here
    would collapse five repos' builds into a single queue."""
    write_workflow(
        tmp_path,
        "r.reusable.yml",
        """\
name: R
on:
  workflow_call:
permissions:
  contents: read
jobs:
  work:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_missing_permissions_is_rejected(tmp_path):
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo hi
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "permissions" in out


def test_missing_required_input_is_rejected(tmp_path):
    """`skill-validate.reusable.yml` declares `client-script: required: true`."""
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
concurrency:
  group: x
permissions:
  contents: read
jobs:
  skill:
    uses: ufal/atrium-project/.github/workflows/skill-validate.reusable.yml@v1
""",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "client-script" in out


# ── #69 round 5: the action-version floor ────────────────────────────────────

_FLOOR = """\
name: Floor
on: push
concurrency:
  group: floor
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: %s
"""


@pytest.mark.parametrize(
    "uses",
    ["actions/checkout@v4", "actions/setup-python@v5", "actions/github-script@v7", "github/codeql-action/init@v3"],
)
def test_action_below_the_floor_is_rejected(tmp_path, uses):
    """The two templates the floor paragraph named sat below it for weeks: nothing enforced it."""
    write_workflow(tmp_path, "x.yml", _FLOOR % uses)
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "below the ecosystem floor" in out
    assert uses.rsplit("@", 1)[0] in out


@pytest.mark.parametrize("uses", ["actions/checkout@v7", "actions/checkout@v7.0.1", "github/codeql-action/analyze@v4"])
def test_action_at_the_floor_passes(tmp_path, uses):
    write_workflow(tmp_path, "x.yml", _FLOOR % uses)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


def test_floor_ignores_prose_and_unlisted_actions(tmp_path):
    """Parsed, not grepped: a comment quoting the old pin is history, not a finding; an
    action the floor does not list is not the floor's to judge."""
    body = _FLOOR % "some-org/some-action@v1"
    body = body.replace("jobs:", "# this used to be `uses: actions/checkout@v4`\\njobs:")
    write_workflow(tmp_path, "x.yml", body)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── #69 round 5: a permissions block on every job when the workflow has none ─

_TWO_JOBS = """\
name: Two
on: push
concurrency:
  group: two
jobs:
  scoped:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - run: echo hi
  bare:
%s
"""


def test_one_unscoped_job_beside_a_scoped_one_is_rejected(tmp_path):
    """E6's shape: the old rule passed as soon as ANY job had a block."""
    write_workflow(
        tmp_path,
        "x.yml",
        _TWO_JOBS % "    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n      - run: echo hi",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "job 'bare' has no `permissions:`" in out
    assert "job 'scoped'" not in out


def test_an_unscoped_caller_job_is_rejected_too(tmp_path):
    """A caller job without a grant starts its callee from the repository default."""
    write_workflow(
        tmp_path, "x.yml", _TWO_JOBS % "    uses: ufal/atrium-project/.github/workflows/para-drift.reusable.yml@v1"
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "job 'bare' has no `permissions:`" in out


def test_every_job_scoped_passes_without_a_workflow_block(tmp_path):
    body = _TWO_JOBS % (
        "    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    permissions: {}\n    steps:\n      - run: echo hi"
    )
    write_workflow(tmp_path, "x.yml", body)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── #69 round 5: compose files (B2, B3's compose half, B6) ───────────────────

#: A docker caller that publishes `ghcr.io/ufal/atrium-example` (base) and `-api`.
DOCKER_CALLER = """\
name: Docker
on: push
concurrency:
  group: docker
permissions:
  contents: read
  packages: write
  security-events: write
jobs:
  build-and-push:
    uses: ufal/atrium-project/.github/workflows/docker-tool.reusable.yml@v1
    with:
      image-name: ${{ github.repository }}
      build-targets: '["base", "api"]'
"""

_COMPOSE_CLEAN = """\
services:
  tool:
    image: ghcr.io/ufal/atrium-example:${ATRIUM_VERSION:-dev}
    user: "${ATRIUM_UID:-10001}:0"
    build:
      context: .
      args:
        ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example:${ATRIUM_VERSION:-dev}
    environment:
      ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example:${ATRIUM_VERSION:-dev}
    volumes:
      - ./data:/data
      - cache:/cache
  api:
    extends: tool
    image: ghcr.io/ufal/atrium-example-api:${ATRIUM_VERSION:-dev}
    build:
      context: .
      target: api
      args:
        ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example-api:${ATRIUM_VERSION:-dev}
    environment:
      ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example-api:${ATRIUM_VERSION:-dev}
  local:
    image: atrium-example-heavy:local
    pull_policy: build
    build:
      context: .
      target: heavy
volumes:
  cache:
"""

#: The B2 defect, verbatim in shape from four tool repos on 2026-09-29.
_COMPOSE_B2_FORM = """\
services:
  api:
    image: ghcr.io/ufal/atrium-example:${ATRIUM_VERSION:-dev}-api
    build:
      context: .
      target: api
    volumes:
      - ./data:/data
"""


def _compose_repo(tmp_path, compose=_COMPOSE_CLEAN, gitkeep=True):
    write_workflow(tmp_path, "docker.yml", DOCKER_CALLER)
    write_compose(tmp_path, "docker-compose.yml", compose)
    if gitkeep:
        write_gitkeep(tmp_path)


def test_clean_compose_passes(tmp_path):
    """The baseline every compose test perturbs; `extends:` and a local build included."""
    _compose_repo(tmp_path)
    rc, out = run_lint(tmp_path)
    assert rc == 0, out
    assert "1 compose files: 2 GHCR images" in out


def test_b2_tag_suffix_is_rejected(tmp_path):
    """`atrium-<tool>:<ver>-api` asks for a tag CI never publishes (B2)."""
    _compose_repo(
        tmp_path,
        _COMPOSE_CLEAN.replace(
            "atrium-example-api:${ATRIUM_VERSION:-dev}", "atrium-example:${ATRIUM_VERSION:-dev}-api"
        ),
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "the tag must be exactly" in out


def test_b2_is_caught_without_a_docker_caller(tmp_path):
    """Form-only mode: with no docker.yml to read names from, the tag rule still holds."""
    write_workflow(tmp_path, "clean.yml", CLEAN_CALLER)
    write_compose(tmp_path, "docker-compose.yml", _COMPOSE_B2_FORM.replace("    volumes:\n      - ./data:/data\n", ""))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "the tag must be exactly" in out


def test_unpublished_target_is_rejected(tmp_path):
    """`-llm` is not in build-targets, so GHCR has no such image."""
    _compose_repo(tmp_path, _COMPOSE_CLEAN.replace("atrium-example-api:", "atrium-example-llm:"))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "does not publish" in out
    assert "ghcr.io/ufal/atrium-example-api" in out  # names what IS published


def test_repository_expression_resolves_from_the_repo_name(tmp_path):
    """`${{ github.repository }}` is the caller's repo; another name is not published."""
    _compose_repo(tmp_path)
    rc, out = run_lint(tmp_path, "--repo-name", "ufal/atrium-other")
    assert rc == 1
    assert "ghcr.io/ufal/atrium-other" in out


def test_runner_image_mismatch_is_rejected(tmp_path):
    """Paradata must name the image the service runs (B3's compose half)."""
    _compose_repo(
        tmp_path,
        _COMPOSE_CLEAN.replace(
            "      ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example-api:${ATRIUM_VERSION:-dev}\n",
            "      ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example:${ATRIUM_VERSION:-dev}\n",
        ),
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "environment ATRIUM_RUNNER_IMAGE" in out


def test_build_arg_inherited_through_extends_is_checked(tmp_path):
    """alto-postprocess's `api` shape: `extends:` merges `build:`, so without its own
    build arg the api image bakes the batch image's name."""
    compose = _COMPOSE_CLEAN.replace(
        "      target: api\n      args:\n        ATRIUM_RUNNER_IMAGE: ghcr.io/ufal/atrium-example-api:${ATRIUM_VERSION:-dev}\n",
        "      target: api\n",
    )
    _compose_repo(tmp_path, compose)
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "service 'api'" in out
    assert "build arg ATRIUM_RUNNER_IMAGE is ghcr.io/ufal/atrium-example:" in out


def test_overlay_is_checked_merged_onto_its_base(tmp_path):
    """alto-postprocess's GPU overlay: a new image name, but the base's
    ATRIUM_RUNNER_IMAGE survives the merge -- the CPU image in paradata."""
    _compose_repo(tmp_path)
    write_compose(
        tmp_path,
        "docker-compose.gpu.yml",
        "services:\n  tool:\n    image: atrium-example-gpu:local\n    pull_policy: build\n",
    )
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "docker-compose.gpu.yml (merged onto docker-compose.yml)" in out
    assert "runs atrium-example-gpu:local but its build arg" in out


def test_overlay_does_not_repeat_its_base_file_defects(tmp_path):
    """Fixing the base file is one fix: an overlay reports only what it adds."""
    _compose_repo(tmp_path, gitkeep=False)
    write_compose(tmp_path, "docker-compose.gpu.yml", "services:\n  tool:\n    environment:\n      X: y\n")
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "does not contain" in out
    assert "merged onto" not in out


def test_local_build_without_pull_policy_is_rejected(tmp_path):
    _compose_repo(tmp_path, _COMPOSE_CLEAN.replace("    pull_policy: build\n", ""))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "pull_policy: build" in out


@pytest.mark.parametrize(
    ("user_line", "expected"),
    [("", "sets no `user:`"), ('    user: "1000"\n', "runs as user '1000'")],
)
def test_data_mount_without_a_group_zero_user_is_rejected(tmp_path, user_line, expected):
    """B6: uid 10001 cannot write a directory the host user owns."""
    _compose_repo(tmp_path, _COMPOSE_CLEAN.replace('    user: "${ATRIUM_UID:-10001}:0"\n', user_line))
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert expected in out


def test_data_mount_the_clone_lacks_is_rejected(tmp_path):
    """B6: Docker creates a missing bind source root-owned."""
    _compose_repo(tmp_path, gitkeep=False)
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "Commit data/.gitkeep" in out


def test_each_data_subdirectory_mount_needs_its_own_gitkeep(tmp_path):
    """page-classification's `./data/output:/app/result`: `data/` existing is not enough."""
    compose = _COMPOSE_CLEAN.replace(
        "      - ./data:/data\n", "      - ./data:/data\n      - ./data/output:/app/result\n"
    )
    _compose_repo(tmp_path, compose)
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "Commit data/output/.gitkeep" in out
    write_gitkeep(tmp_path, "data/output")
    rc, out = run_lint(tmp_path)
    assert rc == 0, out


# ── the property that makes the output trustworthy ───────────────────────────


def test_one_break_does_not_mask_others(tmp_path):
    """Findings accumulate: three independent defects are all reported at once.

    If the linter returned at the first error, a maintainer would fix one defect,
    re-run, find another, and learn to distrust a clean run after a fix.
    """
    write_workflow(
        tmp_path,
        "x.yml",
        """\
name: X
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
""",
    )
    write_template(tmp_path, "bad.caller.example.yml", "version: 2\nupdates: []\n")
    # #69's rules, broken in the same run: an action below the floor, and a compose
    # file with the B2 tag form and an unwritable ./data mount.
    write_workflow(tmp_path, "old.yml", _FLOOR % "actions/checkout@v4")
    write_workflow(tmp_path, "docker.yml", DOCKER_CALLER)
    write_compose(tmp_path, "docker-compose.yml", _COMPOSE_B2_FORM)
    rc, out = run_lint(tmp_path)
    assert rc == 1
    assert "timeout-minutes" in out
    assert "concurrency" in out
    assert "permissions" in out
    assert "no `uses:`" in out
    assert "below the ecosystem floor" in out
    assert "the tag must be exactly" in out
    assert "sets no `user:`" in out


def test_hub_itself_passes_its_own_linter():
    """The hub must satisfy the rules it publishes. This is the check that would
    have caught the `docker.caller.example.yml` clobber on the commit that made it."""
    rc, out = run_lint(_HUB_ROOT)
    assert rc == 0, out
