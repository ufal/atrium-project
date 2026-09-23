---
title: translator
nav_order: 50
status: published
round: 6
issue: 57
repo: atrium-translator
role: index
---

# translator

<div class="atrium-pipeline" markdown="0">
<a href="../page-classification/">page-classification</a>
<a href="https://ufal.github.io/atrium-alto-postprocess/">alto-postprocess</a>
<span class="here">translator</span>
<a href="https://ufal.github.io/atrium-nlp-enrich/">nlp-enrich</a>
<a href="https://ufal.github.io/atrium-llm-enrich/">llm-enrich</a>
</div>

**Translates XML in place.** Every tag, every namespace, every attribute and — for ALTO —
every coordinate survives; only the text changes. The output is the same document in
another language, not a rendering of it.

Two kinds of input, one core:

* **ALTO OCR pages** — the positional text layer produced by
  [alto-postprocess](https://ufal.github.io/atrium-alto-postprocess/).
* **[AMCR](../../external-tools.md#amcr-metadata-xml) metadata records**, bare or inside
  [OAI-PMH](../../external-tools.md#oai-pmh) envelopes — translated at XPath targets named
  in `amcr-fields.txt`.

The default translation engine is LINDAT's CUBBITT service; an OpenAI-compatible LLM API
or a self-hosted CTranslate2 model can be selected instead. Archaeological terms are kept
consistent through a controlled Czech–English vocabulary.

It runs as a batch CLI (`main.py`), as a containerised service (`POST /translate`), and as
an [Agent Skill](../../agent-skills.md).

## What it takes in, what it hands on

|                          |                                                                                                                                                       |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                   | One ALTO or AMCR XML file, or a directory of them, optionally with an ATRIUM document record to accrete onto                                          |
| **Out**                  | `<name>_<target_lang>.<ext>` — the translated document; a `_log.csv` of every source/target text pair; a paradata JSON; optionally the updated record |
| **Writes in the record** | The `translations` block, and `derived_from.translated_xml` — the name of the translated file                                                         |
| **Reads from upstream**  | `PAGE_ALTO/<doc>/<doc>-N.alto.xml` from alto-postprocess                                                                                              |

## Where it sits — the translator is a terminal branch

The translator reads the per-page ALTO that alto-postprocess writes, and its output is an
**end product**: an English edition of the page or record, for readers and for
publication. The later stages work on the original text — `nlp-enrich` reads
`DOC_LINE_CATEG/` and the original `ALTO/` — so no stage reads `TRANSLATED/`.

What persists in the pipeline is a **reference**: the translated document is recorded in
the document record as `derived_from.translated_xml`, and the `translations` block records
how it was made. So the file topology fans out from `alto-postprocess` and stops here,
while the *record* runs on through every stage. [Pipelines](../../pipelines.md) draws both
layers.

## How a translation is made

**ALTO pages** keep their geometry. Each text block is translated twice: once whole, for a
fluent translation, and once line by line, only to learn how many words belong on each
line. The fluent translation is then split across the original lines and written into the
original word boxes, so every coordinate survives.
[Reference → ALTO dual-pass reconstruction](reference.md#alto-dual-pass-reconstruction)
draws it step by step.

**Metadata records** are translated field by field: each XPath in `amcr-fields.txt` selects
the free-text fields to translate, and only their text changes. With `--output-mode append`
the Czech is kept and the English is added beside it, marked `xml:lang="en"`.
[Reference → Metadata mode](reference.md#metadata-amcr-mode) has the detail.

**The source language** is detected by FastText unless it is given — per text block in ALTO,
per field in metadata — so a record that mixes languages is handled piece by piece.

**Controlled terms** from the AMCR and TEATER thesauri keep their fixed English equivalent:
they are masked before translation and restored afterwards (CUBBITT), or given to the model
as a glossary (LLM backends). See
[Reference → Vocabulary protection](reference.md#vocabulary-protection).

## The three backends

| Name                     | Class              | Glossary support                             | Configured by                                                                                                                                                                 |
|--------------------------|--------------------|----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`lindat`** *(default)* | `LindatTranslator` | ✗                                            | `TRANSLATION_URL`, defaulting to LINDAT's CUBBITT API. Model names are fetched **live** from the API and composed as `<src>-<tgt>`                                            |
| `openai_compatible`      | `LLMTranslator`    | ✓ — glossary injected into the prompt        | `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, optional `LLM_PROVIDER` / `LLM_LANGUAGES`. Raw REST, no vendor SDK. **No model id is hardcoded**                                  |
| `ct2`                    | `CT2Translator`    | ✓ for `eurollm` (prompt); ✗ for NMT families | `CT2_MODEL_DIR`, `CT2_MODEL_FAMILY` (`eurollm` / `madlad` / `nllb` / `opus`), `CT2_SP_MODEL`, `CT2_DEVICE`, `CT2_COMPUTE_TYPE` (default `int8`). Needs `requirements-ct2.txt` |

Selection order: `--backend` → `config.txt` `translation_backend` → `TRANSLATION_BACKEND`
→ `lindat`. An unknown name raises with the available list.

!!! note "The `ct2` backend"
    The CTranslate2 self-hosting backend in `processors/ct2_translator.py` runs EuroLLM,
    MADLAD-400, NLLB-200 or Opus-MT from a converted model directory. Its dependencies are
    optional: `ctranslate2` and `sentencepiece` load on the first translation, which fails
    with an install hint when `requirements-ct2.txt` is missing. Before the model loads,
    `CT2_COMPUTE_TYPE` (default `int8`) is checked against what `CT2_DEVICE` supports, and a
    bad value names the valid ones.

    The licence follows the model family: EuroLLM and MADLAD-400 are Apache-2.0, Opus-MT is
    recorded as CC BY 4.0, and NLLB-200 is **CC BY-NC 4.0**. For commercial use, choose one
    of the permissive families; [Reference → Licence](reference.md#licence-is-computed-not-declared)
    gives the full permissive recipe.

## Evaluating translation quality

Archival OCR text rarely comes with a reference translation, so the repository's
evaluation harness, `eval/bakeoff.py`, measures backends in two ways and reports both side
by side, one summary row per backend:

* **with references**, when a reference file is supplied: chrF and BLEU through sacreBLEU,
  and COMET — the standard machine-translation metrics;
* **without references**, always: whether numbers, dates and codes survive, how often the
  output is empty, the output-to-input length ratio (a guard against truncation and
  invented text), how many expected glossary terms appear, and how far each backend's
  output diverges from the baseline's; reference-free COMET-QE can be switched on as well.

It calls the real backends over the network, so it is run by hand against a chosen sample
rather than in CI. [Reference → Other entry points](reference.md#other-entry-points) lists
its flags, and `docs/translation-backends.md` in the repository compares the candidate
models it was built to choose between.

## Languages

Twenty, mapped ISO 639-3 → ISO 639-1 by the language identifier: `cs`, `en`, `fr`, `de`,
`ru`, `pl`, `uk`, `sk`, `bg`, `hr`, `sl`, `lv`, `lt`, `et`, `hu`, `ro`, `es`, `it`, `nl`,
`hi`. Detection uses `facebook/fasttext-language-identification`; in ALTO mode it runs
**once per `TextBlock`** so every line in a block is translated consistently.

Whether a given pair is actually served depends on the backend — CUBBITT is Czech-centric,
and offers the pairs the LINDAT service lists. The repository's backend evaluation document
compares nine candidates on exactly this axis.

## Licence — computed per run, not declared

Every component carries a licence and a condition, and the paradata records what the run
resolved to. A **default run resolves to CC BY-NC-SA 4.0**, because CUBBITT's models are
CC BY-NC-SA and FastText's weights are CC BY-NC. A permissive run is possible but has to be
assembled deliberately — see
[Reference](reference.md#licence-is-computed-not-declared).

## Where to go next

* **[Guide](guide.md)** — install it, run it, troubleshoot it
* **[Reference](reference.md)** — every flag, every endpoint, every output field, and how each mode works
* **[Changelog](changelog.md)** — the release history, grouped into arcs
* **[History](history.md)** — why it is shaped the way it is
* **[Pipelines](../../pipelines.md)** — where this stage sits, end to end
* **[External tools & services](../../external-tools.md)** — LINDAT, CUBBITT, UDPipe, ALTO, AMCR

## Sources

Read from `ufal/atrium-translator` at branch **`master`**, commit `71feaef` (2026-09-23),
and from the hub's canonical documents. This table records **provenance**: what this page
was written from, not a build instruction.

| Source                                                    | What was taken from it                                             |
|-----------------------------------------------------------|--------------------------------------------------------------------|
| `README.md` §§ Features, Logic Overview, Paradata         | behaviour, language handling, output description                   |
| `processors/backend.py`, `processors/ct2_translator.py`   | the registry, the protocol, the selection order, the `ct2` backend |
| `processors/identifier.py`                                | the 20 language codes                                              |
| `utils.py`                                                | the ALTO and metadata processing summarised above                  |
| `eval/bakeoff.py`                                         | the evaluation metrics                                             |
| `para_config.txt`                                         | the licence component table                                        |
| `atrium-project/docs/templates/shared/atrium_document.py` | block ownership                                                    |
| `atrium-project/docs/document_schema.md`                  | the write/read contract                                            |
