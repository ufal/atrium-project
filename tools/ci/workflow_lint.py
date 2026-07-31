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
USES_RE = re.compile(
    r"uses:\s*(?P<action>[\w.-]+/[\w./-]+)@(?P<ref>\S+)(?P<rest>[^\n]*)"
)
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
    paths = sorted((root / ".github" / "workflows").glob("*.yml"))
    paths += sorted((root / "docs" / "templates" / "workflows").glob("*.yml"))
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
            ["git", "ls-remote", f"https://github.com/{action}",
             f"refs/tags/{tag}^{{}}", f"refs/tags/{tag}"],
            capture_output=True, text=True, timeout=60, check=False,
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
                f"{path}: could not resolve {action}@{version['version']} "
                f"(network?); pin format was still checked."
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


def check_template_inputs(path: Path, doc: dict, root: Path, findings: Findings) -> int:
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
        ref = re.match(
            r"ufal/atrium-project/(\.github/workflows/[^@]+)@", str(job["uses"])
        )
        if not ref:
            continue
        callee_path = root / ref.group(1)
        if not callee_path.exists():
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


def check_template_permissions(path: Path, doc: dict, root: Path, findings: Findings) -> int:
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
        ref = re.match(
            r"ufal/atrium-project/(\.github/workflows/[^@]+)@", str(job["uses"])
        )
        if not ref:
            continue
        callee_path = root / ref.group(1)
        if not callee_path.exists():
            continue  # pinned to a tag we cannot read from the working tree
        callee = yaml.safe_load(callee_path.read_text(encoding="utf-8")) or {}

        # No explicit block anywhere in the caller -> repo default applies.
        if job.get("permissions") is None and doc.get("permissions") is None:
            continue

        granted = {**(doc.get("permissions") or {}), **(job.get("permissions") or {})}
        for callee_job, callee_body in (callee.get("jobs") or {}).items():
            needed = callee_body.get("permissions") or callee.get("permissions") or {}
            if not isinstance(needed, dict):
                continue
            for scope, level in needed.items():
                checked += 1
                have = granted.get(scope, "none")
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
    parser.add_argument("--repo-root", default=".", help="hub checkout root")
    parser.add_argument(
        "--offline", action="store_true",
        help="skip only the network check that a pinned SHA matches its version comment",
    )
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    findings = Findings()
    paths = workflow_files(root)
    if not paths:
        print(f"::error::no workflow files found under {root}", file=sys.stderr)
        return 1

    pins = perms = inputs = 0
    docs: dict[Path, dict] = {}
    for path in paths:
        doc = load(path, findings)
        if doc is None:
            continue
        rel = path.relative_to(root)
        docs[rel] = doc
        pins += check_pins(rel, path.read_text(encoding="utf-8"), findings, args.offline)
        check_secrets_inherit(rel, doc, findings)
        perms += check_template_permissions(rel, doc, root, findings)
        inputs += check_template_inputs(rel, doc, root, findings)
    check_duplicate_names(docs, findings)

    for note in findings.notes:
        print(f"::notice::{note}")

    if findings.ok:
        print(
            f"OK - {len(paths)} workflow/template files parse; "
            f"{pins} write-scoped pins verified; "
            f"{perms} caller/callee permission pairs satisfied; "
            f"{inputs} passed inputs declared; "
            f"no duplicate workflow names; no structural `secrets: inherit`."
        )
        return 0

    for error in findings.errors:
        print(f"::error::{error}")
    print(
        f"\n{len(findings.errors)} problem(s) in the hub's workflows or templates. "
        f"These files are the source of truth for every caller in the ecosystem.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
