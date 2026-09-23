# ATRIUM hub site tree — issue #57, rounds 3–5 (content)

Everything here lands on **`atrium-project`'s default branch (`main`)**, not on `gh-pages`.
`gh-pages` receives the *built* site; this is its source, and `.github/workflows/pages.yml`
is what does the building. See [`PAGES_SETUP.md`](PAGES_SETUP.md) for the publishing
mechanics.

## What round 3 changed, and why

Round 2 shipped **38 draft shells** — frontmatter, a `## Sources` table and an outline of
`<!-- ASSEMBLER: -->` markers — to be filled at build time by an assembler that would slice
each tool's `README.md` into site pages. The maintainer's verdict on what that published was
*"no new information available"*, and it was correct: **34 of the 38 pages were a second copy
of something already public.** A mirror rebuilt on a cron can only tie its source or lag it.

`f47bf54` then removed the 25 `docs_site/tools/**` mirror pages and the `- Tools:` nav block,
leaving 13 hub shells and no tool sections at all.

**Round 3 writes pages instead of generating them.** The assembler (`57.plan.md` §B) is
retired along with `_generators/{make_hub,make_config,headings,hub_spec}.py`. Ten tool pages
are written — five for `page-classification`, five for `translator`, the two repositories
whose documentation is furthest along — and every claim in them was verified against the
tool's code at a named commit, not taken from its prose.

Each page keeps a `## Sources` table, but its job has changed: it is now a **provenance
record** naming what was read and at which ref, not a build instruction.

## What round 4 changed

**The nine remaining hub shells are written**, plus the portal copy on `index.md` — the
static parts of the site: the repository map, the architecture, the document contract, the
schemas, the SKOS vocabulary, RO-Crate export, agent skills, operations and the contribution
standard. Each is the **page-classification + translator view** of a contract whose normative
text lives in the hub's `docs/`: the concrete fields, URIs, endpoints, probes, images and
branches those two tools have, read out of their code, and where the hub document and the code
disagree. The other three tools appear only as identity rows until their sections are written.

**Two round-3 errors are corrected**, line by line: both tool guides named the API image
`atrium-<tool>:<version>-api` — the registry publishes `atrium-<tool>-api:<version>`, with no
leading `v` — and page-classification's overview repeated the hub's claim that the tool reads its
label list from the filesystem at run time, which is true only of `--train`/`--eval`.

Two findings were **run, not inferred**: the shared `atrium_document.py` and `atrium_paradata.py`,
driven with each tool's calls and `para_config.txt`, reproduce the licence each tool's record
ends up with, and the worked example on the document-contract page validates against the schema.
The RO-Crate page's mapping table is the real exporter's output on that same record.

**Tables follow the maintainer's formatter**: every column padded to its longest cell by
character count, one space either side, separator dashes = width + 2 — reverse-engineered from
the round-3 commit, where it reproduces 13 of 14 reformatted files byte-for-byte (the 14th differs
only in one table the formatter skipped). Tables indented inside content tabs are aligned the same
way.

## What round 5 changed

**The designed-but-unwritten sections are filled**, still scoped to page-classification and the
translator:

