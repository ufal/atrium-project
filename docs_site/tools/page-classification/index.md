---
title: page-classification
nav_order: 30
status: published
round: 7
issue: 57
repo: atrium-page-classification
role: index
---

# page-classification

<div class="atrium-pipeline" markdown="0">
<span class="here">page-classification</span>
<a href="https://ufal.github.io/atrium-alto-postprocess/">alto-postprocess</a>
<a href="../translator/">translator</a>
<a href="https://ufal.github.io/atrium-nlp-enrich/">nlp-enrich</a>
<a href="https://ufal.github.io/atrium-llm-enrich/">llm-enrich</a>
</div>

**Sorts a scanned page into one of 11 structural categories, so that a human — or a
script — can decide what should happen to it next.** A page of handwritten prose, a
photographic plate and a printed form all need different treatment; the classifier is
what tells them apart before any of that treatment is chosen.

It is an image classifier: fine-tuned vision models — Vision Transformers, RegNetY and
EfficientNetV2 — look at the whole page at once and return a probability for each
category. No text is read, so the language of the page does not matter.

It runs three ways: a batch CLI (`run.py`), a containerised HTTP service
(`POST /predict_image`, `POST /predict_document`), and an [Agent Skill](../../agent-skills.md)
that wraps the service. All three serve the same published models, one at a time or as a
five-model ensemble.

## What it takes in, what it hands on

|                         |                                                                                                                                                       |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                  | A page image (PNG or JPEG), or a PDF through the service — up to 50 pages, 10 MB                                                                      |
| **Out**                 | A Top-N CSV (`FILE, PAGE, CLASS-1…N, SCORE-1…N`), optionally a per-class raw-score CSV, a paradata JSON, and — when asked — an ATRIUM document record |
| **Owns in the record**  | The whole `page_categories` block, plus `pages[].category` and `pages[].category_confidence`                                                          |
| **Reads from upstream** | Nothing. It is the first stage; its input is the scan itself                                                                                          |

## Where it sits in the pipeline

page-classification is the first stage, and its categories **inform a routing decision**
rather than trigger one: which pages go to OCR, which to handwriting recognition, which
to table extraction, which to image extraction. That decision is made by a person or a
script reading the result tables. The next stage, `alto-postprocess`, works from OCR
output and does not read `page_categories`.

What travels between stages is the **record**. Each stage takes `--document-json` in,
writes only the block it owns, deep-copies everything else, and stamps
`assembled.blocks[<block>]` with its `program`, `run_id` and `paradata_ref`. See
[Pipelines](../../pipelines.md) for the file flow and the record flow drawn side by side.

!!! note "Who may write a block, and who did"
    `BLOCK_OWNERS` in the hub-canonical `atrium_document.py` says which program **may**
    write a block. To find out which program **did** write it in a given record, read
    `assembled.blocks[<block>].program`.

## The 11 categories

The set is built from three orthogonal criteria: **presence of graphical elements**
(drawings or photos), **type of text** (handwritten, printed, typed or mixed), and
**presence of a tabular / form layout**.

| Label     | What it is                                                                               |
|-----------|------------------------------------------------------------------------------------------|
| `DRAW`    | Drawings, maps, paintings, schematics or graphics, possibly with text labels or captions |
| `DRAW_L`  | The same, but inside a table-like layout, or with a legend formatted as a table          |
| `LINE_HW` | Handwritten text in a tabular or form-like structure                                     |
| `LINE_P`  | Printed text in a tabular or form-like structure                                         |
| `LINE_T`  | Machine-typed text in a tabular or form-like structure                                   |
| `PHOTO`   | Photographs or photographic cutouts, possibly with captions                              |
| `PHOTO_L` | Photos inside a table-like layout, or with tabular annotations                           |
| `TEXT`    | Mixtures of printed, handwritten and/or typed text, possibly with minor graphics         |
| `TEXT_HW` | Only handwritten text, in paragraph or block form (non-tabular)                          |
| `TEXT_P`  | Only printed text, in paragraph or block form (non-tabular)                              |
| `TEXT_T`  | Only machine-typed text, in paragraph or block form (non-tabular)                        |

**Reading a label.** The stem names the dominant content, the suffix qualifies it:

| Stem    | Meaning                 | Suffixes                                                                  |
|---------|-------------------------|---------------------------------------------------------------------------|
| `TEXT`  | running text            | `_HW` handwritten · `_P` printed · `_T` typewritten · none = a mixture    |
| `LINE`  | text in a table or form | `_HW` handwritten · `_P` printed · `_T` typewritten                       |
| `DRAW`  | drawings, maps, plans   | `_L` inside a table-like layout or with a tabular legend · none = free    |
| `PHOTO` | photographs             | `_L` inside a table-like layout or with tabular annotations · none = free |

**What each category suggests doing next.** The reason the categories exist is that each
calls for a different processing chain. The classifier does not route pages itself; this
is the decision its output is designed to support:

