---
title: page-classification workflow
nav_order: 15
status: published
round: 7
issue: 57
repo: atrium-page-classification
role: workflow
authored: true
---

# Sorting archive pages for content-specific processing

*The page-classification workflow.* Tool section: [page-classification](../tools/page-classification/index.md).

## Purpose

Archival documents mix typed reports, handwritten notes, printed forms, tables, drawings, maps
and photographs, and each kind of page needs a different treatment: OCR for printed or typed
text, handwritten text recognition for manuscripts, table extraction for forms, image
extraction for drawings and photographs. This workflow looks at every scanned page and
assigns it one of eleven categories, so that each page can be sent to the processing chain
that suits it before any of that processing is run. It works on the page image alone, so the
language of the page does not matter.

## At a glance

|                    |                                                                                                                                                                                                                                                  |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | page images (PNG or JPEG), one file per page, named `<document>-<page>` or `<document>_<page>`; a scanned PDF is split into page images first, or sent whole to the HTTP service                                                                 |
| **Out**            | a table of the top-ranked categories and their scores per page (CSV); optionally a table of all eleven scores; a paradata log (JSON); optionally the ATRIUM document record (JSON). The HTTP service answers in JSON, with the call's provenance |
| **Runs as**        | a command-line tool (`run.py`); a container image; an HTTP service image, which also accepts a PDF; an [Agent Skill](../agent-skills.md)                                                                                                         |
| **Compute**        | CPU is enough; a GPU makes large batches faster                                                                                                                                                                                                  |
| **Network**        | fetches the fine-tuned models from the Hugging Face Hub on first use, then works from its cache                                                                                                                                                  |
| **Code licence**   | MIT                                                                                                                                                                                                                                              |
| **Output licence** | computed per run: classifying and evaluating resolve to MIT, a PDF classified by the service included; training on the published dataset to CC BY-NC 4.0                                                                                         |
| **Record**         | SSH Open Marketplace tool [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw)                                                                                                                                                 |

## Steps

