---
title: translator — Changelog
nav_order: 53
status: published
round: 8
issue: 57
repo: atrium-translator
role: changelog
---

# translator — Changelog

**The release history from v0.0.2 on.** The canonical entries live in the tool's
[`CONTRIBUTING.md`](https://github.com/ufal/atrium-translator/blob/master/CONTRIBUTING.md#-release-history).
This page gives the same history in two other shapes: a scannable line per release, and the
arcs those releases belong to.

Releases are numbered as pre-releases in the project's own sense — `0.x`, then `-beta` —
and from `v0.10.1` on each one publishes its container images through the release gate
described on [Operations](../../operations.md#the-release-gate).

## The five arcs

**1 · Getting XML in and out intact** (`v0.0.2` → `v0.4.1`). The early releases narrow the
problem. `v0.0.2` accepts almost anything — txt, pdf, xml — and `v0.1.0` adds a draft AMCR
path with no line-level logging. `v0.2.1` is the first release that says what the tool is
*for*: ALTO and AMCR XML only. `v0.3.0` adds paradata logging, `v0.4.0` the controlled
vocabulary, `v0.4.1` the first tests.

**2 · Making ALTO output structurally honest** (`v0.5.0` → `v0.8.0`). `v0.5.0` is the
technical centre of the project: the **dual-pass reconstruction** — translate the block for
quality, translate each line as a structural anchor, then realign — together with NMT-safe
vocabulary sentinels and the number-agreement guard. `v0.6.0` hardens it: XXE-proof XML
parsing through an lxml secure parser, `TranslationError` with exponential back-off instead
of logging corrupt output, pinned dependencies, and `--fast-align`. `v0.8.0` moves ALTO
translation from per-block to **per-page** calls, which is where the ~20× call-count
reduction comes from.

**3 · Backends** (`v0.6.2` → `v0.7.0`, and issue #4). A pluggable `TranslationBackend`
protocol replaces the hardcoded LINDAT call, with `lindat` and `openai_compatible`
registered and a CTranslate2 scaffold alongside. `v0.7.0` calls this "finalized in theory
(not tested in practice)": the architecture was settled first, and the choice between
candidate models was left to a measurement harness, `eval/bakeoff.py`.

**4 · Production readiness** (`v0.9.0` → `v1.1.0-beta`). OpenAPI conformance, shared
version and licence tests, the `atrium_document` integration, the hub's reusable workflows
at `@v1`, and then two releases that are about behaviour rather than features:
`v1.0.0-beta` makes five announced-but-inert contracts real, and `v1.1.0-beta` adds the
replace/append switch and fixes three defects that only appeared under real use.

**5 · Trusting the output** (`v1.2.0-beta` → `v1.2.1-beta`). The first sample refresh against
the live service found replies that were not translations, an aligner that trusted them, and
an `append` mode for ALTO that lost the source. `v1.2.0-beta` checks every reply against its
source, re-runs and keeps-as-source what fails, keeps the scanned text in ALTO `append`,
makes `--source_lang auto` fall back instead of guessing, and gives the log a `status` per
line. `v1.2.1-beta` makes each document record state the run's licence, makes `--xsd` work
on AMCR records — which settles that AMCR 2.2 accepts `replace` output and not `append` — and
corrects the published API image name in the documentation.

## v1.2.1-beta — licence in every record, `--xsd` on AMCR

* **Every document record states the run's licence.** The record took its licence block
  before the backend's components were recorded, so the record of a one-file run — one
  pipeline stage, one `/translate` call — and the first record of a batch named only
  FastText, or no component at all, and resolved to CC BY-NC 4.0 instead of the run's
  CC BY-NC-SA 4.0.
* **`--xsd` works on AMCR records.** The AMCR 2.2 schema imports the W3C XML-namespace schema
  over `http://`, which lxml's libxml2 cannot fetch, so loading it always failed; imports are
  resolved by the tool now. A harvested record is validated inside its OAI-PMH envelope, not
  the envelope itself.
* **The answer it gives:** AMCR 2.2 accepts the records as source and as `replace` output,
  and rejects `append` output — `xml:lang` is not declared on the free-text fields and the
  repeated element is not allowed. `append` on AMCR records logs a warning; ALTO in either
  mode validates against ALTO 3.1.
* **Image name.** The API image is `ghcr.io/ufal/atrium-translator-api:<version>`; the README
  and the compose file named a tag that is never published.

## v1.2.0-beta — trusting the output

**The degenerate-output guard.** Every reply — block, line anchor, metadata field — is
checked against its own source for being empty, far too long, cut short or stuck in a loop.
A bad reply is requested again; a segment that still fails is re-run once the whole document
is done; one that never recovers keeps its source text and is logged `untranslated`. A
batched reply is accepted only when every item in it passes.

**ALTO alignment restored.** Line anchors are checked before they steer the split, a line
with an unusable anchor is placed by word count (`approx_alignment`), no line with text is
starved while words remain, and a table column whose repeated cells the model merged is
placed line by line from each cell's own translation.

**ALTO `append` keeps the source.** `CONTENT` stays as scanned; each `String` gains
`<ALTERNATIVE PURPOSE="translation:<target>">`. `replace` moves an existing block `LANG` to the
target language.

**Source language.** A FastText guess is used only when the text is long enough, the score
high enough and the language one the backend translates; otherwise the element's label, the
document's language, then `--default-source-lang` (`cs`). The record gets
`translations.detected_source_lang`.

**The log.** A sixth column, `status` (`ok` / `rerun` / `approx_alignment` / `untranslated`);
rows in document order; written beside the output and moved into place when the document is
done. Also: `ct2` registered as a backend, vocabulary provenance columns, a metadata-mode
directory scan that leaves `*.alto.xml` out.

## v1.1.0-beta — the replace/append switch

**The replace/append switch.** `--output-mode replace|append` — also a `config.txt` key, an
`OUTPUT_MODE` environment variable and a `/translate` field — decides whether the
source-language field is overwritten or kept beside an `xml:lang`-marked sibling, the shape
AMCR's own thesaurus already uses for `heslo` / `heslo_en`. In ALTO mode this release
labelled the block rather than adding a per-`String` alternative (`v1.2.0-beta` replaced that
with an `ALTERNATIVE` per `String`, keeping the scanned text). `replace` stays the default,
and its output is byte-identical across all 16 shipped samples.

**Three fixes that only real use could find:**

* `/translate` answered **HTTP 200 with the metadata untranslated** — a hard-coded empty
  XPath list. Targets now load from `AMCR_FIELDS_PATH`, and an unconfigured request is a
  **422** rather than a successful-looking no-op.
* Request parameters were read from the query string while callers were sending them in the
  body. Both are now accepted.
* The page-batch fallback degraded call count by roughly **20×** behind a silent
  `except Exception: pass`. It is now counted, categorised (clean batching / line-count
  mismatch / transport error) and logged as a per-document summary.

## v1.0.0-beta — the release where five contracts became real

Prompted by a production-readiness review rather than a filed issue. Each defect lived
somewhere the test suite was structurally not looking, and each fix was confirmed by
reintroducing the defect and watching the new guard go red.

| Defect                                     | What was actually happening                                                                                                                                                                                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **The retry policy was not configuration** | `http_retry.py` clamped its arguments *upward*, so `LINDAT_MAX_RETRIES` and its `LLM_*` twins were read and discarded. The effective policy was 11 attempts backing off to **2,046 s for one failing chunk** — unreachable against a 20-second drain window |
| **413 was unreachable**                    | `/translate` read the whole upload before checking its size, for exactly the inputs the limit existed to refuse                                                                                                                                             |
| **The CLI always exited 0**                | Every failure path was a bare `return`. A Kubernetes `Job` reported success for a run that translated nothing                                                                                                                                               |
| **A failed FastText load was swallowed**   | `detect()` then answered `("en", 0.0)` for every document while the service reported itself healthy — the failure mode of an egress-restricted cluster specifically                                                                                         |
| **The release zip could not start**        | It omitted `atrium_document.py` and `service/atrium_service.py`, both imported by the entry points. `ModuleNotFoundError` on the primary download path for anyone not using the container                                                                   |

**Breaking:** the batch CLI now exits non-zero on failure.

## Every release

| Version         | What changed                                                                                                                                                                                                                                                     |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **v1.2.1-beta** | Every document record states the run's licence; `--xsd` loads the AMCR schema and validates the record inside an OAI-PMH envelope — AMCR 2.2 accepts `replace`, rejects `append`; API image name corrected                                                       |
| **v1.2.0-beta** | Degenerate-output guard with end-of-document re-run; ALTO alignment restored; ALTO `append` keeps `CONTENT` and adds `ALTERNATIVE`; safer `--source_lang auto`; log `status` column; `ct2` registered                                                            |
| **v1.1.0-beta** | The replace/append switch; `/translate` metadata 422; body *and* query parameters accepted; batch-fallback instrumentation                                                                                                                                       |
| **v1.0.0-beta** | Pre-production hardening — five announced-but-inert contracts made real. **Breaking:** non-zero CLI exit on failure                                                                                                                                              |
| **v0.10.5**     | Re-vendored `atrium_document.py`; `.coveragerc` stops omitting `service/*` — where a `backend`-less `/translate` HTTP 500 had been hiding — floor held at 81 % against a re-measured 82.87 %                                                                     |
| **v0.10.4**     | **`doc_id` is inherited, never re-derived.** The input is `PAGE_ALTO/<doc>/<doc>-1.alto.xml`, a page — so the record, the log's `file` column and the paradata key all take the *document's* id while per-file outputs keep the per-file name                    |
| **v0.10.3**     | End-to-end CI for document-JSON input/output refined against the draft schema                                                                                                                                                                                    |
| **v0.10.2**     | Workflow references repinned to the hub's `@v1` tag                                                                                                                                                                                                              |
| **v0.10.1**     | The release path exercised end to end: version guard, post-publish Trivy digest scan with SARIF, BuildKit SBOM and provenance attestations. No functional change                                                                                                 |
| **v0.10.0**     | First `atrium_document` integration; paradata template refreshed                                                                                                                                                                                                 |
| **v0.9.0**      | API standardised to OpenAPI rules, aligned with the `agent-skill` branch                                                                                                                                                                                         |
| **v0.8.1**      | Shared version-reading and licence tests; LLM review round                                                                                                                                                                                                       |
| **v0.8.0**      | **Per-page instead of per-block calls for ALTO** — the origin of the ~20× call-count reduction; `agent_dev_logs/` introduced                                                                                                                                     |
| **v0.7.0**      | Multi-backend support finalised *in theory, not tested in practice*                                                                                                                                                                                              |
| **v0.6.2**      | Draft multi-backend translation model                                                                                                                                                                                                                            |
| **v0.6.1**      | Second LLM review round; Docker CI alignment                                                                                                                                                                                                                     |
| **v0.6.0**      | **Security:** XXE-proof XML parsing via an lxml secure parser. **Reliability:** `TranslationError` with exponential back-off instead of logging corrupt output; all dependencies pinned. **Performance:** `--fast-align` and the `LINDAT_*` rate-limit variables |
| **v0.5.1**      | Docker wrapper; `fasttext` swapped for `fasttext-wheel`, removing the compiler requirement                                                                                                                                                                       |
| **v0.5.0**      | **Dual-pass ALTO reconstruction** — block plus line translation with similarity-based token alignment; NMT-safe vocabulary sentinels and the number-agreement guard; per-run licence resolution and paradata                                                     |
| **v0.4.1**      | Pytest for the main functionality                                                                                                                                                                                                                                |
| **v0.4.0**      | Controlled vocabulary added                                                                                                                                                                                                                                      |
| **v0.3.0**      | AMCR samples; paradata logging of outputs                                                                                                                                                                                                                        |
| **v0.2.1**      | **Narrowed to ALTO and AMCR XML**; citation, licence and contribution drafts                                                                                                                                                                                     |
| **v0.1.0**      | Broad input support with a draft AMCR path; no ALTO line logging yet                                                                                                                                                                                             |
| **v0.0.2**      | Working draft — txt, pdf, xml, no AMCR XPath configuration                                                                                                                                                                                                       |

## Sources

Read from `ufal/atrium-translator` at release **`v1.2.1-beta`** (branch **`master`**). The arcs
are written here, not taken from a source. This table records **provenance**, not a
build instruction.

| Source                                  | What was taken from it                              |
|-----------------------------------------|-----------------------------------------------------|
| `CONTRIBUTING.md` § `📦 Release History` | every release line and the two release descriptions |
| `agent_dev_logs/DEVLOG.md`              | the v1.0.0-beta defect table, cross-checked         |
| `CITATION.cff`                          | the current version and its release date            |
