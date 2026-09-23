---
title: The document contract
nav_order: 6
status: partial
round: 4
issue: 57
---

# The document contract

The `atrium_document` record is the one thing that travels through the whole pipeline. This
page says what it holds, who may write which part of it, and — the part the normative
documents cannot tell you — how page-classification and the translator actually write it.

!!! info "Normative text lives in the hub; this is the two-tool view of it"
    [`docs/document_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md)
    is the specification. This page shows what two of the five writers do with it, verified
    against their code, and where the two disagree.

## The object

One JSON file per document, named `<doc_id>.document.json`, schema version **`1.0`** (frozen).
The module that writes it, `atrium_document.py`, is vendored byte-identically into every tool, so
every tool writes the record the same way; what differs is which calls each tool makes.

| Part                                                                                                        | What it holds                                                                                                   |
|-------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `schema_version`, `record_type`, `doc_id`                                                                   | identity — `record_type` is `atrium-document`, or `atrium-document-merged` for a merge of parallel branches     |
| `source`                                                                                                    | the original input: its identifier, checksum and how it was acquired (`source.origin`)                          |
| `provenance`                                                                                                | the resolved licence of the whole record, and `contributors[]` — every run that wrote to it                     |
| `assembled`                                                                                                 | one **stamp** per block: who wrote it last, in which run                                                        |
| `page_categories`, `pages`, `content`, `lines`, `tables`, `entities`, `translations`, `enrichment`, `forms` | the tool blocks — one authorised writer each, see [Repository map](repository-map.md#who-may-write-which-block) |
| `derived_from`                                                                                              | references to **persistent** outputs a stage produced                                                           |
| `regenerable`                                                                                               | **recipes** for disposable outputs, never their paths                                                           |

Five keys are required: `schema_version`, `record_type`, `doc_id`, `provenance`, `assembled`.
Six are reserved — no tool can `set_block()` them: those five and `source`. The schema adds one
consistency rule worth knowing: **any block named in `assembled.blocks` must exist at the top
level**, so a record cannot claim a contribution it does not contain.

### The stamp, and the contributor list

Every write stamps the block it touched:

```json
"assembled": { "blocks": { "<block>": {
  "program": "…", "run_id": "…", "paradata_ref": "…", "updated_at": "…" } } }
```

and every run that wrote anything appends itself once:

```json
"provenance": { "contributors": [ {
  "program": "…", "run_id": "…", "paradata_ref": "…",
  "blocks": "page_categories,pages", "at": "…" } ] }
```

`blocks` is a **comma-separated string**, not a list. The stamp names only the *most recent*
writer of a block, so for a block several programs write fields of — `pages[]`, `entities[]` —
`contributors[]` is the only complete account. The hub's statement of the rule lists `program`,
`run_id` and `paradata_ref`; the stamp also carries `updated_at`.

## The six rules, and what each tool actually does

The rules are the hub's. The right-hand columns are read from each tool's code.

| Rule                                | page-classification                                                                                                                                                                                             | translator                                                                                                                                                                  |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1 · Baseline in, record out**     | **Opt-in.** No record is written unless `--document-json-out` or `--document-json-out-dir` is set (or their `[DOCUMENT]` config keys). Writes the file itself, atomically, rather than through `finalize()`     | **Always writes one**, by default as `<doc_id>.document.json` next to its output, baseline or not                                                                           |
| **2 · Own block only**              | `set_block("page_categories", …)` **merged with the baseline's categories** — page keys from an earlier run survive — plus a keyed `merge_block("pages", …)` restricted to `category` and `category_confidence` | `set_block("translations", …)` and `add_derived_from("translated_xml", …)`. `entities[].translation_en` is authorised and **never written**                                 |
| **3 · No baseline → own part only** | derives `doc_id` from the filename: a trailing `-N` or `_N` is the page, the rest is the document (`scan_0007.png` → document `scan`, page `"7"`); no suffix means page `1`, with a warning                     | **inherits `doc_id` from the baseline** — its input is a page, `<doc>-1.alto.xml`, so deriving it would re-key the document — and derives it only when there is no baseline |
| **4 · Per-block provenance**        | stamps `page_categories`, `pages`, and `derived_from` when it records a result table                                                                                                                            | stamps `translations` and `derived_from`                                                                                                                                    |
| **5 · Licences accrete**            | contributes its paradata licence block; see below                                                                                                                                                               | contributes its paradata licence block **before** its backend's components are logged; see below                                                                            |
| **6 · Unknown blocks preserved**    | ✓ through the shared module                                                                                                                                                                                     | ✓ through the shared module                                                                                                                                                 |

### Rule 5 in practice: what licence a record ends up with

This is where the two tools' records say something other than their own paradata.

=== "page-classification"

    | Path         | Record licence                                                                                                                                                                                                                                                                            |
    |--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | CLI          | **MIT** — only `vit_models` is always-on; `lindat_dataset` counts only when training, which writes no record                                                                                                                                                                              |
    | HTTP service | **CC BY-NC 4.0**, with `license_note: "License helper unavailable or no components recorded; defaulted conservatively to CC BY-NC 4.0."` — the service writes records without a paradata logger, so it contributes no licence block and the module falls back to its conservative default |

    The same inference, run two ways, yields two different licences on the record.

=== "translator"

    `process_single_file()` attaches the run's licence block to the record **before** the
    backend's components are logged — `lindat_cubbitt` (CC BY-NC-SA 4.0) is logged only *after*
    the first file succeeds. So:

    | Run                                  | What the translator contributes to the record                                |
    |--------------------------------------|------------------------------------------------------------------------------|
    | first file, explicit `--source_lang` | **no components at all** — FastText is not loaded, CUBBITT not yet logged    |
    | first file, `--source_lang auto`     | FastText only — **CC BY-NC 4.0**                                             |
    | every later file of the same run     | CUBBITT as well — **CC BY-NC-SA 4.0**, as it should be                       |
    | HTTP service, every request          | components are logged after the call returns — **nothing**, on every request |

    The run's paradata, written at the end, says CC BY-NC-SA 4.0. The end-to-end test translates
    exactly one file with `--source_lang cs` — the first case.

Both results were confirmed by running the shared `atrium_document.py` and `atrium_paradata.py`
with each tool's `para_config.txt` and each tool's sequence of calls. The worked example below is
the output of that run.

### What the references actually point at

Rule-by-rule discipline says only `source` and `derived_from` may reference files, and only
persistent ones. What the two tools put there:

| Field          | page-classification                                                                                                                                                      | translator                                                                                                                                                                               |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `derived_from` | `classification` — the result table, which is **one CSV for the whole run** (or one per day when `--chunk` is on), not a per-document file; absent for a single-file run | `translated_xml` — a **bare filename** such as `CTX000000003-1_en.alto.xml`, not a path. In a batch run every file shares one baseline and one output path, so the last file's name wins |
| `paradata_ref` | CLI: `paradata/<run>_page-classification.json` — the file is actually written under `result/paradata/`. Service: empty                                                   | CLI: `<output>/paradata/<run>_translator.json`, possibly absolute. Service: a path inside a per-request temporary directory that is deleted with the response                            |

## Over HTTP

Both services can accrete onto a record uploaded with the request — as a multipart part named
`document_json` — and they return it differently:

|                                                                   | page-classification                                                                                      | translator                                                                            |
|-------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Returns the record                                                | inside its JSON response, as `document_json`                                                             | as the second part of a `multipart/mixed` response, after the translated XML          |
| Without a baseline                                                | only if `document_json_out=true` is sent — it can originate a record                                     | **never** — it cannot originate a record over HTTP                                    |
| A baseline that fails to load (corrupt, or a newer major version) | **422** `Unusable document_json baseline`                                                                | a generic **500** `Translation processing failed.`                                    |
| A baseline that loads but does not validate                       | accreted onto with a warning — the response carries `document_json_schema_error`, so a caller can see it | accreted onto with a warning in the service log only; nothing in the response says so |
| Its own output fails the schema (baseline valid)                  | refused — **500** `Document record rejected by its own schema`                                           | refused — the generic **500**                                                         |

## A worked example

What the record looks like after page-classification and then the translator have written to it
— **generated by running the shared module with the calls each tool makes**, and validated
against `atrium_document.schema.json`. alto-postprocess, which runs between them in the real
chain, is left out so that only these two tools' writes are visible; in the real chain its blocks
and licence components would be here too.

After **page-classification** (`-f CTX000000003-1.png --document-json-out 1_pc.json`, no
baseline):

```json
{
  "schema_version": "1.0",
  "record_type": "atrium-document",
  "doc_id": "CTX000000003",
  "provenance": {
    "license": "MIT",
    "license_url": "https://opensource.org/license/mit/",
    "license_detail": {
      "effective_license": "MIT",
      "determined_by": ["vit_models"],
      "components": [{"name": "vit_models", "license": "MIT", "rank": 1}],
      "…": "…"
    },
    "contributors": [{
      "program": "page-classification",
      "run_id": "260922-220516",
      "paradata_ref": "paradata/260922-220516_page-classification.json",
      "blocks": "page_categories,pages",
      "at": "2026-09-22T22:05:16.866272+00:00"
    }]
  },
  "assembled": {
    "blocks": {
      "page_categories": {"program": "page-classification", "run_id": "260922-220516", "…": "…"},
      "pages":           {"program": "page-classification", "run_id": "260922-220516", "…": "…"}
    },
    "had_baseline": false,
    "note": "Blocks reflect CONTRIBUTED steps only; a block is absent until its tool has run."
  },
  "page_categories": {"1": "TEXT_P"},
  "pages": [{"page": "1", "category": "TEXT_P", "category_confidence": 0.981}]
}
```

Then the **translator** takes that record as `--document-json` and writes:

```json
{
  "derived_from": {"translated_xml": "CTX000000003-1_en.alto.xml"},
  "translations": {"source_lang": "cs", "target_lang": "en", "backend": "lindat", "output_mode": "replace"},
  "assembled":  {"blocks": {"translations": {"program": "translator", "…": "…"},
                            "derived_from": {"program": "translator", "…": "…"}},
                 "had_baseline": true},
  "provenance": {"license": "MIT",
                 "contributors": [ "…page-classification…",
                                   {"program": "translator", "blocks": "translations,derived_from", "…": "…"} ]}
}
```

`page_categories` and `pages` pass through untouched (rule 2). And the record's licence is still
**MIT, determined by `vit_models` alone** — although the translation it now describes was made
with a CC BY-NC-SA 4.0 service. That is rule 5's defect, in the record itself.

!!! warning "Do not copy the hub fixture"
    `fixtures/atrium_document.example.json` is the hub's illustrative record. It uses
    `page_categories` values `"Text"` and `"Plate"` — neither is one of the
    [eleven labels](../tools/page-classification/index.md#the-11-categories) — a
    `derived_from.translated_xml` of `TRANSLATED/…`, which is not what the translator writes, and no
    `output_mode`. The example above is what the code produces.

## How paradata accumulates

Every run also writes its own **paradata** file — the per-run log the `paradata_ref` fields point
at: tool version, run id, the resolved licence with its full derivation, timings, configuration,
and statistics. It is written by the shared `atrium_paradata.py`, schema version **`2.0`**.

The versioning rule is the same for both: an **additive** change does not bump the version; a
**breaking** one bumps the major and ships a `_migrate_X_to_Y()` function. A record or paradata
file with a *newer* major version than the reader knows is **refused**; an older one is migrated.
(`docs/paradata_schema.md` describes the paradata JSON as nested `provenance`, `license`, `timing`,
`config` and `statistics` blocks; the file is in fact flat — `tool_version`, `start_time`,
`license_detail` and so on at the top level.)

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                                                                 | What was taken from it                                                        |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_document.schema.json`, `atrium_paradata.py`                                                         | the object, the stamp, the rules as implemented; byte-identical in both tools |
| `atrium-project/docs/document_schema.md:41-62`, `docs/paradata_schema.md`                                                                                              | the rules as specified                                                        |
| `atrium-page-classification@vit` `8c98a3d` — `atrium_document_adapter.py`, `utils.py`, `run.py`, `service/document_json.py`, `service/api.py`, `setup/para_config.txt` | what page-classification writes                                               |
| `atrium-translator@master` `88242fe` — `main.py:168-200, 410-532, 575-690`, `utils.py:385-403`, `service/api.py`, `para_config.txt`                                    | what the translator writes, and when it logs its licence components           |
| an in-memory run of the shared modules with each tool's calls and `para_config.txt`, validated with `jsonschema`, 2026-09-22                                           | the licence results and the worked example                                    |
| `atrium-project/fixtures/atrium_document.example.json`                                                                                                                 | compared, not used                                                            |
