"""tests/test_pages_exclude.py — the fences around the legacy Pages build, checked
rather than trusted (atrium-project#57).

GitHub Pages for this repository is set to "Deploy from a branch", so GitHub's
built-in `pages-build-deployment` job runs the legacy Jekyll builder over whatever
folder the dropdown names. That job is not a workflow file here and cannot be edited;
the only lever over what it publishes is an `exclude:` list in the `_config.yml`
BESIDE THE SOURCE.

WHY THERE ARE TWO CONFIGS. The folder setting moved twice in one day:

  * 2026-09-21, run 35582651532 — source `./docs`. Failed on a Liquid syntax error at
    docs/docker_gha_roadmap.md:79. Fenced by `docs/_config.yml`.
  * 2026-09-21, run 35612083327 — source `.` (the repository root). `Configuration
    file: none` — Jekyll looks for `_config.yml` beside the source, so the docs-scoped
    fence stopped being read the moment the dropdown changed, and the blast radius
    went from two files to the entire repository.

So both exist, neither depends on the other, and this file checks both. Whichever way
the dropdown is set, one of them is the fence and the other is inert.

WHAT THE FENCES ARE HOLDING BACK. github-pages enables `jekyll-optional-front-matter`,
which makes every front-matter-less `.md` a rendered page, and Jekyll runs Liquid over
ALL markdown including inside fenced code blocks and code spans — so quoting a GitHub
Actions expression is enough to kill the build. Both failures were doing real work: a
GREEN build from either source publishes files carrying email addresses, and under the
root source it also publishes all 79 files of `agent_dev_logs/`, several of which are
open memos addressed to named individuals. Nothing was published only because the
builds crashed. That is an accident, not a safeguard.

WHY A TEST AND NOT JUST THE LISTS. A hand-written exclusion list is exactly the shape
#59 spent a round eliminating: "a guardrail cannot see what it is supposed to hold."
Someone adding a new top-level file gets it published by default, silently. So the
checks are BIDIRECTIONAL — every entry in a config names something that exists, and
everything that exists is either excluded or on the reviewed allow-list. Neither
direction alone is enough.

The two content checks are the ones that would actually have caught these incidents:
no publishable file may carry a Liquid construct (that is the crash), and none may
carry a partner address (that is the leak).

SCOPING, DELIBERATELY. The address check tests the two ARUP/ARUB domains, not "any
email address anywhere". 57.plan.md section F makes the point: all five tool READMEs
and CONTRIBUTING files carry a maintainer contact address and are published on
purpose, so a blanket assertion fails on day one against content that is public by
design, and a test that fails for the wrong reason gets disabled.

THESE GUARD STOPGAPS. Both configs should be deleted, not maintained, once an owner
points Settings -> Pages at `gh-pages` / `/ (root)`; the real site is built from
`docs_site/` by `.github/workflows/pages.yml`. Delete this file with them.

Run: pytest tests/test_pages_exclude.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

ROOT_CONFIG = REPO_ROOT / "_config.yml"
DOCS_CONFIG = DOCS / "_config.yml"

# The ONLY thing the root-source build may publish. README.md is already public on the
# repository page, and `jekyll-readme-index` turns it into the site index, so
# https://ufal.github.io/atrium-project/ serves something true instead of a 404.
# Verified 2026-09-21: zero Liquid constructs, zero email addresses.
ROOT_PUBLISHABLE = {"README.md"}

# What the docs-source build may publish, for the case where the folder is set back to
# /docs. Adding a row to either set is a review decision: it puts that file on the
# public web.
DOCS_PUBLISHABLE = {
    "agent_skill_strategy.md",
    "document_schema.md",
    "k8s_acceptance_runbook.md",
    "k8s_deployment.md",
    "paradata_schema.md",
    "rocrate_export.md",
    "skill_acceptance_runbook.md",
    "skills_catalog.md",
    "skos_strategy.md",
}

# Jekyll skips entries beginning with `.` or `_` on its own (Jekyll::EntryFilter#special?),
# which is why `.github/`, `.gitignore` and `_generators/` are absent from both exclude
# lists — and why neither config needs to exclude itself.
JEKYLL_SKIPS = (".", "_")

# Liquid's two constructs. Jekyll applies them to fenced code and code spans alike,
# which is the whole reason this repository's own documentation broke the build.
LIQUID = re.compile(r"\{\{|\{%")

# The ARUP/ARUB partner domains, per docs/arub-p_contacts.md. NOT a general address
# pattern -- see the module docstring.
PARTNER_ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@(?:arub\.cz|arup\.cas\.cz)", re.I)

# (config path, the directory it fences, the reviewed allow-list for that source)
FENCES = [
    pytest.param(ROOT_CONFIG, REPO_ROOT, ROOT_PUBLISHABLE, id="root"),
    pytest.param(DOCS_CONFIG, DOCS, DOCS_PUBLISHABLE, id="docs"),
]

# Every file either fence may publish, as (config-relative) paths from the repo root.
ALL_PUBLISHABLE = sorted({f"{n}" for n in ROOT_PUBLISHABLE} | {f"docs/{n}" for n in DOCS_PUBLISHABLE})


def _excluded(config: Path) -> list[str]:
    data = yaml.safe_load(config.read_text())
    assert isinstance(data, dict), f"{config} must parse to a mapping, got {type(data)}"
    excluded = data.get("exclude")
    assert excluded, (
        f"{config} has no non-empty `exclude:` list. An empty fence is worse than no "
        f"fence -- it looks like protection and provides none."
    )
    return excluded


def _visible(directory: Path) -> set[str]:
    """Names Jekyll would consider in the Pages checkout.

    TRACKED FILES ONLY, and the distinction is load-bearing rather than pedantic. The
    Pages builder runs over a fresh clone of the branch, so a gitignored build artifact
    is not there -- but it IS in a contributor's working tree. Reading the filesystem
    directly made this test fail locally on `site/` (mkdocs output) and `stubs/`
    (make_stubs.py output) while passing in CI, which is the worst of both: noise for
    whoever runs it, and no extra safety. `git ls-files` is what the builder sees.

    Entries beginning with `.` or `_` are dropped because Jekyll skips them itself
    (Jekyll::EntryFilter#special?), which is also why neither config excludes itself.
    """
    out = subprocess.run(["git", "ls-files", "-z"], cwd=directory, capture_output=True, text=True, check=True).stdout
    top = {entry.split("/", 1)[0] for entry in out.split("\0") if entry}
    return {name for name in top if not name.startswith(JEKYLL_SKIPS)}


@pytest.mark.parametrize("config, directory, publishable", FENCES)
def test_the_fence_exists(config, directory, publishable):
    assert config.is_file(), (
        f"{config.relative_to(REPO_ROOT)} is missing. While GitHub Pages deploys this "
        f"repository from a branch, the `_config.yml` beside the source folder is the "
        f"only thing stopping the legacy Jekyll build from publishing the internal "
        f"tree. Both folder settings have been used in one day, so both fences stay "
        f"until Pages is moved to the gh-pages branch -- then delete both and this test."
    )


@pytest.mark.parametrize("config, directory, publishable", FENCES)
def test_every_exclusion_names_something_that_exists(config, directory, publishable):
    """An exclusion for a renamed or deleted path is a fence with a hole in it."""
    missing = [e for e in _excluded(config) if not (directory / e).exists()]
    assert not missing, (
        f"{config.relative_to(REPO_ROOT)} excludes {missing}, which no longer exist. "
        f"A stale entry is silently vacuous: if the path was renamed, the new name is "
        f"being published right now."
    )


@pytest.mark.parametrize("config, directory, publishable", FENCES)
def test_everything_visible_is_excluded_or_reviewed(config, directory, publishable):
    """The other direction: nothing reaches the site without a decision."""
    unaccounted = _visible(directory) - set(_excluded(config)) - publishable
    assert not unaccounted, (
        f"{sorted(unaccounted)} in {directory.relative_to(REPO_ROOT) or '.'} is neither "
        f"excluded by {config.relative_to(REPO_ROOT)} nor on its reviewed allow-list, so "
        f"the legacy Pages build would publish it by default. Decide: add it to the "
        f"exclude list, or add it to the allow-list here after checking it carries no "
        f"internal content, no Liquid and no address."
    )


@pytest.mark.parametrize("config, directory, publishable", FENCES)
def test_the_allow_list_is_real(config, directory, publishable):
    """An allow-list must not accumulate names of files that are gone."""
    ghosts = [name for name in publishable if not (directory / name).is_file()]
    assert not ghosts, f"{sorted(ghosts)} is allow-listed but does not exist in {directory}."


def test_the_root_fence_withholds_the_two_trees_that_matter():
    """Belt and braces: these two are why the root fence exists at all.

    `agent_dev_logs/` is 79 files of internal chronology -- issue exports, open memos
    to named individuals, and three files carrying email addresses. `docs/` is the
    canonical internal tree. Neither is publishable under any dropdown setting.
    """
    excluded = set(_excluded(ROOT_CONFIG))
    for name in ("agent_dev_logs", "docs"):
        assert name in excluded, (
            f"{name}/ must stay excluded by the root _config.yml. Under the `/ (root)` "
            f"Pages folder it would otherwise be published in full."
        )


def test_the_three_sensitive_docs_are_excluded_by_name():
    """The same, for the docs fence."""
    excluded = set(_excluded(DOCS_CONFIG))
    for name, why in (
        ("arub-p_contacts.md", "five ARUP/ARUB partner email addresses"),
        ("plan_repo_review.md", "a personal email address"),
        ("docker_gha_roadmap.md", "a 97 KB internal roadmap, and a fatal Liquid construct"),
    ):
        assert name in excluded, f"docs/{name} must stay excluded -- it carries {why}."


@pytest.mark.parametrize("relpath", ALL_PUBLISHABLE)
def test_no_publishable_file_carries_a_liquid_construct(relpath):
    """The crash, as a regression test.

    `{{ ... }}` or `{% ... %}` anywhere in a published file is either a fatal parse
    error (when a `}` appears inside, as in `format('-{0}', ...)`) or a silent
    substitution to the empty string. Both ship something wrong.
    """
    hits = [
        f"{i}: {ln.strip()[:90]}"
        for i, ln in enumerate((REPO_ROOT / relpath).read_text().splitlines(), 1)
        if LIQUID.search(ln)
    ]
    assert not hits, (
        f"{relpath} carries Liquid constructs that the legacy Pages build will "
        f"interpret:\n  " + "\n  ".join(hits) + "\n"
        "Jekyll renders Liquid inside fenced code blocks and code spans too, so quoting "
        "a GitHub Actions expression is enough. Either exclude this file or move the "
        "snippet out of the published set."
    )


@pytest.mark.parametrize("relpath", ALL_PUBLISHABLE)
def test_no_publishable_file_carries_a_partner_address(relpath):
    """The leak, as a regression test."""
    found = PARTNER_ADDRESS.findall((REPO_ROOT / relpath).read_text())
    assert not found, (
        f"{relpath} carries {len(found)} ARUP/ARUB partner address(es) and is "
        f"allow-listed for publication. Move it to the relevant _config.yml exclude list."
    )
