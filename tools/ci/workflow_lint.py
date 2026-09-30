#!/usr/bin/env python3
"""Policy checks for the ATRIUM hub's own workflows and caller templates (issue #18).

The hub is the single source of truth for every reusable workflow in the
ecosystem -- 38 caller jobs across six repos resolve to files in this repository
(35 in the five tool repos at `@v1`, 3 hub-local by path; counted 2026-09-30) --
yet until now nothing in CI looked at those files. Every defect
found in them during #18 was found by hand:

  * `security.reusable.yml` kept a mutable `aquasecurity/trivy-action@v0.36.0`
    tag through a pinning pass that converted the other ten occurrences -- in
    the very file whose comment documents that action's 2026-03 compromise.
  * `docker.caller.example.yml` granted an explicit permissions block that
    omitted `security-events: write`, so anyone adopting the template
    reproduced a parse-time startup_failure.
  * `secrets: inherit` survived in a template after being removed from all ten
    live callers.

Each check below corresponds to one of those. They are cheap and they run on
every push, which is the point: a check that only a human remembers to run is
not a check.

Exit code is 0 when clean, 1 when any check fails. Every failure names the file.

Usage:
    python tools/ci/workflow_lint.py [--repo-root .] [--offline] [--repo-name owner/repo]

`--offline` skips only the network half of the pin check (that a pinned SHA is
really what its version comment claims). Everything else is static.

Round 5 (#69) added three rules that hold what the roadmap's pilot slice fixed:
the action-version floor, a `permissions:` block on every job of a workflow that
declares none at the top, and the compose image/`./data` rule (check_compose),
which runs wherever a repository has root compose files -- i.e. in the five tool
repos, through workflow-lint.reusable.yml.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

import yaml

# Actions that hold write scope or push artifacts. These are the ones where a
# force-pushed tag would run attacker code with something worth stealing, so
# they must resolve to an immutable commit. Read-only and upload-only actions
# (setup-python, checkout, metadata, login, codecov) are deliberately absent.
WRITE_SCOPED = {
    "softprops/action-gh-release",
    "peter-evans/create-pull-request",
    "docker/build-push-action",
    "aquasecurity/trivy-action",
}

PERMISSION_ORDER = {"none": 0, "read": 1, "write": 2}

# The action-version floor (#69, roadmap E3): the majors docs/docker_gha.md §2 names
# as the Node-24 baseline. The floor was a paragraph nobody enforced, and the two
# caller templates below it (`checkout@v4`, `setup-python@v5`, `github-script@v7`)
# stayed there for weeks after every live workflow moved -- a template is adopted by
# copy, so it re-seeds the old majors in whichever repo copies it next.
#
# Keyed by `owner/repo`, so every `github/codeql-action/<sub>` shares one floor. The
# write-scoped actions (WRITE_SCOPED) are absent on purpose: they are SHA-pinned, and
# whether the SHA is the release its comment claims is check_pins' job.
ACTION_FLOOR = {
    "actions/checkout": 7,
    "actions/setup-python": 7,
    "actions/cache": 6,
    "actions/upload-artifact": 7,
    "actions/github-script": 9,
    "codecov/codecov-action": 7,
    "github/codeql-action": 4,
    "docker/login-action": 4,
    "docker/metadata-action": 6,
    "docker/setup-buildx-action": 4,
}
MAJOR_REF_RE = re.compile(r"^v(?P<major>\d+)(?:\.\d+)*$")

# `uses: owner/repo@ref` with an optional trailing `# vX.Y` version comment.
USES_RE = re.compile(r"uses:\s*(?P<action>[\w.-]+/[\w./-]+)@(?P<ref>\S+)(?P<rest>[^\n]*)")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_COMMENT_RE = re.compile(r"#\s*(?P<version>v?[\d][\w.-]*)")


class Findings:
    """Collects failures so one run reports everything, not just the first."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def error(self, path: Path, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def note(self, message: str) -> None:
        self.notes.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def workflow_files(root: Path) -> list[Path]:
    """Hub workflows plus the caller templates we publish for other repos.

    The templates matter as much as the live workflows: they are what the next
    repo copies, so a defect there is a defect waiting to be adopted.
    """
    # W5 (2026-08-06): `*.yaml` included alongside `*.yml`. GitHub accepts both
    # spellings for workflows; a template saved with the other extension was simply
    # invisible to every check here.
    #
    # docs/templates/skill/ publishes a caller template too, and being outside the
    # glob is exactly how it kept an `@test` pin through the 2026-07-31 migration
    # that moved all 40 live callers to `@v1` (issue #10, G7). A published template
    # is adopted by copy, so an unlinted one is a defect waiting to be inherited.
    search_dirs = [
        root / ".github" / "workflows",
        root / "docs" / "templates" / "workflows",
        root / "docs" / "templates" / "skill",
    ]
    paths: list[Path] = []
    for directory in search_dirs:
        paths += sorted(directory.glob("*.yml"))
        paths += sorted(directory.glob("*.yaml"))
    # dependabot.yml is a policy file this ecosystem publishes a template for, and
    # the Requires-Python guard lives in it — worth parsing even though it carries no
    # `name:`/`jobs:` (see check_template_shape for why that distinction matters).
    dependabot = root / ".github" / "dependabot.yml"
    if dependabot.exists():
        paths.append(dependabot)
    return paths


