---
title: translator
nav_order: 50
status: published
round: 3
issue: 57
repo: atrium-translator
role: index
---

# translator

<div class="atrium-pipeline" markdown="0">
<a href="../page-classification/index.md">page-classification</a>
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
* **AMCR metadata records**, including OAI-PMH envelopes — translated at XPath targets
  named in `amcr-fields.txt`.

It runs as a batch CLI (`main.py`), as a containerised service (`POST /translate`), and as
an Agent Skill.

## What it takes in, what it hands on

|                         |                                                                                                                                                       |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **In**                  | One ALTO or AMCR XML file, or a directory of them, optionally with an ATRIUM document record to accrete onto                                          |
| **Out**                 | `<name>_<target_lang>.<ext>` — the translated document; a `_log.csv` of every source/target text pair; a paradata JSON; optionally the updated record |
| **Owns in the record**  | The `translations` block, and `entities[].translation_en`                                                                                             |
| **Reads from upstream** | `PAGE_ALTO/<doc>/<doc>-N.alto.xml` from alto-postprocess                                                                                              |

## Where it sits — the translator is a terminal branch

This is the fact most likely to surprise someone reading a pipeline diagram.

!!! warning "Nothing downstream reads the translated files"
    **No repository in the ecosystem reads `TRANSLATED/`** — zero hits across all four
    downstream repositories. `nlp-enrich` reads `DOC_LINE_CATEG/` and the *original*
    `ALTO/`, never the translator's output.

    What persists is a **reference**: the translated document is recorded in the document
    record as `derived_from.translated_xml`, and the `translations` block records how it
    was made. The translation is a published artefact and a provenance entry, not an input
    to a later stage.

    So the file topology fans out from `alto-postprocess` and stops here. What is linear is
    the *record*. [Pipelines](../../pipelines.md) draws both layers.

## The three backends

