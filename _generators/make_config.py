#!/usr/bin/env python3
"""Generate mkdocs.yml, docs/site.yml, PAGES_SETUP.md and the site stylesheet.

`nav` is DERIVED from the generated tree rather than typed, so the bidirectional
invariant (every file in nav, every nav entry a file) holds by construction. Round 3
turns that into a test, the way tests/test_shared_manifest.py does for MANIFEST.json.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from repos import REPOS  # noqa: E402

OUT = pathlib.Path(__file__).parent.parent / "hub"
SITE = OUT / "docs_site"
GENERATED = "2026-09-18"

MKDOCS = """# mkdocs.yml — ATRIUM aggregate documentation site (atrium-project#57)
#
# DRAFT, round 2. The nav below is complete and matches docs_site/ exactly; the
# pages it names are shells. Round 3 adds tools/docs/assemble_docs.py, which fills
# them from the sources each shell's `## Sources` table names.
#
# WHY docs_dir IS NOT `docs`: the hub's `docs/` already holds 13 canonical markdown
# files plus `docs/templates/` -- including `docs/templates/shared/`, which
# para-drift.reusable.yml enforces byte-identical across five repositories.
# Publishing from `docs/` would mean moving that tree, and `docs/templates` is
# referenced 363 times across the six repos, with the paths baked into the
# docstrings of the vendored files themselves. `docs_site/` costs nothing.
#
# WHY THE PUBLISHING SOURCE IS A BRANCH: Pages' branch source offers only `/` or
# `/docs` as folders -- there is no arbitrary-folder option -- and `/docs` is taken.
# So: build here, publish the result to `gh-pages`. See PAGES_SETUP.md.

site_name: ATRIUM — UFAL documentation
site_description: >-
  Documentation for the UFAL side of the ATRIUM project: the page classifier, the
  ALTO post-processor, the translator, and the NLP and LLM enrichers.
site_url: https://ufal.github.io/atrium-project/
repo_url: https://github.com/ufal/atrium-project
repo_name: ufal/atrium-project
edit_uri: ""          # pages are derived, not edited in place -- an edit link would lie
copyright: >-
  Developed by UFAL, Charles University · funded by ATRIUM · MIT licensed

docs_dir: docs_site
site_dir: site        # add to .gitignore -- the hub's current .gitignore has no
                      # build-output rule; it was written for tool caches only

theme:
  name: material
  language: en
  features:
    - navigation.sections
    - navigation.top
    - navigation.indexes
    - navigation.tracking
    - search.highlight
    - search.suggest
    - content.code.copy
    - toc.follow
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: deep purple
      accent: deep purple
      toggle: {{icon: material/brightness-7, name: Switch to dark mode}}
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: deep purple
      accent: deep purple
      toggle: {{icon: material/brightness-4, name: Switch to light mode}}

extra_css:
  - assets/extra.css

markdown_extensions:
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes            # every README defines its footnotes in one EOF block:
                         # 30 in nlp-enrich, 19 in page-classification, 9 in alto
                         # (numbering skips [^3]), 8 each in translator and llm-enrich
  - md_in_html
  - tables
  - toc:
      permalink: true
      slugify: !!python/object/apply:pymdownx.slugs.slugify {{kwds: {{case: lower}}}}
  - pymdownx.details
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid       # the corpus currently has ZERO ```mermaid blocks;
          class: mermaid      # docs_site/pipelines.md is where it gets its first
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true

plugins:
  - search

# --strict is the point of the aggregate topology: every cross-repo link is
# INTERNAL here, so a broken one fails the build. Under six separate sites those
# links would be absolute URLs that --strict cannot see, and the corpus already
# contains a broken cross-file anchor
# (atrium-alto-postprocess/service/README.md:93 -> ../README.md#composite-quality-score,
#  whose only real heading is docs/categorization_logic.md:214).
strict: true

nav:
{nav}
"""

EXTRA_CSS = """/* docs_site/assets/extra.css — ATRIUM site styling hook (DRAFT, round 2).
   Deliberately thin: Material's own palette does the work. This file exists so
   round 3 has somewhere to put the pipeline strip and the six-site switcher
   without patching the theme. */

:root {
  --atrium-violet: #6b3fa0;
}

/* Pipeline strip — rendered on each tool section's index page. */
.atrium-pipeline { display: flex; flex-wrap: wrap; gap: .3rem; align-items: center;
                   margin: 1rem 0; font-size: .8rem; }
