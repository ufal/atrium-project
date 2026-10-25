# Documentation style and structure

> **Status:** guide, added 2026-10-20 for [#79](https://github.com/ufal/atrium-project/issues/79).
> **Scope:** the six tool repositories' documentation, and the hub's. A guide, not a template:
> reuse a file that already does the job, and leave out a layer a tool does not need.

The hub explains the whole ATRIUM chain; each tool repository explains its own tool. A reader should
know where to look for a kind of information in any of the six, and reach it quickly.

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
| Development and history | contributor                | setup, tests, fixtures, CI, releases; dated decisions; the changelog                                                                            | experiments woven into the user guide                                      | `CONTRIBUTING.md` (its Release History is the changelog), `docs/development.md`, `docs/decisions/` |

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
   service it needs, checked against a released version.
7. **One home per contract.** OpenAPI, JSON Schema, the configuration reference and the shared contracts
   each have one authoritative file; other pages link to it.
8. **Current guidance and its history live apart.** Calibration rounds, superseded methods and dated
   decisions move to evaluation pages, decision records or the changelog. Evidence is moved, not dropped.
9. **Documentation is edited.** Generated or code-synchronised text is an input. Each major page is read
   for order, length and clarity by a person before it ships.

## README outline

[`templates/README.template.md`](templates/README.template.md) has the skeleton. Its sections:

1. What it does and when to use it.
2. Inputs and outputs.
3. Quick start, with the expected result.
4. Its role in the ATRIUM workflow (link to the [hub site](https://ufal.github.io/atrium-project/)).
5. Limits and maturity.
6. Documentation map: usage, API and operations, configuration, how it works, reference, evaluation,
   development.
7. Licence, citation and acknowledgements.

Adapt it: a section that does not matter for a tool is left out, not filled.

## Checklist for a documentation pull request

- [ ] The current behaviour and its limits are stated, next to the instructions they affect.
- [ ] The quick start or example works from a clean checkout or the published image, and shows its
      expected result.
- [ ] Each page sits in its layer; nothing in the README needs the reference to be understood.
- [ ] Links and anchors resolve (`python3 tools/docs_check.py --repo <repo>` in the hub).
- [ ] No contract is copied: the API, schemas and configuration are linked to their one home.
- [ ] When content moves, the description has a relocation map (old section → new file and section),
      and confirms that caveats, examples and evidence were kept.
- [ ] Someone who did not write the tool followed the quick start and found the reference.

## The check

`tools/docs_check.py` (stdlib only, like `tools/runbook_check.py`) reads a tool repository's Markdown and
reports:

- decorative emoji in a heading (an error);
- a relative link to a file that does not exist, or an anchor that matches no heading of its target
  (errors; GitHub's anchor rules, U+FE0F included);
- a README without a documentation map or without a link to this guide (errors);
- a README longer than 250 lines (a warning).

All six tools and the hub pass it since 2026-10-25. It runs in every repository's Workflow Policy
Lint (`workflow-lint.reusable.yml`), on pull requests and pushes, with its report in the run's summary.
It is advisory until the newcomer review (#79 D) is in, and blocking after it
([`ci_policy.md`](ci_policy.md)).
