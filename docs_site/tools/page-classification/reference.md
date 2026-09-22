---
title: page-classification — Reference
nav_order: 32
status: published
round: 3
issue: 57
repo: atrium-page-classification
role: reference
---

# page-classification — Reference

Look something up and stop reading. Every value here was read out of the code at
`vit` / `8415ce7`, not out of the prose — where the two disagree, the disagreement is
recorded under [Known drift](#known-drift--read-this-before-trusting-a-number).

## CLI — `run.py`

Defaults come from `setup/config.txt`, read before the parser is built. Flags written
`--x / --no-x` are `argparse.BooleanOptionalAction`: passing `--no-x` overrides a `true`
in the config file, which a bare `store_true` could not do.

### Input and output

| Flag                   | Default                        | What it does                                                                  |
|------------------------|--------------------------------|-------------------------------------------------------------------------------|
| `-f`, `--file`         | —                              | A single page image                                                           |
| `-d`, `--directory`    | —                              | A folder of unprocessed pages                                                 |
| `--dir`                | off                            | Process the folder named in `[INPUT] FOLDER_INPUT` instead of passing `-d`    |
| `-ff`, `--file_format` | `png` (`[SETUP] files_format`) | Extension to collect from a directory                                         |
| `--inner / --no-inner` | `True` (`[SETUP] inner`)       | Recurse into nested folders                                                   |
| `--chunk / --no-chunk` | `False` (`[INPUT] chunking`)   | Write predictions in chunks of `[INPUT] chunk_size` (100) as the run proceeds |
| `-tn`, `--topn`        | `3` (`[SETUP] top_N`)          | How many categories to report. Validated at start-up: must be 1–11            |
| `--raw / --no-raw`     | `False` (`[SETUP] raw`)        | Also emit per-class scores for all 11 categories                              |

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

None of these five appear in the tool's README.

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

The `[YOLO]` and `[DOCUMENT]` sections are documented **nowhere** in the repository's own
prose. `[HF] token` is deliberately blank in version control; the token is read from the
environment at run time.

## HTTP service

Started by `python -m service.api`. Environment: `HOST` (`0.0.0.0`), `PORT` (`8000`),
`RELOAD` (`false`), `GRACEFUL_SHUTDOWN_S` (`20`), `LOG_LEVEL` (`INFO`), `ALLOWED_ORIGINS`,
`MAX_UPLOAD_MB`, `HF_HOME`, `HF_TOKEN`. Beyond that shared table the service layer reads
**no** environment at all — few deployment knobs, which is a fact rather than a gap.

| Method | Path                     | Returns                                                                                                                                                      |
|--------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET`  | `/`                      | `{"message": "Welcome to the ATRIUM Page Classification API. Use /info for available models."}`                                                              |
| `GET`  | `/info`                  | `service`, `version`, `endpoints`, `limits` (`max_upload_mb: 10`, `max_pdf_pages: 50`), `categories` (all 11), `available_models` (`v1.4`…`v5.4` plus `all`) |
| `GET`  | `/health`                | `{"status":"ok"}`, always 200                                                                                                                                |
| `GET`  | `/health?deep=true`      | 503 with `status`, `detail`, `in_flight`, `draining` when degraded or draining                                                                               |
| `GET`  | `/ready`                 | 503 `starting` → 200 `ready` → 503 `draining` on SIGTERM                                                                                                     |
| `POST` | `/predict_image`         | `ImageResponse`                                                                                                                                              |
| `POST` | `/predict_document`      | per-page predictions for a PDF                                                                                                                               |
| `GET`  | `/docs`, `/openapi.json` | FastAPI built-ins                                                                                                                                            |

The browser frontend is mounted at **`/frontend`**, not at `/`.

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

```json
// POST /predict_image
{ "type": "image",
  "predictions": [{"label": "TEXT_P", "score": 0.981}],
  "document_json": null,
  "document_json_schema_error": null }

// POST /predict_document
{ "type": "document",
  "pages": [{"page": 1, "predictions": [{"label": "DRAW", "score": 0.94}]}] }
```

`document_json_schema_error` is non-null only when an uploaded baseline failed to
validate and the record was emitted with a warning rather than refused — a field an
automated caller can test instead of grepping the service log.

### Errors

| Code  | When                                                                               |
|-------|------------------------------------------------------------------------------------|
| `400` | Wrong content type for the endpoint                                                |
| `413` | Over `MAX_UPLOAD_BYTES`, or a PDF with more than 50 pages                          |
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

The fold rule is `splitN ↔ foldN column ↔ seed = 420 + (N−1)`.

!!! note "`MODEL_STATIC` states the contract, not what the Hub serves"
    Those `params_bytes` mirror the `v*.3` row of the same base model. Between
    2026-09-13 and 2026-09-16 **all five `v*.4` revisions served the same
    `regnety_160` checkpoint** — 322,925,148 bytes on every one of them. `--best` would
    have averaged one model with itself five times, returned well-formed predictions and
    still reported "Ensemble (Average of 5 Models)". Nothing would have raised.
    `tests/test_best_ensemble_distinct.py` is the standing guard; its `-m slow` half reads
    each revision's `config.json` from the Hub, and it is the half to run before ever
    moving these keys again.

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
resolution rather than by ordering luck. `model_accuracies_new.csv` is therefore *not*
stale and must not be "corrected" — it is a faithful record of the sweep namespace.

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

!!! info "RO-Crate export is real, and documented nowhere in the repository"
    `atrium_rocrate.py` ships a deterministic exporter — `@graph` sorted by `@id`,
    `datePublished` derived from block stamps rather than the clock — with
    `--document`, `--run`, `--paradata`, `--out-dir` and `--selftest`. Neither `README.md`
    nor `CONTRIBUTING.md` mentions it. See [RO-Crate export](../../contracts/rocrate.md).

## Licence resolution

`setup/para_config.txt` declares the components; the paradata records what a given run
actually resolved to.

| Component        | Licence      | When it counts                   |
|------------------|--------------|----------------------------------|
| `vit_models`     | MIT          | always                           |
| `deepdoctection` | Apache-2.0   | conditional                      |
| `lindat_dataset` | CC BY-NC 4.0 | conditional — only when training |

So an inference or evaluation run is **MIT**; `--train` pulls in the LINDAT dataset and
the run resolves to **CC BY-NC-SA 4.0**. (The dataset is published as CC BY-NC-**SA** 4.0;
`para_config.txt` spells it CC BY-NC 4.0, which is the third spelling in the repository
and is noted below.)

## Known drift — read this before trusting a number

Each item was confirmed against the code at `vit` / `8415ce7`. These are reported here,
not fixed here; each is a candidate issue in the tool's own repository.

**Numbers that disagree with themselves**

1. `v4.2` and `v5.2` accuracies are **swapped** between the table (`README.md:690-691`)
   and the prose that discusses it (`:720`, `:740`).
2. `v4.3` is stated as **98.92 %** in the Top-1 table and **99.16 %** in the prose at
   `README.md:781`. The registry and `model_accuracies_top1.csv` agree on 99.16.
3. `regnety_160` is listed at **224 px** in the README's base-model table and in the
   Acknowledgements; `MODEL_STATIC` says **384**.
4. The Versions table names `v1.2`'s base as `efficientnetv2_s.in21k` and `v4.2`'s as
   `efficientnetv2_l`; the published `v1.3`/`v1.4` are `efficientnetv2_m` and
   `v4.3`/`v4.4` are `regnety_160`. The "strange order of base model versions" is
   acknowledged in the README and never resolved — the two namespaces above are the
   explanation.
5. **No accuracy figures exist for the `v*.4` models that `--best` now uses.** Every
   published number describes `v*.3`.

**Defaults that are not what the prose says**

6. `--file_format` is documented as defaulting to `jpeg`; the config ships `png`, and
   that is what argparse uses.
7. `api_client.py` defaults to `-v v4.3`, which is not in the service's
   `AVAILABLE_VERSIONS` (`v1.4`–`v5.4`). It resolves, but outside the warmed set — so the
   first call downloads.
8. `setup/setup_api_service.sh` downloads `v1.3`–`v5.3`, not the `v*.4` ensemble the
   service serves, and ends by suggesting `uvicorn service.api:app --reload` while the
   published image runs `python -m service.api`. The two treat `RELOAD` differently.

**Documented shapes that the code does not return**

9. `service/README.md`'s `/predict_image` examples show `model_version` and
   `requested_topn`. `ImageResponse` declares neither, and FastAPI's `response_model`
   **filters unknown keys**, so they are never returned.
10. `GET /` is documented as serving the static interface; it returns a JSON welcome
    message. The interface is at `/frontend`.

**Stale paths and links**

11. The README links `supplement_scripts/…` in five places; the directory is
    `supplementary/scripts/`.
12. The paradata example link points at a file that is not in the repository.
13. The tree diagram lists `result/stats/model_accuracies.csv` and two plots; the real
    files are `model_accuracies_top1.csv` and `model_accuracies_top3.csv`, and the plots
    do not exist.
14. `.gitignore` contains `/chekcpoint/` — a typo — so the real `checkpoint/` directory is
    **not** ignored.
15. The `transformers` 5.x caution ends mid-sentence, without naming the exception.

**Things that exist but are unwritten**

16. YOLO support — `yolo_classifier.py`, `--yolo`, `--yolo_base` and the whole `[YOLO]`
    config section — has **zero** mentions in `README.md` or `CONTRIBUTING.md`, though the
    parser's own description says "Page sorter based on ViT / YOLO-cls".
17. `--chunk` / `--no-chunk` and `[INPUT] chunk_size` are undocumented, and they change the
    output-writing path to append mode.
18. All five `--document-json*` flags and `[DOCUMENT]` are undocumented on the CLI side.
19. RO-Crate export and the SKOS registry — 45 KB and 49 KB of code respectively — have no
    README mention.
20. `README.html` (178 KB, git-tracked, one commit stale) sits at the repository root with
    no stated generator. **This site is the HTML documentation; that file is not.**

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `8415ce7`
(2026-09-21). This table records **provenance**, not a build instruction.

| Source                                              | What was taken from it                                             |
|-----------------------------------------------------|--------------------------------------------------------------------|
| `run.py:36-219` (`build_parser`)                    | the complete flag table and every default                          |
| `setup/config.txt`                                  | the configuration table                                            |
| `model_registry.py:36-48, 94-119, 150-217`          | ensemble, folds, `MODEL_STATIC`, the two namespaces                |
| `service/api.py:50-58, 150-166, 226-330`            | limits, response models, endpoints, errors                         |
| `utils.py:95-125`                                   | the CSV column construction                                        |
| `setup/para_config.txt`                             | licence components                                                 |
| `README.md`, `service/README.md`, `CONTRIBUTING.md` | compared against the above; disagreements listed under Known drift |