| Category            | Typical next step                                                           |
|---------------------|-----------------------------------------------------------------------------|
| `TEXT_P`, `TEXT_T`  | OCR for printed or typewritten text                                         |
| `TEXT_HW`           | handwritten text recognition (HTR)                                          |
| `TEXT`              | both — the page mixes printed, typed and handwritten text                   |
| `LINE_P`, `LINE_T`  | table or form extraction, with OCR for the cells                            |
| `LINE_HW`           | table or form extraction, with HTR for the cells                            |
| `DRAW`, `PHOTO`     | image extraction; captions, if any, through OCR                             |
| `DRAW_L`, `PHOTO_L` | image extraction plus table extraction for the surrounding layout or legend |

!!! note "The order is load-bearing, and each label has a URI"
    `model_registry.CATEGORIES` declares the labels in exactly the order of the first
    table above, and that order **is the label→index binding** every checkpoint was
    trained against: reordering it would silently relabel every prediction. The hub
    mirrors it in `docs/templates/shared/atrium_vocab.py` as `PAGE_CATEGORIES`.

    Each label also has a stable SKOS identifier —
    `https://w3id.org/atrium/page-category/TEXT_HW` and so on. Records carry the bare
    label; `model_registry.category_uri()` turns it into the URI. See
    [SKOS & the ATRIUM vocabulary](../../contracts/skos.md).

**There is deliberately no `enum` in the document schema for this field.**
`validate_document()` is a live output gate that raises, so an enum would turn a single
labelling slip into a stalled pipeline; the vocabulary registry reports an unknown label
instead of refusing it. Inference always uses the fixed `CATEGORIES` list; training and
evaluation read the category list from the folder names of the training tree.

## How a prediction is made

1. **Load and resize.** Each page image is resized to the model's square input — 224 or
   384 pixels, depending on the base model — and normalised with that base model's own
   mean and standard deviation. Nothing is cropped or rotated: page orientation and
   margins are part of what the model sees. The service first renders each page of a
   PDF at 300 dpi.
2. **Score.** The model produces one value per category; a softmax turns them into
   probabilities that sum to 1.
3. **Rank.** The `N` highest (`-tn`, default 3) become `CLASS-1…N` and `SCORE-1…N`,
   best first. `SCORE-1` is the model's confidence in its top answer.

