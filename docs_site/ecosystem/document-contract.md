---
title: The document contract
nav_order: 6
status: partial
round: 6
issue: 57
---

# The document contract

The `atrium_document` record is the one thing that travels through the whole pipeline. This
page says what it holds, who may write which part of it, how it is built up stage by stage,
and how page-classification and the translator write it.

!!! info "Normative text lives in the hub"
    [`docs/document_schema.md`](https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md)
    is the specification. This page explains it, with page-classification and the translator
    as the worked cases.

## The object

One JSON file per document, named `<doc_id>.document.json`, schema version **`1.0`** (frozen as
[`doc-schema-v1`](https://github.com/ufal/atrium-project/releases/tag/doc-schema-v1)).
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
`contributors[]` is the only complete account.

### The life of a record

1. **Load.** A stage opens the record it was given with `--document-json` — the *baseline* —
   or starts a new one. A baseline written by a newer major schema version is refused; an
   older one is migrated.
2. **Write.** The stage writes only the blocks it owns: `set_block()` replaces a whole block,
   `merge_block()` updates chosen fields inside a keyed list such as `pages[]`. Everything
   else in the baseline is carried through untouched.
3. **Stamp.** Each written block gets its `assembled.blocks` stamp, the run is added to
   `provenance.contributors[]`, and the run's licence block is added to the record's.
4. **Validate.** The finished record is checked against `atrium_document.schema.json`; a
   stage never emits a record that fails its own schema.
5. **Write out.** The file is written atomically — to a temporary name, then renamed — so a
   reader never sees half a record.

The next stage repeats the cycle with this file as its baseline.

## The six rules, per tool

The rules are the hub's; the right-hand columns show how each tool applies them.

| Rule                                | page-classification                                                                                                                                                                                             | translator                                                                                                                                                                  |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1 · Baseline in, record out**     | **Opt-in.** No record is written unless `--document-json-out` or `--document-json-out-dir` is set (or their `[DOCUMENT]` config keys). Writes the file itself, atomically, rather than through `finalize()`     | **Always writes one**, by default as `<doc_id>.document.json` next to its output, baseline or not                                                                           |
| **2 · Own block only**              | `set_block("page_categories", …)` **merged with the baseline's categories** — page keys from an earlier run survive — plus a keyed `merge_block("pages", …)` restricted to `category` and `category_confidence` | `set_block("translations", …)` and `add_derived_from("translated_xml", …)`                                                                                                  |
| **3 · No baseline → own part only** | derives `doc_id` from the filename: a trailing `-N` or `_N` is the page, the rest is the document (`scan_0007.png` → document `scan`, page `"7"`); no suffix means page `1`, with a warning                     | **inherits `doc_id` from the baseline** — its input is a page, `<doc>-1.alto.xml`, so deriving it would re-key the document — and derives it only when there is no baseline |
| **4 · Per-block provenance**        | stamps `page_categories`, `pages`, and `derived_from` when it records a result table                                                                                                                            | stamps `translations` and `derived_from`                                                                                                                                    |
| **5 · Licences accrete**            | contributes its paradata licence block; see below                                                                                                                                                               | contributes its paradata licence block; see below                                                                                                                           |
| **6 · Unknown blocks preserved**    | ✓ through the shared module                                                                                                                                                                                     | ✓ through the shared module                                                                                                                                                 |

### How the record's licence is computed

`provenance.license` is not declared by anyone. Each run contributes the licence block its
paradata has resolved, at the moment the record is written, from the components logged so
far, and the record's licence is recomputed
from the previous `license_detail` plus every block contributed since, by the shared
`para_licenses` rule: **the most restrictive licence wins**, and `license_detail` keeps the
full derivation — which components, with which licence, decided it.

A page-classification inference run contributes **MIT** (`vit_models` is its only
always-on component; the training dataset counts only for `--train`, which writes no
record). A translator run with the default backend and vocabulary logs the CUBBITT, UDPipe,
AMCR and TEATER components, which resolve in its paradata to **CC BY-NC-SA 4.0**.

When no licence block with any component has ever been contributed, the module falls back
conservatively to **CC BY-NC 4.0** and says so in `provenance.license_note`.

### What the references point at

Only `source` and `derived_from` may reference files, and only persistent ones. What the
two tools put there:

| Field          | page-classification                                                                                                                      | translator                                                                                             |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `derived_from` | `classification` — the run's result table, one CSV for the whole run (or one per day when `--chunk` is on); absent for a single-file run | `translated_xml` — the translated file's name, such as `CTX000000003-1_en.alto.xml`                    |
| `paradata_ref` | the run's paradata file; empty for records written by the service, which keeps no paradata file                                          | the run's paradata file under `<output>/paradata/`; in the service, the per-request paradata, not kept |

## Over HTTP

Both services can accrete onto a record uploaded with the request — as a multipart part named
`document_json` — and they return it differently:

|                                                  | page-classification                                                  | translator                                                                    |
|--------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Returns the record                               | inside its JSON response, as `document_json`                         | as the second part of a `multipart/mixed` response, after the translated XML  |
| Without a baseline                               | only if `document_json_out=true` is sent — it can originate a record | only with a baseline — over HTTP it extends records rather than starting them |
| Its own output fails the schema (baseline valid) | refused with a **500**                                               | refused with a **500**                                                        |

## A worked example

What the record looks like after page-classification and then the translator have written to it
— generated by running the shared module with the calls each tool makes, and validated
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
  "provenance": {"license": "…", "license_detail": "…",
                 "contributors": [ "…page-classification…",
                                   {"program": "translator", "blocks": "translations,derived_from", "…": "…"} ]}
}
```

`page_categories` and `pages` pass through untouched (rule 2); the translator adds its
blocks, its stamps and itself to `contributors[]`, and its licence block joins
page-classification's in the computation of `provenance.license` (rule 5). The values in
`page_categories` are the [eleven labels](../tools/page-classification/index.md#the-11-categories).

## How paradata accumulates

Every run also writes its own **paradata** file — the per-run log the `paradata_ref` fields point
at: tool version, run id, the resolved licence with its full derivation, timings, configuration,
and statistics. It is written by the shared `atrium_paradata.py`, schema version **`2.0`**.

The file is a flat JSON object — `tool_version`, `run_id`, `start_time`, `license_detail`,
configuration and statistics at the top level; `docs/paradata_schema.md` describes its fields.

The versioning rule is the same for both: an **additive** change does not bump the version; a
**breaking** one bumps the major and ships a `_migrate_X_to_Y()` function. A record or paradata
file with a *newer* major version than the reader knows is **refused**; an older one is migrated.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                                                                 | What was taken from it                                         |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_document.py`, `atrium_document.schema.json`, `atrium_paradata.py`, `para_licenses.py`                                     | the object, the stamp, the life cycle, the licence computation |
| `atrium-project/docs/document_schema.md`, `docs/paradata_schema.md`                                                                                                    | the rules as specified                                         |
| `atrium-page-classification@vit` `adee922` — `atrium_document_adapter.py`, `utils.py`, `run.py`, `service/document_json.py`, `service/api.py`, `setup/para_config.txt` | what page-classification writes                                |
| `atrium-translator@master` `71feaef` — `main.py`, `utils.py`, `service/api.py`, `para_config.txt`                                                                      | what the translator writes                                     |
| an in-memory run of the shared modules with each tool's calls, validated with `jsonschema`, 2026-09-22                                                                 | the worked example                                             |
