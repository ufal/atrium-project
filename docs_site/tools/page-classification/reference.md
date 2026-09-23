---
title: page-classification — Reference
nav_order: 32
status: published
round: 6
issue: 57
repo: atrium-page-classification
role: reference
---

# page-classification — Reference

Look something up and stop reading. Every value here is taken from the code; the files
it was read from are listed under [Sources](#sources). For what the tool is and how a
prediction is made, start at the [Overview](index.md).

## CLI — `run.py`

Defaults come from `setup/config.txt`, read before the parser is built. Flags written
`--x / --no-x` are `argparse.BooleanOptionalAction`: passing `--no-x` overrides a `true`
in the config file, which a bare `store_true` could not do.

### Input and output

| Flag                   | Default                        | What it does                                                                                                |
|------------------------|--------------------------------|-------------------------------------------------------------------------------------------------------------|
| `-f`, `--file`         | —                              | A single page image                                                                                         |
| `-d`, `--directory`    | —                              | A folder of unprocessed pages                                                                               |
| `--dir`                | off                            | Process the folder named in `[INPUT] FOLDER_INPUT` instead of passing `-d`                                  |
| `-ff`, `--file_format` | `png` (`[SETUP] files_format`) | Extension to collect from a directory                                                                       |
| `--inner / --no-inner` | `True` (`[SETUP] inner`)       | Recurse into nested folders                                                                                 |
| `--chunk / --no-chunk` | `False` (`[INPUT] chunking`)   | Write predictions in chunks of `[INPUT] chunk_size` (100), appending to the output file as the run proceeds |
| `-tn`, `--topn`        | `3` (`[SETUP] top_N`)          | How many categories to report. Validated at start-up: must be 1–11                                          |
| `--raw / --no-raw`     | `False` (`[SETUP] raw`)        | Also emit per-class scores for all 11 categories                                                            |

### Model selection

| Flag                 | Default                                                | What it does                                                                      |
|----------------------|--------------------------------------------------------|-----------------------------------------------------------------------------------|
| `-m`, `--model`      | `./model/model_<revision-without-dots>`                | Folder holding the model sub-folders                                              |
| `-b`, `--base`       | `timm/regnety_160.swag_ft_in1k` (`[SETUP] base_model`) | Base-model repository                                                             |
| `-rev`, `--revision` | —                                                      | Hugging Face revision: `main`, `vN.0` or `vN.M`                                   |
| `--hf / --no-hf`     | `False` (`[HF] use_hf`)                                | Take model and processor from the Hugging Face hub                                |
| `--yolo / --no-yolo` | `False` (`[YOLO] use_yolo`)                            | Use a YOLO-cls model instead of ViT/CNN — **overrides `--base` and `--revision`** |
| `--yolo_base`        | `yolov8s-cls.pt` (`[YOLO] yolo_base`)                  | Short tag (`yv8s`), an Ultralytics id, or a local `.pt` path                      |

### Ensemble

| Flag                   | Default | What it does                                                                                           |
|------------------------|---------|--------------------------------------------------------------------------------------------------------|
| `--best`               | off     | Run all five models of the canonical ensemble; the result is averaged into one Top-N CSV automatically |
| `--parallel`           | off     | Memory-aware grouped parallel execution for `--best`. **Requires CUDA**                                |
| `--no-average-best`    | off     | Skip the automatic averaging                                                                           |
| `--save-intermediates` | off     | Also keep each model's individual Top-N CSV                                                            |

### Training and evaluation

| Flag                       | Default                      | What it does                                                                                                                                                  |
|----------------------------|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--train / --no-train`     | `False` (`[TRAIN] Training`) | Train                                                                                                                                                         |
| `--eval / --no-eval`       | `False` (`[TRAIN] Testing`)  | Evaluate                                                                                                                                                      |
| `--folds`                  | `0` (`[TRAIN] cross_runs`)   | Number of cross-validation folds, 80/10/10 split                                                                                                              |
| `--folds_csv`              | `[TRAIN] folds_csv`          | Explicit folds CSV (`PNG` column + `foldN` columns holding `train`/`dev`/`test`). **Takes precedence over `--folds`**; pages absent from the CSV are excluded |
| `--fold_column`            | auto                         | Which fold column to read. Resolved per revision from `REVISION_BEST_FOLDS` when omitted                                                                      |
| `--average`                | off                          | Average existing fold weights                                                                                                                                 |
| `-ap`, `--average_pattern` | —                            | Which weights to average, e.g. `model_v4`                                                                                                                     |

### Document-record integration

| Flag                              | Default                            | What it does                                                |
|-----------------------------------|------------------------------------|-------------------------------------------------------------|
| `--document-json`                 | `[DOCUMENT] document_json`         | Baseline record, for a single-file run                      |
| `--document-json-out`             | `[DOCUMENT] document_json_out`     | Where to write the updated record                           |
| `--document-json-dir`             | `[DOCUMENT] document_json_dir`     | Baseline **directory**, for a batch run                     |
| `--document-json-out-dir`         | `[DOCUMENT] document_json_out_dir` | Output directory, one `<doc_id>.document.json` per document |
| `--strict-document-json / --no-…` | `False` (`[DOCUMENT] strict`)      | Turn ownership and schema warnings into errors              |

The adapter is **opt-in and a no-op** unless an output path or directory is set, on the
CLI or in the config.

## Configuration — `setup/config.txt`

| Section      | Keys as shipped                                                                                                                                                                          |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `[OUTPUT]`   | `FOLDER_RESULTS=./result` · `FOLDER_CPOINTS=./checkpoint` · `FOLDER_MODELS=./model`                                                                                                      |
| `[EVAL]`     | `FOLDER_PAGES=./small_data_samples`                                                                                                                                                      |
| `[TRAIN]`    | `FOLDER_PAGES=./small_data_samples` · `cross_runs=0` · `folds_csv=` · `test_size=0.1` · `log_step=100` · `epochs=3` · `lr=5e-5` · `max_categ=14000` · `Training=False` · `Testing=False` |
| `[SETUP]`    | `files_format=png` · `seed=420` · `base_model=timm/regnety_160.swag_ft_in1k` · `batch=16` · `top_N=3` · `raw=False` · `inner=True`                                                       |
| `[YOLO]`     | `use_yolo=False` · `yolo_base=yolov8s-cls.pt` · `yolo_imgsz=224` · `yolo_epochs=30` · `yolo_patience=20` · `yolo_lr0=0` · `yolo_dropout=0.1` · `yolo_cache=True`                         |
| `[INPUT]`    | `FOLDER_INPUT=./small_data_samples` · `chunk_size=100` · `chunking=False`                                                                                                                |
| `[HF]`       | `repo_name=ufal/vit-historical-page` · `token=` (read from `$HF_TOKEN`) · `use_hf=False` · `revision=main` · `latest=v4.4`                                                               |
| `[DOCUMENT]` | all four paths blank · `strict=False`                                                                                                                                                    |

`[HF] token` is deliberately blank in version control; the token is read from `$HF_TOKEN`
at run time. `[HF] latest` names the newest published single-model revision; `--best`
does not read it, because the ensemble is fixed in code (see
[The canonical ensemble](#the-canonical-ensemble)). `[YOLO]` configures the optional YOLO-cls
path (`yolo_imgsz`, the Ultralytics training schedule); `[DOCUMENT]` holds the defaults for
the five document-record flags above.

## HTTP service

Started by `python -m service.api`. Environment: `HOST` (`0.0.0.0`), `PORT` (`8000`),
`RELOAD` (`false`), `GRACEFUL_SHUTDOWN_S` (`20`), `LOG_LEVEL` (`INFO`), `ALLOWED_ORIGINS`,
`MAX_UPLOAD_MB` (`10`; the older `MAX_UPLOAD_BYTES` is still honoured as a fallback),
`HF_HOME`, `HF_TOKEN`. These are the ecosystem's shared service variables; the service
defines none of its own.

At start-up the service loads and warms the five models of the canonical ensemble
(`v1.4`–`v5.4`), off the event loop, before `/ready` reports `ready`. Any other revision
passed as `version` is resolved and downloaded on its first request.

| Method | Path                     | Returns                                                                                                                                                      |
|--------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET`  | `/`                      | a short JSON welcome message pointing at `/info`                                                                                                             |
| `GET`  | `/info`                  | `service`, `version`, `endpoints`, `limits` (`max_upload_mb: 10`, `max_pdf_pages: 50`), `categories` (all 11), `available_models` (`v1.4`…`v5.4` plus `all`) |
| `GET`  | `/health`                | `{"status":"ok"}`, always 200 — liveness, including while draining                                                                                           |
| `GET`  | `/health?deep=true`      | 503 with `status`, `detail`, `in_flight`, `draining` when degraded or draining                                                                               |
| `GET`  | `/ready`                 | 503 `starting` until warm-up completes → 200 `ready` → 503 `draining` after SIGTERM                                                                          |
| `POST` | `/predict_image`         | `ImageResponse`                                                                                                                                              |
| `POST` | `/predict_document`      | per-page predictions for a PDF                                                                                                                               |
| `GET`  | `/docs`, `/openapi.json` | FastAPI built-ins                                                                                                                                            |

A static browser interface is served at **`/frontend`**: upload an image or a PDF, pick a
model or the ensemble, and read the Top-N back.

### Request fields

Both prediction endpoints take the same multipart form:

| Field               | Type      | Default  | Notes                                                                                                        |
|---------------------|-----------|----------|--------------------------------------------------------------------------------------------------------------|
| `file`              | upload    | required | `/predict_image`: `content_type` must start `image/`. `/predict_document`: must be exactly `application/pdf` |
| `version`           | form      | `"all"`  | One of `v1.4`…`v5.4`, or `all` for the ensemble                                                              |
| `topn`              | form      | `3`      |                                                                                                              |
| `document_json`     | upload    | —        | Baseline ATRIUM record to accrete onto                                                                       |
| `document_json_out` | form bool | `False`  | Ask for the updated record in the response                                                                   |

### Response shapes

`POST /predict_image`:

```json
{ "type": "image",
  "predictions": [{"label": "TEXT_P", "score": 0.981}],
  "document_json": null,
  "document_json_schema_error": null }
```

`POST /predict_document` — one entry per PDF page, numbered from 1; `document_json` is
added only when a record was asked for:

```json
{ "type": "document",
  "pages": [{"page": 1, "predictions": [{"label": "DRAW", "score": 0.94}]}] }
```

From the command line:

```bash
curl -F file=@page.png -F version=v4.4 -F topn=3 http://localhost:8000/predict_image
curl -F file=@report.pdf -F version=all http://localhost:8000/predict_document
curl -F file=@page.png -F document_json=@record.json -F document_json_out=true \
     http://localhost:8000/predict_image         # accrete onto a baseline record
```

`service/api_client.py` wraps the same calls: `python3 service/api_client.py -f page.png -v v4.4 --top 3`.

`document_json_schema_error` is non-null only when an uploaded baseline failed to
validate and the record was emitted with a warning rather than refused — a field an
automated caller can test instead of grepping the service log.

### Errors

| Code  | When                                                                               |
|-------|------------------------------------------------------------------------------------|
| `400` | Wrong content type for the endpoint                                                |
| `413` | Over `MAX_UPLOAD_MB`, or a PDF with more than 50 pages                             |
| `422` | The uploaded `document_json` baseline is unparseable, or written by a newer schema |
| `500` | Inference failure, or the service's own output failed schema validation            |
| `503` | Draining after SIGTERM                                                             |

## The canonical ensemble

`--best`, `parallel_best.run_best_models` and the service's `version=all` all read one
dict, `REVISION_BEST_MODELS`. Since **v1.8.0-beta** it names the `v*.4` generation.

| Revision | Base model                               | Fold    | Resolution | Params (bytes) |
|----------|------------------------------------------|---------|------------|----------------|
| `v1.4`   | `timm/tf_efficientnetv2_m.in21k_ft_in1k` | `fold1` | 384        | 211,489,788    |
| `v2.4`   | `google/vit-base-patch16-224`            | `fold5` | 224        | 343,228,460    |
| `v3.4`   | `google/vit-base-patch16-384`            | `fold2` | 384        | 344,395,820    |
| `v4.4`   | `timm/regnety_160.swag_ft_in1k`          | `fold1` | 384        | 322,393,660    |
| `v5.4`   | `google/vit-large-patch16-384`           | `fold2` | 384        | 1,214,808,108  |

The fold rule is `splitN ↔ foldN column ↔ seed = 420 + (N−1)`. Resolution and parameter
size come from `MODEL_STATIC`, which `--parallel` reads to group models by memory before
running them.

`tests/test_best_ensemble_distinct.py` guards the ensemble: its static half asserts that
the five revisions name five distinct base models, and its `-m slow` half reads each
revision's `config.json` from the Hub and asserts the published architectures are
distinct too. The [changelog](changelog.md#v180-beta) records why that test exists.

### Two version namespaces, and where they collide

`REVISION_TO_BASE_MODEL` holds both, and reading it as one is the mistake:

* **Sweep numbering** — one number per candidate base model, as recorded in
  `model_accuracies_new.csv`: `v4.` = efficientnetv2_L, `v6.` = regnety_120,
  `v7.` = regnety_160, `v8.` = regnety_640, `v9.`/`v10.`/`v11.` = the DiT family,
  `v12.` = efficientnetv2_M.
* **Published numbering** — the five sweep winners, re-published under compact names:
  `v1.3` = efficientnetv2_m (sweep `v12.3.1`), `v2.3` = vit-base-224,
  `v3.3` = vit-base-384, `v4.3` = regnety_160 (sweep `v7.3.1`), `v5.3` = vit-large-384.

They **collide on `v1.3` and `v4.3`**. The published meaning wins, by exact-key-first
resolution rather than by ordering luck. `model_accuracies_new.csv` records the sweep
namespace; the Hugging Face model card and this site use the published one.

## Outputs and their columns

Written under `[OUTPUT] FOLDER_RESULTS` (default `./result`).

| File                                      | Columns                                                                                                                                                                         |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `{stamp}_{rev}_TOP-{N}.csv`               | `FILE, PAGE, CLASS-1…N, SCORE-1…N`. At `top_N == 1` a `CATEGORY` alias is **added**; `CLASS-1` and `SCORE-1` are kept, because the confidence is needed for the document record |
| `{stamp}_{rev}_RAW.csv`                   | `FILE, PAGE` followed by all 11 category columns, in canonical order                                                                                                            |
| `{stamp}_{n}_{rev}_TOP-{N}_EVAL.csv`      | as Top-N, plus `TRUE` (the gold label)                                                                                                                                          |
| `{stamp}_{n}_{rev}_EVAL_RAW.csv`          | raw per-class probabilities, plus `TRUE`                                                                                                                                        |
| `{stamp}_BEST_{n}_models_TOP-1.csv`       | `FILE, PAGE, CLASS-1-v1.4 … CLASS-1-v5.4` — one Top-1 column per model                                                                                                          |
| `{stamp}_BEST_{n}_models_AVG_TOP-{N}.csv` | `FILE, PAGE, V1.4 … V5.4, CLASS-1, SCORE-1, …` — probability-averaged. **Zero scores are emitted blank, and the paired `CLASS-K` is blanked too**                               |
| `{stamp}_{n}_{rev}_conf_mat_TOP-{N}.png`  | confusion matrix, 300 dpi                                                                                                                                                       |
| `{stamp}_{rev}_FOLD_{n}_DATASETS.txt`     | the train/dev/test split actually used                                                                                                                                          |
| `model/gpu_profile.json`                  | measured VRAM profile used by `--parallel` to group models                                                                                                                      |
| `{stamp}_page-classification.json`        | paradata — tool version, run id, resolved licence, config, statistics, skipped files                                                                                            |
| `<doc_id>.document.json`                  | the ATRIUM record, carrying `page_categories`, `pages[].category`, `pages[].category_confidence`                                                                                |
| `ro-crate-metadata.json`                  | RO-Crate 1.1 JSON-LD, from `atrium_rocrate.py`'s own CLI                                                                                                                        |

!!! info "RO-Crate export"
    `atrium_rocrate.py`, vendored from the hub, is a deterministic exporter — `@graph`
    sorted by `@id`, `datePublished` derived from the record's stamps rather than the
    clock — with `--document`, `--run`, `--paradata`, `--out-dir` and `--selftest`. It
    runs as a separate step over finished records. See
    [RO-Crate export](../../contracts/rocrate.md).

## Licence resolution

`setup/para_config.txt` declares the components; the paradata records what a given run
actually resolved to.

| Component        | Licence      | When it counts                   |
|------------------|--------------|----------------------------------|
| `vit_models`     | MIT          | always                           |
| `lindat_dataset` | CC BY-NC 4.0 | conditional — only when training |
| `ultralytics`    | AGPL-3.0     | conditional — only with `--yolo` |

So an inference or evaluation run is **MIT**; `--train` pulls in the LINDAT dataset and
the run resolves to **CC BY-NC 4.0** — non-commercial, not share-alike. A `--yolo` run adds
Ultralytics: an inference run with it resolves to **AGPL-3.0**, and with `--train` the
resolver ranks CC BY-NC 4.0 above it. The rule — the most restrictive component wins — is
the shared `para_licenses.py`, the same in every ATRIUM tool.

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `adee922`
(2026-09-23). This table records **provenance**, not a build instruction.

| Source                                   | What was taken from it                                  |
|------------------------------------------|---------------------------------------------------------|
| `run.py` (`build_parser`)                | the complete flag table and every default               |
| `setup/config.txt`                       | the configuration table                                 |
| `model_registry.py`                      | ensemble, folds, `MODEL_STATIC`, the two namespaces     |
| `service/api.py`, `service/inference.py` | limits, warm-up, response models, endpoints, errors     |
| `service/atrium_service.py`              | `/health`, `/ready` and the upload-limit resolution     |
| `service/api_client.py`                  | the client invocation                                   |
| `utils.py`, `parallel_best.py`           | the CSV column construction and the ensemble file names |
| `setup/para_config.txt`                  | licence components                                      |
