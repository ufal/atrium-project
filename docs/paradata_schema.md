# ATRIUM Paradata Schema & Migration Policy

This document defines the schema versioning policy for the `atrium_paradata.py` run records, and
how ATRIUM tools read records written under an older schema.

A run's paradata describe the run that produced the current version of a distribution (ARÚP's
output contract of 12 November 2026, §6; [atrium-project#84](https://github.com/ufal/atrium-project/issues/84)).
They are the only home of run data: the document record carries none
([`document_schema.md`](document_schema.md)). AMČR stores them as the distribution's RO-Crate
`paradata/<distribution>`, built from this record ([`rocrate_export.md`](rocrate_export.md) §5).

## Schema `3.0`

| Key                                                        | Meaning                                                                                                                       |
|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `program`, `tool_version`, `repository`, `docker_image`, … | the software that ran                                                                                                         |
| `run_id`, `run_uuid`, `run_agent`                          | the run's ids and the operating organisation (below)                                                                          |
| `action_status`                                            | `completed`, or `failed` with `error` (a short message). What AMČR stores is always `completed` (D13)                         |
| `start_time`, `end_time`, `duration_seconds`               | when the run ran                                                                                                              |
| `inputs`, `outputs`                                        | each by AMČR distribution **`name`** and **`sha512`**, with `media_type` and `stored` (below)                                 |
| `parameters`                                               | only what shaped the output: a model revision, a threshold, the forced pages, the translator's field list. Never a path       |
| `limits`                                                   | the sampling and splitting notes (below)                                                                                      |
| `components`                                               | each component used: `name`, `version` when known, and its own `license` or terms, as facts (`para_licenses.component_terms`) |
| `config`, `statistics`, `skipped_files_detail`             | the tool's configuration and counters, as in 2.0; a skipped file is named by its file name only                               |

**No licence** (D2). There is no `license`, `license_url` or `license_detail`, and nothing is
computed or merged: the rights in an output depend on the source document and are stated only by
whoever holds them ([#6](https://github.com/ufal/atrium-project/issues/6)). `components` is a list of
facts, never reduced to one value. `para_licenses` keeps only the spelling of licence ids
(`normalise_license()`, `LICENSE_URL`) and `component_terms()`.

**Inputs and outputs** are the RO-Crate action's `object` and `result`:

```json
"outputs": [
  {"name": "atrium/document-json", "sha512": "9f2c…", "media_type": "application/json", "stored": true,
   "record_fields": {"lines": ["lemma", "upos"], "entities": ["surface", "type_cnec", "char_span"]}}
]
```

* `ParadataLogger.add_input(name, data=None, *, path=None, sha512=None, media_type=None, stored=True)`
  and `add_output(…, record_fields=None)`. Pass the bytes, a `path` to hash (read, never recorded) or
  the `sha512`. Never a local path and never a SHA-256 `ni:` identifier.
* For the record (`atrium/document-json`): an input is the record version read; an output names the
  blocks **and fields** the run wrote, `record_fields` = `DocumentRecord.written()`.
* `stored: false`: an intermediate that is not stored but reaches a stored distribution (D23), such
  as digital-convert's docproc of a mixed document (H14). It is still named by its SHA-512. An
  intermediate that reaches no stored distribution is not recorded.

**Failure and limits** (D13). A failed or incomplete step fails the job, so nothing is written to
AMČR. `ParadataLogger.fail(error)` marks the run failed, and so does leaving its `with` block with an
exception. A limit that **trimmed, skipped or stopped** content is not a note: `note_limit()` and
`note_limits()` raise `ContentLimitError` (reason `limit_exceeded`) and the run fails. Only explicit
**sampling** and **splitting**, where a tool specifies them, are recorded in `limits`:

```json
"limits": [
  {"limit": "lang_id_document_chars", "value": 20000, "effect": "sampled", "count": 1,
   "detail": "language decided on the first 20000 of 58213 characters"}
]
```

| Member   | Meaning                                                                           |
|----------|-----------------------------------------------------------------------------------|
| `limit`  | the limit's `/info` `limits` key (the service's `limits_meta` names the variable) |
| `value`  | the limit's effective value during the run                                        |
| `effect` | `sampled` · `split` (`atrium_limits.RECORDED_EFFECTS`)                            |
| `count`  | how many units (segments, lines, pages, chunks) it applied to                     |
| `detail` | a human-readable sentence; may be empty                                           |

`atrium_limits.EFFECTS` keeps the three failing names so older notes stay readable;
`ParadataLogger.limits_applied` is an alias of `limits`. Notes for the same `limit` and `effect` are
merged (counts add up), and a service echoes them in its response.

**`run_uuid` and `run_agent`** (atrium-project#71). `run_uuid` is `urn:uuid:` and a random UUID,
minted when the logger starts: the run's stable id and the `@id` of its RO-Crate `CreateAction`.
`run_id` has one-second resolution and names the paradata file. `run_agent` is `ATRIUM_RUN_AGENT`,
the IRI (a ROR id, say) of the organisation operating the deployment; `""` when unset. Never a
processing account.

**Service mode.** A service creates its logger with `paradata_dir=None`: nothing is written to the
container's filesystem, `finalize()` returns `""`, `logger.record` is the finalized record, and
`logger.paradata_ref` is the `run_uuid`. The service returns the run as `paradata`, a Process Run
Crate `CreateAction` built from that record (`atrium_rocrate.action_from_paradata`).

**Bash stages** use the CLI shim with a state file: `start`, `component`, `input`, `output`,
`parameter`, `note-limit`, `skip`, `success`, `fail`, `finish`. A step that writes the record reads the run from the
state file (`ParadataLogger.from_state_file(state)`).

**Merging.** `merge_paradata_files` and `merge_run_paradata` carry each stage's `program`,
`run_uuid` and status; `merge_run_paradata` also each stage's inputs and outputs. Components are
united, limits are tagged with the stage's `program`, a failed stage fails the merged record, and a
merged record mints its own `run_uuid`. No licence is merged and no local path is carried.

## Reading older records

`load_paradata()` migrates on read, and a newer MAJOR is refused:

* `1.x` → `2.0` as before;
* `2.x` → `3.0` (`_migrate_2_0_to_3_0()`): `license`, `license_url` and `license_detail` are
  dropped, the components of `license_detail` become `components` (name and licence, as facts),
  `limits_applied` becomes `limits`, and `action_status` is `completed` (a 2.x record was written by
  a run that finished). A 2.x record has no `inputs`/`outputs` by distribution name; nothing invents
  them.

## Versioning Rules

1. **Additive Updates:** adding an optional field or component requires **no bump**. Existing
   parsers ignore unknown keys.
2. **Breaking Changes:** renaming or deleting a field, or changing what one means, bumps
   `SCHEMA_VERSION` to the next major. `3.0` is such a bump (the licence block went).
3. **Migration Mechanics:** a bump mandates a sequential `_migrate_X_to_Y()`, and the tool branches
   on the major.

## Consumers to Update on Bumps

Before releasing a breaking bump, update:

- `merge_paradata_files` and `merge_run_paradata`
- the `_cli()` shim and the bash stages that call it
- `atrium_rocrate.action_from_paradata` and `tools/ci/rocrate_check.py`
- each tool's own paradata writers (re-vendor, then adapt: `scripts/revendor_shared.sh --repo atrium-<tool>`)

## Changelog

- **2026-11-12, `3.0` (atrium-project#84):** no licence fields and no calculated licence;
  `components` as facts; `inputs`/`outputs` by distribution name and SHA-512, with `stored` and
  `record_fields`; `parameters`; `action_status` and `error`; `limits` replaces `limits_applied`
  and holds sampling and splitting only (D13).
- **2026-10-01 (#71):** `run_uuid`, `run_agent`, service mode.
- **2026-09-27 (#53 factor III):** `limits_applied`.
