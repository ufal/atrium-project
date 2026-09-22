---
title: page-classification — Guide
nav_order: 31
status: published
round: 3
issue: 57
repo: atrium-page-classification
role: guide
---

# page-classification — Guide

Get it running — from a local checkout, from a container, or as one stage of the
pipeline — without reading the code. Every flag mentioned here is listed in full on the
[Reference](reference.md) page.

!!! warning "Clone the right branch"
    The default branch is **`vit`**, not `master`. `master` holds a 46-line index that
    points at the `vit` and `clip` variants; `clip` is a separate CLIP-based model with
    its own Hugging Face repository, and `agent-skill` is the Agent Skill packaging.
    `CONTRIBUTING.md` documents only `test` and `master`, which is a trap worth knowing
    about before you follow its branching instructions.

## 1 · Local install

Python **3.11** exactly — CI runs 3.11 across all six ATRIUM repositories, and numpy ≥ 2.5
requires 3.12, so a floating numpy pin breaks the install outright.

```bash
git clone https://github.com/ufal/atrium-page-classification.git
cd atrium-page-classification
python3 -m venv .venv && source .venv/bin/activate
pip install -r setup/requirements.txt
python3 run.py --hf          # pulls the model from the Hugging Face hub
```

There is no `pip install .` — the repository ships no `pyproject.toml` and no console
script. Every invocation is `python3 run.py` from the repository root.

`model/`, `result/` and `checkpoint/` are git-ignored runtime directories, created on
first run and mounted as volumes under Docker.

!!! danger "Pull a `v*.4` revision explicitly"
    The Hugging Face `main` branch still resolves to **`v4.3`**, the previous generation.
    `setup/config.txt` already points `[HF] latest` at `v4.4`, but `main` has not moved —
    so pass `-rev v4.4` (or `--best`, which reads the `v*.4` ensemble directly) until it
    does.

## 2 · Classify something

**One page:**

```bash
python3 run.py -f /full/path/to/page.png            # Top-3, printed to the console
python3 run.py -f /full/path/to/page.png -tn 1      # single best guess
python3 run.py -f /full/path/to/page.png --best     # all five models, averaged
```

**A directory** — note that you must either pass `-d` *or* pass `--dir` to use the
preset from `[INPUT] FOLDER_INPUT`; with neither, nothing happens at all:

```bash
python3 run.py -d /data/pages --inner                      # recurse into subfolders
python3 run.py --dir --inner --best                        # ensemble over the config default
python3 run.py --dir --inner --best --parallel             # memory-aware, CUDA only
python3 run.py --dir --inner --raw                         # per-class scores, all 11 columns
```

Directory processing runs in batches (`[SETUP] batch`, default 16). Above roughly half a
million files, simply *listing* the tree takes noticeable time before any inference
starts.

Results land in `[OUTPUT] FOLDER_RESULTS` (default `./result`) as timestamped CSVs —
see [Reference → Outputs](reference.md#outputs-and-their-columns) for the column schemas.

## 3 · Run it as a container

The README gives Docker three lines. Here is the whole picture.

Two images are published to GHCR from the same Dockerfile:

| Image                                                   | Stage  | Entry point                             | What it is                    |
|---------------------------------------------------------|--------|-----------------------------------------|-------------------------------|
| `ghcr.io/ufal/atrium-page-classification:<version>`     | `base` | `python3 /app/entrypoint.py` → `run.py` | the batch CLI                 |
| `ghcr.io/ufal/atrium-page-classification:<version>-api` | `api`  | `python -m service.api`                 | the HTTP service on port 8000 |

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

There is **no cross-service orchestration** in this ecosystem — no
`compose/docker-compose.pipeline.yml` exists. The only working end-to-end recipe is the
hub's CI workflow, and this is its page-classification stage, reproduced verbatim:

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

`HF_TOKEN` is optional but worth setting: anonymous Hugging Face pulls hit a 429 rate
limit in CI, which is why the workflow passes one. The `--document-json-out` flag is what
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

## Troubleshooting

The repository has no troubleshooting section and no FAQ. These are the failure modes
that are real, and where each one is actually decided.

| Symptom                                                              | Cause                                                                                     | Fix                                                                             |
|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Container reports healthy but nothing can reach it                   | `HOST=127.0.0.1` binds inside the container only                                          | leave `HOST` unset (defaults to `0.0.0.0`)                                      |
| Every browser request is blocked, no error in the log                | `ALLOWED_ORIGINS` set to the **empty string** means "no origins"; *omitting* it means `*` | set it explicitly, or remove the line entirely                                  |
| Browser works from `localhost:8080` but not `127.0.0.1:8080`         | they are different origins to a browser                                                   | list both, as the compose default does                                          |
| `pip install` aborts with "No matching distribution found" for numpy | numpy ≥ 2.5 requires Python 3.12                                                          | stay on 3.11 and keep the `<2.5` pin; `dependabot.yml` already ignores the bump |
| Crash on meta device when loading a `timm` base                      | `transformers` 5.x has no meta kernel for these bases                                     | pin below 5.0 — `dependabot.yml` ignores that bump for the same reason          |
| First service call stalls downloading weights                        | `api_client.py` defaults to `-v v4.3`, which is outside the warmed `v1.4`–`v5.4` set      | pass `-v v4.4`, or warm the version you intend to use                           |
| `EACCES` writing results under Docker                                | host directory not writable by uid 10001                                                  | `chown 10001` the mounted directory, or mount one that is group-writable        |
| Container exits 143                                                  | clean SIGTERM drain                                                                       | expected; not a failure                                                         |

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `8415ce7`
(2026-09-21). This table records **provenance**, not a build instruction.

| Source                                                               | What was taken from it                                                    |
|----------------------------------------------------------------------|---------------------------------------------------------------------------|
| `README.md` §§ How to install, How to run prediction, For developers | the install and invocation sequences                                      |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.gpu.yml`         | image targets, volumes, uid, healthcheck and shutdown behaviour           |
| `setup/config.txt`                                                   | training and batching defaults                                            |
| `.env.example`                                                       | the `ALLOWED_ORIGINS` and `HOST` traps, documented there and nowhere else |
| `.github/dependabot.yml`                                             | the numpy and `transformers` ignore rules, and why they exist             |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`            | Stage 1, reproduced verbatim                                              |
