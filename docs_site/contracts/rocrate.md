---
title: RO-Crate export
nav_order: 7
status: partial
round: 6
issue: 57
---

# RO-Crate export

What ATRIUM can publish as an RO-Crate, the run description every service returns, and how the
blocks page-classification and the translator write are carried into a crate.

!!! info "Scope"
    The exporter handles every block. The mapping below is for the blocks these two tools
    write, taken from the exporter's own output.
    [`docs/rocrate_export.md`](https://github.com/ufal/atrium-project/blob/main/docs/rocrate_export.md)
    is the full guide, including an RO-Crate tutorial from zero.

## RO-Crate in one paragraph

An RO-Crate is a folder with one extra file, `ro-crate-metadata.json`: a JSON-LD description of
what is in the folder, who made it, with which software, and under which licence — written in
schema.org terms so that repositories and catalogues can read it without knowing anything about
ATRIUM. ATRIUM's exporter, `atrium_rocrate.py`, writes **RO-Crate 1.2 with the Process Run Crate
0.5 profile**, the pair agreed with AMČR, which stores every archived record as an RO-Crate
(atrium-project#71). It turns a [document record](../ecosystem/document-contract.md) into such a
description, a set of records from one run into a crate of crates, and one run of one tool into a
`CreateAction`.

A crate is what a repository, a catalogue or a reviewer receives: the data files plus a
description they can read with generic RO-Crate tooling — who produced what, with which
program and version, when, under which licence — without running any ATRIUM code.

## What happens to these two tools' blocks

Exporting the [worked-example record](../ecosystem/document-contract.md#a-worked-example) —
page-classification's `page_categories` and `pages`, then the translator's `translations` and
`derived_from` — with each run's paradata gives 22 entities:

| In the record                                     | In the crate                                                                                                                                   | What the crate carries                                                                                                                            |
|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `page_categories: {"1": "TEXT_P"}`                | a `DefinedTerm` `https://w3id.org/atrium/page-category/TEXT_P`, in the `DefinedTermSet` `…/scheme/page-category`, listed in the root's `about` | the label: a crate says the document is *about* `TEXT_P`; the per-page assignment stays in the record                                             |
| `pages[].category`, `pages[].category_confidence` | the same `DefinedTerm`, de-duplicated                                                                                                          | the label, once; the confidence stays in the record                                                                                               |
| `translations`                                    | a `#block-translations` `CreativeWork`, in the `result` of the translator's run                                                                | the block and its date; the language pair, backend and output mode stay in the record                                                             |
| `derived_from.translated_xml`                     | a `File` `CTX000000003-1_en.alto.xml`, `encodingFormat: application/alto+xml`, in the root's `hasPart`                                         | the translated file, by the name the translator records; with the folder at hand, its `contentSize`                                               |
| `derived_from.classification` (when present)      | a `File` in `hasPart`                                                                                                                          | page-classification's result table for the run                                                                                                    |
| each `assembled.blocks` stamp                     | a `#block-<name>` `CreativeWork` with `recordBlock` and `dateModified`                                                                         | the block; the run that wrote it lists it as `result`                                                                                             |
| each `provenance.contributors[]` entry            | a `CreateAction` with the run's `run_uuid` as `@id` (`#run-<program>-<run_id>` for a record written before it existed)                         | who ran, when (`startTime`/`endTime`), in which image, with what status, and what they produced                                                   |
| each program                                      | a `SoftwareApplication` whose `@id` is its release page, with `version`, the repository `url` and the authors as `creator`                     | the program, its version and its authors; without paradata the id is the repository and the version reads `unrecorded`                            |
| `provenance.license`                              | the root's `license`                                                                                                                           | the record's computed licence — see [how the record's licence is computed](../ecosystem/document-contract.md#how-the-records-licence-is-computed) |

The root declares the Process Run Crate profile; the project's authors appear as ORCID `Person`
entities, the `creator` of each tool.

For page-classification's half of that record, the heart of the output reads:

```json
{ "@id": "./", "@type": "Dataset",
  "name": "ATRIUM document record CTX000000003", "identifier": { "@id": "#doc_id" },
  "conformsTo": { "@id": "https://w3id.org/ro/wfrun/process/0.5" },
  "about": [ { "@id": "https://w3id.org/atrium/page-category/TEXT_P" } ],
  "license": { "@id": "https://opensource.org/license/mit/" },
  "datePublished": "2026-09-22",
  "mentions": [ { "@id": "#run-page-classification-260922-220516" }, "…" ] },
{ "@id": "#run-page-classification-260922-220516", "@type": "CreateAction",
  "instrument": { "@id": "https://github.com/ufal/atrium-page-classification/releases/tag/v1.9.0-beta" },
  "containerImage": { "@id": "#image:ghcr.io/ufal/atrium-page-classification:1.9.0-beta" },
  "startTime": "2026-09-22T22:04:58+00:00", "endTime": "2026-09-22T22:05:16+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus",
  "result": [ { "@id": "#block-page_categories" }, { "@id": "#block-pages" } ] },
{ "@id": "https://github.com/ufal/atrium-page-classification/releases/tag/v1.9.0-beta",
  "@type": "SoftwareApplication", "name": "atrium-page-classification", "version": "1.9.0-beta",
  "url": "https://github.com/ufal/atrium-page-classification",
  "creator": [ { "@id": "https://orcid.org/0009-0002-4773-2797" }, "…" ] }
```

## What every service returns: the run

Each service answers a successful call with its run as `paradata`: one Process Run Crate
`CreateAction` for that call, built by `atrium_rocrate.create_action()`. Its `@id` is the
`run_uuid` the call stamped into the record it returned; its `instrument` is the tool at its
release; its `containerImage` is the image it ran as; its `object` is the upload (by content
hash) and the record it was handed; its `result` is the blocks it wrote; its `agent` is the
operating organisation when `ATRIUM_RUN_AGENT` is set; and `paradataRecord` carries the run's whole
paradata record. It is what AMČR stores as the run's paradata file.

A **fragment** is the same kind of entities without a descriptor or a root, for a crate someone
else owns: `atrium_rocrate.py --document … --fragment` for a record, `action_fragment()` for one
service's action. The host keeps its own root `./`, lists the actions in its `mentions` and
declares the profile.

## Properties of a crate

* **It is deterministic.** Entities are merged by `@id`, the descriptor and the root come first,
  everything else is sorted by `@id`, and the JSON is written with sorted keys. The same record
  always produces byte-identical output, so a crate can be diffed and committed.
* **`datePublished` is derived, not stamped.** It is the newest of the record's block stamps and
  contributor times, cut to a date — never the export clock.
* **Identifiers are stable.** A run is its `run_uuid`, a tool its release page, an uploaded file
  its content; the exporter mints none of them.
* **Granularity survives.** Each block keeps its own entity and each run lists the blocks it
  wrote, so "who produced the page categories" and "who produced the translation" have separate
  answers.
* **Controlled values become resolvable terms**, under the [SKOS URIs](skos.md#how-a-uri-is-minted).
* **It is validated.** The hub's CI runs the RO-Crate validator on the module's sample crates and
  on the end-to-end run's record, once for RO-Crate 1.2 and once for Process Run Crate 0.5.

## Running the exporter

The exporter is vendored into every tool as `atrium_rocrate.py` and runs as a separate step,
over records that already exist — a tool run writes records, and a crate is made from them
when they are to be published:

```bash
python atrium_rocrate.py --document CTX000000003.document.json --paradata run1.json --paradata run2.json --out-dir crate/
python atrium_rocrate.py --document CTX000000003.document.json --fragment
python atrium_rocrate.py --run 1.document.json 2.document.json --paradata run.json --out-dir crate/
python atrium_rocrate.py --selftest
```

`--document` writes one document's crate (`--data-dir` adds the files' sizes); `--fragment` its
entities only (`--wrap` puts them under a stub root); `--run` writes a run crate whose `hasPart`
holds one sub-crate per document. The write is atomic.

A crate describes; it does not replace the record. Per-page detail — which page carries
which category, with what confidence, and the language pair of a translation — stays in the
record, which can itself be shipped inside the crate as one of its files.
`rocrate_export.md` §8 lists what the export leaves for later work.

## Where RO-Crate sits among the standards

RO-Crate is one of the standards the project's data management plan names, alongside CIDOC-CRM,
SKOS, PeriodO, Getty AAT, TEI, DataCite and IIIF. The ecosystem deliberately does **not** apply
heavyweight ontologies — W3C PROV-O, CIDOC-CRM — during raw extraction over a corpus of more than a
million pages: the record stays a plain JSON document, and the crate is the *view* that a
catalogue reads. `rocrate_export.md` §3 is the reasoning in full.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                        | What was taken from it                 |
|---------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `atrium-project/docs/templates/shared/atrium_rocrate.py` — run on the worked-example record with its paradata | the mapping table and the JSON excerpt |
| `atrium-project/docs/rocrate_export.md` §§3, 4.1, 5, 7, 8, 9                                                  | the design and the reasoning           |
