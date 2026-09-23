---
title: SKOS & the ATRIUM vocabulary
nav_order: 8
status: partial
round: 4
issue: 57
---

# SKOS & the ATRIUM vocabulary

How ATRIUM names its controlled labels with stable identifiers, what the `page-category`
vocabulary contains in full, and what page-classification and the translator actually do with it.

!!! info "Written for page-classification and translator"
    The registry holds six vocabularies; one of them belongs to page-classification, and the
    translator uses none. The other five are described with their owners' sections.
    [`docs/skos_strategy.md`](https://github.com/ufal/atrium-project/blob/main/docs/skos_strategy.md)
    is the normative text.

## What SKOS is doing here

SKOS — the W3C's *Simple Knowledge Organization System* — is a small RDF vocabulary for writing
down a controlled list: each term is a `skos:Concept` with a stable URI, a label, and a place in a
`skos:ConceptScheme`. ATRIUM uses it for one purpose: **so that a bare string in a record — `TEXT_HW`
in `page_categories` — can be resolved to one unambiguous, documented concept.**

It is an internal alignment framework, and deliberately modest:

* **Nothing is published.** No external service is contacted, and no vocabulary registration is a
  prerequisite for any of it.
* **No namespace was requested.** A request for a DARIAH vocabulary namespace was set aside as a
  long-horizon item; using SKOS to align the data internally was judged worth doing without it.
* **Source vocabularies keep their own URIs.** AMCR and TEATER already mint resolvable identifiers,
  and ATRIUM does not re-mint them.
* **ATRIUM mints URIs only for what it authors** — and roots them all in one constant, so the day a
  real namespace exists, one line changes.

The registry is `atrium_vocab.py`, one of the [17 shared files](../ecosystem/architecture.md#what-is-canonical-and-what-is-vendored),
vendored byte-identically into both documented tools.

## How a URI is minted

```text
SKOS_BASE = https://w3id.org/atrium/

scheme      https://w3id.org/atrium/scheme/<scheme>
concept     https://w3id.org/atrium/<scheme>/<notation>
collection  https://w3id.org/atrium/<scheme>/collection/<name>
```

The notation is kept **case-preserving** — letters, digits, `_` and `.` survive; any other run of
characters becomes one `-`. So:

|                | URI                                                        |
|----------------|------------------------------------------------------------|
| the scheme     | `https://w3id.org/atrium/scheme/page-category`             |
| one concept    | `https://w3id.org/atrium/page-category/TEXT_HW`            |
| one collection | `https://w3id.org/atrium/page-category/collection/tabular` |

!!! note "These URIs do not resolve yet"
    `w3id.org/atrium` has not been registered — it is an optional follow-up that blocks nothing.
    The URIs are stable **identifiers** today; they become resolvable **locators** only once the
    redirect exists.

## The six vocabularies at a glance

| Scheme              | Concepts | Authority                                              | Record field                                        |
|---------------------|----------|--------------------------------------------------------|-----------------------------------------------------|
| **`page-category`** | **11**   | page-classification — `model_registry.py` `CATEGORIES` | `page_categories`, `pages[].category`               |
| `line-category`     | 7        | alto-postprocess and digital-convert                   | `lines[].categ`                                     |
| `quality-band`      | 3        | alto-postprocess                                       | `pages[].quality_band`                              |
| `entity-type`       | 4        | nlp-enrich                                             | `entities[].type_teitok`                            |
| `cnec`              | 28       | nlp-enrich (CNEC 2.0)                                  | `entities[].type_cnec`                              |
| `theme`             | 11       | nlp-enrich's taxonomy                                  | `enrichment.items[].teater_category`, via the facet |

64 concepts in all; the module's own docstring says "~90". **The translator appears in none of
them** — see [below](#the-translator-and-its-glossary).

## `page-category`, in full

The eleven concepts, in the order `model_registry.CATEGORIES` declares them. **The order is
load-bearing**: it is the label-to-index binding the models were trained with, and the registry's
`PAGE_CATEGORIES` must match it exactly.

| Notation  | URI                       | Definition                                                                                              |
|-----------|---------------------------|---------------------------------------------------------------------------------------------------------|
| `DRAW`    | `…/page-category/DRAW`    | drawings, maps, paintings, schematics, or graphics, potentially containing some text labels or captions |
| `DRAW_L`  | `…/page-category/DRAW_L`  | drawings, etc but presented within a table-like layout or includes a legend formatted as a table        |
| `LINE_HW` | `…/page-category/LINE_HW` | handwritten text organized in a tabular or form-like structure                                          |
| `LINE_P`  | `…/page-category/LINE_P`  | printed text organized in a tabular or form-like structure                                              |
| `LINE_T`  | `…/page-category/LINE_T`  | machine-typed text organized in a tabular or form-like structure                                        |
| `PHOTO`   | `…/page-category/PHOTO`   | photographs or photographic cutouts, potentially with text captions                                     |
| `PHOTO_L` | `…/page-category/PHOTO_L` | photos presented within a table-like layout or accompanied by tabular annotations                       |
| `TEXT`    | `…/page-category/TEXT`    | mixtures of printed, handwritten, and/or typed text, potentially with minor graphical elements          |
| `TEXT_HW` | `…/page-category/TEXT_HW` | only handwritten text in paragraph or block form (non-tabular)                                          |
| `TEXT_P`  | `…/page-category/TEXT_P`  | only printed text in paragraph or block form (non-tabular)                                              |
| `TEXT_T`  | `…/page-category/TEXT_T`  | only machine-typed text in paragraph or block form (non-tabular)                                        |

Each concept's `prefLabel` is its notation.

### Facets are collections, not a hierarchy

The categories cut across three independent criteria — graphical content, kind of text, tabular
layout — so they do not form a tree. The registry says so by modelling each criterion as a
`skos:Collection`, which states membership without implying that one concept is *narrower* than
another:

| Collection    | Label                               | Members                                                |
|---------------|-------------------------------------|--------------------------------------------------------|
| `graphical`   | carries graphical elements          | `DRAW` · `DRAW_L` · `PHOTO` · `PHOTO_L` · `TEXT`       |
| `tabular`     | laid out as a table, form or legend | `DRAW_L` · `LINE_HW` · `LINE_P` · `LINE_T` · `PHOTO_L` |
| `handwritten` | contains handwritten text           | `LINE_HW` · `TEXT` · `TEXT_HW`                         |
| `printed`     | contains printed text               | `LINE_P` · `TEXT` · `TEXT_P`                           |
| `typed`       | contains machine-typed text         | `LINE_T` · `TEXT` · `TEXT_T`                           |

There is no `skos:broader` anywhere in the scheme and no top concept. `TEXT` belongs to four
collections — it is the one mixed category — and `PHOTO` and `DRAW` belong to `graphical` only.

## What page-classification actually does with it

Less than the design suggests. Read from the code at `vit` @ `8c98a3d`:

| Mechanism                                                                              | Status                                                           |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `model_registry.category_uri(label)` — turns a label into its concept URI              | **defined, never called**                                        |
| `atrium_vocab.validate_labels()` — reports unknown or mis-cased labels without raising | **never called** on the labels the tool emits                    |
| an import-time comparison of `CATEGORIES` against the scheme's labels                  | runs — the one live check                                        |
| a drift warning in `collect_images()`                                                  | runs, but only for `--train` and `--eval`, which write no record |

So an unknown label would reach a record unreported. The registry *would* catch it — run by hand,
`validate_labels("page-category", ["TEXT", "Text", "Plate"])` answers that `Text` differs from
`TEXT` only in case and that `Plate` is not in the scheme — but nothing on the inference path calls
it. Records carry bare labels, not URIs; a consumer that wants the URI builds it with
`concept_uri("page-category", label)`.

!!! note "Defect V-2 is fixed"
    `skos_strategy.md`'s defect **V-2** — `collect_images()` derived its categories with
    `sorted(os.listdir(directory))`, so a stray file in a training tree shifted every class index,
    and the shipped `small_data_samples/LICENSE` stopped a run with `NotADirectoryError` — is fixed,
    and follow-up **F2** records it. The function now keeps only sub-directories, hidden ones
    excluded, and three tests in `TestCollectImages` pin it, one of them on the shipped sample tree.
    The drift warning in the table above still runs, for the case a filter cannot catch: a stray or
    missing category *directory*.

## The translator and its glossary

The translator does **not** import `atrium_vocab` and writes no field that carries a scheme. Its
controlled vocabulary is something else: a **translation glossary**,
`data_samples/vocabulary.csv`, with two columns — `source_lemma,target_translation` — and 5,087
rows, harvested by `load_vocab.py` from AMCR (over OAI-PMH) and TEATER (over GraphQL). The glossary
protects terms during translation; it does not label anything in the record. See
[translator → Guide](../tools/translator/guide.md#6--use-the-vocabulary).

`skos_strategy.md` records work on that harvester which the code at `master` @ `88242fe` does not
contain:

| `skos_strategy.md` says                                                   | At `master` @ `88242fe`                                                           |
|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| F3: `load_vocab.py` gained a `--from-flat DIR` option                     | no such option — the flags are `--out`, `--delay`, `--skip-amcr`, `--skip-teater` |
| F3: the committed CSV was regenerated as 5 columns and 4,952 rows         | 2 columns, 5,087 rows                                                             |
| V-3: the `main()` / CLI the README documents "does not exist in the file" | it exists — `main()` with an `argparse` interface                                 |

## "`broader` means two things"

`skos_strategy.md` §5.2 is its best-known finding: in the **source** vocabularies, AMCR's
`hierarchie_vyse` edges all cross from one scheme to another and so become `skos:related`, while
TEATER's `broader` edges stay within one scheme and become real `skos:broader`. That concerns the
vocabularies nlp-enrich builds from AMCR and TEATER. **It does not touch `page-category`**, which
asserts no `broader` at all.

## Getting the vocabulary

```bash
python atrium_vocab.py --jsonld           # the whole registry as JSON-LD
python atrium_vocab.py --turtle           # … or as Turtle
python atrium_vocab.py --labels page-category
python atrium_vocab.py --selftest
```

Run from either tool's checkout, where the file sits at the repository root. The JSON-LD output is
what [`atrium_vocab.schema.json`](schemas.md#atrium_vocabschemajson) describes.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                                                                       | What was taken from it                                                                                                  |
|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_vocab.py` — run, not only read                                  | `SKOS_BASE`, the minting rules, the six schemes, the page-category concepts and collections, `validate_labels()` output |
| `atrium-project/docs/skos_strategy.md` §§0, 5.2, 6, 7                                                        | the design decisions and the defect / follow-up status, compared against the code                                       |
| `atrium-page-classification@vit` `8c98a3d` — `model_registry.py`, `utils.py:126-215`, `run.py:385-413`       | what page-classification calls and does not call                                                                        |
| `atrium-translator@master` `88242fe` — `load_vocab.py`, `data_samples/vocabulary.csv`, `processors/vocab.py` | the glossary and its harvester                                                                                          |
