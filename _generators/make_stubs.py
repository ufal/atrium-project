#!/usr/bin/env python3
"""Generate the five tool-repo gh-pages stub trees (issue #57; round 2, docs links round 7).

Each tree becomes the ROOT of that repository's `gh-pages` branch. The branch is
an orphan: it shares no history with test/master/main/vit and carries no source.

Design note: the cards render the README badge information as LOCAL chips rather
than as img.shields.io images. A landing card whose only job is to point somewhere
should not depend on a third-party image host being up, and shields.io images are
the slowest thing on any GitHub README.
"""

from __future__ import annotations

import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from repos import HUB_SITE, ORG, REPOS  # noqa: E402

OUT = pathlib.Path(__file__).parent.parent / "stubs"
CSS = (pathlib.Path(__file__).parent / "style.css").read_text()

GENERATED = "2026-09-25"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def chips_html(repo: dict) -> str:
    rows = []
    for k, v, url, _kind in repo["chips"]:
        rows.append(
            f'      <li><a class="chip" href="{esc(url)}" rel="noopener">'
            f'<span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></a></li>'
        )
    return "\n".join(rows)


def pipeline_html(current: dict) -> str:
    """The sibling strip. Each neighbour links to ITS OWN published page.

    It used to link to `{HUB_SITE}/tools/<short>/`. Those are hub sections, and the
    hub site did not exist -- 40 of the 90 hub links across the five gh-pages
    branches were sibling links, every one of them a 404, and they would stay 404 for
    as long as the hub's own Pages stayed broken. `https://ufal.github.io/<slug>/` is
    the neighbour's real page: four of the five have been serving since 2026-09-19,
    and each one carries its own "Documentation ->" button into the hub section, so
    nothing is lost by going one hop through it.

    The card's OWN hub links -- the eyebrow, "Documentation ->", "ATRIUM docs home"
    and the footer -- deliberately still point at the hub. They are the reason the hub
    site has to come up, not a workaround for it being down.
    """
    items = []
    for i, r in enumerate(REPOS):
        if i:
            items.append('      <li class="arrow">&rarr;</li>')
        label = esc(r["short"])
        if r["slug"] == current["slug"]:
            items.append(f'      <li><span class="here">{label}</span></li>')
        else:
            items.append(f'      <li><a href="https://ufal.github.io/{r["slug"]}/">{label}</a></li>')
    return "\n".join(items)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_tag}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{css_href}assets/style.css">
<link rel="canonical" href="{canonical}">
</head>
<body>
<div class="wrap">

  <div class="eyebrow">
    <a href="{hub_site}/">ATRIUM</a>
    <span class="sep">/</span>
    <span>{short}</span>
  </div>

  <main class="card">
{lead}
    <p class="tagline">{tagline}</p>
    <p class="role">{role}</p>

    <ul class="chips">
{chips}
    </ul>

    <div class="actions">
      <a class="btn btn-primary" href="{hub_site}/{docs_path}">Documentation &rarr;</a>
      <a class="btn" href="{org}/{slug}">Source on GitHub</a>
      <a class="btn" href="{hub_site}/">ATRIUM docs home</a>
    </div>

    <div class="pipeline">
      <h2>Where this sits in the pipeline</h2>
      <ul class="stages">
{pipeline}
      </ul>
    </div>
  </main>

  <footer>
    <p>This page is a published stub. The documentation itself lives in the
       <a href="{hub_site}/{docs_path}">ATRIUM hub site</a>; the code lives on the
       <a href="{org}/{slug}/tree/{default_branch}"><code>{default_branch}</code></a> branch.</p>
    <p>Developed by <a href="https://ufal.mff.cuni.cz">UFAL</a>, Charles University &middot;
       funded by <a href="https://atrium-research.eu/">ATRIUM</a> &middot;
       MIT licensed &middot; generated {generated}</p>
  </footer>

</div>
</body>
</html>
"""

LEAD_INDEX = """    <h1>{title}</h1>
    <p class="sub">{subtitle}</p>"""

LEAD_404 = """    <p class="notfound-code">404 &middot; page not found</p>
    <h1>{title}</h1>
    <p class="sub">That page is not on this stub &mdash; try the documentation site.</p>"""

README = """# `gh-pages` &mdash; published stub for `{slug}`

**This branch is not source.** It is an orphan branch holding one static landing
card, published by GitHub Pages at <{pages_url}>.

* The **code** lives on [`{default_branch}`]({org}/{slug}/tree/{default_branch}).
* The **documentation** lives in the ATRIUM hub site at
  <{hub_site}/{docs_path}>, written from this repository's own
  `README.md`, `CONTRIBUTING.md` and `agent_dev_logs/DEVLOG.md`, which stay the full
  manual. Nothing is copied here &mdash; see
  [`atrium-project` issue #57]({org}/atrium-project/issues/57).

## What is in here

| Path               | Purpose                                                         |
|--------------------|-----------------------------------------------------------------|
| `index.html`       | the landing card                                                |
| `404.html`         | the same card, framed as a not-found page                       |
| `assets/style.css` | self-contained styles; no webfont, no CDN, no script            |
| `.nojekyll`        | tell Pages to serve these files as-is instead of running Jekyll |
| `README.md`        | this file                                                       |

## Maintaining it

A static card does not need regenerating &mdash; that is the point of putting it on a
branch rather than building it in CI. Edit it only when the repository's name,
one-line description or place in the pipeline changes.

The card deliberately renders the README's badges as **local chips** rather than
`img.shields.io` images, so the page has zero external requests and cannot be left
half-drawn by a slow third-party image host.

## Enabling Pages for this repository

One-time, needs repository admin: **Settings &rarr; Pages &rarr; Build and deployment
&rarr; Source: Deploy from a branch &rarr; Branch: `gh-pages` / `/ (root)`**.
See `PAGES_SETUP.md` in the hub repository for the full note.

_Generated {generated} for issue #57._
"""


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> int:
    count = 0
    for repo in REPOS:
        root = OUT / repo["slug"]
        short, slug = repo["short"], repo["slug"]
        pages_url = f"https://ufal.github.io/{slug}/"
        common = dict(
            title=esc(repo["title"]),
            subtitle=esc(repo["subtitle"]),
            tagline=esc(repo["tagline"]),
            role=esc(repo["role"]),
            chips=chips_html(repo),
            pipeline=pipeline_html(repo),
            hub_site=HUB_SITE,
            org=ORG,
            slug=slug,
            short=short,
            docs_path=repo["docs_path"],
            default_branch=repo["default_branch"],
            generated=GENERATED,
            description=esc(repo["tagline"]),
            canonical=pages_url,
            css_href="",
        )

        write(
            root / "index.html",
            PAGE.format(
                title_tag=esc(f"{repo['title']} — ATRIUM"),
                lead=LEAD_INDEX.format(title=esc(repo["title"]), subtitle=esc(repo["subtitle"])),
                **common,
            ),
        )
        write(
            root / "404.html",
            PAGE.format(
                title_tag=esc(f"Page not found — {short} — ATRIUM"),
                lead=LEAD_404.format(title=esc(repo["title"])),
                **common,
            ),
        )
        write(root / "assets" / "style.css", CSS)
        write(root / ".nojekyll", "")
        write(
            root / "README.md",
            README.format(
                slug=slug,
                short=short,
                docs_path=repo["docs_path"],
                org=ORG,
                hub_site=HUB_SITE,
                default_branch=repo["default_branch"],
                pages_url=pages_url,
                generated=GENERATED,
            ),
        )
        count += 5
        print(f"  {slug}/  -> 5 files")
    print(f"total: {count} files in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
