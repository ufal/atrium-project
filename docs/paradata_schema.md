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