| # | Step                    | What happens                                                                                                                                                                                                                                                                                                                                                                                               | In → out        | Activity    |
|---|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-------------|
| 1 | Prepare the page images | Scanned PDFs are rendered to one image per page with the bundled converter (`data_scripts/`: pdftoppm on Unix, ImageMagick with Ghostscript on Windows, 300 dpi by default). Each image is named after its document and page number, `<document>-<page>.png`; the number after the last `-` or `_` becomes the page number in every result. The HTTP service renders a PDF's pages itself, with pypdfium2. | PDF → PNG, JPEG | Converting  |
| 2 | Choose the model        | One fine-tuned model — a named revision of `ufal/vit-historical-page` — or the five-model ensemble (`--best`, or `version=all`, the service's default), which averages the scores of revisions `v1.4`–`v5.4`: three Vision Transformers, a RegNetY and an EfficientNetV2. Naming a revision explicitly keeps results reproducible.                                                                         | —               | —           |
| 3 | Classify the pages      | Each image is resized to the model's input size, scored for all eleven categories, and the scores are turned into probabilities. The highest-ranked categories (three by default) are kept with their scores, best first. A single page, a folder or a whole tree can be processed.                                                                                                                        | PNG, JPEG → CSV | Identifying |
| 4 | Review the results      | The result table gives each page's best category (`CLASS-1`) and its confidence (`SCORE-1`). A low top score with a close second marks a page worth a human look; the all-scores table and, with the ensemble, one vote per model make disagreement visible.                                                                                                                                               | CSV → CSV       | —           |
| 5 | Route the pages         | Each category calls for its own processing chain (table below). The classifier does not move pages itself: the decision is taken by a person or a script reading the result table.                                                                                                                                                                                                                         | CSV → —         | —           |
| 6 | Record provenance       | Every command-line run writes a paradata log with the tool version, run id, configuration, statistics, skipped files and the resolved licence; the HTTP service writes no file and returns the same record in its answer. On request the run also writes its block of the ATRIUM document record, which later pipeline stages build on.                                                                    | → JSON          | —           |

**What each category suggests doing next:**

| Category            | Typical next step                                                           |
|---------------------|-----------------------------------------------------------------------------|
| `TEXT_P`, `TEXT_T`  | OCR for printed or typewritten text                                         |
| `TEXT_HW`           | handwritten text recognition (HTR)                                          |
| `TEXT`              | both — the page mixes printed, typed and handwritten text                   |
| `LINE_P`, `LINE_T`  | table or form extraction, with OCR for the cells                            |
| `LINE_HW`           | table or form extraction, with HTR for the cells                            |
| `DRAW`, `PHOTO`     | image extraction; captions, if any, through OCR                             |
| `DRAW_L`, `PHOTO_L` | image extraction plus table extraction for the surrounding layout or legend |

The labels themselves, and how the models were trained, are on the tool's
[Overview](../tools/page-classification/index.md#the-11-categories).

**Two side workflows** use the same tool: training and evaluating a model on one's own
labelled pages ([Pipelines → W8](../pipelines.md#w8--training-and-evaluation-page-classification)),
and turning PDFs into a labelled training set and corrections back into it
([Pipelines → W12](../pipelines.md#w12--annotation-round-trip-page-classifications-half)).

## What you get

* **A routing decision per page** — the Top-N table (`FILE, PAGE, CLASS-1…N, SCORE-1…N`), one row
  per page, best guess first. The HTTP service gives the same per page in JSON.
* **Evidence for review** — the all-scores table, and, with the command-line ensemble, each
  model's own vote.
* **A provenance record** — the paradata log of the run, or the `paradata` of a service answer,
  with the licence it resolved to.
* **A document record** (on request) — `page_categories` maps each page to its label, and every
  page carries its category and confidence, ready for the next stage to build on.

Every column is described in
[Reference → Outputs](../tools/page-classification/reference.md#outputs-and-their-columns).

## Limits

* **One category per page.** A page that combines, say, a photograph and running text gets the
  category of what dominates; the categories with the `_L` suffix and `TEXT` exist for the
  common mixtures.
* **Neighbouring categories are the hard cases.** Most errors fall between categories that look
  alike, `TEXT` and `TEXT_T` above all.
* **The categories come from one kind of archive.** They were formed from archival documents of
  1920–2020; pages of a very different kind are forced into the nearest category.
* **The command-line tool reads images, not PDFs.** PDFs are rendered first (step 1); the HTTP
  service accepts a PDF directly and renders it itself.
* **The service renders PDFs with a different engine.** The training pages were made with
  pdftoppm; the service uses pypdfium2, which is about as close to pdftoppm in pixels as PyMuPDF,
  the engine it replaced. On 2,514 pages of 15 born-digital AMČR reports, pypdfium2 and PyMuPDF
  gave the same top-1 label on 2,509 pages; the other five moved to a neighbouring category. The
  tool's `data_scripts/pdf_rasteriser_comparison.md` holds the measurements.
* **A PDF request classifies at most 50 pages.** That is the default of `MAX_PDF_PAGES`; a longer
  PDF is refused (413) before any page is rendered, and the `pages` field classifies part of it
  instead. An upload is at most 10 MB by default (`MAX_UPLOAD_MB`).
* **Truncated images.** The command-line tool classifies a truncated scan, its missing part
  filled grey; the HTTP service refuses it (422).
* **The ensemble can answer with fewer models.** If one of the five models fails, the service
  averages the others. The answer does not say so; the service log does, once per failing
  model. Before `v1.9.4-beta`, on a GPU node, every model fetched from the Hub failed this way.

## Provenance and licence

Each command-line run writes `<stamp>_page-classification.json`, the paradata log. The HTTP
service writes no file: each answer carries the same record in `paradata`, the call's RO-Crate
`CreateAction`. The licence of the run is computed from the components it actually used, as
declared in the tool's `setup/para_config.txt`; the most restrictive one wins:

| Component                   | Licence      | Counts when                         |
|-----------------------------|--------------|-------------------------------------|
| code and fine-tuned models  | MIT          | always                              |
| the LINDAT training dataset | CC BY-NC 4.0 | training (`--train`)                |
| Ultralytics YOLO            | AGPL-3.0     | only with the optional YOLO backend |
| pypdfium2 (PDFium)          | Apache-2.0   | the service renders an uploaded PDF |

The HTTP service renders PDF pages with pypdfium2 (Apache-2.0 or BSD-3-Clause) since
`v1.9.1-beta`. Apache-2.0 ranks with MIT, so a classified PDF still resolves to MIT. Before
that the service used PyMuPDF, which is AGPL-3.0 and was not declared.

In the [document record](../ecosystem/document-contract.md) the tool owns the
`page_categories` block and each page's `category` and `category_confidence`.

## Where it sits

* **First stage** of the scanned-document pipeline — [Pipelines → W1](../pipelines.md#w1--scanned--ocr-document-pipeline).
  Its output informs a routing decision; the next stage works from the OCR output.
* **Page classification** step of the AMČR text workflow
  [`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP).
* Also used in [W4](../pipelines.md#w4--containerised-service--api-workflow) (as a service),
  [W5](../pipelines.md#w5--agent-skill-workflow) (from a coding agent),
  [W6](../pipelines.md#w6--e2e-smoke-the-integration-contract) (the end-to-end test),
  [W8](../pipelines.md#w8--training-and-evaluation-page-classification) and
  [W12](../pipelines.md#w12--annotation-round-trip-page-classifications-half).

## On other platforms

**SSH Open Marketplace.** Tool record [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw).
The model is published on the Hugging Face Hub as
[`ufal/vit-historical-page`](https://huggingface.co/ufal/vit-historical-page), the training data
at LINDAT as [`hdl:20.500.12800/1-6184`](http://hdl.handle.net/20.500.12800/1-6184), and the
method in [arXiv:2507.21114](https://arxiv.org/abs/2507.21114).

**Galaxy sheet.**

|                               |                                                                                                                                                                                                                                              |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**           | a collection of page images — `png`, `jpg`                                                                                                                                                                                                   |
| **Parameters**                | model revision; single model or ensemble; how many categories to keep per page; for a PDF, which pages to classify                                                                                                                           |
| **Workflow outputs**          | Top-N table — `tabular` (CSV); all-scores table — `tabular` (CSV); paradata — `json`; document record — `json`                                                                                                                               |
| **Container**                 | `ghcr.io/ufal/atrium-page-classification-api:<version>` — the service image (`POST /predict_image`, `POST /predict_document`)                                                                                                                |
| **Compute**                   | CPU; a GPU destination speeds up large collections                                                                                                                                                                                           |
| **Network or reference data** | the Hugging Face Hub, for the model weights — or the weights staged on the server beforehand                                                                                                                                                 |
| **Scanned PDFs**              | sent to `POST /predict_document` as they are (rendered with pypdfium2 at 300 dpi, at most 50 pages per request or per `pages` selection; set by `PDF_RENDER_DPI` and `MAX_PDF_PAGES`), or converted to page images by a step before this one |
| **Test data**                 | `small_data_samples/` in the tool repository — labelled page images, one folder per category, under CC BY-NC 4.0 (its `LICENSE`)                                                                                                             |
| **Credit**                    | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                     |
| **Closest Galaxy tools**      | `image_learner` (image classification with the same model families, built for training); `doclayoutyolo` (a document-image model in its own container); Galaxy's shared `huggingface` data table, for staged model weights                   |

## Sources

Read from `ufal/atrium-page-classification` at release **`v1.9.5-beta`** (2026-10-19; its code is
that of `v1.9.4-beta`, commit `d0fac40` on the default branch **`vit`**) and from this site's
page-classification section. This table records **provenance**, not a build instruction.

| Source                                                                                                                                                            | What was taken from it                                                                  |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `README.md` §§ Versions, Model description, Categories, How to run, Data preparation, Paradata logging                                                            | purpose, the category criteria, the step order, the converters                          |
| `run.py`, `model_registry.py`, `utils.py`, `setup/config.txt`                                                                                                     | the classification steps, file naming, the ensemble, truncated scans                    |
| `service/api.py`, `service/pdf_render.py`, `service/inference.py`, `service/requirements.txt`                                                                     | the PDF route, its rendering library and limits; a truncated upload; a reduced ensemble |
| `service/README.md` (at `v1.9.4-beta`) §§ API Usage, Limits, Errors                                                                                               | the `pages` field, the limits and their settings, the call's `paradata`                 |
| `classifier.py` (`load_from_hub`), `atrium_paradata.py`, `atrium_rocrate.py` (`create_action`)                                                                    | Hub-loaded models on the device; the paradata log and its service form                  |
| `setup/para_config.txt`, `para_licenses.py`                                                                                                                       | the licence components and how they rank                                                |
| `data_scripts/pdf_rasteriser_comparison.md`, `data_scripts/unix/pdf2png.sh`, `data_scripts/windows/pdf2png.bat`                                                   | the renderers and how far apart they are; the AMČR label run                            |
| `Dockerfile`, `.dockerignore`                                                                                                                                     | the two images and their entry points; no model weights inside                          |
| `small_data_samples/`                                                                                                                                             | test data and its licence                                                               |
| `CITATION.cff`                                                                                                                                                    | credit; the release date                                                                |
| `CONTRIBUTING.md` § Release History (`v1.8.0-beta`–`v1.9.4-beta`), § Branches; `agent_dev_logs/DEVLOG.md` (header); `.github/workflows/release.yml`, `docker.yml` | what changed since the last reading; the release branch                                 |
| `atrium-project/docs_site/tools/page-classification/index.md`, `reference.md`                                                                                     | the category table, the outputs, the licence rule                                       |
| `DARIAH-ERIC/atrium-galaxy-tools`; `usegalaxy-eu/usegalaxy-eu-tools`; `goeckslab/gleam`; `bgruening/galaxytools`                                                  | the Galaxy analogues and conventions (read at `v1.8.0-beta`, not re-read)               |
