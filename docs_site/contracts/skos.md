---
title: SKOS & the ATRIUM vocabulary
nav_order: 8
status: partial
round: 6
issue: 57
---

# SKOS & the ATRIUM vocabulary

How ATRIUM names its controlled labels with stable identifiers, what the `page-category`
vocabulary contains in full, and how page-classification and the translator use it.

!!! info "Scope"
    The registry holds six vocabularies; one of them belongs to page-classification, and the
    translator uses none. The other five belong to alto-postprocess and nlp-enrich.
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

!!! note "Identifiers first, locators second"
    An ATRIUM URI is a stable **identifier**: records and crates can use it whether or not
    anything answers at that address. Making it a resolvable **locator** is a matter of a
    `w3id.org` redirect to a published copy of the registry, which changes no data and no
    code.

In Turtle, as `python atrium_vocab.py --turtle` writes it, one concept reads:

```turtle
a-page-category:TEXT_HW rdf:type skos:Concept ;
    skos:definition "only handwritten text in paragraph or block form (non-tabular)"@en ;
    skos:inScheme atrium-scheme:page-category ;
    skos:notation "TEXT_HW" ;
    skos:prefLabel "TEXT_HW"@en .
```

## The six vocabularies at a glance

| Scheme              | Concepts | Authority                                              | Record field                                        |
|---------------------|----------|--------------------------------------------------------|-----------------------------------------------------|
| **`page-category`** | **11**   | page-classification — `model_registry.py` `CATEGORIES` | `page_categories`, `pages[].category`               |
| `line-category`     | 7        | alto-postprocess and digital-convert                   | `lines[].categ`                                     |
| `quality-band`      | 3        | alto-postprocess                                       | `pages[].quality_band`                              |
| `entity-type`       | 4        | nlp-enrich                                             | `entities[].type_teitok`                            |
| `cnec`              | 28       | nlp-enrich (CNEC 2.0)                                  | `entities[].type_cnec`                              |
| `theme`             | 11       | nlp-enrich's taxonomy                                  | `enrichment.items[].teater_category`, via the facet |

**The translator appears in none of them** — see [below](#the-translator-and-its-glossary).

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

## How page-classification uses it

`model_registry.CATEGORIES` is the authority: the tool writes exactly those eleven strings.
When `model_registry.py` is imported, it compares `CATEGORIES` with the registry's
`page-category` labels and prints a note if the two sets ever differ; it never changes
`CATEGORIES` and never stops a run. Training and evaluation, which read the category list from
the folder names of the training tree, do the same comparison for that tree.

Records carry the bare label. To get from a label to its concept:

```python
from atrium_vocab import concept_uri, validate_labels

concept_uri("page-category", "TEXT_HW")
# 'https://w3id.org/atrium/page-category/TEXT_HW'
validate_labels("page-category", ["TEXT", "Text", "Plate"])
# reports that "Text" differs from TEXT only in case, and that "Plate" is not in the scheme
```

`validate_labels()` reports rather than raises — the same advisory stance as the missing
`enum` in the [schema](schemas.md#page_categories--written-by-page-classification).
`model_registry.category_uri(label)` is the tool's own shortcut for `concept_uri`.

## The translator and its glossary

The translator does **not** import `atrium_vocab` and writes no field that carries a scheme. Its
controlled vocabulary is something else: a **translation glossary**,
`data_samples/vocabulary.csv`, with five columns — `source_lemma,target_translation,source,source_id,uri`
— harvested by `load_vocab.py` from AMCR (over OAI-PMH) and TEATER (over GraphQL). The
`source_id` and `uri` columns point back at the source vocabulary's own concept — for example
`https://api.aiscr.cz/id/HES-000497` for AMCR's *(polo)zemnice*, "pit house" — so a protected
term stays traceable without ATRIUM minting a URI for it. The glossary protects terms during
translation; it does not label anything in the record. See
[translator → Guide](../tools/translator/guide.md#6--use-the-vocabulary).

## "`broader` means two things"

`skos_strategy.md` §5.2 records a modelling decision about the **source** vocabularies: AMCR's
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

| Source                                                                                                       | What was taken from it                                                                                                        |
|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `atrium-project/docs/templates/shared/atrium_vocab.py` — run, not only read                                  | `SKOS_BASE`, the minting rules, the six schemes, the concepts and collections, the Turtle excerpt, `validate_labels()` output |
| `atrium-project/docs/skos_strategy.md` §§0, 5.2, 6, 7                                                        | the design decisions                                                                                                          |
| `atrium-page-classification@vit` `adee922` — `model_registry.py`, `utils.py`                                 | the authority list, the advisory comparison, `category_uri`                                                                   |
| `atrium-translator@master` `71feaef` — `load_vocab.py`, `data_samples/vocabulary.csv`, `processors/vocab.py` | the glossary, its columns and its harvester                                                                                   |