def load(path: Path, findings: Findings) -> dict | None:
    """Check 1 -- every file parses. Returns None (and records) on failure."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        findings.error(path, f"does not parse as YAML: {exc}")
        return None


def resolve_tag(action: str, tag: str) -> str | None:
    """Commit SHA a tag points at, or None if it cannot be resolved.

    The `^{}` deref is load-bearing. For an ANNOTATED tag, `refs/tags/v3`
    names the tag object, not the commit -- pinning that SHA silently fails,
    because the SHA a workflow needs is the commit. Both `action-gh-release@v3`
    and `trivy-action@v0.36.0` are annotated, so this bit us in practice.
    """
    try:
        out = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{action}", f"refs/tags/{tag}^{{}}", f"refs/tags/{tag}"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    deref = [ln.split("\t")[0] for ln in out.splitlines() if ln.endswith("^{}")]
    plain = [ln.split("\t")[0] for ln in out.splitlines() if not ln.endswith("^{}")]
    if deref:
        return deref[0]
    return plain[0] if plain else None


def check_pins(path: Path, text: str, findings: Findings, offline: bool) -> int:
    """Check 2 -- write-scoped actions are SHA-pinned and honestly labelled.

    A pin with a wrong or stale version comment is arguably worse than none:
    it tells a reader the action is at v3 when it is not, and nobody re-checks
    a comment. So the comment is verified against the real tag, not trusted.
    """
    checked = 0
    for match in USES_RE.finditer(text):
        action, ref, rest = match["action"], match["ref"], match["rest"]
        if action not in WRITE_SCOPED:
            continue
        checked += 1
        if not SHA_RE.match(ref):
            findings.error(
                path,
                f"{action} is pinned to the mutable tag '{ref}'. Write-scoped "
                f"actions must use a 40-char commit SHA -- a tag can be "
                f"force-pushed (GHSA-69fq-xp46-6x23 hit this very ecosystem).",
            )
            continue
        version = VERSION_COMMENT_RE.search(rest)
        if not version:
            findings.error(
                path,
                f"{action} is SHA-pinned but has no '# vX' comment, so no "
                f"reader (or Dependabot) can tell which release it is.",
            )
            continue
        if offline:
            continue
        actual = resolve_tag(action, version["version"])
        if actual is None:
            findings.note(
                f"{path}: could not resolve {action}@{version['version']} (network?); pin format was still checked."
            )
        elif actual != ref:
            findings.error(
                path,
                f"{action} claims '# {version['version']}' but that tag "
                f"resolves to {actual[:12]}..., not the pinned {ref[:12]}.... "
                f"Either the comment is stale or the SHA is wrong.",
            )
    return checked


def check_secrets_inherit(path: Path, doc: dict, findings: Findings) -> None:
    """Check 3 -- no structural `secrets: inherit`.

    Parsed, never grepped. The explanatory comments in these very files contain
    the literal string 'secrets: inherit', so a grep-based version of this
    check reports the exact opposite of the truth.
    """
    for job_name, job in (doc.get("jobs") or {}).items():
        if isinstance(job, dict) and job.get("secrets") == "inherit":
            findings.error(
                path,
                f"job '{job_name}' passes `secrets: inherit`, handing the "
                f"callee every secret in the repo. Declare only what the "
                f"reusable actually needs.",
            )


def check_duplicate_names(docs: dict[Path, dict], findings: Findings) -> None:
    """Check 5 -- no two workflows claim the same `name:`.

    A duplicate name is the fingerprint of a copy-paste clobber: one file
    overwritten with another's contents. That happened twice in #18 --
    `codeql.caller.example.yml` became a copy of the Docker example, and
    `skill-validate.reusable.yml` was overwritten with `security.reusable.yml`,
    silently destroying 348 lines and breaking the five `agent-skill` callers
    that pass an input the replacement does not declare.

    Neither was caught by parsing, pins, permissions or secrets -- every one of
    those passes happily on a well-formed file that is simply the wrong file.

    Compared WITHIN a directory, not across. A caller template is the worked
    example of a real caller, so `docs/templates/workflows/codeql.caller.example.yml`
    sharing the display name "CodeQL" with `.github/workflows/codeql.yml` is
    correct and expected. Both real clobbers were within a single directory.
    """
    seen: dict[tuple[str, str], Path] = {}
    for path, doc in docs.items():
        name = doc.get("name")
        if not name:
            continue
        key = (str(path.parent), name)
        if key in seen:
            findings.error(
                path,
                f"declares name {name!r}, which {seen[key].name} in the same "
                f"directory already uses. Two workflows sharing a name usually "
                f"means one was overwritten with a copy of the other.",
            )
        else:
            seen[key] = path


def resolve_callee(uses: str, root: Path, hub_root: Path) -> Path | None:
    """Filesystem path of the reusable a job calls, or None if not resolvable.

    Two call forms exist in this ecosystem and both must resolve, or the
    permission and input checks quietly pass by asserting nothing:

      * `ufal/atrium-project/.github/workflows/X.yml@ref` -- resolved from
        HUB_ROOT. When linting a tool repo, the callee lives in a different
        repository; without a hub checkout to resolve against, both checks
        no-op. That is why running this against atrium-translator reported
        "0 caller/callee permission pairs" -- not a clean bill of health, just
        an unasked question. The caller/callee permission check is the one that
        catches the Wave B startup_failure class, so it is precisely the check
        worth having outside the hub.

      * `./.github/workflows/X.yml` -- a same-repo call, resolved from ROOT.
        The hub's own codeql.yml and pre-commit.yml use this form so that a
        self-check validates the ref being pushed rather than the last released
        tag.
    """
    cross_repo = re.match(r"ufal/atrium-project/(\.github/workflows/[^@]+)@", uses)
    if cross_repo:
        candidate = hub_root / cross_repo.group(1)
    elif uses.startswith("./"):
        candidate = root / uses[2:]
    else:
        return None  # third-party or unrecognised; not ours to check
    return candidate if candidate.exists() else None


def check_template_inputs(path: Path, doc: dict, root: Path, hub_root: Path, findings: Findings) -> int:
    """Check 6 -- a template only passes inputs its reusable declares.

    This is the check that catches a clobbered callee directly: after
    `skill-validate.reusable.yml` was overwritten, the template still passed
    `client-script` while the replacement declared `image-ref`,
    `citation-path` and `para-config-path`. GitHub rejects an undeclared input
    at parse time, so those callers were already broken -- latently, because
    nobody had pushed to an `agent-skill` branch since.
    """
    checked = 0
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict) or "uses" not in job:
            continue
        callee_path = resolve_callee(str(job["uses"]), root, hub_root)
        if callee_path is None:
            continue
        callee = yaml.safe_load(callee_path.read_text(encoding="utf-8")) or {}
        # `on:` parses as the boolean True in YAML 1.1, hence the fallback.
        trigger = callee.get(True) or callee.get("on") or {}
        declared = set(((trigger.get("workflow_call") or {}).get("inputs") or {}))
        passed = set(job.get("with") or {})
        for undeclared in sorted(passed - declared):
            findings.error(
                path,
                f"job '{job_name}' passes input '{undeclared}', which "
                f"{callee_path.name} does not declare. GitHub rejects this at "
                f"parse time. Declared there: {sorted(declared) or 'none'}.",
            )
        checked += len(passed)
    return checked


#: Sentinel for `permissions: write-all` -- satisfies every scope.
_SHORTHAND_WRITE_ALL = object()
#: Sentinel for `permissions: read-all` -- read on every scope, write on none.
_SHORTHAND_READ_ALL = object()


def _normalise_permissions(perms):
    """Map a `permissions:` value to a dict, or a shorthand sentinel.

    GitHub accepts three shapes: a mapping, the string `read-all`/`write-all`, and
    `{}` (all scopes none). Treating the string form as a mapping is what crashed
    the linter (see check_template_permissions).
    """
    if perms is None:
        return None
    if isinstance(perms, dict):
        return perms
    text = str(perms).strip()
    if text == "write-all":
        return _SHORTHAND_WRITE_ALL
    if text == "read-all":
        return _SHORTHAND_READ_ALL
    # Unknown scalar -- treat as granting nothing rather than guessing.
    return {}


def check_template_shape(path: Path, doc: dict, text: str, findings: Findings) -> int:
    """Check -- a published `*.caller.example.yml` must actually call something.

    W1's failure mode, made mechanical. `docker.caller.example.yml` was overwritten
    with a dependabot config: 58 lines, zero `uses:`. Nothing caught it, because
    `check_duplicate_names` skips any file with no `name:` key -- and a dependabot
    config has none -- so the very check written to catch "the fingerprint of a
    copy-paste clobber" was blind to the clobber that actually happened. The
    workflow it was meant to exemplify (the most-used reusable in the ecosystem) had
    no caller example for two days.

    A caller example whose entire purpose is to be copied as a caller must contain a
    `uses:`. That is the whole rule.
    """
    if not path.name.endswith(".caller.example.yml"):
        return 0
    if "uses:" in text:
        return 1
    findings.error(
        path,
        "is a *.caller.example.yml but contains no `uses:` -- it cannot be a caller "
        "example. This is the docker.caller.example.yml clobber signature (a "
        "dependabot config written over the docker caller template, 2026-08-04): "
        "the file a downstream repo copies would not call anything.",
    )
    return 1


def check_caller_ref(path: Path, doc: dict, findings: Findings) -> int:
    """Check -- hub reusables are pinned at `@v1`, not a branch or another tag.

    G7 widened the template glob so the `@test`-pinned skill template became
    VISIBLE, but visibility is not a rule: nothing yet fails a caller pinned at
    `@test`, `@main` or `@v2-beta`. A branch pin means the caller silently follows
    whatever lands on that branch -- which is exactly how a reusable change reaches
    all five repos without anyone choosing to adopt it.
    """
    checked = 0
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict) or "uses" not in job:
            continue
        uses = str(job["uses"])
        if "ufal/atrium-project/.github/workflows/" not in uses:
            continue  # third-party or local reusable; pins are check_pins' job
        checked += 1
        ref = uses.rsplit("@", 1)[-1] if "@" in uses else ""
        if ref != "v1":
            findings.error(
                path,
                f"job '{job_name}' pins a hub reusable at '@{ref}', not '@v1'. "
                "Branch and pre-release pins make a hub change reach this repo "
                "without anyone adopting it; `v1` is the ecosystem's adoption point.",
            )
    return checked


def check_job_hygiene(path: Path, doc: dict, findings: Findings) -> int:
    """Check -- every runner job sets `timeout-minutes`, and every triggerable
    workflow sets `concurrency` (with cancellation semantics a scheduled run can
    survive) and an explicit `permissions` block.

    These three policies were rolled out by hand, and `all-repos-smoke.yml` lost all
    three within two days of the rollout. A hand-applied policy with no rule behind
    it is a policy that drifts back.

    Reusables (`workflow_call`-only) are exempt from `concurrency`: the CALLER owns
    the concurrency group, and setting one in the callee would collapse five repos'
    builds into a single queue.
    """
    checked = 0
    jobs = doc.get("jobs") or {}
    if not jobs:
        return 0  # dependabot config or similar -- not a workflow

    triggers = doc.get(True) or doc.get("on") or {}
    if isinstance(triggers, str):
        triggers = {triggers: None}
    trigger_names = set(triggers) if isinstance(triggers, dict) else set()
    is_reusable_only = trigger_names == {"workflow_call"}

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        # A caller job (`uses:`) runs no runner of its own -- the callee sets the timeout.
        if "uses" in job:
            continue
        checked += 1
        if job.get("timeout-minutes") is None:
            findings.error(
                path,
                f"job '{job_name}' has no `timeout-minutes`. A hung job holds a "
                "runner for the 6-hour default; every other job in this ecosystem "
                "sets one.",
            )

    concurrency = doc.get("concurrency")
    if not is_reusable_only and concurrency is None:
        findings.error(
            path,
            "has no `concurrency` group. Overlapping runs of the same workflow race "
            "each other; every other triggerable workflow here sets one.",
        )
    elif "schedule" in trigger_names and isinstance(concurrency, dict):
        # Requiring the BLOCK is not the same as requiring it to be correct, and this
        # rule exists because the gap between the two ate a nightly. Every group here is
        # keyed `<workflow>-${{ github.ref }}`, so a scheduled run and a push run on the
        # same ref land in ONE group -- and with cancel-in-progress the push wins. On
        # 2026-08-19 that cancelled all-repos-smoke run #32 eleven seconds before a push
        # run started, and a cancelled run reports no failure: the nightly stops
        # producing a signal without ever going red. (issue atrium-project#10)
        #
        # Two remedies, both accepted, because they suit different workflows:
        #   * scope the group by `github.event_name` -- keeps push/PR de-duplication,
        #     which is the whole point of cancelling on a busy branch; or
        #   * `cancel-in-progress: false` -- right for the heavy, infrequent jobs whose
        #     runs are never redundant (the e2e smokes and vocab-refresh already do this).
        group = str(concurrency.get("group", ""))
        cancel = concurrency.get("cancel-in-progress", False)
        # An expression (`${{ !startsWith(github.ref, 'refs/tags/') }}`) is not False: it
        # evaluates true for every non-tag ref, scheduled runs included.
        may_cancel = cancel is not False
        event_scoped = "github.event_name" in group or "github.run_id" in group
        if may_cancel and not event_scoped:
            findings.error(
                path,
                f"is triggered by `schedule` but its concurrency group ({group!r}) does "
                f"not distinguish the event and cancel-in-progress is {cancel!r}. A push "
                "to the same ref will cancel the scheduled run, which then reports no "
                "failure rather than a result. Add `github.event_name` to the group, or "
                "set `cancel-in-progress: false`.",
            )

    # E6, generalised (#69). The old rule passed as soon as ANY job had a block, so a
    # workflow with no top-level `permissions:` could scope one job and leave its
    # siblings at the repository default -- exactly docker-tool.reusable.yml's shape in
    # 2026-08, where the jobs running arbitrary test and build code were the unscoped
    # ones. With no workflow-level block, a job's own block is its only scope, so every
    # job needs one. A caller job (`uses:`) counts too: without a grant of its own the
    # callee starts from the repository default.
    if doc.get("permissions") is None:
        bare = [name for name, j in jobs.items() if isinstance(j, dict) and j.get("permissions") is None]
        if bare and len(bare) == sum(isinstance(j, dict) for j in jobs.values()):
            findings.error(
                path,
                "declares no `permissions:` at workflow or job level, so it inherits the "
                "repository default token scope. Least privilege is explicit here.",
            )
        else:
            for name in bare:
                findings.error(
                    path,
                    f"job '{name}' has no `permissions:` and the workflow declares none at the "
                    "top, so this job runs at the repository default token scope while its "
                    "siblings are scoped. Give it its own block, or add a workflow-level one.",
                )
    return checked


def _step_uses(doc: dict):
    """Yield (job name, `uses:` value) for every STEP of a parsed workflow.

    Parsed, not grepped: these files quote old pins in their comments on purpose (the
    history of a fix is part of the fix), and a grep would flag the explanation.
    """
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("uses"):
                yield job_name, str(step["uses"])


def check_action_floor(path: Path, doc: dict, findings: Findings) -> int:
    """Check -- every floor-listed action is at or above the ecosystem's major.

    Only a `@vN[.x.y]` ref is compared. A SHA pin is check_pins' job, and a local
    (`./…`) or `docker://` reference has no major to compare.
    """
    checked = 0
    for job_name, uses in _step_uses(doc):
        if "@" not in uses:
            continue
        action, ref = uses.rsplit("@", 1)
        floor = ACTION_FLOOR.get("/".join(action.split("/")[:2]))
        if floor is None:
            continue
        checked += 1
        major = MAJOR_REF_RE.match(ref)
        if major and int(major["major"]) < floor:
            findings.error(
                path,
                f"job '{job_name}' uses {action}@{ref}, below the ecosystem floor @v{floor} "
                "(docs/docker_gha.md §2, the Node-24 baseline). A template below the floor "
                "re-seeds the old major in every repo that copies it.",
            )
    return checked


def check_required_inputs(path: Path, doc: dict, root: Path, hub_root: Path, findings: Findings) -> int:
    """Check -- a caller passes every input its callee declares `required: true`.

    `skill-validate.reusable.yml` declares `client-script: required: true` and
    nothing enforced it, so a caller omitting it fails at run time with an empty
    string rather than at lint time with a name.
    """
    checked = 0
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict) or "uses" not in job:
            continue
        callee_path = resolve_callee(str(job["uses"]), root, hub_root)
        if callee_path is None:
            continue
        callee = yaml.safe_load(callee_path.read_text(encoding="utf-8")) or {}
        call_spec = (callee.get(True) or callee.get("on") or {}).get("workflow_call") or {}
        declared = call_spec.get("inputs") or {}
        passed = set(job.get("with") or {})
        for name, spec in declared.items():
            if not isinstance(spec, dict) or not spec.get("required"):
                continue
            checked += 1
            if name not in passed:
                findings.error(
                    path,
                    f"job '{job_name}' omits required input '{name}' of {callee_path.name}.",
                )
    return checked


def check_template_permissions(path: Path, doc: dict, root: Path, hub_root: Path, findings: Findings) -> int:
    """Check 4 -- a template's permission grant covers what its reusable requests.

    GitHub caps a reusable workflow's job permissions at the calling job's
    grant and rejects the caller at PARSE time if it asks for more --
    a startup_failure, not a step failure, so no amount of local YAML
    validation catches it. This is what took down docker.yml in all five tool
    repos at once.

    The distinction that matters, and that a naive version of this check gets
    wrong: an EXPLICIT permissions block that omits a scope fails, but NO block
    at all inherits the repository default and is fine.
    """
    checked = 0
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict) or "uses" not in job:
            continue
        callee_path = resolve_callee(str(job["uses"]), root, hub_root)
        if callee_path is None:
            continue
        callee = yaml.safe_load(callee_path.read_text(encoding="utf-8")) or {}

        # No explicit block anywhere in the caller -> repo default applies.
        if job.get("permissions") is None and doc.get("permissions") is None:
            continue

        # W5 (2026-08-06): `permissions:` also accepts the SHORTHAND STRINGS
        # `read-all` / `write-all` (and a job may use `{}` for "none"). The previous
        # `{**doc_perms, **job_perms}` assumed both were always mappings and raised
        # `TypeError: 'str' object is not a mapping` on the legal shorthand — the
        # linter crashed instead of reporting, taking down every later check with it.
        # Reproduced directly against `permissions: read-all`.
        doc_perms = _normalise_permissions(doc.get("permissions"))
        job_perms = _normalise_permissions(job.get("permissions"))
        # A job-level block REPLACES the workflow-level one; it does not merge with
        # it. So the effective grant is the job's when it has one, else the workflow's.
        effective = job_perms if job_perms is not None else doc_perms
        if effective is _SHORTHAND_WRITE_ALL:
            continue  # write-all satisfies every scope
        # read-all grants `read` on every scope -- and write on none.
        read_all = effective is _SHORTHAND_READ_ALL
        granted = effective if isinstance(effective, dict) else {}
        for callee_job, callee_body in (callee.get("jobs") or {}).items():
            needed = callee_body.get("permissions") or callee.get("permissions") or {}
            if not isinstance(needed, dict):
                continue
            for scope, level in needed.items():
                checked += 1
                have = "read" if read_all else granted.get(scope, "none")
                if PERMISSION_ORDER.get(str(have), 0) >= PERMISSION_ORDER.get(str(level), 0):
                    continue
                findings.error(
                    path,
                    f"job '{job_name}' grants {scope}: {have}, but "
                    f"{callee_path.name} job '{callee_job}' requests "
                    f"{scope}: {level}. GitHub rejects this at parse time "
                    f"(startup_failure) -- grant it explicitly.",
                )
    return checked


# ── compose files (#69: B2, B3's compose half, B6) ───────────────────────────
#
# Three roadmap findings lived in compose files and nothing read them:
#   * B2 -- compose asked for `atrium-<tool>:<ver>-api` while CI publishes
#     `atrium-<tool>-api:<ver>`, so `docker compose pull` 404'd in four repos;
#   * B3 -- a compose `ATRIUM_RUNNER_IMAGE` that differs from the service's own image
#     makes paradata name an image the run did not use (alto's GPU overlay kept the
#     CPU name once merged; alto `api` baked the batch name through `extends:`);
#   * B6 -- `./data` bind mounts that no clone contains, so Docker created them
#     root-owned and the uid-10001 container could not write its output.
# The rule is enforced where the defect was: every tool repo runs this linter through
# workflow-lint.reusable.yml, with GITHUB_REPOSITORY naming the caller.

COMPOSE_BASES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
COMPOSE_GLOBS = ("docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml")
GHCR_IMAGE_RE = re.compile(r"^ghcr\.io/(?P<name>[^:@\s]+):(?P<tag>\S+)$")
# The tag is the release version and nothing else: `${ATRIUM_VERSION:-dev}`. A target
# suffix after it (`${ATRIUM_VERSION:-dev}-api`) is B2 -- the target is part of the NAME.
VERSION_TAG_RE = re.compile(r"^\$\{ATRIUM_VERSION(?::?-[^}]*)?\}$")
REPOSITORY_EXPR_RE = re.compile(r"\$\{\{\s*github\.repository\s*\}\}")


class PublishSpec:
    """What the repo's docker.yml publishes: `image-name` and `build-targets`."""

    def __init__(self, image_name: str | None, targets: list[str] | None, source: Path | None) -> None:
        self.image_name = image_name
        self.targets = targets
        self.source = source

    def published_names(self) -> dict[str, str]:
        if not self.image_name or self.targets is None:
            return {}
        return {(self.image_name if t == "base" else f"{self.image_name}-{t}"): t for t in self.targets}


