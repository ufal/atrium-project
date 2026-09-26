---
title: Schemas
nav_order: 9
status: partial
round: 6
issue: 57
---

# Schemas

The two JSON Schemas the ecosystem ships, read field by field for the parts page-classification
and the translator write.

!!! info "Scope"
    The schemas cover every block. The annotations below cover the fields owned by
    page-classification and the translator; the blocks of alto-postprocess, nlp-enrich and
    llm-enrich are described in the schema itself.

Both files are canonical in the hub (`docs/templates/shared/`) and vendored byte-identically into
every tool, where `para-drift` checks them.

## `atrium_document.schema.json`

The schema of the [document record](../ecosystem/document-contract.md) — JSON Schema, version
`1.0`. It validates with `additionalProperties: true` at the top level and on most blocks, by
design: rule 6 of the contract says a stage must carry blocks it does not recognise forward
untouched.

### `page_categories` — written by page-classification

|          |                                                                              |
|----------|------------------------------------------------------------------------------|
| Type     | object; each value a string                                                  |
| Keys     | page labels, as strings — `"1"`, `"2"`, …                                    |
| Values   | a label from the `page-category` scheme — `x-atrium-scheme: "page-category"` |
| `enum`   | **none, on purpose**                                                         |
| Examples | `{"1": "TEXT", "2": "DRAW"}`                                                 |

**`x-atrium-scheme`** is an ATRIUM annotation, not a JSON Schema keyword: validators ignore
it, and it tells a reader which controlled vocabulary the values come from. A consumer turns
a value into its SKOS URI with `atrium_vocab.concept_uri("page-category", value)` — for
`TEXT_HW`, `https://w3id.org/atrium/page-category/TEXT_HW`. See
[SKOS & the ATRIUM vocabulary](skos.md).

### `pages[]` — shared, keyed by `page`

| Field                                                                                           | Type                 | Written by              |                                                                                  |
|-------------------------------------------------------------------------------------------------|----------------------|-------------------------|----------------------------------------------------------------------------------|
| `page`                                                                                          | string, **required** | whoever creates the row | a label, so `iv` or `A-1` survive; never derive order from it — use `page_index` |
| `category`                                                                                      | string               | page-classification     | the same label as `page_categories` for that page                                |
| `category_confidence`                                                                           | number, 0–1          | page-classification     | the top-1 score, `SCORE-1` of the result table                                   |
| `page_index`, `quality_score`, `quality_band`, `needs_ocr`, `needs_ocr_reason`, `ocr`, `canvas` |                      | the originator          | not written by either documented tool                                            |

Items allow additional properties. page-classification writes `category` and
`category_confidence` through a **keyed merge** on `page`, so a row another stage created is
extended, never replaced.

### `translations` — written by the translator

| Field                  | Type   | What the translator writes                                                                                        |
|------------------------|--------|-------------------------------------------------------------------------------------------------------------------|
| `source_lang`          | string | the source language as requested — a code such as `"cs"`, or `"auto"` when it was detected per block or field     |
| `target_lang`          | string | e.g. `"en"`                                                                                                       |
| `backend`              | string | the backend's registry name: `lindat`, `openai_compatible` or `ct2`                                               |
| `output_mode`          | string | `replace` or `append` — carried as an additional property, which the block allows                                 |
| `detected_source_lang` | string | with `source_lang: "auto"` only: the language the document resolved to, e.g. `"cs"` — also an additional property |

No field is required. The translated text itself is not in this block: the file is referenced
from `derived_from.translated_xml`.

### `entities[].translation_en`

Declared as a string and assigned to the translator. Entities are created by nlp-enrich, which
runs after the translator, so the field is reserved rather than filled in the current
pipeline order.

### `derived_from`

An object of strings, with no owner check: any program can write any key. The two tools write
`classification` (page-classification) and `translated_xml` (the translator) — see
[what they point at](../ecosystem/document-contract.md#what-the-references-point-at).

### Validating a record

Every tool validates the record it writes before writing it. To check one by hand, against
the vendored schema:

```python
import json, jsonschema

schema = json.load(open("atrium_document.schema.json"))
record = json.load(open("CTX000000003.document.json"))
jsonschema.validate(record, schema)  # raises ValidationError on failure
```

or through the shared module, which also applies the version rules below:
`atrium_document.load_document(path)` refuses a newer major version and migrates an older one.

## `atrium_vocab.schema.json`

A structural schema for the **JSON-LD export** of the vocabulary registry
(`atrium_vocab.py --jsonld`) — not for the record. It pins the `@context` prefixes (`skos`, `dct`,
`rdfs`, and the source vocabularies), requires a `registry_version`, and allows three node types in
`@graph`: `skos:Concept` (must have `inScheme`, `prefLabel`, `notation`), `skos:ConceptScheme`
(must have a title, description and comment) and `skos:Collection` (must have a `prefLabel`).

It is vendored into every tool and byte-checked by `para-drift`. See
[SKOS & the ATRIUM vocabulary](skos.md).

## Version policy

| Contract            | Version                                                                                               | On a newer major          | On an older major                          |
|---------------------|-------------------------------------------------------------------------------------------------------|---------------------------|--------------------------------------------|
| document record     | `1.0`, frozen as [`doc-schema-v1`](https://github.com/ufal/atrium-project/releases/tag/doc-schema-v1) | `load_document()` refuses | migrated                                   |
| paradata            | `2.0`                                                                                                 | refused                   | migrated (`1.0 → 2.0` adds `docker_image`) |
| vocabulary registry | `1.0`                                                                                                 | —                         | —                                          |
| RO-Crate            | `1.1` (the RO-Crate specification's version)                                                          | —                         | —                                          |

An **additive** change — a new optional field, a new block — does not bump a version. A
**breaking** change bumps the major and ships a `_migrate_X_to_Y()` function. A record missing
`schema_version` is read as `1.0`.

The document record's freeze is a tag, one per major: `doc-schema-v1` is commit `544298b`, and it
never moves. An additive change after it keeps that tag as the reference, but has to be registered.
Every tool carries the frozen copy, `atrium_document.schema.doc-schema-v1.json`, and a vendored
`tests/test_schema_freeze.py` that checks its own schema against it: nothing declared at the freeze
removed, and every constraint added since listed in one register (so far one,
`lines[].style.region`). The hub also checks that every record shape the tools write validates
against both the frozen schema and the current one. The rule and the procedure for a new major are
in the hub's
[`document_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md#freeze--conformance).

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                  | What was taken from it                                       |
|-------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.schema.json`                                                      | every field definition quoted above                          |
| `atrium-project/docs/templates/shared/atrium_vocab.schema.json`                                                         | the registry schema                                          |
| `atrium-project/docs/templates/shared/test_schema_freeze.py`, tag `doc-schema-v1` (`544298b`)                           | the freeze tag, the post-freeze register                     |
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_paradata.py`, `atrium_vocab.py`, `atrium_rocrate.py` | version constants, the load/migrate behaviour, `concept_uri` |
| `atrium-page-classification@vit` `adee922` — `run.py`, `atrium_document_adapter.py`                                     | what page-classification writes                              |
| `atrium-translator` `v1.2.1-beta` — `utils.py`, `processors/backend.py`                                                 | what the translator writes, and the backend names            |
