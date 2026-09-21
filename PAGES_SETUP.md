# Enabling GitHub Pages for the ATRIUM repositories

_Rewritten 2026-09-21 for [issue #57](https://github.com/ufal/atrium-project/issues/57), against the
live state of the six repositories. The 2026-09-18 edition said `has_pages` was false on all six and
that enablement "may already be automatic"; both were overtaken within a day._

All six repositories publish from a **`gh-pages` branch, folder `/ (root)`**. Five of them already do.

## Where each repository actually stands

Measured 2026-09-21 from the `pages build and deployment` runs in each repository's Actions tab.

| Repository                   | `gh-pages` branch | Pages     | Source                     | Last build                    |
|------------------------------|-------------------|-----------|----------------------------|-------------------------------|
| `atrium-project` (hub)       | ⚠️ not yet         | on 09-21  | **`main` / `/docs`** ⚠️     | ✅ green, *fenced* — see below |
| `atrium-page-classification` | ✅ 09-19          | on 09-19  | `gh-pages` / `/ (root)`    | ✅ success                    |
| `atrium-alto-postprocess`    | ✅ 09-19          | ❌ **off** | —                          | — **never built**             |
| `atrium-translator`          | ✅ 09-19          | on 09-19  | `gh-pages` / `/ (root)`    | ✅ success                    |
| `atrium-nlp-enrich`          | ✅ 09-19          | on 09-19  | `gh-pages` / `/ (root)`    | ✅ success                    |
| `atrium-llm-enrich`          | ✅ 09-19          | on 09-21  | `gh-pages` / `/ (root)`    | ✅ success                    |

So two things are outstanding, and they are the same dropdown.

## Outstanding step 1 — point the hub at `gh-pages`

**`ufal/atrium-project` → Settings → Pages → Build and deployment → Source: _Deploy from a branch_ →
Branch: `gh-pages` / `/ (root)` → Save.**

Do this **after** `.github/workflows/pages.yml` has run once on `main`, which is what creates the
branch. Before that the dropdown has nothing to offer.

The hub is currently set to **`main` / `/docs`**, which is wrong twice over — see
[Why the hub must not publish from `/docs`](#why-the-hub-must-not-publish-from-docs).

## Outstanding step 2 — switch Pages on for `atrium-alto-postprocess`

Same dropdown. Its `gh-pages` branch has been sitting there since 2026-09-19 with the landing card on
it and Pages never switched on, so <https://ufal.github.io/atrium-alto-postprocess/> 404s while its
four siblings serve. There has never been a `pages build and deployment` run in that repository.

## Why an owner has to do it

That setting is **admin-level**, and the maintainer token is `admin: false` on all six repositories
(and additionally `maintain: false` on `atrium-project` and `atrium-llm-enrich`).

**`actions/configure-pages` cannot do it either, and the earlier plan was wrong to say it could.**
Its `findOrCreatePagesSite` **GETs the existing Pages site first** and returns whatever it finds; it
only POSTs `build_type: workflow` when the GET fails. On a repository where Pages is already enabled
as a *branch* source — which is exactly the hub's situation — it is a no-op, and a subsequent
`actions/deploy-pages` then fails because the site is not of type `workflow`.

There is one credible automation path left, `PUT /repos/{owner}/{repo}/pages` with a token carrying
`pages: write`. It was **not** attempted: `docs.github.com` is unreachable from the authoring
environment, so the permission requirement could not be verified, and a settings mutation issued from
CI on the strength of an unverified guess is worse than one dropdown.

## Why the hub must not publish from `/docs`

Two reasons. The first is that it does not work; the second is why you should be glad it does not.

**It did not build — fixed 2026-09-21 by `docs/_config.yml`.** Run
[35582651532](https://github.com/ufal/atrium-project/actions/runs/35582651532) failed with:

```text
Liquid Exception: Liquid syntax error (line 79): Variable
'{{ matrix.target != 'base' && format('-{0}'  was not properly terminated
with regexp: /\}\}/  in docker_gha_roadmap.md
```

Jekyll runs Liquid over **all** markdown — inside fenced code blocks and inline code spans too, which
is not obvious — so the GitHub Actions expression quoted at `docs/docker_gha_roadmap.md:79` is read as
a template variable and the parse dies. There are **nine such occurrences across two files**:

| File                        | Lines                             |
|-----------------------------|-----------------------------------|
| `docs/docker_gha.md`        | 213                               |
| `docs/docker_gha_roadmap.md`| 79, 80, 92, 99, 190, 252, 414, 437 |

Line 79 is the only hard failure; the other eight would render as empty strings, silently corrupting
the two documents that explain the ecosystem's Docker and CI story.

> ### ⚠️ Why this could not simply be "fixed in place"
>
> `docs/` is the hub's **canonical internal tree**. A *green* Jekyll build from it would publish:
>
> * `docs/arub-p_contacts.md` — **five ARÚP/ARÚB partner email addresses**;
> * `docs/plan_repo_review.md` — the maintainer's personal address, and self-declared stale;
> * `docs/docker_gha_roadmap.md` — a 97 KB internal roadmap.
>
> The failing build log already shows `Rendering: arub-p_contacts.md`; it only died four files later.
> Nothing was leaked **by accident, not by design** — so escaping the Liquid on its own would have
> turned the build green and put the contact list on the public web.
>
> **What landed instead: `docs/_config.yml`.** It excludes those three, plus `docker_gha.md` and
> `templates/`, so the build is green *and* cannot publish them. No source file was edited — the
> markdown is correct; it is Jekyll that is wrong for this corpus, and escaping `{{` would have
> corrupted how GitHub renders those files in the repository browser.

## The fence: `docs/_config.yml`

GitHub's `pages-build-deployment` job is not a workflow file in this repository and cannot be edited.
The only two levers over it are **what lives under `docs/`** and **where the Pages source points**.
`docs/_config.yml` is the first lever.

| Excluded                 | Why                                                                         |
|--------------------------|-----------------------------------------------------------------------------|
| `arub-p_contacts.md`     | five ARÚP/ARÚB partner email addresses                                      |
| `plan_repo_review.md`    | a personal email address; self-declares as stale                            |
| `docker_gha_roadmap.md`  | 97 KB internal roadmap — and the fatal Liquid at `:79`                      |
| `docker_gha.md`          | one `{{version}}` at `:213` resolves to the empty string, not an error — the page would ship silently claiming `type=semver,pattern=`. Wrong is worse than absent. |
| `templates/`             | vendored canonical code, caller examples and «placeholder» skeletons — not documentation. Jekyll would render its four `.md` files and copy every `.py`/`.yml`/`.sh` into the site verbatim. |

Nine files still publish: `agent_skill_strategy` · `document_schema` · `k8s_acceptance_runbook` ·
`k8s_deployment` · `paradata_schema` · `rocrate_export` · `skill_acceptance_runbook` ·
`skills_catalog` · `skos_strategy`. All nine were checked: **zero Liquid constructs, zero email
addresses of any kind.** Their URLs (`…/skos_strategy.html`) are temporary and disappear when the
source moves — nothing links to them.

`tests/test_docs_pages_exclude.py` holds the list honest in both directions: every exclusion must
name a file that exists, and every file under `docs/` must be either excluded or on a reviewed
allow-list. It also fails if a publishable file grows a Liquid construct or a partner address. Each
of its six checks was deliberately broken and confirmed to fail before being trusted.

**Both files are stopgaps. Delete them when the Pages source moves** — the legacy builder stops
running and nothing reads them again.

### Reproducing the build locally

Verified on `jekyll 3.10.0` / `liquid 4.0.4`, the versions the GitHub Pages image pins:

```bash
gem install --no-document 'jekyll:3.10.0' kramdown-parser-gfm \
  jekyll-optional-front-matter jekyll-relative-links jekyll-readme-index \
  jekyll-default-layout jekyll-titles-from-headings

printf 'plugins:\n  - jekyll-optional-front-matter\n  - jekyll-relative-links\n  - jekyll-readme-index\n  - jekyll-default-layout\n  - jekyll-titles-from-headings\n' > /tmp/ghp.yml
jekyll build -s docs -d /tmp/jk --config docs/_config.yml,/tmp/ghp.yml
```

`jekyll-optional-front-matter` is the one that matters: without it, front-matter-less `.md` files are
copied as static assets and Liquid never runs, so a plain `jekyll build` passes and hides the bug.
GitHub Pages forces that plugin on.

**And `/docs` is not the designed source anyway.** Pages' branch source offers exactly two folder
choices, `/ (root)` and `/docs`. `/docs` already holds the hub's 13 canonical markdown files plus
`docs/templates/` — and `docs/templates/shared/` is enforced byte-identical across all five tool
repositories by `para-drift.reusable.yml`. Moving that tree would touch **363 references across the
six repos**, with the paths baked into the docstrings of the vendored files themselves, requiring all
17 canonical files to be re-vendored inside one atomic window or CI goes red in five repositories at
once.

A `gh-pages` branch changes **zero** references.

## What lands on `gh-pages`

| Repository                   | Branch content                     | Written by                              | URL                                                  |
|------------------------------|------------------------------------|-----------------------------------------|------------------------------------------------------|
| `atrium-project`             | the built MkDocs site              | `.github/workflows/pages.yml` on every push to `main` | <https://ufal.github.io/atrium-project/>             |
| `atrium-page-classification` | orphan branch, static landing card | `_generators/make_stubs.py`, by hand     | <https://ufal.github.io/atrium-page-classification/> |
| `atrium-alto-postprocess`    | orphan branch, static landing card | `_generators/make_stubs.py`, by hand     | <https://ufal.github.io/atrium-alto-postprocess/>    |
| `atrium-translator`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand     | <https://ufal.github.io/atrium-translator/>          |
| `atrium-nlp-enrich`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand     | <https://ufal.github.io/atrium-nlp-enrich/>          |
| `atrium-llm-enrich`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand     | <https://ufal.github.io/atrium-llm-enrich/>          |

The five tool-repo branches are **orphan** branches holding a static landing card. They share no
history with `test`/`master`/`main`/`vit` and never need regenerating — which is the main
simplification the branch source buys over an Actions source. `57.plan.md` §G's
`pages-stub.reusable.yml` plus a per-repo caller is therefore **obsolete**: the stubs shipped as
static files on 2026-09-19 and there is nothing left for a reusable workflow to do.

The hub's branch is different: it is **derived output**, rewritten by `mkdocs gh-deploy --force
--no-history` on every push to `main`, plus a daily 07:00 cron so a tool repo's docs change is picked
up within 24 h. Never commit to it by hand.

## How the hub's site is built

```bash
pip install -r tools/docs/requirements.txt
mkdocs build --strict          # docs_site/ -> site/, 38 pages
```

`site/` is gitignored. `mkdocs.yml` sets `strict: true` **and** `validation.links.anchors: warn` —
the second line matters, because `--strict` promotes warnings but not info, and MkDocs classes a
broken anchor as info by default. Without it the config's own stated reason for `strict: true` (the
known-broken `alto-postprocess/service/README.md:93` anchor) would not have been checked at all.

## The markdown stays readable regardless

The site's markdown source lives on the hub's default branch at `docs_site/`, where GitHub renders it
as markdown in the normal repository browser. Nothing is hidden behind a Pages build, whether or not
the switch is ever flipped.