**One model or five.** By default one model runs — the revision chosen with `-rev`, or a
local checkpoint. `--best` (and the service's `version=all`) runs all five models of the
canonical ensemble on every page and averages their scores: each model's Top-N
probabilities are summed per category and divided by five, and the result is re-ranked.
The run also records each model's own Top-1 vote, so disagreement stays visible.
`--average` is a different thing: it averages the **weights** of several fold checkpoints
of one base model into a single model, before any page is seen.

## The models

The fine-tuned models are published on Hugging Face as **revisions of one repository**,
[`ufal/vit-historical-page`](https://huggingface.co/ufal/vit-historical-page). A revision
is named `vX.Y`:

| `X` — model slot | Base model                               | Input  |
|------------------|------------------------------------------|--------|
| `v1.Y`           | `timm/tf_efficientnetv2_m.in21k_ft_in1k` | 384 px |
| `v2.Y`           | `google/vit-base-patch16-224`            | 224 px |
| `v3.Y`           | `google/vit-base-patch16-384`            | 384 px |
| `v4.Y`           | `timm/regnety_160.swag_ft_in1k`          | 384 px |
| `v5.Y`           | `google/vit-large-patch16-384`           | 384 px |

`Y` is the **generation** — which annotated data the model was trained on. Generations
`.0`–`.2` are the early, smaller annotation rounds (up to 14,270 pages), in which slots 1
and 4 held EfficientNetV2-S and EfficientNetV2-L; `.3` is the full 48,499-page dataset
with five-fold cross-validation; `.4` is the same five base models retrained on the
subset whose licence is CC BY-NC 4.0 (38,307 pages from 37,316 documents, against
`v*.3`'s 38,625 training pages from 37,328). **The canonical ensemble is `v1.4`–`v5.4`**,
and `v4.4` is the recommended single model: small, fast and the most accurate of its
generation.

Two alternatives sit beside the main line:

* **YOLO-cls** — `--yolo` swaps the Hugging Face models for an Ultralytics YOLO
  classification model (`--yolo_base`, e.g. `yv8s`). It is an option for training and
  inference with a different speed/accuracy trade-off, and it brings the AGPL-3.0 licence
  of Ultralytics into the run (see [Licence](#licence-and-how-it-is-computed)).
* **CLIP** — a separate, CLIP-based classifier for the same categories lives on the
  repository's `clip` branch, with its own Hugging Face repository.

## How well it works

Measured on the held-out evaluation split of the full dataset (4,823 pages), for the
`v*.3` generation:

| Base model                               | Revision | Top-1       | Top-3       | Note                     |
|------------------------------------------|----------|-------------|-------------|--------------------------|
| `timm/regnety_160.swag_ft_in1k`          | `v4.3`   | **99.16 %** | **100.0 %** | best, and small          |
| `google/vit-large-patch16-384`           | `v5.3`   | 99.12 %     | 99.94 %     | best of the large models |
| `google/vit-base-patch16-384`            | `v3.3`   | 98.92 %     | 99.98 %     |                          |
| `timm/tf_efficientnetv2_m.in21k_ft_in1k` | `v1.3`   | 98.83 %     | 99.78 %     |                          |
| `google/vit-base-patch16-224`            | `v2.3`   | 98.79 %     | 99.96 %     | smallest of the five     |

These five were chosen from a sweep of twelve base models — including the DiT family,
RegNetY-120 and -640, and EfficientNetV2-S and -L — all trained and tested on the same data.

!!! note "The `v*.4` generation"
    The figures above describe `v*.3`. The `v*.4` models — what `--best` and
    `version=all` use — are the same five base models trained the same way on the
    CC BY-NC 4.0 subset described above; [History](history.md#2026-06--08--retraining-on-the-licensed-dataset-15)
    records how the two generations compare.

Where the models do go wrong, it is mostly between neighbouring categories — `TEXT`
against `TEXT_T` above all, whose pages often look alike. Averaging fold models or
ensembling tends to raise overall accuracy, but can lower it on exactly those ambiguous
pairs.

## The data

**48,499 page images from 37,328 archival documents**, spanning 1920–2020 — archaeological
reports and related material from Czech archives, so drawings of pottery, arrowheads and
stones are common among the `DRAW` pages. The dataset and its annotation are published on
LINDAT under **CC BY-NC 4.0** at
[`hdl.handle.net/20.500.12800/1-6184`](http://hdl.handle.net/20.500.12800/1-6184);
`small_data_samples/` in the repository holds a few example pages per category.

The split is deterministic periodic sampling with a randomised offset, not a shuffle,
because pages of one kind arrive in clusters: per category, every *S*-th page — shifted by
a random amount within a quarter period — goes to the development and test sets, 10 %
each, and the rest to training. Five cross-validation folds repeat this with the seed
incremented per fold (`splitN ↔ foldN ↔ seed 420+(N−1)`). The `TEXT` category was capped
at `max_categ = 14000` pages because it otherwise dominates.

Peer-reviewed description: **[Page image classification for content-specific data
processing](https://arxiv.org/abs/2507.21114)** (arXiv 2507.21114).

## Licence, and how it is computed

Repository code is **MIT**. The licence of a *run*, though, is resolved from the
components that run actually touched, and recorded in the paradata:

* an inference or evaluation run resolves to **MIT**;
* `--train` pulls in the LINDAT dataset and resolves to **CC BY-NC 4.0**;
* `--yolo` adds Ultralytics, and an inference run with it resolves to **AGPL-3.0**.

See [Reference → Licence resolution](reference.md#licence-resolution).

## How to cite

Cite the paper for the method and the LINDAT record for the data:

* *Page image classification for content-specific data processing* —
  [arXiv:2507.21114](https://arxiv.org/abs/2507.21114)
* the training dataset — [`hdl.handle.net/20.500.12800/1-6184`](http://hdl.handle.net/20.500.12800/1-6184)
* the software — `CITATION.cff` in the repository, which GitHub renders as
  *Cite this repository*

## Where to go next

* **[Guide](guide.md)** — install it, prepare input, run it, read the output
* **[Reference](reference.md)** — every flag, every endpoint, every output column
* **[Changelog](changelog.md)** — the release history, grouped into arcs
* **[History](history.md)** — why it is shaped the way it is
* **[Workflow](../../workflows/page-classification.md)** — the workflow step by step, as its SSH Open Marketplace and Galaxy records describe it
* **[Pipelines](../../pipelines.md)** — where this stage sits, end to end
* **[External tools & services](../../external-tools.md)** — Hugging Face, LINDAT, ALTO, and the rest

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `adee922`
(2026-09-23), and from the hub's canonical documents. This table records **provenance**:
what this page was written from, not a build instruction.

| Source                                                                      | What was taken from it                                                        |
|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `README.md` §§ Goal, Versions, Model description, Data, Categories, Results | category definitions, generations, accuracy figures, dataset and split        |
| `model_registry.py`                                                         | the canonical label order, the revision → base-model map, the `v*.4` ensemble |
| `classifier.py`, `parallel_best.py`                                         | preprocessing, softmax scoring, ensemble averaging, fold-weight averaging     |
| `service/api.py`                                                            | the 300 dpi PDF rendering and the upload limits                               |
| `setup/para_config.txt`                                                     | the licence component table                                                   |
| `atrium-project/docs/templates/shared/atrium_document.py`                   | block ownership                                                               |
| `atrium-project/docs/document_schema.md`                                    | the write/read contract, the no-`enum` decision                               |
| `atrium-project/docs/templates/shared/atrium_vocab.py`                      | `PAGE_CATEGORIES` and the concept URIs                                        |
| `result/stats/model_accuracies_top1.csv`, `model_accuracies_top3.csv`       | the per-revision accuracy figures                                             |
