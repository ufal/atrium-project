---
title: External tools & services
nav_order: 3
status: partial
round: 7
issue: 57
authored: true
---

# External tools & services

Every external standard, service, model and institution ATRIUM depends on, in a couple of
sentences each, with a pointer to where it is actually used. Written for someone who has
never met SKOS, LINDAT or ALTO — if a name in this documentation is unfamiliar, it should be
explained here.

!!! info "Scope"
    Every entry page-classification and the translator depend on, including the shared
    standards and infrastructure both tools vendor, and the platforms all five tools'
    workflows are published on. Entries that only the other three tools use are named at the
    end of each section.

**On this page:**
[Terms used across this site](#terms-used-across-this-site) ·
[Data & OCR formats](#data--ocr-formats) ·
[Models](#models) ·
[Hosting, repository & registration](#hosting-repository--registration) ·
[Metadata standards & serialisations](#metadata-standards--serialisations) ·
[Domain vocabularies](#domain-vocabularies) ·
[Runtime & infrastructure](#runtime--infrastructure) ·
[The ATRIUM project itself](#the-atrium-project-itself) ·
[Named in the DMP, deliberately not implemented](#named-in-the-dmp-deliberately-not-implemented)

## Terms used across this site

| Term                    | Meaning                                                                                                                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **OCR** / **HTR**       | optical character recognition (printed or typed text) / handwritten text recognition — different engines, which is why pages are classified first                                         |
| **NMT**                 | neural machine translation — a model trained to translate whole sentences, such as CUBBITT                                                                                                |
| **record**              | the `atrium_document` JSON file that travels through the pipeline, one per document — see [The document contract](ecosystem/document-contract.md)                                         |
| **block**               | one top-level part of the record, written by exactly one tool — `page_categories`, `translations`, …                                                                                      |
| **accretion**           | how the record grows: each stage adds its own block and carries every other block forward unchanged                                                                                       |
| **paradata**            | data about the *process*: which program, version and configuration produced an output, when, and under which licence — one JSON file per run                                              |
| **provenance**          | the record's account of who contributed what: per-block stamps plus a list of contributing runs                                                                                           |
| **FAIR**                | Findable, Accessible, Interoperable, Reusable — the principles research data publication aims at; RO-Crate export is ATRIUM's route to them                                               |
| **`PAGE_ALTO/`**        | alto-postprocess's output: one ALTO file per page, `<doc>/<doc>-N.alto.xml` — what the translator reads                                                                                   |
| **`DOC_LINE_CATEG/`**   | alto-postprocess's per-line table: every text line with its quality category — what nlp-enrich and llm-enrich read                                                                        |
| **TEITOK**              | a corpus format and platform built on TEI XML, keeping tokens linked to their position on the page — nlp-enrich's output                                                                  |
| **GraphQL**             | a query language for web APIs, in which the client names exactly the fields it wants — how TEATER is queried                                                                              |
| **originator**          | the program that creates the positional plane (`pages`, `content`, `lines`, `tables`) of a record: alto-postprocess for OCR, `digital-convert` otherwise                                  |
| **workflow narrative**  | a tool's workflow told step by step, with the formats in and out of every step — the text its SSH Open Marketplace and Galaxy records are built from; see [Workflows](workflows/index.md) |
| **actionable workflow** | a workflow described on the SSH Open Marketplace that can also be run — in ATRIUM, as a Galaxy workflow                                                                                   |

## Data & OCR formats

### ALTO XML

**What it is.** *Analyzed Layout and Text Object* — an XML standard for the output of OCR,
maintained by the Library of Congress. It records not just the recognised text but *where on
the page each piece of it sits*: a document is `Page` → `TextBlock` → `TextLine` → `String`,
and each `String` carries one token in a `CONTENT` attribute plus its bounding box.

**Where ATRIUM uses it.** It is the backbone format of the whole pipeline. `alto-postprocess`
consumes OCR ALTO and emits per-page ALTO under `PAGE_ALTO/`; the
[translator](tools/translator/index.md) rewrites ALTO in place, preserving every coordinate;
the E2E fixture is one ALTO v3 page. Versions v1–v4 are in scope, with one catch:
alto-postprocess's ALTO methods split only v3 files (`page_split.py`), while its text-lines
method and service read every version.

**Why it is harder than it looks.** Because ALTO stores text *spatially*, translating or
rewriting it is not a text operation — see
[ALTO dual-pass reconstruction](tools/translator/reference.md#alto-dual-pass-reconstruction)
for what preserving that structure actually costs.

**Onward:** <https://www.loc.gov/standards/alto/>

### AMCR metadata XML

**What it is.** The record format of the **Archaeological Map of the Czech Republic**
(*Archeologická mapa České republiky*) — the national database of archaeological
investigations, finds and sites. Records describe a field investigation: its location,
circumstances, finds and free-text notes.

**Where ATRIUM uses it.** The translator's second input mode. Ten XPath targets in
`amcr-fields.txt` name the free-text fields that get translated — `popis`, `poznamka`,
`lokalizace`, `lokalizace_okolnosti`, `souhrn_upresneni` and the protected-data fields.
`load_vocab.py` also harvests AMCR's controlled vocabulary (*heslář*) to build the
translation glossary.

**One detail worth carrying.** AMCR's own thesaurus already expresses bilingual pairs as
sibling elements — `heslo` / `heslo_en` — which is exactly the shape the translator's
`append` output mode adopts rather than inventing a new one.

**Onward:** <https://amcr-info.cz/>

### OAI-PMH

**What it is.** The *Open Archives Initiative Protocol for Metadata Harvesting* — a small,
very old, very stable HTTP protocol for pulling metadata records out of a repository in bulk.
You ask for `GetRecord` or `ListRecords`, optionally since a date, and get XML back. It is how
digital libraries have exchanged catalogue data for twenty years.

**Where ATRIUM uses it.** AMCR is harvested over OAI-PMH: `amcr-inputs.txt` holds sample
`GetRecord` URLs against `https://api.aiscr.cz/2.2/oai` — the records in `my_documents/` — and `load_vocab.py` walks the same endpoint with `ListRecords` to build
the vocabulary ([W7](pipelines.md#w7--vocabulary-harvesting--review-the-translators-half)). The
translator's metadata mode finds the AMCR and OAI-PMH namespaces anywhere in a file, so that it
can translate fields *inside* an OAI-PMH envelope as well as in a bare record.

**Why it is listed here.** Three repositories harvest AMCR over it — the translator, nlp-enrich
and llm-enrich.

**Onward:** <https://www.openarchives.org/pmh/>

### CoNLL-U and Universal Dependencies

**What it is.** Universal Dependencies (UD) is a cross-lingual framework for annotating grammar —
lemmas, parts of speech, morphological features, syntax — with treebanks in well over a hundred
languages. CoNLL-U is its file format: one token per line, ten tab-separated columns.

**Where ATRIUM uses it.** The translator's lemmatiser sends text to [UDPipe](#udpipe-2) in
4,000-character chunks and reads the CoNLL-U that comes back: the FORM and LEMMA columns, and the
`Number=` feature from FEATS — which is what lets the vocabulary skip plural tokens
([W7](pipelines.md#w7--vocabulary-harvesting--review-the-translators-half)). Comment lines,
multi-word token ranges and empty nodes are skipped. There are eight UD 2.15 models: cs, sk, pl,
de, fr, en, ru, uk.

**Worth knowing.** A language outside those eight is **not lemmatised**: the single-word
vocabulary pass is skipped for it, with one warning per language. Requests ask only for the
tokenizer and tagger, since the dependency parse is not needed.

**Onward:** <https://universaldependencies.org/format.html>

### PDF, and the three tools that rasterise it

**What it is.** A PDF page has to become an image before a vision model can classify it, and the
choice of rasteriser and resolution decides what the model sees.

**Where ATRIUM uses it.** page-classification rasterises PDFs in three different places, with three
different tools:

| Where                                                                                                  | Tool                                  | Resolution                                                      |
|--------------------------------------------------------------------------------------------------------|---------------------------------------|-----------------------------------------------------------------|
| the service's `POST /predict_document`                                                                 | PyMuPDF (`fitz`), `page.get_pixmap()` | 300 dpi (`PDF_RENDER_DPI`); at most 50 pages (`service/api.py`) |
| dataset preparation on Unix ([W12](pipelines.md#w12--annotation-round-trip-page-classifications-half)) | poppler's `pdftoppm`                  | 300 dpi by default                                              |
| dataset preparation on Windows                                                                         | ImageMagick with Ghostscript          | 300 dpi by default                                              |

**Worth knowing.** The service renders PDF pages at 300 dpi, the resolution the training pages
were made at, rather than PyMuPDF's own 72 dpi default. `poppler-utils` is needed only on the
machine that prepares a dataset: only `pdf2png.sh` calls `pdftoppm`. PyMuPDF is distributed
under AGPL-3.0 or a commercial licence, and Ghostscript under AGPL-3.0.

**Onward:** <https://pymupdf.readthedocs.io/> · <https://poppler.freedesktop.org/>

### Formats used by the other stages

PAGE XML and hOCR (other OCR output formats), METS (a packaging standard for digitised
objects), TEI P5 and TEITOK (text-encoding formats), and IOB2 (a token-level tagging scheme for
named entities) belong to alto-postprocess and nlp-enrich. TEITOK in particular: nlp-enrich
writes it (its "format 2" follows the conventions of the TEITOK tools — flexiconv, flexipipe,
xmltokenizer, teitok-tools — and is tested against flexiconv's reader); llm-enrich and
alto-postprocess read it.

Each has a reference in the repository that uses it:

* **OCR and text input formats** — ALTO, PAGE XML, hOCR, ABBYY FineReader XML, DjVuXML,
  Tesseract TSV, OCR JSON, PDF text layers, TEI/TEITOK, office, e-mail and plain-text files: the
  standard behind each, the tools that write it and what alto-postprocess keeps of it, in
  [Formats and their standards](https://github.com/ufal/atrium-alto-postprocess/blob/master/docs/text_inputs.md#formats-and-their-standards).
* **TEITOK as an output** — the standards it builds on, how nlp-enrich composes a file from the
  line table, UDPipe, NameTag and the ALTO layout, the tools that write or read it, and the
  pitfalls: nlp-enrich's README, from
  [The format and the standards it builds on](https://github.com/ufal/atrium-nlp-enrich#the-format-and-the-standards-it-builds-on)
  to [Pitfalls](https://github.com/ufal/atrium-nlp-enrich#pitfalls).

## Models

### Hugging Face Hub

**What it is.** The de-facto public registry for machine-learning models, datasets and the
code to run them — think of it as a package index where the packages are model weights. A
model is addressed as `owner/name`, optionally at a `revision` (a branch or tag), and pulled
by the `huggingface_hub` library into a local cache.

**Where ATRIUM uses it.** Everywhere a model is loaded. It is the single most-referenced
external service in the ecosystem. The classifier pulls its weights with `--hf`; the translator
pulls the FastText language-identification model; `HF_HOME` is set to `/cache/huggingface` in
every container so the cache survives restarts, and `HF_TOKEN` lifts the rate limit that applies
to anonymous downloads.

**Onward:** <https://huggingface.co/>

### `ufal/vit-historical-page`

**What it is.** ATRIUM's own published model repository — the fine-tuned page classifiers,
one revision per generation.

**Where ATRIUM uses it.** `setup/config.txt` `[HF] repo_name`, and the HTTP service. The
service warms revisions `v1.4`–`v5.4`, the five-model canonical ensemble. Revisions are named
`vX.Y` — model slot and data generation; see
[page-classification → The models](tools/page-classification/index.md#the-models).

!!! note "Name a revision"
    Pass the revision you mean — `-rev v4.4` for the recommended single model, or `--best` for
    the ensemble — rather than relying on the repository's `main` branch.

**Onward:** <https://huggingface.co/ufal/vit-historical-page>

### `timm/regnety_160.swag_ft_in1k`

**What it is.** A RegNetY-16GF convolutional image classifier from the `timm` library,
pre-trained with Meta's SWAG weakly-supervised method and fine-tuned on ImageNet-1k. About
84 M parameters.

**Where ATRIUM uses it.** The default `[SETUP] base_model`, and the base of the best-performing
published revision — `v4.3` at 99.16 % top-1 and 100 % top-3. It is also what the E2E smoke
test passes as `-m`. Notable because it beats every ViT variant tried while being a quarter the
size of the largest.

**Onward:** <https://huggingface.co/timm/regnety_160.swag_ft_in1k>

### `facebook/fasttext-language-identification`

**What it is.** A tiny, extremely fast language classifier from Meta's FastText project. It
takes a string and returns an ISO 639-3 code with a confidence score, over 200 languages, with
no GPU and essentially no latency.

**Where ATRIUM uses it.** The translator's `--source_lang auto` path. It maps FastText's 639-3
output to the 639-1 codes translation services expect, and uses a guess only when the text has
at least 20 letters, the score is at least 0.5 and the language is one the backend translates;
otherwise the element's own language label, the document's language and a default (`cs`)
decide — see [the translator's language rules](tools/translator/reference.md#languages). In ALTO
mode it runs once per `TextBlock` so every line in a block is translated consistently.

**Two things to know.** Its weights are **CC BY-NC 4.0**, so auto-detection alone makes a run's
output non-commercial — passing `--source_lang` explicitly avoids that. And if the model fails
to load, nothing is detected — the fallbacks decide every block — and the service reports the
failure on `GET /health?deep=true`.

**Onward:** <https://huggingface.co/facebook/fasttext-language-identification>

### CUBBITT

**What it is.** *Charles University Block-Backtranslation-Improved Transformer Translation* — a
neural machine translation system developed at the Institute of Formal and Applied Linguistics,
best known for reaching professional-level quality on Czech↔English news translation. It is
served publicly by LINDAT as a REST API.

**Where ATRIUM uses it.** It is the translator's **default backend** (`lindat`). Model names are
fetched live from the API and composed as `<src>-<tgt>`; the endpoint is attachable through
`TRANSLATION_URL`, so a self-hosted instance or a local stub substitutes with no code change.

**Licence consequence.** CUBBITT's models are **CC BY-NC-SA 4.0**, which is why a default
translator run resolves to CC BY-NC-SA 4.0 — see
[translator → Licence](tools/translator/reference.md#licence-is-computed-not-declared).

**Onward:** <https://lindat.mff.cuni.cz/services/translation/>

### UDPipe 2

**What it is.** A trainable pipeline for tokenisation, tagging, lemmatisation and dependency
parsing, trained on Universal Dependencies treebanks and served as a REST API by LINDAT. Given a
sentence it returns CoNLL-U — one line per token, with its lemma and morphological features.

**Where ATRIUM uses it.** Lemma matching for the translator's controlled vocabulary: a glossary
term is matched against a document by *lemma* rather than surface form, so an inflected Czech
word still matches its dictionary entry. Models are named per language
(`czech-pdt-ud-2.15-241121`, `slovak-snk-ud-2.15-241121`, and six more). `nlp-enrich` calls the same service,
with the same `UDPIPE_URL` variable name.

**Licence consequence.** The **engine** is MPL 2.0, but the **models** are CC BY-NC-SA 4.0 —
they are separate entries in the licence table for exactly that reason.

**Onward:** <https://lindat.mff.cuni.cz/services/udpipe/>

### The TEATER thesaurus

**What it is.** A thesaurus of archaeological terminology with Czech and English names for
each concept, organised in a tree of categories and served from `teater.aiscr.cz` over GraphQL
rather than OAI-PMH.

**Where ATRIUM uses it.** Together with the AMCR *heslář*, it is one of the two sources
`load_vocab.py` unions into the translation glossary, and
`llm-enrich` builds a nested union of both for its category enum. Its data is CC BY-NC 4.0, so
loading the vocabulary makes a run non-commercial.

**Onward:** <https://teater.aiscr.cz/>

### The page-classification ML stack

**What it is.** PyTorch runs the models; Hugging Face `transformers` loads and fine-tunes them;
`timm` supplies the vision architectures — RegNetY, EfficientNetV2 — behind the `timm/…`
checkpoints; Ultralytics provides YOLO classifiers as an alternative model family; scikit-learn
computes the evaluation reports.

**Where ATRIUM uses it.** The pins that carry a reason, from `setup/requirements.txt`:

| Package                 | Pin                    | Why                                                                                                                                       |
|-------------------------|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `torch` / `torchvision` | `==2.7.1` / `==0.22.1` | installed first, from the CPU wheel index unless `TORCH_INDEX_URL` points at a CUDA one; Dependabot ignores both                          |
| `transformers`          | `>=4.57.6,<5`          | 5.x constructs models on the `meta` device, which crashes the timm builders for the RegNetY and EfficientNetV2 checkpoints `--best` loads |
| `numpy`                 | `>=2.4.6,<2.5`         | 2.5 requires Python ≥ 3.12 and every image runs 3.11; a Dependabot ignore rule holds the ceiling                                          |
| `ultralytics`           | `>=8.4.155`            | the `--yolo` path, off by default (`[YOLO] use_yolo = False`)                                                                             |
| `timm`                  | `>=1.0.29`             | never imported directly — the `timm/…` checkpoints load through `transformers`                                                            |

**Worth knowing.** Ultralytics distributes its package and base weights under AGPL-3.0.
`para_config.txt` declares it as the conditional component `ultralytics`, and `run.py` logs it on
every `--yolo` run, so a `--yolo` inference run resolves to AGPL-3.0; with `--train`, the resolver
ranks the dataset's CC BY-NC 4.0 above it. The `transformers<5` pin lives in
`setup/requirements.txt` only — `service/requirements.txt` deliberately leaves the model stack out,
and the image installs both files.

**Onward:** <https://pytorch.org/> · <https://huggingface.co/docs/transformers> ·
<https://huggingface.co/docs/timm> · <https://docs.ultralytics.com/>

### Translation back-ends beyond CUBBITT

**What it is.** The translator chooses its engine through a registry (`processors/backend.py`), so
the same pipeline — ALTO reconstruction, vocabulary protection, the record — can run against a
different model.

**Where ATRIUM uses it.**

| Back-end                                                                                                                                  | Status                                                                                       | Licence component                                                                                     |
|-------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `lindat` — [CUBBITT](#cubbitt)                                                                                                            | the default                                                                                  | `lindat_cubbitt`, CC BY-NC-SA 4.0                                                                     |
| `openai_compatible` — any OpenAI-style chat-completions API; the code's examples are OpenRouter, Gemini, Mistral, Groq and a local Ollama | registered; plain REST over `requests`, no SDK                                               | `llm_api` = "LLM provider ToS", unrecognised on purpose                                               |
| `ct2` — CTranslate2 running EuroLLM, MADLAD-400, NLLB or OPUS-MT                                                                          | registered; `ctranslate2` and `sentencepiece` load on first use, from `requirements-ct2.txt` | `ctranslate2` MIT; `eurollm`, `madlad400` Apache-2.0; `opus_mt` CC BY 4.0; `nllb200` **CC BY-NC 4.0** |

**Worth knowing.** CT2's default compute type is `int8`, which runs on every device; a compute
type the device cannot run is refused before the model loads, with the list of valid ones. The model
licence follows `CT2_MODEL_FAMILY`, so an NLLB run is non-commercial. An LLM run's licence
resolves to the unrecognised provider-terms string; see [SPDX and Creative
Commons](#spdx-and-creative-commons).

**Onward:** <https://opennmt.net/CTranslate2/> · <https://huggingface.co/utter-project> ·
<https://huggingface.co/google/madlad400-3b-mt>

### sacreBLEU and COMET

**What it is.** sacreBLEU computes reproducible BLEU and chrF scores against reference
translations. COMET is a neural metric that tracks human judgement more closely.

**Where ATRIUM uses it.** `eval/bakeoff.py`, the translator's comparison of back-ends. It
always reports reference-less signals — length ratio, number preservation, glossary hit rate,
empty outputs and failures (counted apart), and each back-end's similarity to the first one
listed — and, given `--refs`, chrF and BLEU per segment and per corpus (sacreBLEU) plus COMET
(`--comet-model`, default `Unbabel/wmt22-comet-da`). COMET-QE is opt-in with `--comet-qe-model`.
Per-segment rows go to `--out`, one row per back-end to `--summary-out`.

**Worth knowing.** Both scorers are imported lazily: without sacreBLEU or `unbabel-comet` the run
warns and leaves those columns blank. `eval/requirements-eval.txt` installs sacreBLEU and lists
`unbabel-comet` as an opt-in line, because it pulls in torch and downloads large checkpoints.

**Onward:** <https://github.com/mjpost/sacrebleu> · <https://unbabel.github.io/COMET/>

### Models used by the other stages

`Qwen/Qwen2.5-0.5B`, `hantian/layoutreader`, `THUDM/glm-4v-9b`, NameTag 3 (LINDAT's named-entity
recogniser), Korektor (its spelling corrector) and the keyword extractors belong to nlp-enrich
and llm-enrich.

## Hosting, repository & registration

### LINDAT/CLARIAH-CZ

**What it is.** The Czech national research infrastructure for language and cultural-heritage
data, hosted at the Institute of Formal and Applied Linguistics (ÚFAL), Charles University. It is
two things at once, and confusing them is easy: a **repository** that stores and issues persistent
identifiers for datasets, and a **service host** that runs public APIs — translation, UDPipe,
NameTag, Korektor.

**Where ATRIUM uses it.** Both roles. The page-classification training dataset is published there;
the translator's default backend and its lemmatiser are LINDAT-hosted APIs. Every Agent Skill
client takes its base URL from one environment variable, so a hosted deployment of the ATRIUM
services can be used without changing any code.

**Onward:** <https://lindat.cz/>

### The Handle System, and persistent identifiers

**What it is.** A system for naming digital objects with an identifier that survives the object
moving. A handle looks like `20.500.12800/1-6184` and resolves through a proxy —
`hdl.handle.net/20.500.12800/1-6184` — so the citation stays valid when the hosting URL changes.
DOIs are handles with extra rules on top.

**Where ATRIUM uses it.** `hdl.handle.net/20.500.12800/1-6184` is the **primary citation for the
page-classification training dataset**, 48,499 pages from 37,328 documents — the identifier to
cite wherever the dataset is used.

**Onward:** <https://www.handle.net/>

### GHCR — the GitHub Container Registry

**What it is.** GitHub's Docker registry, addressed as `ghcr.io/<owner>/<image>:<tag>`. Images
inherit the repository's visibility and can be pulled anonymously when it is public.

**Where ATRIUM uses it.** Every tool publishes two images per release — a batch image and a
`-api` image — from one Dockerfile with two stages. The E2E smoke test pulls them by tag, which
is what makes `image-tag` the most consequential input in that workflow.

!!! note "`:latest` moves only on a version tag"
    Only a push to the `test` branch publishes, as `sha-*` and `:test`; pushes to other branches
    publish nothing. `:latest` and the version tag move only on a `v*` tag, and only after the
    release gate passes — `-beta` tags included. So `:latest` means *the most recent release that
    passed the gate*, not *the most recent build* — which matters when reading an E2E result. See
    [W6](pipelines.md#w6--e2e-smoke-the-integration-contract) and [Operations](operations.md#images-and-tags).

**Onward:** <https://docs.github.com/packages>

### SSH Open Marketplace

**What it is.** A discovery portal for the social sciences and humanities that lists tools and
services, training materials, datasets and workflows. Records are contributed by their authors
and published once a moderator approves them, and every item keeps a persistent identifier — the
short code in its address, such as `RER7Fw`. A **workflow** record is a narrative: a description
followed by ordered steps, where each step can name its activity, its input and output formats,
and the tools or services it uses as related records.

**Where ATRIUM uses it.** Every ÚFAL tool has a tool-or-service record under the keyword
`ATRIUM catalogue` — [`RER7Fw`](https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw)
(page-classification), [`YParYU`](https://marketplace.sshopencloud.eu/tool-or-service/YParYU)
(alto-postprocess), [`CizIUW`](https://marketplace.sshopencloud.eu/tool-or-service/CizIUW)
(translator), [`EMhu3X`](https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X)
(nlp-enrich), [`j9fqxo`](https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo)
(llm-enrich). The translator's workflow has its own record,
[`13eHAZ`](https://marketplace.sshopencloud.eu/workflow/13eHAZ), and the AMČR text workflow,
[`0xSpVP`](https://marketplace.sshopencloud.eu/workflow/0xSpVP), strings the tools together.
The text these records are built from is on [Workflows](workflows/index.md).

**Onward:** <https://marketplace.sshopencloud.eu/>

### TaDiRAH

**What it is.** The *Taxonomy of Digital Research Activities in the Humanities* — a controlled
list of what researchers do with digital methods: collecting, converting, enriching, analysing,
translating and so on. The SSH Open Marketplace names the *activity* of a tool, and of each step
of a workflow, with terms based on it.

**Where ATRIUM uses it.** Each step of a [workflow narrative](workflows/index.md) names its
activity with the term the marketplace offers — *Converting*, *Extracting*, *Translating*,
*Named Entity Recognition* — so the step can be copied into a workflow record as it stands.

**Onward:** <https://vocabs.dariah.eu/tadirah/>

### Galaxy

**What it is.** An open web platform for running analysis tools and chaining them into
workflows without programming. A Galaxy **tool** is a command-line program described by an XML
wrapper that declares its inputs, outputs and parameters, each input and output with a Galaxy
**datatype** (`alto`, `tei`, `xml`, `tabular`, `json`, `pdf`, `png`, …); the program runs from a
package or a container. A **workflow** chains tools and is shared as a `.ga` file, with an
annotation, a creator, a licence and labelled inputs and outputs. Tools are published through
the Galaxy **ToolShed** and tested with **Planemo**; public servers such as usegalaxy.eu install
them. [ssh.usegalaxy.eu](https://ssh.usegalaxy.eu/) is usegalaxy.eu's entry point for the social
sciences and humanities, with the same tools and a Digital Humanities section. The Intergalactic
Workflow Commission (**IWC**) curates reviewed workflows.

**Where ATRIUM uses it.** An *actionable workflow* is one that is described on the SSH Open
Marketplace and can also be run — in ATRIUM, as a Galaxy workflow. DARIAH keeps ATRIUM's Galaxy
tool wrappers and workflows in the
[`atrium-galaxy-tools`](https://github.com/DARIAH-ERIC/atrium-galaxy-tools) repository. Each
[workflow narrative](workflows/index.md) carries a Galaxy sheet for its tool: the datatypes of
its inputs and outputs, its container, compute and network needs, and its test data.

**Onward:** <https://galaxyproject.org/> · <https://planemo.readthedocs.io/>

### WorkflowHub, and Workflow RO-Crate

**What it is.** A registry for computational workflows. It gives each workflow a citable
identifier and stores it as a **Workflow RO-Crate** — an [RO-Crate](#ro-crate-11-and-the-process-run-crate-profile)
whose main entity is the workflow itself, with its inputs, outputs, creator and licence. Galaxy
workflows reviewed by the IWC, and those of the Galaxy Training Network, are deposited there
automatically.

**Where ATRIUM uses it.** When a Galaxy workflow of an ATRIUM tool is published, WorkflowHub is
where it becomes citable; the [field table on Workflows](workflows/index.md#one-text-three-platforms)
shows which part of a narrative fills which field of the crate. It is a different crate from the
one the tools export for their records, which describes a document and the runs that produced it.

**Onward:** <https://workflowhub.eu/>

## Metadata standards & serialisations

### SKOS

**What it is.** The W3C's *Simple Knowledge Organization System* — an RDF vocabulary for thesauri
and controlled lists. A concept has a preferred label, a definition and a notation; concepts are
grouped into schemes and collections, and linked to other vocabularies by mapping properties.

**Where ATRIUM uses it.** `atrium_vocab.py`, vendored into both tools, is ATRIUM's registry of six
controlled label sets. page-classification's eleven categories are one of them, `page-category`,
and its model registry is checked against that scheme at import time. The translator carries the
file but does not import it; its glossary is a CSV. The full picture is on
[SKOS & the ATRIUM vocabulary](contracts/skos.md).

**Onward:** <https://www.w3.org/TR/skos-reference/>

### RO-Crate 1.1, and the Process Run Crate profile

**What it is.** A convention for packaging research data. A folder becomes a crate when it holds
one JSON-LD file, `ro-crate-metadata.json`, saying what is in the folder, who made it, with which
software and under which licence. *Profiles* add rules for particular kinds of crate; the Process
Run Crate profile is for "these tools were run over these inputs".

**Where ATRIUM uses it.** `atrium_rocrate.py`, vendored into every tool and run as its own step, writes
RO-Crate 1.1. A run crate also declares the profile `https://w3id.org/ro/wfrun/process/0.5`. See
[W13](pipelines.md#w13--ro-crate-export--fair-publication) and
[RO-Crate export](contracts/rocrate.md).

**Worth knowing.** Profiles are versioned independently of RO-Crate itself, so a crate names both:
RO-Crate 1.1 for the container, and the profile version for what the crate claims to describe.

**Onward:** <https://www.researchobject.org/ro-crate/>

### JSON-LD

**What it is.** JSON with an `@context` that maps its keys onto web vocabularies, so the same file
is ordinary JSON to a program and linked data to an RDF tool.

**Where ATRIUM uses it.** Two outputs, both written with the Python standard library alone: the
RO-Crate descriptor, and `atrium_vocab.py --jsonld`. `atrium_vocab.schema.json` describes the
shape of the latter.

**Worth knowing.** JSON-LD is kept *off* the extraction path (`rocrate_export.md` §3): nothing
writes JSON-LD while a document is being processed; the exporter produces it afterwards, from
records already on disk.

**Onward:** <https://json-ld.org/>

### schema.org

**What it is.** The shared vocabulary search engines and catalogues use to describe things on the
web — `Dataset`, `Person`, `SoftwareApplication`, `CreateAction`, `DefinedTerm`, and so on.

**Where ATRIUM uses it.** Implicitly, through RO-Crate's context. Every entity in an ATRIUM crate
is typed with schema.org terms: a `DefinedTerm` per page category, a `CreateAction` per run, a
`SoftwareApplication` per tool. The string `schema.org` never appears in the code — the RO-Crate
context supplies it.

**Onward:** <https://schema.org/>

### Turtle and RDF

**What it is.** RDF is the W3C data model of subject–predicate–object triples that SKOS is written
in; Turtle is its most readable text serialisation.

**Where ATRIUM uses it.** `atrium_vocab.py --turtle` writes the whole registry as Turtle — six
schemes and their concepts — without `rdflib` or any other dependency.

**Worth knowing.** The output is byte-stable (two runs compare equal), sorted, and free of blank
nodes, and it uses one prefix per scheme (`a-page-category:`, `a-theme:`, …) because, as the code
notes, a Turtle local name cannot carry a `/`.

**Onward:** <https://www.w3.org/TR/turtle/>

### Dublin Core

**What it is.** A small set of general-purpose metadata terms — title, creator, date, source and
the like — maintained by DCMI. `dct:` is the usual prefix for its RDF namespace.

**Where ATRIUM uses it.** In the SKOS output only: every scheme carries `dct:title` and
`dct:description`, and the schemes taken from an outside authority carry a `dct:source`.

**Onward:** <https://www.dublincore.org/specifications/dublin-core/dcmi-terms/>

### JSON Schema

**What it is.** A vocabulary for describing what a valid JSON document looks like, and the
validators that check a document against that description.

**Where ATRIUM uses it.** `atrium_document.schema.json` (draft 2020-12) is the contract of the
[document record](ecosystem/document-contract.md), and `validate_document()` runs on every record
either tool writes.

**Worth knowing.** Without the `jsonschema` library installed, validation **raises** rather than
passing silently — a gate that quietly becomes a no-op cannot be told apart from one that
passed. Both tools list `jsonschema` among their requirements.

**Onward:** <https://json-schema.org/>

### SPDX and Creative Commons

**What it is.** SPDX is the standard list of software and data licence identifiers — `MIT`,
`Apache-2.0`, `CC-BY-NC-4.0`. Creative Commons licences govern most of the data and models used
here; their building blocks are BY (attribution), NC (non-commercial) and SA (share-alike).

**Where ATRIUM uses it.** `para_licenses.py`, vendored into both tools, ranks every licence a run
touched and reports the most restrictive one as the run's licence:

| Rank | Licences                                 |
|------|------------------------------------------|
| 0    | Public Domain, CC0                       |
| 1    | MIT, Apache-2.0, BSD-3-Clause, CC BY 4.0 |
| 2    | MPL 2.0                                  |
| 3    | LGPL-3.0, CC BY-SA 4.0                   |
| 4    | GPL-3.0, AGPL-3.0                        |
| 5    | CC BY-NC 4.0, glm-4                      |
| 6    | CC BY-NC-SA 4.0                          |

**Worth knowing.**

* The keys mix SPDX identifiers with display names. **SPDX spellings** resolve through the alias
  table (`CC0-1.0`, `CC-BY-SA-4.0`, the `-only` / `-or-later` GPL forms), and every catalogued key
  also resolves in any casing (`bsd-3-clause`, `lgpl-3.0`).
* An unrecognised licence is treated as the most restrictive, and so **becomes the run's effective
  licence**: its raw string, an empty URL, **both** the non-commercial and share-alike flags set,
  and a warning in the notes. The translator's `llm_api = LLM provider ToS` is unrecognised on
  purpose, so a run on the LLM back-end resolves to that string; a component missing from
  `para_config.txt` is logged as `UNKNOWN` and resolves the same way.
* A run that logs no component at all falls back conservatively to CC BY-NC 4.0.

**Onward:** <https://spdx.org/licenses/> · <https://creativecommons.org/licenses/>

### ORCID

**What it is.** Persistent identifiers for researchers, of the form `https://orcid.org/0000-…`.

**Where ATRIUM uses it.** Both tools' `CITATION.cff` files list the project's authors, each with
an ORCID. The RO-Crate exporter uses those ORCIDs as the `@id`s of its `Person` entities.

**Onward:** <https://orcid.org/>

### CITATION.cff

**What it is.** A small YAML file that tells GitHub, Zenodo and reference managers how to cite a
repository.

**Where ATRIUM uses it.** Every tool carries one (`cff-version: 1.2.0`), with the current version
and release date. It is also a **release gate**:
`check_version.py` reads the first column-0 `version:`, strips a leading `v`, and fails unless it
equals `para_config.txt`'s `[tool] version` — and, on a tag push, the tag. `security.reusable.yml`
runs it in CI, and each tool's release workflow runs it again. GitHub renders the file as the
repository's *Cite this repository* button.

**Onward:** <https://citation-file-format.github.io/>

### w3id.org

**What it is.** A community-run permanent-identifier service: `https://w3id.org/<name>/…`
redirects to wherever the content currently lives, so an identifier outlives a change of host.

**Where ATRIUM uses it.** `https://w3id.org/atrium/` is the root of every ATRIUM concept URI
(`atrium_vocab.py`'s `SKOS_BASE`), and RO-Crate's own context and profiles live under
`w3id.org/ro/`.

**Worth knowing.** A w3id identifier works as an identifier whether or not its redirect is in
place; registering the redirect — a one-file pull request to the w3id repository — is what
makes it dereferenceable. See [SKOS](contracts/skos.md#how-a-uri-is-minted).

**Onward:** <https://w3id.org/>

## Domain vocabularies

AMCR, TEATER and OAI-PMH are described above. Two more belong to nlp-enrich's part of the
pipeline:

* **CNEC 2.0** — the *Czech Named Entity Corpus* type hierarchy, used for the named-entity
  types nlp-enrich assigns (`entities[].type_cnec`).
* **Getty AAT** — the *Art & Architecture Thesaurus*, a structured vocabulary for describing
  cultural heritage objects; the registry declares its namespace and the record schema has an
  `entities[].pid.aat` slot for linking an entity to an AAT concept.

## Runtime & infrastructure

### Docker and Compose

**What it is.** Docker packages a program with everything it needs into an image; Compose describes
how to run one or more containers from those images.

**Where ATRIUM uses it.** One `Dockerfile` per tool with two targets: `base`, the batch image, and
`api`, which runs `python -m service.api`. Both build on `python:3.11-slim`, run as uid
10001, and keep the Hugging Face cache at `/cache/huggingface`. Compose runs the batch service by
default and the HTTP service under the `api` profile.

**Worth knowing.** page-classification's `api` service `extends` the batch one, so it has to re-set
`ATRIUM_RUNNER_IMAGE`, which it would otherwise inherit from the batch image; the translator
defines its two services separately. Details, including the image tags, are in
[Operations](operations.md).

**Onward:** <https://docs.docker.com/compose/>

### Kubernetes

**What it is.** The container orchestrator the partner institutions run the services on.

**Where ATRIUM uses it.** Not in either tool repository. The hub ships the template,
`docs/templates/k8s/atrium-service.deployment.yaml`: `startupProbe` and `readinessProbe` on
`/ready`, `livenessProbe` on `/health`, a 60-second termination grace. The probe table,
environment and sizing for each tool are on [Operations](operations.md).

**Worth knowing.** A service image is named `atrium-<tool>-api:<version>` — see
[Operations → Images and tags](operations.md#images-and-tags).

**Onward:** <https://kubernetes.io/docs/>

### GitHub Actions

**What it is.** GitHub's built-in CI: workflows in `.github/workflows/`, and *reusable* workflows
that one repository can call from another.

**Where ATRIUM uses it.** Each tool calls seven hub reusables at `@v1` — `api-contract`, `codeql`,
`docker-tool`, `para-drift`, `pre-commit`, `security`, `workflow-lint` — plus workflows of its own.
See [Architecture → The CI federation](ecosystem/architecture.md#the-ci-federation).

**Worth knowing.** `v1` is a movable major tag, so the hub can update every caller at once.
Third-party actions are pinned by commit SHA instead — `trivy-action`, `build-push-action`,
`action-gh-release` — so a moved upstream tag cannot change what runs.

**Onward:** <https://docs.github.com/actions>

### FastAPI and uvicorn

**What it is.** FastAPI is a Python web framework; uvicorn is the ASGI server that runs it.

**Where ATRIUM uses it.** Both HTTP services are FastAPI applications started by `uvicorn.run()` in
`service/api.py`, with uvicorn's `[standard]` extras, declared in each tool's
`service/requirements.txt`.

**Onward:** <https://fastapi.tiangolo.com/> · <https://www.uvicorn.org/>

### ruff, pre-commit and Dependabot

**What it is.** ruff is a Python linter and formatter; pre-commit runs such checks before each
commit and in CI; Dependabot opens pull requests when a pinned dependency has a newer version.

**Where ATRIUM uses it.** Both tools run pre-commit-hooks and ruff (page-classification adds
shellcheck for its data scripts), with ruff at line length 120, Python 3.11, rules `E`, `F`,
`W`, `I`. Dependabot in page-classification watches GitHub Actions and pip in `/setup` and
`/service`; in the translator it watches GitHub Actions, pip in `/`, `/service` and `/eval`
(ignoring numpy ≥ 2.0, which fasttext-wheel 0.9.2 cannot run on) and the `docker` base image.

**Worth knowing.** A `docker` ecosystem only helps with a **digest-pinned** base: a bare
`python:3.11-slim` never changes name, so there is nothing to propose. Pinning the base by
digest and declaring the ecosystem turns a base-image update into a reviewed pull request; the
hub's `docs/templates/Dockerfile` and example Dependabot configuration do both. The background
is [the base image that blocked a release](tools/translator/history.md#the-base-image-that-blocked-a-release).

**Onward:** <https://docs.astral.sh/ruff/> · <https://pre-commit.com/> ·
<https://docs.github.com/code-security/dependabot>

### Trivy, CodeQL, SARIF and Codecov

**What it is.** Trivy scans container images for known vulnerabilities; CodeQL analyses source code
for security flaws; SARIF is the file format both use to report findings to GitHub; Codecov
collects test-coverage reports.

**Where ATRIUM uses it.** All in the hub reusables:

* **Trivy** scans every published image by digest — CRITICAL and HIGH, fixed-only, report-only —
  and fails a release on a fixable CRITICAL, on tag pushes only. The action is pinned to a commit
  SHA because its tags were compromised in March 2026 (GHSA-69fq-xp46-6x23).
* **CodeQL** analyses Python with `build-mode: none`.
* Both upload **SARIF** to GitHub code scanning.
* **Codecov** receives coverage only when a token is configured. What fails a build is each
  repository's own `.coveragerc` `fail_under` floor.

**Onward:** <https://trivy.dev/> · <https://codeql.github.com/> ·
<https://docs.oasis-open.org/sarif/sarif/v2.1.0/> · <https://about.codecov.io/>

### BuildKit SBOM and provenance

**What it is.** A software bill of materials lists what an image contains; a provenance attestation
records how it was built. BuildKit can attach both to an image as it is pushed.

**Where ATRIUM uses it.** `docker/build-push-action` with `sbom: true` and `provenance: true`, on
every published image. It replaced a separate SBOM job that could race the image it described.

**Onward:** <https://docs.docker.com/build/metadata/attestations/>

### Infrastructure used by the other stages

vLLM and Ollama (servers for running large language models locally) belong to llm-enrich;
alto-tools (ALTO utilities, vendored as `alto_tools.py`) to alto-postprocess. flexiconv (UFAL's
converter of PDF, DOCX, PAGE XML, hOCR, … into TEITOK; GPL-3.0-or-later, optional, pinned at
v0.3.10) belongs to nlp-enrich, whose `api_flexiconv.sh` runs it on the command line only — no
service image contains it; llm-enrich vendors the same adapter.

## The ATRIUM project itself

### DARIAH, ARIADNE, CLARIN and OPERAS

**What it is.** Four European research infrastructures: arts and humanities (DARIAH), archaeology
(ARIADNE), language technologies (CLARIN), and open scholarly communication (OPERAS). ATRIUM —
*Advancing fronTier Research In the arts and hUManities* — is the EU project that bridges them.

**Where ATRIUM uses it.** Not in the two tools' code. The hub README states the project's purpose,
and the shared modules mention two of them: the SKOS registry leaves the externally published,
DARIAH-namespaced SKOS version of the AMCR and TEATER vocabularies to a separate project, and the
record schema describes `entities[].pid` as "the ARIADNE/GoTriple hook".

**Onward:** <https://atrium-research.eu/> · <https://www.dariah.eu/> ·
<https://www.ariadne-research-infrastructure.eu/> · <https://www.clarin.eu/> ·
<https://operas-eu.org/>

### ÚFAL, Charles University

**What it is.** The Institute of Formal and Applied Linguistics at Charles University, Prague — the
developer of this tool chain, and the host of [LINDAT/CLARIAH-CZ](#lindatclariah-cz).

**Where ATRIUM uses it.** Both tools' `LICENSE` ("Copyright (c) 2025 UFAL"), their READMEs'
acknowledgements, and this site's footer.

**Onward:** <https://ufal.mff.cuni.cz/>

### ARÚP and ARÚB

**What it is.** The Institutes of Archaeology of the Czech Academy of Sciences — *Archeologický
ústav AV ČR* — in Prague (ARÚP) and Brno (ARÚB). They hold the collections these tools were built
for, and they are the partners the services are handed to.

**Where ATRIUM uses it.** In the data: the AMCR sample records name
`Archeologický ústav AV ČR, Praha, v.v.i.` as the responsible organisation. In page-classification's
results: `result/ARUP_averaged_SHORT.csv` and `result/ARUB_averaged_SHORT.csv` are ensemble
classifications of each institute's pages. And at the deployment boundary: the handoff is a Docker
image that the partners run on their own Kubernetes ([Operations](operations.md)).

**Onward:** <https://www.arup.cas.cz/> · <https://www.arub.cz/>

### AIS CR — `aiscr.cz`

**What it is.** The Czech archaeological information infrastructure that publishes the AMCR
database and the TEATER thesaurus, under the `aiscr.cz` domain. Its OAI-PMH endpoint identifies
itself as *Archaeological Map of the Czech Republic (AMCR)* and licenses its metadata under
CC BY-NC 4.0.

**Where ATRIUM uses it.** `aiscr.cz` hosts everything the translator harvests or links to: the AMCR
OAI-PMH endpoint `api.aiscr.cz/2.2/oai`, AMCR's identifier namespace `api.aiscr.cz/id/` (also a
prefix in the SKOS registry), the AMCR XML schema under `api.aiscr.cz/schema/amcr/2.2/`, and TEATER
at `teater.aiscr.cz` — GraphQL at `/api/graphql`, identifiers under `/id/`.

**Onward:** <https://www.aiscr.cz/>

### The data management plan

**What it is.** The project's data management plan (DMP), which names the standards the project
commits to.

**Where ATRIUM uses it.** Cited in the hub documentation — `rocrate_export.md` §3 quotes its
standards list, and `atrium_rocrate.py` is designed for "a corpus the DMP sizes at 1.2 million"
pages. The plan itself is a project document, not part of the code repositories.

## Named in the DMP, deliberately not implemented

The DMP's standards column names RO-Crate alongside CIDOC CRM, SKOS, PeriodO, Getty AAT, TEI,
DataCite and IIIF (`rocrate_export.md` §3). SKOS and RO-Crate are implemented (above), and AAT is
a declared namespace. The design keeps heavyweight semantic models — CIDOC CRM, PROV-O, JSON-LD —
off the raw-extraction path: a corpus of more than a million pages is processed as plain JSON
records, and richer views such as an RO-Crate are derived from them afterwards.

| Standard   | What it is                                                                            | Status here                                                                                                                                                                   |
|------------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CIDOC CRM  | the ISO ontology for cultural-heritage information — events, objects, actors, places  | not used; ruled off the extraction path by §3                                                                                                                                 |
| W3C PROV-O | the W3C ontology for provenance                                                       | not used; `atrium_paradata.py` and the record's `provenance` block are the provenance record, and the exporter maps them to RO-Crate rather than to a second provenance model |
| PeriodO    | a gazetteer of scholarly definitions of historical periods                            | not used in these tools                                                                                                                                                       |
| DataCite   | the metadata schema of the DOI registration agency                                    | not used in these tools; releases are cited through `CITATION.cff`                                                                                                            |
| IIIF       | the International Image Interoperability Framework, for serving and annotating images | not used in these tools                                                                                                                                                       |
| TEI        | the Text Encoding Initiative's XML for encoding texts                                 | not in these two tools; nlp-enrich writes TEITOK, a TEI-based format                                                                                                          |

## Sources

Written from the tree at the refs below, plus the public documentation each entry links to.
This table records **provenance**, not a build instruction.

| Source                                                                                                                                                                                                                                                                                                                                                                                  | What was taken from it                                                                                                                              |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `atrium-translator` `v1.2.1-beta` — `processors/{backend,identifier,language,translator,lemmatizer,llm_translator,ct2_translator}.py`, `config.txt`, `para_config.txt`, `docs/translation-backends.md`, `amcr-inputs.txt`, `load_vocab.py`, `eval/`, `service/requirements.txt`, `.github/dependabot.yml`, `CITATION.cff`, `data_samples/my_documents/`                                 | CUBBITT, UDPipe, FastText, AMCR, OAI-PMH, TEATER, CoNLL-U, the back-ends, sacreBLEU / COMET, FastAPI, AIS CR hosts, and every licence consequence   |
| `atrium-page-classification` @ `vit` `adee922` — `setup/{requirements,para_config,config}.txt`, `service/{api.py,inference.py,requirements.txt}`, `Dockerfile`, `docker-compose.yml`, `.github/dependabot.yml`, `.coveragerc`, `.pre-commit-config.yaml`, `data_scripts/`, `result/`, `README.md`, `CITATION.cff`                                                                       | Hugging Face, `ufal/vit-historical-page`, `regnety_160`, the ML stack, PDF rasterisation, Docker, the LINDAT dataset handle, ARÚP/ARÚB result files |
| the shared files both tools vendor — `atrium_vocab.py`, `atrium_rocrate.py`, `atrium_document.py` + schema, `atrium_paradata.py`, `para_licenses.py`, `check_version.py`                                                                                                                                                                                                                | every metadata-standards entry; the licence and Turtle behaviour                                                                                    |
| `atrium-project` @ `main` `7b0b84e` — `docker-tool.reusable.yml`, `security.reusable.yml`, `codeql.reusable.yml`, `docs/templates/Dockerfile`, `docs/templates/workflows/dependabot.example.yml`, `docs/rocrate_export.md` §3, `docs/skos_strategy.md`                                                                                                                                  | Trivy, CodeQL, SBOM, GHCR tagging, Dependabot, the DMP standards                                                                                    |
| `atrium-alto-postprocess` @ `test` `2e2794d` — `page_split.py`, `text_formats.py`; its `docs/text_inputs.md` and `atrium-nlp-enrich`'s `README.md` § "TEITOK XML" as extended on 2026-09-24                                                                                                                                                                                             | the ALTO version note; the two format references                                                                                                    |
| SSH Open Marketplace records `RER7Fw`, `YParYU`, `CizIUW`, `EMhu3X`, `j9fqxo`, `13eHAZ`, `0xSpVP`, `IrpmkB`; `SSHOC/sshoc-marketplace-frontend` (metadata guidelines); `DARIAH-ERIC/atrium-galaxy-tools`; `usegalaxy-eu/infrastructure-playbook`, `usegalaxy-eu/usegalaxy-eu-tools`; `galaxyproject/galaxy` (`datatypes_conf.xml.sample`); `galaxyproject/iwc`, `galaxyproject/planemo` | SSH Open Marketplace, TaDiRAH, Galaxy, WorkflowHub                                                                                                  |
| `https://api.aiscr.cz/2.2/oai?verb=Identify`                                                                                                                                                                                                                                                                                                                                            | the AMCR endpoint's self-description and metadata licence                                                                                           |
