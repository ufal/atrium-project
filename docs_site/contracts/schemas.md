---
title: Schemas
nav_order: 9
status: partial
round: 4
issue: 57
---

# Schemas

The two JSON Schemas the ecosystem ships, read field by field for the parts page-classification
and the translator write — and what each schema says that the code does not do.

!!! info "Annotated so far: the fields the two documented tools write"
    The schemas cover every block. The annotations below cover the fields owned by
    page-classification and the translator; the rest are added with their tools' sections.

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

The one field in the record that carries `x-atrium-scheme` and is written by page-classification.
Its examples were corrected from `"Text"` / `"Plate"`, neither of which is a valid label; the
hub's example fixture still carries the old values.

### `pages[]` — shared, keyed by `page`

| Field                                                                                           | Type                 | Written by              |                                                                                  |
|-------------------------------------------------------------------------------------------------|----------------------|-------------------------|----------------------------------------------------------------------------------|
| `page`                                                                                          | string, **required** | whoever creates the row | a label, so `iv` or `A-1` survive; never derive order from it — use `page_index` |
| `category`                                                                                      | string               | page-classification     | **no `x-atrium-scheme`** — the same values as `page_categories`, unannotated     |
| `category_confidence`                                                                           | number, 0–1          | page-classification     | the top-1 score, rounded to 3 decimals by the CLI and unrounded by the service   |
| `page_index`, `quality_score`, `quality_band`, `needs_ocr`, `needs_ocr_reason`, `ocr`, `canvas` |                      | the originator          | not written by either documented tool                                            |

Items allow additional properties. page-classification writes `category` and
`category_confidence` through a **keyed merge** on `page`, so a row another stage created is
extended, never replaced.

### `translations` — written by the translator

| Field         | Type   | Declared                                    | What the translator writes                                                                              |
|---------------|--------|---------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `source_lang` | string | ✓                                           | the **requested** source language — which can be the literal string `"auto"`, not the language detected |
| `target_lang` | string | ✓                                           | e.g. `"en"`                                                                                             |
| `backend`     | string | ✓ — examples `lindat`, `ctranslate2`, `llm` | `lindat` or `openai_compatible` — the registry's names                                                  |
| `output_mode` | —      | **not declared**                            | `replace` or `append`; allowed because the block has `additionalProperties: true`                       |

No field is required.

### `entities[].translation_en`

Declared as a string and assigned to the translator. **No code path writes it.** A comment in the
translator's `utils.py` says so plainly — "UNIMPLEMENTED, not merely deferred".

### `derived_from`

An object of strings, with no owner check: any program can write any key. The two tools write
`classification` (page-classification) and `translated_xml` (the translator) — see
[what they point at](../ecosystem/document-contract.md#what-the-references-actually-point-at).

### What the schema says that the code does not

| The schema, or the hub document, says                                                                                     | The code                                                                                                                                                      |
|---------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `page_categories`: "page-classification derives its label list from the filesystem at runtime (utils.py collect_images)"  | only `--train` and `--eval` do — and they write no record. Inference, the path that writes `page_categories`, uses the fixed list `model_registry.CATEGORIES` |
| `page_categories`: an unknown label raises "the advisory NOTE the registry raises"                                        | page-classification never calls the registry's `validate_labels()` on the labels it emits                                                                     |
| `docs/document_schema.md`: `x-atrium-scheme` is "a new annotation on each vocabulary-bearing field", listing seven fields | the schema carries it on **two**: `page_categories` and `lines[].categ`                                                                                       |
| `translations`: "Language pair and the persistent translated artifact it produced"                                        | the artifact is not in this block; it is `derived_from.translated_xml`                                                                                        |
| `translations.backend` examples: `lindat`, `ctranslate2`, `llm`                                                           | the registry's names are `lindat`, `openai_compatible` and `ct2`; `ctranslate2` and `llm` never appear                                                        |
| `$id`: `https://github.com/ufal/atrium-project/docs/templates/shared/atrium_document.schema.json`                         | that URL does not resolve — a GitHub file URL needs `/blob/<ref>/`                                                                                            |

None of these stops a record validating; each is a description that will mislead a reader.

## `atrium_vocab.schema.json`

A structural schema for the **JSON-LD export** of the vocabulary registry
(`atrium_vocab.py --jsonld`) — not for the record. It pins the `@context` prefixes (`skos`, `dct`,
`rdfs`, and the source vocabularies), requires a `registry_version`, and allows three node types in
`@graph`: `skos:Concept` (must have `inScheme`, `prefLabel`, `notation`), `skos:ConceptScheme`
(must have a title, description and comment) and `skos:Collection` (must have a `prefLabel` — its
description also asks for at least one member, which the schema does not enforce).

It is vendored, byte-checked by `para-drift`, and shipped in page-classification's release
bundle — but **no test and no CI step validates the registry's output against it.** See
[SKOS & the ATRIUM vocabulary](skos.md).

## Version policy

| Contract            | Version                                      | On a newer major          | On an older major                             |
|---------------------|----------------------------------------------|---------------------------|-----------------------------------------------|
| document record     | `1.0`, frozen                                | `load_document()` refuses | migrated — the migration is currently a no-op |
| paradata            | `2.0`                                        | refused                   | migrated (`1.0 → 2.0` adds `docker_image`)    |
| vocabulary registry | `1.0`                                        | —                         | —                                             |
| RO-Crate            | `1.1` (the RO-Crate specification's version) | —                         | —                                             |

An **additive** change — a new optional field, a new block — does not bump a version. A
**breaking** change bumps the major and ships a `_migrate_X_to_Y()` function. A record missing
`schema_version` is read as `1.0`.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                       | What was taken from it                                  |
|------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.schema.json`                                                           | every field definition quoted above                     |
| `atrium-project/docs/templates/shared/atrium_vocab.schema.json`                                                              | the registry schema                                     |
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_paradata.py`, `atrium_vocab.py`, `atrium_rocrate.py`      | version constants and the load/migrate behaviour        |
| `atrium-page-classification@vit` `8c98a3d` — `run.py:385-413`, `atrium_document_adapter.py`, `.github/workflows/release.yml` | what page-classification writes, and the release bundle |
| `atrium-translator@master` `88242fe` — `utils.py:363-403`, `processors/backend.py`                                           | what the translator writes, and the backend names       |
| `atrium-project/docs/document_schema.md:438-452`                                                                             | the hub's statements, compared                          |
| a search of every `.py`, `.yml` and `.sh` in the hub and both tools for `atrium_vocab.schema`                                | that nothing validates against it                       |
