#!/usr/bin/env python3
"""Policy checks for the ATRIUM hub's own workflows and caller templates (issue #18).

The hub is the single source of truth for every reusable workflow in the
ecosystem -- 37 caller jobs across six repos resolve `@v1` to files in this
repository -- yet until now nothing in CI looked at those files. Every defect
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
    python tools/ci/workflow_lint.py [--repo-root .] [--offline]

`--offline` skips only the network half of the pin check (that a pinned SHA is
really what its version comment claims). Everything else is static.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

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
    workflow sets `concurrency` and an explicit `permissions` block.

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

    if not is_reusable_only and doc.get("concurrency") is None:
        findings.error(
            path,
            "has no `concurrency` group. Overlapping runs of the same workflow race "
            "each other; every other triggerable workflow here sets one.",
        )

    has_job_perms = any(
        isinstance(j, dict) and j.get("permissions") is not None for j in jobs.values()
    )
    if doc.get("permissions") is None and not has_job_perms:
        findings.error(
            path,
            "declares no `permissions:` at workflow or job level, so it inherits the "
            "repository default token scope. Least privilege is explicit here.",
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
                    f"job '{job_name}' omits required input '{name}' of "
                    f"{callee_path.name}.",
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
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    hub_root = Path(args.hub_root).resolve() if args.hub_root else root
    findings = Findings()
    paths = workflow_files(root)
    if not paths:
        print(f"::error::no workflow files found under {root}", file=sys.stderr)
        return 1

    pins = perms = inputs = 0
    shapes = refs = hygiene = required = 0
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
    check_duplicate_names(docs, findings)

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