def docker_publish_spec(root: Path, hub_root: Path, repo_name: str | None) -> PublishSpec:
    """Read `image-name`/`build-targets` from the caller of docker-tool.reusable.yml."""
    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue  # check 1 reports it
        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict) or "docker-tool.reusable.yml" not in str(job.get("uses", "")):
                continue
            passed = job.get("with") or {}
            name = passed.get("image-name")
            if isinstance(name, str) and REPOSITORY_EXPR_RE.search(name):
                name = REPOSITORY_EXPR_RE.sub(repo_name, name) if repo_name else None
            if isinstance(name, str) and "${{" in name:
                name = None  # another expression: form-only checks
            raw_targets = passed.get("build-targets")
            if raw_targets is None:
                callee = resolve_callee(str(job["uses"]), root, hub_root)
                if callee is not None:
                    callee_doc = yaml.safe_load(callee.read_text(encoding="utf-8")) or {}
                    spec = callee_doc.get(True) or callee_doc.get("on") or {}
                    raw_targets = (
                        ((spec.get("workflow_call") or {}).get("inputs") or {}).get("build-targets") or {}
                    ).get("default")
            try:
                targets = json.loads(raw_targets) if isinstance(raw_targets, str) else None
            except json.JSONDecodeError:
                targets = None
            return PublishSpec(name.lower() if isinstance(name, str) else None, targets, path)
    return PublishSpec(None, None, None)


