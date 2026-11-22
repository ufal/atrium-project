# Publishing the ATRIUM sites on GitHub Pages

How the hub's documentation site and the six tools' landing pages are built and published. The dated
record of how this came about, with the Jekyll fences and the state tables of September 2026, is in
[`docs/decisions/pages-publishing.md`](docs/decisions/pages-publishing.md).

## What is published, from where

All seven repositories publish from a **`gh-pages` branch, folder `/ (root)`**:

| Repository                   | `gh-pages` holds                        | Written by                                         | URL                                                  |
|------------------------------|-----------------------------------------|----------------------------------------------------|------------------------------------------------------|
| `atrium-project`             | the built MkDocs site                   | `.github/workflows/pages.yml`, on a push to `main` | <https://ufal.github.io/atrium-project/>             |
| `atrium-page-classification` | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-page-classification/> |
| `atrium-ocr-postprocess`     | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-ocr-postprocess/>     |
| `atrium-translator`          | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-translator/>          |
| `atrium-nlp-enrich`          | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-nlp-enrich/>          |
| `atrium-keyword-extract`     | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-keyword-extract/>     |
| `atrium-digital-convert`     | an orphan branch, a static landing card | `_generators/make_stubs.py`, by hand               | <https://ufal.github.io/atrium-digital-convert/>     |

The Pages source of a repository is an admin-level setting, changed in *Settings → Pages* by an owner. The
archived predecessors `atrium-alto-postprocess` and `atrium-llm-enrich` keep serving their old cards: GitHub
does not redirect Pages when a repository is replaced.

## The hub's site

The source is `docs_site/` on the hub's default branch, `main`, where GitHub also renders it as Markdown.
`.github/workflows/pages.yml` builds it on every pull request into `main` or `test`, and on a push to
`main` (a merged pull request) publishes it with `mkdocs gh-deploy --force --no-history`. The `gh-pages`
branch is derived output: never commit to it by hand.

```bash
pip install -r tools/docs/requirements.txt
mkdocs build --strict          # docs_site/ -> site/
```

`site/` is gitignored. `mkdocs.yml` sets `strict: true` **and** `validation.links.anchors: warn`: `--strict`
promotes warnings but not info, and MkDocs reports a broken anchor as info unless told otherwise.

**Why not `/docs`.** Pages' branch source offers two folders, `/ (root)` and `/docs`. The hub's `docs/` is
its internal reference tree: it holds partner contacts and internal plans, and its `docs/templates/` paths
are cited across the tool repositories, so it is neither published nor moved. Only the built site is.

## The tools' landing cards

Each tool's `gh-pages` is an orphan branch with one static landing card, sharing no history with the
repository's other branches. `_generators/make_stubs.py` writes all six from `_generators/repos.py`,
which holds each card's title, tagline and links; a card changes only when it is regenerated and pushed
to that repository's `gh-pages`.
