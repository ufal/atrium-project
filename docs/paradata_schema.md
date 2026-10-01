# 🗃️ ATRIUM Paradata Schema & Migration Policy

This document defines the schema versioning policy for the `atrium_paradata.py` provenance JSONs, handling how ATRIUM tools interact with historical logs when architectures change.

## Schema `2.0` Context
- **Contract:** Establishes fixed `provenance`, `license`, `timing`, `config`, and `statistics` blocks along with `record_type` for multi-stage pipelines.
- **Old Log Validity:** Pre-`2.0` (or unversioned `1.0` logs) remain completely valid. Tools load historical logs using the transparent migrator built into `atrium_paradata.py` (`load_paradata()` automatically upconverts them).

## Versioning Rules
1. **Additive Updates:** Adding an optional field or component requires **no bump**. Existing parsers will ignore the unknown keys seamlessly.
2. **Breaking Changes:** If a field is renamed, deleted, or fundamentally alters semantic calculation, the `SCHEMA_VERSION` will be explicitly bumped to the next major component (e.g. `3.0`).
3. **Migration Mechanics:** A schema bump mandates the inclusion of a sequential migration script (`_migrate_X_to_Y()`). The tool will branch logic depending on the major iteration.

## Consumers to Update on Bumps
If a schema bump is required, downstream aggregators relying on hard-key lookups must be updated manually. Before releasing a breaking bump, update:
- Both `merge_paradata_files` and `merge_run_paradata`
- `_cli()` bash shim parser dependencies
- `alto`'s `run_pipeline.py` which drives the stage aggregation
- Compose network orchestration logic

## Optional fields added within `2.0`

### `limits_applied` (2026-09-27, atrium-project#53 factor III)
Every limit that **shaped** the run's result without refusing it. A limit that refused the
input is not here: the service answered with `reason: "limit_exceeded"` instead (hub
`docs/agent_skill_strategy.md` §4.4). Additive under rule 1 above — no bump; a record
without the key means "not recorded", which is what every record before this date is.

```json
"limits_applied": [
  {"limit": "lang_id_document_chars", "value": 20000, "effect": "sampled", "count": 1,
   "detail": "language decided on the first 20000 of 58213 characters"}
]
```

| Member   | Meaning                                                                                                      |
|----------|--------------------------------------------------------------------------------------------------------------|
| `limit`  | the limit's `/info` `limits` key (the service's `limits_meta` names the variable)                            |
| `value`  | the limit's effective value during the run                                                                   |
| `effect` | `sampled` · `split` · `trimmed` · `skipped` · `stopped` — published, never renamed (`atrium_limits.EFFECTS`) |
| `count`  | how many units (segments, lines, pages, chunks, terms) it applied to                                         |
| `detail` | a human-readable sentence; may be empty                                                                      |

- `ParadataLogger.finalize()` always writes the key (`[]` when nothing applied). Notes are added
  with `ParadataLogger.note_limit(limit, value, effect, count, detail)` or `note_limits(notes)`
  (an `atrium_limits.LimitNotes`), and from a bash stage with
  `python atrium_paradata.py note-limit --state … --limit … --value … --effect … --count …`.
  Notes for the same `limit` and `effect` are merged (counts add up).
- `merge_paradata_files` and `merge_run_paradata` carry every stage's notes into the merged
  record's `limits_applied`, each tagged with the stage's `program`.
- Every service response also echoes the same list (`limits_applied` in JSON, the
  `X-Atrium-Limits-Applied` header otherwise), next to the run's `paradata` (below).

### `run_uuid` and `run_agent`, and the service mode (2026-10-01, atrium-project#71)
Two more optional fields, so no bump either. A record written before this date has neither.

| Field       | Meaning                                                                                                                                                                                                             |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `run_uuid`  | the run's stable id, `urn:uuid:` and a random UUID, minted when the logger starts. `run_id` has one-second resolution, so two workers started together share one; they never share a `run_uuid`                     |
| `run_agent` | `ATRIUM_RUN_AGENT`: the IRI (a ROR id, say) of the organisation operating the deployment; `""` when unset. It is the `agent` of the run's CreateAction. Never a processing account, which only reads and calls back |

- `run_uuid` is what ties the three records of a run together. It is stamped into the document
  record (`DocumentRecord(run_uuid=logger.run_uuid)`, on every block and the contributor entry),
  and it is the `@id` of the run's RO-Crate `CreateAction`
  (`atrium_rocrate.create_action(logger.record)`). The CLI state file keeps it across a bash
  stage's calls, and a step of such a stage that writes the record reads the run from that file,
  `ParadataLogger.from_state_file(state)` (its `run_id`, `run_uuid` and `paradata_ref`).
  `merge_paradata_files` and `merge_run_paradata` carry each step's and stage's
  `run_uuid`, and a merged record mints its own. Merged stages also carry their `repository`,
  `tool_version`, `docker_image` and `start_time`/`end_time`, so a run crate describes each stage
  by itself.
- **Service mode.** A service creates its logger with `paradata_dir=None`: nothing is written to
  the container's filesystem, `finalize()` returns `""`, `logger.record` is the finalized record,
  and `logger.paradata_ref` is the `run_uuid` instead of a file path. The service returns the run
  as `paradata`, a Process Run Crate `CreateAction` built from that record
  ([`rocrate_export.md`](rocrate_export.md) §5), with every successful response.
