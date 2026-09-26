# ATRIUM hub site tree — issue #57, rounds 3–7 (content)

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

## What round 6 changed

**The site now publishes only lasting facts.** Rounds 3–5 held every page to "values verified
against code, and named drift where the two disagree" — which filled the pages with audit
material that goes stale within days: "Known drift" lists (20+ items per tool), defect
write-ups, README-versus-code asides, open-issue status, commit SHAs and `file:NN` references in
prose. The maintainer's #57 TODO asks for static, unchangeable descriptions instead. Round 6
rewrote all **23** pages to that bar, scoped as before to page-classification and the
translator, and moved every removed finding — re-checked against the current heads, with a
status each — into [`agent_dev_logs/digests/57.findings.md`](agent_dev_logs/digests/57.findings.md),
which lives outside `docs_site/` and is never published.

- **Stripped:** both tools' `## Known drift` sections; the agent-skills Known drift; the
  contributing-standards "Contradictions" section; the schemas "What the schema says that the
  code does not"; the rocrate "What a crate cannot yet say"; every "Written so far / round N"
  admonition (replaced by one `!!! info "Scope"` form); dated measurements, counts that change
  with each release or harvest, and SHAs / line references outside `## Sources`.
- **Reframed, not lost:** each stripped section's lasting core is kept as plain description —
  e.g. the terminal-branch warning became "the translator's output is an end product"; "Rule 5
  in practice" became "How the record's licence is computed"; "Nobody runs it yet" became
  "Running the exporter"; history pages became a settled narrative with no "still open".
- **Added (lasting content the pages lacked):** page-classification — how a prediction is made,
  label naming and what each category suggests doing next, preparing input, reading the output
  (real rows from a committed result table), the `vX.Y` revision scheme, YOLO-cls and CLIP,
  `curl` examples, how to cite. Translator — how a translation is made, metadata (AMCR) mode
  step by step, vocabulary protection (Tag-and-Protect vs prompt glossary), language
  identification and pair discovery, a dual-pass Mermaid diagram, a code map, design limits,
  `CT2_*` / `LLM_*` environment rows. Hub — "How the ecosystem works" on the portal, a workflow
  index on Pipelines, a glossary of terms on External tools, the deployment model and a
  batch-image quick start on Operations, "Anatomy of a tool" on Architecture, the record's life
  cycle on the document contract, release steps / shared-code rule / "Contributing to this site"
  on Contributing standards, a Turtle concept and an RO-Crate excerpt from the real exporter.
- **Corrected against the current heads** (pc `vit` @ `adee922`, translator `master` @
  `71feaef`): `ct2` is a registered `--backend`; the dataset licence is CC BY-NC 4.0 everywhere
  in page-classification; `checkpoint/` is *not* git-ignored; the upload variable is
  `MAX_UPLOAD_MB`; ct2 NMT families apply no vocabulary protection (only `lindat` and the LLM
  back-ends do); the round-5 data-script findings are fixed at `a95c6c6`.
- **Site defect fixed:** the `atrium-pipeline` strips linked `../<tool>/index.md` inside raw
  HTML, which MkDocs does not rewrite — those links 404'd on the built site. Now `../<tool>/`.

## What round 7 changed

**A Workflows section: one narrative per tool** (`docs_site/workflows/`, six pages). Issue #57's
TODO asked for every workflow "from beginning to end with a clear purpose and results stated";
#4/#17 need the same text as SSH Open Marketplace workflow records, and #66 needs it as Galaxy
workflows. A narrative is written once, in a fixed shape — Purpose · At a glance · Steps ·
What you get · Limits · Provenance and licence · Where it sits · On other platforms · Sources —
so each section fills one field of the SSH Open Marketplace record, of the Galaxy `.ga` file and
of a Workflow RO-Crate. The overview page holds that field table.

- **Two depths.** page-classification and the translator, the two tools whose workflow has
  settled, get **full** narratives, with a Galaxy sheet each (datatypes, container, compute,
  network, test data, the closest tools already in Galaxy). alto-postprocess, nlp-enrich and
  llm-enrich get the **stable core** — purpose, step order, formats, licence floor, records —
  written only from behaviour present in their latest release tag and unchanged on `test`,
  with a *Scope* box pointing to their README for the rest.
- **The model it follows** is ATRIUM's own T4.2.1 pairing: DARIAH's SSH Open Marketplace
  workflow `IrpmkB` (the narrative) and its Galaxy workflow in `DARIAH-ERIC/atrium-galaxy-tools`
  (the runnable twin).
- **Glossary:** four new entries on External tools — SSH Open Marketplace, TaDiRAH, Galaxy,
  WorkflowHub and Workflow RO-Crate — and two terms, *workflow narrative* and *actionable
  workflow*.
