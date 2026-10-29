---
title: Glossary
nav_order: 20
status: published
issue: 79
---

# Glossary

The words these pages use, explained in a sentence or two each. Each entry links to the page that holds
the full description. Tools, models, standards and institutions have longer entries on
[External tools & services](external-tools.md).

| Term                        | Meaning                                                                                                                                                                                                                   |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **accretion**               | How the record grows. Each stage adds its own block and passes every other block on unchanged ([The document contract](ecosystem/document-contract.md)).                                                                  |
| **actionable workflow**     | A workflow on the SSH Open Marketplace that can also be run. In ATRIUM it runs as a [Galaxy](external-tools.md#galaxy) workflow.                                                                                          |
| **AIS CR**                  | The Archaeological Information System of the Czech Republic, the infrastructure behind AMČR and TEATER, at `aiscr.cz` ([more](external-tools.md#ais-cr--aiscrcz)).                                                        |
| **ALTO**                    | An XML format for OCR output. It keeps every word with its position on the page image ([more](external-tools.md#alto-xml)).                                                                                               |
| **AMČR**                    | The Archaeological Map of the Czech Republic (*Archeologická mapa České republiky*): the national archaeological database of ARÚP and ARÚB, and the partner that runs the ATRIUM pilot.                                   |
| **ARÚP, ARÚB**              | The Institutes of Archaeology of the Czech Academy of Sciences in Prague and in Brno. They hold the collections the tools were built for ([more](external-tools.md#arúp-and-arúb)).                                       |
| **block**                   | One top-level part of the record, written by exactly one tool: `page_categories`, `lines`, `translations` and so on.                                                                                                      |
| **born-digital**            | A document created on a computer, so its text is already stored in the file: a PDF exported from Word, for example. The opposite of a scan. digital-convert reads these.                                                  |
| **category (page)**         | One of the eleven page types page-classification assigns, such as `TEXT_T` (typed text) or `PHOTO` ([the definitions](https://github.com/ufal/atrium-page-classification/blob/test/docs/reference/categories.md)).        |
| **CNEC 2.0**                | The entity types of the Czech Named Entity Corpus, used by NameTag's Czech model. nlp-enrich turns its codes into readable names, such as "Geographical name".                                                            |
| **CoNLL-U**                 | A plain-text table with one word per line: its lemma, part of speech, grammatical features and syntax ([more](external-tools.md#conll-u-and-universal-dependencies)).                                                     |
| **CUBBITT**                 | The Czech–English translation model behind LINDAT's translation service, the translator's default ([more](external-tools.md#cubbitt)).                                                                                    |
| **`DOC_LINE_CATEG/`**       | ocr-postprocess's per-line table: every text line with its line category. nlp-enrich reads it.                                                                                                                            |
| **end-to-end test (E2E)**   | The test that runs the tools one after another on sample documents and checks what each passes on ([W6 on Pipelines](pipelines.md#w6--e2e-smoke-the-integration-contract)).                                               |
| **ensemble**                | page-classification's five `vX.4` models scoring the same page, with their scores averaged. It is the service's default. It has no held-out accuracy figure of its own.                                                   |
| **FAIR**                    | Findable, Accessible, Interoperable, Reusable: the principles research-data publication aims at. RO-Crate export is ATRIUM's route to them.                                                                               |
| **fold**                    | One of five ways the annotated pages were divided into training (80 %), development (10 %) and test (10 %) parts. Each published page-classification model was trained on one fold.                                       |
| **GraphQL**                 | A query language for web APIs, in which the client names exactly the fields it wants. TEATER is queried this way.                                                                                                         |
| **held-out**                | Pages, or other data, a model never saw in training. Accuracy is only honest when it is measured on held-out data.                                                                                                        |
| **image (container)**       | A packaged program, published on GitHub's container registry. Each tool ships at least two: a batch image for the command line and an `-api` image for the service ([Operations](operations.md#images-and-tags)).         |
| **LINDAT/CLARIAH-CZ**       | The Czech research infrastructure for language data. It hosts the services nlp-enrich and the translator call: UDPipe, NameTag and translation ([more](external-tools.md#lindatclariah-cz)).                              |
| **line category**           | The label ocr-postprocess gives each text line: `Clear`, `Noisy`, `Trash` (illegible), `Non-text` or `Empty`.                                                                                                             |
| **NameTag**                 | LINDAT's named-entity recogniser. nlp-enrich uses NameTag 3 to find names of people, places and organisations.                                                                                                            |
| **NMT**                     | Neural machine translation: a model trained to translate whole sentences, such as CUBBITT.                                                                                                                                |
| **OCR / HTR**               | Optical character recognition (printed or typed text) and handwritten text recognition. They are different engines, which is why pages are classified first.                                                              |
| **OpenAPI**                 | A machine-readable description of a service's endpoints. Each tool commits it as `service/openapi.json`; it is the API's one contract.                                                                                    |
| **originator**              | The tool that creates a record's page and line structure: ocr-postprocess for OCR output, digital-convert for born-digital files.                                                                                         |
| **`PAGE_ALTO/`**            | ocr-postprocess's output folder: one ALTO file per page, `<doc>/<doc>-N.alto.xml`. The translator reads it.                                                                                                               |
| **paradata**                | Data about the process: which program, version and settings produced an output, when, and with which components and licences. One JSON file per run ([Licences and paradata](ecosystem/licences.md)).                     |
| **pilot (S2)**              | AMČR colleagues running the six services themselves, December 2026 – January 2027 ([S2 pilot handover](pilot.md)).                                                                                                        |
| **provenance**              | The record's account of who contributed what: a stamp on each block, and a list of the runs that wrote to it.                                                                                                             |
| **quality score**           | A number from 0 to 1 that ocr-postprocess gives each line, built from nine measurements of its text. The line category is decided from it and a short list of rules.                                                      |
| **record**                  | The ATRIUM document record: one JSON file per document, `<doc_id>.document.json`, that every stage reads and adds to ([The document contract](ecosystem/document-contract.md)).                                           |
| **revision (model)**        | A named version of a model on the Hugging Face Hub, such as `v4.4`. Name the revision you mean: the Hub's default can point to an older one.                                                                              |
| **RO-Crate**                | A standard way to package research data with its description, so a repository can publish it ([RO-Crate export](contracts/rocrate.md)).                                                                                   |
| **routing**                 | Deciding, from a page's category, which processing it needs next: OCR, handwriting recognition, table extraction, image handling or nothing. A person or a script decides; the tools do not.                              |
| **runbook**                 | A service's `service/README.md`: how to start it, what it downloads, what its errors mean and what to do, and its known limits.                                                                                           |
| **SKOS**                    | A W3C standard for publishing vocabularies. ATRIUM's label lists, such as the page categories, are published as SKOS concepts ([SKOS](contracts/skos.md)).                                                                |
| **SSH Open Marketplace**    | The European catalogue of humanities tools and workflows. Each ATRIUM tool has a record there ([more](external-tools.md#ssh-open-marketplace)).                                                                           |
| **TEATER**                  | A thesaurus of archaeological terms with Czech and English names, published by AIS CR. keyword-extract's controlled keywords come from it and from AMČR's keyword lists ([more](external-tools.md#the-teater-thesaurus)). |
| **TEI, TEITOK**             | TEI is the standard XML for encoding texts in the humanities. TEITOK is a corpus format and platform built on it, keeping every word linked to its place on the page. nlp-enrich writes TEITOK.                           |
| **top-1, top-3**            | The share of pages whose correct category is the model's first answer (top-1), or among its first three (top-3).                                                                                                          |
| **UDPipe**                  | LINDAT's tool for words, lemmas, parts of speech and sentence structure. nlp-enrich uses UDPipe 2 ([more](external-tools.md#udpipe-2)).                                                                                   |
| **vocabulary (controlled)** | A fixed list of terms that a keyword must come from: here, AMČR's keyword lists and TEATER. A controlled keyword is one of these terms; a statistical keyword is a word taken from the text.                              |
| **workflow narrative**      | A tool's workflow told step by step, with the formats in and out of each step. Its SSH Open Marketplace and Galaxy records are built from it ([Workflows](workflows/index.md)).                                           |

## Sources

| Source                                                                                               | What was taken from it                                       |
|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| this site's [External tools & services](external-tools.md), its former "Terms used across this site" | the fifteen original terms, and the institutions and formats |
| the six tools' `README.md` at their 10-29 patch releases                                             | the categories, line categories, quality score, ensemble     |
| atrium-page-classification `docs/evaluation/results.md`, `docs/evaluation/data.md`                   | fold, held-out, top-1 and top-3                              |
| atrium-nlp-enrich `docs/how-it-works.md`                                                             | CNEC 2.0 and NameTag                                         |
| [S2 pilot handover](pilot.md), [Operations](operations.md)                                           | the pilot's dates; images                                    |
