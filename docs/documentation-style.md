# Documentation style and structure

> **Scope:** the documentation of the six ATRIUM tool repositories and of this hub. A guide, not a
> template: reuse a file that already does the job, and leave out a layer a tool does not need.

The hub explains the whole ATRIUM chain; each tool repository explains its own tool. A reader should
know where to look for a kind of information in any of the six, and reach it quickly.

## Readers

Six kinds of reader use these pages. Each arrives with different questions, and each needs a short
path to the answers.

| Reader                       | Their first questions                                                                                                             | Their path (hub → tool)                                                                                                                                                                                                            |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Archive and collection staff | What happens to my documents? What comes back? How reliable is it? What must a person check? Does anything leave the institution? | [For archives](../docs_site/for-archives.md), the [glossary](../docs_site/glossary.md), [Licences and paradata](../docs_site/ecosystem/licences.md) → the README's opening and limits                                              |
| Operators                    | Which image? What resources? Which settings? Which hosts does it call? Is it healthy? What does an error mean?                    | [Operations](../docs_site/operations.md), [Production pilot](../docs_site/pilot.md) → `service/README.md`                                                                                                                          |
| Integrators                  | How do I make a first call? What goes in and out? Where is the contract? What do the errors mean?                                 | [the document contract](../docs_site/ecosystem/document-contract.md), [Schemas](../docs_site/contracts/schemas.md) → the README's quick start, `docs/usage.md`, `service/openapi.json`                                             |
| Developers                   | How is it built? How do I test and release? Why is it this way? Where is the history?                                             | [Architecture](../docs_site/ecosystem/architecture.md), [Contributing standards](../docs_site/contributing-standards.md), [Development history](../docs_site/development-history.md) → `docs/development.md`, reference, decisions |
| Project managers             | What exists? How mature is it? What is measured, what is experimental? What depends on whom?                                      | [Status](../docs_site/status.md), [Production pilot](../docs_site/pilot.md) → the README's "Limits and maturity"                                                                                                                   |
| Researchers and evaluators   | What is the method? What was measured, on which data? How do I reproduce or cite it?                                              | → `docs/evaluation/`, `docs/how-it-works.md`, the README's citation                                                                                                                                                                |

A page serves one or two of these readers. Its first sentence says what it answers, so a reader knows at
once whether to stay.

## Layers

