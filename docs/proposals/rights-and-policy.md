# Proposal: execution evidence, processing policy and output rights

> **Status:** draft for review on [#6](https://github.com/ufal/atrium-project/issues/6), 2026-10-20. Nothing here
> is implemented. It changes what records and crates assert, so it is a class (c) change under
> [`shared_components.md`](../shared_components.md): it needs AMČR's agreement before any shared module changes.
> Draft schema: [`atrium_rights.schema.json`](atrium_rights.schema.json).

## What changes, in one paragraph

Today a run computes one licence for its outputs, the most restrictive of the component licences it used
(`para_licenses.merge_effective_licenses()`), writes it to the paradata and to the record's
`provenance.license` / `license_detail`, and the RO-Crate export states it as the root dataset's licence
(`atrium_rocrate._license_entity()`). That is an inference presented as a rights statement. The proposal records
three things separately: **what a run used** (with each component's own licence or terms, and where that is
documented), **which processing policy allowed it**, and, only when someone with the standing to do so asserts it,
**the rights in an output**. An output with no assertion has unknown rights, and says nothing.

## The three records

### 1. Execution evidence: the components a run used

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

### 2. Processing policy: what a deployment allows

A deployment names a policy file (`ATRIUM_POLICY_PATH`, JSON, owned by the operator, i.e. AMČR for the pilot). Before
a route that the policy covers (an external service, a model with restrictive terms), the tool evaluates it and
records the outcome in the paradata:

```json
{"policy": {"id": "amcr-pilot", "version": "2026-12", "source": "/etc/atrium/policy.json"},
 "decisions": [{"route": "lindat-translation", "components": ["lindat_cubbitt"], "decision": "allowed",
                "rule": "external-services: lindat.mff.cuni.cz permitted"}]}
```

A refused route fails the request with a registered reason (`policy_refused`) rather than falling back silently.
Without a policy file, behaviour is today's, and the paradata records `"policy": null`.

### 3. Output rights: an assertion, not a calculation

An optional `rights` block on a record (and on an exported collection), written only through an explicit call
(`atrium_document.assert_rights()`), never by a processing stage:

| Field         | Meaning                                                                                       |
|---------------|-----------------------------------------------------------------------------------------------|
| `statement`   | an SPDX expression, a rights URI (e.g. a RightsStatements.org URI) or a short text            |
| `asserted_by` | the agent making the assertion (an IRI, e.g. the institution's ROR)                           |
| `basis`       | what it rests on: the source's rights, the policy id, an agreement                            |
| `scope`       | which outputs it covers: the record, a block, a derived file                                  |
| `date`        | when it was asserted                                                                          |

No tool fills it from component licences. An unknown status stays unknown.

## RO-Crate 1.2 and Process Run Crate 0.5

- Each component becomes a contextual entity (`SoftwareApplication`, `Dataset`, `DefinedTermSet` or `WebAPI`) with
  **its own** `license` and `version`, listed as the `CreateAction`'s `instrument`, as Process Run Crate expects.
- The policy and its decisions are a `CreativeWork` linked from the action, with each decision as a
  `PropertyValue`.
- **The root dataset's `license` is written only from a rights assertion.** Without one it is left out, and the
  crate's description says that rights are not established. RO-Crate recommends a root licence; leaving it out is
  accurate, writing the calculated one is not.
- For a collection of derived files, `atrium_rocrate` can also write a `REUSE.toml`, generated from the rights
  assertions of those files, never from component licences.

## Migration

| Today                                | During the transition (schema 1.x, additive)                                                           | At schema 2.0                                                   |
|--------------------------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `provenance.license`, `license_url`  | still written, with `provenance.license_basis: "calculated"`; described in the schema as a calculation | moved by `_migrate_1_to_2()` to `provenance.calculated_license` |
| `provenance.license_detail`          | as above                                                                                               | moved with it                                                   |
| paradata `license`, `license_detail` | kept, marked calculated; `components_used` and `policy` added                                          | `license*` dropped from new paradata                            |
| crate root `license`                 | **stops** (a separate, early change, since it is the one false assertion in an export)                 | from `rights` only                                              |
| `para_config.txt [components]`       | `components.json` beside it, generated once from it and then edited                                    | `[components]` removed                                          |

Historical paradata and records stay as written; reading them, a consumer sees a calculated value labelled as such.

## Order of work, once agreed

1. Agree the schema (this page and the draft), including the questions below.
2. Inventories: `components.json` and `REUSE.toml` in the six repositories, with evidence for each licence.
3. Shared modules: `atrium_paradata` records `components_used` and `policy`; `atrium_rocrate` emits component
   entities and drops the calculated root licence; `atrium_document` gains `rights` and `assert_rights()`.
4. A small `atrium_policy.py`: load, evaluate, record; called before the external routes (translator and nlp-enrich
   to LINDAT, keyword-extract to its LLM backend).
5. Tests in every repository, the E2E lanes, and AMČR's sign-off on the change's issue.

## Questions

1. **Who asserts output rights** in records AMČR publishes: AMČR only (recommended), or may a deployment set a
   default assertion?
2. **The crate root without an assertion:** leave `license` out (recommended), or state a rights URI for "not
   evaluated"?
3. **The policy file:** written by AMČR per deployment, with ÚFAL shipping an example and the evaluation code?
