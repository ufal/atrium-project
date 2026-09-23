---
title: RO-Crate export
nav_order: 7
status: partial
round: 4
issue: 57
---

# RO-Crate export

What ATRIUM can publish as an RO-Crate, what happens to page-classification's and the
translator's contributions on the way, and what a crate cannot yet say.

!!! info "Shown for page-classification and translator"
    The exporter handles every block. The mapping below is for the blocks these two tools write,
    and it was produced by running the exporter, not by reading about it.
    [`docs/rocrate_export.md`](https://github.com/ufal/atrium-project/blob/main/docs/rocrate_export.md)
    is the full guide, including an RO-Crate tutorial from zero.

## RO-Crate in one paragraph

An RO-Crate is a folder with one extra file, `ro-crate-metadata.json`: a JSON-LD description of
what is in the folder, who made it, with which software, and under which licence — written in
schema.org terms so that repositories and catalogues can read it without knowing anything about
ATRIUM. ATRIUM's exporter, `atrium_rocrate.py` (RO-Crate **1.1**), turns a
[document record](../ecosystem/document-contract.md) into such a description, and a set of records
from one run into a crate of crates.

## What happens to these two tools' blocks

Exporting the [worked-example record](../ecosystem/document-contract.md#a-worked-example) —
page-classification's `page_categories` and `pages`, then the translator's `translations` and
`derived_from` — gives 18 entities:

| In the record                                     | In the crate                                                                                                                                   | What survives                                                                                                                                                                                                                                                                    |
|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `page_categories: {"1": "TEXT_P"}`                | a `DefinedTerm` `https://w3id.org/atrium/page-category/TEXT_P`, in the `DefinedTermSet` `…/scheme/page-category`, listed in the root's `about` | **the label only.** Which page it was assigned to is gone — a crate says the document is *about* `TEXT_P`, not that page 1 is `TEXT_P`                                                                                                                                           |
| `pages[].category`, `pages[].category_confidence` | the same `DefinedTerm`, de-duplicated                                                                                                          | the confidence (`0.981`) is **dropped**                                                                                                                                                                                                                                          |
| `translations`                                    | a `#block-translations` `CreativeWork`, created by `#tool-translator`                                                                          | **only that the block exists.** `source_lang`, `target_lang`, `backend` and `output_mode` are not mapped — a crate cannot say which language pair or which translation service was used                                                                                          |
| `derived_from.translated_xml`                     | a `File` `CTX000000003-1_en.alto.xml`, `encodingFormat: application/alto+xml`, in the root's `hasPart`                                         | the file — named by the **bare filename** the translator records, with no path and no checksum                                                                                                                                                                                   |
| `derived_from.classification` (when present)      | a `File` in `hasPart`                                                                                                                          | the file — which is page-classification's **run-wide** result CSV, not a per-document one                                                                                                                                                                                        |
| each `assembled.blocks` stamp                     | a `#block-<name>` `CreativeWork` with `recordBlock`, `dateModified` and `creator`                                                              | who wrote each block last                                                                                                                                                                                                                                                        |
| each `provenance.contributors[]` entry            | a `#run-<program>-<run_id>` `CreateAction`: `instrument` the tool, `result` the blocks it wrote                                                | who ran, when, and what they produced                                                                                                                                                                                                                                            |
| each program                                      | a `#tool-<program>` `SoftwareApplication` with the repository `url`                                                                            | version, image and runtime only if a paradata map is passed in from Python — the command line never passes one                                                                                                                                                                   |
| `provenance.license`                              | the root's `license`                                                                                                                           | the record's licence — **including its defect**: the example resolves to MIT, determined by `vit_models`, although it describes a CC BY-NC-SA 4.0 translation. See [rule 5 in practice](../ecosystem/document-contract.md#rule-5-in-practice-what-licence-a-record-ends-up-with) |

The root also names the four `CITATION.cff` authors as ORCID `Person` entities — hard-coded in the
exporter, because the hub has no `CITATION.cff` of its own to read them from.

## What a crate gets right

* **It is deterministic.** Entities are merged by `@id`, the descriptor and the root come first,
  everything else is sorted by `@id`, and the JSON is written with sorted keys. The same record
  always produces byte-identical output, so a crate can be diffed and committed.
* **`datePublished` is derived, not stamped.** It is the newest of the record's block stamps and
  contributor times, cut to a date — never the export clock. (`rocrate_export.md` says block stamps
  only; the code reads both.)
* **Granularity survives.** Each block keeps its own entity with its own creator, so "who produced
  the page categories" and "who produced the translation" have separate answers.
* **Controlled values become resolvable terms**, under the [SKOS URIs](skos.md#how-a-uri-is-minted).

## Nobody runs it yet

The exporter is vendored into both tools — and **neither calls it**. There is no reference to
`atrium_rocrate` in either tool's runtime code; page-classification's release bundle does not even
ship it. It is a reader, run by hand over records that already exist:

```bash
python atrium_rocrate.py --document CTX000000003.document.json --out-dir crate/
python atrium_rocrate.py --run 1.document.json 2.document.json --paradata run.json --out-dir crate/
python atrium_rocrate.py --selftest
```

`--document` writes one document's crate; `--run` writes a run crate whose `hasPart` holds one
sub-crate per document, and additionally conforms to the Process Run Crate profile. The write is
atomic.

## What a crate cannot yet say

From `rocrate_export.md` §7, plus what running it on these two tools' records shows:

| Gap                                                                | Consequence                                                              |
|--------------------------------------------------------------------|--------------------------------------------------------------------------|
| **No commit SHA** — paradata records a branch or tag               | software provenance is "this ref", not "this commit"                     |
| **No output checksums** — `sha256` exists only on `source`         | a `hasPart` file cannot be verified from the crate                       |
| **No DOI or other PID** anywhere                                   | the crate's `@id` is a local path                                        |
| **The hub has no `CITATION.cff`**                                  | author metadata is hard-coded in the exporter                            |
| `entities[].translation_en` is owned but **never written**         | that part of the schema can never appear in a crate                      |
| `translations` is **not mapped**                                   | a crate cannot say which language pair or service produced a translation |
| page categories lose **their pages and confidences**               | a crate cannot say which page is which category                          |
| `derived_from` values are **bare filenames** or **run-wide files** | the crate's `hasPart` entries do not identify one document's files       |

`skos_strategy.md` also records a change to prefer the source vocabulary's URI as a term's `@id`
(its V-5 / F6) as done. The exporter at the hub's `main` does not contain it; it does not affect
`page-category`, whose terms are ATRIUM-minted either way.

## Where RO-Crate sits among the standards

RO-Crate is one of the standards the project's data management plan names, alongside CIDOC-CRM,
SKOS, PeriodO, Getty AAT, TEI, DataCite and IIIF. The ecosystem deliberately does **not** apply
heavyweight ontologies — W3C PROV-O, CIDOC-CRM — during raw extraction over a corpus of more than a
million pages: the record stays a plain JSON document, and the crate is the *view* that a
catalogue reads. `rocrate_export.md` §3 is the reasoning in full.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                  | What was taken from it                                             |
|---------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_rocrate.py` — run on the worked-example record, 2026-09-22 | the mapping table, entity by entity                                |
| `atrium-project/docs/rocrate_export.md` §§3, 4.1, 6, 7                                                  | the design, the `datePublished` rule as documented, the known gaps |
| a search of both tools' runtime Python at `vit` @ `8c98a3d` and `master` @ `88242fe`                    | that neither calls the exporter                                    |
| `atrium-page-classification/.github/workflows/release.yml`                                              | the release bundle's contents                                      |
| `atrium-project/docs/skos_strategy.md` V-5 / F6                                                         | compared against the exporter                                      |
