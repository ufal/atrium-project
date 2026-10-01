# 📦 RO-Crate Export

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

## 🎯 1. The one-paragraph version

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

## 📚 2. RO-Crate from zero

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

## 🤔 3. Why ATRIUM has one

Three reasons, in descending order of how much they bind us:

1. **The pilot needs it.** AMČR stores every archived record as an RO-Crate (RO-Crate 1.2 with
   Process Run Crate 0.5), and every run's paradata as a JSON-LD file with one `CreateAction`
   (grounding report of 2026-09-30, items 1-3; atrium-project#71). Every ATRIUM service returns
   that action for its call, and the record's crate entities are what AMČR's record crate embeds.
2. **The DMP names it.** RO-Crate appears in the WP3 standards column alongside CIDOC CRM, SKOS,
   PeriodO, Getty AAT, TEI, DataCite and IIIF.
3. **The record already promised it.** [`document_schema.md`](document_schema.md) has described
   the document record as "one FAIR, versioned JSON for search and **catalogue export**" since it
   was written, and accretion rule 5 exists so the JSON "stays self-describing for catalogue
   export". This is the consumer.

### What it is *not*, and this matters

The architecture deliberately avoids heavyweight ontological standards — W3C PROV-O, CIDOC-CRM,
JSON-LD — **during raw extraction**, because a 1.2-million-page corpus cannot afford them on the
hot path. `atrium_rocrate.py` does not reverse that decision. A crate is built **after the fact,
over records already on disk**; a service builds one small `CreateAction` from the paradata record
it has already written, once per call. No stage computes anything for it.

---

## 🗺️ 4. The mapping

### 4.1 Field by field

Every property comes from something the record or its paradata already carries. Where a field
does not exist it is **omitted, not guessed** — a crate that asserts a checksum nobody computed is
worse than one that admits the gap. The one exception is a tool's `version`, which RO-Crate 1.2
makes a MUST: without paradata it reads `"unrecorded"`, which states the gap instead of hiding it.

| RO-Crate                     | ATRIUM source                                                                     | Note                                                                                |
|------------------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| root `identifier`            | `doc_id`, as a `PropertyValue` (`#doc_id`)                                        | the form RO-Crate 1.2 recommends                                                    |
| root `name`                  | `doc_id`                                                                          |                                                                                     |
| root `datePublished`         | the record's **newest `assembled.blocks[*].updated_at`**                          | never the clock — see §7.3                                                          |
| root `license`               | `provenance.license_url` / `license`                                              | already the most-restrictive union from `para_licenses.merge_effective_licenses()`  |
| root `conformsTo`            | the Process Run Crate 0.5 `Profile`                                               | the descriptor names RO-Crate 1.2                                                   |
| root `hasPart` → `File`      | `derived_from` values, **and only those**                                         | persistent step outputs; `contentSize` when the files are present (`data_dir`)      |
| root `isBasedOn` → `#source` | `source`                                                                          | contextual, not a part — §4.2; carries the archive's `sha512`, or else `sha256`     |
| root `about` → `DefinedTerm` | every controlled value in the record                                              | `@id` from `atrium_vocab.concept_uri()`                                             |
| root `mentions`              | the `CreateAction`s and the regenerable recipes                                   |                                                                                     |
| `CreateAction`               | one per `provenance.contributors[]` entry                                         | `@id` = its `run_uuid`; a record written before #71 keeps `#run-<program>-<run_id>` |
| `CreativeWork` per block     | one per `assembled.blocks[…]` stamp                                               | §4.3; the action that wrote it lists it as `result`                                 |
| `SoftwareApplication`        | `REPO_URLS` plus, with paradata, `repository` / `tool_version` / `python_version` | `@id` = the release page; `version`; the four ORCID authors as `creator`            |
| `ContainerImage`, `agent`    | paradata `docker_image` (ATRIUM_RUNNER_IMAGE) and `run_agent` (ATRIUM_RUN_AGENT)  | on the action, only when recorded                                                   |

The ATRIUM authors are each **tool's `creator`**, not the root's `author`: the record is the
archive's, the software is theirs (atrium-project#71). ORCIDs are their `@id`s, so no ATRIUM
identifier is minted for a person.

### 4.2 The reference-discipline rule, restated in RO-Crate terms

This is the part where ATRIUM's existing design and RO-Crate's hard rule turn out to be the same
rule. [`document_schema.md`](document_schema.md) says only two classes of reference may appear in
a record — the **original input** and **persistent step outputs** — and that "transient artifacts
are **never** referenced". RO-Crate says everything in `hasPart` must be in the crate. So:

| ATRIUM block   | Becomes                                  | Because                                                                    |
|----------------|------------------------------------------|----------------------------------------------------------------------------|
| `derived_from` | `hasPart` data entities                  | persistent step outputs; the files exist                                   |
| `regenerable`  | contextual entities, **never `hasPart`** | recipes for files that do not exist                                        |
| `source`       | root `isBasedOn`, contextual             | archive-managed; it carries no path *by design*, so it is not in the crate |

A crate that put `regenerable` in `hasPart` would be invalid for exactly the reason the record
forbids storing the derived Markdown: the file is not there. `atrium_rocrate.py`'s `--selftest`
asserts all three of these directly, so the rule cannot rot.

The `#source` entity is honest about its own absence:

```json
{
  "@id": "#source",
  "@type": "CreativeWork",
  "name": "CTX000000001.alto.xml",
  "identifier": "CTX000000001",
  "encodingFormat": "application/alto+xml",
  "sha256": "3b1f0000…",
  "description": "The ORIGINAL input this record was built from, identified by doc_id and its digest. Archive-managed and not part of this crate. Acquired as: ABBYY-ALTO."
}
```

### 4.3 Why each block gets its own entity

`assembled.blocks` is, in the record's own words, "the source of granularity" — re-running one
tool rewrites exactly one entry. A crate that flattened that to a single "produced by the ATRIUM
pipeline" claim would throw away the one thing the accretion design bought. So each stamped block
becomes a small contextual entity, and each run's `CreateAction` lists the blocks it wrote as its
`result`.

**Who wrote a block is answered by the actions, not by the block.** `entities` is a field-split
block: nlp-enrich wrote the entities, llm-enrich later wrote `entities[].pid` into the same rows.
Both runs list `#block-entities` as a `result`, which is the record's `provenance.contributors[]`
said in RO-Crate. The block entity itself carries no `creator`: in RO-Crate `creator` is for people
(the tools' authors), and a stamp names only the most recent writer anyway
([`document_schema.md`](document_schema.md), rule 4). A stamp whose run has no contributor entry —
a record assembled from a hand-built baseline — still gets an action, reconstructed from the stamp.

---

## 🧾 5. One run: the `CreateAction`

### 5.1 What every service returns

Every ATRIUM service returns its run as `paradata`, with every successful response
(atrium-project#71). It is one Process Run Crate `CreateAction`, as nested JSON-LD, built by
`create_action()` from the paradata record the service's logger has just finalized. It is the same
document AMČR stores as the run's paradata file, and it reads:

```json
{
  "@context": ["https://w3id.org/ro/crate/1.2/context", { "…": "the local terms, §10" }],
  "@id": "urn:uuid:5a1e0c1e-1b2d-4c3e-8f40-0a1b2c3d4e5f",
  "@type": "CreateAction",
  "name": "atrium-alto-postprocess run 260724-101112",
  "instrument": {
    "@id": "https://github.com/ufal/atrium-alto-postprocess/releases/tag/v1.6.0-beta",
    "@type": "SoftwareApplication",
    "name": "atrium-alto-postprocess", "version": "1.6.0-beta",
    "url": "https://github.com/ufal/atrium-alto-postprocess",
    "creator": [ { "@id": "https://orcid.org/0009-0002-4773-2797", "@type": "Person", "name": "Kateryna Lutsai" }, "…" ]
  },
  "containerImage": {
    "@id": "#image:ghcr.io/ufal/atrium-alto-postprocess-api:1.6.0-beta",
    "@type": ["ContainerImage", "CreativeWork"],
    "additionalType": { "@id": "https://w3id.org/ro/terms/workflow-run#DockerImage" },
    "registry": "ghcr.io", "name": "ufal/atrium-alto-postprocess-api", "tag": "1.6.0-beta"
  },
  "object": [
    { "@id": "ni:///sha-256;…", "@type": "CreativeWork", "name": "page.alto.xml",
      "encodingFormat": "application/alto+xml", "contentSize": "48213", "sha256": "…" },
    { "@id": "#record", "@type": "CreativeWork", "identifier": "AMCR-F-0042", "name": "AMCR-F-0042.document.json" }
  ],
  "result": [ { "@id": "#block-lines", "@type": "CreativeWork", "recordBlock": "lines" }, "…" ],
  "agent": { "@id": "https://ror.org/…", "@type": "Organization" },
  "startTime": "2026-07-24T10:11:12+00:00",
  "endTime": "2026-07-24T10:11:40+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus",
  "paradataRecord": { "schema_version": "2.0", "program": "alto-postprocess", "run_uuid": "urn:uuid:5a1e…", "…": "…" }
}
```

* **`@id` is the run's `run_uuid`**, the value the call stamped into every block of the record it
  returned. The response, the record and the archived crate name the run the same way.
* **`instrument`** is the tool. Its `@id` is its release page, so it is stable and resolvable; it
  carries `version` (never `softwareVersion`) and its authors as `creator`.
* **`containerImage`** is the image the service runs as (`ATRIUM_RUNNER_IMAGE`, the tag the
  registry carries, atrium-project#69 B3).
* **`object`** is what the call read: the upload, identified by its content (RFC 6920
  `ni:///sha-256;…`, so the output of one stage and the input of the next are one entity), and
  `#record`, the record it was handed — an AMČR seed or the previous stage's record.
* **`result`** is what it wrote: the record's blocks (`#block-<name>`, the entities of §4.3) and
  any output file.
* **`agent`** is the organisation operating the deployment, from `ATRIUM_RUN_AGENT`, an IRI.
  Unset, there is no agent: one is never invented, and it is never the processing account, which
  only reads and calls back (grounding report §8).
* **`startTime` / `endTime`** are UTC, to the second: the profile's pattern refuses Python's
  microseconds. **`actionStatus`** is `CompletedActionStatus`; `FailedActionStatus` with `error`
  exists for a caller that records a failure, but a service returns no action with an error
  body: AMČR records a failed call from the status and reason code.
* **`paradataRecord`** is the whole paradata record as a JSON literal, so nothing it says is lost
  to a schema.org mapping.

`action_problems(action)` is the shared contract check: every repository's contract test and the
E2E run it against a real response.

### 5.2 Where each service returns it

| Service             | Where the action is                                                                                                      | Output file in `result` |
|---------------------|--------------------------------------------------------------------------------------------------------------------------|-------------------------|
| page-classification | `paradata` in `/predict_image` and `/predict_document`                                                                   | `predictions.json`      |
| alto-postprocess    | `paradata` in `/process`                                                                                                 | `cleaned_lines.json`    |
| translator          | `paradata` with `response_format=json`; `paradata.json`, the fourth part of `multipart/mixed`; none in a bare XML answer | the translated XML      |
| nlp-enrich          | `paradata` in `/enrich`, `/enrich_text` and a job's result                                                               | `<doc_id>.teitok.xml`   |
| llm-enrich          | `paradata` in `/extract_keywords` and `/extract_keywords_text`                                                           | `results.json`          |

A JSON output file is the response member of that name, and an XML one the document returned;
each is identified by its content, like the upload. nlp-enrich runs a pipeline of
stages: its `paradataRecord` is the merged pipeline-run record, and its `@id` is the `run_uuid`
the stats stage stamped into the record (the merged run's own when no record was asked for).
alto-postprocess, the one service that reads the source, also records `source.origin` in the
record it returns (`docs/document_schema.md`, The AMČR seed).

### 5.3 Fragments: entities for a crate someone else owns

AMČR's record crate is AMČR's: its root is the archived record, its files are the record's
distributions. What ATRIUM contributes are entities: the runs, the tools and their authors, the
images, the controlled terms, the record's blocks. A **fragment** is exactly that — the entities
with **no metadata descriptor and no root**, so embedding one never creates a second root:

* `document_crate(record, fragment=True)`: the record's entities. No `derived_from` files (the
  host decides which files it holds), and `source_id="…"` points every action's `object` at the
  host's own entity for the original instead of a `#source`.
* `action_fragment(action)`: one service's `CreateAction`, flattened. In a crate the graph is flat,
  so `paradataRecord` travels there as its JSON text.

The host puts the entities in its `@graph`, lists every `CreateAction` in its root's `mentions`
and every `DefinedTerm` in `about`, and declares the Process Run Crate profile on its root.
`wrap_fragment()` does exactly that under a stub root, which is how a fragment is validated (§9)
and a working example for the host.

---

## 🔬 6. A real worked example

Everything below is genuine output from
`python3 atrium_rocrate.py --document fixtures/atrium_document.example.json` — 48 entities. The
example record predates `run_uuid` and comes with no paradata, so its runs keep their legacy ids
and its tools read `"version": "unrecorded"`; pass `--paradata` for each run to get the release ids.

**The descriptor** — the entry point. `about` points at the root; `conformsTo` pins the spec:

```json
{
  "@id": "ro-crate-metadata.json",
  "@type": "CreativeWork",
  "about": { "@id": "./" },
  "conformsTo": { "@id": "https://w3id.org/ro/crate/1.2" }
}
```

**The root**, abridged — note that every value is either a literal or an `@id` pointer:

```json
{
  "@id": "./",
  "@type": "Dataset",
  "identifier": { "@id": "#doc_id" },
  "name": "ATRIUM document record CTX000000001",
  "datePublished": "2026-07-25",
  "schemaVersion": "1.0",
  "conformsTo": { "@id": "https://w3id.org/ro/wfrun/process/0.5" },
  "license":   { "@id": "https://creativecommons.org/licenses/by-nc-sa/4.0/" },
  "isBasedOn": { "@id": "#source" },
  "hasPart":   [ { "@id": "DOC_LINE_CATEG/CTX000000001.csv" },
                 { "@id": "KW_PER_DOC_LLM/CTX000000001_enriched.json" }, … 2 more … ],
  "mentions":  [ { "@id": "#regenerable-markdown" },
                 { "@id": "#run-alto-postprocess-260725-072210" }, … 4 more runs … ],
  "about":     [ { "@id": "https://w3id.org/atrium/cnec/gc" }, … 7 more terms … ]
}
```

**A run**, with its instrument and results:

```json
{
  "@id": "#run-nlp-enrich-260725-074512",
  "@type": "CreateAction",
  "name": "nlp-enrich run 260725-074512",
  "endTime": "2026-07-25T03:54:14+00:00",
  "actionStatus": "http://schema.org/CompletedActionStatus",
  "instrument": { "@id": "https://github.com/ufal/atrium-nlp-enrich" },
  "object":     { "@id": "#source" },
  "result": [ { "@id": "#block-entities" }, { "@id": "#block-lines" },
              { "@id": "#block-pages" },    { "@id": "#block-derived_from" } ],
  "description": "Contributed block(s) entities, lines, pages, derived_from. Run paradata: not recorded."
}
```

**A regenerable recipe** — a contextual entity, deliberately absent from `hasPart`. Its source is
a file of the crate, so it is a reference:

```json
{
  "@id": "#regenerable-markdown",
  "@type": "CreativeWork",
  "name": "markdown",
  "regenerableFrom": { "@id": "TEITOK/CTX000000001.teitok.xml" },
  "regenerableWith": "xml_to_md@0.3.0",
  "description": "DISPOSABLE derivation, recorded as a reproducible recipe rather than a stored path (detail: full). Deliberately absent from hasPart: the file is not in this crate and is not meant to be."
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

## ⚙️ 7. Using it

### 7.1 The functions

**Per-document** — the primitive, one crate per `doc_id`:

```bash
python3 atrium_rocrate.py --document CTX000000001.document.json \
    --paradata paradata/260724-101112_alto-postprocess.json --paradata paradata/260724-101500_nlp-enrich.json \
    --data-dir crates/CTX000000001/ --out-dir crates/CTX000000001/
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
from atrium_rocrate import create_action, document_crate, file_entity, block_entities, write_crate

crate = document_crate(record, paradata=[alto_paradata, nlp_paradata])
write_crate(crate, "crates/CTX000000001/")

action = create_action(
    logger.record, inputs=[file_entity(name, data, media_type=mt)], outputs=block_entities(["pages", "lines"])
)
```

`paradata` is the run records of the runs that wrote the record, matched by `run_uuid` (else by
program and `run_id`); the `{program: record}` map of earlier versions is still accepted. Without
it the crate is still valid — it just says less about *what ran*.

### 7.2 What the folder looks like

A crate is a **directory**, and the metadata file's paths are relative to it. So the data files
must sit where the record says they do:

```
crates/CTX000000001/
├── ro-crate-metadata.json            <- what this module writes
├── DOC_LINE_CATEG/CTX000000001.csv   <- you place these; the module does not move files
├── TEITOK/CTX000000001.teitok.xml
├── TRANSLATED/CTX000000001.alto.xml
└── KW_PER_DOC_LLM/CTX000000001_enriched.json
```

> ⚠️ **`atrium_rocrate.py` writes metadata; it does not copy data.** Assembling the directory is
> the caller's job, and it must use the same relative paths `derived_from` records — otherwise the
> `hasPart` entries point at files that are not there, and the crate is invalid. This is deliberate:
> a module that moved pipeline outputs around would be a second, competing opinion about where
> artifacts live. With `--data-dir` pointing at that directory, each file found there gains its
> `contentSize`.

### 7.3 Determinism, and why it is a feature

Two runs on the same record produce **byte-identical** JSON: `@graph` is sorted by `@id` (with the
descriptor and root pinned first), `json.dumps` runs with `sort_keys=True`, **`datePublished` comes
from the record's own newest block stamp, not from `datetime.now()`**, and a run's `@id` is the
`run_uuid` the record carries — the exporter mints nothing. Re-exporting an archived record in 2031
reproduces the crate it shipped with.

This is not fussiness. The canonical files are drift-gated by byte comparison, and a crate that
changed on every export could not be committed, diffed, or checksummed.

---

## 🚫 8. What a crate cannot yet say

Recorded rather than papered over. None of these blocks a crate; each makes it materially better.

| Gap                                                                                            | Consequence                                                                                | Fix                                                                        |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **No git SHA.** Paradata carries `runner_ref` (a branch or tag), not a commit.                 | Software provenance is "this release", not "this commit".                                  | add a commit SHA to `atrium_paradata`                                      |
| **No output checksums.** `sha256` exists only on `source` and on a service's inputs.           | Every `hasPart` file is named without a hash, so tampering is undetectable from the crate. | add `sha256` alongside each `derived_from` value                           |
| **`derived_from` paths are the tools' own**, sometimes absolute or bare names.                 | A crate over a real record needs its files placed by hand; a fragment leaves them out.     | relative paths in every tool's `derived_from`                              |
| **No DOI or PID anywhere** — not on any `CITATION.cff`, not on any record.                     | The crate has no persistent identifier; `@id` is a local path.                             | out of scope here; needs a repository deposit                              |
| **`forms` has no writer** in any repo, and `entities[].translation_en` is owned-but-unwritten. | Two declared parts of the schema can never appear in a crate.                              | `forms`: see `54.plan.md` §C; `translation_en`: reserved (#70, 2026-09-30) |

---

## ✅ 9. Validating a crate

There are two different checks and it is important not to mistake one for the other.

**`--selftest` is a structural check, run in every repository.** It is a
`para-drift.reusable.yml` step and asserts the things this module is responsible for:

```bash
python3 atrium_rocrate.py --selftest      # exit 0, or 1 with one line per problem
```

It checks the descriptor and the profile; the root's required properties; that **no reference
dangles**; that `regenerable` never reaches `hasPart` and `derived_from` always does; that output
is deterministic and `datePublished` derived from the record; that runs keep their `run_uuid`
ids, tools their release ids, `version` and authors; the fragment and its wrapping; and that a
service's `CreateAction` meets `action_problems()`.

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

## 🧩 10. Design decisions, and what was rejected

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
way to add terms: `regenerableFrom`, `regenerableWith`, `recordBlock`, `sha512` and
`paradataRecord` (a JSON literal) under `https://w3id.org/atrium/`, and the four Workflow Run
terms (`ContainerImage`, `containerImage`, `registry`, `tag`). Declaring those four here rather than
loading the Workflow Run context keeps every crate dependent on exactly one remote document.

**Stable ids.** A run is its `run_uuid` (`urn:uuid:…`), minted by `atrium_paradata` when the run
starts and carried in the record; `run_id` has one-second resolution and two parallel workers can
share one. A tool is its release page, an absolute URL that resolves. An upload is its content
(`ni:` URI). None of them is minted by the exporter.

**`creator` is for people.** The ATRIUM authors are each tool's `creator`. A block is attributed
by the run that wrote it, not by a `creator` naming software.

**`PROCESS_RUN_PROFILE` is pinned and checked.** 0.5 is the profile IRI the validator ships; the
caveat that used to sit on the constant is replaced by the hub's validator job.

---

## 📦 11. Distribution and maintenance

`atrium_rocrate.py` is **hub-canonical**: it lives in `docs/templates/shared/` and is copied
byte-identical into the five tool repos, exactly like `atrium_document.py` and `atrium_vocab.py`.
It sits at each tool repo's root, beside `atrium_vocab.py`, which it imports for concept URIs. A
service imports it from there to build its `CreateAction`.

It is registered once, as a row in [`templates/shared/MANIFEST.json`](templates/shared/MANIFEST.json)
(atrium-project#59). `scripts/revendor_shared.sh`, `para-drift.reusable.yml` (its `diff -u` and its
`--selftest` step) and the `[format] exclude` list of [`templates/ruff.toml`](templates/ruff.toml)
all read that row. Without the exclusion `ruff format` would reflow the vendored copy to the
local `line-length`, and para-drift would go red on the next commit.

**To change the crate's shape**, edit only the hub copy, run `scripts/revendor_shared.sh --check`
then without `--check`, commit the hub edit and the five vendored copies in **one window**, and
only then move `v1`. `para-drift` reads the hub at `hub-ref` (default `v1`), so any other order
turns five repositories red.

**Bumping `ROCRATE_VERSION`** is a compatibility statement about every crate already written,
exactly like `SCHEMA_VERSION` in `atrium_document.py`. `conformsTo` is what a consumer reads to
decide how to interpret the graph. Do not bump it to pick up a new property.

---

## 📖 12. Further reading

* RO-Crate 1.2 specification — [w3id.org/ro/crate/1.2](https://w3id.org/ro/crate/1.2)
* Process Run Crate 0.5 — [w3id.org/ro/wfrun/process/0.5](https://w3id.org/ro/wfrun/process/0.5)
* The validator — [github.com/crs4/rocrate-validator](https://github.com/crs4/rocrate-validator)
* schema.org vocabulary, which supplies `Dataset`, `File`, `Person`, `CreateAction`, `SoftwareApplication`, `DefinedTerm`
* [`document_schema.md`](document_schema.md) — the record being exported, the AMČR seed, and the reference discipline §4.2 rests on
* [`paradata_schema.md`](paradata_schema.md) — the run record an action is built from (`run_uuid`, `run_agent`)
* [`skos_strategy.md`](skos_strategy.md) — the URI policy behind every `DefinedTerm`
