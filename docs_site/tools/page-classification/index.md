---
title: page-classification
nav_order: 30
status: published
round: 3
issue: 57
repo: atrium-page-classification
role: index
---

# page-classification

<div class="atrium-pipeline" markdown="0">
<span class="here">page-classification</span>
<a href="https://ufal.github.io/atrium-alto-postprocess/">alto-postprocess</a>
<a href="../translator/index.md">translator</a>
<a href="https://ufal.github.io/atrium-nlp-enrich/">nlp-enrich</a>
<a href="https://ufal.github.io/atrium-llm-enrich/">llm-enrich</a>
</div>

**Sorts a scanned page into one of 11 structural categories, so that a human — or a
script — can decide what should happen to it next.** A page of handwritten prose, a
photographic plate and a printed form all need different treatment; the classifier is
what tells them apart before any of that treatment is chosen.

It runs three ways: a batch CLI (`run.py`), a containerised HTTP service
(`POST /predict_image`, `POST /predict_document`), and an Agent Skill that wraps the
service. All three read the same five-model ensemble.

## What it takes in, what it hands on

|                         |                                                                                                                                                       |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                  | A page image (PNG or JPEG), or a PDF through the service — up to 50 pages, 10 MB                                                                      |
| **Out**                 | A Top-N CSV (`FILE, PAGE, CLASS-1…N, SCORE-1…N`), optionally a per-class raw-score CSV, a paradata JSON, and — when asked — an ATRIUM document record |
| **Owns in the record**  | The whole `page_categories` block, plus `pages[].category` and `pages[].category_confidence`                                                          |
| **Reads from upstream** | Nothing. It is the first stage; its input is the scan itself                                                                                          |

## Where it sits in the pipeline — and the correction that matters

Every diagram in this ecosystem draws five boxes with arrows between them. For this
stage, that arrow does not exist as a file handoff.

!!! warning "page-classification → alto-postprocess is a human routing decision"
    `alto-postprocess` **never reads `page_categories`**. The only occurrences of that
    key in its tree are in the vendored schema files, i.e. deep-copy pass-through. The
    11 categories exist to *inform* the routing decision — which pages go to OCR, which
    to HTR, which to table extraction, which to image extraction — not to trigger it.

    What does travel is the **record**: each stage takes `--document-json` in, writes
    only the block it owns, deep-copies everything else, and stamps
    `assembled.blocks[<block>]` with its `program`, `run_id` and `paradata_ref`. See
    [Pipelines](../../pipelines.md) for both layers drawn out.

`BLOCK_OWNERS` in the hub-canonical `atrium_document.py` authorises **writes** only. To
find out who wrote a block in a *given* record, read
`assembled.blocks[<block>].program` — code that hardcodes a program name off the
ownership table is reading the wrong contract.

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

!!! note "The order is load-bearing, and each label has a URI"
    `model_registry.CATEGORIES` declares the labels in exactly the order above, and that
    order **is the label→index binding** used at training time. The hub mirrors it in
    `docs/templates/shared/atrium_vocab.py` as `PAGE_CATEGORIES`, which must stay in
    step.

    Each label also has a stable SKOS identifier —
    `https://w3id.org/atrium/page-category/TEXT_HW` and so on — minted through
    `model_registry.category_uri()`. **The tool's own README never mentions this.** See
    [SKOS & the ATRIUM vocabulary](../../contracts/skos.md).

**There is deliberately no `enum` in the document schema for this field.**
`validate_document()` is a live output gate that raises, and the tool derives its label
list from `sorted(os.listdir())` at run time — so an enum would convert a directory
naming slip into a stalled pipeline. The vocabulary registry reports instead of
refusing. Two consequences worth knowing: the schema's own
`page_categories.examples` used to be `{"1": "Text", "2": "Plate"}` — *neither is a
member of the set* — and `fixtures/atrium_document.example.json` still carries those
values today.

## How well it works

Measured on the held-out evaluation split, published in the tool's README:

