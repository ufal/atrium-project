---
title: External tools & services
nav_order: 3
status: partial
round: 5
issue: 57
authored: true
---

# External tools & services

Every external standard, service, model and institution ATRIUM depends on, in a couple of
sentences each, with a pointer to where it is actually used. Written for someone who has
never met SKOS, LINDAT or ALTO — if a name in this documentation is unfamiliar, it should be
explained here.

!!! info "Written so far: every entry page-classification and the translator depend on"
    That includes the shared standards and infrastructure both tools vendor. Entries that only
    the other three tools use are marked *pending* under their headings and will be written as
    those sections land.

## Data & OCR formats

### ALTO XML

**What it is.** *Analyzed Layout and Text Object* — an XML standard for the output of OCR,
maintained by the Library of Congress. It records not just the recognised text but *where on
the page each piece of it sits*: a document is `Page` → `TextBlock` → `TextLine` → `String`,
and each `String` carries one token in a `CONTENT` attribute plus its bounding box.

**Where ATRIUM uses it.** It is the backbone format of the whole pipeline. `alto-postprocess`
consumes OCR ALTO and emits per-page ALTO under `PAGE_ALTO/`; the
[translator](tools/translator/index.md) rewrites ALTO in place, preserving every coordinate;
the E2E fixture is one ALTO v3 page. Versions v1–v4 are in scope.

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

