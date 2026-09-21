"""tests/test_docs_pages_exclude.py — the fence around the legacy Pages build,
checked rather than trusted (atrium-project#57).

GitHub Pages for this repository is set to "Deploy from a branch: main / /docs", so
GitHub's built-in `pages-build-deployment` job runs the legacy Jekyll builder over
`docs/` — this repository's CANONICAL INTERNAL TREE, not a docs site. That job is not
a workflow file here and cannot be edited; the only lever over what it publishes is
`docs/_config.yml`'s `exclude:` list.

WHAT WENT WRONG WITHOUT IT. Run 35582651532 failed on a Liquid syntax error at
`docs/docker_gha_roadmap.md:79` — github-pages enables `jekyll-optional-front-matter`,
which makes every front-matter-less `.md` a rendered page, and Jekyll runs Liquid over
ALL markdown including inside fenced code blocks and code spans, so a quoted GitHub
Actions expression is parsed as a template variable. The failure was doing real work:
the build log reaches `Rendering: arub-p_contacts.md` — FIVE ARUP/ARUB PARTNER EMAIL
ADDRESSES — and dies four files later. Nothing was published only because the build
crashed. Fixing the Liquid without the exclusion list would have turned the build
green and put the contact list on the public web.

WHY A TEST AND NOT JUST THE LIST. A hand-written exclusion list is exactly the shape
#59 spent a round eliminating: "a guardrail cannot see what it is supposed to hold."
Someone adding `docs/new_internal_note.md` gets it published by default, silently, and
nothing says otherwise. So the check below is BIDIRECTIONAL — every entry in
docs/_config.yml names something that exists, and everything that exists under docs/
is either excluded or on the reviewed allow-list. Neither direction alone is enough.

The two content checks are the ones that would actually have caught this incident:
no publishable file may carry a Liquid construct (that is the crash), and none may
carry a partner address (that is the leak).

SCOPING, DELIBERATELY. `test_no_publishable_doc_carries_a_partner_address` checks the
two ARUP/ARUB domains, not "any email address anywhere". 57.plan.md section F makes
the point: all five tool READMEs and CONTRIBUTING files carry a maintainer contact
address and are published on purpose, so a blanket assertion fails on day one against
content that is public by design, and a test that fails for the wrong reason gets
disabled. This file only ever looks at `docs/`, where today no publishable file
carries an address of any kind.

THIS GUARDS A STOPGAP. `docs/_config.yml` should be deleted, not maintained, once an
owner points Settings -> Pages at `gh-pages` / `/ (root)`; the real site is built from
`docs_site/` by `.github/workflows/pages.yml`. Delete this file with it.

Run: pytest tests/test_docs_pages_exclude.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
CONFIG = DOCS / "_config.yml"

# Everything under docs/ that the legacy build MAY publish. Adding a row here is a
# review decision: it puts that file on the public web at
# https://ufal.github.io/atrium-project/<name>.html for as long as Pages points at
# main / /docs. Verified 2026-09-21: none carries a Liquid construct or an address.
PUBLISHABLE = {
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

# Jekyll never publishes its own config.
NOT_CONTENT = {"_config.yml"}

# Liquid's two constructs. Jekyll applies them to fenced code and code spans alike,
# which is the whole reason this repository's CI documentation broke the build.
LIQUID = re.compile(r"\{\{|\{%")

# The ARUP/ARUB partner domains, per docs/arub-p_contacts.md. NOT a general address
# pattern -- see the module docstring.
PARTNER_ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@(?:arub\.cz|arup\.cas\.cz)", re.I)


def _excluded() -> list[str]:
    data = yaml.safe_load(CONFIG.read_text())
    assert isinstance(data, dict), f"{CONFIG} must parse to a mapping, got {type(data)}"
    excluded = data.get("exclude")
    assert excluded, (
        f"{CONFIG} has no non-empty `exclude:` list. An empty fence is worse than no "
        f"fence -- it looks like protection and provides none."
    )
    return excluded


def _top_level() -> set[str]:
    """Names directly under docs/, as Jekyll's `exclude` addresses them."""
    return {p.name for p in DOCS.iterdir() if not p.name.startswith(".")} - NOT_CONTENT