- **`pipelines.md`** — W5 (Agent-Skill), W7 (vocabulary harvesting, the translator's half), W12
  (the annotation round trip, page-classification's half) and W13 (RO-Crate export) are written;
  "the remaining nine" becomes "the remaining five", all belonging to the other three tools.
- **`external-tools.md`** — the "Still to write" block becomes real sections: the metadata
  standards and serialisations both tools vendor, CoNLL-U, PDF rasterisation, the classifier's ML
  stack, the translator's other back-ends and its evaluation metrics, the runtime and CI
  infrastructure, the project and its institutions, and the DMP standards deliberately not
  implemented. Entries only the other tools use stay marked *pending*.
- **`development-history.md`** — the cross-repository chronology, condensed from the hub
  `DEVLOG.md` into six eras, plus the four lessons that record keeps repeating.

**Every behavioural claim the surveys could only infer was run** on copies in a scratch directory
— `sort.sh`, `move_single.sh`, `pdf2png.sh` (against a stub `pdftoppm`), `filtering.py`,
`downscale.py`, `result_analysis.sh`, the `collect_images()` listing, `load_vocab.py`, the
vocabulary loader, `para_licenses.py`, both shared selftests, and CTranslate2's accepted compute
types. What could not be checked from here is stated as such: AIS CR's own site and the LINDAT
dataset record were unreachable, so those entries say only what the code relies on.

**Four round-3 statements are corrected**, line by line: `--train` resolves to **CC BY-NC 4.0**
(what `para_config.txt` declares), not the README's CC BY-NC-SA 4.0 — on `pipelines.md` W8 and on
page-classification's overview and reference; `amcr-inputs.txt` holds 15 URLs, not 16; OAI-PMH *is*
named by all three repositories that use it; UDPipe model names carry the `-241121` suffix.

## Layout

| Path                          | What it is                                                                                                               |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `mkdocs.yml`                  | site config. `docs_dir: docs_site`, `site_dir: site`, `strict: true`, `validation.links.anchors: warn`                   |
| `PAGES_SETUP.md`              | the publishing mechanics: why a branch source, how Pages is enabled, what the legacy Jekyll builder would have published |
| `docs_site/**`                | **23 pages** — 13 hub pages + 2 repos × 5 tool-section pages                                                             |
| `docs_site/assets/extra.css`  | styling hook; the `.atrium-pipeline` strip on each tool index uses it                                                    |
| `.github/workflows/pages.yml` | builds `docs_site/` with `--strict`; publishes to `gh-pages` on push to `main`                                           |
| `tools/docs/requirements.txt` | the pinned toolchain — mkdocs 1.6.1, mkdocs-material 9.7.7, pymdown-extensions 12.0.1                                    |
| `_generators/`                | what is left of the round-2 generators: `make_stubs.py`, `repos.py`, `style.css`                                         |

## Page status

| Page                                                                                   | State                                                                              |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `index.md`                                                                             | **written** — the portal: what ATRIUM is, the six repositories, where to start     |
| `pipelines.md`                                                                         | **partial** — both layer diagrams and W1, W4–W8, W12, W13 written; five listed     |
| `external-tools.md`                                                                    | **partial** — every entry the two tools depend on written; the rest marked pending |
| `development-history.md`                                                               | **partial** — per-repo index and the cross-repository chronology written           |
| `tools/page-classification/*`                                                          | **written** — 5 pages, from `vit` @ `8415ce7`                                      |
| `tools/translator/*`                                                                   | **written** — 5 pages, from `master` @ `88242fe`                                   |
| `ecosystem/repository-map.md`                                                          | **written** — six identity rows; depth for the two documented tools                |
| `ecosystem/{architecture,document-contract}.md`, `contracts/{schemas,skos,rocrate}.md` | **partial** — written for page-classification and translator                       |
| `agent-skills.md`, `operations.md`, `contributing-standards.md`                        | **partial** — written for page-classification and translator                       |

`mkdocs.yml`'s `nav` and `docs_site/` agree in both directions, **23 ↔ 23**, checked by a
green `mkdocs build --strict`. Under `strict: true` a nav entry with no file and a file with
no nav entry are both build failures, which is why a tool section may only be added to the
nav in the same commit as its pages. **No page on the site is a round-2 shell any more.**

## Why `docs_site/` and not `docs/`

The hub's `docs/` already holds 13 canonical markdown files plus `docs/templates/` — and
`docs/templates/shared/` is enforced byte-identical across all five tool repositories by
`para-drift.reusable.yml`. Publishing from `docs/` would mean moving that tree, and
`docs/templates` is referenced **363 times across the six repos**, with the paths baked into
the docstrings of the vendored files themselves. All 17 canonical files would have to be
re-vendored inside one atomic window or CI goes red in five repositories at once.
`docs_site/` costs nothing.

## The shape a written tool page uses

1. **frontmatter** — `title`, `nav_order`, `status`, `round`, `issue`, plus `repo`/`role` on
   tool pages. `nav_order` is `20 + stage*10 + role_index`: page-classification 30–34,
   translator 50–54, with 40–44 and 60–74 reserved for the three sections not yet written.
2. **The page.** Written prose, tables and diagrams — no markers, no admonition claiming the
   page will be filled later.
3. **`## Sources`** — a provenance table: what was read, at which ref, and what was taken
   from it.

The bar every page has to clear: **a reader is better off here than on the README.** Three
things earn that, and the round-2 shells had none of them — cross-repository facts the tool
repository cannot state about itself, values verified against code rather than prose, and
named drift where the two disagree.

## Verified

As of round 5 (2026-09-23), on the maintainer's `88bc1a6` plus this round's files:

- `mkdocs build --strict` → **exits 0**, 23 pages, on mkdocs 1.6.1 / mkdocs-material 9.7.7 /
  pymdown-extensions 12.0.1. Every internal cross-page link and anchor resolves.
- `python3 -m pytest tests/ -q` → **141 passed, 4 skipped**, unchanged from round 4. (Round 3
  recorded 111 / 22; the difference is only that `pytest`, `pyyaml` and `jsonschema` are installed
  in this environment, so fewer tests skip. No test file changed.)
- `python3 tools/ci/workflow_lint.py --repo-root . --hub-root . --offline` → **OK**.
- The built `site/` contains **no** `ASSEMBLER` marker and **no** "Draft shell" admonition on any
  page, and none of: the personal contact address, `arub-p_contacts`, maintainer handles, token
  prefixes, the grant number, internal secret names, CI run IDs, or cluster paths and hostnames.
- Every markdown table in every rendered page produces an HTML `<table>` (counted per page for the
  three pages round 5 touched).
- Three Mermaid diagrams render as `class="mermaid"` elements — two on `pipelines.md`, one on
  `ecosystem/architecture.md`.

## Contents

```
  .github/workflows/pages.yml
  INDEX.md
  PAGES_SETUP.md
  mkdocs.yml
  tools/docs/requirements.txt
  _generators/make_stubs.py
  _generators/repos.py
  _generators/style.css
  docs_site/index.md
  docs_site/pipelines.md
  docs_site/external-tools.md
  docs_site/development-history.md
  docs_site/agent-skills.md
  docs_site/operations.md
  docs_site/contributing-standards.md
  docs_site/assets/extra.css
  docs_site/contracts/rocrate.md
  docs_site/contracts/schemas.md
  docs_site/contracts/skos.md
  docs_site/ecosystem/architecture.md
  docs_site/ecosystem/document-contract.md
  docs_site/ecosystem/repository-map.md
  docs_site/tools/page-classification/index.md
  docs_site/tools/page-classification/guide.md
  docs_site/tools/page-classification/reference.md
  docs_site/tools/page-classification/changelog.md
  docs_site/tools/page-classification/history.md
  docs_site/tools/translator/index.md
  docs_site/tools/translator/guide.md
  docs_site/tools/translator/reference.md
  docs_site/tools/translator/changelog.md
  docs_site/tools/translator/history.md
```

## What these rounds deliberately do not do

- **The other three tool sections.** alto-postprocess, nlp-enrich and llm-enrich keep their
  reserved `nav_order` ranges and nothing else.
- **Any change to a tool repository.** The drift these pages document is reported, not fixed
  at source; each item is a candidate issue in its own repository.
- **Repointing the landing cards' deep links.** `_generators/make_stubs.py` still generates
  cards linking to `…/atrium-project/tools/<short>/` for all five repos. Two of those paths
  now exist; the other three resolve when their sections are written.
- **`PAGES_STRATEGY.md`.** It is referenced by `PAGES_SETUP.md`, `DEVLOG.md`,
  `57.digest.md` and `57.plan.md`, and **has never existed in this repository** — every
  `§`-reference to it points nowhere. Its 12-page design survives only as a DEVLOG summary.
  Flagged here, not written.
- **The hub's licence statement.** `mkdocs.yml`'s `copyright:` line and every landing card say
  "MIT licensed", but the hub has **no `LICENSE` and no `CITATION.cff`** — the two tools are MIT,
  the hub states nothing. Left for the maintainer to decide, not edited.
