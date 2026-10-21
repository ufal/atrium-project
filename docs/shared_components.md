# Shared components: owners, adoption and compatibility

> **Status:** policy, added 2026-10-20 for [#82](https://github.com/ufal/atrium-project/issues/82).
> **Scope:** code, contracts, tests and data that more than one of the six tool repositories use.
> The inventories stay where they are: [`templates/shared/MANIFEST.json`](templates/shared/MANIFEST.json)
> (hub files), the consumers' `tests/test_vendored_*_parity.py` (tool-to-tool copies) and
> `.github/production-image.json` (what each image runs). This page says how they are governed.

## Who owns what

| Component                                                                        | Owner           | Consumers                        | Role in the consumer                                               | Adopted revision recorded in                                                   |
|----------------------------------------------------------------------------------|-----------------|----------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Record, paradata, service and limits modules, `healthcheck.py` (`MANIFEST.json`) | hub             | all six                          | runtime, in every production image                                 | the caller's `hub-ref` (`v1` today; a commit SHA after the pin sweep, #40/#72) |
| `atrium_document.schema.json` and the frozen `…doc-schema-v1.json`               | hub (with AMČR) | all six                          | contract: the record AMČR receives                                 | as above; the freeze is tag `doc-schema-v1`                                    |
| `check_version.py`, `atrium_openapi.py`                                          | hub             | all six                          | release tooling (`atrium_openapi.py` also serves `/info`'s digest) | as above                                                                       |
| The 11 shared `tests/test_*.py`                                                  | hub             | all six                          | contract tests, not in images                                      | as above                                                                       |
| `text_formats.py` (the document reader)                                          | ocr-postprocess | digital-convert                  | runtime                                                            | `ADOPTED` in digital-convert `tests/test_vendored_reader_parity.py`            |
| `teitok_read.py`, `bbox_scale.py` (TEITOK reading, geometry)                     | nlp-enrich      | digital-convert, keyword-extract | runtime                                                            | `ADOPTED` in each consumer's `tests/test_vendored_teitok_parity.py`            |
| `flexiconv_convert.py`, its requirements, test and fixtures                      | nlp-enrich      | digital-convert                  | experimental CLI path; not in the production image                 | as above                                                                       |
| The curated vocabulary (`atrium-vocabulary-<v>.zip`, a release asset)            | keyword-extract | translator                       | data bundled in the image                                          | `VOCABULARY_PIN` in translator `tests/test_vocabulary_pin.py`                  |

The AMČR ↔ ÚFAL exchange contract (the record schema, its field meanings, the service responses
AMČR consumes) is **jointly governed**: changes may start at ÚFAL, but a change to an agreed meaning
needs AMČR's agreement (class (c) below).

## Rules

1. **One owner per component.** A shared file has one owning repository and a public contract.
   Consumers never change a vendored copy: a fix lands at the owner first and is then adopted.
2. **Every consumer records what it adopted.**
   - *Hub files:* the hub commit its callers pin (`hub-ref` and the `uses:` SHA move together;
     [`release_trust.md`](release_trust.md) step 7).
   - *Tool-to-tool copies:* `ADOPTED = {"owner", "commit", "release"}` (a 40-hex owner commit and the first
     owner release that contains it) beside the per-file SHA-256 pins in `VENDORED`.
   - *Data assets:* the owner release, the asset's SHA-256 as the immutable release lists it, and the
     SHA-256 of the file built from it.
3. **Adoption is a reviewed change.** The consumer updates the copy, `VENDORED`, `ADOPTED`, the tests and
   `production-image.json` in one pull request. A green consumer release stays reproducible with what it
   adopted; it need not follow the owner's `test` branch.
4. **Classify each change by impact.**

   | Class | What changes                                                                                                                                             | Needs, in the same change                                                                                                                                                                                                                     |
   |-------|----------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
   | (a)   | implementation only: no change to inputs, outputs, schema or meaning                                                                                     | owner tests; re-vendor; byte parity                                                                                                                                                                                                           |
   | (b)   | a backward-compatible addition: an optional field, a new block, a new reason                                                                             | (a), plus the contract tests: `VALID_SHAPES`, a `POST_FREEZE_CHANGES` entry with its row in [`document_schema.md`](document_schema.md), the OpenAPI compare                                                                                   |
   | (c)   | breaking, or a change of meaning: a field removed or renamed, validation tightened, or what a record, its paradata, RO-Crate or rights statements assert | (b), plus the schema version procedure (`document_schema.md` §"Changing the schema after the freeze"), review by every affected tool, an E2E run on recorded inputs, and **AMČR's agreement** recorded on the change's issue before it merges |

   The schema freeze means no uncoordinated interface churn, not that justified changes are forbidden.
   The rights model of [#6](https://github.com/ufal/atrium-project/issues/6) is a class (c) change.
5. **Test behaviour, not only bytes.** Byte parity shows that two copies are the same file, not that a
   change is compatible. An externally visible change needs its unit, API, record or RO-Crate tests and a
   cross-tool run. No check is made green by skipping it ([`ci_policy.md`](ci_policy.md)).
6. **Releases are self-contained.** Each image and source tag carries a fixed copy of its shared code and
   declares where it came from (`production-image.json`). Nothing fetches source, schemas or vocabularies
   from GitHub at startup.
7. **Keep attribution.** Copied files keep their header naming the owner. The rights in generated data
   are a separate question (#6).

## Owner revision vs. the owner's `test` branch

`vendored-parity` (`para-drift.reusable.yml`) compares each copy with its owner in two steps (#82 B):

- **Blocking:** the consumer's copies match their `VENDORED` pins (the local test) and the owner's files
  **at `ADOPTED["commit"]`**. `tools/ci/vendored_pins.py list` reads the pins without importing the test; the
  job checks the owner out at that commit and runs the pin tests. A local edit, a pin that names the wrong
  revision, or an owner the caller's `vendored-from` does not list, fails.
- **Advisory:** the same files compared with the owner's `test` head (`vendored_pins.py ahead`). A
  difference goes to the job summary as a table of the files the owner changed since, which is the cue for
  an adoption pull request, not a defect.
- **Urgent or coordinated fixes:** the owner opens the adoption pull requests in the consumers itself, so
  nobody has to wait for a red build to learn of them.

Before this, the job compared the copies with the owner's `test` head and failed on any difference, so an
owner commit to `test` could turn an unchanged consumer red.

## Pull request checklist (shared components)

Copy into the description of any pull request that changes, or adopts, a shared component:

1. **Owner and source:** the owner repository and the 40-hex commit (or release and asset SHA-256).
2. **Scope:** the owner paths and the consumer paths touched.
3. **Impact class:** (a), (b) or (c), with one line of reason.
4. **Contract tests:** which were updated; for (c), the link to AMČR's agreement.
5. **Consumers:** the adoption pull request (or issue) for each consumer in the map above.
6. **Pins:** copy, `VENDORED`, `ADOPTED` and `production-image.json` changed in the same commit.
7. **Rollout and rollback:** the merge order (owner, then consumers) and how to go back (revert the
   adoption; the previous `ADOPTED` still passes).

## Re-vendoring

- Hub files: `scripts/revendor_shared.sh` (all six checkouts beside the hub; `--check` only compares).
- `text_formats.py`: the same script, from `../atrium-ocr-postprocess`.
- TEITOK files: copy from `../atrium-nlp-enrich` (same paths), then run the consumer's
  `python3 tests/test_vendored_teitok_parity.py`, which prints the new `VENDORED` lines; set `ADOPTED` to
  `git -C ../atrium-nlp-enrich rev-parse HEAD` and the first release that contains it.
- The vocabulary: `load_vocab.py --from-release <release>` in the translator, then update
  `VOCABULARY_PIN` and the README in one change.

A standalone shared Python package is not planned. It is worth reconsidering only if update frequency,
failures or deployment cost show that copying costs more than it saves.
