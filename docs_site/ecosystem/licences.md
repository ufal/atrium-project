---
title: Licences and paradata
nav_order: 7
status: published
issue: 79
---

# Licences and paradata

This page explains, without code, what the ATRIUM tools record about the software, models and data they
use, and who states the rights in what they produce. It is for archive staff and integrators.

## What a run records

Every stored output of a document — in AMČR's words, every *distribution*, such as the layout, the record,
the TEITOK file or the English metadata — has its own **paradata**: a short account of the runs that made
its current version. For each step it says which program and version ran, for which organisation, when,
with which settings, what it read and what it wrote. Inputs and outputs are named by their distribution
name and their SHA-512 checksum. Earlier versions of an output keep their paradata in AMČR's archive.

The paradata also list the **components** each run used: the models, datasets, vocabularies and web
services. Each component is listed with its own licence, or, for a web service, the terms of use it is
offered under. The record itself carries no run data: what a step did is in the paradata, never in the
record ([The document contract](document-contract.md#where-the-run-history-is)).

## Three layers, nothing computed

The rights around an output have three layers. None of them is calculated from the others.

| Layer                    | What it says                                                                                               | Where you find it                                                                                             |
|--------------------------|------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| 1. Rights in the content | the document's own licence, otherwise AMČR's default, CC BY-NC 4.0; the outputs derived from it inherit it | AMČR's RO-Crate of the record, the File API (`Link: rel="license"`), the Digital Archive, OAI-PMH and ARIADNE |
| 2. Produced with         | each step's components and their terms, listed one by one, never merged into one licence                   | the paradata of the output, shown beside the download                                                         |
| 3. AMČR's conditions     | a condition of reuse that AMČR decides to honour, stated with its reason                                   | AMČR's policy, shown with layer 1                                                                             |

A component's licence covers that component. It does not, by itself, set the rights in what the run
produces:

- **A licence covers what it is attached to:** a program, a model or a dataset. Using a tool does not put
  what it produces under the tool's licence.
- **Web services have terms of use, not a licence for their output.** LINDAT, for example, licenses its
  software and models and offers its services under [Terms of Use](https://lindat.mff.cuni.cz/en/terms-of-use).
- **Using a component is not, by itself, making a derived work of it.** For example, tagging a line with one
  term from a vocabulary. Whether an output is a derived work is a legal question.
- **The rights in an output depend first on the source document.** No tool knows those rights, so no tool
  states them. AMČR does, in layer 1.

The tools' pages list each component with its licence or terms. They never say that a result "is" under
any licence. An RO-Crate that a tool exports names `#no-licence-asserted` as its licence: an entity that
says no licence is asserted, because RO-Crate requires the field.

## What may leave the archive

- **The pipeline decides, per job,** what an external service may receive, from the job's licence flag.
- **LINDAT** is a secure service, and sending protected metadata fields to it for translation is allowed.
  The English metadata (`metadata-en`) then follows exactly the access rules of the metadata it was made
  from, in AMČR, the Digital Archive, the API and OAI-PMH.
- **The ATR's cloud fallback is off** in the pilot: the text recognition runs on AIS CR's own cluster.
- **Until the terms of LINDAT's services are settled** ([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)),
  AMČR does not publish outputs made through them: the linguistic layer, the entities, the TEITOK file and
  the English metadata.

## Older records and crates

Records of schema 1.x and paradata of schema 2.x carried a calculated field: `provenance.license` in the
record, `license` in the paradata. It was the most restrictive licence among the components, a rule the
project has dropped. It was never the licence of an output, and nothing should be read from it. Record
schema 2.0 and paradata 3.0 no longer have it, and reading an older file drops it in memory; files on disk
stay as they were written. Use the list of components instead.

## Where the details are

| To see                                      | Read                                                                                                                                                                  |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| each tool's components and their licences   | the tool's workflow page, under [Workflows](../workflows/index.md), and its `docs/reference/licences.md`                                                              |
| what the record holds, and who writes it    | [The document contract](document-contract.md)                                                                                                                         |
| every field of the paradata file            | [`docs/paradata_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/paradata_schema.md)                                                                 |
| the RO-Crate view                           | [RO-Crate export](../contracts/rocrate.md)                                                                                                                            |
| the October proposal, and what became of it | [`docs/proposals/rights-and-policy.md`](https://github.com/ufal/atrium-project/blob/main/docs/proposals/rights-and-policy.md)                                         |
| the discussion                              | [#6](https://github.com/ufal/atrium-project/issues/6), [#4](https://github.com/ufal/atrium-project/issues/4), [#78](https://github.com/ufal/atrium-project/issues/78) |

## Sources

| Source                                                                                                        | What was taken from it                                          |
|---------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| ARÚP's output contract of 12 November 2026, sections 6 and 8                                                  | the paradata per distribution, the three layers, what may leave |
| `atrium-project/docs/templates/shared/atrium_paradata.py`, `atrium_document.py`, `atrium_rocrate.py` (`test`) | paradata 3.0, the removed fields, `#no-licence-asserted`        |