def _mapping(value) -> dict[str, str]:
    """`environment:` / `build.args:` in either compose form, as a dict."""
    if isinstance(value, dict):
        return {str(k): "" if v is None else str(v) for k, v in value.items()}
    if isinstance(value, list):
        out = {}
        for item in value:
            key, _, val = str(item).partition("=")
            out[key] = val
        return out
    return {}


def _volume(value) -> tuple[str | None, str | None, str]:
    """(source, target, type) of a compose volume in short or long syntax."""
    if isinstance(value, dict):
        return value.get("source"), value.get("target"), str(value.get("type", "volume"))
    parts = str(value).split(":")
    if len(parts) == 1:
        return None, parts[0], "volume"
    source = parts[0]
    return source, parts[1], "bind" if source.startswith((".", "/", "~")) else "volume"


def _merge_service(base: dict, over: dict) -> dict:
    """Compose's merge for the keys these checks read: mappings merge, `build.args`
    and `environment` merge by key, `volumes` merge by container path."""
    out = dict(base)
    for key, value in over.items():
        if key == "extends":
            continue
        if key == "build":
            old = {"context": base["build"]} if isinstance(base.get("build"), str) else dict(base.get("build") or {})
            new = {"context": value} if isinstance(value, str) else dict(value or {})
            merged = {**old, **new}
            args = {**_mapping(old.get("args")), **_mapping(new.get("args"))}
            if args:
                merged["args"] = args
            out["build"] = merged
        elif key == "environment":
            out[key] = {**_mapping(base.get(key)), **_mapping(value)}
        elif key == "volumes":
            by_target = {_volume(v)[1]: v for v in list(base.get(key) or []) + list(value or [])}
            out[key] = list(by_target.values())
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            out[key] = {**base[key], **value}
        else:
            out[key] = value
    return out


