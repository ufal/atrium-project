# Enabling GitHub Pages for the ATRIUM repositories

_Generated 2026-09-18 for [issue #57](https://github.com/ufal/atrium-project/issues/57)._

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

| Repository                   | Branch content                     | URL                                                  |
|------------------------------|------------------------------------|------------------------------------------------------|
| `atrium-project`             | the built MkDocs site              | <https://ufal.github.io/atrium-project/>             |
| `atrium-page-classification` | orphan branch, static landing card | <https://ufal.github.io/atrium-page-classification/> |
| `atrium-alto-postprocess`    | orphan branch, static landing card | <https://ufal.github.io/atrium-alto-postprocess/>    |
| `atrium-translator`          | orphan branch, static landing card | <https://ufal.github.io/atrium-translator/>          |
| `atrium-nlp-enrich`          | orphan branch, static landing card | <https://ufal.github.io/atrium-nlp-enrich/>          |
| `atrium-llm-enrich`          | orphan branch, static landing card | <https://ufal.github.io/atrium-llm-enrich/>          |

The five tool-repo branches are **orphan** branches holding a static landing card.
They share no history with `test`/`master`/`main`/`vit` and never need regenerating —
which is the main simplification the branch source buys over an Actions source.

## The markdown stays readable regardless

The site's markdown source lives on the hub's default branch at `docs_site/`, where
GitHub renders it as markdown in the normal repository browser. Nothing is hidden
behind a Pages build, whether or not the switch is ever flipped.
