---
title: Licences and paradata
nav_order: 7
status: published
round: 8
issue: 6
---

# Licences and paradata

> **Pending: record schema 2.0 and paradata 3.0** ([atrium-project#84](https://github.com/ufal/atrium-project/issues/84)).
> This page describes the 1.x record the released tools write today. On the hub branch `84-doc-schema-v2` the record
> holds content only (no `provenance`, `assembled`, `derived_from`, `regenerable` or licence), ocr-postprocess is the one
> writer of `pages`, `content` and `lines`, and the paradata name each input and output by distribution name and SHA-512.
> Each tool adopts it in its own repository; see the hub's `docs/document_schema.md` and `docs/paradata_schema.md`.

This page explains, without code, what the ATRIUM tools record about the software, models and data they use,
and who states the rights in what they produce.

## What a run records

Every run of an ATRIUM tool writes a short log, its **paradata**. It says which program and version ran, when,
with which settings, and what it produced. It also lists the **components** the run used: the models, datasets,
vocabularies and web services. Each component is listed with its own licence, or, for a web service, the terms of
use it is offered under.

The document record that travels through the pipeline points to the paradata of every run that wrote to it. So
for any record you can find out which tools touched it and what each of them used.

A component's licence covers that component. It does not, by itself, set the rights in what the run produces:

- **A licence covers what it is attached to:** a program, a model or a dataset. Using a tool does not put
  what it produces under the tool's licence.
- **Web services have terms of use, not a licence for their output.** LINDAT, for example, licenses its
  software and models and offers its services under [Terms of Use](https://lindat.mff.cuni.cz/en/terms-of-use).
- **Using a component is not, by itself, making a derived work of it.** For example, tagging a line with one
  term from a vocabulary. Whether an output is a derived work is a legal question.
- **The rights in an output depend first on the source document.** No tool knows those rights.

The tools' pages list each component with its licence or terms. They do not say that a result "is" under any
licence.

## An old field to ignore

Records and paradata still carry one older field: `provenance.license` in the record, `license` in the paradata.
It was calculated by a rule the project has dropped: the most restrictive licence among the components. It is
not a licence, a summary or a warning, and nothing should be read from it. Use the list of components instead.
From the pilot releases of 4 November 2026 the record marks it `provenance.license_basis: "calculated"`, and an
RO-Crate export no longer writes it as the licence of the crate (below).

## What changes

The [proposal on #6](https://github.com/ufal/atrium-project/blob/test/docs/proposals/rights-and-policy.md) keeps
what is useful and drops the calculated field:

1. **Keep the list of components,** each with its own licence or terms and where that was read, and make it
   more precise.
2. **Record which processing policy allowed the run.** The deployment's operator (AMČR, for the pilot) writes
   the policy: for example, whether texts may be sent to an external service. Each document also carries its own
   permission, and a document without one is not sent to an external service.
3. **State the rights in an output only when someone entitled to do so asserts them.** Without that, the rights
   are unknown, and the record says nothing.

AMČR agreed to this on 22 October 2026: AMČR states the rights of the outputs it publishes, and no tool makes
an automatic or default licence assertion. In the shared modules:

- **done in the pilot releases of 4 November:** an RO-Crate export points its `license` to a "no licence asserted" entity
  (`#no-licence-asserted`), as agreed on [#6](https://github.com/ufal/atrium-project/issues/6) on 29 October
  2026; the record marks the calculated field `provenance.license_basis: "calculated"`; the paradata's notes
  list the components and say that no output licence is asserted;
- **next:** the record's next schema version moves the calculated field to `provenance.calculated_license`, and
  the paradata's next version stops writing it.

Records and paradata written before stay as they are.

## Where the details are

| To see                                      | Read                                                                                                                                                                  |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| each tool's components and their licences   | the tool's workflow page, under [Workflows](../workflows/index.md)                                                                                                    |
| how the record grows and points to paradata | [The document contract](document-contract.md)                                                                                                                         |
| every field of the paradata file            | [`docs/paradata_schema.md`](https://github.com/ufal/atrium-project/blob/test/docs/paradata_schema.md)                                                                 |
| the proposal in full, for implementers      | [`docs/proposals/rights-and-policy.md`](https://github.com/ufal/atrium-project/blob/test/docs/proposals/rights-and-policy.md)                                         |
| the discussion                              | [#6](https://github.com/ufal/atrium-project/issues/6), [#4](https://github.com/ufal/atrium-project/issues/4), [#78](https://github.com/ufal/atrium-project/issues/78) |
