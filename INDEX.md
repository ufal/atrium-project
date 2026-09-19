# ATRIUM hub site tree — drafts, issue #57 round 2

Everything here lands on **`atrium-project`'s default branch (`main`)**, not on
`gh-pages`. `gh-pages` receives the *built* site; this is its source.

**These are shells.** Every page carries frontmatter, a one-sentence purpose, a
`## Sources` table and an outline whose sections carry `<!-- ASSEMBLER: -->` markers.
**No prose is copied from any source file** — round 3 fills them, and "nothing moves"
forbids copying regardless: `README.md` and `CONTRIBUTING.md` stay canonical and
full-length in their own repositories, and the split is regenerated on every build so
it cannot drift.

## Layout

| Path | What it is |
|---|---|
| `mkdocs.yml` | site config draft. `docs_dir: docs_site`, `site_dir: site`, `strict: true` |
| `PAGES_SETUP.md` | the one-time Pages enablement step, per repository |
| `docs/site.yml` | the assembler manifest **draft** — a shape, not a working file |
| `docs_site/**` | 38 page drafts (13 hub pages + 5 repos × 5 tool-section pages) |
| `docs_site/assets/extra.css` | thin styling hook for the pipeline strip and switcher |
| `_generators/` | **scaffolding, not repo files** — see below |

Also needed, and not included as a file because it is a one-line edit: add `site/`
to the hub's `.gitignore`, which currently has no build-output rule (it was written
for tool caches only).

## Why `docs_site/` and not `docs/`

The hub's `docs/` already holds 13 canonical markdown files plus `docs/templates/` —
and `docs/templates/shared/` is enforced byte-identical across all five tool
repositories by `para-drift.reusable.yml`. Publishing from `docs/` would mean moving
that tree, and `docs/templates` is referenced **363 times across the six repos**,
with the paths baked into the docstrings of the vendored files themselves. All 17
canonical files would have to be re-vendored inside one atomic window or CI goes red
in five repositories at once. `docs_site/` costs nothing.

## The five-part shape every page draft uses

1. **frontmatter** — `title`, `nav_order`, `status: draft`, plus `repo`/`role` on tool pages
2. **Purpose** — one sentence: who the page is for, what they leave knowing
3. **Sources** — a table of exact repo paths, `##` sections, split depth and treatment
   (`render` · `split at depth N` · `transposed` · `derived` · `transclude` ·
   `suppressed` · `EXCLUDED` · `AUTHORED`)
4. **Outline** — the headings the assembled page will have
5. **`<!-- ASSEMBLER: source="…" section="…" depth=N -->`** markers, one per section

## What the source pointers are worth

They were **read out of the repositories**, not written from memory, using a
fence-aware heading parser — the same rule `57.plan.md` §B.2 specifies for the
assembler. **208 source paths were checked and all 208 resolve.** `nav` ↔ `docs_site/`
↔ `docs/site.yml` agree in both directions, 38 = 38 = 38; round 3 turns that into a
test, the way `tests/test_shared_manifest.py` does for `MANIFEST.json`.

The parser matters: a naive `^## ` regex finds **23** `##` headings in
`docs/agent_skill_strategy.md` where only **18** are real — the other five are inside
the SKILL.md skeleton quoted in `## Appendix A`. It would have written five source
pointers to sections that do not exist, in the hub's own pilot page.

## `_generators/`

The scripts that produced these drafts. **They are not repository files** and should
not be committed as-is. Two are worth keeping for round 3:

- `headings.py` — the fence-aware parser above; the assembler needs exactly this
- `hub_spec.py` — the README-section → page routing table, which encodes where each
  of the five tool repos' sections belongs

`make_stubs.py`, `make_hub.py` and `make_config.py` regenerate everything in both
archives from scratch, so a correction is a one-line edit plus a re-run rather than
38 hand edits.

## What this round deliberately does not do

No assembler, no `site_manifest.py`, no tests, no build/deploy workflow, no prose, no
change to any README, and no docs-site link added anywhere. All of that is round 3.

## Contents

```
  PAGES_SETUP.md
  _generators/headings.py
  _generators/hub_spec.py
  _generators/make_config.py
  _generators/make_hub.py
  _generators/make_stubs.py
  _generators/repos.py
  _generators/style.css
  docs/site.yml
  docs_site/agent-skills.md
  docs_site/assets/extra.css
  docs_site/contracts/rocrate.md
  docs_site/contracts/schemas.md
  docs_site/contracts/skos.md
  docs_site/contributing-standards.md
  docs_site/development-history.md
  docs_site/ecosystem/architecture.md
  docs_site/ecosystem/document-contract.md
  docs_site/ecosystem/repository-map.md
  docs_site/external-tools.md
  docs_site/index.md
  docs_site/operations.md
  docs_site/pipelines.md
  docs_site/tools/alto-postprocess/changelog.md
  docs_site/tools/alto-postprocess/guide.md
  docs_site/tools/alto-postprocess/history.md
  docs_site/tools/alto-postprocess/index.md
  docs_site/tools/alto-postprocess/reference.md
  docs_site/tools/llm-enrich/changelog.md
  docs_site/tools/llm-enrich/guide.md
  docs_site/tools/llm-enrich/history.md
  docs_site/tools/llm-enrich/index.md
  docs_site/tools/llm-enrich/reference.md
  docs_site/tools/nlp-enrich/changelog.md
  docs_site/tools/nlp-enrich/guide.md
  docs_site/tools/nlp-enrich/history.md
  docs_site/tools/nlp-enrich/index.md
  docs_site/tools/nlp-enrich/reference.md
  docs_site/tools/page-classification/changelog.md
  docs_site/tools/page-classification/guide.md
  docs_site/tools/page-classification/history.md
  docs_site/tools/page-classification/index.md
  docs_site/tools/page-classification/reference.md
  docs_site/tools/translator/changelog.md
  docs_site/tools/translator/guide.md
  docs_site/tools/translator/history.md
  docs_site/tools/translator/index.md
  docs_site/tools/translator/reference.md
  mkdocs.yml
```
