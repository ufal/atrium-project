---
title: Workflows
nav_order: 14
status: published
round: 7
issue: 57
authored: true
---

# Workflows

One page per tool, telling its workflow from beginning to end: what it is for, each step with
the formats that go in and come out, what the user ends up with, what licence that result
carries, and where the same workflow is published on other platforms.

[Pipelines](../pipelines.md) shows how the tools connect to each other. These pages take one
tool at a time and describe it the way a person using only that tool meets it.

## The five narratives

| Tool                                          | Depth       | What the workflow does                                                                                     | SSH Open Marketplace                                                                                                                                   |
|-----------------------------------------------|-------------|------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [page-classification](page-classification.md) | full        | sorts scanned archive pages into eleven categories that decide how each page is processed next             | tool [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw)                                                                            |
| [alto-postprocess](alto-postprocess.md)       | stable core | turns OCR output into per-page text and a table of text lines labelled by language and OCR quality         | tool [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU)                                                                            |
| [translator](translator.md)                   | full        | translates the text inside XML documents and writes it back without changing their structure               | tool [`CizIUW`](https://marketplace.sshopencloud.eu/tool-or-service/CizIUW) · workflow [`13eHAZ`](https://marketplace.sshopencloud.eu/workflow/13eHAZ) |
| [nlp-enrich](nlp-enrich.md)                   | stable core | adds lemmas, part-of-speech tags, syntax and named entities to text lines, and writes TEITOK XML           | tool [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X)                                                                            |
| [llm-enrich](llm-enrich.md)                   | stable core | maps text onto the AMČR and TEATER vocabularies with a language model, and converts born-digital documents | tool [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo)                                                                            |

The five tools are also steps of one chain: the AMČR text workflow, which ARÚP curates on the
SSH Open Marketplace as [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).
[Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline) draws the same chain from
the tools' side.

## What every narrative contains

The sections are fixed, so that the same text can be pasted into a workflow record without
being rewritten, and so that a reader who has read one narrative can find their way in the
next.

1. **Purpose** — what the workflow is for, in one paragraph.
2. **At a glance** — inputs and outputs with their formats, the ways the tool runs, the
   hardware it needs, what it reaches over the network, the licence of the code and the rule
   for the licence of the output.
3. **Steps** — numbered. Each step says what happens, what goes in and what comes out (with
   formats), and the research activity it performs, named with the
   [TaDiRAH](../external-tools.md#tadirah) terms the SSH Open Marketplace uses.
4. **What you get** — the outputs, and how to read them.
5. **Limits** — what follows from how the tool works. Nothing here describes the state of
   work in progress.
6. **Provenance and licence** — the paradata log every run writes, the block the tool owns in
   the [document record](../ecosystem/document-contract.md), and how the licence of a run is
   computed.
7. **Where it sits** — the cross-tool workflows on [Pipelines](../pipelines.md) the tool takes
   part in, and its step in the AMČR chain.
8. **On other platforms** — its SSH Open Marketplace records and a Galaxy sheet: the Galaxy
   datatypes of its inputs and outputs, the container, compute and network needs, test data,
   and the closest tools already available in Galaxy.
9. **Sources** — what the page was written from, and at which release.

## Two depths

**Full** narratives cover all nine sections. They are written for tools whose workflow has
settled: page-classification and the translator.

**Stable-core** narratives are written for tools whose rules, defaults or inputs change from
release to release: alto-postprocess, nlp-enrich and llm-enrich. They give the purpose, the order of
the steps, the formats, the licence floor and the records, and leave out thresholds, default
models and options that are not part of a release. Each says so in a *Scope* box at the top,
and links to the tool's README for the rest. A full narrative replaces the stable core once
the workflow has settled.

## One text, three platforms

A workflow is published in three places, each with its own fields. The narrative is written
so that each field can be filled from one section:

| Narrative                      | SSH Open Marketplace workflow record                                        | Galaxy workflow (`.ga`)                                     | Workflow RO-Crate (WorkflowHub)       |
|--------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------|---------------------------------------|
| page title                     | label                                                                       | `name`                                                      | `name`                                |
| Purpose                        | description (about 1,500 characters)                                        | `annotation`                                                | `description`                         |
| At a glance — formats          | input format, output format                                                 | labelled workflow inputs and outputs, with Galaxy datatypes | `input`, `output` (formal parameters) |
| Steps                          | steps: label, description, activity, input and output format, related items | steps: `label`, `annotation`, tool id and version           | the workflow's parts                  |
| Provenance and licence         | `license` property, licence table in the description                        | `license` (SPDX identifier)                                 | `license`                             |
| Sources — authors              | actors (Author, Contact), with ORCID                                        | `creator` (Person, with ORCID)                              | `creator`                             |
| Sources — release              | version                                                                     | `release`                                                   | `version`                             |
| On other platforms             | related items, accessible at, external identifiers                          | `tags`; links in the annotation                             | `url`                                 |
| On other platforms — test data | media and "see also" links                                                  | `-tests.yml` and `test-data/`                               | the Workflow Testing RO-Crate         |

The same bar applies on every platform: a record should stay true until the tool changes.
The version field is the only value expected to change with each release.

## The model this follows

The pairing of a narrative with a runnable workflow already exists inside ATRIUM. Task 4.2.1,
vocabulary-driven information extraction, is described step by step in the SSH Open
Marketplace workflow [`IrpmkB`](https://marketplace.sshopencloud.eu/workflow/IrpmkB), and the
same workflow runs as a Galaxy workflow in DARIAH's
[`atrium-galaxy-tools`](https://github.com/DARIAH-ERIC/atrium-galaxy-tools) repository, whose
workflow list links back to the narrative.

The narratives here follow that pairing, and add the workflow metadata that Galaxy's own
best practice asks for: an annotation, a creator with an ORCID, a licence, labelled inputs and
outputs, an annotation on every step, and tests with sample data. [External tools →
Galaxy](../external-tools.md#galaxy) explains the Galaxy terms.

## Keeping the platforms in step

* **On every release** — the version field of the SSH Open Marketplace record, and the release
  named in the narrative's Sources.
* **When a step, a format or a licence component changes** — the narrative first, then the
  matching step of the SSH Open Marketplace record, then the Galaxy workflow's annotation.
* **Licence rows** always come from the tool's `para_config.txt`, the machine-readable
  declaration each run's licence is computed from.

## Sources

Written from the five tool repositories at their release tags and from the SSH Open
Marketplace and Galaxy sources below. This table records **provenance**, not a build
instruction.

| Source                                                                                                                                  | What was taken from it                                               |
|-----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| SSH Open Marketplace records `RER7Fw`, `YParYU`, `CizIUW`, `EMhu3X`, `13eHAZ`, `0xSpVP`, `IrpmkB`                                       | record identifiers; the fields of a workflow record and of its steps |
| SSH Open Marketplace metadata guidelines (`SSHOC/sshoc-marketplace-frontend`, `content/contribute/metadata-guidelines`)                 | the recommended description length; relation types                   |
| `DARIAH-ERIC/atrium-galaxy-tools` — `README.md`, `workflows/README.md`, `workflows/T4.2.1-Vocab_Driven_IE.ga`, `tools/atrium_tools.xml` | the narrative-to-Galaxy pairing                                      |
| `galaxyproject/iwc` — `workflows/README.md`; `galaxyproject/planemo` — `docs/best_practices_workflows.rst`                              | workflow metadata best practice                                      |
| `galaxyproject/training-material` — `topics/digital-humanities/tutorials/introduction_to_dh/workflows/`                                 | a published humanities workflow with its tests                       |
| the five narratives on this site                                                                                                        | the table of tools                                                   |
