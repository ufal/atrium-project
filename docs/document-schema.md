# 📄 ATRIUM Document Schema & Accretion Policy

This document defines the per-document aggregate record produced by `atrium_document.py` — the
**paradata pair**. Where [`paradata-schema.md`](paradata-schema.md) covers *how a run behaved*,
this covers *what we know about one document*: text, pages, entities and enrichment, gathered
across the pipeline into one FAIR, versioned JSON for search and catalogue export.

Template files: [`templates/shared/atrium_document.py`](templates/shared/atrium_document.py) ·
[`templates/shared/atrium_document.schema.json`](templates/shared/atrium_document.schema.json).
Design discussion: [ufal/atrium-llm-enrich#13](https://github.com/ufal/atrium-llm-enrich/issues/13).

## Why accretion, not an aggregator

The tools are separate containers reached over their own APIs, and **no tool sees another tool's
outputs**. So the record is not assembled by a central service; it travels *with* the document.
Each tool takes the previous version of the JSON — if it is given one — and returns it with
**only its own block** updated:

```
doc.json ──► [alto] ──► doc.json ──► [nlp] ──► doc.json ──► [llm] ──► doc.json
              pages/lines           entities            enrichment
```

This keeps every tool independently runnable, makes updates granular (re-run one tool → one
block changes), and needs no shared volume or orchestrator.

## Schema `1.0` Context
- **Contract:** fixed `source`, `derived_from`, `regenerable`, `provenance` and `assembled`
  blocks, plus the content blocks (`pages`, `content`, `lines`, `entities`, `translations`,
  `enrichment`, `page_categories`) each owned by exactly one tool.
- **First published version.** There is nothing to migrate yet; `load_document()` already
  carries the guard and `migrate_document()` the branch point, so the mechanism exists before
  it is needed.

## The accretion contract (six rules)

1. **Baseline in, record out.** Tools take an optional `--document-json` and write
   `--document-json-out` (default `<doc_id>.document.json`); services accept and return an
   optional `document_json` part.
2. **Own block only.** A tool writes its own block(s); every other block is deep-copied through
   **unchanged**. This invariant is what makes the pair safe to pass around.
3. **No baseline → own part only** (plus `doc_id`/`schema_version`, and `source` if it is the
   first writer). Standalone runs keep working; `assembled.had_baseline` records which case it was.
4. **Per-block provenance.** Every write stamps `assembled.blocks[<block>]` with the writing
   tool's `program`, its paradata `run_id`, and a `paradata_ref`. Granularity comes from here.
   For a field-split block the stamp names the **most recent** writer, so the full picture lives
   in `provenance.contributors[]`, where each run lists the blocks it wrote.
5. **Licenses accrete** through `para_licenses.merge_effective_licenses` — the same
   most-restrictive union as paradata — so the JSON stays self-describing for catalogue export.
6. **Unknown or newer blocks are preserved** verbatim; a newer MAJOR `schema_version` is refused
   with the same guard as `load_paradata()`.

## Reference discipline (non-negotiable)

Only two classes of reference may appear: the **original input** (`source`, keyed by `doc_id` +
`sha256` — originals are archive-managed, so no path is required) and **persistent step outputs**
(`derived_from`).

Transient artifacts are **never** referenced. Page images and thumbnails are produced during
processing or created late by the presentation layer and are not stored; the annotated Markdown is
derived and disposable. Both belong in `regenerable` as a recipe:

```json
"regenerable": {
  "markdown": { "from": "TEITOK/CTX000000001.teitok.xml",
                "converter": "xml_to_md@0.3.0", "detail": "full" }
}
```

Visual overlay still works without stored images: bounding boxes stay in ALTO/TEITOK coordinate
space and `pages[].teitok_surface` is a **logical** `<surface>` id, so the presentation layer
re-renders on demand.

## Block ownership

One owner per block. Blocks that several tools contribute to are split **by field**
(`BLOCK_FIELD_OWNERS`), so no field is ever co-mutated — use `merge_block()` for those and
`set_block()` for blocks you own outright.

| Tool | Owns |
|---|---|
| page-classification | `page_categories` · `pages[]` *category, category_confidence* |
| alto-postprocess | `pages[]` *quality_score, quality_band, needs_ocr, ocr, canvas* · `content` · `lines[]` *categ, quality_score, lang, text* |
| translator | `translations` · `entities[]` *translation_en* |
| nlp-enrich | `entities[]` · `lines[]` *lemma, upos, feats, teitok_ref, bbox* · `pages[]` *teitok_surface* · `derived_from.teitok` |
| llm-enrich | `enrichment` · `entities[]` *pid* · `regenerable.markdown` |

## Usage

Alongside the tool's existing `ParadataLogger`, so both records share one `run_id`:

```python
from atrium_document import DocumentRecord

with DocumentRecord.open(doc_id, "llm-enrich",
                         baseline=args.document_json,      # may be None — rule 3
                         run_id=logger._run_id,
                         paradata_ref=paradata_path) as doc:
    doc.set_block("enrichment", {"items": items})
    doc.add_derived_from("enriched", f"{doc_id}_enriched.json")
    doc.add_regenerable("markdown", {"from": teitok_path,
                                     "converter": "xml_to_md@0.3.0", "detail": "full"})
    doc.add_license_detail(paradata["license_detail"])
```

Field-level contribution into a shared block:

```python
doc.merge_block("lines", rows)   # writes only this program's declared fields
```

Shell stages use the CLI shim, as they do for paradata:

```bash
python atrium_document.py set-block --doc-id "$DOC" --program alto-postprocess \
    --block pages --payload pages.json --baseline "$DOC.document.json" --out "$DOC.document.json"
```

## Versioning Rules
1. **Additive Updates:** adding an optional field or a new block requires **no bump** — rule 6
   means existing tools pass unknown keys through untouched.
2. **Breaking Changes:** renaming/removing a field, or changing block ownership, bumps
   `SCHEMA_VERSION` to the next major (e.g. `2.0`).
3. **Migration Mechanics:** a bump mandates a sequential `_migrate_X_to_Y()` and a branch in
   `migrate_document()`, exactly as in `atrium_paradata.py`.

## Consumers to Update on Bumps
- `merge_document_records()` and the `_cli()` shim in `atrium_document.py`
- `atrium_document.schema.json` (kept in step with the module — one is the contract, one the validator)
- Every tool's block writer, and any search/presentation layer indexing the record
- This document and the ownership table above

## Distribution

`atrium_document.py` and `atrium_document.schema.json` are **hub-canonical**: they live here in
`docs/templates/shared/` and are copied byte-identical into the tool repos, enforced by
`para-drift.reusable.yml` — the same guarantee already covering `atrium_paradata.py` and
`para_licenses.py`.
