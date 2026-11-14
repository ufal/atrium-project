# RO-Crate Export

> **Repository names (2026-10-01).** This document predates the repository moves of atrium-project#72 and
> uses the names of its time: `alto-postprocess` is now `ocr-postprocess`; `llm-enrich` split into
> `keyword-extract` (its keyword stage, with the keyword extraction of `nlp-enrich`) and `digital-convert`
> (the born-digital converter). The old repositories are superseded and, since 2026-10-19, archived (read-only). Read the names below through that map;
> the current ones are in [`docs_site/ecosystem/repository-map.md`](../docs_site/ecosystem/repository-map.md).

This document explains **what RO-Crate is** (assuming you have never seen one), **why ATRIUM has
one**, and **how to use `atrium_rocrate.py`**: the crate of a document record, the
`CreateAction` every service returns for its run, and the fragment another crate embeds. It is the
companion to [`document_schema.md`](document_schema.md), which defines the record this exports, to
[`paradata_schema.md`](paradata_schema.md), which defines the run record an action is built from,
and to [`skos_strategy.md`](skos_strategy.md), which defines the vocabulary URIs it references.

Template file: [`templates/shared/atrium_rocrate.py`](templates/shared/atrium_rocrate.py).
Design discussion: [ufal/atrium-project#54](https://github.com/ufal/atrium-project/issues/54); the
pilot baseline agreed with AMČR: [ufal/atrium-project#71](https://github.com/ufal/atrium-project/issues/71).

---

## 1. The one-paragraph version

An **RO-Crate** ("Research Object Crate") is a folder of files plus a single metadata file at its
root called `ro-crate-metadata.json`. That file says, in a machine-readable way: *what this folder
is, which files are in it, who made them, under what licence, and with which software*. It is a
community convention, not a piece of software — you do not install RO-Crate, you **write one
JSON file to a convention**, and any tool that knows the convention can read your folder.

`atrium_rocrate.py` writes that file from an `atrium_document` record, and builds the
`CreateAction` that describes one run of one tool. ATRIUM writes **RO-Crate 1.2** with the
**Process Run Crate 0.5** profile: the pair agreed with AMČR, which stores every archived record as
an RO-Crate and every run as a `CreateAction` (atrium-project#71). Nothing else changes: no pipeline
behaviour, no new dependency, no upload anywhere.

---

## 2. RO-Crate from zero

### 2.1 The problem it solves

You hand a colleague — or ARIADNE, or a repository, or a reviewer in 2031 — a folder:

```
CTX000000001/
├── TEITOK/CTX000000001.teitok.xml
├── TRANSLATED/CTX000000001.alto.xml
└── KW_PER_DOC_LLM/CTX000000001_enriched.json
```

They can open the files. They cannot tell what document this is, who produced it, which tool
version, whether they may redistribute it, or what `KW_PER_DOC_LLM` means. Every one of those
answers exists in ATRIUM — in the `.document.json` record and its paradata — but in a format only
ATRIUM understands.

RO-Crate is the agreed shape for putting those answers *in the folder*, in a form a stranger's
software can read.

### 2.2 The format, in four concepts

`ro-crate-metadata.json` is **JSON-LD**. For our purposes JSON-LD is ordinary JSON with two extra
conventions: `@id` names a thing, and `@type` says what kind of thing it is. Anywhere a value is
`{"@id": "…"}`, that is a **pointer** to another thing, not a string.

The file has exactly two top-level keys:

```json
{
  "@context": "https://w3id.org/ro/crate/1.2/context",
  "@graph": [ … every entity, as a flat list … ]
}
```

* **`@context`** — where the property names come from. `name`, `creator`, `license` are not ours;
  they are [schema.org](https://schema.org) terms, and the context is what says so. It is a URL,
  it is fixed by the spec version, and you do not invent it. ATRIUM's crates add a small local map
  after it, for the few terms the RO-Crate context does not define (§10).
* **`@graph`** — a **flat** list of entities. Not nested: relationships are expressed by `@id`
  pointers, so the same entity can be referenced from many places without being copied. This is
  the single most surprising thing about the format on first reading.

Inside `@graph` there are four kinds of entity, and knowing which is which is most of
understanding RO-Crate:

| Kind                    | `@id`                                   | What it is                                                                                                                                     |
|-------------------------|-----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **Metadata descriptor** | `ro-crate-metadata.json`                | Describes the metadata file itself, and says which spec version it follows. Every crate has exactly one, and it is the entry point.            |
| **Root data entity**    | `./`                                    | The crate as a whole — the folder. Carries `name`, `description`, `datePublished`, `license`, and `hasPart`.                                   |
| **Data entities**       | a file path, e.g. `TEITOK/x.teitok.xml` | Files and folders that are **actually in the crate**. Listed in the root's `hasPart`.                                                          |
| **Contextual entities** | `#something` or a URL                   | Things that are *not* files: people, organisations, software, licences, actions, vocabulary terms. Referenced from wherever they are relevant. |

> ⚠️ **The one hard rule.** Everything in `hasPart` must actually exist in the crate (or be a
> resolvable URL), and every data entity must be reachable from the root through `hasPart`. A crate
> that lists a file it does not contain is invalid. This turns out to matter enormously for
> ATRIUM — see §4.2.

### 2.3 A minimal crate, in full

```json
{
  "@context": "https://w3id.org/ro/crate/1.2/context",
  "@graph": [
    {
      "@id": "ro-crate-metadata.json",
      "@type": "CreativeWork",
      "conformsTo": { "@id": "https://w3id.org/ro/crate/1.2" },
      "about": { "@id": "./" }
    },
    {
      "@id": "./",
      "@type": "Dataset",
      "name": "My folder",
      "description": "What is in it and why.",
      "datePublished": "2026-09-09",
      "license": { "@id": "https://creativecommons.org/licenses/by/4.0/" },
      "hasPart": [ { "@id": "notes.txt" } ]
    },
    { "@id": "notes.txt", "@type": "File", "name": "notes" }
  ]
}
```

That is a complete, valid RO-Crate. `name`, `description`, `datePublished` and `license` on the
root are the required four; everything beyond them is optional enrichment.

### 2.4 Vocabulary you will meet

| Term                                 | Meaning here                                                                                                                                                                                                                          |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Profile**                          | A named extra set of expectations layered on the base spec. ATRIUM declares *Process Run Crate 0.5*, because its crates describe tool runs. In RO-Crate 1.2 a profile is named on the **root's** `conformsTo`, as a `Profile` entity. |
| **`conformsTo`**                     | On the descriptor: the specification (`https://w3id.org/ro/crate/1.2`). On the root: the profiles.                                                                                                                                    |
| **`CreateAction`**                   | schema.org's "something was made": one run of one tool, with its `instrument` (the tool), `object` (what it read), `result` (what it wrote), `agent`, times and status.                                                               |
| **`SoftwareApplication`**            | A program, with its `version`. Its `creator` is the people who wrote it.                                                                                                                                                              |
| **`ContainerImage`**                 | A Workflow Run term: the image a run executed in, with its `registry`, `name` and `tag`.                                                                                                                                              |
| **`DefinedTerm` / `DefinedTermSet`** | A controlled-vocabulary term and its scheme. Ours resolve into the SKOS registry — see [`skos_strategy.md`](skos_strategy.md).                                                                                                        |
| **Fragment**                         | ATRIUM's word for crate entities without a descriptor and a root, made to be embedded in a crate someone else owns (§5.3).                                                                                                            |

---

## 3. Why ATRIUM has one

Three reasons, in descending order of how much they bind us:

1. **The pilot needs it.** AMČR stores every archived record as an RO-Crate (RO-Crate 1.2 with
   Process Run Crate 0.5), and every run's paradata as a JSON-LD file with one `CreateAction`
   (grounding report of 2026-09-30, items 1-3; atrium-project#71). Every ATRIUM service returns
   that action for its call, and the record's crate entities are what AMČR's record crate embeds.
2. **The DMP names it.** RO-Crate appears in the WP3 standards column alongside CIDOC CRM, SKOS,
   PeriodO, Getty AAT, TEI, DataCite and IIIF.
3. **The record needs it.** Since record schema 2.0 the document record holds content only
   ([`document_schema.md`](document_schema.md)); how each version of it was made is said by the
   runs' paradata, and this is their form.

### What it is *not*, and this matters

The architecture deliberately avoids heavyweight ontological standards — W3C PROV-O, CIDOC-CRM,
JSON-LD — **during raw extraction**, because a 1.2-million-page corpus cannot afford them on the
hot path. `atrium_rocrate.py` does not reverse that decision. A crate is built **after the fact,
over records already on disk**; a service builds one small `CreateAction` from the paradata record
it has already written, once per call. No stage computes anything for it.

---

## 4. The mapping

### 4.1 Field by field

Since record schema 2.0 and paradata 3.0 (atrium-project#84) the record holds content only, so every
statement about a run comes from that run's paradata. Where a field does not exist it is **omitted,
not guessed** — a crate that asserts a checksum nobody computed is worse than one that admits the
gap. The one exception is a tool's `version`, which RO-Crate 1.2 makes a MUST: without paradata it
reads `"unrecorded"`, which states the gap instead of hiding it.

| RO-Crate                     | ATRIUM source                                                                            | Note                                                                                         |
|------------------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| root `identifier`            | `doc_id`, as a `PropertyValue` (`#doc_id`)                                               | the form RO-Crate 1.2 recommends                                                             |
| root `name`                  | `doc_id`                                                                                 |                                                                                              |
| root `datePublished`         | the **newest run's end time**                                                            | never the clock — see §7.3                                                                   |
| root `license`               | `#no-licence-asserted`, unless the caller asserts one (`license=`)                       | the rights in a document are the archive's to state; the tools assert none (D2)              |
| root `conformsTo`            | the Process Run Crate 0.5 `Profile`                                                      | the descriptor names RO-Crate 1.2                                                            |
| root `isBasedOn` → `#source` | `source`                                                                                 | contextual, not a part — §4.2; carries the archive's `sha512`                                |
| root `about` → `DefinedTerm` | every controlled value in the record; every AMČR/TEATER concept in `teater_category_ids` | `@id` from `atrium_vocab.concept_uri()`; a source concept keeps its own URI (nothing minted) |
| root `mentions`              | the runs' `CreateAction`s                                                                | one per paradata record (`action_from_paradata`) or returned action                          |
| `CreateAction` `object`      | paradata `inputs`                                                                        | by AMČR distribution name and SHA-512 (§5.1); the record input is the record version read    |
| `CreateAction` `result`      | paradata `outputs`                                                                       | the record's carries `recordFields`, the blocks and fields the run wrote                     |
| `SoftwareApplication`        | paradata `repository` / `tool_version` / `python_version`, else `REPO_URLS`              | `@id` = the release page; `version`; its own authors (`PROGRAM_AUTHORS`) as `creator`        |
| `ContainerImage`, `agent`    | paradata `docker_image` (ATRIUM_RUNNER_IMAGE) and `run_agent` (ATRIUM_RUN_AGENT)         | on the action, only when recorded                                                            |

Each **tool's `creator`** is its own authors, not the root's `author`: the record is the
archive's, the software is theirs (atrium-project#71). Who wrote which tool is `PROGRAM_AUTHORS`,
taken from each tool's `CITATION.cff`; a program it does not list (a predecessor) gets the authors
every tool has (`CORE_AUTHORS`), and a service's `-api` suffix is ignored. ORCIDs are their `@id`s,
so no ATRIUM identifier is minted for a person.

### 4.2 Distributions, not files

AMČR stores a document's outputs as **distributions** (`atrium/document-json`, `atr/docproc-json`,
`atr/teitok-xml`, `metadata`, `metadata-en`), and the crate names them the same way: every input and
output of a run is a `CreativeWork` with the distribution's `name` and its `sha512`, and an `@id`
that joins the two (`#atr/docproc-json@<first 16 hex of the digest>`). So the output of one step and
the input of the next are one entity, and a crate never names a local path or a SHA-256 `ni:` URI
(contract §6). An intermediate that is not stored but reaches a stored distribution is still named
by its SHA-512 and carries `stored: false` (D23).

The document crate has no `hasPart`: the files are AMČR's, held in its own crate, and a record names
none. The original is archive-managed and not in the crate, so `source` becomes the root's
`isBasedOn`, a contextual entity that is honest about its absence:

```json
{
  "@id": "#source",
  "@type": "CreativeWork",
  "name": "CTX000000001.pdf",
  "identifier": "CTX000000001",
  "encodingFormat": "application/pdf",
  "sha512": "72e9c14d…",
  "description": "The ORIGINAL input this record was built from, identified by doc_id and its SHA-512. Archive-managed and not part of this crate. Text obtained as: atr."
}
```

### 4.3 What a run wrote into the record

The record carries no stamps (D1). The run's paradata output for the record names the blocks
**and fields** the run wrote (`record_fields`, from `DocumentRecord.written()`), and the action's
result carries them as `recordFields`, a JSON literal:

```json
{
  "@id": "#atrium/document-json@eeeeeeeeeeeeeeee",
  "@type": "CreativeWork",
  "name": "atrium/document-json",
  "encodingFormat": "application/json",
  "sha512": "eeee…",
  "recordFields": "{\"lines\": [\"page\", \"line\", \"text\", \"block\", \"text_source\", \"bbox_precision\"], \"pages\": [\"page\", \"page_index\", \"content_status\"]}"
}
```

That is finer than 1.x's one entity per block: a field-split block (`entities`, written by
nlp-enrich, with `pid` added by keyword-extract) is answered field by field, and the record version
each run read is its `object`, so the chain of versions is explicit.

---

## 5. One run: the `CreateAction`

### 5.1 What every service returns

Every ATRIUM service returns its run as `paradata`, with every successful response
(atrium-project#71). It is one Process Run Crate `CreateAction`, as nested JSON-LD, built by
`action_from_paradata()` from the paradata record the service's logger has just finalized. It is
the document AMČR stores as the distribution's `paradata/<distribution>`, and it reads:

```json
{
  "@context": ["https://w3id.org/ro/crate/1.2/context", { "…": "the local terms, §10" }],
  "@id": "urn:uuid:5a1e0c1e-1b2d-4c3e-8f40-0a1b2c3d4e5f",
  "@type": "CreateAction",
  "name": "atrium-ocr-postprocess run 260724-101112",
  "instrument": {
    "@id": "https://github.com/ufal/atrium-ocr-postprocess/releases/tag/v1.16.0-beta",
    "@type": "SoftwareApplication",
    "name": "atrium-ocr-postprocess", "version": "1.16.0-beta",
    "creator": [ { "@id": "https://orcid.org/0009-0002-4773-2797", "@type": "Person", "name": "Kateryna Lutsai" }, "…" ]
  },
  "containerImage": { "@id": "#image:ghcr.io/ufal/atrium-ocr-postprocess-api:1.16.0-beta", "…": "…" },
  "object": [
    { "@id": "#atr/docproc-json@cccccccccccccccc", "@type": "CreativeWork", "name": "atr/docproc-json", "sha512": "cccc…" },
    { "@id": "#atrium/document-json@dddddddddddddddd", "@type": "CreativeWork", "name": "atrium/document-json", "sha512": "dddd…" }
  ],
  "result": [
    { "@id": "#atrium/document-json@eeeeeeeeeeeeeeee", "@type": "CreativeWork", "name": "atrium/document-json",
      "sha512": "eeee…", "recordFields": "{\"lines\": [\"…\"], \"pages\": [\"…\"]}" }
  ],
  "agent": { "@id": "https://ror.org/…", "@type": "Organization" },
  "startTime": "2026-07-24T10:11:12+00:00",
  "endTime": "2026-07-24T10:11:40+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus",
  "paradataRecord": { "schema_version": "3.0", "program": "ocr-postprocess", "run_uuid": "urn:uuid:5a1e…", "…": "…" }
}
```

* **`@id` is the run's `run_uuid`**, minted by `atrium_paradata` when the run starts. The response,
  the paradata file and the archived crate name the run the same way.
* **`instrument`** is the tool. Its `@id` is its release page, so it is stable and resolvable; it
  carries `version` (never `softwareVersion`) and its authors as `creator`.
* **`containerImage`** is the image the service runs as (`ATRIUM_RUNNER_IMAGE`).
* **`object`** is what the call read and **`result`** what it wrote, each a distribution by name
  and SHA-512 (§4.2), from the paradata `inputs` and `outputs`. The record's result carries
  `recordFields` (§4.3).
* **`agent`** is the organisation operating the deployment, from `ATRIUM_RUN_AGENT`, an IRI.
  Unset, there is no agent: one is never invented, and it is never the processing account.
* **`startTime` / `endTime`** are UTC, to the second. **`actionStatus`** is
  `CompletedActionStatus`, or `FailedActionStatus` with `error` when the paradata say
  `action_status: failed`. A failed step fails the job and nothing is stored (D13), so what AMČR
  stores is always completed.
* **`paradataRecord`** is the whole paradata record as a JSON literal, so nothing it says is lost
  to a schema.org mapping. It carries no licence: `components` lists each component with its own
  terms, as facts.

`action_problems(action)` is the shared contract check, run by every repository's contract test and
by the E2E against a real response. Besides the frame it checks that every `object` and `result`
names a distribution and a SHA-512, that no `@id` is an `ni:` URI, that the record's result carries
`recordFields`, and that `paradataRecord` carries no licence.

### 5.2 Where each service returns it

| Service             | Where the action is                                                                                                      |
|---------------------|--------------------------------------------------------------------------------------------------------------------------|
| page-classification | `paradata` in `/predict_image` and `/predict_document`                                                                   |
| ocr-postprocess     | `paradata` in `/process`                                                                                                 |
| translator          | `paradata` with `response_format=json`; `paradata.json`, the fourth part of `multipart/mixed`; none in a bare XML answer |
| nlp-enrich          | `paradata` in `/enrich`, `/enrich_text` and a job's result                                                               |
| keyword-extract     | `paradata` in `/extract_keywords` and `/extract_keywords_text`                                                           |

nlp-enrich runs a pipeline of stages: its `paradataRecord` is the merged pipeline-run record. Each
tool adopts paradata 3.0 in its own repository; until it does, its action keeps the 1.x shape.

### 5.3 Fragments: entities for a crate someone else owns

AMČR's record crate is AMČR's: its root is the archived record, its files are the record's
distributions. What ATRIUM contributes are entities: the runs, the tools and their authors, the
images, the controlled terms. A **fragment** is exactly that — the entities with **no metadata
descriptor and no root**, so embedding one never creates a second root:

* `document_crate(record, paradata=…, fragment=True)`: the record's entities. `source_id="…"`
  points at the host's own entity for the original instead of a `#source`.
* `action_fragment(action)`: one service's `CreateAction`, flattened. In a crate the graph is flat,
  so `paradataRecord` and `recordFields` travel there as JSON text.

The host puts the entities in its `@graph`, lists every `CreateAction` in its root's `mentions`
and every `DefinedTerm` in `about`, and declares the Process Run Crate profile on its root.
`wrap_fragment()` does exactly that under a stub root, which is how a fragment is validated (§9)
and a working example for the host.

---

## 6. A real worked example

Everything below is genuine output of `document_crate()` over
`fixtures/atrium_document.example.json` and the module's two sample paradata records (an
ocr-postprocess run that built the record from docproc, and an nlp-enrich run that added entities)
— 37 entities. The record alone (`python3 atrium_rocrate.py --document …`) gives a crate with no
runs; pass `--paradata` once per run.

**The root**, abridged — every value is either a literal or an `@id` pointer, and there is no
`license`:

```json
{
  "@id": "./",
  "@type": "Dataset",
  "identifier": { "@id": "#doc_id" },
  "name": "ATRIUM document record CTX000000001",
  "datePublished": "2026-07-24",
  "schemaVersion": "2.0",
  "conformsTo": { "@id": "https://w3id.org/ro/wfrun/process/0.5" },
  "isBasedOn": { "@id": "#source" },
  "mentions":  [ { "@id": "urn:uuid:5a1e0c1e-1b2d-4c3e-8f40-0a1b2c3d4e5f" },
                 { "@id": "urn:uuid:9c8b7a6d-5e4f-4321-9abc-def012345678" } ],
  "about":     [ { "@id": "https://api.aiscr.cz/id/HES-000021" }, … 7 more terms … ]
}
```

**The second run**: it read the record version the first one wrote, and wrote the next version and
the TEITOK file:

```json
{
  "@id": "urn:uuid:9c8b7a6d-5e4f-4321-9abc-def012345678",
  "@type": "CreateAction",
  "name": "atrium-nlp-enrich run 260724-101500",
  "instrument": { "@id": "https://github.com/ufal/atrium-nlp-enrich/releases/tag/v1.4.0" },
  "object": [ { "@id": "#atrium/document-json@eeeeeeeeeeeeeeee" } ],
  "result": [ { "@id": "#atrium/document-json@aaaaaaaaaaaaaaaa" }, { "@id": "#atr/teitok-xml@ffffffffffffffff" } ],
  "startTime": "2026-07-24T10:15:00+00:00",
  "endTime": "2026-07-24T10:16:02+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus"
}
```

**A controlled term**, joining the crate to the SKOS registry:

```json
{
  "@id": "https://w3id.org/atrium/entity-type/LOC",
  "@type": "DefinedTerm",
  "name": "LOC",
  "termCode": "LOC",
  "inDefinedTermSet": { "@id": "https://w3id.org/atrium/scheme/entity-type" }
}
```

---

## 7. Using it

### 7.1 The functions

**Per-document** — one crate per `doc_id`, with the runs that wrote it:

```bash
python3 atrium_rocrate.py --document CTX000000001.document.json \
    --paradata paradata/260724-101112_ocr-postprocess.json --paradata paradata/260724-101500_nlp-enrich.json \
    --out-dir crates/CTX000000001/
# -> crates/CTX000000001/ro-crate-metadata.json
```

**The fragment**, and the same under a stub root for a validator or a reader:

```bash
python3 atrium_rocrate.py --document CTX000000001.document.json --fragment                # entities only
python3 atrium_rocrate.py --document CTX000000001.document.json --fragment --wrap --out-dir out/
```

**Per-run** — one crate per pipeline run, whose `hasPart` **references** the per-document crates
rather than re-describing them, so it stays the same size for five documents as for five thousand:

```bash
python3 atrium_rocrate.py --run doc_json/*.document.json \
    --paradata paradata/260724-101112_pipeline-run.json \
    --out-dir crates/
```

Without `--out-dir` the crate goes to stdout, which is what you want for a pipe or a diff.

From Python:

```python
from atrium_rocrate import action_from_paradata, document_crate, write_crate

action = action_from_paradata(logger.record)  # what a service returns as `paradata`
crate = document_crate(record, paradata=[ocr_paradata, nlp_paradata])
write_crate(crate, "crates/CTX000000001/")
```

A caller that has no paradata 3.0 record builds the entities itself: `create_action(paradata,
inputs=[file_entity(name, data, media_type=…)], outputs=[record_result(doc.written(), data)])`, and
`record_entity(doc_id, data)` for the record version read.

### 7.2 What the folder looks like

A document crate is one file, `ro-crate-metadata.json`, in a directory of the caller's choosing:
it names no data files (§4.2). A run crate's `hasPart` references the per-document crates, which
sit beside it as `<doc_id>/ro-crate-metadata.json`. `atrium_rocrate.py` writes metadata; it never
copies or moves pipeline outputs.

### 7.3 Determinism, and why it is a feature

Two runs on the same input produce **byte-identical** JSON: `@graph` is sorted by `@id` (with the
descriptor and root pinned first), `json.dumps` runs with `sort_keys=True`, **`datePublished` comes
from the newest run's end time, not from `datetime.now()`**, and a run's `@id` is the `run_uuid`
its paradata carry — the exporter mints nothing. Re-exporting an archived record in 2031 reproduces
the crate it shipped with.

This is not fussiness. The canonical files are drift-gated by byte comparison, and a crate that
changed on every export could not be committed, diffed, or checksummed.

---

## 8. What a crate cannot yet say

Recorded rather than papered over. None of these blocks a crate; each makes it materially better.

| Gap                                                                            | Consequence                                                    | Fix                                           |
|--------------------------------------------------------------------------------|----------------------------------------------------------------|-----------------------------------------------|
| **No git SHA.** Paradata carries `runner_ref` (a branch or tag), not a commit. | Software provenance is "this release", not "this commit".      | add a commit SHA to `atrium_paradata`         |
| **No DOI or PID anywhere** — not on any `CITATION.cff`, not on any record.     | The crate has no persistent identifier; `@id` is a local path. | out of scope here; needs a repository deposit |
| **`entities[].translation_en` is reserved**, written by no tool.               | A declared part of the schema can never appear in a crate.     | reserved (#70, contract §5)                   |
| **Tools still on paradata 2.0** return actions without distributions.          | Their `object`/`result` fail `action_problems()`.              | each tool adopts paradata 3.0 (#84)           |

---

## 9. Validating a crate

There are two different checks and it is important not to mistake one for the other.

**`--selftest` is a structural check, run in every repository.** It is a
`para-drift.reusable.yml` step and asserts the things this module is responsible for:

```bash
python3 atrium_rocrate.py --selftest      # exit 0, or 1 with one line per problem
```

It checks the descriptor and the profile; the root's required properties; that **no reference
dangles**; that the root names `#no-licence-asserted`; that output is deterministic and `datePublished`
derived from the runs; that runs keep their `run_uuid` ids, tools their release ids, `version` and
authors; that inputs and outputs are named by distribution and SHA-512, never an `ni:` URI; the
fragment and its wrapping; and that a service's `CreateAction` meets `action_problems()`.

**Conformance is the RO-Crate validator's, run in the hub's CI only.** `tools/ci/rocrate_check.py`
runs [`roc-validator`](https://github.com/crs4/rocrate-validator), pinned in
`tools/ci/requirements-rocrate.txt`, against each profile **separately**:

* `ro-crate-1.2`;
* `process-run-crate-0.5 --disable-profile-inheritance`. The validator declares Process Run Crate
  0.5 a profile of RO-Crate **1.1**, and with inheritance on it would require the descriptor to say
  1.1.

| Where                                     | What it validates                                                                                        | Fails on                                             |
|-------------------------------------------|----------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `hub-self-check.yml` (`rocrate-validate`) | the module's sample document crate, run crate, record fragment and service action (the last two wrapped) | RO-Crate MUST; Process Run Crate MUST **and** SHOULD |
| `e2e-pipeline-smoke.yml`                  | the fragment of the E2E's final record, from the record and every stage's paradata file, wrapped         | MUST of either; SHOULDs are reported as warnings     |

The RO-Crate SHOULD notes the samples carry are known and stay: the root has no `publisher` (the
archive that publishes a crate adds itself); the operating organisation has no `contactPoint`
(`ATRIUM_RUN_AGENT` gives an IRI and nothing more); open-ended lists (`mentions`, `result`) stay
arrays when they hold one value; and a run crate's nested record crate is a reference, so its
metadata file keeps the nested path as `@id` and its `Dataset` lists no `hasPart`, which is the
nested crate's own business.

A fragment has no root, so it can only be validated inside one: the stub root of
`wrap_fragment()`. The validator stays out of the tool repositories on purpose: the module is
stdlib-only (§10), and one pinned check in the hub covers the byte-identical copies in all five.

**The version pair moves together**, in one planned pass: to RO-Crate 1.3 with Process Run Crate
0.6, when the validator checks that pair (`ROCRATE_VERSION`, `PROCESS_RUN_PROFILE` and the pin).

---

## 10. Design decisions, and what was rejected

**Standard library only — no `rocrate` package, no `rdflib`.** The same rule
[`atrium_vocab.py`](templates/shared/atrium_vocab.py) states for itself, for the same reason: the
serialisation here is small, closed and fully determined by the record, and the output is
drift-gated by byte comparison. A general-purpose serialiser that emits blank-node identifiers or
unordered graphs fails that gate on every run. It would also add a third-party dependency to six
repositories, each with its own requirements files and image builds, to save a few hundred lines
of dictionary construction.

**Hand-rolled JSON-LD is precedented here, not novel.** `atrium_vocab.to_jsonld()` already emits
`@context` + `@graph` with `@id`/`@type` entities, deterministically, stdlib-only, with a
`--selftest` and a companion JSON Schema. `atrium_rocrate.py` is built to the same shape
deliberately, so a maintainer who has read one can read the other.

**Both crate kinds, and the action.** A per-document crate matches the record's own granularity
and is the natural unit for catalogue export. A run crate matches the DMP's provenance framing.
The `CreateAction` is the unit AMČR stores per run. Making the run crate *reference* the document
crates rather than inline them is what keeps it viable at corpus scale.

**`@context` is an array.** RO-Crate 1.2's own context plus a small local map, the spec-sanctioned
way to add terms: `sha512`, `stored`, `recordFields` and `paradataRecord` (the last two JSON
literals) under `https://w3id.org/atrium/`, and the four Workflow Run
terms (`ContainerImage`, `containerImage`, `registry`, `tag`). Declaring those four here rather than
loading the Workflow Run context keeps every crate dependent on exactly one remote document.

**Stable ids.** A run is its `run_uuid` (`urn:uuid:…`), minted by `atrium_paradata` when the run
starts; `run_id` has one-second resolution and two parallel workers can share one. A tool is its
release page, an absolute URL that resolves. A distribution version is its name and SHA-512. None
of them is minted by the exporter.

**`creator` is for people.** A tool's authors are its `creator`. What a run wrote is its
`result`, not a `creator` naming software.

**No licence asserted on the root** (D2). A crate root names a licence only when its caller
asserts one. Otherwise its `license` names `#no-licence-asserted`, a `CreativeWork` that asserts
nothing: the rights depend on the source and on AMČR's permission, and each run's paradata lists
its components with their own terms. RO-Crate 1.2 requires a root `license` (rule 13.3), and the
placeholder is not a calculated licence: motyc's option 1 on
[#6](https://github.com/ufal/atrium-project/issues/6#issuecomment-6818590785), confirmed on
2026-11-12 together with the removal of the calculated licence. A fragment carries no licence
entity; its host's root decides.

**`PROCESS_RUN_PROFILE` is pinned and checked.** 0.5 is the profile IRI the validator ships; the
caveat that used to sit on the constant is replaced by the hub's validator job.

---

## 11. Distribution and maintenance

`atrium_rocrate.py` is **hub-canonical**: it lives in `docs/templates/shared/` and is copied
byte-identical into the five tool repos, exactly like `atrium_document.py` and `atrium_vocab.py`.
It sits at each tool repo's root, beside `atrium_vocab.py`, which it imports for concept URIs. A
service imports it from there to build its `CreateAction`.

It is registered once, as a row in [`templates/shared/MANIFEST.json`](templates/shared/MANIFEST.json)
(atrium-project#59). `scripts/revendor_shared.sh`, `para-drift.reusable.yml` (its `diff -u` and its
`--selftest` step) and the `[format] exclude` list of [`templates/ruff.toml`](templates/ruff.toml)
all read that row. Without the exclusion `ruff format` would reflow the vendored copy to the
local `line-length`, and para-drift would go red on the next commit.

**To change the crate's shape**, edit only the hub copy and follow the re-vendor procedure in
[`docker_gha.md`](docker_gha.md): the hub commit first, then `v1` on it, then one commit per tool
repository with its copies (`scripts/revendor_shared.sh`) and its pins
(`scripts/pin_hub_reusables.py --sha …`) together. `para-drift` reads the hub at each caller's
pinned `hub-ref`, so copies newer than the pin fail it.

**Bumping `ROCRATE_VERSION`** is a compatibility statement about every crate already written,
exactly like `SCHEMA_VERSION` in `atrium_document.py`. `conformsTo` is what a consumer reads to
decide how to interpret the graph. Do not bump it to pick up a new property.

---

## 12. Further reading

* RO-Crate 1.2 specification — [w3id.org/ro/crate/1.2](https://w3id.org/ro/crate/1.2)
* Process Run Crate 0.5 — [w3id.org/ro/wfrun/process/0.5](https://w3id.org/ro/wfrun/process/0.5)
* The validator — [github.com/crs4/rocrate-validator](https://github.com/crs4/rocrate-validator)
* schema.org vocabulary, which supplies `Dataset`, `File`, `Person`, `CreateAction`, `SoftwareApplication`, `DefinedTerm`
* [`document_schema.md`](document_schema.md) — the record being exported and the AMČR seed
* [`paradata_schema.md`](paradata_schema.md) — the run record an action is built from (inputs, outputs, `run_uuid`, `run_agent`)
* [`skos_strategy.md`](skos_strategy.md) — the URI policy behind every `DefinedTerm`