def test_config_exists_while_pages_points_at_docs():
    assert CONFIG.is_file(), (
        "docs/_config.yml is missing. While GitHub Pages is set to main / /docs, it is "
        "the only thing stopping the legacy Jekyll build from publishing this "
        "repository's internal tree -- including five partner email addresses. If Pages "
        "has been moved to gh-pages / (root), delete this test with the config."
    )


def test_every_exclusion_names_something_that_exists():
    """An exclusion for a renamed or deleted file is a fence with a hole in it."""
    missing = [e for e in _excluded() if not (DOCS / e).exists()]
    assert not missing, (
        f"docs/_config.yml excludes {missing}, which no longer exist under docs/. "
        f"A stale entry is silently vacuous: if the file was renamed, the new name is "
        f"being published right now."
    )


def test_everything_under_docs_is_excluded_or_reviewed():
    """The other direction: nothing reaches the site without a decision."""
    unaccounted = _top_level() - set(_excluded()) - PUBLISHABLE
    assert not unaccounted, (
        f"{sorted(unaccounted)} under docs/ is neither excluded by docs/_config.yml nor "
        f"listed in PUBLISHABLE here, so the legacy Pages build would publish it by "
        f"default. Decide: add it to the exclude list, or add it to PUBLISHABLE after "
        f"checking it carries no internal content, no Liquid and no address."
    )


def test_publishable_set_is_real():
    """PUBLISHABLE must not accumulate names of files that are gone."""
    ghosts = [name for name in PUBLISHABLE if not (DOCS / name).is_file()]
    assert not ghosts, f"PUBLISHABLE names {ghosts}, which do not exist under docs/."


@pytest.mark.parametrize("name", sorted(PUBLISHABLE))
def test_no_publishable_doc_carries_a_liquid_construct(name):
    """The crash, as a regression test.

    `{{ ... }}` or `{% ... %}` anywhere in a published file is either a fatal parse
    error (when a `}` appears inside, as in `format('-{0}', ...)`) or a silent
    substitution to the empty string. Both ship something wrong.
    """
    hits = [
        f"{i}: {ln.strip()[:90]}" for i, ln in enumerate((DOCS / name).read_text().splitlines(), 1) if LIQUID.search(ln)
    ]
    assert not hits, (
        f"docs/{name} carries Liquid constructs that the legacy Pages build will "
        f"interpret:\n  " + "\n  ".join(hits) + "\n"
        "Jekyll renders Liquid inside fenced code blocks and code spans too, so quoting "
        "a GitHub Actions expression is enough. Either exclude this file in "
        "docs/_config.yml or move the snippet out of the published set."
    )


@pytest.mark.parametrize("name", sorted(PUBLISHABLE))
def test_no_publishable_doc_carries_a_partner_address(name):
    """The leak, as a regression test."""
    found = PARTNER_ADDRESS.findall((DOCS / name).read_text())
    assert not found, (
        f"docs/{name} carries {len(found)} ARUP/ARUB partner address(es) and is on the "
        f"PUBLISHABLE list. Move it to docs/_config.yml's exclude list."
    )


def test_the_three_sensitive_files_are_excluded_by_name():
    """Belt and braces: these three are why the fence exists at all."""
    excluded = set(_excluded())
    for name, why in (
        ("arub-p_contacts.md", "five ARUP/ARUB partner email addresses"),
        ("plan_repo_review.md", "a personal email address"),
        ("docker_gha_roadmap.md", "a 97 KB internal roadmap, and the fatal Liquid"),
    ):
        assert name in excluded, f"docs/{name} must stay excluded -- it carries {why}."
