---
title: page-classification — Guide
nav_order: 31
status: published
round: 6
issue: 57
repo: atrium-page-classification
role: guide
---

# page-classification — Guide

Get it running — from a local checkout, from a container, or as one stage of the
pipeline — without reading the code. Every flag mentioned here is listed in full on the
[Reference](reference.md) page.

!!! note "Branches"
    The code lives on the default branch, **`vit`**. `master` is a short index pointing at
    the two model-family lines, `vit` and `clip` — `clip` is a separate CLIP-based
    classifier with its own Hugging Face repository — and `agent-skill` holds the Agent
    Skill packaging. See [History → Branches](history.md#branches).

## 1 · Local install

Python **3.11** — the version the container images and CI use across all six ATRIUM
repositories. numpy is pinned below 2.5, because 2.5 requires Python 3.12.

```bash
git clone https://github.com/ufal/atrium-page-classification.git
cd atrium-page-classification
python3 -m venv .venv && source .venv/bin/activate
pip install -r setup/requirements.txt
python3 run.py --hf          # pulls the model from the Hugging Face hub
```

There is no `pip install .` — the repository ships no `pyproject.toml` and no console
script. Every invocation is `python3 run.py` from the repository root.

`model/`, `result/` and `checkpoint/` are runtime directories — downloaded weights,
result tables and training checkpoints — created on first run and mounted as volumes
under Docker.

**Choosing a model.** `-rev` pins one revision of `ufal/vit-historical-page` —
`-rev v4.4` is the recommended single model, small and the most accurate of its
generation — and `--best` runs the five-model ensemble instead. Name a revision
explicitly rather than relying on the repository's `main` branch; the
[Overview](index.md#the-models) explains the revision names.

## 2 · Classify something

**One page:**

```bash
python3 run.py -f /full/path/to/page.png            # Top-3, printed to the console
python3 run.py -f /full/path/to/page.png -tn 1      # single best guess
python3 run.py -f /full/path/to/page.png --best     # all five models, averaged
```

**A directory** — pass `-d <path>`, or `--dir` to use the preset in
`[INPUT] FOLDER_INPUT`. Input is selected only by `-f`, `-d` or `--dir`:

```bash
python3 run.py -d /data/pages --inner                      # recurse into subfolders
python3 run.py --dir --inner --best                        # ensemble over the config default
python3 run.py --dir --inner --best --parallel             # memory-aware, CUDA only
python3 run.py --dir --inner --raw                         # per-class scores, all 11 columns
```

Directory processing runs in batches (`[SETUP] batch`, default 16). Memory use grows
with the batch: roughly 2 GB at 4, 5 GB at 16 and 17 GB at 64, on CPU or GPU alike — below
12 is safe on an office desktop. Above roughly half a million files, simply *listing* the
tree takes noticeable time before any inference starts.

Results land in `[OUTPUT] FOLDER_RESULTS` (default `./result`) as timestamped CSVs —
see [Reading the output](#reading-the-output) below, and
[Reference → Outputs](reference.md#outputs-and-their-columns) for every column schema.

### Preparing input

The classifier reads **page images**, one file per page. Scanned PDFs are split first with
the bundled converter, which renders every page at 300 dpi with poppler's `pdftoppm`, in
parallel, into one sub-folder per PDF:

```bash
data_scripts/unix/pdf2png.sh --dir /data/pdfs --output /data/pages      # PDFs are kept
data_scripts/unix/pdf2png.sh --dir /data/pdfs --format jpg --dpi 200    # other options
```

`data_scripts/windows/pdf2png.bat` does the same with ImageMagick and Ghostscript, one file
at a time. The HTTP service needs neither: `POST /predict_document` takes the PDF itself
and renders it at the same 300 dpi.

**The file name carries the page number.** A page image is expected to be named
`<document>-<page>.png` or `<document>_<page>.png`; the tool splits on the *last* separator,
so `report_2021_003.png` is document `report_2021`, page 3. Those two halves become the
`FILE` and `PAGE` columns of every result table and the key of the document record. A name
without a trailing page number is treated as page 1, with a warning.

### Reading the output

A Top-3 run produces one row per page, best guess first; scores are normalised
probabilities, rounded to three decimals. These rows are from a `v4.3` run committed in the
tool repository as `result/tables/20260530-1220_model_v43_TOP-3.csv`:

```text
FILE,PAGE,CLASS-1,CLASS-2,CLASS-3,SCORE-1,SCORE-2,SCORE-3
atrium,1,TEXT,LINE_P,TEXT_P,0.981,0.017,0.002
atrium,2,LINE_P,TEXT,TEXT_P,1.0,0.0,0.0
atrium,4,LINE_P,TEXT,TEXT_P,0.799,0.146,0.055
atrium,23,TEXT_P,TEXT,PHOTO,0.549,0.451,0.0
```

`CLASS-1` is the category to act on; a low `SCORE-1` with a close `CLASS-2` — page 23
above — marks a page worth a human look. `--raw` adds a table with one probability column per category, which
is convenient for review because ambiguous pages spread their probability across several
columns. With `--best` the run also writes one Top-1 vote per model, so disagreement
between the five models is visible page by page.

When a record is requested, the same Top-1 lands in the [document record](../../ecosystem/document-contract.md):
`page_categories` maps each page number to its label, and `pages[].category` /
`pages[].category_confidence` carry the label and `SCORE-1`.

## 3 · Run it as a container

Two images are published to GHCR from the same Dockerfile. `<version>` is the release without its
leading `v` — `1.8.0-beta` — or `latest`; see [Operations](../../operations.md#images-and-tags) for
when each tag moves.

| Image                                                   | Stage  | Entry point                             | What it is                    |
|---------------------------------------------------------|--------|-----------------------------------------|-------------------------------|
| `ghcr.io/ufal/atrium-page-classification:<version>`     | `base` | `python3 /app/entrypoint.py` → `run.py` | the batch CLI                 |
| `ghcr.io/ufal/atrium-page-classification-api:<version>` | `api`  | `python -m service.api`                 | the HTTP service on port 8000 |

The `-api` suffix belongs to the image **name**: pull
`atrium-page-classification-api:<version>` for the service. An image built locally with Compose
carries its own local tag.

```bash
# batch, over ./data/input, writing to ./data/output
docker compose run --rm classify

# the HTTP service
docker compose --profile api up --build      # → http://localhost:8000/info
```

**On a GPU**, overlay the second compose file and rebuild against the CUDA wheel index:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm classify
#   build with: --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126
```

Volumes worth knowing: `./data:/data`, `./data/output:/app/result`, and the named
volumes `page-model:/app/model` and `hf-cache:/cache/huggingface` — the last one is what
stops every container start re-downloading the weights.

The container runs as non-root `atrium`, **uid 10001**. If the host directory you mount
is not writable by that uid, the run fails with `EACCES` before any inference happens.

!!! note "Exit code 143 is a clean stop, not a crash"
    The `api` stage sets `STOPSIGNAL SIGTERM` and drains for `GRACEFUL_SHUTDOWN_S`
    (default 20 s). A clean shutdown therefore exits **143** (128 + SIGTERM). Kubernetes
    and Compose both report that as a non-zero exit; it is the expected value.

## 4 · Run it as one stage of the pipeline

Each pipeline stage runs as its own container, and the document record passed between
them with `--document-json` / `--document-json-out` is the handoff. The hub's end-to-end
smoke workflow is the reference sequence; this is its page-classification stage:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -v "$PWD/hf-cache":/cache/huggingface \
  -e HF_TOKEN \
  ghcr.io/ufal/atrium-page-classification:latest \
  -f /workspace/work/input/CTX000000003-1.png \
  -m timm/regnety_160.swag_ft_in1k --hf \
  --document-json-out /workspace/work/doc_json/1_pc.json
```

`HF_TOKEN` is optional: public models need none, but anonymous Hugging Face downloads are
rate-limited, so automated runs should pass one. The `--document-json-out` flag is what
makes the stage write an ATRIUM document record for the next stage to accrete onto — see
[Pipelines](../../pipelines.md).

## 5 · Train or evaluate

```bash
python3 run.py --train                                     # config-driven training
python3 run.py --eval -rev v4.4                            # score one revision
python3 run.py --train --folds 5                           # 5-fold cross-validation, 80/10/10
python3 run.py --train --folds_csv folds.csv --fold_column fold1
python3 run.py --average -ap 'model_v4'                    # average existing fold weights
```

`--folds_csv` reproduces a model's *original* split rather than regenerating one — pages
absent from the CSV are excluded. Omit `--fold_column` and it is resolved per revision
from `REVISION_BEST_FOLDS`. The CSV is staged by the maintainer and is deliberately not
committed.

Hyperparameters live in `setup/config.txt` `[TRAIN]`: `epochs = 3`, `lr = 5e-5`,
`test_size = 0.1`, `max_categ = 14000`. Augmentation is colour jitter, sharpness and
Gaussian blur at 50 % each — **no rotation, reshaping or flipping**, because page
orientation is part of what the model is being asked to read.

Training data is a folder per category, named exactly as the 11 labels; the category
list is read from those folder names, so the tree must hold the category folders and
nothing else at that level. How a labelled tree is produced from a classified one is
described in [Pipelines → W12](../../pipelines.md#w12--annotation-round-trip-page-classifications-half).

## 6 · Use it from a coding agent

The `agent-skill` branch packages the HTTP service as an Agent Skill, so a coding agent can
classify a page or a PDF by calling the running service rather than reading this manual.
Installation and the contract it relies on are on the [Agent skills](../../agent-skills.md)
page.

## Troubleshooting

| Symptom                                                              | Cause                                                                                     | Fix                                                                             |
|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Container reports healthy but nothing can reach it                   | `HOST=127.0.0.1` binds inside the container only                                          | leave `HOST` unset (defaults to `0.0.0.0`)                                      |
| Every browser request is blocked, no error in the log                | `ALLOWED_ORIGINS` set to the **empty string** means "no origins"; *omitting* it means `*` | set it explicitly, or remove the line entirely                                  |
| Browser works from `localhost:8080` but not `127.0.0.1:8080`         | they are different origins to a browser                                                   | list both, as the compose default does                                          |
| `pip install` aborts with "No matching distribution found" for numpy | numpy ≥ 2.5 requires Python 3.12                                                          | stay on 3.11 and keep the `<2.5` pin; `dependabot.yml` already ignores the bump |
| Crash on meta device when loading a `timm` base                      | `transformers` 5.x has no meta kernel for these bases                                     | pin below 5.0 — `dependabot.yml` ignores that bump for the same reason          |
| First service call for a revision is slow                            | only the ensemble revisions `v1.4`–`v5.4` are loaded at start-up; others download on use  | request one of `v1.4`–`v5.4`, or accept one slow first call                     |
| `EACCES` writing results under Docker                                | host directory not writable by uid 10001                                                  | `chown 10001` the mounted directory, or mount one that is group-writable        |
| Container exits 143                                                  | clean SIGTERM drain                                                                       | expected; not a failure                                                         |

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `adee922`
(2026-09-23). This table records **provenance**, not a build instruction.

| Source                                                                 | What was taken from it                                          |
|------------------------------------------------------------------------|-----------------------------------------------------------------|
| `README.md` §§ How to install, How to run prediction, Data preparation | the install, invocation and conversion sequences; memory table  |
| `utils.py` (`doc_id_and_page`, `dataframe_results`)                    | the file-name convention and the result-table rows              |
| `result/tables/20260530-1220_model_v43_TOP-3.csv`                      | the sample rows                                                 |
| `data_scripts/unix/pdf2png.sh`, `data_scripts/windows/pdf2png.bat`     | PDF rasterisation options and defaults                          |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.gpu.yml`           | image targets, volumes, uid, healthcheck and shutdown behaviour |
| `setup/config.txt`                                                     | training and batching defaults                                  |
| `.env.example`                                                         | the `ALLOWED_ORIGINS` and `HOST` behaviour                      |
| `.github/dependabot.yml`                                               | the numpy and `transformers` ignore rules, and why they exist   |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`              | the pipeline-stage invocation                                   |
