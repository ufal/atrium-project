---
title: RO-Crate export
nav_order: 7
status: published
round: 8
issue: 79
---

# RO-Crate export

This page explains what ATRIUM can publish as an RO-Crate, the run description every service returns,
and what a crate holds. It is for integrators.
[`docs/rocrate_export.md`](https://github.com/ufal/atrium-project/blob/main/docs/rocrate_export.md) is the
full guide, including an RO-Crate tutorial from zero.

## RO-Crate in one paragraph

An RO-Crate is a folder with one extra file, `ro-crate-metadata.json`: a JSON-LD description of what is in
the folder, who made it, with which software, and under which licence — written in schema.org terms so
that repositories and catalogues can read it without knowing anything about ATRIUM. ATRIUM's exporter,
`atrium_rocrate.py`, writes **RO-Crate 1.2 with the Process Run Crate 0.5 profile**, the pair agreed with
AMČR. It turns a [document record](../ecosystem/document-contract.md) and the paradata of the runs that
wrote it into such a description, a set of records from one run into a crate of crates, and one run of one
tool into a `CreateAction`.

## What a crate holds

The record holds content only, so everything a crate says about how the record was made comes from the
runs' paradata.

| In the crate                                    | Taken from                             | What it says                                                                                                                  |
|-------------------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| the root `Dataset`, its `identifier` and `name` | the record's `doc_id`                  | which document this is                                                                                                        |
| the root's `isBasedOn` → `#source`              | the record's `source`                  | the original, by file name, media type and SHA-512; it is the archive's, not part of the crate                                |
| the root's `about` → `DefinedTerm`s             | every controlled value in the record   | the page categories, line categories, entity types and vocabulary concepts, as resolvable URIs                                |
| the root's `mentions` → `CreateAction`s         | each run's paradata                    | one action per run: the tool, the image, the times, the status                                                                |
| an action's `object` and `result`               | the paradata's inputs and outputs      | each input and output as an AMČR distribution, by name and SHA-512; for the record, the fields the run wrote (`recordFields`) |
| a `SoftwareApplication` per tool                | the paradata, or the tool's repository | the tool at its release, with its `version` and its authors from `CITATION.cff` as `creator`                                  |
| the root's `license` → `#no-licence-asserted`   | —                                      | no licence is asserted: the rights depend on the source and on AMČR, and each run lists its components with their own terms   |

For the example record of the hub, with two sample runs (the record built by ocr-postprocess, then
nlp-enrich adding its layer), the heart of the crate reads:

```json
{ "@id": "./", "@type": "Dataset",
  "name": "ATRIUM document record CTX000000001", "identifier": { "@id": "#doc_id" },
  "schemaVersion": "2.0",
  "conformsTo": { "@id": "https://w3id.org/ro/wfrun/process/0.5" },
  "isBasedOn": { "@id": "#source" },
  "license": { "@id": "#no-licence-asserted" },
  "datePublished": "2026-07-24",
  "mentions": [ { "@id": "urn:uuid:5a1e0c1e-1b2d-4c3e-8f40-0a1b2c3d4e5f" },
                { "@id": "urn:uuid:9c8b7a6d-5e4f-4321-9abc-def012345678" } ] },
{ "@id": "urn:uuid:9c8b7a6d-5e4f-4321-9abc-def012345678", "@type": "CreateAction",
  "name": "atrium-nlp-enrich run 260724-101500",
  "instrument": { "@id": "https://github.com/ufal/atrium-nlp-enrich/releases/tag/v1.4.0" },
  "object": [ { "@id": "#atrium/document-json@eeeeeeeeeeeeeeee" } ],
  "result": [ { "@id": "#atrium/document-json@aaaaaaaaaaaaaaaa" }, { "@id": "#atr/teitok-xml@ffffffffffffffff" } ],
  "startTime": "2026-07-24T10:15:00+00:00", "endTime": "2026-07-24T10:16:02+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus" }
```

The second run read the record version the first one wrote, and wrote the next version and the TEITOK
file; the versions and checksums are the module's sample values.

## What every service returns: the run

Each service answers a successful call with its run as `paradata`: one Process Run Crate `CreateAction`
for that call. Its `@id` is the run's `run_uuid`; its `instrument` is the tool at its release; its
`containerImage` is the image it ran as; its `object` is what the call read and its `result` what it
wrote, each an AMČR distribution by name and SHA-512; its `agent` is the operating organisation when
`ATRIUM_RUN_AGENT` is set; and `paradataRecord` carries the run's whole paradata record. It is what AMČR
stores as the distribution's paradata, `paradata/<distribution>`.

A **fragment** is the same kind of entities without a descriptor or a root, for a crate someone else owns:
`atrium_rocrate.py --document … --fragment` for a record, `action_fragment()` for one service's action. The
host keeps its own root `./`, lists the actions in its `mentions` and declares the profile. AMČR builds the
crate of each archived record this way: its root is the whole AMČR record, and it reuses ATRIUM's
descriptions of the actions and the software, and the validator.

## Properties of a crate

* **It is deterministic.** Entities are merged by `@id`, the descriptor and the root come first, everything
  else is sorted by `@id`, and the JSON is written with sorted keys. The same record and paradata always
  produce byte-identical output, so a crate can be diffed and committed.
* **`datePublished` is derived, not stamped.** It is the newest run's end time, cut to a date — never the
  export clock. Without paradata there is no run, and it reads `1970-01-01`.
* **Identifiers are stable.** A run is its `run_uuid`, a tool its release page, a distribution version its
  name and SHA-512; the exporter mints none of them.
* **It names no local path.** Inputs and outputs are distributions, never file paths or SHA-256 `ni:` URIs.
* **Controlled values become resolvable terms**, under the [SKOS URIs](skos.md#how-a-uri-is-minted).
* **It is validated.** The hub's CI runs the RO-Crate validator on the module's sample crates and on the
  end-to-end run's record, once for RO-Crate 1.2 and once for Process Run Crate 0.5.

## Running the exporter

The exporter is vendored into every tool as `atrium_rocrate.py` and runs as a separate step, over records
that already exist:

```bash
python atrium_rocrate.py --document CTX000000003.document.json --paradata run1.json --paradata run2.json --out-dir crate/
python atrium_rocrate.py --document CTX000000003.document.json --fragment
python atrium_rocrate.py --run 1.document.json 2.document.json --paradata run.json --out-dir crate/
python atrium_rocrate.py --selftest
```

`--document` writes one document's crate; `--fragment` its entities only (`--wrap` puts them under a stub
root); `--run` writes a run crate whose `hasPart` references one sub-crate per document. The write is
atomic.

A crate describes; it does not replace the record. Per-page detail — which page carries which category,
with what confidence — stays in the record. `rocrate_export.md` §8 lists what a crate cannot yet say.

## Where RO-Crate sits among the standards

RO-Crate is one of the standards the project's data management plan names, alongside CIDOC-CRM, SKOS,
PeriodO, Getty AAT, TEI, DataCite and IIIF. The ecosystem deliberately does **not** apply heavyweight
ontologies — W3C PROV-O, CIDOC-CRM — during raw extraction over a corpus of more than a million pages: the
record stays a plain JSON document, and the crate is the *view* that a catalogue reads.
`rocrate_export.md` §3 is the reasoning in full.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                                                                      | What was taken from it                 |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `atrium-project/docs/templates/shared/atrium_rocrate.py` (`test`) — `document_crate()` on `fixtures/atrium_document.example.json` with `_sample_paradata()` | the mapping and the JSON excerpt       |
| `atrium-project/docs/rocrate_export.md` §§3, 4, 5, 7, 8, 9                                                                                                  | the design and the reasoning           |
| ARÚP's output contract of 12 November 2026, section 8                                                                                                       | AMČR's own crate of an archived record |
