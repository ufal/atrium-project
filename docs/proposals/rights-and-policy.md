# Proposal: execution evidence, processing policy and output rights

> **Status:** draft on [#6](https://github.com/ufal/atrium-project/issues/6), 2026-10-20; the approach approved by
> AMČR (motyc) on 2026-10-22, with three adjustments made here: `scope` and `basis` are mandatory, the per-document
> policy is described, and the document schema's migration is kept apart from paradata versioning. Nothing here is
> implemented yet. It is a class (c) change under [`shared_components.md`](../shared_components.md). Draft schema:
> [`atrium_rights.schema.json`](atrium_rights.schema.json).

## In plain words

**Today.** Every run lists the components it used (models, datasets, vocabularies, web services), each with its
licence. From that list it also computes one label, the most restrictive of those licences
(`para_licenses.merge_effective_licenses()`). The label is written into the run's paradata, into the record as
`provenance.license`, and into an RO-Crate export as the crate's licence (`atrium_rocrate._license_entity()`).

**The problem.** That label reads as the licence of the output, and it is not one. A tool's or a model's licence
does not become the licence of what it produces. Web services such as LINDAT's offer terms of use, not a licence
for their output. "The strictest wins" does not settle whether licences can be combined. And the rights in an
output depend first on the rights in the source document, which no tool knows. (motyc and Pavel on
[#4](https://github.com/ufal/atrium-project/issues/4) and [#6](https://github.com/ufal/atrium-project/issues/6),
October 2026.)

**The proposal.** Three separate records instead of one label:
1. **What a run used:** each component with its own licence or terms of use, and where that was read.
2. **Which policy allowed it:** a policy written by the deployment's operator (AMČR for the pilot), together with
   each document's own permission, checked before a run sends anything to an external service or uses a model
   with restrictive terms. A document without that permission is not sent out.
3. **The rights in an output, only when asserted:** written only when someone entitled to do so states them.
   Without that, the rights are unknown and the record says nothing.

**What changes for a user.** Records and crates stop stating a licence that nobody granted. They still say
exactly what was used and under which terms. A deployment can refuse a route its policy forbids, instead of
finding out afterwards. Old records keep their values, marked as calculated.

A short explanation for readers outside the project is on the documentation site:
[Licences and paradata](https://ufal.github.io/atrium-project/ecosystem/licences/).

## What AMČR decided (2026-10-22)

1. **Who asserts output rights:** AMČR, for the outputs it publishes, on the basis of the source's rights and
   permissions. No processing tool makes an automatic or default licence assertion.
2. **The crate root without an assertion:** leave `license` out. Still open: RO-Crate 1.2 makes the root's
   `license` a MUST (and allows a text there), so a standalone crate without it fails the validator. Two ways
   to meet both, put to motyc on #6: (a) the root's `license` names a contextual entity `#no-licence-asserted`
   ("No licence asserted"; its description says the rights depend on the source and on AMČR's permission),
   which asserts nothing and keeps the crate valid; (b) leave it out and accept the validator's error for
   standalone crates. Until he answers, `atrium_rocrate` keeps writing the calculated label. A fragment,
   which AMČR embeds under its own root, is not affected.
3. **The policy:** AMČR defines it; ÚFAL provides the schema, the reference implementation and examples. External
   processing is also allowed or refused **per document** (aiscr-webamcr#2590), and a missing authorisation
   refuses it.

The correction of the misleading output-licence assertions comes first, and historical evidence is kept. The
inventories (`components.json`, REUSE) follow and do not hold it up.

## For implementers

The rest of this page is the detailed design: the fields of each record, the RO-Crate mapping, the migration and
the order of work.

### The three records

#### 1. Execution evidence: the components a run used

One entry per component actually exercised, in the run's paradata (`components_used`), referenced from the
record by the run's `run_uuid`:

| Field       | Meaning                                                                                        |
|-------------|------------------------------------------------------------------------------------------------|
| `id`        | stable id within the tool's inventory, e.g. `lindat_cubbitt`, `fasttext_lid`                   |
| `kind`      | `software`, `model`, `dataset`, `vocabulary` or `service`                                      |
| `name`      | human-readable name                                                                            |
| `version`   | release, model revision, image digest or API version; `null` when the provider publishes none  |
| `licence`   | an SPDX expression (`Apache-2.0`, `CC-BY-NC-4.0`), a `LicenseRef-*`, or `null`                 |
| `terms_url` | for services and models with terms instead of a licence: the terms in force                    |
| `evidence`  | where the licence or terms were read: model card, LICENSE file, terms page, with the date read |

The source is a per-repository inventory, `components.json`, replacing the `[components]` section of
`para_config.txt` (which keeps `[tool]`). Files inside a repository (code, vendored code, sample data) are declared
the REUSE way, in a `REUSE.toml` and SPDX headers; `components.json` covers what is outside it: dependencies,
models, data and services.

#### 2. Processing policy: what a deployment allows

A deployment names a policy file (`ATRIUM_POLICY_PATH`, JSON, owned by the operator, i.e. AMČR for the pilot). Before
a route that the policy covers (an external service, a model with restrictive terms), the tool evaluates it and
records the outcome in the paradata:

```json
{"policy": {"id": "amcr-pilot", "version": "2026-12", "source": "/etc/atrium/policy.json"},
 "decisions": [{"route": "lindat-translation", "components": ["lindat_cubbitt"], "decision": "allowed",
                "rule": "external-services: lindat.mff.cuni.cz permitted"}]}
```

A refused route fails the request with a registered reason (`policy_refused`) rather than falling back silently.

**Per document.** The deployment's policy says which routes may be used at all; each document's permission says
whether this document may leave AMČR for them (aiscr-webamcr#2590). AMČR's pipeline passes the permission with
the request, as a `processing_permission` object, the same in the services and in the batch tools (a
`<doc_id>.permission.json` next to the input):

```json
{"doc_id": "C-202000543A", "external_processing": "allowed", "basis": "amcr:permission/2026-117",
 "decided_by": "https://ror.org/<AMČR's ROR>", "date": "2026-11-20"}
```

A route is used only when both allow it. An external route for a document whose permission is missing, or says
`refused`, fails with `policy_refused` (cause `no_document_authorisation` or `document_refused`); processing
inside the image is not external and goes on. The decision is recorded per document, with the permission's
`basis`. A deployment that sets `ATRIUM_POLICY_PATH` enforces both; without a policy file (development, research
runs) the tools behave as today and the paradata records `"policy": null`, so such a record is never mistaken for
one from AMČR's deployment.

#### 3. Output rights: an assertion, not a calculation

An optional `rights` list on a record (and on an exported collection), written only through an explicit call
(`atrium_document.assert_rights()`), never by a processing stage. Every field is mandatory: an assertion without
its `scope` or its `basis` is refused.

| Field         | Meaning                                                                            |
|---------------|------------------------------------------------------------------------------------|
| `statement`   | an SPDX expression, a rights URI (e.g. a RightsStatements.org URI) or a short text |
| `asserted_by` | the agent making the assertion (an IRI, e.g. the institution's ROR)                |
| `basis`       | what it rests on: the source's rights, the policy id, an agreement                 |
| `scope`       | which outputs it covers: the record, a block, a derived file                       |
| `date`        | when it was asserted                                                               |

No tool fills it from component licences. An unknown status stays unknown.

### RO-Crate 1.2 and Process Run Crate 0.5

- Each component becomes a contextual entity (`SoftwareApplication`, `Dataset`, `DefinedTermSet` or `WebAPI`) with
  **its own** `license` and `version`, listed as the `CreateAction`'s `instrument`, as Process Run Crate expects.
- The policy and its decisions are a `CreativeWork` linked from the action, with each decision as a
  `PropertyValue`.
- **The root dataset's `license` is written only from a rights assertion** whose `scope` is the record (or the
  run, for a run crate). Without one it is left out, and the crate's description says that rights are not
  established. RO-Crate 1.2 requires a root licence, so a standalone crate without it fails the validator; how to
  meet both is the open point on #6, with the two options under "What AMČR decided" (a fragment is not affected).
- For a collection of derived files, `atrium_rocrate` can also write a `REUSE.toml`, generated from the rights
  assertions of those files, never from component licences.

### Migration

The document record and the paradata are versioned apart, and each keeps its own rules: the record's schema is
1.0 (`atrium_document.SCHEMA_VERSION`, `migrate_document()`), the paradata's 2.0 (`atrium_paradata.SCHEMA_VERSION`,
`docs/paradata_schema.md`).

**The document record, schema 1.x → 2.0.**

| Today                               | During the transition (1.x, additive)                                                                  | At 2.0                                                              |
|-------------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| `provenance.license`, `license_url` | still written, with `provenance.license_basis: "calculated"`; described in the schema as a calculation | moved by `_migrate_1_0_to_2_0()` to `provenance.calculated_license` |
| `provenance.license_detail`         | as above                                                                                               | moved with it                                                       |
| no `rights`                         | `rights`, optional, written only by `assert_rights()`                                                  | unchanged                                                           |
| crate root `license`                | **stops** (a separate, early change, since it is the one false assertion in an export)                 | from `rights` only                                                  |

**The paradata, 2.x → 3.0.** Adding `components_used` and `policy` is an optional addition within 2.x. Dropping
`license*` changes what a field means, so by `docs/paradata_schema.md` it is 3.0:

| Today                       | During the transition (2.x, additive)                               | At 3.0                       |
|-----------------------------|---------------------------------------------------------------------|------------------------------|
| `license`, `license_detail` | kept, described as calculated; `components_used` and `policy` added | `license*` no longer written |

**The inventory.** `para_config.txt [components]` gets `components.json` beside it, generated once from it and
then edited; `[components]` is removed when every tool reads `components.json`.

Historical paradata and records stay as written: nothing rewrites a file on disk. Reading them, a consumer sees a
calculated value labelled as such (`migrate_document()` in memory for a record; the version for paradata).

### Order of work, once agreed

1. **The correction first:** the schema and the docs describe `provenance.license` and the paradata `license` as
   calculated from the components, not as the output's licence (done 2026-10-25: the record schema's
   descriptions, `document_schema.md`, `paradata_schema.md`, `rocrate_export.md` and the site pages); the crate root stops carrying it (once the
   RO-Crate point above is settled); historical files untouched.
2. Shared modules: `atrium_document` gains `rights` and `assert_rights()` (with `scope` and `basis` required);
   `atrium_rocrate` writes the root licence from `rights` only and emits component entities.
3. A small `atrium_policy.py`: load the deployment policy and the document's permission, evaluate, record; called
   before the external routes (translator and nlp-enrich to LINDAT, keyword-extract to its LLM backend).
4. Inventories: `components.json` and `REUSE.toml` in the six repositories, with evidence for each licence. They do
   not block 1-3.
5. Tests in every repository, the E2E lanes, and AMČR's sign-off on the change's issue.