**Where ATRIUM uses it.** AMCR is harvested over OAI-PMH: `amcr-inputs.txt` holds 15
`GetRecord` URLs against `https://api.aiscr.cz/2.2/oai` — the records in `my_documents/`, which
also holds one ALTO file — and `load_vocab.py` walks the same endpoint with `ListRecords` to build
the vocabulary ([W7](pipelines.md#w7--vocabulary-harvesting--review-the-translators-half)). The
translator's metadata mode does deep recursive namespace extraction specifically so that it can
translate fields *inside* an OAI-PMH envelope.

**Why it is listed here.** Three repositories harvest AMCR over it — the translator, nlp-enrich
and llm-enrich — and all three name the protocol in their READMEs or code, but none says what it
is.

**Onward:** <https://www.openarchives.org/pmh/>

## Models

### Hugging Face Hub

**What it is.** The de-facto public registry for machine-learning models, datasets and the
code to run them — think of it as a package index where the packages are model weights. A
model is addressed as `owner/name`, optionally at a `revision` (a branch or tag), and pulled
by the `huggingface_hub` library into a local cache.

**Where ATRIUM uses it.** Everywhere a model is loaded. It is the single most-referenced
external service in the ecosystem. The classifier pulls its weights with `--hf`; the translator
pulls the FastText language-identification model; `HF_HOME` is set to `/cache/huggingface` in
every container so the cache survives restarts, and `HF_TOKEN` raises the anonymous rate limit
that CI kept hitting.

**Onward:** <https://huggingface.co/>

### `ufal/vit-historical-page`

**What it is.** ATRIUM's own published model repository — the fine-tuned page classifiers,
one revision per generation.

**Where ATRIUM uses it.** `setup/config.txt` `[HF] repo_name`, and hardcoded in
`service/inference.py`. The service warms revisions `v1.4`–`v5.4`, the five-model canonical
ensemble.

!!! warning "`main` does not point at the current generation"
    The repository's `main` branch still resolves to **`v4.3`**, a generation behind what
    `--best` averages. Pull `-rev v4.4` explicitly. See
    [page-classification → Guide](tools/page-classification/guide.md#1--local-install).

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
output to the 639-1 codes the translation API expects, across
[20 languages](tools/translator/reference.md#languages), with a confidence threshold of 0.2. In
ALTO mode it runs once per `TextBlock` so every line in a block is translated consistently.

**Two things to know.** Its weights are **CC BY-NC 4.0**, so auto-detection alone makes a run's
output non-commercial — passing `--source_lang` explicitly avoids that. And if the model fails
to load, detection answers `("en", 0.0)` for every document; that is now reported through
`GET /health?deep=true` rather than swallowed.

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

**What it is.** A controlled vocabulary of archaeological terminology, harvested over GraphQL
rather than OAI-PMH.

**Where ATRIUM uses it.** Together with the AMCR *heslář*, it is one of the two sources
`load_vocab.py` unions into the translation glossary (roughly 5,000 rows as shipped), and
`llm-enrich` builds a nested union of both for its category enum. Its data is CC BY-NC 4.0, so
loading the vocabulary makes a run non-commercial.

## Hosting, repository & registration

### LINDAT/CLARIAH-CZ

**What it is.** The Czech national research infrastructure for language and cultural-heritage
data, hosted at the Institute of Formal and Applied Linguistics (ÚFAL), Charles University. It is
two things at once, and confusing them is easy: a **repository** that stores and issues persistent
identifiers for datasets, and a **service host** that runs public APIs — translation, UDPipe,
NameTag, Korektor.

**Where ATRIUM uses it.** Both roles. The page-classification training dataset is published there;
the translator's default backend and its lemmatiser are LINDAT-hosted APIs; a future hosted
deployment of the ATRIUM services is expected there too, which is why every Agent Skill client
takes its base URL from one environment variable.

**Why it is listed here.** Four live API dependencies and the project's primary dataset citation
rest on it, and **no repository in the ecosystem says what it is.**

**Onward:** <https://lindat.cz/>

### The Handle System, and persistent identifiers

**What it is.** A system for naming digital objects with an identifier that survives the object
moving. A handle looks like `20.500.12800/1-6184` and resolves through a proxy —
`hdl.handle.net/20.500.12800/1-6184` — so the citation stays valid when the hosting URL changes.
DOIs are handles with extra rules on top.

**Where ATRIUM uses it.** `hdl.handle.net/20.500.12800/1-6184` is the **primary citation for the
page-classification training dataset**, 48,499 pages from 37,328 documents. It is cited in four
places across the ecosystem and defined in none of them, which is the reason for this entry.

!!! note "One handle is cited inconsistently"
    `service/README.md`'s footnote points at handle `1-5959` while the main README points at
    `1-6184`. Recorded in
    [page-classification → Known drift](tools/page-classification/reference.md#known-drift--read-this-before-trusting-a-number).

**Onward:** <https://www.handle.net/>

### GHCR — the GitHub Container Registry

**What it is.** GitHub's Docker registry, addressed as `ghcr.io/<owner>/<image>:<tag>`. Images
inherit the repository's visibility and can be pulled anonymously when it is public.

**Where ATRIUM uses it.** Every tool publishes two images per release — a batch image and a
`-api` image — from one Dockerfile with two stages. The E2E smoke test pulls them by tag, which
is what makes `image-tag` the most consequential input in that workflow.

!!! warning "`:latest` moves only on a version tag"
    Only a push to the `test` branch publishes, as `sha-*` and `:test`; pushes to other branches
    publish nothing. `:latest` and the version tag move only on a `v*` tag, and only after the
    release gate passes — `-beta` tags included. So `:latest` means *the most recent release that
    passed the gate*, not *the most recent build* — which matters when reading an E2E result. See
    [W6](pipelines.md) and [Operations](operations.md#images-and-tags).

**Onward:** <https://docs.github.com/packages>

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

**Where ATRIUM uses it.** `atrium_rocrate.py`, vendored into both tools and run by hand, writes
RO-Crate 1.1. A run crate also declares the profile `https://w3id.org/ro/wfrun/process/0.5`. See
[W13](pipelines.md#w13--ro-crate-export--fair-publication) and
[RO-Crate export](contracts/rocrate.md).

**Worth knowing.** The profile pin carries a code comment asking for it to be verified "before the
first published crate" (`atrium_rocrate.py:84-88`): the profiles are versioned independently of
RO-Crate itself, and no crate has been published yet.

**Onward:** <https://www.researchobject.org/ro-crate/>

### JSON-LD

**What it is.** JSON with an `@context` that maps its keys onto web vocabularies, so the same file
is ordinary JSON to a program and linked data to an RDF tool.

**Where ATRIUM uses it.** Two outputs, both written with the Python standard library alone: the
RO-Crate descriptor, and `atrium_vocab.py --jsonld`. `atrium_vocab.schema.json` describes the
shape of the latter; no test or CI step validates against it.

**Worth knowing.** `rocrate_export.md` §3 lists JSON-LD among the standards kept *off* the
extraction path. The two statements agree: nothing writes JSON-LD while a document is being
processed; the exporter produces it afterwards, from records already on disk.

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
schemes, 64 concepts — without `rdflib` or any other dependency.

**Worth knowing.** The output is byte-stable (two runs compare equal), sorted, and free of blank
nodes, and it uses one prefix per scheme (`a-page-category:`, `a-theme:`, …) because, as the code
notes, a Turtle local name cannot carry a `/`. Checked by running it.

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
passing silently — a gate that quietly becomes a no-op cannot be told apart from one that passed
(`atrium_document.py:1044-1061`). page-classification pins `jsonschema>=4.26.0`; the translator
lists it unpinned. The schemas' `$id`s, `https://github.com/ufal/atrium-project/docs/templates/…`,
lack the `/blob/<ref>/` segment and do not resolve.

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

**Worth knowing** — each of these was run, not read:

* The keys mix SPDX identifiers with display names. **SPDX spellings** resolve through the alias
  table (`CC0-1.0`, `CC-BY-SA-4.0`, the `-only` / `-or-later` GPL forms), and every catalogued key
  also resolves in any casing (`bsd-3-clause`, `lgpl-3.0`). Until 2026-09 those four fell through
  as unrecognised.
* An unrecognised licence is treated as the most restrictive, and so **becomes the run's effective
  licence**: its raw string, an empty URL, **both** the non-commercial and share-alike flags set,
  and a warning in the notes. (The flags used to be false, so a consumer reading only them saw a
  permissive licence.) The translator's `llm_api = LLM provider ToS` is unrecognised on purpose,
  so a run on the LLM back-end resolves to that string; a component missing from
  `para_config.txt` is logged as `UNKNOWN` and resolves the same way.
* A run that logs no component at all falls back to CC BY-NC 4.0 (`atrium_paradata.py:25-26`),
  while the resolver on its own returns MIT for an empty list.

**Onward:** <https://spdx.org/licenses/> · <https://creativecommons.org/licenses/>

### ORCID

**What it is.** Persistent identifiers for researchers, of the form `https://orcid.org/0000-…`.

**Where ATRIUM uses it.** Both tools' `CITATION.cff` files list the same four authors, each with an
ORCID. The RO-Crate exporter uses those ORCIDs as the `@id`s of its `Person` entities — hard-coded
in `atrium_rocrate.py:101-107`, because the hub has no `CITATION.cff` of its own to read them from.

**Onward:** <https://orcid.org/>

### CITATION.cff

**What it is.** A small YAML file that tells GitHub, Zenodo and reference managers how to cite a
repository.

**Where ATRIUM uses it.** Both tools, `cff-version: 1.2.0`: page-classification at `1.8.0-beta`
(2026-09-16), the translator at `1.1.0-beta` (2026-09-14). It is also a **release gate**:
`check_version.py` reads the first column-0 `version:`, strips a leading `v`, and fails unless it
equals `para_config.txt`'s `[tool] version` — and, on a tag push, the tag. `security.reusable.yml`
runs it in CI, and each tool's release workflow runs it again.

**Worth knowing.** Neither file carries a DOI, so nothing yet cites a persistent identifier.

**Onward:** <https://citation-file-format.github.io/>

### w3id.org

**What it is.** A community-run permanent-identifier service: `https://w3id.org/<name>/…`
redirects to wherever the content currently lives, so an identifier outlives a change of host.

**Where ATRIUM uses it.** `https://w3id.org/atrium/` is the root of every ATRIUM concept URI
(`atrium_vocab.py`'s `SKOS_BASE`), and RO-Crate's own context and profiles live under
`w3id.org/ro/`.

**Worth knowing.** The `atrium` redirect **has not been registered** (`skos_strategy.md`, item F5:
"optional; blocks nothing"), so no ATRIUM URI resolves today. The URIs identify correctly
regardless; dereferencing waits on a one-file pull request to the w3id repository.

**Onward:** <https://w3id.org/>

## Domain vocabularies

AMCR, TEATER and OAI-PMH are written above. CNEC 2.0 is pending with the nlp-enrich section, and
so is **Getty AAT**: `atrium_vocab.py` declares its namespace and the schema reserves an
`entities[].pid.aat` slot, but no triple uses the prefix and neither tool here writes the slot.

## Data & OCR formats, continued

### CoNLL-U and Universal Dependencies

**What it is.** Universal Dependencies (UD) is a cross-lingual framework for annotating grammar —
lemmas, parts of speech, morphological features, syntax — with treebanks in well over a hundred
languages. CoNLL-U is its file format: one token per line, ten tab-separated columns.

**Where ATRIUM uses it.** The translator's lemmatiser sends text to [UDPipe](#udpipe-2) in
4,000-character chunks and reads the CoNLL-U that comes back: the FORM and LEMMA columns, and the
`Number=` feature from FEATS — which is what lets the vocabulary skip plural tokens
([W7](pipelines.md#w7--vocabulary-harvesting--review-the-translators-half)). Comment lines,
multi-word token ranges and empty nodes are skipped. There are eight UD 2.15 models: cs, sk, pl,
de, fr, en, ru, uk (`processors/lemmatizer.py:82-94`).

**Worth knowing.** A language outside those eight is **not lemmatised**: the single-word
vocabulary pass is skipped for it, with one warning per language. It used to get the Czech model
silently. Requests ask only for the tokenizer and tagger; the dependency parse, which was never
read, is no longer requested.

**Onward:** <https://universaldependencies.org/format.html>

### PDF, and the three tools that rasterise it

**What it is.** A PDF page has to become an image before a vision model can classify it, and the
choice of rasteriser and resolution decides what the model sees.

**Where ATRIUM uses it.** page-classification rasterises PDFs in three different places, with three
different tools:

| Where                                                                                                  | Tool                                  | Resolution                                                              |
|--------------------------------------------------------------------------------------------------------|---------------------------------------|-------------------------------------------------------------------------|
| the service's `POST /predict_document`                                                                 | PyMuPDF (`fitz`), `page.get_pixmap()` | 300 dpi (`PDF_RENDER_DPI`); at most 50 pages (`service/api.py`)         |
| dataset preparation on Unix ([W12](pipelines.md#w12--annotation-round-trip-page-classifications-half)) | poppler's `pdftoppm`                  | 300 dpi by default                                                      |
| dataset preparation on Windows                                                                         | ImageMagick with Ghostscript          | 300 dpi by default                                                      |

**Worth knowing.** The service renders PDF pages at 300 dpi, the resolution the training pages
were made at; PyMuPDF's own default is 72 dpi, which is what the service used before
`PDF_RENDER_DPI` was set. `poppler-utils` is not installed in the image or in CI: only
`pdf2png.sh` calls `pdftoppm`, on the machine that prepares a dataset. PyMuPDF is distributed under
AGPL-3.0 or a commercial licence, and Ghostscript under AGPL-3.0; neither is a component in
`para_config.txt`.

**Onward:** <https://pymupdf.readthedocs.io/> · <https://poppler.freedesktop.org/>

### Formats still pending

PAGE XML, hOCR, METS, TEI P5, TEITOK, IOB2 and the `source.origin` originator set belong with the
alto-postprocess and nlp-enrich sections.

## Models, continued

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
| `numpy`                 | `>=2.4.6,<2.5`         | 2.5 requires Python ≥ 3.12 and every image runs 3.11; Dependabot bumped past the ceiling twice before an ignore rule stopped it           |
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

**Worth knowing.** CT2's default compute type is `int8`. It used to be `int4`, which CTranslate2
4.8.2 rejects outright (`ValueError: Invalid compute type: int4`, checked against a real install),
so the back-end failed on its first load unless `CT2_COMPUTE_TYPE` was set. A compute type the
device cannot run is now refused before the model loads, with the list of valid ones. The model
licence follows `CT2_MODEL_FAMILY`, so an NLLB run is non-commercial. An LLM run's licence
resolves to the unrecognised provider-terms string; see [SPDX and Creative
Commons](#spdx-and-creative-commons).

**Onward:** <https://opennmt.net/CTranslate2/> · <https://huggingface.co/utter-project> ·
<https://huggingface.co/google/madlad400-3b-mt>

### sacreBLEU and COMET

**What it is.** sacreBLEU computes reproducible BLEU and chrF scores against reference
translations. COMET is a neural metric that tracks human judgement more closely.

**Where ATRIUM uses it.** `eval/bakeoff.py`, the translator's planned comparison of back-ends. It
always reports reference-less signals — length ratio, number preservation, glossary hit rate,
empty outputs and failures (counted apart), and each back-end's similarity to the first one
listed — and, given `--refs`, chrF and BLEU per segment and per corpus (sacreBLEU) plus COMET
(`--comet-model`, default `Unbabel/wmt22-comet-da`). COMET-QE is opt-in with `--comet-qe-model`.
Per-segment rows go to `--out`, one row per back-end to `--summary-out`.

**Worth knowing.** Both scorers are imported lazily: without sacreBLEU or `unbabel-comet` (still
commented out of `eval/requirements-eval.txt`, since it pulls torch) the run warns and leaves those
columns blank. The bake-off **has never been run**; no `bakeoff.csv` is committed.

**Onward:** <https://github.com/mjpost/sacrebleu> · <https://unbabel.github.io/COMET/>

### Models still pending

`Qwen/Qwen2.5-0.5B`, `hantian/layoutreader`, `THUDM/glm-4v-9b`, the LLM registry, NameTag 3,
Korektor and the keyword extractors belong with the nlp-enrich and llm-enrich sections.

## Runtime & infrastructure

### Docker and Compose

**What it is.** Docker packages a program with everything it needs into an image; Compose describes
how to run one or more containers from those images.

**Where ATRIUM uses it.** One `Dockerfile` per tool with two targets: `base`, the batch image, and
`api`, which runs `python -m service.api`. Both build on `python:3.11-slim` (the translator and
the hub's template pin it by digest; page-classification still floats the tag), run as uid
10001, and keep the Hugging Face cache at `/cache/huggingface`. Compose runs the batch service by
default and the HTTP service under the `api` profile.

**Worth knowing.** page-classification's `api` service `extends` the batch one, so it has to re-set
`ATRIUM_RUNNER_IMAGE`, which it would otherwise inherit from the batch image; the translator
defines its two services separately. Details, including the image tags, are in
[Operations](operations.md).

**Onward:** <https://docs.docker.com/compose/>

### Kubernetes

**What it is.** The container orchestrator the partner institutions will run the services on.

**Where ATRIUM uses it.** Not in either tool repository. The hub ships the template,
`docs/templates/k8s/atrium-service.deployment.yaml`: `startupProbe` and `readinessProbe` on
`/ready`, `livenessProbe` on `/health`, a 60-second termination grace. The probe table,
environment and sizing for each tool are on [Operations](operations.md).

**Worth knowing.** The template's image line is `ghcr.io/ufal/atrium-<tool>:<version>-api`, a tag
that is never published — see [Operations → Images and tags](operations.md#images-and-tags).

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
`service/api.py`. Both pin `fastapi>=0.141.1` and `uvicorn[standard]>=0.53.0`. The translator's
used to be a plain `uvicorn>=0.52.4`, without the `[standard]` extras and never bumped, because
Dependabot did not watch its `service/`; it now does.

**Onward:** <https://fastapi.tiangolo.com/> · <https://www.uvicorn.org/>

### ruff, pre-commit and Dependabot

**What it is.** ruff is a Python linter and formatter; pre-commit runs such checks before each
commit and in CI; Dependabot opens pull requests when a pinned dependency has a newer version.

**Where ATRIUM uses it.** Both tools run pre-commit-hooks `v6.0.0` and ruff `v0.15.18`
(page-classification adds shellcheck `v0.11.0`), with ruff at line length 120, Python 3.11, rules
`E`, `F`, `W`, `I`. The hub's own `.pre-commit-config.yaml` is older — `v5.0.0`, `v0.9.0`,
`v0.10.0`. Dependabot in page-classification watches GitHub Actions and pip in `/setup` and
`/service`; in the translator it watches GitHub Actions, pip in `/`, `/service` and `/eval`
(ignoring numpy ≥ 2.0, which fasttext-wheel 0.9.2 cannot run on) and the `docker` base image.

**Worth knowing.** A `docker` ecosystem only helps with a **digest-pinned** base: a bare
`python:3.11-slim` never changes name, so there is nothing to propose. The translator, the hub
(for `docs/templates/Dockerfile`) and the hub's example configuration now pin by digest and
declare the ecosystem, holding the tag on 3.11; the other tools still float the tag. That gap is
what lay behind [the base image that blocked a
release](tools/translator/history.md#the-base-image-that-blocked-a-release).

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
* **Codecov** receives coverage only when a token is configured. The floors that actually fail a
  build are the `.coveragerc` `fail_under` values: 38 % for page-classification, 81 % for the
  translator.

**Onward:** <https://trivy.dev/> · <https://codeql.github.com/> ·
<https://docs.oasis-open.org/sarif/sarif/v2.1.0/> · <https://about.codecov.io/>

### BuildKit SBOM and provenance

**What it is.** A software bill of materials lists what an image contains; a provenance attestation
records how it was built. BuildKit can attach both to an image as it is pushed.

**Where ATRIUM uses it.** `docker/build-push-action` with `sbom: true` and `provenance: true`, on
every published image. It replaced a separate SBOM job that could race the image it described.

**Onward:** <https://docs.docker.com/build/metadata/attestations/>

### Infrastructure still pending

vLLM, Ollama, flexiconv and alto-tools belong with the llm-enrich and alto-postprocess sections.

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

**Worth knowing.** None of the public documentation expands the two acronyms; the expansion here is
the institutes' own name, as it appears in their records.

**Onward:** <https://www.arup.cas.cz/> · <https://www.arub.cz/>

### AIS CR — `aiscr.cz`

**Where ATRIUM uses it.** `aiscr.cz` hosts everything the translator harvests or links to: the AMCR
OAI-PMH endpoint `api.aiscr.cz/2.2/oai`, AMCR's identifier namespace `api.aiscr.cz/id/` (also a
prefix in the SKOS registry), the AMCR XML schema under `api.aiscr.cz/schema/amcr/2.2/`, and TEATER
at `teater.aiscr.cz` — GraphQL at `/api/graphql`, identifiers under `/id/`.

**Worth knowing.** The acronym is **expanded nowhere** in the ecosystem. This entry records only
what the code relies on; the system's own site describes the rest.

**Onward:** <https://www.aiscr.cz/>

### The data management plan

**What it is.** The project's data management plan (DMP), which names the standards the project
commits to.

**Where ATRIUM uses it.** Cited in the hub documentation — `rocrate_export.md` §3 quotes its
standards list, and `atrium_rocrate.py` is designed for "a corpus the DMP sizes at 1.2 million"
pages — but the document itself is in no repository.

## Named in the DMP, deliberately not implemented

The DMP's standards column names RO-Crate alongside CIDOC CRM, SKOS, PeriodO, Getty AAT, TEI,
DataCite and IIIF (`rocrate_export.md` §3). SKOS and RO-Crate are implemented (above), and AAT is a
declared prefix only. A search of both tools' trees finds **no occurrence** of CIDOC CRM, PROV-O,
PeriodO, DataCite or IIIF outside the vendored exporter's design notes. §3 gives a reason for
leaving out CIDOC CRM, PROV-O and JSON-LD — a corpus of more than a million pages cannot afford them
*during raw extraction* — and gives none for the others.

| Standard   | What it is                                                                            | Status here                                                                                                                                                                                                                  |
|------------|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CIDOC CRM  | the ISO ontology for cultural-heritage information — events, objects, actors, places  | not used; ruled off the extraction path by §3                                                                                                                                                                                |
| W3C PROV-O | the W3C ontology for provenance                                                       | not used, and **not in the DMP's list** — it appears only in §3's "not on the hot path" sentence. `atrium_paradata.py` is the provenance record, and the exporter's own docstring says it is "not a second provenance model" |
| PeriodO    | a gazetteer of scholarly definitions of historical periods                            | not used; no reason recorded                                                                                                                                                                                                 |
| DataCite   | the metadata schema of the DOI registration agency                                    | not used; no reason recorded — and no repository has a DOI, not even in a `CITATION.cff` ([RO-Crate export](contracts/rocrate.md#what-a-crate-cannot-yet-say))                                                               |
| IIIF       | the International Image Interoperability Framework, for serving and annotating images | not used; no reason recorded                                                                                                                                                                                                 |
| TEI        | the Text Encoding Initiative's XML for encoding texts                                 | not in these two tools; nlp-enrich writes TEITOK, a TEI-based format — pending with that section                                                                                                                             |

## Sources

Written from the tree at the refs below, plus the public documentation each entry links to.
This table records **provenance**, not a build instruction.

| Source                                                                                                                                                                                                                                                                                  | What was taken from it                                                                                      |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `atrium-translator` @ `master` `88242fe` — `processors/{backend,identifier,translator}.py`, `config.txt`, `para_config.txt`, `docs/translation-backends.md`, `amcr-inputs.txt`                                                                                                          | CUBBITT, UDPipe, FastText, AMCR, OAI-PMH, TEATER, and every licence consequence                             |
| `atrium-page-classification` @ `vit` `8415ce7` — `setup/config.txt`, `service/inference.py`, `README.md`                                                                                                                                                                                | Hugging Face, `ufal/vit-historical-page`, `regnety_160`, the LINDAT dataset handle                          |
| `atrium-page-classification` @ `vit` `8c98a3d` — `setup/{requirements,para_config,config}.txt`, `service/{api.py,requirements.txt}`, `Dockerfile`, `docker-compose.yml`, `.github/dependabot.yml`, `.coveragerc`, `.pre-commit-config.yaml`, `data_scripts/`, `result/`, `CITATION.cff` | the ML stack, PDF rasterisation, Docker, Dependabot, pre-commit, coverage, ARÚP/ARÚB result files (round 5) |
| `atrium-translator` @ `master` `88242fe` — `processors/{lemmatizer,backend,llm_translator,ct2_translator}.py`, `load_vocab.py`, `eval/`, `service/requirements.txt`, `.github/dependabot.yml`, `CITATION.cff`, `data_samples/my_documents/`                                             | CoNLL-U, back-ends, sacreBLEU / COMET, FastAPI pins, AIS CR hosts, the OAI-PMH count (round 5)              |
| the shared files both tools vendor — `atrium_vocab.py`, `atrium_rocrate.py`, `atrium_document.py` + schema, `atrium_paradata.py`, `para_licenses.py`, `check_version.py`                                                                                                                | every metadata-standards entry; the licence and Turtle claims were checked by running the modules (round 5) |
| `atrium-project` @ `test` `88bc1a6` — `docker-tool.reusable.yml`, `security.reusable.yml`, `codeql.reusable.yml`, `.pre-commit-config.yaml`, `.github/dependabot.yml`, `docs/rocrate_export.md` §3, `docs/skos_strategy.md` §3.2 / F5                                                   | Trivy, CodeQL, SBOM, the hub's own pins, the DMP standards and their status (round 5)                       |
| the READMEs of `atrium-nlp-enrich` @ `master` and `atrium-llm-enrich` @ `main`                                                                                                                                                                                                          | that both name OAI-PMH (round 5 correction)                                                                 |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`, `docker-tool.reusable.yml`                                                                                                                                                                                                   | GHCR tagging behaviour                                                                                      |
