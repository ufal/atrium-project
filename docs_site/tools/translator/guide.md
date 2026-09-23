---
title: translator — Guide
nav_order: 51
status: published
round: 3
issue: 57
repo: atrium-translator
role: guide
---

# translator — Guide

Get it running — from a local checkout, from a container, or as one stage of the
pipeline — without reading the code. Every flag mentioned here is listed in full on the
[Reference](reference.md) page.

!!! warning "Clone the right branch"
    The default branch is **`master`**. `test` is currently the same commit; `main` also
    exists and is **stale and divergent**. Three near-identical refs plus one that is not
    is a trap worth knowing about before you clone.

## 1 · Local install

Python **3.11**. Language identification needs `fasttext`, which is shipped here as
`fasttext-wheel` precisely so that a C++ compiler is not required.

```bash
git clone https://github.com/ufal/atrium-translator.git
cd atrium-translator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

There is no `pip install .` — the repository ships no `pyproject.toml`, no `setup.py` and
no console script. Every invocation is `python main.py` from the repository root.

## 2 · Translate something

**ALTO pages** — structure-preserving, the mode most of the pipeline uses:

```bash
python main.py /data/PAGE_ALTO/CTX000000003 \
    --alto --formats alto.xml \
    --source_lang cs --target_lang en \
    -o /data/translated
```

**AMCR metadata records** — the XPath targets come from `amcr-fields.txt`:

```bash
python main.py /data/amcr --formats xml --xpaths amcr-fields.txt -o /data/translated
```

**Keeping the source text beside the translation** instead of overwriting it:

```bash
python main.py /data/amcr --output-mode append -o /data/translated
```

`append` inserts a same-tag sibling carrying `xml:lang="<target>"`, which is the shape
AMCR's own thesaurus already uses for `heslo` / `heslo_en`, and stamps the source element
with its own `xml:lang`. Re-running is then a no-op rather than a double translation,
because the pair is detectable. In ALTO mode `append` **labels rather than duplicates** —
it sets `LANG` on the `TextBlock` and leaves the `String` inventory 1:1 with the source.

!!! tip "Run `append` with `--xsd` the first time against real AMCR data"
    Whether the schema permits the repeated element (`maxOccurs`) is an open question that
    the validator settles. Note that `--xsd` is **not applied to ALTO** — only to the
    metadata path.

**Fewer API calls, slightly coarser line splits:**

```bash
python main.py /data/PAGE_ALTO/... --alto --fast-align -o /data/translated
```

## 3 · Configuration, and the precedence that actually applies

Four layers, highest first:

**CLI flag → `config.txt` key → environment variable → built-in default.**

!!! danger "`--source_lang` does not default to `cs`"
    The README says the default is `cs`. `parse_arguments()` sets `default=None` and falls
    through to the config file — and the shipped `config.txt` says `source_lang = auto`.
    **The effective default for anyone using the repository as shipped is `auto`**, i.e.
    FastText detection. Pass `--source_lang cs` explicitly if that is what you mean; doing
    so also keeps the CC BY-NC FastText component out of the run's resolved licence.

The endpoints are attachable, which is the point of `config.txt`'s own note on them: they
are environment variables rather than config keys because they vary per deployment.

| Variable                                    | Default                                                  | What it points at                       |
|---------------------------------------------|----------------------------------------------------------|-----------------------------------------|
| `TRANSLATION_URL` (alias `LINDAT_BASE_URL`) | `https://lindat.mff.cuni.cz/services/translation/api/v2` | the translation API                     |
| `UDPIPE_URL`                                | `https://lindat.mff.cuni.cz/services/udpipe/api/process` | UDPipe 2, for vocabulary lemma matching |

Point both at a local stub and the whole pipeline runs offline, with no code change —
which is exactly what the repository's own integration tests do.

## 4 · Run it as a container