The layers follow the usual split of tutorial, how-to, explanation and reference
([Diátaxis](https://diataxis.fr/)), used as guidance.

| Layer                   | Reader                     | Holds                                                                                                                                           | Does not hold                                                              | Usual file                                                                                         |
|-------------------------|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| README                  | first-time visitor         | what the tool does and when to use it; inputs and outputs; one quick start with its expected result; where it fits; limits; a documentation map | algorithms, parameter catalogues, design debates, test and release history | `README.md`, about 100–250 lines                                                                   |
| Usage                   | user, integrator           | prerequisites, practical CLI or API examples, choosing a mode, reading the result, ordinary troubleshooting                                     | code internals, research notebooks                                         | `docs/usage.md` or `docs/getting-started.md`                                                       |
| Operations and API      | deployer, integrator       | endpoints, formats, configuration, limits, errors and what to do about them, deployment                                                         | a second copy of the API specification                                     | `service/README.md` (the runbook); `service/openapi.json`                                          |
| How it works            | anyone who wants the idea  | the processing flow in plain words, the components, why it is built this way; one diagram if it helps                                           | low-level rules before the concepts                                        | `docs/how-it-works.md` or `docs/architecture.md`                                                   |
| Reference               | developer, expert          | complete parameter tables, formats, schemas, rules, thresholds, diagnostic fields, edge cases                                                   | introductions and history                                                  | `docs/configuration.md`, `docs/reference/`                                                         |
| Evaluation and limits   | anyone judging the results | what was measured, on which data, with which metric; known failure modes; experimental features                                                 | the claim that passing unit tests shows model quality                      | `docs/evaluation/`                                                                                 |
| Development and history | contributor                | setup, tests, fixtures, CI, releases; dated decisions; the changelog; the pointer to the working records                                        | experiments woven into the user guide                                      | `CONTRIBUTING.md` (its Release History is the changelog), `docs/development.md`, `docs/decisions/` |

The full AMČR chain, the shared contracts and the cross-tool architecture belong to the hub and its
site. A tool's documentation links to them and does not restate them.

## Rules

1. **Write for the reader.** Start with the problem the tool solves, the result it produces and the next
   thing the reader can do. Plain, precise English; short paragraphs; one term per concept.
2. **Disclose progressively.** The README can be skimmed in two minutes. Depth is one link away, never
   in the way.
3. **No decorative emoji**, in headings or in text. Few badges, no stacks of callouts. Plain headings keep
   their anchors stable.
4. **A heading names the question it answers.** Tables are for comparisons and reference data, not a
   substitute for an explanation. A diagram is there because it explains.
5. **Keep levels of certainty apart:** released behaviour, optional or research features, plans, measured
   results and known limits. A limit stands next to the instruction it affects.
6. **Every tool has a copy-and-run example** with its input, its expected result and any external
   service it needs, checked against the code it describes (see [Examples](#examples)).
7. **One home per contract.** OpenAPI, JSON Schema, the configuration reference and the shared contracts
   each have one authoritative file; other pages link to it.
8. **Current guidance and its history live apart.** Calibration rounds, superseded methods and dated
   decisions move to evaluation pages, decision records or the changelog. Evidence is moved, not dropped.
9. **Documentation is edited.** Generated or code-synchronised text is an input. Each major page is read
   for order, length and clarity by a person before it ships.
10. **Parked features stay out of the user path.** A feature parked during the AMČR pilot is not
    introduced in a README, a usage page or a how-it-works page. Its reference section stays, and opens
    with the [parked notice](#standard-sentences); an endpoint that still exists stays in the runbook's
    endpoint table, marked parked.

### Plain language

- **Short sentences.** Aim for an average of 20 words or fewer, and split any sentence over 35. One idea
  per sentence; the subject and the verb come first.
- **Asides become sentences.** A parenthesis that needs a comma inside it is a second sentence.
- **Define a term where a page first uses it,** or link it to the
  [glossary](../docs_site/glossary.md). Readers outside ÚFAL do not know "ATR", "docproc", "held-out",
  "fold", "paradata", "seed" or "TEITOK".
- **A number carries its unit and its base:** "95.8 % of 4,795 held-out pages", not "95.8 %".
- **One name per thing,** everywhere:

  | Write                                                                          | Not                         |
  |--------------------------------------------------------------------------------|-----------------------------|
  | AMČR, ARÚP, ARÚB                                                               | AMCR, ARUP, ARUB, ARÚ/B     |
  | born-digital                                                                   | digital-born                |
  | the record (first use: the ATRIUM document record)                             | the JSON, the document file |
  | paradata (first use: the paradata of a run)                                    | run log, run record         |
  | the ATR (first use: the ATR, AIS CR's text-recognition service)                | OCR, when the ATR is meant  |
  | docproc (first use: docproc, the layout format of digital-convert and the ATR) | the docproc JSON            |
  | the AMČR pilot                                                                 | the S2 pilot, S2            |
  | behaviour, licence (noun)                                                      | behavior, license (noun)    |

  Code identifiers keep their spelling (`categ`, `needsAtr`, `license_url`).

### Shorthand and history

- **No tracker shorthand in the user and operator path.** A README, usage page, runbook, configuration
  page or how-it-works page states the fact, not the issue, work package, meeting or round it came from.
  Shorthand includes issue numbers, decision and hand-off codes from meeting documents ("D13", "H3"),
  numbered requests ("ask 3"), section signs that point into internal documents ("§4.4"), and dated
  phrases such as "since the output contract of 12 November". Link an issue only for an open problem the
  reader may want to follow, once, at the end of the sentence. A heading never carries an issue number.
- **No version history in the user path.** "Since v1.10.0-beta", "formerly" and "until" belong in
  CONTRIBUTING's Release History or `docs/development.md`. A README keeps one line about a former name,
  in its last section.

### Summary first

- **Evaluation and decision pages open with "In short":** what was measured or decided, the main figure or
  choice, what it means for a user, and what it does not show. Five lines at most.
- **A decision page** then states Decision · Status · Why · Consequence, before the dated record.

### Standard sentences

Some facts appear on many pages. Each has one wording, and a page that states the fact uses it, adapted
only in its grammar. The route itself is told once, on the hub's
[Pipelines](../docs_site/pipelines.md) page; a tool's "Where it fits in ATRIUM" says its own step in one
paragraph and links there.

| Fact            | Wording                                                                                                                                                                                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| record version  | The tools write record schema 2.0. The published schema is `doc-schema-v1`; 2.0 is published as `doc-schema-v2` once the pilot has proven it.                                                                                                                 |
| failure         | A step that cannot finish fails the job and writes nothing: there is no partial output.                                                                                                                                                                       |
| licences        | Each run lists the components it used, each with its own licence or terms. No licence of an output is computed: the rights in an output follow the source document.                                                                                           |
| LINDAT hold     | Until the terms of LINDAT's services are settled ([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)), AMČR does not publish outputs made through them: the linguistic layer, the entities, the TEITOK file and the English metadata.      |
| parked notice   | Parked during the AMČR pilot: not part of the pipeline or the service.                                                                                                                                                                                        |
| acknowledgement | Funded by the European Union under Horizon Europe (ATRIUM, GA 101132163), with the support of the LINDAT/CLARIAH-CZ (LM2023062) and AIS CR (LM2023031) research infrastructures, funded by the Ministry of Education, Youth and Sports of the Czech Republic. |

### Examples

- **Run from a checkout first.** A quick start shows the command line or the service from a checkout of
  the branch it documents; the published image follows, with its tag written `<version>`. Until a
  release carries what the page describes, the page names the first release that does, and sends readers
  of older tags to the README at that tag.
- **A server runs in the background.** Start it with `docker run -d --name …` or in a second terminal,
  wait for `/ready`, then call it; stop it at the end. Never put a foreground server and the `curl` that
  calls it in one code block.
- **Write into a scratch folder.** An example writes into `out/` or a temporary folder, never into a
  tracked samples folder whose files would then prove nothing.
- **Show the expected result,** abridged to the fields a reader should check, and say what happens when
  an external service it calls is missing.

### Links

Inside a repository, links are relative. The hub links its own documents at `blob/main` (the branch the
site is built from), and a tool's documentation at `blob/test` (the branch the next release is cut
from). `python3 tools/docs_check.py` checks relative links and their anchors. It does not follow a link into
another repository or to the site: check those by hand when the heading they point to changes.

### Working records

Each repository's `agent_dev_logs/` (the DEVLOG, the per-issue digests and plans, the issue exports) is the
maintainers' working record, not documentation for readers. **Exactly one Markdown file outside it points
there**: `docs/development.md` in a tool, and
[`docs_site/development-history.md`](../docs_site/development-history.md) in the hub. Every other page cites
the issue instead. A folder name in a technical statement, such as the files an image or a published site
leaves out, is not a pointer.

## README outline

[`templates/README.template.md`](templates/README.template.md) has the skeleton. Its sections:

1. What it does and when to use it, in words a non-specialist follows.
2. Inputs and outputs.
3. What you need, then the quick start, with the expected result.
4. Its role in the ATRIUM workflow (link to the [hub site](https://ufal.github.io/atrium-project/)).
5. Limits and maturity: one sentence per limit, then what it means for the reader, then the link.
6. Documentation map, grouped by reader: use it, run the service, judge the results, change the code.
7. Licence, citation and acknowledgements (the [standard wording](#standard-sentences)); a former name,
   if any, in one line.

Adapt it: a section that does not matter for a tool is left out, not filled.

## Checklist for a documentation pull request

- [ ] The current behaviour and its limits are stated, next to the instructions they affect.
- [ ] The quick start or example works as written from a clean checkout or the published image, and
      shows its expected result.
- [ ] Each page sits in its layer; nothing in the README needs the reference to be understood.
- [ ] Each page's first sentence says what it answers; its terms are defined or linked to the glossary.
- [ ] Sentences average about 20 words; one spelling per name; the standard sentences are used.
- [ ] No issue numbers, decision codes or version history in README, usage, runbook, configuration or
      how-it-works text.
- [ ] Parked features are out of the user path, and their reference sections carry the parked notice.
- [ ] Evaluation and decision pages open with "In short".
- [ ] Links and anchors resolve (`python3 tools/docs_check.py --repo <repo>` in the hub).
- [ ] No contract is copied: the API, schemas and configuration are linked to their one home.
- [ ] Only `docs/development.md` (in the hub, `docs_site/development-history.md`) points into
      `agent_dev_logs/`.
- [ ] When content moves, the description has a relocation map (old section → new file and section),
      and confirms that caveats, examples and evidence were kept.
- [ ] Someone who did not write the tool followed the quick start and found the reference; for a page
      written for archive staff, operators or managers, someone from that group read it.

## The check

`tools/docs_check.py` (stdlib only, like `tools/runbook_check.py`) reads a tool repository's Markdown and
reports:

- decorative emoji in a heading (an error);
- a relative link to a file that does not exist, or an anchor that matches no heading of its target
  (errors; GitHub's anchor rules, U+FE0F included);
- a README without a documentation map or without a link to this guide (errors);
- a README longer than 250 lines (a warning).

All six tools and the hub pass it. It runs in every repository's Workflow Policy Lint
(`workflow-lint.reusable.yml`) on pull requests, with its report in the run's summary. It is advisory
until an independent reader has reviewed the tools' documentation, and blocking after that
([`ci_policy.md`](ci_policy.md)).

Planned additions: a warning for a page whose sentences average over 25 words, and one for tracker
shorthand in the user and operator path; an error when more than one Markdown file points into
`agent_dev_logs/`. Like the length warning, the sentence figure is a prompt for an editor, not a target.