.atrium-pipeline a,
.atrium-pipeline span.here { padding: .25rem .55rem; border-radius: 6px;
                             border: 1px solid var(--md-default-fg-color--lightest);
                             text-decoration: none; }
.atrium-pipeline span.here { background: var(--atrium-violet); color: #fff; font-weight: 600; }

/* Draft banner: make unfinished pages obvious while round 3 is in progress. */
.md-content .admonition.warning > .admonition-title { font-variant-caps: all-small-caps;
                                                      letter-spacing: .04em; }

/* Release tables are transposed into one ### per version, but source tables that
   survive elsewhere still need to not blow out the column. */
.md-typeset table:not([class]) td { word-break: break-word; }
"""

PAGES_SETUP = """# Enabling GitHub Pages for the ATRIUM repositories

_Generated {generated} for [issue #57](https://github.com/ufal/atrium-project/issues/57)._

All six repositories publish from a **`gh-pages` branch, folder `/ (root)`**.

## The one-time step, per repository

**Settings → Pages → Build and deployment → Source: _Deploy from a branch_ →
Branch: `gh-pages` / `/ (root)` → Save.**

That setting is **admin-level**. The maintainer token is `admin: false` on all six
repositories (and additionally `maintain: false` on `atrium-project` and
`atrium-llm-enrich`), so an organisation owner has to do it, or it has to happen
automatically.

## It may already be automatic — verify on one repo first

GitHub has long auto-configured Pages the first time a `gh-pages` branch appears;
that behaviour is what `mkdocs gh-deploy` and `peaceiris/actions-gh-pages` rely on.
**This was not re-verified while writing this file** — `docs.github.com` was
unreachable from the authoring environment — so treat it as likely, not certain.

**Do this:** push `gh-pages` to **one** repository, wait a minute, and check
`https://ufal.github.io/<repo>/`. If it serves, the other five need nothing. If it
404s, the manual step above is required and an owner should do all six at once.

Pushing the branch is safe either way: the content simply sits there until Pages is
pointed at it.

## Why a branch and not a folder

Pages' branch source offers exactly two folder choices, `/ (root)` and `/docs`.
There is no arbitrary-folder option. `/docs` is unavailable in `atrium-project`
because `docs/` already holds the hub's 13 canonical markdown files plus
`docs/templates/` — and `docs/templates/shared/` is enforced byte-identical across
all five tool repositories by `para-drift.reusable.yml`. Moving it would touch
**363 references across the six repos**, with the paths baked into the docstrings of
the vendored files themselves, requiring all 17 canonical files to be re-vendored
inside one atomic window or CI goes red in five repositories at once.

A `gh-pages` branch changes **zero** references.

## What lands on `gh-pages`

| Repository | Branch content | URL |
|---|---|---|
| `atrium-project` | the built MkDocs site | <https://ufal.github.io/atrium-project/> |
{stub_rows}

The five tool-repo branches are **orphan** branches holding a static landing card.
They share no history with `test`/`master`/`main`/`vit` and never need regenerating —
which is the main simplification the branch source buys over an Actions source.

## The markdown stays readable regardless

The site's markdown source lives on the hub's default branch at `docs_site/`, where
GitHub renders it as markdown in the normal repository browser. Nothing is hidden
behind a Pages build, whether or not the switch is ever flipped.
"""

SITE_YML = """# docs/site.yml — the assembler manifest for the ATRIUM documentation site.
#
# DRAFT, round 2 (atrium-project#57). This file is a SHAPE, not a working manifest:
# round 3 adds tools/docs/site_manifest.py to read it and tools/docs/assemble_docs.py
# to act on it.
#
# IT IMITATES docs/templates/shared/MANIFEST.json ON PURPOSE. #59 established the
# house pattern for exactly this problem -- one registration drives every consumer,
# and a test asserts they all agree, because "a guardrail cannot see what it is
# supposed to hold". Inventing a second registration convention would re-create the
# defect #59 exists to prevent. So:
#
#   * one reader           -> tools/docs/site_manifest.py, exposing load_manifest()
#                             and ManifestError, with a --json / --tsv CLI, mirroring
#                             tools/shared_manifest.py's 109-line surface
#   * one agreement test   -> tests/test_docs_manifest.py, carrying the four patterns
#                             from tests/test_shared_manifest.py:
#                               1. bidirectional on-disk <-> manifest agreement
#                               2. a deliberately-broken tmp_path fixture that must raise
#                               3. a structural "no hand-written list survived" regex
#                               4. a prose-count citation test
#   * --check writes nothing, exactly as scripts/revendor_shared.sh defines it
#
# Validation round 3 must enforce (the same five checks shared_manifest.py makes):
# non-empty `pages`; every entry carries the required fields; no duplicate `page`;
# no duplicate (source, section) pair; `sources` is a list.

_comment:
  - "The single registration for the ATRIUM documentation site. Adding a page means"
  - "adding one entry here -- not editing mkdocs.yml's nav, the assembler and a test"
  - "in three places that would then drift independently."
  - "Round 2 status: every `page` below exists as a draft shell in docs_site/ and"
  - "every shell appears here. That bidirectional property is what test 1 asserts."

defaults:
  # Each tool repo is read at its default branch unless an entry pins a ref.
  # Verified 2026-09-18. page-classification is `vit`, not `master`: that is worth
  # correcting on its own terms, but under this topology it is NOT a blocker --
  # the site publishes from atrium-project, and page-classification's docs are
  # merely READ at the ref named here.
  refs:
    atrium-project: main
    atrium-page-classification: vit
    atrium-alto-postprocess: master
    atrium-translator: master
    atrium-nlp-enrich: master
    atrium-llm-enrich: main
  split_depth: 3
  link_rewrite:
    doc_to_doc: site-relative
    doc_to_code: github-blob-at-ref
    doc_to_ci: github-blob-at-ref
    agent_dev_logs: github-blob-at-ref   # those pages are not published

# Files that must never reach the built site. Round 3's test greps the built
# site/ for each path AND for the five ARUP/ARUB partner addresses.
#
# NOTE ON SCOPING THE GREP: all five tool READMEs and all five CONTRIBUTING files
# carry a contact address of their own -- one shared maintainer address, zero
# overlap with the partner set -- and they are published deliberately. A blanket
# "no email addresses in the built site" assertion fails on day one against content
# that is public by design, and a test that fails for the wrong reason gets disabled.
exclude:
{excludes}
# Shared blocks rendered ONCE and linked from their other consumers. Measured
# 2026-09-17; ~67,700 B recoverable in total. Deliberately NOT here: the five
# READMEs (pairwise similarity 0.012-0.108, ~2,400 B shareable -- no machinery is
# worth building) and `## Release History` (195,371 B, five distinct changelogs,
# 0 % shareable; it is transposed five times, which is a readability win, not a
# de-duplication win).
render_once:
{render_once}
pages:
{pages}"""


def nav_lines() -> str:
    def entry(indent, label, path):
        return f"{' ' * indent}- {label}: {path}"

    L = [
        "  - Home: index.md",
        "  - Pipelines: pipelines.md",
        "  - External tools & services: external-tools.md",
        "  - Ecosystem:",
        "      - Architecture: ecosystem/architecture.md",
        "      - Repository map: ecosystem/repository-map.md",
        "      - The document contract: ecosystem/document-contract.md",
        "  - Contracts:",
        "      - RO-Crate export: contracts/rocrate.md",
        "      - SKOS & the ATRIUM vocabulary: contracts/skos.md",
        "      - Schemas: contracts/schemas.md",
        "  - Agent skills: agent-skills.md",
        "  - Operations: operations.md",
        "  - Contributing standards: contributing-standards.md",
        "  - Tools:",
    ]
    for r in REPOS:
        s = r["short"]
        L += [
            f"      - {s}:",
            f"          - Overview: tools/{s}/index.md",
            f"          - Guide: tools/{s}/guide.md",
            f"          - Reference: tools/{s}/reference.md",
            f"          - Changelog: tools/{s}/changelog.md",
            f"          - History: tools/{s}/history.md",
        ]
    L.append("  - Development history: development-history.md")
    return "\n".join(L)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    (OUT / "mkdocs.yml").write_text(MKDOCS.format(nav=nav_lines()))

    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    (SITE / "assets" / "extra.css").write_text(EXTRA_CSS)

    stub_rows = "\n".join(
        f"| `{r['slug']}` | orphan branch, static landing card | <https://ufal.github.io/{r['slug']}/> |" for r in REPOS
    )
    (OUT / "PAGES_SETUP.md").write_text(PAGES_SETUP.format(generated=GENERATED, stub_rows=stub_rows))

    excludes = "\n".join(
        [
            "  - path: atrium-project/docs/arub-p_contacts.md",
            '    reason: "five personal email addresses of named ARUP/ARUB partners"',
            "  - path: atrium-project/docs/plan_repo_review.md",
            '    reason: "carries a personal email; self-declares as stale"',
            "  - path: atrium-project/docs/docker_gha_roadmap.md",
            '    reason: "internal roadmap, 97,253 B"',
            "  - path: atrium-nlp-enrich/data_samples/vocab/6.D-eval.decision-package.md",
            '    reason: "open memo addressed to named individuals"',
            "  - path: atrium-nlp-enrich/data_samples/vocab/6.O3O4.decision-package.md",
            '    reason: "open memo addressed to named individuals"',
            "  - path: atrium-llm-enrich/data_samples/vocab/6.D-eval.decision-package.md",
            '    reason: "open memo addressed to named individuals"',
            "  - path: atrium-llm-enrich/data_samples/vocab/6.O3O4.decision-package.md",
            '    reason: "open memo addressed to named individuals"',
            "  - path: atrium-llm-enrich/digital_born/README.md",
            '    reason: "self-declared Phase 0 exploration scratch space"',
            "  - path: atrium-alto-postprocess/tools/quality_model/EXPERIMENTS.md",
            '    reason: "unfilled results table"',
            "  - path: atrium-page-classification/README.html",
            '    reason: "178,278 B stale pre-rendered HTML; delete-or-exclude decision pending"',
            '  - section: "Results log (fill in)"',
            "    in: [atrium-project/docs/k8s_acceptance_runbook.md,",
            "         atrium-project/docs/skill_acceptance_runbook.md]",
            '    reason: "empty placeholder tables"',
            "",
        ]
    )

    render_once = "\n".join(
        [
            '  - block: "CONTRIBUTING ## 🔁 Contributor Workflow"',
            "    owner: atrium-project/docs/templates/CONTRIBUTING.md",
            "    identical_in: [atrium-page-classification, atrium-alto-postprocess,",
            "                   atrium-translator, atrium-nlp-enrich]",
            "    bytes_each: 413",
            "    recovers: 1239",
            '  - block: "CONTRIBUTING ## 📋 Pull Request Format"',
            "    owner: atrium-project/docs/templates/CONTRIBUTING.md",
            "    identical_in: [atrium-page-classification, atrium-alto-postprocess,",
            "                   atrium-translator, atrium-nlp-enrich]",
            "    bytes_each: 688",
            "    recovers: 2064",
            '  - block: "CONTRIBUTING ## ✏️ Commit Messages (the type table)"',
            "    owner: atrium-project/docs/templates/CONTRIBUTING.md",
            "    identical_in: [all five tool repos and the hub template]",
            "    bytes_each: 659",
            "    recovers: 3295",
            '  - block: "CONTRIBUTING ## 🌿 Branches & Environments"',
            "    owner: atrium-project/docs/templates/CONTRIBUTING.md",
            "    near_identical_in: [all five]",
            '    similarity: "0.75-0.91"',
            '    delta: "three example branch names per repo, and master vs main"',
            "    recovers: 3900",
            '  - block: "CONTRIBUTING ## 🔗 Shared (\\"drop-in\\") code"',
            "    owner: atrium-llm-enrich/CONTRIBUTING.md",
            '    note: "the ONLY repo documenting the shared-code mechanism; the other four',
            '           never mention the hub canon, the 17-file manifest or re-vendoring"',
            "    recovers: 0",
            '  - block: "data_samples/vocab/RUNBOOK.md"',
            "    owner: atrium-nlp-enrich",
            "    byte_identical_in: [atrium-llm-enrich]",
            "    bytes: 28939",
            "    recovers: 28939",
            '  - block: "prompts/RUNBOOK.md"',
            "    owner: atrium-nlp-enrich",
            "    byte_identical_in: [atrium-llm-enrich]",
            "    bytes: 19948",
            "    recovers: 19948",
            "",
        ]
    )

    md = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("*.md"))
    pages = "\n".join(
        f'  - page: {p}\n    shell: true\n    sources: "see the page\'s own ## Sources table"' for p in md
    )
    (OUT / "docs").mkdir(parents=True, exist_ok=True)
    (OUT / "docs" / "site.yml").write_text(
        SITE_YML.format(excludes=excludes, render_once=render_once, pages=pages) + "\n"
    )

    print(f"  mkdocs.yml ({len(nav_lines().splitlines())} nav lines)")
    print(f"  docs/site.yml ({len(md)} pages registered)")
    print("  PAGES_SETUP.md, docs_site/assets/extra.css")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