Two images are published to GHCR from one Dockerfile. `<version>` is the release without its
leading `v` — `1.1.0-beta` — or `latest`; see [Operations](../../operations.md#images-and-tags) for
when each tag moves.

| Image                                          | Stage  | Entry point             | What it is                    |
|------------------------------------------------|--------|-------------------------|-------------------------------|
| `ghcr.io/ufal/atrium-translator:<version>`     | `base` | `python main.py`        | the batch CLI                 |
| `ghcr.io/ufal/atrium-translator-api:<version>` | `api`  | `python -m service.api` | the HTTP service on port 8000 |

The `-api` suffix belongs to the image **name**. The compose file tags the image it builds locally
as `atrium-translator:${ATRIUM_VERSION}-api`; that is a local tag, not one the registry publishes.

```bash
docker compose run --rm translator          # batch, ./data:/data
docker compose --profile api up --build     # the service → http://localhost:8000/info
```

Volumes: `./data:/data`, `hf-cache:/cache/huggingface` (the FastText model), and
`./config.txt:/app/config.txt:ro`. The container runs as non-root `atrium`, **uid 10001**.

!!! note "Exit code 143 is a clean stop"
    The `api` stage sets `STOPSIGNAL SIGTERM` and drains for `GRACEFUL_SHUTDOWN_S`
    (default 20 s). A clean shutdown exits **143** (128 + SIGTERM), which Kubernetes and
    Compose both report as non-zero. That is the expected value.

## 5 · Run it as one stage of the pipeline

There is **no cross-service orchestration** in this ecosystem — no
`compose/docker-compose.pipeline.yml` exists. The only working end-to-end recipe is the
hub's CI workflow, and this is its translator stage, reproduced verbatim:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/work/atrium-translator-main \
  ghcr.io/ufal/atrium-translator:latest \
  /workspace/work/PAGE_ALTO/CTX000000003/CTX000000003-1.alto.xml \
  --alto --formats alto.xml --source_lang cs --target_lang en \
  -o /workspace/work/translated \
  --document-json /workspace/work/doc_json/2_alto.json \
  --document-json-out /workspace/work/doc_json/3_translate.json
```

The two `--document-json*` flags are what make the stage participate in record accretion:
the baseline comes in, only the `translations` block is written, and everything else is
deep-copied through. The record's `doc_id` is **inherited from the baseline**, never
re-derived from the page filename — which matters here more than anywhere, because the
input is `…-1.alto.xml`, a page, not the document. See [Pipelines](../../pipelines.md).

## 6 · Use the vocabulary

With a vocabulary CSV loaded (`source_lemma,target_translation`), the **Tag-and-Protect**
strategy runs before every translation call: multi-word phrases are matched longest-first,
as whole words, at every occurrence; single words are matched by lemma through UDPipe with a
singular/plural agreement guard (for the eight languages with a UDPipe model; any other
language skips the lemma pass); matches are replaced by NMT-safe sentinels,
translated, and restored with the controlled translation.

```bash
python main.py /data/amcr --vocabulary data_samples/vocabulary.csv -o /data/translated
python load_vocab.py --out data_samples/vocabulary.csv      # rebuild it from AMCR + TEATER
```

`load_vocab.py` harvests AMCR over OAI-PMH and TEATER over GraphQL; `--skip-amcr` and
`--skip-teater` take one source at a time, and `--delay` throttles the harvest. The
shipped vocabulary is roughly 5,000 rows.

Loading it changes the run's resolved licence: AMCR and TEATER data are both CC BY-NC 4.0.

## Troubleshooting

The repository has no troubleshooting section. These are the failure modes that are real,
and where each one is decided.

| Symptom                                                 | Cause                                                                                                                         | Fix                                                                                                                     |
|---------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `.env` values have no effect under `python main.py`     | **Nothing calls `load_dotenv`.** `.env` reaches the *container* through Compose's `env_file`, but a bare local run ignores it | export the variables, or run through Compose                                                                            |
| `EACCES` writing to `./data` under Docker               | host directory not writable by uid 10001                                                                                      | `chown 10001` the mounted directory                                                                                     |
| Container reports healthy, nothing can reach it         | `HOST=127.0.0.1` binds inside the container only                                                                              | leave `HOST` unset (defaults to `0.0.0.0`)                                                                              |
| Every document is detected as English                   | the FastText model failed to load; `detect()` then answers `("en", 0.0)` for everything                                       | check `GET /health?deep=true`, which now reports it; or pass `--source_lang` explicitly, which skips detection entirely |
| `/translate` returns 200 with the metadata untranslated | fixed in v1.1.0-beta — an unconfigured `AMCR_FIELDS_PATH` used to yield an empty XPath list                                   | upgrade; it is now a **422**                                                                                            |
| A translation run is very slow, with no error           | the page batch fell back to one call per item — up to ~20× more calls                                                         | v1.1.0-beta counts and logs it; look for the per-document `WARNING` summary                                             |
| `LOG_LEVEL` does not quiet the batch CLI                | **43 `print()` calls remain** in runtime code                                                                                 | known gap; `LOG_LEVEL` governs the service, not the CLI diagnostics                                                     |
| Container exits 143                                     | clean SIGTERM drain                                                                                                           | expected; not a failure                                                                                                 |

## Sources

Read from `ufal/atrium-translator` at branch **`master`**, commit `88242fe` (2026-09-21).
This table records **provenance**, not a build instruction.

| Source                                                                       | What was taken from it                                                              |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `README.md` §§ Prerequisites, Docker & Compose, Usage, Environment Variables | the install and invocation sequences                                                |
| `main.py:268-352`                                                            | the real flag defaults, and the `--source_lang` correction                          |
| `config.txt`                                                                 | the precedence rules and the attachable-endpoint note, quoted from its own comments |
| `Dockerfile`, `docker-compose.yml`                                           | image targets, volumes, uid, shutdown behaviour                                     |
| `agent_dev_logs/digests/46.digest.md`                                        | the batch-fallback instrumentation and the `/translate` 422 fix                     |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`                    | Stage 3, reproduced verbatim                                                        |