- **Wired in:** nav group *Workflows* after Pipelines; the portal cards, "Start here" and the
  by-question table; both tool overviews' "Where to go next"; the repository map's *Docs here*
  column for the three tools without a section; the Pipelines scope note and *Other workflows*.
- **Landing cards:** `_generators/repos.py` gains a `docs_path` per repository and
  `make_stubs.py` uses it, so the "Documentation →" button of alto-postprocess, nlp-enrich and
  llm-enrich lands on their workflow page instead of a missing tool section. The regenerated
  cards also carry alto-postprocess's multi-format tagline and nlp-enrich's current chips.

## What round 8 changed

**The translator section follows `v1.2.1-beta`.** Its five tool pages and its workflow page were
written against `71feaef`/`v1.1.0-beta`, before issue #46's output guard, ALTO append rework and
language rules existed; each claim was re-read against the code and corrected:

- ALTO `append` is an `ALTERNATIVE` per `String` with `CONTENT` kept, not a block label;
- the source-language rules (detected ≥ 0.5 and ≥ 20 letters, backend-supported → element
  label → document language → default `cs`) replace the 0.2 threshold and the "answers `en`"
  failure mode; `translations.detected_source_lang`;
- the degenerate-output guard, the end-of-document re-run and the log's `status` column;
- **AMCR 2.2 does not accept `append` output** — measured, not assumed: the shipped records
  validate against the published schema as source (15/15) and `replace` output (15/15), not as
  `append` output (0/15); ALTO of either mode is valid ALTO 3.1;
- new flags and variables on Reference and Operations; `v1.2.0-beta` / `v1.2.1-beta` on the
  Changelog, and #46 on History.

**Deployment docs corrected.** The shared K8s manifest named the API image
`atrium-<tool>:<version>-api`, which the release workflow never publishes; it is
`atrium-<tool>-api:<version>`. `docs/k8s_deployment.md`'s translator rows gain `OUTPUT_MODE`,
`AMCR_FIELDS_PATH`, `LINDAT_GUARD_RETRIES` and `DEFAULT_SOURCE_LANG`.

## Layout