def _load_services(path: Path) -> dict[str, dict]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    services = doc.get("services") or {}
    return {str(k): v for k, v in services.items() if isinstance(v, dict)}


def _resolve_extends(services: dict[str, dict], directory: Path, depth: int = 0) -> dict[str, dict]:
    """Apply `extends:` within one file (and to a `file:` it names), as compose does
    before it merges an overlay."""
    resolved: dict[str, dict] = {}

    def resolve(name: str, seen: frozenset) -> dict:
        if name in resolved:
            return resolved[name]
        service = services.get(name) or {}
        extends = service.get("extends")
        if extends:
            base_name, other = (
                (extends, None) if isinstance(extends, str) else (extends.get("service"), extends.get("file"))
            )
            if other and depth < 3 and (directory / other).is_file():
                base = _resolve_extends(_load_services(directory / other), directory, depth + 1).get(base_name, {})
            elif not other and base_name not in seen:
                base = resolve(base_name, seen | {name})
            else:
                base = {}
            service = _merge_service(base, service)
        resolved[name] = service
        return service

    for name in services:
        resolve(name, frozenset({name}))
    return resolved


def _data_source(source: str | None) -> PurePosixPath | None:
    """The repo-relative path of a bind source under `data/`, else None."""
    if not source or source.startswith(("/", "~")):
        return None
    parts = [p for p in PurePosixPath(source).parts if p != "."]
    return PurePosixPath(*parts) if parts and parts[0] == "data" else None


