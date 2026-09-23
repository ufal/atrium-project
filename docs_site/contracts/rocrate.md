---
title: RO-Crate export
nav_order: 7
status: partial
round: 6
issue: 57
---

# RO-Crate export

What ATRIUM can publish as an RO-Crate, and how the blocks page-classification and the
translator write are carried into it.

!!! info "Scope"
    The exporter handles every block. The mapping below is for the blocks these two tools
    write, taken from the exporter's own output.
    [`docs/rocrate_export.md`](https://github.com/ufal/atrium-project/blob/main/docs/rocrate_export.md)
    is the full guide, including an RO-Crate tutorial from zero.

## RO-Crate in one paragraph

An RO-Crate is a folder with one extra file, `ro-crate-metadata.json`: a JSON-LD description of
what is in the folder, who made it, with which software, and under which licence — written in
schema.org terms so that repositories and catalogues can read it without knowing anything about
ATRIUM. ATRIUM's exporter, `atrium_rocrate.py` (RO-Crate **1.1**), turns a
[document record](../ecosystem/document-contract.md) into such a description, and a set of records
from one run into a crate of crates.

A crate is what a repository, a catalogue or a reviewer receives: the data files plus a
description they can read with generic RO-Crate tooling — who produced what, with which
program, when, under which licence — without running any ATRIUM code.

## What happens to these two tools' blocks

Exporting the [worked-example record](../ecosystem/document-contract.md#a-worked-example) —
page-classification's `page_categories` and `pages`, then the translator's `translations` and
`derived_from` — gives 18 entities:

| In the record                                     | In the crate                                                                                                                                   | What the crate carries                                                                                                                            |
|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `page_categories: {"1": "TEXT_P"}`                | a `DefinedTerm` `https://w3id.org/atrium/page-category/TEXT_P`, in the `DefinedTermSet` `…/scheme/page-category`, listed in the root's `about` | the label: a crate says the document is *about* `TEXT_P`; the per-page assignment stays in the record                                             |
| `pages[].category`, `pages[].category_confidence` | the same `DefinedTerm`, de-duplicated                                                                                                          | the label, once; the confidence stays in the record                                                                                               |
| `translations`                                    | a `#block-translations` `CreativeWork`, created by `#tool-translator`                                                                          | the block, with its creator and date; the language pair, backend and output mode stay in the record                                               |
| `derived_from.translated_xml`                     | a `File` `CTX000000003-1_en.alto.xml`, `encodingFormat: application/alto+xml`, in the root's `hasPart`                                         | the translated file, by the name the translator records                                                                                           |
| `derived_from.classification` (when present)      | a `File` in `hasPart`                                                                                                                          | page-classification's result table for the run                                                                                                    |
| each `assembled.blocks` stamp                     | a `#block-<name>` `CreativeWork` with `recordBlock`, `dateModified` and `creator`                                                              | who wrote each block last                                                                                                                         |
| each `provenance.contributors[]` entry            | a `#run-<program>-<run_id>` `CreateAction`: `instrument` the tool, `result` the blocks it wrote                                                | who ran, when, and what they produced                                                                                                             |
| each program                                      | a `#tool-<program>` `SoftwareApplication` with the repository `url`                                                                            | the program and its repository; version, image and runtime when a paradata map is passed in from Python                                           |
| `provenance.license`                              | the root's `license`                                                                                                                           | the record's computed licence — see [how the record's licence is computed](../ecosystem/document-contract.md#how-the-records-licence-is-computed) |

The root also names the project's authors as ORCID `Person` entities.

For page-classification's half of that record, the heart of the output reads:

```json
{ "@id": "./", "@type": "Dataset",
  "name": "ATRIUM document record CTX000000003", "identifier": "CTX000000003",
  "about": [ { "@id": "https://w3id.org/atrium/page-category/TEXT_P" } ],
  "license": { "@id": "https://opensource.org/license/mit/" },
  "datePublished": "2026-09-22",
  "mentions": [ { "@id": "#run-page-classification-260922-220516" } ],
  "author": [ "…" ] },
{ "@id": "#block-page_categories", "@type": "CreativeWork", "recordBlock": "page_categories",
  "creator": { "@id": "#tool-page-classification" },
  "dateModified": "2026-09-22T22:05:16.866272+00:00" },
{ "@id": "https://w3id.org/atrium/page-category/TEXT_P", "@type": "DefinedTerm",
  "name": "TEXT_P", "termCode": "TEXT_P",
  "inDefinedTermSet": { "@id": "https://w3id.org/atrium/scheme/page-category" } }
```

## Properties of a crate

* **It is deterministic.** Entities are merged by `@id`, the descriptor and the root come first,
  everything else is sorted by `@id`, and the JSON is written with sorted keys. The same record
  always produces byte-identical output, so a crate can be diffed and committed.
* **`datePublished` is derived, not stamped.** It is the newest of the record's block stamps and
  contributor times, cut to a date — never the export clock.
* **Granularity survives.** Each block keeps its own entity with its own creator, so "who produced
  the page categories" and "who produced the translation" have separate answers.
* **Controlled values become resolvable terms**, under the [SKOS URIs](skos.md#how-a-uri-is-minted).

## Running the exporter

The exporter is vendored into every tool as `atrium_rocrate.py` and runs as a separate step,
over records that already exist — a tool run writes records, and a crate is made from them
when they are to be published:

```bash
python atrium_rocrate.py --document CTX000000003.document.json --out-dir crate/
python atrium_rocrate.py --run 1.document.json 2.document.json --paradata run.json --out-dir crate/
python atrium_rocrate.py --selftest
```

`--document` writes one document's crate; `--run` writes a run crate whose `hasPart` holds one
sub-crate per document, and additionally conforms to the Process Run Crate profile. The write is
atomic.

A crate describes; it does not replace the record. Per-page detail — which page carries
which category, with what confidence, and the language pair of a translation — stays in the
record, which can itself be shipped inside the crate as one of its files.
`rocrate_export.md` §7 lists what the export leaves for later work.

## Where RO-Crate sits among the standards

RO-Crate is one of the standards the project's data management plan names, alongside CIDOC-CRM,
SKOS, PeriodO, Getty AAT, TEI, DataCite and IIIF. The ecosystem deliberately does **not** apply
heavyweight ontologies — W3C PROV-O, CIDOC-CRM — during raw extraction over a corpus of more than a
million pages: the record stays a plain JSON document, and the crate is the *view* that a
catalogue reads. `rocrate_export.md` §3 is the reasoning in full.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                      | What was taken from it                 |
|---------------------------------------------------------------------------------------------|----------------------------------------|
| `atrium-project/docs/templates/shared/atrium_rocrate.py` — run on the worked-example record | the mapping table and the JSON excerpt |
| `atrium-project/docs/rocrate_export.md` §§3, 4.1, 6, 7                                      | the design and the reasoning           |
