#!/usr/bin/env python3
"""
skill_drift_check.py — report `agent-skill` ↔ default-branch drift (hub issue #31, strategy §12.2).

The `agent-skill` branches are trimmed derivatives of the default branches, kept current by
porting `service/` changes forward **by hand**. Three of the five branches share no git history
with their default branch at all, so `git log`/`git merge` say nothing useful about how stale a
skill branch is. This tool answers that question directly, by content.

It is the check that would have caught the 2026-07-29 re-drift in seconds: the accretion
parameters missing from three services, the absent `atrium_document.py`, the stale
`atrium_paradata.py`, and the two-minor version lag on every branch.

Checks
------
    content   common files whose content differs, minus the expected-divergence allowlist.
              Deltas listed in DOCUMENTED_DIVERGENCES are printed as notes instead, so a
              clean run still means "nothing unexamined", not "nothing I looked at"
    missing   files under `service/` that the default branch carries and the skill branch
              does not. The content pass compares only COMMON files, which is right for the
              §5 trim but blind here — and that blind spot is what let nlp-enrich reach CI
              missing `service/healthcheck.py` while this tool called the repo clean
    runtime   modules the skill branch's own `service/` imports but does not carry (the
              service would not start), plus modules the default branch's `service/` newly
              imports that a port would have to bring along
    container the issue-#55 HEALTHCHECK. `Dockerfile` and `docker-compose*` are content-
              allowlisted for good reason, which also hid every skill branch dropping the
              healthcheck while `service/README.md` documented it as live. Satisfied by a
              Dockerfile HEALTHCHECK or a compose `healthcheck:`
    version   `para_config.txt` `[tool] version` parity — §4.6 surfaces this through `/info`,
              so a lag here means every skill branch misreports its version
    shared    byte-parity of the para-drift-guarded shared files

Exit codes: 0 clean · 1 drift found · 2 usage error. stdlib-only, like the e2e tools.

Usage
-----
    python3 tools/skill_drift_check.py                       # all repos beside the hub
    python3 tools/skill_drift_check.py --repo atrium-translator
    python3 tools/skill_drift_check.py --test-ref origin/master --quiet
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

# tools/ is this script's own directory when run as `python3 tools/skill_drift_check.py`
# (Python puts a script's own directory at sys.path[0]) -- inserted explicitly too, so a
# test importing this module from elsewhere still finds shared_manifest beside it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared_manifest import load_manifest  # noqa: E402

# Files a trimmed skill branch is *expected* to diverge on — the branch README documents
# skill installation rather than development, and the container/ignore files are retargeted.
# Everything else differing is drift worth a human's attention.
ALLOWLIST = {
    "README.md",
    "CONTRIBUTING.md",
    "Dockerfile",
    ".gitignore",
    ".dockerignore",
}
ALLOWLIST_GLOBS = ("docker-compose",)

# Files whose CONTENT is allowlisted above but which still carry one thing the skill branch
# must not silently lose. Allowlisting `Dockerfile` and `docker-compose*` wholesale is right —
# the skill images are deliberately trimmed and retargeted — but it also hid, for six weeks,
# that every skill branch had dropped the issue-#55 HEALTHCHECK while `service/README.md` went
# on documenting it as live. So the allowlist covers the diff, and this covers the contract.
#
# Satisfied by EITHER a Dockerfile HEALTHCHECK or a compose-level `healthcheck:` — the
# single-stage skill Dockerfiles start the API through a compose entrypoint override, so
# compose is the correct home for it there.
CONTAINER_CONTRACT_TOKEN = "healthcheck"
CONTAINER_CONTRACT_FILES = ("Dockerfile", "docker-compose.yml", "docker-compose.yaml")

# Divergences that are DELIBERATE and reviewed, as {(repo, path): why}. Reported as a
# separate informational line rather than counted as drift, so "0 findings" keeps meaning
# "nothing unexamined" instead of quietly widening to "nothing I chose to look at".
#
# The bar for an entry here is that the skill branch is RIGHT and the default branch has
# nothing to fix: either the file documents a branch whose §5 trim makes the default-branch
# text false, or the code is a guarded no-op that the default branch would gain nothing from.
# Anything else — including anything that would change what the service DOES — belongs in a
# port, not in this table.
DOCUMENTED_DIVERGENCES = {
    ("atrium-page-classification", "service/README.md"): (
        "the default-branch text cites setup/requirements-test.txt and "
        "tests/test_service_runtime_deps.py, both of which §5 trims from a skill branch; "
        "skill-validate step 2 fails on the first of them (2026-09-09)"
    ),
    ("atrium-translator", "service/api.py"): (
        "adds the `.exists()`-guarded /frontend StaticFiles mount, so the branch README's "
        "long-standing 'mounted at /frontend' claim is true. A no-op on any branch without "
        "service/frontend/, so it is forward-mergeable rather than a fork (2026-09-09)"
    ),
    ("atrium-llm-enrich", "service/api.py"): ("same guarded /frontend mount as atrium-translator (2026-09-09)"),
}

# Guarded byte-identical by the hub's para-drift.reusable.yml. Read from the single
# manifest (atrium-project#59) rather than a hand-maintained tuple -- the tuple this
# replaced named 5 of what was, by the time #59 was filed, 16 guarded files: three
# canonical modules (#51's atrium_vocab.py, #54's atrium_rocrate.py, #18's
# check_version.py) and six tests/test_*.py files had landed in para-drift.reusable.yml
# and scripts/revendor_shared.sh without this tuple ever being told. Loading the same
# manifest those two now also read makes that specific omission structurally
# impossible: the next file added lands here for free, or the addition is incomplete
# everywhere at once rather than silently in just this one place.
_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "docs" / "templates" / "shared" / "MANIFEST.json"
SHARED_FILES = tuple(entry["dest"] for entry in load_manifest(_MANIFEST_PATH))

REPOS = (
    "atrium-page-classification",
    "atrium-translator",
    "atrium-alto-postprocess",
    "atrium-nlp-enrich",
    "atrium-llm-enrich",
)

_VERSION_RE = re.compile(r"^\s*version\s*=\s*(\S+)", re.M)

# Tokens that look like a repo-relative script path. Matches inside Python string literals
# (`subprocess.run([..., "api_util/chunk.py"])`) and inside shell scripts (`python3
# api_util/summarize_nt_udp.py`) alike, because both are just text at this point. Callers
# intersect the result with the ref's real file list, so a false match cannot invent a
# dependency -- only a real file that is really named can enter the closure.
_SCRIPT_TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh)")

# Inline code (`x`) and fenced blocks (```...```) in markdown -- where a doc puts a command
# the reader is meant to run, as opposed to prose that merely names a file.
_CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]+`", re.S)


def git(repo: Path, *args: str) -> str:
    """Run git in `repo`; return stdout, or '' when the command fails (missing ref/path).

    Decoded leniently — some tracked blobs are binary (the KER idf pickles), and this
    tool only ever reads text out of the ones it parses.
    """
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


def tree(repo: Path, ref: str) -> dict:
    """path -> (mode, blob sha) for every file at `ref`.

    Comparing recorded SHAs rather than file contents is binary-safe, needs one git call
    per ref instead of one per file, and surfaces mode-only changes (the 100755 -> 100644
    drift on nlp-enrich) that a content diff would silently pass.
    """
    entries = {}
    for line in git(repo, "ls-tree", "-r", ref).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and len(parts) >= 3:
            entries[path] = (parts[0], parts[2])
    return entries


def blob(repo: Path, ref: str, path: str) -> str:
    return git(repo, "show", f"{ref}:{path}")


def allowlisted(path: str) -> bool:
    return path in ALLOWLIST or any(path.startswith(g) for g in ALLOWLIST_GLOBS)


def _catches_import_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    caught = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(isinstance(node, ast.Name) and node.id in {"ImportError", "ModuleNotFoundError"} for node in caught)


def _module_index(files: set) -> dict:
    """Importable dotted name -> repo-relative .py path, for every module in `files`.

    Packages are indexed under the package name (`api_util/__init__.py` -> `api_util`)
    so `from api_util import x` and `import api_util.x` both resolve. Before this
    existed the closure only knew ROOT modules (`"/" not in f`), which is why a package
    submodule could go missing from a skill branch and be reported nowhere — see
    `runtime_closure`.
    """
    index = {}
    for path in files:
        if not path.endswith(".py"):
            continue
        parts = path[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
            if not parts:
                continue
        index[".".join(parts)] = path
    return index


def _resolve_module(name: str, index: dict) -> str:
    """The file providing dotted `name`, by longest-prefix match, or "".

    `from api_util.document_hook import run_document_hook` yields the dotted name
    `api_util.document_hook`; `from atrium_document import X` yields `atrium_document`.
    Trailing components that are objects rather than modules are trimmed off.
    """
    parts = name.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in index:
            return index[candidate]
        parts.pop()
    return ""


def _absolute_name(module: str, level: int, source_path: str) -> str:
    """Resolve a relative import to an absolute dotted name.

    `from .llm_translator import LLMTranslator` inside `processors/backend.py` (level 1)
    is `processors.llm_translator`. Relative imports used to be skipped outright
    (`and not node.level`), which is why translator's `processors/` chain — reached only
    through relative imports inside a lazy registry function — looked unreachable.
    """
    if not level:
        return module  # already absolute -- `from typing import Any` is not `service.typing`
    package = source_path.rsplit("/", 1)[0].split("/") if "/" in source_path else []
    if level > 1:
        package = package[: -(level - 1)] if level - 1 <= len(package) else []
    return ".".join([*package, module]) if module else ".".join(package)


# Directories §5 trims from EVERY skill branch by design. A file under one of these can
# never be a runtime dependency of the service, so a reference reaching into one is prose
# (a docstring citing a test, a comment naming a helper script), not a dependency. Without
# this, `service/*.py` docstrings that mention `tests/test_service_api.py` dragged the whole
# test suite into the closure and every repo reported dozens of "missing" files.
_NEVER_RUNTIME = ("tests/", "tools/", "data_scripts/", "supplementary/")

# Closure ROOTS beyond `service/**.py`. §6 makes `scripts/atrium_<verb>.py` the only thing
# the agent actually executes, and §7's SKILL.md is what tells it to; a file those name is
# as load-bearing as one `service/api.py` imports. Adding them caught llm-enrich's
# `api_util/layout_md.py`: `SKILL.md:130` tells the agent to run `api_util/xml_to_md.py`,
# that file is ON the branch, it imports `layout_md` at `:31`, and `layout_md` is NOT --
# a documented, user-facing break invisible to a service/-only walk.
_ROOT_DOCS = ("SKILL.md", "README.md", "service/README.md")


def _is_runtime_path(path: str) -> bool:
    return not path.startswith(_NEVER_RUNTIME)


def _is_namespace_package(dotted: str, files: set) -> bool:
    """True when `dotted` is a repo-local directory carrying no `__init__.py` on this ref."""
    prefix = dotted.replace(".", "/") + "/"
    return any(f.startswith(prefix) for f in files) and f"{prefix}__init__.py" not in files


def _local_prefixes(files: set) -> set:
    """Top-level names that are repo-local: root modules and package directories.

    Used to tell "this import failed to resolve because it is third-party" (numpy) from
    "this import failed to resolve because the file is MISSING" (api_util.document_hook on
    a branch that dropped it). Only the second is a finding.
    """
    prefixes = set()
    for path in files:
        head, _, tail = path.partition("/")
        prefixes.add(head[:-3] if not tail and head.endswith(".py") else head)
    return prefixes


def _docstring_ids(module: ast.AST) -> set:
    """Node ids of every docstring Constant, so prose can be excluded from script scanning."""
    ids = set()
    for node in ast.walk(module):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            if isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def _script_refs_py(module: ast.AST) -> set:
    """Script paths named in real STRING LITERALS of a parsed Python module.

    Scanning raw source text instead would read comments and docstrings as dependencies.
    That is not theoretical: translator's `processors/backend.py:83-87` documents a
    deliberately-unregistered backend in a comment —

        # processors/ct2_translator.py.  It is intentionally NOT registered by
        # from .ct2_translator import CT2Translator

    — and a text scan reported that file as a missing runtime dependency of the skill
    branch, which is the exact opposite of what the comment says. Docstrings are excluded
    for the same reason: a module docstring citing `tests/test_service_api.py` is prose.
    """
    docstrings = _docstring_ids(module)
    found = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in docstrings:
            continue
        # The WHOLE string must be the path. A path mentioned inside a sentence is prose,
        # not an invocation -- atrium_document.py:1038 raises
        #   f"(scripts/revendor_shared.sh); para-drift expects the pair to travel together."
        # which named a hub maintenance script as a runtime dependency of five skill
        # branches. `_RUN_PIPELINE = _REPO_ROOT / "run_pipeline.py"` still counts, which is
        # the form the real subprocess call sites use.
        candidate = node.value.strip()
        if _SCRIPT_TOKEN_RE.fullmatch(candidate):
            found.add(candidate)
    return found


def _script_refs_sh(text: str) -> set:
    """Script paths a shell script execs, ignoring comment lines.

    Import analysis cannot see `python3 api_util/summarize_nt_udp.py`. nlp-enrich's whole
    batch path is exactly that shape — `service/enrichment.py` execs `run_pipeline.py`,
    which execs `api_1_manifest.sh`..`api_4_stats.sh`, which exec `api_util/*.py` — so
    without this the closure stops at the first `subprocess` call and calls the rest
    unreachable.
    """
    live = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    return set(_SCRIPT_TOKEN_RE.findall("\n".join(live)))


def _references_of(repo: Path, ref: str, path: str, index: dict, files: set, local: set):
    """(resolved paths, referenced-but-absent paths) for one file.

    The second element is the half that was missing until 2026-09-16: `_module_index` is
    built from files that EXIST, so an unresolvable import used to vanish silently. A
    reference counts as absent only when it is unambiguously repo-local — its first
    component is a root module or a package directory on this ref — so a third-party
    import (`torch`, `numpy`) is never reported.
    """
    text = blob(repo, ref, path)
    resolved, absent = set(), set()

    def classify(tokens: set) -> None:
        for token in tokens:
            if token in files:
                resolved.add(token)
            elif "/" in token and token.split("/", 1)[0] in local:
                absent.add(token)

    if not path.endswith(".py"):
        classify(_script_refs_sh(text))
        return resolved, absent  # a shell script contributes only what it execs

    try:
        module = ast.parse(text)
    except (SyntaxError, ValueError):
        return resolved, absent

    classify(_script_refs_py(module))

    optional = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Try) and any(_catches_import_error(h) for h in node.handlers):
            optional.update(
                id(child)
                for stmt in node.body
                for child in ast.walk(stmt)
                if isinstance(child, (ast.Import, ast.ImportFrom))
            )

    # `declared` are modules the source really names, so an unresolvable one is a MISSING
    # file. `probes` are speculative — in `from pkg import a, b`, each of a/b might be a
    # submodule or might be a class — so they may resolve but must never report an absence,
    # or every `from typing import Any` would invent a missing typing/Any.py.
    declared, probes = set(), set()
    for node in ast.walk(module):
        if id(node) in optional:
            continue
        if isinstance(node, ast.Import):
            declared.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _absolute_name(node.module or "", node.level, path)
            if not base:
                continue
            declared.add(base)
            probes.update(f"{base}.{alias.name}" for alias in node.names)

    for name in declared | probes:
        target = _resolve_module(name, index)
        if target:
            resolved.add(target)
            continue
        if name.split(".")[0] not in local:
            continue  # third-party or stdlib -- not our problem
        if "." not in name:
            # A bare repo-local root module that did not resolve: `from main import ...`
            # where main.py is not on this ref. A name that is a DIRECTORY is excluded --
            # `from api_util import layout_md` names the package, and `api_util.py` is not
            # a file that was ever supposed to exist; the missing submodule is reported by
            # the namespace-package rule below instead.
            is_package_dir = any(f.startswith(f"{name}/") for f in files)
            if name in declared and not is_package_dir:
                absent.add(f"{name}.py")
            continue
        if name in declared:
            # Repo-local package, unresolvable submodule -> the file is not on this ref.
            absent.add(name.replace(".", "/") + ".py")
        elif _is_namespace_package(name.rsplit(".", 1)[0], files):
            # A probe from `from pkg import x`. Normally x might be a class defined in
            # pkg/__init__.py, so an unresolvable probe proves nothing -- otherwise every
            # `from typing import Any` would invent typing/Any.py. But when pkg has NO
            # __init__.py it is a namespace package, so `x` can ONLY be a submodule, and
            # its absence is a real missing file. That is llm-enrich exactly:
            # `from api_util import layout_md` in api_util/xml_to_md.py:31, api_util/ has
            # no __init__.py, and layout_md.py is not on the branch -- while SKILL.md:130
            # tells the agent to run xml_to_md.py.
            absent.add(name.replace(".", "/") + ".py")

    return resolved, absent


def _walk_closure(repo: Path, ref: str, files: set, universe: set = None):
    """(needed paths, referenced-but-absent paths), from `service/**.py` outward.

    One level is not enough: translator's `service/api.py` never imports `atrium_document`
    itself, but the `main.py` it calls does — so a one-level scan would report the skill
    branch as complete while the ported service still fails at runtime.

    Works in PATHS rather than root-module names (it used names until 2026-09-16). The old
    shape could represent neither a package submodule nor a shell script, so three
    genuinely missing files sat on skill branches with every check green:

      * nlp-enrich   `api_util/validate_teitok_xml.py` — exec'd by `api_4_stats.sh`
      * nlp-enrich   `api_util/document_hook.py`       — imported by `api_util/summarize_nt_udp.py`
      * llm-enrich   `api_util/layout_md.py`           — imported by `api_util/xml_to_md.py`,
                                                         which that branch's SKILL.md tells the
                                                         agent to run

    That is the same failure mode as the `service/healthcheck.py` incident this module's
    docstring cites, one directory over.
    """
    index = _module_index(files)
    # "Repo-local" is decided against the UNION of both refs, not this ref alone. A module
    # deleted from the skill branch is repo-local by evidence of the default branch, and
    # that is precisely the drift worth reporting -- judged from `files` alone, a missing
    # root module like `main.py` is indistinguishable from a third-party import and was
    # silently skipped.
    local = _local_prefixes(files if universe is None else files | universe)
    pending = {f for f in files if f.startswith("service/") and f.endswith(".py")}
    pending |= {f for f in files if f.startswith("scripts/") and f.endswith((".py", ".sh"))}
    for doc in _ROOT_DOCS:
        if doc not in files:
            continue
        # Only backticked spans: markdown prose names files constantly, but a command the
        # reader is told to RUN is written as code. SKILL.md:130's
        # "with `api_util/xml_to_md.py` first" is the shape that matters.
        for span in _CODE_SPAN_RE.findall(blob(repo, ref, doc)):
            pending |= {token for token in _SCRIPT_TOKEN_RE.findall(span) if token in files and _is_runtime_path(token)}

    needed, absent, seen = set(), set(), set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        if not path.startswith(("service/", "scripts/")):
            # service/ and scripts/ are roots, checked by the `missing` family and by
            # skill-validate's referenced-path step respectively.
            needed.add(path)
        found, gone = _references_of(repo, ref, path, index, files, local)
        absent |= {g for g in gone if _is_runtime_path(g)}
        pending |= {f for f in found if _is_runtime_path(f)} - seen
    return needed, absent


def runtime_closure(repo: Path, ref: str, files: set, universe: set = None) -> set:
    """Repo-relative file paths the service needs at runtime. See `_walk_closure`."""
    return _walk_closure(repo, ref, files, universe)[0]


def missing_references(repo: Path, ref: str, files: set, universe: set = None) -> set:
    """Repo-local files the service REFERENCES but this ref does not carry."""
    return _walk_closure(repo, ref, files, universe)[1]


def version_of(repo: Path, ref: str, files: set) -> str:
    for candidate in ("para_config.txt", "setup/para_config.txt"):
        if candidate in files:
            match = _VERSION_RE.search(blob(repo, ref, candidate))
            if match:
                return match.group(1)
    return "?"


def check_repo(repo: Path, test_ref: str, skill_ref: str, quiet: bool) -> list:
    """Return (findings, notes) for one repo — empty findings == clean.

    `notes` carries the reviewed, deliberate divergences, which are shown but do not make
    the repo drifted; `findings` is what a human still has to act on.
    """
    findings, notes = [], []
    test_tree, skill_tree = tree(repo, test_ref), tree(repo, skill_ref)
    if not test_tree or not skill_tree:
        return [f"cannot resolve {test_ref} and/or {skill_ref} — fetch them first"], notes
    test_files, skill_files = set(test_tree), set(skill_tree)

    # --- content: common files that differ -----------------------------------------------
    differing, mode_only, documented = [], [], []
    for path in sorted(test_files & skill_files):
        if allowlisted(path):
            continue
        (test_mode, test_sha), (skill_mode, skill_sha) = test_tree[path], skill_tree[path]
        if test_sha != skill_sha:
            reason = DOCUMENTED_DIVERGENCES.get((repo.name, path))
            (documented if reason else differing).append(path if not reason else (path, reason))
        elif test_mode != skill_mode:
            mode_only.append(f"{path} ({skill_mode} vs {test_mode})")
    if differing:
        findings.append(f"{len(differing)} common file(s) differ from {test_ref}:")
        findings += [f"    {path}" for path in differing]
    notes.extend(f"{path} — {reason}" for path, reason in documented)
    if mode_only:
        findings.append("file-mode drift: " + ", ".join(mode_only))

    # --- service/ files present on the default branch and absent here ---------------------
    # The content pass above compares only files COMMON to both refs, which is right for the
    # §5 trim (tests/, lint configs and the rest are meant to be gone) but blind in one place:
    # a file under service/ is by definition part of the service, so its absence is a gap
    # rather than a trim. That blind spot is not hypothetical — nlp-enrich reached CI missing
    # `service/healthcheck.py` while its own `service/README.md` cited the file, and this tool
    # reported the repo as clean. Directories the trim legitimately removes are excluded.
    missing_service = sorted(
        path
        for path in test_files - skill_files
        if path.startswith("service/") and not path.startswith("service/test") and Path(path).name != "__init__.py"
    )
    if missing_service:
        findings.append(
            "service/ file(s) on " + test_ref + " that the skill branch does not carry: " + ", ".join(missing_service)
        )

    # --- container contract ---------------------------------------------------------------
    if any(path in test_files for path in CONTAINER_CONTRACT_FILES):
        declared_on_test = any(
            CONTAINER_CONTRACT_TOKEN in blob(repo, test_ref, path).lower()
            for path in CONTAINER_CONTRACT_FILES
            if path in test_files
        )
        declared_on_skill = any(
            CONTAINER_CONTRACT_TOKEN in blob(repo, skill_ref, path).lower()
            for path in CONTAINER_CONTRACT_FILES
            if path in skill_files
        )
        if declared_on_test and not declared_on_skill:
            findings.append(
                "issue-#55 container contract lost: " + test_ref + " declares a HEALTHCHECK "
                "and the skill branch declares none, in the Dockerfile or in compose"
            )

    # --- runtime closure -----------------------------------------------------------------
    # `runtime_closure` returns repo-relative PATHS (2026-09-16), so a package submodule or
    # an exec'd script is representable. Both loops below compare paths directly; the old
    # `f"{name}.py"` reconstruction could only ever express a root module.
    skill_needed, skill_absent = _walk_closure(repo, skill_ref, skill_files, universe=test_files)
    missing_now = sorted({path for path in skill_needed if path not in skill_files} | skill_absent)
    if missing_now:
        findings.append(
            "skill branch references files it does not carry (the skill is broken as shipped): "
            + ", ".join(missing_now)
        )

    port_closure = runtime_closure(repo, test_ref, test_files)
    missing_after_port = sorted(path for path in port_closure if path not in skill_files and path not in missing_now)
    if missing_after_port:
        findings.append(
            "a port of the default-branch service/ would additionally need: " + ", ".join(missing_after_port)
        )

    # --- version -------------------------------------------------------------------------
    test_version = version_of(repo, test_ref, test_files)
    skill_version = version_of(repo, skill_ref, skill_files)
    if test_version != skill_version:
        findings.append(f"version lag (§4.6, surfaced by /info): skill {skill_version} vs {test_ref} {test_version}")

    # --- shared files --------------------------------------------------------------------
    # Present on both: must be byte-identical, since para-drift guards them on the default
    # branch. Absent from the skill branch: only a defect when the service actually needs it
    # — dev-only members of the set (para_licenses.py) are legitimately trimmed by §5.
    #
    # Going from 5 entries to 16 (atrium-project#59) walked in two shapes the original
    # `removesuffix(".py") in port_closure or path.startswith("service/")` test cannot
    # see, and would silently have called both "needed" and "absent" for:
    #   - a `.schema.json` file: `.removesuffix(".py")` is a no-op on it and it is never
    #     under `service/`, so the absence branch could NEVER fire -- its owning module
    #     (atrium_document.schema.json -> atrium_document) is what determines whether the
    #     service needs it, checked against port_closure the same way a .py module is.
    #   - a `tests/test_*.py` entry: skill_ify.py's own TRIM_DIRS trims `tests/` from
    #     EVERY skill branch by design (§5), so its absence must never be a finding --
    #     unlike the .py/.schema.json cases above, there is no "needed" test for these,
    #     only the parity check when a copy happens to exist on both refs.
    for path in SHARED_FILES:
        on_test, on_skill = path in test_files, path in skill_files
        if on_test and on_skill:
            if test_tree[path][1] != skill_tree[path][1]:
                findings.append(f"para-drift-guarded file out of parity: {path}")
            continue
        if not on_test:
            continue
        if path.startswith("tests/"):
            continue
        if path.endswith(".schema.json"):
            # A schema is never imported; its OWNING module decides whether the service
            # needs it (atrium_document.schema.json -> atrium_document.py).
            needed = f"{path[: -len('.schema.json')]}.py" in port_closure
        else:
            needed = path in port_closure or path.startswith("service/")
        if needed:
            findings.append(f"para-drift-guarded file needed by the service but absent: {path}")

    return findings, notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report agent-skill ↔ default-branch drift (strategy §12.2).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="directory holding the tool repo clones (default: the hub's parent)",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        metavar="NAME",
        help="check only this repo (repeatable; default: all five service repos)",
    )
    parser.add_argument("--test-ref", default="origin/test", help="default-branch ref (default: origin/test)")
    parser.add_argument("--skill-ref", default="origin/agent-skill", help="skill ref (default: origin/agent-skill)")
    parser.add_argument("--quiet", action="store_true", help="print only repos with drift")
    args = parser.parse_args()

    drifted = 0
    checked = 0
    for name in args.repos or REPOS:
        repo = args.repos_root / name
        if not (repo / ".git").exists():
            print(f"[skill-drift][SKIP] {name}: no clone at {repo}")
            continue
        checked += 1
        findings, notes = check_repo(repo, args.test_ref, args.skill_ref, args.quiet)
        if findings:
            drifted += 1
            print(f"\n[skill-drift][DRIFT] {name}")
            for line in findings:
                print(f"  - {line}" if not line.startswith("    ") else line)
        elif not args.quiet:
            print(f"[skill-drift][OK]    {name}: aligned with {args.test_ref}")
        for note in notes:
            print(f"  · documented divergence: {note}")

    if not checked:
        print("[skill-drift][FAIL] no repo clones found — pass --repos-root", file=sys.stderr)
        return 2
    print(f"\n[skill-drift] {checked - drifted}/{checked} repos aligned")
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