def _check_service(name: str, service: dict, spec: PublishSpec, root: Path, counts: dict[str, set]) -> list[str]:
    """The findings for one resolved service, as messages (the caller names the file)."""
    problems: list[str] = []
    image = service.get("image")
    build = service.get("build")
    published = spec.published_names()
    if isinstance(image, str):
        match = GHCR_IMAGE_RE.match(image)
        if match:
            counts["published"].add(image)
            if not VERSION_TAG_RE.match(match["tag"]):
                problems.append(
                    f"service '{name}' asks for {image}: the tag must be exactly "
                    "`${ATRIUM_VERSION:-dev}`. CI publishes the target as part of the image "
                    "NAME (`ghcr.io/<tool>-<target>:<version>`), so a tag suffix names an image "
                    "that does not exist and `docker compose pull` fails (roadmap B2).",
                )
            if published and match["name"].lower() not in published:
                problems.append(
                    f"service '{name}' asks for ghcr.io/{match['name']}, which "
                    f"{spec.source.name if spec.source else 'docker.yml'} does not publish. "
                    f"Published: {', '.join(f'ghcr.io/{n}' for n in sorted(published))}. A service "
                    "built only locally takes a bare name and `pull_policy: build`.",
                )
        elif build is not None:
            counts["local"].add(image)
            if service.get("pull_policy") != "build":
                problems.append(
                    f"service '{name}' builds {image}, a name no registry publishes, without "
                    "`pull_policy: build` -- so `docker compose pull` asks a registry for it.",
                )
        args = _mapping(build.get("args")) if isinstance(build, dict) else {}
        for where, values in (("build arg", args), ("environment", _mapping(service.get("environment")))):
            recorded = values.get("ATRIUM_RUNNER_IMAGE")
            if recorded and recorded != image:
                problems.append(
                    f"service '{name}' runs {image} but its {where} ATRIUM_RUNNER_IMAGE is "
                    f"{recorded}, so paradata names an image this service did not run "
                    "(roadmap B3). Set it to the service's own `image:`.",
                )
    mounts = [_data_source(_volume(v)[0]) for v in service.get("volumes") or [] if _volume(v)[2] == "bind"]
    mounts = [m for m in mounts if m is not None]
    if not mounts:
        return problems
    counts["data"].add(name)
    user = str(service.get("user") or "")
    if not user.endswith(":0"):
        problems.append(
            f"service '{name}' bind-mounts ./{mounts[0]} but "
            + ("sets no `user:`" if not user else f"runs as user {user!r}")
            + '. Use `user: "${ATRIUM_UID:-10001}:0"`: the image runs as uid 10001, a clone '
            "is owned by the host user, and the image's writable paths are group-0 writable "
            "so a host uid with group 0 can use them (roadmap B6).",
        )
    for mount in mounts:
        if not (root / mount / ".gitkeep").is_file():
            problems.append(
                f"service '{name}' bind-mounts ./{mount}, which the repository does not "
                f"contain: Docker creates it root-owned on first run. Commit {mount}/.gitkeep "
                "(and un-ignore it) so a clone has it (roadmap B6).",
            )
    return problems


