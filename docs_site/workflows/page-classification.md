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

*The page-classification workflow.* Tool section: [page-classification](https://github.com/ufal/atrium-page-classification/blob/test/README.md).

## Purpose

Archival documents mix typed reports, handwritten notes, printed forms, tables, drawings, maps
and photographs, and each kind of page needs a different treatment: OCR for printed or typed
text, handwritten text recognition for manuscripts, table extraction for forms, image
extraction for drawings and photographs. This workflow looks at every scanned page and
assigns it one of eleven categories, so that each page can be sent to the processing chain
that suits it before any of that processing is run. It works on the page image alone, so the
language of the page does not matter.

## At a glance

|                        |                                                                                                                                                                                                                                                                                                                           |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                 | page images (PNG, JPEG, TIFF or any format Pillow reads), one file per page, named `<document>-<page>` or `<document>_<page>`; or a PDF, which the command line and the HTTP service both render page by page                                                                                                             |
| **Out**                | a table of the top-ranked categories and their scores per page (CSV); optionally a table of all eleven scores; a paradata log (JSON); optionally the ATRIUM document record (JSON). The HTTP service answers in JSON, with the call's provenance                                                                          |
| **Runs as**            | a command-line tool (`run.py`); a container image, which also runs a Galaxy job script; an HTTP service image; an [Agent Skill](../agent-skills.md)                                                                                                                                                                       |
| **Compute**            | CPU is enough; a GPU makes large batches faster                                                                                                                                                                                                                                                                           |
| **Network**            | fetches the fine-tuned models from the Hugging Face Hub on first use, then works from its cache; or reads models staged once in a folder, offline (`--models-dir`)                                                                                                                                                        |
| **Code licence**       | MIT                                                                                                                                                                                                                                                                                                                       |
| **Component licences** | the code and the fine-tuned models are MIT; the LINDAT training dataset (CC BY-NC 4.0) is used only for training; the optional YOLO backend is AGPL-3.0; the service renders PDFs with pypdfium2 (Apache-2.0). These do not by themselves set the rights in the output: [Licences and paradata](../ecosystem/licences.md) |
| **Record**             | SSH Open Marketplace tool [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw)                                                                                                                                                                                                                          |

## Steps

| # | Step                    | What happens                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | In → out        | Activity    |
|---|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-------------|
| 1 | Prepare the page images | A PDF is rendered to one image per page with pypdfium2 at 300 dpi (`PDF_RENDER_DPI`), by the command line (`-f report.pdf`, or `-ff pdf` for a folder) and the HTTP service alike; `--pages` (`pages`) selects part of it. The bundled converters (`data_scripts/`: pdftoppm on Unix, ImageMagick with Ghostscript on Windows) remain for preparing training pages. Each image is named after its document and page number, `<document>-<page>.png`; the number after the last `-` or `_` becomes the page number in every result. | PDF → PNG, JPEG | Converting  |
| 2 | Choose the model        | One fine-tuned model — a named revision of `ufal/vit-historical-page` — or the five-model ensemble (`--best`, or `version=all`, the service's default), which averages the scores of revisions `v1.4`–`v5.4`: three Vision Transformers, a RegNetY and an EfficientNetV2. Naming a revision explicitly keeps results reproducible.                                                                                                                                                                                                 | —               | —           |
| 3 | Classify the pages      | Each image is resized to the model's input size, scored for all eleven categories, and the scores are turned into probabilities. The highest-ranked categories (three by default) are kept with their scores, best first. A single page, a folder or a whole tree can be processed.                                                                                                                                                                                                                                                | PNG, JPEG → CSV | Identifying |
| 4 | Review the results      | The result table gives each page's best category (`CLASS-1`) and its confidence (`SCORE-1`). A low top score with a close second marks a page worth a human look; the all-scores table and, with the ensemble, one vote per model make disagreement visible.                                                                                                                                                                                                                                                                       | CSV → CSV       | —           |
| 5 | Route the pages         | Each category calls for its own processing chain (table below). The classifier does not move pages itself: the decision is taken by a person or a script reading the result table.                                                                                                                                                                                                                                                                                                                                                 | CSV → —         | —           |
| 6 | Record provenance       | Every command-line run writes a paradata log with the tool version, run id, configuration, statistics, skipped files and the resolved licence; the HTTP service writes no file and returns the same record in its answer. On request the run also writes its block of the ATRIUM document record, which later pipeline stages build on.                                                                                                                                                                                            | → JSON          | —           |

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
[Overview](https://github.com/ufal/atrium-page-classification/blob/test/docs/reference/categories.md#definitions).

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
  with each component's licence.
* **A document record** (on request) — `page_categories` maps each page to its label, and every
  page carries its category and confidence, ready for the next stage to build on.

Every column is described in
[Reference → Outputs](https://github.com/ufal/atrium-page-classification/blob/test/docs/reference/outputs.md#the-files-a-run-writes).

## Limits

* **One category per page.** A page that combines, say, a photograph and running text gets the
  category of what dominates; the categories with the `_L` suffix and `TEXT` exist for the
  common mixtures.
* **Neighbouring categories are the hard cases.** Most errors fall between categories that look
  alike, `TEXT` and `TEXT_T` above all.
* **The categories come from one kind of archive.** They were formed from archival documents of
  1920–2020; pages of a very different kind are forced into the nearest category.
* **PDFs are rendered with a different engine.** The training pages were made with pdftoppm; the
  service and, since `v1.10.3-beta`, the command line use pypdfium2, which is about as close to
  pdftoppm in pixels as PyMuPDF, the engine it replaced. On 2,514 pages of 15 born-digital AMČR
  reports, pypdfium2 and PyMuPDF gave the same top-1 label on 2,509 pages; the other five moved to a
  neighbouring category. The tool's `data_scripts/pdf_rasteriser_comparison.md` holds the
  measurements.
* **A PDF request classifies at most 50 pages.** That is the default of `MAX_PDF_PAGES`; a longer
  PDF is refused (413) before any page is rendered, and the `pages` field classifies part of it
  instead. An upload is at most 10 MB by default (`MAX_UPLOAD_MB`). The command line has no such
  cap.
* **Truncated images.** The command-line tool classifies a truncated scan, its missing part
  filled grey; the HTTP service refuses it (422).
* **The ensemble can answer with fewer models.** If one of the five models fails, the others are
  averaged: in the service, and since `v1.12.0-beta` in the command line's `--best` too, which stopped
  before. Since `v1.9.10-beta` the answer's `models_used` lists the revisions that answered (per page for
  a PDF); the service log names the failing model, once, and the command line the models that answered.
  Before `v1.9.4-beta`, on a GPU node, every model fetched from the Hub failed this way.

## Provenance and licence

Each command-line run writes `<stamp>_page-classification.json`, the paradata log. The HTTP
service writes no file: each answer carries the same record in `paradata`, the call's RO-Crate
`CreateAction`. The paradata lists the components the run actually used, each with its licence,
as declared in the tool's `setup/para_config.txt`:

| Component                   | Licence      | Used when                                                              |
|-----------------------------|--------------|------------------------------------------------------------------------|
| code and fine-tuned models  | MIT          | always                                                                 |
| the LINDAT training dataset | CC BY-NC 4.0 | training (`--train`)                                                   |
| Ultralytics YOLO            | AGPL-3.0     | only with the optional YOLO backend                                    |
| pypdfium2 (PDFium)          | Apache-2.0   | a PDF is rendered (the service; the command line since `v1.10.3-beta`) |

The HTTP service renders PDF pages with pypdfium2 (Apache-2.0 or BSD-3-Clause) since `v1.9.1-beta`,
the command line since `v1.10.3-beta`; before that the service used PyMuPDF (AGPL-3.0), which was
not declared. The paradata also carries a computed label, the most restrictive of the licences
listed (MIT for a classification run). It is not the licence of the output: [Licences and
paradata](../ecosystem/licences.md).

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
| **Workflow inputs**           | a collection of page images — `png`, `jpg`, `tiff` — or a PDF                                                                                                                                                                                |
| **Parameters**                | model revision; single model or ensemble; how many categories to keep per page; for a PDF, which pages to classify                                                                                                                           |
| **Workflow outputs**          | Top-N table — `tabular` (CSV); all-scores table — `tabular` (CSV); paradata — `json`; document record — `json`                                                                                                                               |
| **Container**                 | `ghcr.io/ufal/atrium-page-classification:<version>` — the batch image (`run.py`); since `v1.10.5-beta` it runs the job script Galaxy hands it                                                                                                |
| **Compute**                   | CPU; a GPU destination speeds up large collections                                                                                                                                                                                           |
| **Network or reference data** | the weights staged on the server once (`run.py --hf --models-dir DIR`, a data table) and read offline; the Hugging Face Hub only as a fallback                                                                                               |
| **Scanned PDFs**              | rendered by the tool itself with pypdfium2 at 300 dpi (`PDF_RENDER_DPI`); `--pages` selects part of a PDF                                                                                                                                    |
| **Test data**                 | `small_data_samples/` in the tool repository — labelled page images, one folder per category, under CC BY-NC 4.0 (its `LICENSE`)                                                                                                             |
| **Credit**                    | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                                     |
| **Closest Galaxy tools**      | `image_learner` (image classification with the same model families, built for training); `doclayoutyolo` (a document-image model in its own container); Galaxy's shared `huggingface` data table, for staged model weights                   |

## Sources

Read from `ufal/atrium-page-classification` at release **`v1.12.0-beta`** (2026-10-29, branch
`test`; the default branch **`vit`** catches up when `test` is merged into it) and from this site's
page-classification section. Earlier readings were at `v1.10.5-beta` (2026-10-27) and `v1.9.5-beta` (2026-10-19). This table records
**provenance**, not a build instruction.

| Source                                                                                                                                                            | What was taken from it                                                                  |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `README.md` §§ Versions, Model description, Categories, How to run, Data preparation, Paradata logging                                                            | purpose, the category criteria, the step order, the converters                          |
| `run.py`, `page_inputs.py`, `model_registry.py`, `utils.py`, `setup/config.txt`                                                                                   | the classification steps, file naming, the ensemble, truncated scans                    |
| `service/api.py`, `service/pdf_render.py`, `service/inference.py`, `service/requirements.txt`                                                                     | the PDF route, its rendering library and limits; a truncated upload; a reduced ensemble |
| `service/README.md` (at `v1.12.0-beta`) §§ API Usage, Limits, Errors                                                                                              | the `pages` field, the limits and their settings, the call's `paradata`                 |
| `classifier.py` (`load_from_hub`), `atrium_paradata.py`, `atrium_rocrate.py` (`create_action`)                                                                    | Hub-loaded models on the device; the paradata log and its service form                  |
| `setup/para_config.txt`, `para_licenses.py`                                                                                                                       | the licence components and how they rank                                                |
| `data_scripts/pdf_rasteriser_comparison.md`, `data_scripts/unix/pdf2png.sh`, `data_scripts/windows/pdf2png.bat`                                                   | the renderers and how far apart they are; the AMČR label run                            |
| `Dockerfile`, `entrypoint.py`, `.dockerignore`                                                                                                                    | the two images and their entry points; no model weights inside                          |
| `small_data_samples/`                                                                                                                                             | test data and its licence                                                               |
| `CITATION.cff`                                                                                                                                                    | credit; the release date                                                                |
| `CONTRIBUTING.md` § Release History (`v1.8.0-beta`–`v1.10.5-beta`), § Branches; the repository's timeline (header); `.github/workflows/release.yml`, `docker.yml` | what changed since the last reading; the release branch                                 |
| the tool's `README.md`, `docs/reference/categories.md`, `docs/reference/outputs.md` (until 2026-10-25 the hub's `tools/page-classification/` pages)               | the category table, the outputs, the licence rule                                       |
| `DARIAH-ERIC/atrium-galaxy-tools`; `usegalaxy-eu/usegalaxy-eu-tools`; `goeckslab/gleam`; `bgruening/galaxytools`                                                  | the Galaxy analogues and conventions (read at `v1.8.0-beta`, not re-read)               |
