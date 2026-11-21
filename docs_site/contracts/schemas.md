---
title: Schemas
nav_order: 9
status: published
round: 8
issue: 79
---

# Schemas

This page lists the schemas the ATRIUM tools write and check against, their versions and how they
change, and how to validate a file by hand. It is for integrators. What each field of the record means,
and who writes it, is on [The document contract](../ecosystem/document-contract.md).

## The schema files

| Schema                                      | What it validates                                                      | Version                          | Home                                                                                                                                                       |
|---------------------------------------------|------------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `atrium_document.schema.json`               | the ATRIUM document record (`atrium/document-json`)                    | `2.0`                            | the hub's `docs/templates/shared/`, copied into every tool                                                                                                 |
| `atrium_document.schema.doc-schema-v1.json` | records of the published 1.x schema                                    | `1.0`, frozen as `doc-schema-v1` | the same, never edited                                                                                                                                     |
| `atrium_vocab.schema.json`                  | the JSON-LD export of the vocabulary registry                          | `1.0`                            | the same                                                                                                                                                   |
| the docproc schema                          | the layout that digital-convert and the ATR write (`atr/docproc-json`) | as ARÚP versions it              | ARÚP's contract, kept in the aiscr-docs-pipeline repository under an ARUP-CAS identifier; digital-convert validates against its copy in `schemas/docproc/` |
| `teitok.xsd`                                | nlp-enrich's TEITOK files (`atr/teitok-xml`)                           | `teitok-2`                       | nlp-enrich's `schemas/teitok/`                                                                                                                             |

The paradata have no JSON Schema of their own: their format, version 3.0, is defined by the shared
`atrium_paradata.py` and described in the hub's
[`paradata_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/paradata_schema.md). The
shared files are canonical in the hub and copied byte for byte into every tool, where the `para-drift`
check keeps them identical.

## `atrium_document.schema.json`

The schema of the [document record](../ecosystem/document-contract.md), JSON Schema, version `2.0`. What it
enforces:

- **Identity.** `schema_version`, `record_type` and `doc_id` are required, and so is either `source` or at
  least one content block: a step that ran and wrote nothing is refused.
- **Content only.** The blocks and fields that schema 2.0 removed — `provenance`, `assembled`,
  `derived_from`, `regenerable`, `forms`, `tables`, `content.reading_order`, the line styles and the page
  verdicts — are refused by name.
- **Unknown blocks pass.** The top level and most blocks allow additional properties, by design: a step
  must carry blocks it does not recognise forward untouched.
- **One line key.** A line is named by `page` and `line`; when the record has `lines[]`, the shared module
  checks that every entity and every `enrichment` item names a line that exists.

### `page_categories` — written by page-classification

|          |                                                                              |
|----------|------------------------------------------------------------------------------|
| Type     | object; each value a string                                                  |
| Keys     | page labels, as strings — `"1"`, `"2"`, …                                    |
| Values   | a label from the `page-category` scheme — `x-atrium-scheme: "page-category"` |
| `enum`   | **none, on purpose**                                                         |
| Examples | `{"1": "TEXT", "2": "DRAW"}`                                                 |

**`x-atrium-scheme`** is an ATRIUM annotation, not a JSON Schema keyword: validators ignore it, and it
tells a reader which controlled vocabulary the values come from. The line categories carry it too
(`line-category`). A consumer turns a value into its SKOS URI with
`atrium_vocab.concept_uri("page-category", value)` — for `TEXT_HW`,
`https://w3id.org/atrium/page-category/TEXT_HW`. There is no `enum`, because page-classification derives
its label list from its training folders at run time; a naming slip gives an advisory note from the
registry rather than a failed pipeline. See [SKOS & the ATRIUM vocabulary](skos.md).

### Validating a record

Every tool validates the record it writes before writing it. To check one by hand, against the vendored
schema:

```python
import json, jsonschema

schema = json.load(open("atrium_document.schema.json"))
record = json.load(open("CTX000000003.document.json"))
jsonschema.validate(record, schema)  # raises ValidationError on failure
```

or through the shared module, which also applies the version rules below and checks the line references:
`atrium_document.load_document(path)` refuses a newer major version and migrates an older one.

## `atrium_vocab.schema.json`

A structural schema for the **JSON-LD export** of the vocabulary registry (`atrium_vocab.py --jsonld`) — not
for the record. It pins the `@context` prefixes (`skos`, `dct`, `rdfs`, and the source vocabularies),
requires a `registry_version`, and allows three node types in `@graph`: `skos:Concept` (must have
`inScheme`, `prefLabel`, `notation`), `skos:ConceptScheme` (must have a title, description and comment) and
`skos:Collection` (must have a `prefLabel`).

It is vendored into every tool and byte-checked by `para-drift`. See
[SKOS & the ATRIUM vocabulary](skos.md).

## Version policy

| Contract            | Version the tools write                                                                                                | On a newer major          | On an older major                                                  |
|---------------------|------------------------------------------------------------------------------------------------------------------------|---------------------------|--------------------------------------------------------------------|
| document record     | `2.0`; the published reference is [`doc-schema-v1`](https://github.com/ufal/atrium-project/releases/tag/doc-schema-v1) | `load_document()` refuses | migrated on read (`1.x → 2.0` drops the removed blocks and fields) |
| paradata            | `3.0`                                                                                                                  | refused                   | migrated on read (`2.x → 3.0` drops the calculated licence)        |
| vocabulary registry | `1.0`                                                                                                                  | —                         | —                                                                  |
| RO-Crate            | `1.2`, with the Process Run Crate profile `0.5`                                                                        | —                         | —                                                                  |

An **additive** change — a new optional field, a new block — does not bump a version. A **breaking** change
bumps the major and ships a `_migrate_X_to_Y()` function. A record missing `schema_version` is read as
`1.0`. Files on disk are never rewritten: migration happens in memory, when a file is read.

**`doc-schema-v2`.** The tools write record schema 2.0. It is published as the tag `doc-schema-v2` once it
has passed the validator, the end-to-end checks and a run through the assembled chain; until then
`doc-schema-v1` is the published reference.

**The freeze.** A record schema's freeze is a tag, one per major: `doc-schema-v1` is commit `544298b`, and it
never moves. Every tool carries the frozen copy, `atrium_document.schema.doc-schema-v1.json`, and a vendored
`tests/test_schema_freeze.py` that pins it by its git blob id. The hub also checks that every record shape the
tools write validates against the current schema. The rule and the procedure for a new major are in the hub's
[`document_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md#freeze--conformance).

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                  | What was taken from it                                           |
|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.schema.json` (`test`)                                             | what the record schema enforces, `page_categories`               |
| `atrium-project/docs/templates/shared/atrium_vocab.schema.json`                                                         | the registry schema                                              |
| `atrium-project/docs/templates/shared/test_schema_freeze.py`, tag `doc-schema-v1` (`544298b`)                           | the freeze                                                       |
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_paradata.py`, `atrium_vocab.py`, `atrium_rocrate.py` | version constants, the load and migrate behaviour, `concept_uri` |
| `atrium-digital-convert/schemas/docproc/`, `atrium-nlp-enrich/schemas/teitok/` (`test`)                                 | the docproc and TEITOK schemas                                   |
| ARÚP's output contract of 12 November 2026, section 4                                                                   | the home of the docproc schema                                   |
