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

|                    |                                                                                                                                                                                    |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**             | page images (PNG or JPEG), one file per page, named `<document>-<page>`; scanned PDFs are split into page images first                                                             |
| **Out**            | a table of the top-ranked categories and their scores per page (CSV); optionally a table of all eleven scores; a paradata log (JSON); optionally the ATRIUM document record (JSON) |
| **Runs as**        | a command-line tool (`run.py`); a container image; an HTTP service image, which also accepts a PDF; an [Agent Skill](../agent-skills.md)                                           |
| **Compute**        | CPU is enough; a GPU makes large batches faster                                                                                                                                    |
| **Network**        | fetches the fine-tuned models from the Hugging Face Hub on first use, then works from its cache                                                                                    |
| **Code licence**   | MIT                                                                                                                                                                                |
| **Output licence** | computed per run: classifying and evaluating resolve to MIT; training on the published dataset to CC BY-NC 4.0                                                                     |
| **Record**         | SSH Open Marketplace tool [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw)                                                                                   |

## Steps

| # | Step                    | What happens                                                                                                                                                                                                                                                                        | In → out        | Activity    |
|---|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-------------|
| 1 | Prepare the page images | Scanned PDFs are rendered to one image per page with the bundled converter (`data_scripts/`). Each image is named after its document and page number, `<document>-<page>.png`; the number after the last separator becomes the page number in every result.                         | PDF → PNG, JPEG | Converting  |
| 2 | Choose the model        | One fine-tuned model — a named revision of `ufal/vit-historical-page` — or the five-model ensemble (`--best`), which averages the scores of a Vision Transformer, RegNetY and EfficientNetV2 models. Naming a revision explicitly keeps results reproducible.                       | —               | —           |
| 3 | Classify the pages      | Each image is resized to the model's input size, scored for all eleven categories, and the scores are turned into probabilities. The highest-ranked categories (three by default) are kept with their scores, best first. A single page, a folder or a whole tree can be processed. | PNG, JPEG → CSV | Identifying |
| 4 | Review the results      | The result table gives each page's best category (`CLASS-1`) and its confidence (`SCORE-1`). A low top score with a close second marks a page worth a human look; the all-scores table and, with the ensemble, one vote per model make disagreement visible.                        | CSV → CSV       | —           |
| 5 | Route the pages         | Each category calls for its own processing chain (table below). The classifier does not move pages itself: the decision is taken by a person or a script reading the result table.                                                                                                  | CSV → —         | —           |
| 6 | Record provenance       | Every run writes a paradata log with the tool version, run id, configuration, statistics, skipped files and the resolved licence. On request the run also writes its block of the ATRIUM document record, which later pipeline stages build on.                                     | → JSON          | —           |

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
  per page, best guess first.
* **Evidence for review** — the all-scores table, and, with the ensemble, each model's own vote.
* **A provenance record** — the paradata log of the run, with the licence it resolved to.
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

## Provenance and licence

Each run writes `<stamp>_page-classification.json`, the paradata log. The licence of the run
is computed from the components it actually used, as declared in the tool's
`setup/para_config.txt`; the most restrictive one wins:

| Component                   | Licence      | Counts when                         |
|-----------------------------|--------------|-------------------------------------|
| code and fine-tuned models  | MIT          | always                              |
| the LINDAT training dataset | CC BY-NC 4.0 | training (`--train`)                |
| Ultralytics YOLO            | AGPL-3.0     | only with the optional YOLO backend |

The HTTP service renders PDF pages with PyMuPDF, which is licensed AGPL-3.0.

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

|                               |                                                                                                                                                                                                                            |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workflow inputs**           | a collection of page images — `png`, `jpg`                                                                                                                                                                                 |
| **Parameters**                | model revision; single model or ensemble; how many categories to keep per page                                                                                                                                             |
| **Workflow outputs**          | Top-N table — `tabular` (CSV); all-scores table — `tabular` (CSV); paradata — `json`; document record — `json`                                                                                                             |
| **Container**                 | `ghcr.io/ufal/atrium-page-classification:<version>` — the command-line image                                                                                                                                               |
| **Compute**                   | CPU; a GPU destination speeds up large collections                                                                                                                                                                         |
| **Network or reference data** | the Hugging Face Hub, for the model weights — or the weights staged on the server beforehand                                                                                                                               |
| **Scanned PDFs**              | converted to page images by a step before this one                                                                                                                                                                         |
| **Test data**                 | `small_data_samples/` in the tool repository — labelled page images, one folder per category                                                                                                                               |
| **Credit**                    | the authors in the tool's `CITATION.cff`, with their ORCIDs; licence MIT                                                                                                                                                   |
| **Closest Galaxy tools**      | `image_learner` (image classification with the same model families, built for training); `doclayoutyolo` (a document-image model in its own container); Galaxy's shared `huggingface` data table, for staged model weights |

## Sources

Read from `ufal/atrium-page-classification` at release **`v1.8.0-beta`** (branch **`vit`**,
commit `adee922`) and from this site's page-classification section. This table records
**provenance**, not a build instruction.

| Source                                                                                                           | What was taken from it                                         |
|------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| `README.md` §§ Model description, Categories, How to run, Data preparation                                       | purpose, the category criteria, the step order                 |
| `run.py`, `model_registry.py`, `utils.py`                                                                        | the classification steps, file naming, the ensemble            |
| `setup/para_config.txt`                                                                                          | the licence components                                         |
| `service/api.py`, `service/requirements.txt`                                                                     | the PDF route of the HTTP service and its rendering library    |
| `Dockerfile`                                                                                                     | the two images and their entry points; no model weights inside |
| `small_data_samples/`                                                                                            | test data                                                      |
| `CITATION.cff`                                                                                                   | credit                                                         |
| `atrium-project/docs_site/tools/page-classification/*`                                                           | the category table, the outputs, the licence rule              |
| `DARIAH-ERIC/atrium-galaxy-tools`; `usegalaxy-eu/usegalaxy-eu-tools`; `goeckslab/gleam`; `bgruening/galaxytools` | the Galaxy analogues and conventions                           |
