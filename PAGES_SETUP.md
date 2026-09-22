# Enabling GitHub Pages for the ATRIUM repositories

_Rewritten 2026-09-21 for [issue #57](https://github.com/ufal/atrium-project/issues/57), against the
live state of the six repositories. The 2026-09-18 edition said `has_pages` was false on all six and
that enablement "may already be automatic"; both were overtaken within a day._

All six repositories publish from a **`gh-pages` branch, folder `/ (root)`**. Five of them already do.

> **What publishes, and why, is decided in [`INDEX.md`](INDEX.md)** (round 3, 2026-09-21).
> This file remains the mechanics and live-state record.
>
> ⚠️ Every reference in this file to `PAGES_STRATEGY.md` names **a document that has never
> existed in this repository** — not in the working tree and not in any commit. It is cited here,
> in `agent_dev_logs/DEVLOG.md`, in `digests/57.digest.md` and in `plans/57.plan.md`, and every
> `§`-reference to it points nowhere. Its 12-page design survives only as a DEVLOG summary. Treat
> those citations as unresolved, not as a file you have not found yet.

## Where each repository actually stands — ✅ all six, 2026-09-21

Re-measured from each repository's `pages build and deployment` runs via the Actions API.

| Repository                   | `gh-pages` | Pages source            | Last build (UTC)      | Runs |
|------------------------------|------------|-------------------------|-----------------------|-----:|
| `atrium-project` (hub)       | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 14:50 success |    5 |
| `atrium-page-classification` | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 12:08 success |    3 |
| `atrium-alto-postprocess`    | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 12:03 success |    3 |
| `atrium-translator`          | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 12:09 success |    3 |
| `atrium-nlp-enrich`          | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 12:06 success |    3 |
| `atrium-llm-enrich`          | ✅          | `gh-pages` / `/ (root)` | ✅ 09-21 12:07 success |    2 |

**Nothing is outstanding.** Both owner-level dropdowns this file used to list are done.

### ✏️ Two claims in the previous edition of this file were wrong

* **`atrium-alto-postprocess` was never "off / never built".** Its `pages-build-deployment` workflow
  dates from **2026-09-19 08:22 UTC** and has three successful runs — it was enabled at the same time
  as its four siblings. The claim was wrong when written, not overtaken.
* **The hub's `gh-pages` is no longer absent.** `.github/workflows/pages.yml` created it and deployed
  `ec06086` as `f9d77d1` (*"Deployed ec06086 with MkDocs version: 1.6.1"*, 87 files), and
  [run 35614832294](https://github.com/ufal/atrium-project/actions/runs/35614832294) builds from
  `head_branch: gh-pages`.

**This file should stop carrying a state table at all.** Three editions running, it has gone stale
within hours of being written, because the Pages source is a repository *setting* that changes with no
commit, no review and no notification. Read the state from the Actions API when it is needed; keep
this file for the mechanics, which do not move.

### What the build publishes — corrected 2026-09-21 (round 3)

It published all **38 draft shells**, including the **25 `tools/<name>/…` mirror pages**, each
carrying *"Draft shell — issue #57, round 2 (2026-09-18)"* and shipping its
`<!-- ASSEMBLER: source=… -->` markers in the delivered HTML. That is the state the maintainer
called *"no new information available"*.

Since then: `f47bf54` removed the 25 mirror pages and the `- Tools:` nav block, and round 3
wrote ten real tool pages in their place. The site is now **23 pages** — 13 hub pages plus five
each for `page-classification` and `translator` — and the built `site/` carries no `ASSEMBLER`
marker and no draft-shell admonition under `tools/`. See [`INDEX.md`](INDEX.md) for the
page-by-page state.

### The fences are gone — this section is history

With the source on `gh-pages`, the legacy Jekyll builder no longer runs over `main`, so
`_config.yml`, `docs/_config.yml` and `tests/test_pages_exclude.py` guarded nothing. **All three
were removed in `f47bf54`.** Everything below about them is **history, not instruction**; it is
kept because it records why they existed and what a green Jekyll build from `main` would have
published.

One caveat, stated once: if anyone ever points Settings → Pages back at `main`, the root
publishes unguarded — `agent_dev_logs/` included.

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

## ⚠️ The folder moved on 2026-09-21, and the fence had to move with it

[Run 35612083327](https://github.com/ufal/atrium-project/actions/runs/35612083327) reports
`Source: /github/workspace/.` and **`Configuration file: none`**. The Pages folder was changed from
`/docs` to `/ (root)`.

**Jekyll reads the `_config.yml` beside its source**, so `docs/_config.yml` stopped being consulted
the moment that dropdown changed. The fence was bypassed, not broken — and the blast radius went from
two files to the entire repository:

| Under `/docs`                    | Under `/ (root)`                                                     |
|----------------------------------|----------------------------------------------------------------------|
| 13 markdown files + `templates/` | **every tracked file**, including all 79 of `agent_dev_logs/`        |
| 2 files carrying addresses       | **5** — three more in `agent_dev_logs/` the docs fence never covered |
| 2 files carrying Liquid          | **9**                                                                |

The three the docs-scoped fence never reached:

* `agent_dev_logs/digests/project_state_1307.md` — a personal address
* `agent_dev_logs/digests/project_state_2706.md` — a personal address
* `agent_dev_logs/issues/2026-06-12.21.issue.open.md` — a partner address

…on top of 23 issue exports, several of which are open memos addressed to named individuals, which
`57.plan.md` §E says are not published at all.

And the nine files that now crash the build include **`PAGES_SETUP.md` — this file, at line 66**,
which quotes the failing Liquid expression verbatim in a fenced block. Documenting the error
reproduced it. The full set: `PAGES_SETUP.md`, `agent_dev_logs/DEVLOG.md`,
`agent_dev_logs/digests/10.digest.md`, `agent_dev_logs/digests/57.digest.md`,
`agent_dev_logs/digests/project_state_0709.md`, `agent_dev_logs/issues/2026-05-27.18.issue.open.md`,
`agent_dev_logs/plans/57.plan.md`, `docs/docker_gha.md`, `docs/docker_gha_roadmap.md`.

## The fences: `_config.yml` and `docs/_config.yml`

GitHub's `pages-build-deployment` job is not a workflow file in this repository and cannot be edited.
The only two levers over it are **what lives in the source folder** and **where the source points**.

**Both fences are kept**, because the dropdown has been set both ways within one day and neither
config depends on the other. Whichever way it is set, one is the fence and the other is inert.

### `_config.yml` (repo root) — the active one

It excludes `agent_dev_logs`, `docs`, `docs_site`, `INDEX.md`, `PAGES_SETUP.md`, `fixtures`, `tests`,
`tools`, `scripts`, `mkdocs.yml` and `ruff.toml`. Jekyll already skips anything beginning with `.` or
`_`, so `.github/`, `.gitignore` and `_generators/` need no entry.

**What publishes: `README.md`, and nothing else.** `jekyll-readme-index` makes it the site index, so
<https://ufal.github.io/atrium-project/> finally serves something true — the project README, already
public on the repository page. Checked: zero Liquid constructs, zero email addresses. That also makes
the **20 hub-root links** on the five stub cards resolve (the eyebrow and "ATRIUM docs home", ×2 pages
×5 repos); the 40 deep `…/tools/<name>/` links still need the real site.

### `docs/_config.yml` — inert now, the fence again if the folder goes back to `/docs`

| Excluded                | Why                                                                                                                                                                                          |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `arub-p_contacts.md`    | five ARÚP/ARÚB partner email addresses                                                                                                                                                       |
| `plan_repo_review.md`   | a personal email address; self-declares as stale                                                                                                                                             |
| `docker_gha_roadmap.md` | 97 KB internal roadmap — and the fatal Liquid at `:79`                                                                                                                                       |
| `docker_gha.md`         | one `{{version}}` at `:213` resolves to the empty string, not an error — the page would ship silently claiming `type=semver,pattern=`. Wrong is worse than absent.                           |
| `templates/`            | vendored canonical code, caller examples and «placeholder» skeletons — not documentation. Jekyll would render its four `.md` files and copy every `.py`/`.yml`/`.sh` into the site verbatim. |

Nine files still publish: `agent_skill_strategy` · `document_schema` · `k8s_acceptance_runbook` ·
`k8s_deployment` · `paradata_schema` · `rocrate_export` · `skill_acceptance_runbook` ·
`skills_catalog` · `skos_strategy`. All nine were checked: **zero Liquid constructs, zero email
addresses of any kind.** Their URLs (`…/skos_strategy.html`) are temporary and disappear when the
source moves — nothing links to them.

`tests/test_pages_exclude.py` holds **both** lists honest in both directions: every exclusion must
name a path that exists, and every tracked entry in each source folder must be either excluded or on a
reviewed allow-list. It also fails if a publishable file grows a Liquid construct or a partner address,
and it asserts by name that `agent_dev_logs/` and `docs/` stay excluded at the root. It compares
against `git ls-files`, not the filesystem — the Pages builder sees a fresh clone, so a gitignored
build artifact like `site/` is not there. Each
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

| Repository                   | Branch content                     | Written by                                            | URL                                                  |
|------------------------------|------------------------------------|-------------------------------------------------------|------------------------------------------------------|
| `atrium-project`             | the built MkDocs site              | `.github/workflows/pages.yml` on every push to `main` | <https://ufal.github.io/atrium-project/>             |
| `atrium-page-classification` | orphan branch, static landing card | `_generators/make_stubs.py`, by hand                  | <https://ufal.github.io/atrium-page-classification/> |
| `atrium-alto-postprocess`    | orphan branch, static landing card | `_generators/make_stubs.py`, by hand                  | <https://ufal.github.io/atrium-alto-postprocess/>    |
| `atrium-translator`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand                  | <https://ufal.github.io/atrium-translator/>          |
| `atrium-nlp-enrich`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand                  | <https://ufal.github.io/atrium-nlp-enrich/>          |
| `atrium-llm-enrich`          | orphan branch, static landing card | `_generators/make_stubs.py`, by hand                  | <https://ufal.github.io/atrium-llm-enrich/>          |

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
