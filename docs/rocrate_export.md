# 📦 RO-Crate Export

This document explains **what RO-Crate is** (assuming you have never seen one), **why ATRIUM has
one**, and **how to use `atrium_rocrate.py`**. It is the companion to
[`document_schema.md`](document_schema.md), which defines the record this exports, and to
[`skos_strategy.md`](skos_strategy.md), which defines the vocabulary URIs it references.

Template file: [`templates/shared/atrium_rocrate.py`](templates/shared/atrium_rocrate.py).
Design discussion: [ufal/atrium-project#54](https://github.com/ufal/atrium-project/issues/54).

---

## 🎯 1. The one-paragraph version

An **RO-Crate** ("Research Object Crate") is a folder of files plus a single metadata file at its
root called `ro-crate-metadata.json`. That file says, in a machine-readable way: *what this folder
is, which files are in it, who made them, under what licence, and with which software*. It is a
community convention, not a piece of software — you do not install RO-Crate, you **write one
JSON file to a convention**, and any tool that knows the convention can read your folder.

`atrium_rocrate.py` writes that file from an `atrium_document` record. Nothing else changes: no
pipeline behaviour, no new dependency, no upload anywhere.

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
  "@context": "https://w3id.org/ro/crate/1.1/context",
  "@graph": [ … every entity, as a flat list … ]
}
```

* **`@context`** — where the property names come from. `name`, `author`, `license` are not ours;
  they are [schema.org](https://schema.org) terms, and the context is what says so. It is a URL,
  it is fixed by the spec version, and you do not invent it.
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
> resolvable URL). A crate that lists a file it does not contain is invalid. This turns out to
> matter enormously for ATRIUM — see §4.2.

### 2.3 A minimal crate, in full

```json
{
  "@context": "https://w3id.org/ro/crate/1.1/context",
  "@graph": [
    {
      "@id": "ro-crate-metadata.json",
      "@type": "CreativeWork",
      "conformsTo": { "@id": "https://w3id.org/ro/crate/1.1" },
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

| Term                                 | Meaning here                                                                                                                                                                               |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Profile**                          | A named extra set of expectations layered on the base spec. We declare the *Process Run Crate* profile on run crates, because they make provenance claims the base spec does not describe. |
| **`conformsTo`**                     | Which spec version and profiles a crate follows.                                                                                                                                           |
| **`CreateAction`**                   | schema.org's "something was made". We use one per contributing tool run.                                                                                                                   |
| **`SoftwareApplication`**            | A program. We use one per ATRIUM tool.                                                                                                                                                     |
| **`DefinedTerm` / `DefinedTermSet`** | A controlled-vocabulary term and its scheme. Ours resolve into the SKOS registry — see [`skos_strategy.md`](skos_strategy.md).                                                             |
| **Detached crate**                   | A metadata file describing things not physically present. Ours are *not* detached — but our `source` entity is, deliberately (§4.2).                                                       |

---

## 🤔 3. Why ATRIUM has one

Three reasons, in descending order of how much they bind us:

1. **The DMP names it.** RO-Crate appears in the WP3 standards column alongside CIDOC CRM, SKOS,
   PeriodO, Getty AAT, TEI, DataCite and IIIF. Until #54 there were zero occurrences of the string
   in any of the six repositories — a commitment with no implementation.
2. **The record already promised it.** [`document_schema.md`](document_schema.md) has described
   the document record as "one FAIR, versioned JSON for search and **catalogue export**" since it
   was written, and accretion rule 5 exists so the JSON "stays self-describing for catalogue
   export". Nothing consumed that. This is the consumer.
3. **It is the cheapest FAIR win available.** Findable/Accessible/Interoperable/Reusable mostly
   asks for metadata that already exists to be written down in an agreed shape. We have the
   metadata. This writes it down.

### What it is *not*, and this matters

The architecture deliberately avoids heavyweight ontological standards — W3C PROV-O, CIDOC-CRM,
JSON-LD — **during raw extraction**, because a 1.2-million-page corpus cannot afford them on the
hot path. `atrium_rocrate.py` does not reverse that decision. It runs **once, after the fact,
over records already on disk**, and adds nothing to any pipeline stage. No tool imports it in
order to produce output; it is a reader.

---

## 🗺️ 4. The mapping

### 4.1 Field by field

Every property comes from something the record or its paradata already carries. Where a field
does not exist it is **omitted, not guessed** — a crate that asserts a checksum nobody computed is
worse than one that admits the gap.

| RO-Crate                     | ATRIUM source                                                                                                                 | Note                                                                               |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| root `identifier`, `name`    | `doc_id`                                                                                                                      |                                                                                    |
| root `datePublished`         | the record's **newest `assembled.blocks[*].updated_at`**                                                                      | never the clock — see §6.2                                                         |
| root `license`               | `provenance.license_url` / `license`                                                                                          | already the most-restrictive union from `para_licenses.merge_effective_licenses()` |
| root `author`                | the four ORCID authors in every `CITATION.cff`                                                                                | ORCIDs are the `@id`s, so no ATRIUM identifier is minted for a person              |
| root `hasPart` → `File`      | `derived_from` values, **and only those**                                                                                     | persistent step outputs                                                            |
| root `isBasedOn` → `#source` | `source`                                                                                                                      | contextual, not a part — §4.2                                                      |
| root `about` → `DefinedTerm` | every controlled value in the record                                                                                          | `@id` from `atrium_vocab.concept_uri()`                                            |
| root `mentions`              | the `CreateAction`s and the regenerable recipes                                                                               |                                                                                    |
| `CreateAction`               | one per `provenance.contributors[]` entry                                                                                     | `program`, `run_id`, `blocks`, `at`, `paradata_ref`                                |
| `CreativeWork` per block     | one per `assembled.blocks[…]` stamp                                                                                           | §4.3                                                                               |
| `SoftwareApplication`        | `REPO_URLS` plus, when paradata is supplied, `tool_version` / `repository` / `docker_image` / `runner_ref` / `python_version` |                                                                                    |

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
  "description": "The ORIGINAL input this record was built from, identified by doc_id + sha256. Archive-managed and not part of this crate. Acquired as: ABBYY-ALTO."
}
```

### 4.3 Why each block gets its own entity

`assembled.blocks` is, in the record's own words, "the source of granularity" — re-running one
tool rewrites exactly one entry. A crate that flattened that to a single "produced by the ATRIUM
pipeline" claim would throw away the one thing the accretion design bought. So each stamped block
becomes a small contextual entity, and each run's `CreateAction` lists the blocks it wrote as its
`result`.

**This reproduces the field-split subtlety exactly, which is worth understanding before it
confuses you.** In the worked example below, `#block-entities` has
`"creator": {"@id": "#tool-llm-enrich"}` — but it appears in the `result` of the **nlp-enrich**
run. Both are correct. `entities` is a field-split block: nlp-enrich wrote the entities,
llm-enrich later wrote `entities[].pid` into the same rows, and the stamp names the **most recent**
writer (`document_schema.md`, rule 4). The full picture lives in `provenance.contributors[]`,
which is what the `CreateAction`s are built from. The crate says the same thing the record says,
including the parts that need a footnote.

---

## 🔬 5. A real worked example

Everything below is genuine output from
`python3 atrium_rocrate.py --document fixtures/atrium_document.example.json` — 46 entities.

**The descriptor** — the entry point. `about` points at the root; `conformsTo` pins the spec:

```json
{
  "@id": "ro-crate-metadata.json",
  "@type": "CreativeWork",
  "about": { "@id": "./" },
  "conformsTo": { "@id": "https://w3id.org/ro/crate/1.1" }
}
```

**The root**, abridged — note that every value is either a literal or an `@id` pointer:

```json
{
  "@id": "./",
  "@type": "Dataset",
  "identifier": "CTX000000001",
  "name": "ATRIUM document record CTX000000001",
  "datePublished": "2026-07-25",
  "schemaVersion": "1.0",
  "license":   { "@id": "https://creativecommons.org/licenses/by-nc-sa/4.0/" },
  "isBasedOn": { "@id": "#source" },
  "author":    [ { "@id": "https://orcid.org/0009-0002-4773-2797" }, … 3 more … ],
  "hasPart":   [ { "@id": "DOC_LINE_CATEG/CTX000000001.csv" },
                 { "@id": "KW_PER_DOC_LLM/CTX000000001_enriched.json" },
                 { "@id": "TEITOK/CTX000000001.teitok.xml" },
                 { "@id": "TRANSLATED/CTX000000001.alto.xml" } ],
  "mentions":  [ { "@id": "#regenerable-markdown" },
                 { "@id": "#run-alto-postprocess-260725-072210" }, … 4 more runs … ],
  "about":     [ { "@id": "https://w3id.org/atrium/entity-type/LOC" }, … 7 more terms … ]
}
```

**A run**, with its instrument and results:

```json
{
  "@id": "#run-nlp-enrich-260725-074512",
  "@type": "CreateAction",
  "name": "nlp-enrich run 260725-074512",
  "startTime": "2026-07-25T03:54:14.027772+00:00",
  "instrument": { "@id": "#tool-nlp-enrich" },
  "object":     { "@id": "#source" },
  "result": [ { "@id": "#block-entities" }, { "@id": "#block-lines" },
              { "@id": "#block-pages" },    { "@id": "#block-derived_from" } ],
  "description": "Contributed block(s) entities, lines, pages, derived_from. Run paradata: not recorded."
}
```

**A regenerable recipe** — a contextual entity, deliberately absent from `hasPart`:

```json
{
  "@id": "#regenerable-markdown",
  "@type": "CreativeWork",
  "name": "markdown",
  "regenerableFrom": "TEITOK/CTX000000001.teitok.xml",
  "softwareVersion": "xml_to_md@0.3.0",
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

> 🐞 **The example fixture currently produces four terms that resolve to nothing** —
> `page-category/Text`, `page-category/Plate`, `line-category/Text` and `theme/kostel` are not in
> the registry. That is defect **V-4** from [`skos_strategy.md`](skos_strategy.md) §6 in its second
> home: that pass corrected the schema's `examples` and left `fixtures/atrium_document.example.json`
> alone. Minting a URI per term is what made it visible. Fix the fixture; do **not** add an `enum`
> to the schema (see the 2026-09-08 changelog entry for why).

---

## ⚙️ 6. Using it

### 6.1 Two crates, one function each

**Per-document** — the primitive, one crate per `doc_id`:

```bash
python3 atrium_rocrate.py --document CTX000000001.document.json --out-dir crates/CTX000000001/
# -> crates/CTX000000001/ro-crate-metadata.json
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
from atrium_rocrate import document_crate, run_crate, write_crate

crate = document_crate(record, paradata={"nlp-enrich": nlp_paradata})
write_crate(crate, "crates/CTX000000001/")
```

`paradata` is an optional `{program: paradata_record}` map. Without it the crate is still valid —
it just says less about *what ran*: each `SoftwareApplication` falls back to a name and a
repository URL, with no version or image digest.

### 6.2 What the folder looks like

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
> artifacts live.

### 6.3 Determinism, and why it is a feature

Two runs on the same record produce **byte-identical** JSON: `@graph` is sorted by `@id` (with the
descriptor and root pinned first), `json.dumps` runs with `sort_keys=True`, and — the part that is
easy to get wrong — **`datePublished` comes from the record's own newest block stamp, not from
`datetime.now()`**. Re-exporting an archived record in 2031 reproduces the crate it shipped with.

This is not fussiness. The canonical files are drift-gated by byte comparison, and a crate that
changed on every export could not be committed, diffed, or checksummed.

---

## 🚫 7. What a crate cannot yet say

Recorded rather than papered over. None of these blocks a first crate; each makes it materially
better.

| Gap                                                                                            | Consequence                                                                                | Fix                                              |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|--------------------------------------------------|
| **No git SHA.** Paradata carries `runner_ref` (a branch or tag), not a commit.                 | Software provenance is "this ref", not "this commit".                                      | add a commit SHA to `atrium_paradata`            |
| **No output checksums.** `sha256` exists only on `source`.                                     | Every `hasPart` file is named without a hash, so tampering is undetectable from the crate. | add `sha256` alongside each `derived_from` value |
| **No DOI or PID anywhere** — not on any `CITATION.cff`, not on any record.                     | The crate has no persistent identifier; `@id` is a local path.                             | out of scope here; needs a repository deposit    |
| **`atrium-project` has no `CITATION.cff`** though all five tool repos do.                      | Author metadata is hardcoded in `AUTHORS` rather than read from the hub.                   | add one                                          |
| **`forms` has no writer** in any repo, and `entities[].translation_en` is owned-but-unwritten. | Two declared parts of the schema can never appear in a crate.                              | product decision — see `54.plan.md` §C           |

---

## ✅ 8. Validating a crate

There are two different checks and it is important not to mistake one for the other.

**`--selftest` is a structural check, not a conformance claim.** It runs in CI (it is a
`para-drift.reusable.yml` step) and asserts the things this module is responsible for:

```bash
python3 atrium_rocrate.py --selftest      # exit 0, or 1 with one line per problem
```

It checks that the descriptor is first and points at the root; that the root carries the four
required properties and is a `Dataset`; that **no reference dangles** (every `{"@id": …}` either
names an entity in the graph or is an absolute URI); that `regenerable` never reaches `hasPart`
and `derived_from` always does; that output is deterministic; that `datePublished` is a bare date
derived from the record; and that block/run/tool entities survive.

**Spec conformance is an external check, run out of band.** Use the RO-Crate community validator
or the online playground once, on a real crate, and record the result — the plan's done-criteria
asks for exactly that. Do **not** add a validator dependency to the repos to get it; see §9.

---

## 🧩 9. Design decisions, and what was rejected

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

**Both crate kinds, not one.** A per-document crate matches the record's own granularity and is
the natural unit for catalogue export. A run crate matches the DMP's provenance framing. Making
the run crate *reference* the document crates rather than inline them is what keeps it viable at
corpus scale.

**`@context` is an array.** RO-Crate's own context plus a small local map declaring the three
extension terms we emit (`regenerableFrom`, `recordBlock`, `schemaVersion`) under
`https://w3id.org/atrium/`. This is the spec-sanctioned way to add terms; the alternative — emitting
undeclared properties — leaves them to be silently dropped by a strict consumer.

**`PROCESS_RUN_PROFILE` is pinned but must be verified before first publication.** The
Workflow-Run RO-Crate profiles are versioned independently of the RO-Crate spec, and ATRIUM's five
containers driven by CI are a *process* run, not a workflow run in the CWL/WDL sense. The constant
carries this warning in the source too.

---

## 📦 10. Distribution and maintenance

`atrium_rocrate.py` is **hub-canonical**: it lives in `docs/templates/shared/` and is copied
byte-identical into the five tool repos, exactly like `atrium_document.py` and `atrium_vocab.py`.
It sits at each tool repo's root, beside `atrium_vocab.py`, which it imports for concept URIs.

Three registrations keep it enforced, and missing any one is silent:

1. a row in `SHARED_FILES` in [`../scripts/revendor_shared.sh`](../scripts/revendor_shared.sh);
2. a `diff -u` step **and a `--selftest` step** in `para-drift.reusable.yml`;
3. a row in the `[format] exclude` list of [`templates/ruff.toml`](templates/ruff.toml) — without
   it `ruff format` reflows the vendored copy to the local `line-length` (120 in three repos, 100
   in two) and para-drift goes red on the next commit.

`revendor_shared.sh` now runs the `--selftest`s itself after copying, so a clean run there still
means "para-drift would pass" — byte-parity alone would not catch a module that is identical
everywhere and broken everywhere.

**To change the crate's shape**, edit only the hub copy, run `scripts/revendor_shared.sh --check`
then without `--check`, commit the hub edit and the five vendored copies in **one window**, and
only then move `v1`. `para-drift` reads the hub at `hub-ref` (default `v1`), so any other order
turns five repositories red.

**Bumping `ROCRATE_VERSION`** is a compatibility statement about every crate already written,
exactly like `SCHEMA_VERSION` in `atrium_document.py`. `conformsTo` is what a consumer reads to
decide how to interpret the graph. Do not bump it to pick up a new property.

---

## 📖 11. Further reading

* RO-Crate specification and the community validator — [researchobject.org/ro-crate](https://www.researchobject.org/ro-crate/)
* schema.org vocabulary, which supplies `Dataset`, `File`, `Person`, `CreateAction`, `SoftwareApplication`, `DefinedTerm`
* [`document_schema.md`](document_schema.md) — the record being exported, and the reference discipline §4.2 rests on
* [`skos_strategy.md`](skos_strategy.md) — the URI policy behind every `DefinedTerm`
* [`paradata_schema.md`](paradata_schema.md) — the run record supplying `SoftwareApplication` detail
