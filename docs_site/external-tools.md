---
title: External tools & services
nav_order: 3
status: partial
round: 3
issue: 57
authored: true
---

# External tools & services

Every external standard, service, model and institution ATRIUM depends on, in a couple of
sentences each, with a pointer to where it is actually used. Written for someone who has
never met SKOS, LINDAT or ALTO — if a name in this documentation is unfamiliar, it should be
explained here.

!!! info "Written so far: the entries page-classification and the translator depend on"
    This round wrote the entries those two tools need. The remaining categories keep their
    outline and will be filled as the other three tool sections land.

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

**Where ATRIUM uses it.** AMCR is harvested over OAI-PMH: `amcr-inputs.txt` holds 16
`GetRecord` URLs against `https://api.aiscr.cz/2.2/oai`, and `load_vocab.py` walks the same
endpoint to build the vocabulary. The translator's metadata mode does deep recursive namespace
extraction specifically so that it can translate fields *inside* an OAI-PMH envelope.

**Why it is listed here.** The protocol is used in three repositories and **named as a
protocol in none of them** — the code simply fetches URLs that happen to be OAI-PMH endpoints.

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
(`czech-pdt-ud-2.15`, `slovak-snk-ud-2.15`, and six more). `nlp-enrich` calls the same service,
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
    A branch push publishes `sha-*` and `:test`, never `:latest`. So `:latest` means *the most
    recent released version*, not *the most recent build* — which matters when reading an E2E
    result. See [W6](pipelines.md).

**Onward:** <https://docs.github.com/packages>

## Still to write

These entries keep their outline from the round-2 draft and are filled as the remaining tool
sections land.

### Metadata standards & serialisations

<!-- SKOS · RO-Crate 1.1 + Process Run Crate · JSON-LD · schema.org · Turtle/RDF · Dublin Core · JSON Schema · SPDX & Creative Commons · ORCID · CITATION.cff · w3id.org -->

SKOS and RO-Crate already have pages of their own —
[SKOS & the ATRIUM vocabulary](contracts/skos.md) and
[RO-Crate export](contracts/rocrate.md). The rest are pending.

### Domain vocabularies

<!-- CNEC 2.0 · Getty AAT -->

AMCR, TEATER and OAI-PMH are written above. CNEC 2.0 and Getty AAT are pending.

### Data & OCR formats, continued

<!-- PAGE XML · hOCR · METS · TEI P5 · TEITOK · CoNLL-U / UD · IOB2 · the `source.origin` originator set -->

ALTO and AMCR are written above. The rest are pending, and belong with the
alto-postprocess and nlp-enrich sections.

### Models, continued

<!-- Qwen/Qwen2.5-0.5B · hantian/layoutreader · THUDM/glm-4v-9b · the LLM registry · NameTag 3 · Korektor · KER / YAKE / KeyBERT -->

Pending, with the nlp-enrich and llm-enrich sections.

### Runtime & infrastructure

<!-- Docker & Compose · Kubernetes · GitHub Actions · vLLM · Ollama · FastAPI · flexiconv · alto-tools · ruff / pre-commit / Dependabot · Trivy / CodeQL / Codecov -->

Pending. [Operations](operations.md) covers the deployment side today.

### The ATRIUM project itself

<!-- the four bridged infrastructures (DARIAH · ARIADNE · CLARIN · OPERAS) · UFAL · ARÚP / ARÚB / AISCR · the work packages · the DMP -->

Pending — and the highest-value gap in this page, because **the acronyms ARÚP, ARÚB and AISCR
are never expanded anywhere in the ecosystem**, while naming the institutions that provide the
data and host the deployment.

### Named in the DMP, deliberately not implemented

<!-- CIDOC-CRM, PROV-O, PeriodO, DataCite, IIIF -->

Pending. [RO-Crate export](contracts/rocrate.md) §3 is the definitive statement on why these
were left off the hot path for a 1.2 M-page corpus, and it deserves surfacing here rather than
staying buried.

## Sources

Written from the tree at the refs below, plus the public documentation each entry links to.
This table records **provenance**, not a build instruction.

| Source                                                                                                                                                                         | What was taken from it                                                             |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `atrium-translator` @ `master` `88242fe` — `processors/{backend,identifier,translator}.py`, `config.txt`, `para_config.txt`, `docs/translation-backends.md`, `amcr-inputs.txt` | CUBBITT, UDPipe, FastText, AMCR, OAI-PMH, TEATER, and every licence consequence    |
| `atrium-page-classification` @ `vit` `8415ce7` — `setup/config.txt`, `service/inference.py`, `README.md`                                                                       | Hugging Face, `ufal/vit-historical-page`, `regnety_160`, the LINDAT dataset handle |
| `atrium-project/.github/workflows/e2e-pipeline-smoke.yml`, `docker-tool.reusable.yml`                                                                                          | GHCR tagging behaviour                                                             |
| `atrium-project/docs/skos_strategy.md`, `docs/rocrate_export.md`                                                                                                               | pointers for the pending standards entries                                         |