def check_compose(root: Path, hub_root: Path, repo_name: str | None, findings: Findings) -> dict[str, int]:
    """Check -- compose files name what CI publishes, record the image they run, and
    can write their `./data` mounts from a fresh clone.

    Each file is read the way compose reads it: `extends:` resolved within the file,
    then an overlay (`docker-compose.<x>.yml`) merged onto its base. The counts in the
    summary are distinct image references and distinct service names.
    """
    counts: dict[str, set] = {"files": set(), "published": set(), "local": set(), "data": set()}
    paths = sorted({p for pattern in COMPOSE_GLOBS for p in root.glob(pattern) if p.is_file()})
    if not paths:
        return {key: 0 for key in counts}
    spec = docker_publish_spec(root, hub_root, repo_name)
    resolved: dict[Path, dict[str, dict]] = {}
    for path in paths:
        try:
            resolved[path] = _resolve_extends(_load_services(path), root)
        except yaml.YAMLError as exc:
            findings.error(path.relative_to(root), f"does not parse as YAML: {exc}")
    for path, services in resolved.items():
        counts["files"].add(path.name)
        base_path = None
        if path.name not in COMPOSE_BASES:
            prefix = path.name.split(".", 1)[0]
            base_path = next(
                (root / b for b in COMPOSE_BASES if b.startswith(prefix + ".") and root / b in resolved), None
            )
        label = str(path.relative_to(root))
        base = resolved.get(base_path, {}) if base_path else {}
        if base_path:
            label += f" (merged onto {base_path.name})"
        for name, service in services.items():
            merged = _merge_service(base[name], service) if name in base else service
            problems = _check_service(name, merged, spec, root, counts)
            # An overlay inherits its base's defects; report only what the overlay adds,
            # so fixing the base file is one fix, not two.
            scratch: dict[str, set] = {key: set() for key in counts}
            already = set(_check_service(name, base[name], spec, root, scratch)) if name in base else set()
            for problem in problems:
                if problem not in already:
                    findings.error(Path(label), problem)
    return {key: len(values) for key, values in counts.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository to lint")
    parser.add_argument(
        "--hub-root",
        default=None,
        help="checkout of ufal/atrium-project used to resolve `ufal/atrium-project/...@ref` "
        "callees. Defaults to --repo-root, which is correct when linting the hub itself. "
        "Pass a separate checkout when linting a TOOL repo, or the caller/callee "
        "permission and input checks silently no-op.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip only the network check that a pinned SHA matches its version comment",
    )
    parser.add_argument(
        "--repo-name",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="owner/repo the linted tree belongs to, used to resolve `${{ github.repository }}` in "
        "docker.yml's `image-name` for the compose check. Defaults to $GITHUB_REPOSITORY, which "
        "workflow-lint.reusable.yml's runner sets to the CALLER; without either, compose image "
        "names are checked for form only.",
    )
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    hub_root = Path(args.hub_root).resolve() if args.hub_root else root
    findings = Findings()
    paths = workflow_files(root)
    if not paths:
        print(f"::error::no workflow files found under {root}", file=sys.stderr)
        return 1

    pins = perms = inputs = 0
    shapes = refs = hygiene = required = floors = 0
    docs: dict[Path, dict] = {}
    for path in paths:
        doc = load(path, findings)
        if doc is None:
            continue
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        docs[rel] = doc
        pins += check_pins(rel, text, findings, args.offline)
        check_secrets_inherit(rel, doc, findings)
        perms += check_template_permissions(rel, doc, root, hub_root, findings)
        inputs += check_template_inputs(rel, doc, root, hub_root, findings)
        # W5 additions.
        shapes += check_template_shape(rel, doc, text, findings)
        refs += check_caller_ref(rel, doc, findings)
        hygiene += check_job_hygiene(rel, doc, findings)
        required += check_required_inputs(rel, doc, root, hub_root, findings)
        # #69 round 5.
        floors += check_action_floor(rel, doc, findings)
    check_duplicate_names(docs, findings)
    compose = check_compose(root, hub_root, args.repo_name, findings)

    for note in findings.notes:
        print(f"::notice::{note}")

    if findings.ok:
        print(
            f"OK - {len(paths)} workflow/template files parse; "
            f"{pins} write-scoped pins verified; "
            f"{perms} caller/callee permission pairs satisfied; "
            f"{inputs} passed inputs declared; "
            f"{required} required inputs passed; "
            f"{refs} hub-reusable refs at @v1; "
            f"{hygiene} runner jobs carry timeout-minutes; "
            f"{shapes} caller templates contain a `uses:`; "
            f"{floors} floor-listed actions at or above the floor; "
            f"{compose['files']} compose files: {compose['published']} GHCR images published by docker.yml, "
            f"{compose['local']} local-only images pinned to `pull_policy: build`, "
            f"{compose['data']} services writing ./data as a set user; "
            f"no duplicate workflow names; no structural `secrets: inherit`."
        )
        return 0

    for error in findings.errors:
        print(f"::error::{error}")
    print(
        f"\n{len(findings.errors)} problem(s) in {root}. "
        f"In the hub these files are the source of truth for every caller in the "
        f"ecosystem; in a tool repo they are what actually runs.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