| Path                                    | What it is                                                                                                               |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `mkdocs.yml`                            | site config. `docs_dir: docs_site`, `site_dir: site`, `strict: true`, `validation.links.anchors: warn`                   |
| `PAGES_SETUP.md`                        | the publishing mechanics: why a branch source, how Pages is enabled, what the legacy Jekyll builder would have published |
| `docs_site/**`                          | **29 pages** — 13 hub pages + 6 Workflows pages + 2 repos × 5 tool-section pages                                         |
| `agent_dev_logs/digests/57.findings.md` | the unpublished findings register: everything round 6 removed from the pages, by owning repository, with a status        |
| `docs_site/assets/extra.css`            | styling hook; the `.atrium-pipeline` strip on each tool index uses it                                                    |
| `.github/workflows/pages.yml`           | builds `docs_site/` with `--strict`; publishes to `gh-pages` on push to `main`                                           |
| `tools/docs/requirements.txt`           | the toolchain ranges — verified with mkdocs 1.6.1, mkdocs-material 9.7.7, pymdown-extensions 12.x                        |
| `_generators/`                          | the landing-card generator: `make_stubs.py`, `repos.py` (with each card's `docs_path`), `style.css`                      |

## Page status

| Page                                                                                   | State                                                                                                                              |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `index.md`                                                                             | **written** — the portal, and how the ecosystem works                                                                              |
| `pipelines.md`                                                                         | **partial** — workflow index; W1, W4–W8, W12, W13 in full; five listed                                                             |
| `external-tools.md`                                                                    | **partial** — glossary of terms; every entry the two tools depend on; SSH Open Marketplace, TaDiRAH, Galaxy, WorkflowHub (round 7) |
| `workflows/*`                                                                          | **written** — overview, 2 full narratives, 3 stable-core narratives (round 7)                                                      |
| `development-history.md`                                                               | **partial** — per-repo index and the cross-repository chronology                                                                   |
| `tools/page-classification/*`                                                          | **written** — 5 pages, from `vit` @ `adee922` (round 6)                                                                            |
| `tools/translator/*`                                                                   | **written** — 5 pages, from release `v1.2.1-beta` (round 8)                                                                        |
| `ecosystem/repository-map.md`                                                          | **written** — six identity rows; depth for the two documented tools                                                                |
| `ecosystem/{architecture,document-contract}.md`, `contracts/{schemas,skos,rocrate}.md` | **partial** — written for page-classification and translator                                                                       |
| `agent-skills.md`, `operations.md`, `contributing-standards.md`                        | **partial** — written for page-classification and translator                                                                       |

`mkdocs.yml`'s `nav` and `docs_site/` agree in both directions, **29 ↔ 29**, checked by a
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
   The Workflows pages use 14–19 (overview, then the tools in pipeline order) and carry
   `role: workflow`.
2. **The page.** Written prose, tables and diagrams — no markers, no admonition claiming the
   page will be filled later.
3. **`## Sources`** — a provenance table: what was read, at which ref, and what was taken
   from it. The one place on a page where commit SHAs and `file:NN` references belong.

The bar every page has to clear: **a reader is better off here than on the README, and the page
stays true until the tool itself changes.** Two things earn the first — cross-repository facts
the tool repository cannot state about itself, and values read from code rather than prose.
The second rules out, since round 6, anything time-bound: drift between documents and code,
defects, open-issue status, dated measurements. Those go to
[`57.findings.md`](agent_dev_logs/digests/57.findings.md) as candidate issues for their owners.

## Verified

**Round 7 (2026-09-25)**, on hub `test` @ `8de7896` plus this round's files; narratives written against
page-classification `v1.8.0-beta`, translator `v1.1.0-beta`, alto-postprocess `v1.5.1-beta`, nlp-enrich `v0.21.0` and
llm-enrich `v0.7.0`:

- `mkdocs build --strict` → **exits 0**, no warnings, 29 pages; `nav` ↔ `docs_site/` 29 ↔ 29.
- **152 of 152** markdown tables render as HTML tables; **seven** Mermaid diagrams, as before.
- No built link points at `…/tools/{alto-postprocess,nlp-enrich,llm-enrich}/`.
- The time-bound-wording sweep leaves nothing on the six Workflows pages; the built site greps clean for e-mail
  addresses and maintainer handles.
- `_generators/make_stubs.py` output differs from each deployed `gh-pages` tree only in the intended lines;
  `ruff check _generators/` clean.
- `pytest tests/` → **154 passed, 2 skipped**; `workflow_lint.py --offline` → **OK**.

**Round 6 (2026-09-23)**, on hub `main` @ `7b0b84e` plus this round's files, pages written
against page-classification `vit` @ `adee922` and translator `master` @ `71feaef`:

- `mkdocs build --strict` → **exits 0**, no warnings, 23 pages; `nav` ↔ `docs_site/` 23 ↔ 23.
- Every markdown table renders as an HTML `<table>` — **128 of 128**, counted per page.
- **Seven** Mermaid diagrams render as `class="mermaid"` — pipelines 2, architecture 2, portal 1,
  agent skills 1, translator reference 1.
- Both tool-index pipeline strips link to directory URLs that exist in the built site.
- A sweep of every page body (outside `## Sources`) for *Known drift, so far, round N, never been
  run, still open, used to, defect, pending, today, currently*, 7-hex SHAs and `file:NN`
  references leaves only tool names (`para-drift`), settled history and behaviour descriptions.
- The built site greps clean for e-mail addresses, the partner-contacts file, maintainer handles,
  token prefixes, the grant number and CI run IDs; the RO-Crate excerpt elides author ORCIDs.
- `python3 -m pytest tests/ -q` → **141 passed, 4 skipped** (unchanged — no code touched);
  `workflow_lint.py --offline` → **OK**.
- Tables follow the maintainer's formatter; the reproduction script leaves all 23 files
  byte-stable on a second pass.

As of round 5 (2026-09-23), on the maintainer's `88bc1a6` plus that round's files:

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
  agent_dev_logs/digests/57.findings.md
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
  docs_site/workflows/index.md
  docs_site/workflows/page-classification.md
  docs_site/workflows/alto-postprocess.md
  docs_site/workflows/translator.md
  docs_site/workflows/nlp-enrich.md
  docs_site/workflows/llm-enrich.md
```

## What these rounds deliberately do not do

- **The other three tool sections.** alto-postprocess, nlp-enrich and llm-enrich keep their
  reserved `nav_order` ranges; until their sections are written, their workflow page is what
  the site says about them.
- **Any change to a tool repository's code or documentation.** The drift these pages document
  is reported, not fixed at source; each item is a candidate issue in its own repository. The
  one exception is each tool's `gh-pages` landing card, which the hub generates.
- **Tool sections behind the landing cards.** Since round 7 a card links to its tool section
  where one exists (page-classification, translator) and to its workflow page otherwise;
  `repos.py`'s `docs_path` is the one value to change when a section is written.
- **`PAGES_STRATEGY.md`.** It is referenced by `PAGES_SETUP.md`, `DEVLOG.md`,
  `57.digest.md` and `57.plan.md`, and **has never existed in this repository** — every
  `§`-reference to it points nowhere. Its 12-page design survives only as a DEVLOG summary.
  Flagged here, not written.
- **The hub's licence statement.** `mkdocs.yml`'s `copyright:` line and every landing card say
  "MIT licensed", but the hub has **no `LICENSE` and no `CITATION.cff`** — the two tools are MIT,
  the hub states nothing. Left for the maintainer to decide, not edited.
