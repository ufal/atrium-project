---
title: Status
nav_order: 22
status: partial
issue: 79
---

# Status at a glance

This page is for project managers and coordinators. It says what each tool is ready for, what has been
measured, what is still experimental and what it depends on. It is updated when the pilot's release set
changes; every fact links to the page that holds it.

## The six tools

All six are beta releases. A release's images are scanned before they are published and listed by
digest ([the release gate](operations.md#the-release-gate)). Its API contract is checked against the
previous release's, as each service's runbook describes under "OpenAPI". The table gives the pilot's
starting releases; the route of this site, with record schema 2.0 and docproc, comes with the 2.0.0-beta
releases of 26 November 2026.

| Tool                | Starting release | What has been measured                                                        | Experimental or not evaluated                                              | Needs at run time                                            | Limits                                                                                               |
|---------------------|------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| page-classification | `1.12.3-beta`    | 94.6–95.9 % of pages typed right first, on about 4,800 unseen pages per model | born-digital pages; the optional YOLO backend; the ensemble's own accuracy | nothing outside (models downloaded at first start)           | [README](https://github.com/ufal/atrium-page-classification/blob/test/README.md#limits-and-maturity) |
| ocr-postprocess     | `1.15.3-beta`    | rule changes, on 2,067 hand-labelled lines and over both collections          | a full validation of the five labels; lines not in Czech                   | nothing outside (models downloaded at first start)           | [README](https://github.com/ufal/atrium-ocr-postprocess/blob/test/README.md#limits-and-maturity)     |
| digital-convert     | `1.4.4-beta`     | tried on 15 AMČR excavation reports; no accuracy figure                       | the optional Docling engine; uploads over 250 MB                           | nothing outside                                              | [README](https://github.com/ufal/atrium-digital-convert/blob/test/README.md#limits-and-maturity)     |
| nlp-enrich          | `1.3.3-beta`     | nothing yet on archival documents                                             | languages other than Czech                                                 | LINDAT's UDPipe and NameTag, or copies of them               | [README](https://github.com/ufal/atrium-nlp-enrich/blob/test/README.md#limits-and-maturity)          |
| keyword-extract     | `1.6.4-beta`     | nothing yet                                                                   | the vocabulary-based keywords: a research output                           | a language-model service, for vocabulary-based keywords only | [README](https://github.com/ufal/atrium-keyword-extract/blob/test/README.md#limits-and-maturity)     |
| translator          | `1.7.5-beta`     | a small backend comparison, without reference translations                    | translation quality; the alternative backends                              | LINDAT's translation service, or a model server you run      | [README](https://github.com/ufal/atrium-translator/blob/test/README.md#limits-and-maturity)          |

What each tool does, in plain words, and what a person should check: [For archives](for-archives.md).

## The pilot

| When                         | What                                                                                                   | Who        |
|------------------------------|--------------------------------------------------------------------------------------------------------|------------|
| 4 November 2026              | the release set of [#77](https://github.com/ufal/atrium-project/issues/77), the pilot's starting point | ÚFAL       |
| 12 November 2026             | ARÚP's output contract: the route, the record and the paradata for the pilot                           | ARÚP, ÚFAL |
| second half of November 2026 | acceptance on AMČR's own cluster, one result row per service                                           | AMČR, ÚFAL |
| December 2026 – January 2027 | the AMČR pilot: the chain assembled step by step, each step with the release proven when it joins      | AMČR       |

The handover, the runbooks and the contacts: [Production pilot](pilot.md).

## What the tools depend on

- **The ATR**, AIS CR's text-recognition service, reads the scanned pages; a document with any page that
  needs it goes through it whole.
- **LINDAT's public services** (UDPipe, NameTag, translation) have no service-level agreement. A
  deployment can run its own copies instead. Until their terms are settled
  ([#78](https://github.com/ufal/atrium-project/issues/78)), AMČR does not publish outputs made through
  them: the linguistic layer, the entities, the TEITOK file and the English metadata.
- **The Hugging Face Hub** supplies the models of page-classification, ocr-postprocess and
  keyword-extract when a service first starts. A deployment without internet access supplies them in
  advance.
- **AMČR decides the rights** in the outputs it publishes. Each run lists the components it used, each with
  its own licence or terms; no licence of an output is computed
  ([Licences and paradata](ecosystem/licences.md)).

## Open decisions and deferred work

- **Per-document permission** to send text to an external service: agreed with AMČR, not yet in the tools
  ([Licences and paradata](ecosystem/licences.md#what-may-leave-the-archive)).
- **LINDAT for the pilot**: CU's written permission for AMČR's use, and the terms of the output of the services
  the translator (its default backend) and nlp-enrich (UDPipe, NameTag) call, are still open
  ([#78](https://github.com/ufal/atrium-project/issues/78)).
- **`doc-schema-v2`**, the record schema 2.0 as a published tag, is tagged only once the pilot has proven it
  end to end; until then the published record schema is `doc-schema-v1`.
- **Parked during the AMČR pilot**, not part of the pipeline or the services: decision models
  ([#83](https://github.com/ufal/atrium-project/issues/83)), Galaxy work beyond the wrappers handed to DARIAH,
  digital-convert's `/describe`, the record's `forms` block, and full-text and ALTO translation.
- **The document-understanding benchmark**, which compares off-the-shelf models with these tools, is deferred
  until after the pilot ([#22](https://github.com/ufal/atrium-project/issues/22)).

## Sources

| Source                                                                                                                      | What was taken from it                                      |
|-----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| the six tools' `README.md`, "Limits and maturity", at the releases in the table                                             | what is measured, what is experimental, what each needs     |
| the six tools' `service/README.md`, "Models and caches"                                                                     | what each service downloads and calls                       |
| [Production pilot](pilot.md); hub issue [#77](https://github.com/ufal/atrium-project/issues/77)                             | the starting releases, the dates, the step-by-step assembly |
| [Operations](operations.md); each `service/README.md`, "OpenAPI"                                                            | the release gate; the API contract check                    |
| [Licences and paradata](ecosystem/licences.md)                                                                              | rights, and the planned per-document permission             |
| hub issues [#22](https://github.com/ufal/atrium-project/issues/22), [#78](https://github.com/ufal/atrium-project/issues/78) | the deferred benchmark; LINDAT's output terms               |
