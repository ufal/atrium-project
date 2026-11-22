# Document understanding: benchmarks and models for the extraction route

> **Status:** research note, added 2026-11-20 for [#22](https://github.com/ufal/atrium-project/issues/22).
> It changes nothing in the AMČR pilot route. Facts were checked on 2026-11-20 against the sources
> linked in each table.
> **Scope:** which public benchmarks and metrics fit ATRIUM's document understanding (DU), and which
> open-weight models to run on the ATRIUM gold set when #22 resumes after the pilot.

## In short

- The evaluation criteria come first: faithful text, no invented values, document structure, schema adherence, long inputs, long outputs, and Czech and German.
- No public benchmark covers Czech field reports with forms and JSON output, so the ATRIUM gold set stays the measure; public sets give context.
- Key information is scored per field by value type, as in ExtractBench, with omissions and hallucinations counted apart.
- Printed Czech is close to solved for strong models; German old scripts and handwriting are the open risk.
- Proposed first run: Qwen3.8-27B as the default, two compact OCR challengers, PP-OCRv6 and PERO-OCR as baselines; no ATRIUM page is scored yet.

## What is the extraction route for?

The route reads a field report and returns its key information as JSON, and its text as Markdown
(tables in HTML) or plain text. The aim is FAIR storage and search, so correct values and a correct
reading order matter. Coordinates do not: a model may use the layout internally, but boxes are not an
output we score.

| Input                                           | Path to the model                                            | The model reads |
|-------------------------------------------------|--------------------------------------------------------------|-----------------|
| Born-digital PDF, DOCX, ODT, other office files | digital-convert, the record, then `json_to_md`               | text            |
| ALTO, PAGE or TEITOK XML                        | `xml_to_md`                                                  | text            |
| Scans, photos, pages that need ATR              | a vision-language model (VLM): Markdown, or JSON in one pass | the page image  |

Every input ends in the same Markdown-to-JSON step, with one schema and one scorer. Text inputs skip
the vision step: they cost less, and their characters are exact.

**What this note does not change:**

- The pilot keeps the agreed route: the layout JSON from digital-convert and the ATR, and the record
  built by ocr-postprocess. A VLM route would be a separate decision after the pilot, measured
  against that route.
- Choosing the ATR's OCR engine belongs to AMČR's own evaluation.
- In the pilot, page categories are an optional weak signal and never choose a route (ARÚP's output
  contract of 12 November 2026). Here they only stratify the gold set and the scores.
- The key-information JSON is a benchmark output, not a record block. The record has no `forms`
  block.

## Which evaluation criteria come first?

Model cards of vision-language models report results by capability area. The card of
[Inkling 2 Small](https://huggingface.co/thinkingmachines/Inkling-2-Small), for example, groups them into
visual perception, visual reasoning, long context, factuality, instruction following and
multilinguality. Our task needs only some of these, and two things that no card reports. The criteria
below are settled first: they decide which public numbers are worth reading and what our own run must
measure. They are ranked by how much a failure would harm FAIR storage.

| # | Criterion                               | Why it matters for field reports                                                                   | Proxies on model cards                                                                                                                                                                                                                                                       | Our measure                                                                                                  |
|---|-----------------------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 1 | Faithful text on degraded pages         | typescripts, carbon copies and handwriting; one misread digit or diacritic changes a value         | OmniDocBench components, MDPBench, CHURRO-DS; [PerceptionBench](https://arxiv.org/pdf/2607.24957) for perception errors, perception-related hallucination included                                                                                                           | CER and NED by tier and page category; CER with diacritics removed                                           |
| 2 | No invented values                      | an invented identifier creates a false link in the archive; an empty field costs less than a guess | the non-hallucination rate of [AA-Omniscience](https://arxiv.org/pdf/2511.13029), which rewards abstaining; [SimpleVQA](https://arxiv.org/pdf/2502.13059) for visual factuality; the abstention items of [GDP.pdf](https://arxiv.org/pdf/2607.11192)                         | hallucinations per field; weighted precision                                                                 |
| 3 | Document structure and cross-references | tables, forms, footnotes, plans with legends, amendments that supersede earlier text               | [GDP.pdf](https://arxiv.org/pdf/2607.11192); [CharXiv](https://arxiv.org/pdf/2406.18521) and [Chartography](https://arxiv.org/pdf/2608.10677) for charts; [MuirBench](https://arxiv.org/pdf/2406.09411) for reasoning across several images, such as the pages of one report | TEDS, DB-template fit, typed field scores                                                                    |
| 4 | Schema and instruction adherence        | the output must fit a JSON Schema and the prompt's rules                                           | [IFBench](https://arxiv.org/pdf/2507.02833), [ComplexConstraints](https://arxiv.org/pdf/2606.09118)                                                                                                                                                                          | schema-valid rate (structured outputs guarantee only the syntax); rule checks per field                      |
| 5 | Long inputs                             | reports run to dozens or hundreds of pages, and earlier pages give context to later ones           | [AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR), [LongBench v2](https://arxiv.org/pdf/2412.15204), [MMLongBench-Doc](https://arxiv.org/pdf/2407.01523); MRCR v2 on Gemma 4's card                                                                        | M1, tokens per document; quality in one pass against page by page                                            |
| 6 | Long outputs                            | a full transcription or a finds table runs to thousands of tokens                                  | [LongProc](https://arxiv.org/pdf/2501.05414); [LongWriter-V](https://arxiv.org/pdf/2502.14834) found VLMs struggling beyond about 1,000 words; ExtractBench's recall on long records                                                                                         | output tokens per page and per document; truncated replies, which must be zero; record recall on long tables |
| 7 | Czech and German                        | Czech dominates the archive; German appears in older and Sudeten-German material                   | [Global-MMLU-Lite](https://huggingface.co/datasets/CohereLabs/Global-MMLU-Lite), with Czech since version 3.0 (a knowledge test, not reading); MDPBench's German column; CHURRO-DS's Czech print                                                                             | CER and field scores by language                                                                             |

### What do the shortlisted models' cards report?

The figures are the vendors' own, from different harnesses and settings. Qwen measured Gemma 4 itself.
A dash means the card does not report the benchmark. Use these figures to shortlist, never to decide.

| Proxy (criterion)                   | Qwen3.8-27B | Qwen3.6-27B | Qwen3.6-35B-A3B | Gemma 4 31B                      | Inkling 2 Small (reference only)        |
|-------------------------------------|-------------|-------------|-----------------|----------------------------------|-----------------------------------------|
| OmniDocBench 1.5 (1, 3)             | 91.1        | 89.4        | 89.9            | 80.1                             | — (v1.6: 94.6)                          |
| CharXiv reasoning, without code (3) | 83.7        | 78.4        | 78.0            | 67.9                             | 85.6                                    |
| BabyVision, without code (1)        | 65.7        | 28.9        | —               | —                                | 68.6                                    |
| SimpleVQA (2)                       | —           | 56.1        | 58.9            | 52.9                             | 68.2, with search and tools             |
| IFBench (4)                         | 79.5        | 69.1        | —               | —                                | —                                       |
| Long context (5)                    | —           | —           | —               | MRCR v2, 8 needles at 128k: 66.4 | AA-LCR 83.3; LongBench v2 70.6          |
| Abstention (2)                      | —           | —           | —               | —                                | AA-Omniscience non-hallucination 73.3 % |
| Multilingual (7)                    | —           | —           | —               | —                                | Global-MMLU-Lite 91.0; MDPBench 81.4    |

Sources: the cards of [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) (its figures and
Qwen3.6-27B's), [Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) and
[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) (their figures and Gemma 4's),
[Gemma 4 31B](https://huggingface.co/google/gemma-4-31B) and
[Inkling 2 Small](https://huggingface.co/thinkingmachines/Inkling-2-Small).

No candidate's card reports long-output quality, abstention or Czech. Qwen3.8-27B's card only advises
allowing up to 131,072 output tokens for the final answer. Our run therefore measures criteria 2, 6 and 7
itself.

## What do we measure?

#22 names four checks: reading order, text, image regions, and forms as key–value pairs. The table
fixes a metric for each output. CER is the character error rate, NED the normalised edit distance,
and TEDS the tree-edit-distance similarity of two HTML tables.

| Output                      | Metric                                                                                                                                                                                | Why                                                                                       | Code today                                                                                                                  |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| Text                        | CER (primary), WER, NED; CER with diacritics removed, as a diagnostic                                                                                                                 | CER is comparable across tools; the diagnostic separates lost diacritics from misreadings | [`eval_metrics.py`](https://github.com/ufal/atrium-digital-convert/blob/test/eval_metrics.py)                               |
| Reading order               | NED over the sequence of matched elements, all element types included                                                                                                                 | order errors break running text and detach captions                                       | new; reuses `levenshtein()`                                                                                                 |
| Tables                      | TEDS, and TEDS-S (structure only)                                                                                                                                                     | the standard since PubTabNet; works on Markdown that carries HTML tables                  | [OmniDocBench](https://github.com/opendatalab/OmniDocBench)'s evaluator, or `teds_score()` once `table_teds.py` is vendored |
| Tables and forms as DB rows | rows aligned to a database template, then typed cell scores as for key information                                                                                                    | a table is good when its rows fit the template's columns                                  | new                                                                                                                         |
| Key information             | typed field scores (next section), weighted F1, error counts; [ANLS\*](https://github.com/deepopinion/anls_star_metric) as the comparable summary; strict value F1 as the strict view | different fields need different notions of "correct"                                      | new; `anls_star` on PyPI                                                                                                    |
| Critical facts (optional)   | pass/fail unit tests in the [olmOCR-Bench](https://huggingface.co/datasets/allenai/olmOCR-bench) style, such as "`C-TX-202400594` appears" or "line A precedes line B"                | the cheapest gold: a test takes seconds to write                                          | new                                                                                                                         |
| Regions                     | presence and count per region type                                                                                                                                                    | Markdown carries no boxes; #22 asks for types and their share of the page                 | new                                                                                                                         |
| Cost                        | input and output tokens per page, seconds per page, peak GPU memory                                                                                                                   | #22's measurements M1 (tokens) and M2 (speed)                                             | `scripts/detail_budget.py`, run paradata                                                                                    |
| Long output                 | output tokens per page and per document; truncated replies, which must be zero; record recall on long tables                                                                          | long transcriptions and finds tables are where models stop early                          | run paradata; new                                                                                                           |

### How is key information scored?

[ExtractBench](https://github.com/ContextualAI/extract-bench) treats the JSON Schema as the scoring
rule: each field names its own metric. Its presets include exact, case-insensitive, fuzzy and
semantic string matching, numeric tolerance, and array alignment. An ATRIUM schema would do the same.
The value types below are a proposal. The fields, tolerances and weights are ARÚP's to choose.

| Value type      | Examples (to confirm with ARÚP)                                          | Normalise before matching                                                                | Match                                                                                                               | Partial credit                            |
|-----------------|--------------------------------------------------------------------------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| Identifier      | AMČR ids such as `C-TX-202400594`; parcel, feature and inventory numbers | Unicode NFC, spaces, dash variants; case only where the scheme ignores it                | exact                                                                                                               | none: one wrong character is a wrong link |
| Date            | dates of fieldwork, year of the report                                   | ISO 8601 at the gold's precision (`1956`, `1956-05`, `1956-05-12`); Roman-numeral months | exact                                                                                                               | none                                      |
| Quantity        | depth in cm, area in m², number of finds, S-JTSK coordinates in metres   | number and unit; decimal comma; unit conversion                                          | within a tolerance set per field                                                                                    | none outside the tolerance                |
| Name            | persons, organisations, cadastral areas, sites                           | case; titles such as PhDr. or Ing.; "Surname, Given"                                     | ANLS (normalised Levenshtein similarity, threshold 0.5) or an embedding score; exact id once linked to a vocabulary | yes                                       |
| Controlled term | document type, period, find type, material                               | label to its AMČR or TEATER id                                                           | exact id                                                                                                            | none                                      |
| Free text       | summary, description of the site                                         | whitespace                                                                               | CER; semantic similarity only as a diagnostic                                                                       | yes                                       |
| List of values  | periods, authors                                                         | each item as its own type                                                                | one-to-one alignment (Hungarian), order ignored unless the field is ordered                                         | per item                                  |
| List of rows    | a finds table, a list of features                                        | each cell as its own type                                                                | rows paired by a key column, otherwise by best match; then cell by cell                                             | per cell                                  |

Each field then has one of four outcomes. As in ExtractBench, omissions and hallucinations are kept apart:

- **correct**: the values match under the field's rule;
- **wrong value**: both sides have a value, and they do not match;
- **omission**: the gold has a value, the output has none;
- **hallucination**: the output has a value, or a key, that the gold does not have.

An invented identifier is the costliest error for FAIR storage, because it creates a false link. The
prompt and the schema should therefore allow an empty field, and prefer it to a guess.

The weighted scores use a weight *w* per field. ARÚP sets the weights; identifiers and vocabulary
links would weigh more than free text.

```text
P  = Σ w·correct / Σ w·(correct + wrong + hallucinated)
R  = Σ w·correct / Σ w·(correct + wrong + omitted)
F1 = 2·P·R / (P + R)
```

The unweighted F1 and the three error counts are reported beside it, by tier and by page category.
ParseBench-2 applies the same idea to parsing: its metrics follow a severity policy, so a changed
number costs more than a harmless formatting change ([paper](https://arxiv.org/pdf/2611.17400)).

Two cautions on the metrics proposed for #22:

- **ANLS is not exact match.** It credits partial similarity: a ten-character identifier with one
  wrong digit scores 0.9. It suits names and short noisy strings, not identifiers.
- **Tree edit distance suits trees whose shape carries meaning:** HTML tables (TEDS) and heading
  trees. On key–value JSON, typed field scores are easier to read and do not depend on key order.

## Which public benchmarks are relevant?

The five columns answer the questions asked of each benchmark. Relevance to ATRIUM's task is marked
**H** (high), **M** (medium) or **L** (low). "Released" gives the first version and, where it
matters, the latest.

### Parsing pages to Markdown or JSON

| Benchmark                                                                                               | What it does                                                                                                                         | Relation to our task                                                                                                                                     | Languages                          | Measures (optimises)                                                                                                           | Released                                                        |
|---------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [OmniDocBench](https://github.com/opendatalab/OmniDocBench) ([paper](https://arxiv.org/pdf/2412.07626)) | pages to Markdown against element-level JSON gold; 1,651 pages of 10 document types in v1.6                                          | **H** for method: its page JSON is #22's proposed gold format, and its evaluator scores Markdown directly. L for data: modern pages                      | Chinese, English                   | text edit distance, table TEDS, reading-order edit distance, formula CDM; its Overall mixes in formulas, so use the components | Dec 2024; v1.5 Sep 2025; v1.6 Apr 2026; v1.7 Apr 2026 (tooling) |
| [Real5-OmniDocBench](https://arxiv.org/pdf/2603.04205)                                                  | OmniDocBench v1.5's 1,355 pages reprinted and captured again: scanned, warped, photographed from a screen, unevenly lit, skewed      | **M**: how models degrade on physical copies, as our scans are                                                                                           | Chinese, English                   | OmniDocBench metrics                                                                                                           | Mar 2026                                                        |
| [PureDocBench](https://arxiv.org/pdf/2605.07492)                                                        | 1,475 pages, each clean, digitally degraded and really captured; 58 models compared                                                  | **M**: degradation with exact, source-derived gold                                                                                                       | not stated                         | text, formulas, tables, reading order                                                                                          | May 2026                                                        |
| [olmOCR-Bench](https://arxiv.org/pdf/2502.18443)                                                        | about 1,400 PDF pages with about 7,000 pass/fail unit tests: text present or absent, order, table cells; an old-scans subset         | **H** for method: unit tests are cheap gold for critical facts. M for data                                                                               | mostly English                     | test pass rate; ignores formatting                                                                                             | Feb 2025                                                        |
| [ParseBench-2](https://arxiv.org/pdf/2611.17400) ([version 1](https://arxiv.org/pdf/2604.08538))        | about 4,300 enterprise cases in six dimensions: text, formatting, tables, charts, visual grounding and forms                         | **M–H**: forms check that values stay with their fields and blank fields stay blank; errors are weighed by severity over 330 error types                 | English                            | deterministic metrics tuned to a severity policy, no LLM judge                                                                 | Apr 2026; version 2 Nov 2026                                    |
| [READoc](https://arxiv.org/pdf/2409.05137)                                                              | whole PDFs to Markdown; 3,576 documents                                                                                              | **M**: whole documents rather than pages                                                                                                                 | English, born-digital              | text, tables, headings and reading order against Markdown gold                                                                 | Sep 2024                                                        |
| [SCORE](https://arxiv.org/pdf/2509.19345)                                                               | an evaluation framework, tested on 1,114 pages                                                                                       | **M** for method: accepts valid alternative structures; tells hallucinations from omissions per token                                                    | any                                | adjusted edit distance, token diagnostics, tolerant table scores                                                               | Sep 2025                                                        |
| [French PDF-to-Markdown](https://arxiv.org/pdf/2602.11960)                                              | hard French pages picked by model disagreement from 60,000 documents, handwriting and forms included                                 | **M**: a European-language template for building our own hard set                                                                                        | French                             | unit tests that ignore harmless formatting                                                                                     | Feb 2026                                                        |
| [CC-OCR](https://arxiv.org/pdf/2412.02210)                                                              | four tracks: scene text, multilingual text, document parsing, key information to JSON                                                | **M**                                                                                                                                                    | multilingual track includes German | per-track scores                                                                                                               | Dec 2024                                                        |
| [OCRBench v2](https://arxiv.org/pdf/2501.00321)                                                         | 31 scenarios of text-centric tasks for VLMs, handwriting included; a public [leaderboard](https://99franklin.github.io/ocrbench_v2/) | **L–M**: general OCR and extraction ability. Best open model in English: Qwen3.6-27B (68.3), ahead of Qwen3.8-27B (63.5) and Gemini 3 Pro Preview (63.4) | English, Chinese                   | task-specific: TEDS, F1, edit distance                                                                                         | Dec 2024                                                        |
| [OmniAI OCR benchmark](https://github.com/getomni-ai/benchmark)                                         | 1,000 documents: OCR, then JSON, compared with gold JSON                                                                             | **M** for method: it scores the end product, as we will                                                                                                  | English                            | JSON field accuracy                                                                                                            | Feb 2025                                                        |

Also published, lower relevance: [Fox](https://arxiv.org/pdf/2405.14295) (fine-grained OCR, 2024),
[Dr. DocBench](https://arxiv.org/pdf/2606.01393) (expert-level pages, May 2026),
[MPDocBench-Parse](https://arxiv.org/pdf/2605.22100) (multi-page parsing, May 2026), and the vendor-run
[IDP leaderboard](https://www.idp-leaderboard.org/). Its version 1.5 averages olmOCR-Bench, OmniDocBench
and its own IDP Core set; its best open-weight entries are Qwen3-VL-235B (79.6) and Qwen3.5-9B (76.7).

### Extracting key information to JSON

| Benchmark                                                                                                                                                | What it does                                                                                                                                                                                        | Relation to our task                                                                                                                                                                                                                                                                           | Languages                    | Measures (optimises)                                                    | Released        |
|----------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|-------------------------------------------------------------------------|-----------------|
| [ExtractBench, Contextual AI](https://arxiv.org/pdf/2602.12247)                                                                                          | 35 PDFs with JSON Schemas and human gold: 12,867 fields, schemas of up to 369 fields                                                                                                                | **H**: the scoring design for our key information. Exact match for identifiers, tolerance for quantities, semantic match for names, aligned arrays, omission told apart from hallucination                                                                                                     | English                      | per-field metric declared in the schema; item-weighted score, pass rate | Feb 2026        |
| [ExtractBench, LlamaIndex](https://arxiv.org/pdf/2607.29677)                                                                                             | 370 documents, 4,869 pages, 67 document types; forms, scans and handwriting included                                                                                                                | **M–H**: the strict view, with exact values and order-free record matching. Open-weight value F1: Qwen3.6-35B-A3B 87.3 %, Gemma 4 26B-A4B 66.2 %, NuExtract3 47.9 %. On the longest documents every VLM scores below 36 % ([results](https://www.llamaindex.ai/blog/introducing-extractbench)) | English                      | value F1 with one-to-one record matching; grounding F1; cost per page   | Jul 2026        |
| [ANLS\*](https://arxiv.org/pdf/2402.03848)                                                                                                               | a metric, not a dataset: ANLS extended to dictionaries, lists and empty answers                                                                                                                     | **H**: one comparable number for JSON output; penalises missing and invented keys                                                                                                                                                                                                              | any                          | ANLS\*                                                                  | Feb 2024        |
| [From Pixels to Structure](https://arxiv.org/pdf/2610.11818)                                                                                             | 8 open VLMs of up to 7B parameters turn page images from three university heritage collections, a prehistoric inventory book among them, into schema-valid JSON; zero-shot, few-shot and fine-tuned | **H**: the closest published task to ours                                                                                                                                                                                                                                                      | not stated in the abstract   | CER, ANLS\*, mAP-F1                                                     | Oct 2026        |
| [RISE Humanities Data Benchmark](https://github.com/RISE-UNIBAS/humanities_data_benchmark)                                                               | 12 historical tasks, such as business letters 1926–35, catalogue cards, personnel cards and Fraktur adverts, with typed output                                                                      | **H**: historical documents to typed JSON, with the cost per 1,000 documents                                                                                                                                                                                                                   | mostly German                | fuzzy match, F1, CER, per task                                          | 2025, versioned |
| [From Handwriting to Structured Data](https://arxiv.org/pdf/2604.16504)                                                                                  | 17 models on a real handwritten medical form                                                                                                                                                        | **M**: weighted field F1 on handwritten forms; the best models reach about 90 %                                                                                                                                                                                                                | English                      | accuracy, weighted F1                                                   | Apr 2026        |
| [RealDocBench](https://arxiv.org/pdf/2606.07401)                                                                                                         | 1,356 field-level questions over 581 regulated documents                                                                                                                                            | **M**: field-level correctness on messy real pages                                                                                                                                                                                                                                             | English                      | question accuracy                                                       | Jun 2026        |
| [VRDU](https://arxiv.org/pdf/2211.15421)                                                                                                                 | two form datasets with nested, repeated fields and unseen templates                                                                                                                                 | **M**: type-aware matching for dates and numbers; template shift like our forms                                                                                                                                                                                                                | English                      | F1                                                                      | Nov 2022        |
| [DocILE](https://arxiv.org/pdf/2302.05658)                                                                                                               | 6,700 business documents, 55 field classes, line items                                                                                                                                              | **L–M**: line items resemble finds tables; scoring needs boxes                                                                                                                                                                                                                                 | English                      | AP, F1                                                                  | Feb 2023        |
| [Kleister](https://arxiv.org/pdf/2105.05796)                                                                                                             | long scanned and born-digital documents                                                                                                                                                             | **L–M**: extraction from long documents                                                                                                                                                                                                                                                        | English                      | F1                                                                      | May 2021        |
| [FUNSD](https://arxiv.org/pdf/1905.13538) / [XFUND](https://github.com/doc-analysis/XFUND) ([paper](https://aclanthology.org/2022.findings-acl.253.pdf)) | noisy scanned forms; XFUND adds seven languages                                                                                                                                                     | **M** (XFUND): key–value linking on forms                                                                                                                                                                                                                                                      | XFUND: German and six others | F1                                                                      | 2019 / 2021     |
| [CORD](https://github.com/clovaai/cord), [SROIE](https://arxiv.org/pdf/2103.10213)                                                                       | receipts                                                                                                                                                                                            | **L**                                                                                                                                                                                                                                                                                          | Indonesian, English          | F1                                                                      | 2019            |

### Tables

| Benchmark                                                                                           | What it does                                                                               | Relation to our task                                                      | Languages                      | Measures (optimises)                   | Released            |
|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|--------------------------------|----------------------------------------|---------------------|
| [PubTabNet](https://arxiv.org/pdf/1911.10683)                                                       | 568,000 table images with HTML gold                                                        | **M**: where TEDS comes from                                              | English                        | TEDS                                   | Nov 2019            |
| [FinTabNet](https://arxiv.org/pdf/2005.00589)                                                       | tables from financial reports                                                              | **L**                                                                     | English                        | TEDS                                   | May 2020            |
| [PubTables-1M](https://arxiv.org/pdf/2110.00061) / [PubTables-v2](https://arxiv.org/pdf/2512.10888) | about a million tables; v2 adds full-page and multi-page tables                            | **M**: grid-based scoring; tables across pages                            | English                        | GriTS                                  | Sep 2021 / Dec 2025 |
| [ICDAR 2019 cTDaR](https://github.com/cndplab-founder/ICDAR2019_cTDaR)                              | table detection and structure, with an archival track of handwritten and hand-drawn tables | **M–H**: the closest public match to old registers; its scores need boxes | historical, mixed              | IoU-based F1                           | 2019                |
| [RD-TableBench](https://github.com/reductoai/RD-TableBench)                                         | 1,000 hard tables: scans, handwriting, several languages                                   | **M**                                                                     | mixed                          | alignment-based similarity             | 2024                |
| [PulseBench-Tab](https://arxiv.org/pdf/2606.07534)                                                  | 1,820 tables from 380 documents; 48 % have merged cells                                    | **M**: tables with merged cells, German included                          | 9 languages, German among them | T-LAG, a graph match of cell adjacency | Apr 2026            |

### Historical, handwritten and multilingual documents

| Benchmark                                                                               | What it does                                                                                   | Relation to our task                                                                                                                            | Languages                                         | Measures (optimises)                            | Released |
|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|-------------------------------------------------|----------|
| [CHURRO-DS](https://arxiv.org/pdf/2509.19768)                                           | 99,491 pages from 155 historical corpora over 22 centuries, printed and handwritten            | **H**: the only large historical text-recognition benchmark with Czech. Czech print has 30 test pages; Czech handwriting is not in the test set | 46 language clusters, Czech and German among them | normalised Levenshtein similarity               | Sep 2025 |
| [MDPBench](https://arxiv.org/pdf/2603.28130)                                            | 3,400 digital and photographed pages; open models lose 17.8 % on average on photographs        | **M–H**: per-language scores, German included                                                                                                   | 17 languages, German but not Czech                | text edit, TEDS, CDM                            | Mar 2026 |
| [MORE](https://arxiv.org/pdf/2607.02956)                                                | real documents with text, tables and catalogues                                                | **M**: long-tail languages                                                                                                                      | 149 languages; Czech not confirmed                | NED, TEDS, CDM                                  | Jul 2026 |
| [TextBite](https://arxiv.org/pdf/2503.16664)                                            | 8,449 Czech pages from the 18th to 20th century: newspapers, dictionaries, handwritten records | **M**: Czech layout and logical segments                                                                                                        | Czech                                             | segmentation scored on text pixels              | Mar 2025 |
| [GT4HistOCR](https://arxiv.org/pdf/1809.05501)                                          | 313,173 printed line images, 15th to 19th century                                              | **M**: German Fraktur                                                                                                                           | German, Latin                                     | CER                                             | Sep 2018 |
| [Chronicling Germany](https://arxiv.org/pdf/2401.16845)                                 | historical German newspaper pages with layout and text                                         | **M**                                                                                                                                           | German                                            | layout scores, CER                              | Jan 2024 |
| [HIPE-OCRepair 2026](https://arxiv.org/pdf/2607.08143)                                  | ICDAR competition on LLM-assisted correction of historical OCR                                 | **L–M**: ocr-postprocess's topic                                                                                                                | several                                           | correction scores that penalise over-correction | Jul 2026 |
| [MTVQA](https://github.com/bytedance/MTVQA) ([paper](https://arxiv.org/pdf/2405.11985)) | questions on text in images                                                                    | **L**                                                                                                                                           | 9 languages, German included                      | accuracy                                        | May 2024 |
| [Historical OCR with LLMs](https://arxiv.org/pdf/2510.06743)                            | 12 multimodal LLMs on 18th-century print                                                       | **M**: names an error to expect, inserting archaic characters from the wrong period                                                             | Russian                                           | CER plus archaic-insertion rates                | Oct 2025 |
| [Survey of OCR evaluation](https://arxiv.org/pdf/2603.25761)                            | a review of how OCR is evaluated, and how historical archives are left out                     | context                                                                                                                                         | —                                                 | —                                               | Mar 2026 |

### Questions and retrieval

These matter later, for semantic search on top of the record.

| Benchmark                                                                                                                     | What it does                                                        | Relation to our task          | Languages                                    | Measures (optimises)        | Released   |
|-------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|-------------------------------|----------------------------------------------|-----------------------------|------------|
| [DocVQA](https://arxiv.org/pdf/2007.00398), [InfographicVQA](https://arxiv.org/pdf/2104.12756)                                | questions on single document images                                 | **L**                         | English                                      | ANLS                        | 2020, 2021 |
| [DUDE](https://arxiv.org/pdf/2305.08455), [MP-DocVQA](https://arxiv.org/pdf/2212.05935)                                       | questions on multi-page documents                                   | **L–M**                       | English                                      | ANLS; DUDE adds calibration | 2023, 2022 |
| [MMLongBench-Doc](https://arxiv.org/pdf/2407.01523), [LongDocURL](https://arxiv.org/pdf/2412.18424)                           | questions on long PDFs                                              | **M**: long reports           | English                                      | accuracy, F1                | 2024       |
| ViDoRe [v1](https://arxiv.org/pdf/2407.01449), [v2](https://arxiv.org/pdf/2505.17166), [v3](https://arxiv.org/pdf/2601.08620) | page retrieval for RAG; v3 has about 26,000 pages and 3,099 queries | **M**: finding the right page | v3 queries in six languages, German included | nDCG                        | 2024–2026  |

### Layout and reading order

Boxes are not our output, so these rank low. Reading order still matters.

| Benchmark                                                                                                              | What it does                                            | Relation to our task                                              | Languages        | Measures (optimises)            | Released |
|------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------|------------------|---------------------------------|----------|
| [DocLayNet](https://arxiv.org/pdf/2206.01062)                                                                          | 80,863 pages, 11 layout classes                         | **L**                                                             | mostly English   | mAP                             | Jun 2022 |
| [M6Doc](https://arxiv.org/pdf/2305.08719), [D4LA](https://arxiv.org/pdf/2308.14978)                                    | layout classes on scanned, photographed and noisy pages | **L**                                                             | English, Chinese | mAP                             | 2023     |
| [ReadingBank](https://github.com/microsoft/unilm/tree/master/layoutreader) ([paper](https://arxiv.org/pdf/2108.11591)) | reading order on 500,000 pages                          | **L–M**: the data behind LayoutReader, which ocr-postprocess uses | English          | BLEU, average relative distance | 2021     |

### Capabilities reported on VLM model cards

Model cards report these next to the document benchmarks above. Inkling 2 Small's card is an example
of the grouping.

| Benchmark                                                                                                                   | What it does                                                                                                         | Relation to our task                                                                                                                                      | Languages                      | Measures (optimises)                                    | Released                       |
|-----------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|---------------------------------------------------------|--------------------------------|
| [PerceptionBench](https://arxiv.org/pdf/2607.24957)                                                                         | 3,000 questions over ten atomic perception skills                                                                    | **M**: separates misreading from misreasoning; perception-related hallucination is the weakest skill                                                      | not stated                     | accuracy per skill                                      | Jul 2026                       |
| [BabyVision](https://arxiv.org/pdf/2601.06521)                                                                              | 388 items on core visual skills that need no language                                                                | **L–M**: whether a model sees symbols and shapes, as on plans                                                                                             | needs no language              | accuracy                                                | Jan 2026                       |
| [SimpleVQA](https://arxiv.org/pdf/2502.13059)                                                                               | short factual questions about images                                                                                 | **M**: visual factuality                                                                                                                                  | not stated                     | accuracy                                                | Feb 2025                       |
| [GDP.pdf](https://arxiv.org/pdf/2607.11192)                                                                                 | 100 questions by professionals over real PDFs, with rubrics of atomic criteria; 11 capabilities, abstention included | **H**: the closest capability test to ours: extraction, tables, footnotes, plans, scan noise, superseding amendments. The best of 17 models passes 30.7 % | not stated                     | rubric score and strict pass rate                       | Jul 2026                       |
| [AA-Omniscience](https://arxiv.org/pdf/2511.13029)                                                                          | 6,000 knowledge questions over 42 topics                                                                             | **M**: whether a model abstains instead of inventing; its index penalises hallucination                                                                   | not stated                     | Omniscience Index (−100 to 100), non-hallucination rate | Nov 2025                       |
| [MuirBench](https://arxiv.org/pdf/2406.09411)                                                                               | 2,600 questions over 11,264 images in 12 multi-image tasks, each paired with an unanswerable twin                    | **M**: reasoning across several images, such as the pages of one report                                                                                   | not stated                     | accuracy                                                | Jun 2024                       |
| [CharXiv](https://arxiv.org/pdf/2406.18521), [Chartography](https://arxiv.org/pdf/2608.10677)                               | 2,323 charts from arXiv papers; 100 professional chart tasks                                                         | **L–M**: graphs in specialist reports                                                                                                                     | not stated                     | accuracy                                                | Jun 2024, Aug 2026             |
| [AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR)                                                         | 100 questions over document sets of about 100k tokens; answers must be reasoned across documents                     | **H**: long reports and their appendices                                                                                                                  | not stated                     | accuracy, judged equality                               | version 1.1 Sep 2026           |
| [LongBench v2](https://arxiv.org/pdf/2412.15204)                                                                            | 503 multiple-choice questions over contexts of 8k to 2M words                                                        | **M**: long-context understanding                                                                                                                         | not stated                     | accuracy                                                | Dec 2024                       |
| [LongProc](https://arxiv.org/pdf/2501.05414)                                                                                | six procedural tasks with outputs up to 8k tokens, such as HTML pages to TSV                                         | **H**: long structured output, the closest public test of a long table or JSON                                                                            | not stated                     | deterministic task scores                               | Jan 2025                       |
| [IFBench](https://arxiv.org/pdf/2507.02833)                                                                                 | precise instruction following with new, unseen output constraints                                                    | **M**: prompt and format rules                                                                                                                            | not stated                     | constraint pass rate                                    | Jul 2025                       |
| [ComplexConstraints](https://arxiv.org/pdf/2606.09118)                                                                      | 75 expert prompts with 1,559 rubric items                                                                            | **M**: complex instructions                                                                                                                               | not stated                     | rubric score                                            | Jun 2026                       |
| [Global-MMLU-Lite](https://huggingface.co/datasets/CohereLabs/Global-MMLU-Lite) ([paper](https://arxiv.org/pdf/2412.03304)) | human-translated knowledge questions; Czech and Slovak since version 3.0                                             | **M**: the Czech competence of the language model, not its reading                                                                                        | 23 languages, Czech among them | accuracy                                                | Dec 2024; version 3.0 May 2026 |

Also on such cards, of low relevance to us: [MMMU-Pro](https://arxiv.org/pdf/2409.02813) (exam questions with images),
[ZeroBench](https://arxiv.org/pdf/2502.09696) (adversarial visual puzzles),
[Humanity's Sixth Sense](https://arxiv.org/pdf/2610.08966) (intuitive scene reasoning),
[ScreenSpot-Pro](https://arxiv.org/pdf/2504.07981) (pointing at elements of software screens) and
[VIALS](https://arxiv.org/pdf/2608.21357) (life-science images).

## Which benchmarks do we use, and how?

1. **Our own gold set is the measure.** It has two layers and an option:
   - a **page layer** in OmniDocBench's page JSON, for text, order and tables. OmniDocBench's pinned
     evaluator scores model Markdown against it directly;
   - a **document layer**: one key-information JSON per document, valid against a JSON Schema per
     document type, scored field by field as above;
   - optionally, **unit tests** for critical facts, where a full transcription costs too much.
2. **Public numbers give context, never a verdict.** Report OmniDocBench's components (never its
   Overall), CHURRO-DS's Czech print and German subsets, MDPBench's German column, Real5 and
   PureDocBench for degradation, and cTDaR's archival track for tables.
3. **Reuse code, not data.** OmniDocBench's evaluator is Apache-2.0, ExtractBench's evaluator is
   MIT, and ANLS\* is on PyPI; check each licence before vendoring. The OmniDocBench and CHURRO-DS
   data are for research only: they are used for internal comparison and never redistributed.
4. **Copy two protocols.** "From Pixels to Structure" scores image-to-JSON with CER and ANLS\* and
   tests fine-tuning on heritage data. RISE reports the cost per 1,000 documents next to quality.
5. **Read model cards by criterion.** When shortlisting, compare candidates on the proxies of the
   seven criteria above, never on an overall index.

## Which models are candidates?

All figures are published results on other data. OmniDocBench (ODB) figures come from its v1.6
leaderboard unless marked otherwise. Its text edit (TE) and reading-order edit (RO) are better when
lower; TEDS is better when higher. "Self-reported" means the vendor's own figure.

### Compact OCR models

| Model                                                                                                                                                                                  | Size, released                  | Licence                                                                                                                                                        | Czech, German, handwriting                                                                                                                  | Output                                                     | Published results                                                                                                                                                           | Serving                                                     |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| [PaddleOCR-VL-1.6](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6) (Baidu; [paper](https://arxiv.org/pdf/2606.03264))                                                            | 0.9B, May 2026                  | Apache-2.0                                                                                                                                                     | 109 languages, [Czech and German among them](https://arxiv.org/pdf/2510.14528); handwriting in scope                                        | Markdown, JSON                                             | ODB 96.34 (TE 0.033, TEDS 94.8, RO 0.128); [Real5](https://arxiv.org/pdf/2606.03264) 93.19; ParseBench-2 70.3; version 1.5 had the best open German score on MDPBench, 84.8 | pip `paddleocr[doc-parser]`; Docker with a vLLM backend     |
| [OvisOCR3](https://huggingface.co/ATH-MaaS/OvisOCR3) ([paper](https://arxiv.org/pdf/2610.33066))                                                                                       | 0.8B, Oct 2026                  | Apache-2.0                                                                                                                                                     | languages not stated; MDPBench 88.8, self-reported                                                                                          | Markdown with HTML tables; key–value JSON to a schema      | ODB 96.74, self-reported; [OvisOCR2](https://arxiv.org/pdf/2607.13639) 96.47 on the leaderboard                                                                             | vLLM, SGLang                                                |
| [LightOnOCR-3](https://huggingface.co/lightonai/LightOnOCR-3-4B) (LightOn)                                                                                                             | 0.8B, 1B, 4B; Oct 2026          | Apache-2.0                                                                                                                                                     | languages not stated; for version 2, its [authors](https://arxiv.org/pdf/2601.14251) call handwriting inconsistent and cursive not a target | Markdown                                                   | olmOCR-Bench 86.3 and ParseBench-2 77.0 (4B)                                                                                                                                | vLLM, SGLang                                                |
| [Chandra OCR 2](https://github.com/datalab-to/chandra) (Datalab)                                                                                                                       | size not stated; Mar 2026       | code Apache-2.0; weights a modified OpenRAIL-M: free for research, personal use and startups under $2M funding or revenue; no use competing with Datalab's API | **Czech 85.3 %, German 94.8 %** on Datalab's 43-language test, metric not defined; handwriting shown by examples                            | Markdown, HTML, JSON with layout                           | olmOCR-Bench 85.8                                                                                                                                                           | vLLM; 1.44 pages/s on one H100                              |
| [MinerU2.5-Pro](https://huggingface.co/opendatalab/MinerU2.5-Pro-2605-1.2B) (OpenDataLab; [paper](https://arxiv.org/pdf/2604.04771))                                                   | 1.2B, May 2026                  | weights Apache-2.0; [MinerU's code](https://github.com/opendatalab/MinerU) adds terms above 100 million monthly users or $20M monthly revenue                  | Chinese, English; MinerU2.5 scored 46.3 on MDPBench                                                                                         | JSON content list, Markdown; native parsing of tagged PDFs | ODB 95.75 (TE 0.036, TEDS 93.4, RO 0.120)                                                                                                                                   | vLLM; 2.12 pages/s on one A100                              |
| [Qianfan-OCR](https://huggingface.co/baidu/Qianfan-OCR) (Baidu; [paper](https://arxiv.org/pdf/2603.13398))                                                                             | 4B, Mar 2026                    | Apache-2.0                                                                                                                                                     | 192 languages                                                                                                                               | Markdown, HTML tables, key-information JSON                | ODB 93.90; olmOCR-Bench 79.8                                                                                                                                                | 1.02 pages/s on one A100, 8-bit                             |
| [dots.mocr](https://huggingface.co/dots-studio/dots.mocr) (rednote, now dots-studio; [dots.ocr paper](https://arxiv.org/pdf/2512.02498))                                               | 3B, Mar 2026                    | MIT tag, plus a separate licence agreement in the repository: check it                                                                                         | MDPBench 80.5, German 82.6                                                                                                                  | JSON with layout, Markdown, HTML tables                    | olmOCR-Bench 83.9                                                                                                                                                           | vLLM                                                        |
| [DeepSeek-OCR 2](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2) ([paper](https://arxiv.org/pdf/2601.20552))                                                                        | 3B mixture of experts, Jan 2026 | Apache-2.0                                                                                                                                                     | "multilingual"; version 1 scored 51.8 on MDPBench                                                                                           | Markdown                                                   | ODB 90.25; olmOCR-Bench 76.3                                                                                                                                                | vLLM                                                        |
| [Nemotron 3.5 Parse](https://huggingface.co/nvidia/Nemotron-3.5-Parse) (NVIDIA)                                                                                                        | 0.63B, Oct 2026                 | OpenMDW-1.1, commercial use allowed                                                                                                                            | 163 language and script entries; the card warns about handwriting and degraded scans                                                        | Markdown, HTML, JSON                                       | ParseBench 75.2                                                                                                                                                             | vLLM; 18.6 pages/s on one H200                              |
| [olmOCR 2](https://github.com/allenai/olmocr) (Ai2; [paper](https://arxiv.org/pdf/2510.19817))                                                                                         | 7B, Oct 2025                    | Apache-2.0                                                                                                                                                     | mostly English; MDPBench 70.4                                                                                                               | Markdown                                                   | olmOCR-Bench 82.4                                                                                                                                                           | vLLM; under $200 per million pages, vendor's figure         |
| [Granite-Docling](https://huggingface.co/ibm-granite/granite-docling-258M) with [Docling](https://github.com/docling-project/docling) (IBM; [paper](https://arxiv.org/pdf/2501.17887)) | 258M, Sep 2025                  | Apache-2.0, MIT                                                                                                                                                | English; other languages experimental                                                                                                       | DocTags, Markdown, HTML, JSON                              | —                                                                                                                                                                           | pip; Docling is already an opt-in engine in digital-convert |

Also strong on OmniDocBench, with no language evidence for Czech:
[Xiaomi-OCR-0](https://huggingface.co/xiaomi-research/Xiaomi-OCR-0) ([paper](https://arxiv.org/pdf/2609.36136); 0.8B, Apache-2.0, 96.83
self-reported) and [Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) ([paper](https://arxiv.org/pdf/2606.23050); 3B, MIT, 94.00; a decoder built for
long outputs without growing memory).

### Classic OCR and handwriting tools

| Tool                                                                                                                                                                                                                                                     | Licence                                                                                                                 | Czech, German, handwriting                                                                                                                                                                                                                                                                                                                     | Output                     | Evidence                                                                                                                                                         | Serving                                                                                                                   |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| [PP-OCRv6](https://arxiv.org/pdf/2606.13108) (PaddleOCR 3.7, Jun 2026)                                                                                                                                                                                   | Apache-2.0                                                                                                              | 50 languages, Czech and German among them                                                                                                                                                                                                                                                                                                      | text, JSON                 | 83.2 % recognition accuracy on the vendor's own set                                                                                                              | pip; runs on CPU; 1.5M–34.5M parameters                                                                                   |
| [PERO-OCR](https://github.com/DCGM/pero-ocr) (Brno University of Technology with the Moravian Library; papers on [layout](https://arxiv.org/pdf/2102.11838), [OCR](https://arxiv.org/pdf/2103.05489) and [adaptation](https://arxiv.org/pdf/2104.13037)) | BSD-3-Clause; the [web app](https://pero-ocr.fit.vutbr.cz/) is free for personal use and any use with manual correction | engines for low-quality print in most European languages including Latin, Fraktur in German and Czech, and handwriting, mainly Czech. The public download covers print; the other engines run in the web app and its REST API, or come on request                                                                                              | ALTO, PAGE XML, plain text | 1–4 % error on well-legible Czech manuscripts corrected by the app's users ([study, PDF](https://www.fit.vut.cz/research/result-file/c181521/280584/clanek.pdf)) | pip; Docker with a GPU; REST API with a test key on request. Pages sent to the app or API may be used to train its models |
| [CHURRO-3B](https://huggingface.co/stanford-oval/churro-3B) (Stanford)                                                                                                                                                                                   | Qwen research licence: check before any production use                                                                  | historical print and handwriting; [matches Gemini 2.5 Pro on Czech print](https://arxiv.org/pdf/2509.19768)                                                                                                                                                                                                                                    | text                       | CHURRO-DS 82.3 printed, 70.1 handwritten; 15.5 times cheaper than Gemini 2.5 Pro                                                                                 | code on GitHub                                                                                                            |
| [Kraken](https://github.com/mittagessen/kraken)                                                                                                                                                                                                          | Apache-2.0                                                                                                              | trainable on our own data, Kurrent for example                                                                                                                                                                                                                                                                                                 | ALTO, PAGE XML             | needs our own training data                                                                                                                                      | pip                                                                                                                       |
| [Transkribus](https://www.transkribus.org/models/transkribus-czech-handwriting-m1) (closed, reference only)                                                                                                                                              | service                                                                                                                 | Czech Handwriting M1: Czech handwriting of the 16th–21st century with some Latin and German; 4,315 training pages; 6.58 % CER. [Moravian Land Records](https://www.transkribus.org/models/moravian-land-records): a prototype for Czech and German hands of 1550–1850; 857 pages; 6.4 % CER. Both rates are on each model's own validation set | —                          | —                                                                                                                                                                | external service                                                                                                          |

Fine-tuning pays off for handwriting: adapting a recogniser to a new writer with 16 to 256 lines cut
its error rate by 25 to 50 % relative ([Kohút and Hradiš](https://arxiv.org/pdf/2302.06308), the PERO
team).

### General vision-language models

| Model                                                                                                          | Size, released                                             | Licence    | Languages, handwriting                                                 | Published results                                                                                                                           | Serving                                                                                                            |
|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)                                                         | 27B dense, Aug 2026                                        | Apache-2.0 | images and video; 262,144-token window; thinking mode on by default    | ODB 1.5 91.1 (card); ParseBench-2 73.4; OCRBench v2 63.5                                                                                    | SGLang, vLLM; the translator already serves it for text                                                            |
| [Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) and Qwen3.6-35B-A3B                                     | 27B dense; 35B mixture of experts with 3B active; Apr 2026 | Apache-2.0 | —                                                                      | OCRBench v2: 68.3 (27B), the best open model, and 65.5 (35B-A3B). ExtractBench (LlamaIndex): 87.3 % value F1 (35B-A3B), the best open model | vLLM                                                                                                               |
| [Gemma 4 31B](https://huggingface.co/google/gemma-4-31B) ([report](https://arxiv.org/pdf/2607.02770))          | 31B dense; also 26B-A4B, 12B, E4B, E2B; Jul 2026           | Apache-2.0 | 140+ languages in pre-training; OCR and handwriting recognition listed | ODB 1.5 average edit 0.131; the 26B-A4B scored 66.2 % on ExtractBench (LlamaIndex)                                                          | vLLM, SGLang                                                                                                       |
| [Qwen3.5-122B-A10B](https://huggingface.co/Qwen/Qwen3.5-122B-A10B)                                             | 122B mixture of experts, 10B active; Feb 2026              | Apache-2.0 | 201 languages claimed                                                  | ODB 1.5 89.8; CC-OCR 81.8; OCRBench 92.1                                                                                                    | vLLM                                                                                                               |
| [Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-27B) smaller sizes                                               | 0.8B to 35B-A3B; Feb–Mar 2026                              | Apache-2.0 | 201 languages claimed                                                  | Qwen3.5-27B ODB 1.5 88.9; Qwen3.5-9B MDPBench 65.7 (German 72.8) and IDP leaderboard 76.7                                                   | vLLM                                                                                                               |
| [Inkling 2 Small](https://huggingface.co/thinkingmachines/Inkling-2-Small) (Thinking Machines; reference only) | 594B mixture of experts, 17B active; Nov 2026              | Apache-2.0 | English, with general multilingual ability; 1M-token window            | ODB v1.6 94.6; MDPBench 81.4; GDP.pdf 25.2; AA-LCR 83.3; AA-Omniscience non-hallucination 73.3 %                                            | needs at least 500 GB of GPU memory (2× B300 or 4× H200), beyond our hardware; its API hosts are external services |

Also available, with weaker or no document evidence: Ovis2.6-30B-A3B (ODB 93.70), InternVL3.5,
Mistral Small 4, GLM-4.6V and MiniCPM-V 4.6. Kimi K2.5 (1T parameters) and MiniMax-M3 (428B) are
too large for this job.

### Schema extractors

| Tool                                                                      | Licence                          | What it does                                                                                                                                                           | Evidence                                                                                                                                                                 |
|---------------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [NuExtract3](https://huggingface.co/numind/NuExtract3) (NuMind, 4B, 2026) | Apache-2.0                       | fills a typed JSON template, which its SDK builds from a JSON Schema or a Pydantic model; empty fields come back as `null` or `[]`                                     | LlamaIndex's ExtractBench run: 47.9 % value F1, 54.4 % on short documents; its card reports 82.35 from NuMind's own run. olmOCR-Bench old scans 37.8. Not a first choice |
| NuExtract 2.0                                                             | 2B and 8B MIT; 4B non-commercial | the same template approach, one generation older                                                                                                                       | —                                                                                                                                                                        |
| Any model served by vLLM                                                  | —                                | [structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html), through the xgrammar or guidance backend, constrain the answer to a JSON Schema | syntax is guaranteed; correctness still has to be scored                                                                                                                 |

### Closed models, as a ceiling only

ODB v1.6: Gemini 3 Pro 92.91 (TE 0.064, TEDS 89.2), GPT-5.2 86.59. MDPBench: Gemini 3 Pro 86.4
overall, 91.2 on German. CHURRO-DS: Gemini 2.5 Pro equals CHURRO-3B on Czech print. Sending pages to
these services needs the job's permission, and the pilot has no cloud fallback.

### Not shortlisted

- **HunyuanOCR** ([paper](https://arxiv.org/pdf/2607.04884)): its [licence](https://huggingface.co/tencent/HunyuanOCR/blob/main/LICENSE) excludes
  the European Union, the United Kingdom and South Korea.
- **jina-ocr-v1**: CC BY-NC 4.0.
- **GLM-OCR**: its eight OCR languages include German but [not Czech](https://arxiv.org/pdf/2603.10910).
- **TeleOCR ([paper](https://arxiv.org/pdf/2608.12898)) and MiniCPM-OCR 1.0**: top OmniDocBench scores (96.91 and 96.44), but tagged for Chinese
  and English only.
- **MonkeyOCRv2** ([paper](https://arxiv.org/pdf/2607.11562)): 17 languages, German but not Czech.
- **OXR-1.0**: the top scores (ODB 97.03, olmOCR-Bench 87.84), but a commercial licence is needed
  above $2M in funding or revenue, with academic research exempt. It also runs on vLLM only through a
  plugin.
- **Infinity-Parser2-Pro** ([paper](https://arxiv.org/pdf/2607.07836)): 35B; its card says quality degrades on multilingual content.

## One model, or one per content type?

page-classification's labels describe the script (printed, typed, handwritten), tabular layout and
graphics of a page ([categories](https://github.com/ufal/atrium-page-classification/blob/test/docs/reference/categories.md)).
That makes them a good way to stratify scores. After the pilot, they could also pick a model per page.

| Pages                                                          | What is hard                                                               | Hypothesis to test                                                                    | First candidates                                                             |
|----------------------------------------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| Printed and typed text (`TEXT_P`, `TEXT_T`)                    | faded carbon copies, diacritics; Fraktur in older German items             | compact OCR models reach the large model's CER on Czech at a fraction of the GPU time | PaddleOCR-VL-1.6, OvisOCR3, LightOnOCR-3; PP-OCRv6 and PERO-OCR as baselines |
| Handwriting and mixed scripts (`TEXT_HW`, `TEXT`)              | Czech and German cursive, Kurrent                                          | compact OCR models fall behind; a large VLM or a handwriting model is needed          | Qwen3.8-27B, Gemma 4 31B, Chandra 2; PERO-OCR's handwriting engine           |
| Forms and tables (`LINE_P`, `LINE_T`)                          | merged cells, key–value fields                                             | a compact parser gets the structure; a schema extractor fills the fields              | PaddleOCR-VL-1.6 or OvisOCR3, then Qwen3.8-27B or Qwen3.6-35B-A3B            |
| Handwritten forms (`LINE_HW`)                                  | both of the above                                                          | one pass from image to JSON with a large VLM                                          | Qwen3.8-27B, Gemma 4 31B                                                     |
| Drawings, plans, photos (`DRAW`, `DRAW_L`, `PHOTO`, `PHOTO_L`) | labels, legends, captions, scale notes; `_L` pages have table-like layouts | a general VLM reads captions and legends; `_L` tables need a table parser             | Qwen3.8-27B; a compact parser for `_L` tables                                |

**Decision rule, as a proposal:**

1. Start with one model for every page: Qwen3.8-27B. It is #22's long-term target, and the translator
   already serves it.
2. Add a second model for a category only if the gold set shows a clear quality gain there, or the same
   quality at a much lower GPU time on a category with many pages. Fix both margins before scoring.
3. Keep at most two models in production. Each extra model is one more image, pin and licence to
   maintain.

Routing by category would itself be a decision after the pilot. During the pilot, categories never
route.

## Which models run first?

| Role (#22's matrix)        | Model                     | Why                                                                                                            |
|----------------------------|---------------------------|----------------------------------------------------------------------------------------------------------------|
| Baseline                   | the agreed route's record | what any change is measured against                                                                            |
| General VLM, the default   | Qwen3.8-27B               | #22's target; Apache-2.0; already served for the translator                                                    |
| General VLM, the alternate | Qwen3.6-35B-A3B           | the best open model on ExtractBench (LlamaIndex), 87.3 % value F1; 3B active parameters, so faster; Apache-2.0 |
| Lightweight                | PaddleOCR-VL-1.6          | Czech and German listed; its predecessor had the best open German score on MDPBench                            |
| Lightweight, the alternate | OvisOCR3                  | top self-reported multilingual and degradation scores; schema JSON built in                                    |
| Domain-compact             | Chandra 2 or CHURRO-3B    | the only published Czech score, or historical training; both under research licences                           |
| Large, hard tiers only     | Qwen3.5-122B-A10B         | tests whether the hard tiers are a capacity problem; 10B active parameters                                     |
| Plain baselines            | PP-OCRv6, PERO-OCR        | Czech-capable classic OCR; PERO is tuned on Czech                                                              |

Apart from the plain baselines and CHURRO-3B, every model here documents vLLM serving, so the runs
share one serving stack.

Each VLM runs in two arms:

- **one pass**: page image to JSON in one call, the target configuration of #22;
- **two passes**: page image to Markdown with a compact model, then Markdown to JSON with Qwen3.8-27B
  or Qwen3.6-35B-A3B. The second pass is the same one that born-digital and XML inputs use.

The `--detail` comparison of #22 (`full`, `standard`, `minimal` Markdown) applies to the second pass.

## What will it cost?

The two collections hold 113,101 documents and 71.8 million lines
([For archives](../../docs_site/for-archives.md)); the project's data management plan sizes them at
about 1.2 million pages. GPU-hours = pages ÷ (pages per second × 3,600).

| Model              | Published speed                 | GPU-hours for 1.2 million pages |
|--------------------|---------------------------------|---------------------------------|
| Nemotron 3.5 Parse | 18.6 pages/s on one H200        | about 18                        |
| LightOnOCR-2-1B    | 5.71 pages/s on one H100        | about 58                        |
| MinerU2.5-Pro      | 2.12 pages/s on one A100        | about 157                       |
| Chandra 2          | 1.44 pages/s on one H100        | about 231                       |
| Qianfan-OCR        | 1.02 pages/s on one A100, 8-bit | about 327                       |
| Qwen3.8-27B        | not published                   | to measure (M2)                 |

These speeds come from each vendor's own pages, settings and hardware. Our pages differ: many are
photos and drawings, and many typescripts are dense. Read the column as an order of magnitude. The
27B-class speed decides what the single-model option costs, which is why #22 measures it (M2)
together with the collection's size in tokens (M1).

Two practical points:

- The Grace Hopper machine is ARM. vLLM publishes ARM images (`latest-aarch64`, `v<version>-aarch64`)
  and documents builds for Grace Hopper ([Docker guide](https://docs.vllm.ai/en/latest/deployment/docker.html)),
  so the VLMs can run there. PaddleOCR-VL's [guide](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)
  lists NVIDIA GPUs and x64 CPUs but no ARM server: test its Transformers-plus-vLLM route there, or
  run it on the x86 nodes.
- Thinking modes stay off for transcription and extraction. They cost tokens, and reasoning text must
  never reach the content.

## What must a VLM step guarantee?

- **Fail, never truncate.** A reply cut by the token limit (`finish_reason: length`), a reply that is
  not valid against the schema, or a page left unprocessed fails the job. Nothing partial is written.
- **Long documents are split, and the split is recorded.** On LlamaIndex's ExtractBench, every VLM
  scores below 36 % on the longest documents, so a long report is extracted by section or page range
  and merged. The split and the context carried over go to the paradata's `limits`.
- **Settings are pinned and recorded.** The model revision, prompt version, image resolution and
  decoding settings go to the paradata's `parameters`.
- **Licences are listed, never merged.** Each component appears in `components` with its version and
  its own licence.
- **Content stays content.** No run data, such as timestamps, paths or model names, goes inside the
  Markdown or JSON.
- **Inputs and outputs are named as in the rest of the chain:** by distribution name and SHA-512,
  never by a temporary path.
- **Pages stay in.** No external service receives a page unless the job's licence flag allows it.

## Open questions after the pilot

These stay open until the pilot is released, and none goes to ARÚP or ARÚB before then. After
the release, requests for staff time or data go through David Novák.

1. **The gold set's shape.** Proposal: a page layer in OmniDocBench's JSON, a document layer of
   key-information JSON per document type, and optional unit tests. Agree, or amend?
2. **Key-information fields.** Which fields does each document type need, field reports first? With
   which value types, tolerances and weights?
3. **The catalogue as a first gold.** May AMČR's own metadata serve as gold for the document layer?
   The document record we tried is public through OAI-PMH; the event record it links to returned
   HTTP 403 without a login.
4. **Annotators.** Who can annotate, and when? The batch shared with
   [page-classification#58](https://github.com/ufal/atrium-page-classification/issues/58) still
   stands.
5. **Hardware.** Cluster GPUs for the compact models; the Grace Hopper machine for the 27B-class and
   the large model, by agreement with Viktor.
6. **A closed ceiling.** May a closed model read pages that are already public, such as the LINDAT
   page dataset? Never other pages.
7. **Research licences.** Are CHURRO-3B and Chandra 2 acceptable in the benchmark, knowing that
   production would need other terms?
8. **PERO's handwriting engine.** Should we ask its authors for local use? Their web app and API may
   reuse uploaded pages to train their models.

## References

Every paper below links to its PDF on arXiv. The tables above link the same papers, and the
repositories or model cards where a tool has no paper.

### Benchmarks and datasets

- Ouyang et al. (2024). *OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations*. CVPR 2025. [PDF](https://arxiv.org/pdf/2412.07626)
- Zhou et al. (2026). *Real5-OmniDocBench: A Full-Scale Physical Reconstruction Benchmark for Robust Document Parsing in the Wild*. arXiv preprint. [PDF](https://arxiv.org/pdf/2603.04205)
- Li et al. (2026). *How Far Is Document Parsing from Solved? PureDocBench: A Source-Traceable Benchmark across Clean, Degraded, and Real-World Settings*. arXiv preprint. [PDF](https://arxiv.org/pdf/2605.07492)
- Poznanski et al. (2025). *olmOCR: Unlocking Trillions of Tokens in PDFs with Vision Language Models*. arXiv preprint; introduces olmOCR-Bench. [PDF](https://arxiv.org/pdf/2502.18443)
- Zhang et al. (2026). *ParseBench: A Document Parsing Benchmark for AI Agents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2604.08538)
- Doulcet et al. (2026). *ParseBench-2: Severity-Aware Evaluation of Document Parsing*. arXiv preprint. [PDF](https://arxiv.org/pdf/2611.17400)
- Li et al. (2024). *READoc: A Unified Benchmark for Realistic Document Structured Extraction*. Findings of ACL 2025. [PDF](https://arxiv.org/pdf/2409.05137)
- Rigal et al. (2026). *Benchmarking Vision-Language Models for French PDF-to-Markdown Conversion*. arXiv preprint. [PDF](https://arxiv.org/pdf/2602.11960)
- Yang et al. (2024). *CC-OCR: A Comprehensive and Challenging OCR Benchmark for Evaluating Large Multimodal Models in Literacy*. arXiv preprint. [PDF](https://arxiv.org/pdf/2412.02210)
- Fu et al. (2024). *OCRBench v2: An Improved Benchmark for Evaluating Large Multimodal Models on Visual Text Localization and Reasoning*. arXiv preprint. [PDF](https://arxiv.org/pdf/2501.00321)
- Liu et al. (2024). *Focus Anywhere for Fine-grained Multi-page Document Understanding*. arXiv preprint. [PDF](https://arxiv.org/pdf/2405.14295)
- Yang et al. (2026). *Dr. DocBench: A Comprehensive Benchmark for Expert-Level and Difficult Document Parsing*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.01393)
- Zhou et al. (2026). *MPDocBench-Parse: Benchmarking Practical Multi-page Document Parsing*. arXiv preprint. [PDF](https://arxiv.org/pdf/2605.22100)
- Ferguson et al. (2026). *ExtractBench: A Benchmark and Evaluation Methodology for Complex Structured Extraction*. arXiv preprint. [PDF](https://arxiv.org/pdf/2602.12247)
- Zhang et al. (2026). *ExtractBench: A Benchmark for Schema-Guided Enterprise Document Extraction*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.29677)
- Bir et al. (2026). *From Pixels to Structure: Lightweight Vision-Language Models for Document OCR and Structured JSON Extraction*. ICDAR 2026. [PDF](https://arxiv.org/pdf/2610.11818)
- Pather et al. (2026). *From Handwriting to Structured Data: Benchmarking AI Digitisation of Handwritten Forms*. arXiv preprint. [PDF](https://arxiv.org/pdf/2604.16504)
- Joshi et al. (2026). *RealDocBench: A Benchmark for Field-Level QA and Layout Understanding on Real-World Regulated Documents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.07401)
- Wang et al. (2022). *VRDU: A Benchmark for Visually-rich Document Understanding*. KDD 2023. [PDF](https://arxiv.org/pdf/2211.15421)
- Šimsa et al. (2023). *DocILE Benchmark for Document Information Localization and Extraction*. ICDAR 2023. [PDF](https://arxiv.org/pdf/2302.05658)
- Stanisławek et al. (2021). *Kleister: Key Information Extraction Datasets Involving Long Documents with Complex Layouts*. ICDAR 2021. [PDF](https://arxiv.org/pdf/2105.05796)
- Jaume et al. (2019). *FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents*. ICDAR 2019 workshop. [PDF](https://arxiv.org/pdf/1905.13538)
- Xu et al. (2021). *LayoutXLM: Multimodal Pre-training for Multilingual Visually-rich Document Understanding*. arXiv preprint; introduces XFUND. [PDF](https://arxiv.org/pdf/2104.08836)
- Xu et al. (2022). *XFUND: A Benchmark Dataset for Multilingual Visually Rich Form Understanding*. Findings of ACL 2022. [PDF](https://aclanthology.org/2022.findings-acl.253.pdf)
- Huang et al. (2021). *ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction*. arXiv preprint. [PDF](https://arxiv.org/pdf/2103.10213)
- Zhong et al. (2019). *Image-based table recognition: data, model, and evaluation*. arXiv preprint; introduces PubTabNet and TEDS. [PDF](https://arxiv.org/pdf/1911.10683)
- Zheng et al. (2020). *Global Table Extractor (GTE): A Framework for Joint Table Identification and Cell Structure Recognition Using Visual Context*. WACV 2021; introduces FinTabNet. [PDF](https://arxiv.org/pdf/2005.00589)
- Smock et al. (2021). *PubTables-1M: Towards comprehensive table extraction from unstructured documents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2110.00061)
- Smock et al. (2025). *PubTables-v2: A new large-scale dataset for full-page and multi-page table extraction*. WACV 2027. [PDF](https://arxiv.org/pdf/2512.10888)
- Pandey et al. (2026). *PulseBench-Tab: A Multilingual Benchmark for Table Extraction with Graph-Based Evaluation*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.07534)
- Semnani et al. (2025). *CHURRO: Making History Readable with an Open-Weight Large Vision-Language Model for High-Accuracy, Low-Cost Historical Text Recognition*. EMNLP 2025. [PDF](https://arxiv.org/pdf/2509.19768)
- Li et al. (2026). *MDPBench: A Benchmark for Multilingual Document Parsing in Real-World Scenarios*. arXiv preprint. [PDF](https://arxiv.org/pdf/2603.28130)
- Xu et al. (2026). *MORE: A Multilingual Document Parsing Benchmark and Evaluation*. ICML 2026. [PDF](https://arxiv.org/pdf/2607.02956)
- Kostelník et al. (2025). *TextBite: A Historical Czech Document Dataset for Logical Page Segmentation*. arXiv preprint. [PDF](https://arxiv.org/pdf/2503.16664)
- Springmann et al. (2018). *Ground Truth for training OCR engines on historical documents in German Fraktur and Early Modern Latin*. JLCL 33(1), 2018. [PDF](https://arxiv.org/pdf/1809.05501)
- Schultze et al. (2024). *Chronicling Germany: An Annotated Historical Newspaper Dataset*. arXiv preprint. [PDF](https://arxiv.org/pdf/2401.16845)
- Ehrmann et al. (2026). *ICDAR 2026 HIPE-OCRepair Competition on LLM-Assisted OCR Post-Correction for Historical Documents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.08143)
- Tang et al. (2024). *MTVQA: Benchmarking Multilingual Text-Centric Visual Question Answering*. Findings of ACL 2025. [PDF](https://arxiv.org/pdf/2405.11985)
- Mathew et al. (2020). *DocVQA: A Dataset for VQA on Document Images*. WACV 2021. [PDF](https://arxiv.org/pdf/2007.00398)
- Mathew et al. (2021). *InfographicVQA*. arXiv preprint. [PDF](https://arxiv.org/pdf/2104.12756)
- Van Landeghem et al. (2023). *Document Understanding Dataset and Evaluation (DUDE)*. ICCV 2023. [PDF](https://arxiv.org/pdf/2305.08455)
- Tito et al. (2022). *Hierarchical multimodal transformers for Multi-Page DocVQA*. arXiv preprint. [PDF](https://arxiv.org/pdf/2212.05935)
- Ma et al. (2024). *MMLongBench-Doc: Benchmarking Long-context Document Understanding with Visualizations*. NeurIPS 2024 Datasets and Benchmarks. [PDF](https://arxiv.org/pdf/2407.01523)
- Deng et al. (2024). *LongDocURL: a Comprehensive Multimodal Long Document Benchmark Integrating Understanding, Reasoning, and Locating*. arXiv preprint. [PDF](https://arxiv.org/pdf/2412.18424)
- Faysse et al. (2024). *ColPali: Efficient Document Retrieval with Vision Language Models*. ICLR 2025; introduces ViDoRe v1. [PDF](https://arxiv.org/pdf/2407.01449)
- Macé et al. (2025). *ViDoRe Benchmark V2: Raising the Bar for Visual Retrieval*. arXiv preprint. [PDF](https://arxiv.org/pdf/2505.17166)
- Loison et al. (2026). *ViDoRe V3: A Comprehensive Evaluation of Retrieval Augmented Generation in Complex Real-World Scenarios*. arXiv preprint. [PDF](https://arxiv.org/pdf/2601.08620)
- Pfitzmann et al. (2022). *DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis*. KDD 2022. [PDF](https://arxiv.org/pdf/2206.01062)
- Cheng et al. (2023). *M6Doc: A Large-Scale Multi-Format, Multi-Type, Multi-Layout, Multi-Language, Multi-Annotation Category Dataset for Modern Document Layout Analysis*. CVPR 2023. [PDF](https://arxiv.org/pdf/2305.08719)
- Da et al. (2023). *Vision Grid Transformer for Document Layout Analysis*. ICCV 2023; introduces D4LA. [PDF](https://arxiv.org/pdf/2308.14978)
- Wang et al. (2021). *LayoutReader: Pre-training of Text and Layout for Reading Order Detection*. EMNLP 2021; introduces ReadingBank. [PDF](https://arxiv.org/pdf/2108.11591)

### Metrics, evaluation and historical OCR

- Peer et al. (2024). *ANLS* – A Universal Document Processing Metric for Generative Large Language Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2402.03848)
- Li et al. (2025). *SCORE: A Semantic Evaluation Framework for Generative Document Parsing*. arXiv preprint. [PDF](https://arxiv.org/pdf/2509.19345)
- Smock et al. (2022). *GriTS: Grid table similarity metric for table structure recognition*. arXiv preprint. [PDF](https://arxiv.org/pdf/2203.12555)
- Beyene and Dancy (2026). *A Survey of OCR Evaluation Methods and Metrics and the Invisibility of Historical Documents*. FAccT 2026. [PDF](https://arxiv.org/pdf/2603.25761)
- Levchenko (2025). *Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities*. LM4DH workshop, RANLP 2025. [PDF](https://arxiv.org/pdf/2510.06743)
- Kohút and Hradiš (2023). *Fine-tuning Is a Surprisingly Effective Domain Adaptation Baseline in Handwriting Recognition*. arXiv preprint. [PDF](https://arxiv.org/pdf/2302.06308)

### VLM capability benchmarks

- Lin et al. (2026). *PerceptionBench: Evaluating Atomic Visual Perception in Multimodal Large Language Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.24957)
- Chen et al. (2026). *BabyVision: Visual Reasoning Beyond Language*. arXiv preprint. [PDF](https://arxiv.org/pdf/2601.06521)
- Cheng et al. (2025). *SimpleVQA: Multimodal Factuality Evaluation for Multimodal Large Language Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2502.13059)
- Garre et al. (2026). *GDP.pdf: Benchmarking Grounded Multimodal Reasoning over Professional PDF Documents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.11192)
- Jackson et al. (2025). *AA-Omniscience: Evaluating Cross-Domain Knowledge Reliability in Large Language Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2511.13029)
- Wang et al. (2024). *MuirBench: A Comprehensive Benchmark for Robust Multi-image Understanding*. arXiv preprint. [PDF](https://arxiv.org/pdf/2406.09411)
- Wang et al. (2024). *CharXiv: Charting Gaps in Realistic Chart Understanding in Multimodal LLMs*. arXiv preprint. [PDF](https://arxiv.org/pdf/2406.18521)
- Garre et al. (2026). *Chartography: A Benchmark for Professional Chart Understanding*. arXiv preprint. [PDF](https://arxiv.org/pdf/2608.10677)
- Bai et al. (2024). *LongBench v2: Towards Deeper Understanding and Reasoning on Realistic Long-context Multitasks*. arXiv preprint. [PDF](https://arxiv.org/pdf/2412.15204)
- Ye et al. (2025). *LongProc: Benchmarking Long-Context Language Models on Long Procedural Generation*. COLM 2025. [PDF](https://arxiv.org/pdf/2501.05414)
- Tu et al. (2025). *LongWriter-V: Enabling Ultra-Long and High-Fidelity Generation in Vision-Language Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2502.14834)
- Pyatkin et al. (2025). *Generalizing Verifiable Instruction Following*. NeurIPS 2025 Datasets and Benchmarks. [PDF](https://arxiv.org/pdf/2507.02833)
- Mehta et al. (2026). *ComplexConstraints and Beyond: Expert Rubrics for RLVR*. GEM workshop, ACL 2026. [PDF](https://arxiv.org/pdf/2606.09118)
- Singh et al. (2024). *Global MMLU: Understanding and Addressing Cultural and Linguistic Biases in Multilingual Evaluation*. arXiv preprint. [PDF](https://arxiv.org/pdf/2412.03304)
- Yue et al. (2024). *MMMU-Pro: A More Robust Multi-discipline Multimodal Understanding Benchmark*. ACL 2025. [PDF](https://arxiv.org/pdf/2409.02813)
- Roberts et al. (2025). *ZeroBench: An Impossible Visual Benchmark for Contemporary Large Multimodal Models*. ICML 2026. [PDF](https://arxiv.org/pdf/2502.09696)
- Guo et al. (2026). *Humanity's Sixth Sense: Benchmarking Intuitive Visual Reasoning in Multimodal Models*. arXiv preprint. [PDF](https://arxiv.org/pdf/2610.08966)
- Li et al. (2025). *ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use*. arXiv preprint. [PDF](https://arxiv.org/pdf/2504.07981)
- Lau et al. (2026). *VIALS: A Benchmark for Visual Interpretation of Artifacts in the Life Sciences*. arXiv preprint. [PDF](https://arxiv.org/pdf/2608.21357)

### Models and tools

- Cui et al. (2025). *PaddleOCR-VL: Boosting Multilingual Document Parsing via a 0.9B Ultra-Compact Vision-Language Model*. arXiv preprint. [PDF](https://arxiv.org/pdf/2510.14528)
- Zhang et al. (2026). *PaddleOCR-VL-1.6: Expanding the Frontier of Document Parsing with Under-Optimized Region Refinement and Progressive Post-Training*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.03264)
- Zhang et al. (2026). *PP-OCRv6: From 1.5M to 34.5M Parameters, Surpassing Billion-Scale VLMs on OCR Tasks*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.13108)
- Lu et al. (2026). *OvisOCR2 Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.13639)
- Xia et al. (2026). *OvisOCR3 Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2610.33066)
- Taghadouini et al. (2026). *LightOnOCR: A 1B End-to-End Multilingual Vision-Language Model for State-of-the-Art OCR*. arXiv preprint. [PDF](https://arxiv.org/pdf/2601.14251)
- Wang et al. (2026). *MinerU2.5-Pro: Pushing the Limits of Data-Centric Document Parsing at Scale*. arXiv preprint. [PDF](https://arxiv.org/pdf/2604.04771)
- Dong et al. (2026). *Qianfan-OCR: A Unified End-to-End Model for Document Intelligence*. arXiv preprint. [PDF](https://arxiv.org/pdf/2603.13398)
- Li et al. (2025). *dots.ocr: Multilingual Document Layout Parsing in a Single Vision-Language Model*. arXiv preprint. [PDF](https://arxiv.org/pdf/2512.02498)
- Wei et al. (2026). *DeepSeek-OCR 2: Visual Causal Flow*. arXiv preprint. [PDF](https://arxiv.org/pdf/2601.20552)
- Poznanski et al. (2025). *olmOCR 2: Unit Test Rewards for Document OCR*. arXiv preprint. [PDF](https://arxiv.org/pdf/2510.19817)
- Auer et al. (2024). *Docling Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2408.09869)
- Livathinos et al. (2025). *Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion*. AAAI 2025 workshop. [PDF](https://arxiv.org/pdf/2501.17887)
- Duan et al. (2026). *GLM-OCR Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2603.10910)
- Yin et al. (2026). *Unlimited OCR Works*. arXiv preprint. [PDF](https://arxiv.org/pdf/2606.23050)
- Chen et al. (2026). *Xiaomi-OCR-0 Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2609.36136)
- Cai et al. (2026). *TeleOCR: Navigating Document Parsing Across Digital and Camera-Captured Documents*. arXiv preprint. [PDF](https://arxiv.org/pdf/2608.12898)
- Liu et al. (2026). *MonkeyOCRv2: A Visual-Text Foundation Model for Document AI*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.11562)
- Li et al. (2026). *HunyuanOCR-1.5: Making Lightweight OCR VLMs Faster and Better*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.04884)
- Huang et al. (2026). *Infinity-Parser2 Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.07836)
- Gemma Team et al. (2026). *Gemma 4 Technical Report*. arXiv preprint. [PDF](https://arxiv.org/pdf/2607.02770)
- Kodym and Hradiš (2021). *Page Layout Analysis System for Unconstrained Historic Documents*. ICDAR 2021. [PDF](https://arxiv.org/pdf/2102.11838)
- Kohút and Hradiš (2021). *TS-Net: OCR Trained to Switch Between Text Transcription Styles*. ICDAR 2021. [PDF](https://arxiv.org/pdf/2103.05489)
- Kišš et al. (2021). *AT-ST: Self-Training Adaptation Strategy for OCR in Domains with Limited Transcriptions*. ICDAR 2021. [PDF](https://arxiv.org/pdf/2104.13037)
- Kišš et al. (2019). *Brno Mobile OCR Dataset*. ICDAR 2019. [PDF](https://arxiv.org/pdf/1907.01307)
- Dvořáková et al. (2022). *Využití PERO OCR při přepisu rukopisů* [The use of PERO OCR in manuscript transcription]. Archivní časopis 72(1), 14–27. [PDF](https://www.fit.vut.cz/research/result-file/c181521/280584/clanek.pdf)

### Sources without a paper

- [RISE Humanities Data Benchmark](https://github.com/RISE-UNIBAS/humanities_data_benchmark): repository and leaderboard.
- [OmniAI OCR benchmark](https://github.com/getomni-ai/benchmark), [RD-TableBench](https://github.com/reductoai/RD-TableBench) and [CORD](https://github.com/clovaai/cord): repositories.
- [ICDAR 2019 cTDaR](https://github.com/cndplab-founder/ICDAR2019_cTDaR): the dataset repository; the competition report is in the ICDAR 2019 proceedings.
- [IDP leaderboard](https://www.idp-leaderboard.org/): a vendor-run leaderboard, version 1.5.
- [ExtractBench results](https://www.llamaindex.ai/blog/introducing-extractbench) and [ParseBench-2 results](https://www.llamaindex.ai/blog/introducing-parsebench-v2): LlamaIndex's announcements, with the open-weight scores.
- [OCRBench v2 leaderboard](https://99franklin.github.io/ocrbench_v2/).
- Transkribus model pages: [Czech Handwriting M1](https://www.transkribus.org/models/transkribus-czech-handwriting-m1) and [Moravian Land Records](https://www.transkribus.org/models/moravian-land-records).
- [PERO-OCR web app](https://pero-ocr.fit.vutbr.cz/): engines, terms of use and the REST API.
- [Inkling 2 Small model card](https://huggingface.co/thinkingmachines/Inkling-2-Small): the capability groups and scores cited above.
- Dataset cards: [AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR) and [Global-MMLU-Lite](https://huggingface.co/datasets/CohereLabs/Global-MMLU-Lite).
- Qwen3.8-27B, the Qwen3.5 family, Chandra 2, Nemotron 3.5 Parse, NuExtract3, Kraken and the Transkribus models: the model cards and repositories linked in the tables.
- vLLM documentation: [structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) and the [Docker guide](https://docs.vllm.ai/en/latest/deployment/docker.html).
- [PaddleOCR-VL guide](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html): supported hardware and serving routes.
- Not checked: the AHisto OCR dataset at Masaryk University and the CORD paper on OpenReview; neither site answered automated requests.

### Project sources

- [#22](https://github.com/ufal/atrium-project/issues/22): the four checks, the gold-format proposal, M1 and M2.
- The output contract of 12 November 2026 (ARÚP): decisions D19, D32 and D33.
- The benchmark harness: [`docs/evaluation/benchmark.md`](https://github.com/ufal/atrium-digital-convert/blob/test/docs/evaluation/benchmark.md) in digital-convert.
- Leaderboards read on 2026-11-20: [OmniDocBench v1.6](https://github.com/opendatalab/OmniDocBench) and [olmOCR-Bench](https://huggingface.co/datasets/allenai/olmOCR-bench).
