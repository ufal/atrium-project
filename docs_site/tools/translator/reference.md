---
title: translator — Reference
nav_order: 52
status: published
round: 3
issue: 57
repo: atrium-translator
role: reference
---

# translator — Reference

Look something up and stop reading. Every value here was read out of the code at
`master` / `88242fe`, not out of the prose — where the two disagree, the disagreement is
recorded under [Known drift](#known-drift).

## CLI — `main.py`

Run as `python main.py [input_path] [flags]` from the repository root. `input_path` is
positional and optional; omitted, it falls back to `config.txt`'s `input_path`.

| Flag                    | Default                                     | What it does                                                                                                                                        |
|-------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `input_path`            | `config.txt` `input_path`                   | File or directory to translate                                                                                                                      |
| `--output`, `-o`        | `config.txt` `output`                       | Output directory                                                                                                                                    |
| `--source_lang`, `-src` | **`auto`** via `config.txt`                 | Source language, or `auto` for FastText detection. The help text says "or 'cs'"; see [Known drift](#known-drift)                                    |
| `--target_lang`, `-tgt` | `en`                                        | Target language                                                                                                                                     |
| `--formats`             | `alto.xml` via `config.txt`                 | Comma-separated extensions, e.g. `alto.xml,txt`                                                                                                     |
| `--config`, `-c`        | `config.txt`                                | Configuration file                                                                                                                                  |
| `--alto`                | off                                         | ALTO in-place mode. **Auto-enabled** when `--formats` contains `alto.xml`                                                                           |
| `--xpaths`              | `amcr-fields.txt` via `config.txt` `fields` | File listing the AMCR XPath targets                                                                                                                 |
| `--xsd`                 | —                                           | URL or path to an XSD for output validation. **Metadata mode only**                                                                                 |
| `--vocabulary`          | `data_samples/vocabulary.csv` via config    | Vocabulary CSV (`source_lemma,target_translation`)                                                                                                  |
| `--document-json`       | —                                           | Baseline ATRIUM record to accrete onto                                                                                                              |
| `--document-json-out`   | —                                           | Where to write the updated record                                                                                                                   |
| `--download-dir`        | `<output>/downloaded_inputs`                | Where URL-ingested inputs land                                                                                                                      |
| `--output-mode`         | `replace`                                   | `replace` or `append`                                                                                                                               |
| `--fast-align`          | off                                         | ALTO only: distribute block tokens by source word count instead of translating each line as an anchor. Far fewer API calls, slightly coarser splits |
| `--backend`             | `lindat`                                    | `lindat` or `openai_compatible`                                                                                                                     |

**Exit codes:** `0` OK · `1` usage · `2` no input · `3` failed. Before v1.0.0-beta every
failure path was a bare `return` and the CLI always exited 0, so a Kubernetes `Job`
reported success for a run that translated nothing.

**Precedence** for `--backend` and `--output-mode`: CLI flag → `config.txt` key → env var
→ built-in default.

### Other entry points

| Script                   | Purpose                                                         | Key flags                                               |
|--------------------------|-----------------------------------------------------------------|---------------------------------------------------------|
| `load_vocab.py`          | Harvest the vocabulary from AMCR (OAI-PMH) and TEATER (GraphQL) | `--out`, `--delay`, `--skip-amcr`, `--skip-teater`      |
| `eval/bakeoff.py`        | Backend comparison harness — **never run**                      | `--samples`, `--backends`, `--refs`, `--limit`, `--out` |
| `check_version.py`       | Release gate: tag == `CITATION.cff` == `para_config.txt`        |                                                         |
| `atrium_rocrate.py`      | RO-Crate 1.1 export, its own CLI                                | `--out-dir`                                             |
| `service/healthcheck.py` | Docker healthcheck; stdlib only, always probes loopback         |                                                         |

## Configuration — `config.txt`

| Key                   | Shipped value                     |
|-----------------------|-----------------------------------|
| `input_path`          | `./data_samples/my_documents`     |
| `source_lang`         | `auto`                            |
| `target_lang`         | `en`                              |
| `formats`             | `alto.xml`                        |
| `output`              | `./data_samples/translated_files` |
| `fields`              | `amcr-fields.txt`                 |
| `vocabulary`          | `data_samples/vocabulary.csv`     |
| `translation_backend` | `lindat`                          |
| `output_mode`         | `replace`                         |

`TRANSLATION_URL` and `UDPIPE_URL` are deliberately **not** keys here — they are
environment variables, because they vary per deployment rather than per run.

`amcr-fields.txt` holds ten AMCR XPaths (`popis`, `poznamka`, `lokalizace`,
`lokalizace_okolnosti`, `souhrn_upresneni`, two `nalez_*/poznamka`, and the three
`lokalita/chranene_udaje/*` fields). `amcr-inputs.txt` holds 16 OAI-PMH `GetRecord` URLs
against `https://api.aiscr.cz/2.2/oai`.

## HTTP service

Started by `python -m service.api`. `MAX_UPLOAD_MB` defaults to **50** — the highest of
the five ATRIUM services, because ALTO XML goes in and ALTO XML comes out.

| Method | Path                     | Returns                                                                                                                   |
|--------|--------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `POST` | `/translate`             | the translated document                                                                                                   |
| `GET`  | `/info`                  | `service`, `version`, `endpoints`, `limits` (`max_upload_mb: 50`), `supported_formats: ["ALTO XML", "AMCR Metadata XML"]` |
| `GET`  | `/health`                | `{"status":"ok"}`, always 200                                                                                             |
| `GET`  | `/health?deep=true`      | 503 with detail when degraded or draining — **this is where a failed FastText load is reported**                          |
| `GET`  | `/ready`                 | 503 until warm, 503 on SIGTERM                                                                                            |
| `GET`  | `/docs`, `/openapi.json` | FastAPI built-ins                                                                                                         |

### `POST /translate`

Multipart. Every scalar is accepted as **either a form field or a query parameter**, because
callers were found sending them both ways.

| Field           | Type       | Default                                |
|-----------------|------------|----------------------------------------|
| `file`          | upload     | required; the filename must end `.xml` |
| `document_json` | upload     | optional baseline ATRIUM record        |
| `source_lang`   | form/query | `auto`                                 |
| `target_lang`   | form/query | `en`                                   |
| `is_alto`       | form/query | `true`                                 |
| `output_mode`   | form/query | `OUTPUT_MODE` env, else `replace`      |

```bash
curl -sf -F "file=@page.alto.xml" \
     "localhost:8000/translate?source_lang=cs&target_lang=en&is_alto=true" \
     -o page_en.alto.xml
```

**Response — 200**, `Content-Type: application/xml`, with
`Content-Disposition: attachment; filename="<doc>_<lang>.alto.xml"`. The body is the
translated document. There is **no JSON envelope on success, by design**: the document is
the payload, so the endpoint composes with `curl -o`.

When `document_json` is supplied the response is instead **`multipart/mixed`** with a
uuid4 boundary — the translated XML first, then the updated record, each with its own
`Content-Disposition` filename.

### Errors

| Status | When                                                                                                                                               |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `413`  | Over `MAX_UPLOAD_MB`, or the declared envelope exceeds the cap. Enforced **during** the read, so an oversized body is refused rather than buffered |
| `415`  | `Content-Type` is neither `multipart/form-data` nor `application/json`                                                                             |
| `422`  | Missing filename, a filename not ending `.xml`, or metadata mode with no readable `AMCR_FIELDS_PATH`                                               |
| `500`  | The pipeline raised — malformed XML, or the backend failed after retries                                                                           |
| `503`  | Warming up, or draining after SIGTERM. **Retryable** against another replica                                                                       |

!!! warning "`detail` is not always a string"
    Error bodies are FastAPI's `{"detail": ...}`. `detail` is a **string** for the errors
    this service raises itself, and a **list of validation objects** when FastAPI rejects
    the request before the handler runs — a `POST` with `Content-Type: application/json`
    and no `file` part returns `422` in that second shape. A client must not assume a
    string.

### Environment

`.env.example` publishes 46 variables. The ones that change behaviour:

| Variable                                                                        | Default             | Effect                                                    |
|---------------------------------------------------------------------------------|---------------------|-----------------------------------------------------------|
| `PORT` / `HOST`                                                                 | `8000` / `0.0.0.0`  | Bind address. `127.0.0.1` makes the container unreachable |
| `MAX_UPLOAD_MB`                                                                 | `50`                | Upload cap                                                |
| `GRACEFUL_SHUTDOWN_S`                                                           | `20`                | Drain window                                              |
| `LOG_LEVEL`                                                                     | `INFO`              | Governs the service; **not** the batch CLI                |
| `ALLOWED_ORIGINS`                                                               | `*`                 | Blank string means *no* origins                           |
| `TRANSLATION_BACKEND`                                                           | `lindat`            | Backend selection                                         |
| `OUTPUT_MODE`                                                                   | `replace`           | Default output mode                                       |
| `AMCR_FIELDS_PATH`                                                              | `amcr-fields.txt`   | XPath targets; unreadable ⇒ 422 in metadata mode          |
| `TRANSLATION_URL` / `UDPIPE_URL`                                                | LINDAT              | Attachable backing services                               |
| `LINDAT_MIN_INTERVAL_S` / `LINDAT_MAX_RETRIES` / `LINDAT_BACKOFF_BASE_S`        | `0.0` / `4` / `1.0` | Transport policy                                          |
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_PROVIDER` / `LLM_LANGUAGES` | —                   | Required by `openai_compatible`                           |

!!! note "The retry defaults are configuration again"
    Until v1.0.0-beta `http_retry.py` clamped its own arguments *upward*
    (`max_retries = max(10, max_retries)`), so these variables were read and then
    discarded. The effective policy was 11 attempts backing off to **2,046 s for one
    failing chunk** — which no request could survive against a 20-second drain window.
    The declared default was always 4.

## ALTO dual-pass reconstruction

Why translated ALTO looks the way it does. Per `TextBlock`:

1. **Gather** — reconstruct each `TextLine`'s text by joining its `String` `CONTENT` values.
2. **Aggregate** — concatenate the block's lines into one string.
3. **Detect** — run FastText **once for the whole block**, so the block is internally consistent.
4. **Pass 1** — translate the whole block in one call. This is the text that is written back.
5. **Pass 2** — translate each non-empty line individually. These are **never written**; they
   are structural anchors telling the aligner how many words each physical line should get.
6. **Align** — `_align_tokens_to_lines` partitions the Pass-1 tokens into one bucket per line,
   searching a ±50 % window around each line's expected word count and picking the split that
   maximises `difflib.SequenceMatcher` similarity against that line's anchor. The last line takes
   the remainder. Within a line, tokens are distributed greedily 1-to-1 across `String`
   elements, and **the last `String` absorbs everything left over**.

Guarantees: translated words never cross line boundaries, every `String` keeps its original
position, and no Pass-1 token is lost.

**Consequence, measured:** on a 79-page sample, 528 of 7,229 `String` boxes (7.3 %) no longer
hold exactly one word — 224 empty, 304 multi-word. None was resized. The word-to-box
correspondence in the output is **manufactured by the bucketing, not observed**, which is the
reason `append` mode labels the block rather than adding a per-`String` English alternative: that
alternative would not be an alternative reading of that word, but whichever token the bucketing
happened to land there.

**Cost:** `_translate_batch` joins a page's blocks and its lines into one call each, falling back
to one call per item when the line count does not survive the round trip. For the 79-page sample
that is roughly **158 calls against up to ~3,288**. The fallback is now counted and logged with a
per-document `WARNING` summary, separating clean batching from line-count mismatch from transport
error.

## Outputs

| Artefact            | Name                                                                  | Contents                                                                                                                                                                                                                                                                                                            |
|---------------------|-----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Translated document | `<stem>_<target_lang><suffix>` — e.g. `MTX201501307_anon_en.alto.xml` | the same document, same tags, same coordinates                                                                                                                                                                                                                                                                      |
| Translation log     | `<original_filename>_log.csv`                                         | `file, page_num, line_num, text_<source_lang>, text_<target_lang>` — **the last two column names are built from the run's languages**, so a header may read `text_auto, text_en`. ALTO: `page_num` is the 1-based page, `line_num` the `TextLine` element id. Metadata: `page_num` empty, `line_num` the full XPath |
| Paradata            | `YYMMDD-HHmmss_translator.json`                                       | schema 2.0 — tool version, run id, resolved licence with its full component derivation, timings, config (including `chunk_limit: 4000`, the language-ID model, the translation API and the 0.2 confidence threshold), statistics, and skipped files                                                                 |
| Document record     | `<doc_id>.document.json`                                              | see below                                                                                                                                                                                                                                                                                                           |
| RO-Crate            | `ro-crate-metadata.json`                                              | only from `atrium_rocrate.py`'s own CLI                                                                                                                                                                                                                                                                             |

### What lands in the document record

```json
"translations": {
  "source_lang": "cs",
  "target_lang": "en",
  "backend": "lindat",
  "output_mode": "replace"
}
```

`output_mode` rides along because `additionalProperties` is true on this block — and a
consumer that finds English in a field needs to know whether the Czech was kept beside it
or overwritten.

The translated **text** is not stored in the record. It persists as
`derived_from.translated_xml`, plus a licence-detail entry. The record's `doc_id` is
**inherited** from the baseline and never re-derived from the input filename, because the
input is a page (`<doc>-1.alto.xml`), not the document. The output is validated before
`finalize()`, so a failed record is never emitted.

## Licence is computed, not declared

`para_config.txt` declares each component, its licence and whether it is `always` or
`conditional`; `para_licenses` resolves the run.

| Component               | Licence              | Counts when                               |
|-------------------------|----------------------|-------------------------------------------|
| `fasttext`              | CC BY-NC 4.0         | language auto-detection actually ran      |
| `lindat_cubbitt`        | CC BY-NC-SA 4.0      | the `lindat` backend was used             |
| `udpipe2_engine`        | MPL 2.0              | vocabulary lemma matching ran             |
| `udpipe2_models`        | CC BY-NC-SA 4.0      | as above                                  |
| `amcr_vocab`            | CC BY-NC 4.0         | the AMCR vocabulary was loaded            |
| `teater_data`           | CC BY-NC 4.0         | the TEATER thesaurus was loaded           |
| `llm_api`               | *"LLM provider ToS"* | the `openai_compatible` backend was used  |
| `ctranslate2`           | MIT                  | CT2 backend                               |
| `eurollm` / `madlad400` | Apache-2.0           | CT2 models                                |
| `opus_mt`               | CC BY 4.0            | CT2 model (tc-big line; older Apache-2.0) |
| `nllb200`               | CC BY-NC 4.0         | CT2 model — **non-commercial**            |

**A default run resolves to CC BY-NC-SA 4.0.** `llm_api` deliberately carries an
unrecognised licence string, so `para_licenses` treats it as maximally restrictive —
ranked highest, with both the non-commercial and share-alike flags set — and warns: the
safe default for a prototype backend whose provider terms are not a CC or OSS licence.
Every `CT2_MODEL_FAMILY` maps to one of the model rows above; an undeclared component
would be logged as `UNKNOWN`, which resolves the same way.

**The permissive recipe** — all three parts are required:

1. `--backend ct2` with a permissive model — EuroLLM or MADLAD-400 (Apache-2.0) or
   Opus-MT (CC BY 4.0), **not** NLLB-200 — see [Overview](index.md#the-three-backends);
2. an explicit `--source_lang`, so FastText never loads and its CC BY-NC weights never count;
3. a permissive or empty vocabulary, so AMCR and TEATER never count.

## Languages

`processors/identifier.py` maps ISO 639-3 → ISO 639-1 for exactly twenty languages:

`ces→cs · eng→en · fra→fr · deu→de · rus→ru · pol→pl · ukr→uk · slk→sk · bul→bg · hrv→hr ·
slv→sl · lav→lv · lit→lt · est→et · hun→hu · ron→ro · spa→es · ita→it · nld→nl · hin→hi`

Detection model: `facebook/fasttext-language-identification`, confidence threshold **0.2**.
UDPipe lemmatisation models are named per language — `czech-pdt-ud-2.15`,
`slovak-snk-ud-2.15`, `polish-pdb-ud-2.15`, `german-gsd-ud-2.15`, `french-gsd-ud-2.15`,
`russian-syntagrus-ud-2.15`, `ukrainian-iu-ud-2.15`, `english-ewt-ud-2.15`. Any other source
language is not lemmatised: the single-word vocabulary pass is skipped for it with one
warning, instead of falling back to the Czech model as it once did. Multi-word vocabulary
phrases are still protected.

## Known drift

Each item was confirmed against the code at `master` / `88242fe`. Reported here, not fixed
here; each is a candidate issue in the tool's own repository.

**The README's paradata example is three versions stale**

1. It shows `"tool_version": "v0.5.0"` and `ghcr.io/ufal/atrium-translator:v0.5.0`;
   `para_config.txt` and `CITATION.cff` both say **v1.1.0-beta**.
2. It resolves to `"license": "CC BY-NC 4.0"` with `lindat_cubbitt` listed as CC BY-NC 4.0;
   `para_config.txt` says **CC BY-NC-SA 4.0**, and the committed paradata sample resolves to
   CC BY-NC-SA 4.0. The README's own licence section gets this right — only the JSON example
   is wrong.
3. Two fields in that example are **markdown links pasted inside JSON string literals**:
   `"repository": "[https://…](https://…)"`. The example is not valid JSON as printed.

**Defaults and behaviour that differ from the prose**

4. `--source_lang` is documented as defaulting to `cs`. The code defaults to `None` and falls
   through to `config.txt`, which ships `auto`.
5. The language-ID **fallback is documented twice, differently**: the README says confidence
   below 0.2 falls back to Czech (true, in metadata mode), while a model that fails to load
   entirely makes `detect()` return `("en", 0.0)` for every document.
6. ~~`CT2_COMPUTE_TYPE` is documented as defaulting to `int8` in the module docstring and
   `int4` in the class docstring and the code.~~ **Fixed:** the default is `int8`
   everywhere (CTranslate2 has no `int4`, so the old default failed every load), and a
   value the device cannot run is refused with the list of valid ones.
7. `--xsd` is **never applied to ALTO** — `process_alto_xml` takes no schema parameter. Stated
   in a digest, nowhere in the README.

**Things that exist but do not do what their presence implies**

8. `entities[].translation_en` is declared as owned by this tool in the hub's block-ownership
   table, and is **unimplemented**. A 19-line comment in `utils.py` says so and points at a
   digest that does not exist in this repository.
9. `atrium_rocrate.py` — 45 KB with 22 tests — is **never called by `main.py` or the
   service**, only by its own CLI. A reader of the README's feature list will assume runs
   produce crates. They do not.
10. `LOG_LEVEL` does not govern the batch CLI: **43 `print()` calls remain** in runtime code.
11. The `live-backend` integration job, whose own header says "run before a release", has
    **never been dispatched**.
12. ~~`ct2` cannot be selected without editing `processors/backend.py`.~~ **Fixed:** `ct2`
    is registered; `ctranslate2` / `sentencepiece` still load only on first use.

**Repository hygiene a newcomer will trip on**

13. `v1.1.0-beta` and `v1.0.0-beta` are published with GitHub's `prerelease` flag set to
    **false**, so a beta presents as the latest stable release.
14. `CONTRIBUTING.md`'s repository footnote points at `ARUP-CAS/atrium-translator`; the
    repository is `ufal/atrium-translator`.
15. The contact address differs between `README.md` and `CONTRIBUTING.md`.
16. The README links `data_samples/my_documents/MTX201501307.alto.xml`; the committed file is
    `MTX201501307_anon.alto.xml`.
17. `main` exists as a stale, divergent branch while `master` is the default.

## Sources

Read from `ufal/atrium-translator` at branch **`master`**, commit `88242fe` (2026-09-21).
This table records **provenance**, not a build instruction.

| Source                                                       | What was taken from it                                         |
|--------------------------------------------------------------|----------------------------------------------------------------|
| `main.py:268-352, 547-550`                                   | the flag table, defaults and exit codes                        |
| `config.txt`, `para_config.txt`                              | configuration and the licence component table                  |
| `service/api.py:55-67, 262-495`                              | limits, request fields, response shapes                        |
| `service/README.md`                                          | the error table and the `detail` shape warning, quoted from it |
| `utils.py:385-403`                                           | the `translations` block as actually written                   |
| `processors/backend.py`, `processors/identifier.py`          | the registry and the language map                              |
| `README.md` §§ Logic Overview, ALTO Dual-Pass Reconstruction | the six-stage algorithm                                        |
| `agent_dev_logs/digests/46.digest.md`                        | every measured figure, and the batch-fallback instrumentation  |
| `docs/translation-backends.md`                               | backend comparison and the permissive recipe                   |
