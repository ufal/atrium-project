---
title: Licences and paradata
nav_order: 7
status: published
round: 8
issue: 6
---

# Licences and paradata

This page explains, without code, what the ATRIUM tools record about the software, models and data they use,
what the one licence they compute means and does not mean, and what is proposed instead.

## What a run records

Every run of an ATRIUM tool writes a short log, its **paradata**. It says which program and version ran, when,
with which settings, and what it produced. It also lists the **components** the run used: the models, datasets,
vocabularies and web services. Each component is listed with its own licence, or, for a web service, the terms of
use it is offered under.

The document record that travels through the pipeline points to the paradata of every run that wrote to it. So
for any record you can find out which tools touched it and what each of them used.

## The licence the tools compute, and what it is not

From that list of components, the shared module `para_licenses.py` also computes **one label**: the most
restrictive of the component licences, on a scale from public domain to CC BY-NC-SA 4.0. It was added as a
warning. If a run used a model published for non-commercial use, the label says so at a glance. The record
carries the label as `provenance.license`, and an RO-Crate export states it as the licence of the crate.

**The label is not the licence of the output, and should not be read as one:**

- **A licence covers what it is attached to:** a program, a model or a dataset. Using a tool does not put
  what it produces under the tool's licence.
- **Web services have terms of use, not a licence for their output.** LINDAT, for example, licenses its
  software and models and offers its services under [Terms of Use](https://lindat.mff.cuni.cz/en/terms-of-use).
- **"The strictest wins" says nothing about compatibility.** Some licences cannot be combined at all. Picking
  the strictest one does not show that the others are respected.
- **Using a component is not, by itself, making a derived work of it.** For example, tagging a line with one
  term from a vocabulary. Whether an output is a derived work is a legal question, and the label cannot answer
  it.
- **The rights in an output depend first on the source document.** No tool knows those rights.

The tools' pages now list each component with its licence or terms. They do not say that a result "is" under any
licence.

## What is proposed

The [proposal on #6](https://github.com/ufal/atrium-project/blob/test/docs/proposals/rights-and-policy.md) keeps
what is useful and drops the label:

1. **Keep the list of components,** each with its own licence or terms and where that was read, and make it
   more precise.
2. **Record which processing policy allowed the run.** The deployment's operator (AMČR, for the pilot) writes
   the policy: for example, whether texts may be sent to an external service.
3. **State the rights in an output only when someone entitled to do so asserts them.** Without that, the rights
   are unknown, and the record says nothing.

This changes what records and crates say, so it waits for AMČR's agreement before any shared module changes
([`shared_components.md`](https://github.com/ufal/atrium-project/blob/test/docs/shared_components.md), class c).
Until then, read `provenance.license` as "the most restrictive licence among the components used", nothing more.

## Where the details are

| To see                                      | Read                                                                                                                                                                  |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| each tool's components and their licences   | the tool's workflow page, under [Workflows](../workflows/index.md)                                                                                                    |
| how the record grows and points to paradata | [The document contract](document-contract.md)                                                                                                                         |
| every field of the paradata file            | [`docs/paradata_schema.md`](https://github.com/ufal/atrium-project/blob/test/docs/paradata_schema.md)                                                                 |
| the proposal in full, for implementers      | [`docs/proposals/rights-and-policy.md`](https://github.com/ufal/atrium-project/blob/test/docs/proposals/rights-and-policy.md)                                         |
| the discussion                              | [#6](https://github.com/ufal/atrium-project/issues/6), [#4](https://github.com/ufal/atrium-project/issues/4), [#78](https://github.com/ufal/atrium-project/issues/78) |