| Name                     | Class              | Glossary support                             | Configured by                                                                                                                                                                 |
|--------------------------|--------------------|----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`lindat`** *(default)* | `LindatTranslator` | ✗                                            | `TRANSLATION_URL`, defaulting to LINDAT's CUBBITT API. Model names are fetched **live** from the API and composed as `<src>-<tgt>`                                            |
| `openai_compatible`      | `LLMTranslator`    | ✓ — glossary injected into the prompt        | `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, optional `LLM_PROVIDER` / `LLM_LANGUAGES`. Raw REST, no vendor SDK. **No model id is hardcoded**                                  |
| `ct2`                    | `CT2Translator`    | ✓ for `eurollm` (prompt); ✗ for NMT families | `CT2_MODEL_DIR`, `CT2_MODEL_FAMILY` (`eurollm` / `madlad` / `nllb` / `opus`), `CT2_SP_MODEL`, `CT2_DEVICE`, `CT2_COMPUTE_TYPE` (default `int8`). Needs `requirements-ct2.txt` |

Selection order: `--backend` → `config.txt` `translation_backend` → `TRANSLATION_BACKEND`
→ `lindat`. An unknown name raises with the available list.

!!! note "`ct2` is registered; its dependencies stay optional"
    The CTranslate2 self-hosting backend in `processors/ct2_translator.py` runs EuroLLM,
    MADLAD-400, NLLB-200 or Opus-MT. It is registered, but importing it never pulls in
    `ctranslate2` or `sentencepiece`: those load on the first translation, which fails with
    an install hint when `requirements-ct2.txt` is missing. Before the model loads,
    `CT2_COMPUTE_TYPE` is checked against what `CT2_DEVICE` supports, and a bad value names
    the valid ones. (The default used to be `int4`, which CTranslate2 does not have, so
    every load without an explicit setting failed.)

    The licence follows the model family: EuroLLM and MADLAD-400 are Apache-2.0, Opus-MT is
    recorded as CC BY 4.0, and NLLB-200 is **CC BY-NC 4.0**. The repository's licensing
    section tells commercial users to "select a self-hosted CTranslate2 model", which is
    true only for the permissive families. [Reference → Licence](reference.md#licence-is-computed-not-declared)
    gives the full permissive recipe.

## How well it translates: unknown, and that is the honest answer

!!! danger "No translation-quality metric has ever been produced for this tool"
    `eval/bakeoff.py` is a complete harness — reference-based chrF and BLEU through
    `sacrebleu` and COMET through `unbabel-comet` when `--refs` is supplied, opt-in COMET-QE,
    reference-less quality estimation otherwise (number and date preservation, empty-output
    rate, length ratio, terminology hit rate), and a per-backend summary CSV. It has
    **never been run**: the issue plan lists "execute `eval/bakeoff.py`" as pending, no
    `bakeoff.csv` is committed, and `unbabel-comet` stays an opt-in install in the
    evaluation requirements.

    There is no BLEU, chrF or COMET number anywhere in the repository. Any figure quoted
    for this tool's translation quality did not come from here.

What *has* been measured is structural, on a 79-page ALTO sample and 15 AMCR records:

| Measurement                                                | Value                                                                |
|------------------------------------------------------------|----------------------------------------------------------------------|
| API calls for the 79-page sample, with page batching       | **~158**, against up to **~3,288** unbatched                         |
| ALTO boxes in, boxes out                                   | 7,229 → 7,229 — **none resized**                                     |
| Boxes no longer holding exactly one word after translation | **528 of 7,229 (7.3 %)** — 224 empty, 304 multi-word                 |
| `xml:lang="cs"` attributes across the AMCR samples         | 426, on 23 element types — and **0** on translated free-text fields  |
| Throughput on the 16-document sample                       | 16 files in 46.45 s ≈ 20.7 files/min, 113 protected vocabulary terms |

That 7.3 % is not a defect to be fixed; it is a consequence of how the alignment works, and
[Reference](reference.md#alto-dual-pass-reconstruction) explains why a per-`String`
alternative reading would be meaningless.

## Languages

Twenty, mapped ISO 639-3 → ISO 639-1 by the language identifier: `cs`, `en`, `fr`, `de`,
`ru`, `pl`, `uk`, `sk`, `bg`, `hr`, `sl`, `lv`, `lt`, `et`, `hu`, `ro`, `es`, `it`, `nl`,
`hi`. Detection uses `facebook/fasttext-language-identification`; in ALTO mode it runs
**once per `TextBlock`** so every line in a block is translated consistently.

Whether a given pair is actually served depends on the backend — CUBBITT is Czech-centric.
The repository's backend evaluation document compares nine candidates on exactly this axis.

## Licence — computed per run, not declared

Every component carries a licence and a condition, and the paradata records what the run
resolved to. A **default run resolves to CC BY-NC-SA 4.0**, because CUBBITT's models are
CC BY-NC-SA and FastText's weights are CC BY-NC. A permissive run is possible but has to be
assembled deliberately — see
[Reference](reference.md#licence-is-computed-not-declared).

## Where to go next

* **[Guide](guide.md)** — install it, run it, and the failure modes nobody wrote down
* **[Reference](reference.md)** — every flag, every endpoint, every output field
* **[Changelog](changelog.md)** — 23 releases, grouped by what actually changed
* **[History](history.md)** — why it is shaped the way it is
* **[Pipelines](../../pipelines.md)** — where this stage sits, end to end
* **[External tools & services](../../external-tools.md)** — LINDAT, CUBBITT, UDPipe, ALTO, AMCR

## Sources

Read from `ufal/atrium-translator` at branch **`master`**, commit `88242fe` (2026-09-21),
and from the hub's canonical documents. This table records **provenance**: what this page
was written from, not a build instruction.

| Source                                                            | What was taken from it                                             |
|-------------------------------------------------------------------|--------------------------------------------------------------------|
| `README.md` §§ Features, Logic Overview, Paradata                 | behaviour, language handling, output description                   |
| `processors/backend.py:40-111`                                    | the registry, the protocol, the selection order, the `ct2` comment |
| `processors/identifier.py:10-34`                                  | the 20 language codes                                              |
| `para_config.txt`                                                 | the licence component table                                        |
| `agent_dev_logs/digests/46.digest.md`                             | every structural measurement quoted above                          |
| `tests/test_bakeoff.py`, `agent_dev_logs/plans/4.plan.md`         | that the bake-off has never been run                               |
| `atrium-project/docs/templates/shared/atrium_document.py:108-118` | block ownership                                                    |
| `atrium-project/docs/document_schema.md:130-142`                  | the write/read contract                                            |