| Base model                               | Revision | Top-1       | Top-3       | Note                                           |
|------------------------------------------|----------|-------------|-------------|------------------------------------------------|
| `timm/regnety_160.swag_ft_in1k`          | `v4.3`   | **99.16 %** | **100.0 %** | best and small — what `main` still resolves to |
| `google/vit-large-patch16-384`           | `v5.3`   | 99.12 %     | 99.94 %     | best of the large models                       |
| `google/vit-base-patch16-384`            | `v3.3`   | 98.92 %     | 99.98 %     |                                                |
| `timm/tf_efficientnetv2_m.in21k_ft_in1k` | `v1.3`   | 98.83 %     | 99.78 %     |                                                |
| `google/vit-base-patch16-224`            | `v2.3`   | 98.79 %     | 99.96 %     | smallest of the five                           |

!!! danger "These figures describe `v*.3`. The default ensemble is now `v*.4`."
    Since **v1.8.0-beta** `--best` and the service's `version=all` average the `v*.4`
    generation — the same five base models retrained on the CC BY-NC 4.0-only subset
    (38,307 pages / 37,316 PDFs, against `v*.3`'s 38,625 / 37,328). **No accuracy figures
    have been published for `v*.4`.** The one measurement that exists is a prediction
    diff: `v*.4` against `v*.3` disagreed on **24 of 229 samples**, all of them cases the
    `v*.3` ensemble was already ambiguous about. This is tracked as issue #48 in the tool
    repository, and until it closes the numbers above are the best available guide rather
    than a description of what you will run.

## The data

**48,499 page images from 37,328 archival documents**, spanning 1920–2020 — archaeological
reports and related material. Published on LINDAT under CC BY-NC-SA 4.0 at
[`hdl.handle.net/20.500.12800/1-6184`](http://hdl.handle.net/20.500.12800/1-6184).

The split is deterministic periodic sampling with a randomised offset, not a shuffle;
10 % test, five cross-validation folds with the seed incremented per fold
(`splitN ↔ foldN ↔ seed 420+(N−1)`). The `TEXT` category was capped at `max_categ = 14000`
because it otherwise dominates.

Peer-reviewed description: **[Page image classification for content-specific data
processing](https://arxiv.org/abs/2507.21114)** (arXiv 2507.21114).

## Licence, and how it is computed

Repository code is **MIT**. The licence of a *run*, though, is resolved from the
components that run actually touched, and recorded in the paradata:

* an inference or evaluation run resolves to **MIT**;
* `--train` pulls in the LINDAT dataset and resolves to **CC BY-NC-SA 4.0**.

## Where to go next

* **[Guide](guide.md)** — install it, run it, and the failure modes nobody wrote down
* **[Reference](reference.md)** — every flag, every endpoint, every output column
* **[Changelog](changelog.md)** — 27 releases, grouped by what actually changed
* **[History](history.md)** — why it is shaped the way it is
* **[Pipelines](../../pipelines.md)** — where this stage sits, end to end
* **[External tools & services](../../external-tools.md)** — Hugging Face, LINDAT, ALTO, and the rest

## Sources

Read from `ufal/atrium-page-classification` at branch **`vit`**, commit `8415ce7`
(2026-09-21), and from the hub's canonical documents. This table records **provenance**:
what this page was written from, not a build instruction.

| Source | What was taken from it |
|---|---|
| `README.md` §§ Versions, Model description, Categories, Results | category definitions, accuracy figures, dataset description |
| `model_registry.py:36-48, 150-200` | the canonical label order, the `v*.4` ensemble, the fold rule |
| `setup/para_config.txt` | the licence component table |
| `atrium-project/docs/templates/shared/atrium_document.py:108-118` | block ownership |
| `atrium-project/docs/document_schema.md:130-142, 438-452, 610-620` | the write/read contract, the no-`enum` decision, the two live defects |
| `atrium-project/docs/templates/shared/atrium_vocab.py:187, 283-295` | `PAGE_CATEGORIES` and the registry authority |
| `agent_dev_logs/digests/48.digest.md` | the open `v*.3` vs `v*.4` question |
