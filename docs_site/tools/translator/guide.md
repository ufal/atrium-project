---
title: translator — Guide
nav_order: 51
status: published
round: 6
issue: 57
repo: atrium-translator
role: guide
---

# translator — Guide

Get it running — from a local checkout, from a container, or as one stage of the
pipeline — without reading the code. Every flag mentioned here is listed in full on the
[Reference](reference.md) page.

!!! note "Branches"
    The code lives on the default branch, **`master`**; `test` is the integration branch
    changes are staged on. See [History → Branches](history.md#branches).

## 1 · Local install

Python **3.11**. Language identification needs `fasttext`, which is shipped here as
`fasttext-wheel` precisely so that a C++ compiler is not required.

```bash
git clone https://github.com/ufal/atrium-translator.git
cd atrium-translator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The repository is not a pip-installable package: every invocation is `python main.py` from
the repository root. Optional back-ends have their own requirement files —
`requirements-llm.txt` for `openai_compatible`, `requirements-ct2.txt` for `ct2`.

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
[Reference → Metadata mode](reference.md#metadata-amcr-mode) walks through the steps.

!!! tip "Validate `append` output against the AMCR schema"
    `--xsd <url-or-path>` validates the finished metadata file and reports any failure as a
    warning — the way to confirm that a target schema accepts the added sibling elements.
    It applies to metadata output only, not to ALTO.

**Straight from AMCR** — an input may be an OAI-PMH `GetRecord` URL, like the samples in
`amcr-inputs.txt`; it is downloaded to `--download-dir` first:

```bash
python main.py "https://api.aiscr.cz/2.2/oai?verb=GetRecord&metadataPrefix=oai_amcr&identifier=https://api.aiscr.cz/id/C-TX-202400594" \
    --formats xml -o /data/translated
```

**Fewer API calls, slightly coarser line splits:**

```bash
python main.py /data/PAGE_ALTO/... --alto --fast-align -o /data/translated
```

## 3 · Configuration and precedence

Four layers, highest first:

**CLI flag → `config.txt` key → environment variable → built-in default.**

!!! note "The source language defaults to detection"
    The shipped `config.txt` sets `source_lang = auto`, so FastText identifies the language
    unless `--source_lang` is given. Pass `--source_lang cs` when the input is known to be
    Czech: it saves the detection step and keeps the CC BY-NC FastText component out of
    the run's resolved licence.

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
leading `v` — `1.1.0-beta` for release `v1.1.0-beta` — or `latest`; see [Operations](../../operations.md#images-and-tags) for
when each tag moves.

| Image                                          | Stage  | Entry point             | What it is                    |
|------------------------------------------------|--------|-------------------------|-------------------------------|
| `ghcr.io/ufal/atrium-translator:<version>`     | `base` | `python main.py`        | the batch CLI                 |
| `ghcr.io/ufal/atrium-translator-api:<version>` | `api`  | `python -m service.api` | the HTTP service on port 8000 |

The `-api` suffix belongs to the image **name**: pull `atrium-translator-api:<version>` for the
service. An image built locally with Compose carries its own local tag.

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

Each pipeline stage runs as its own container, and the document record passed between
them with `--document-json` / `--document-json-out` is the handoff. The hub's end-to-end
smoke workflow is the reference sequence; this is its translator stage:

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

With a vocabulary CSV loaded, controlled terms keep their fixed English translation. On
the `lindat` backend this is **Tag-and-Protect**: multi-word phrases are matched
longest-first, as whole words, at every occurrence; single words are matched by lemma
through UDPipe, skipping plurals so the English keeps its agreement (for the eight
languages with a UDPipe model; any other language skips the lemma pass); matches are
replaced by sentinels the model copies through, and restored after translation. LLM
backends receive the matching terms as a glossary in the prompt instead.
[Reference → Vocabulary protection](reference.md#vocabulary-protection) has the details.

```bash
python main.py /data/amcr --vocabulary data_samples/vocabulary.csv -o /data/translated
python load_vocab.py --out data_samples/vocabulary.csv      # rebuild it from AMCR + TEATER
```

`load_vocab.py` harvests AMCR over OAI-PMH and TEATER over GraphQL; `--skip-amcr` and
`--skip-teater` take one source at a time, and `--delay` throttles the harvest. The shipped
vocabulary holds several thousand Czech–English term pairs, each traceable to the
thesaurus concept it came from.

Loading it changes the run's resolved licence: AMCR and TEATER data are both CC BY-NC 4.0.

## 7 · Use it from a coding agent

The `agent-skill` branch packages the HTTP service as an Agent Skill, so a coding agent can
translate a file by calling the running service. Installation and the contract it relies on
are on the [Agent skills](../../agent-skills.md) page.

## Troubleshooting

| Symptom                                             | Cause                                                                                                  | Fix                                                                                                                 |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `.env` values have no effect under `python main.py` | `.env` is read by Compose (`env_file`) for the container; `main.py` reads only the process environment | export the variables, or run through Compose                                                                        |
| `EACCES` writing to `./data` under Docker           | host directory not writable by uid 10001                                                               | `chown 10001` the mounted directory                                                                                 |
| Container reports healthy, nothing can reach it     | `HOST=127.0.0.1` binds inside the container only                                                       | leave `HOST` unset (defaults to `0.0.0.0`)                                                                          |
| Every document is detected as English               | the FastText model could not be downloaded or loaded; detection then answers `en` for everything       | check `GET /health?deep=true`, which reports it; or pass `--source_lang` explicitly, which skips detection entirely |
| `/translate` answers 422 for a metadata file        | no readable `AMCR_FIELDS_PATH`, so there are no fields to translate                                    | point `AMCR_FIELDS_PATH` at `amcr-fields.txt` or your own XPath list                                                |
| A translation run is slow, with no error            | page batches fell back to one call per item, after a line-count mismatch or a transport error          | read the per-document `WARNING` summary, which counts each cause                                                    |
| Container exits 143                                 | clean SIGTERM drain                                                                                    | expected; not a failure                                                                                             |

## Sources

Read from `ufal/atrium-translator` at branch **`master`**, commit `71feaef` (2026-09-23).
This table records **provenance**, not a build instruction.

| Source                                                                       | What was taken from it                                                              |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `README.md` §§ Prerequisites, Docker & Compose, Usage, Environment Variables | the install and invocation sequences                                                |
| `main.py` (`parse_arguments`, `fetch_xml_from_url`)                          | flag defaults, URL inputs                                                           |
| `config.txt`                                                                 | the precedence rules and the attachable-endpoint note, quoted from its own comments |
| `Dockerfile`, `docker-compose.yml`                                           | image targets, volumes, uid, shutdown behaviour                                     |
| `service/api.py`, `utils.py`                                                 | the metadata-mode 422, the batch-fallback summary                                   |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`                    | the pipeline-stage invocation                                                       |
