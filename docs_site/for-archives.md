---
title: For archives
nav_order: 21
status: published
issue: 79
---

# What the tools do with your documents

This page is for archive and collection staff. It explains, without code, what the ATRIUM tools do
with the documents you give them, what you get back, how far to trust it, and what leaves your
institution. Unfamiliar words are explained in the [glossary](glossary.md).

## Two routes into the chain

**Scanned pages.** A scan or photograph of a paper page goes this way:

1. **page-classification** looks at the image and says what kind of page it is: one of eleven types,
   such as typed text, a handwritten table, a drawing or a photograph. The type tells a person, or a
   script, which treatment the page needs next.
2. **OCR** turns the text pages into text. OCR is run outside these tools.
3. **ocr-postprocess** checks every line of the OCR output and labels its quality. You see which
   lines can be used as they are, which need correcting, and which need another OCR pass.
4. **nlp-enrich** adds grammar and names: each word's base form and part of speech, and the names of
   people, places and organisations.
5. **keyword-extract** adds keywords to the document and its pages.

**Born-digital files.** A PDF exported from Word, or an office file, already holds its text.
**digital-convert** reads it directly, with no OCR. Pages without usable text, such as scanned plans
inside the PDF, are marked for the scanned route. Most of the AMČR reports tried so far mix both
kinds of page, so the choice is made page by page.

**Translation.** The **translator** writes an English version of AMČR metadata records and of OCR
pages. Every tag of the document stays where it was; only the text changes.

Everything a document gains is kept in one file per document, the **record**, together with a log
of which tool did what, when, and with which settings (the **paradata**).

## What you get back, and what a person should check

| Stage               | What you get back                                                                                                   | What a person should check                                                                                                                             |
|---------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| page-classification | a page type for every page, with a score, and the next likely types                                                 | pages with a low score; typed text taken for mixed text, and handwritten tables taken for typed ones, are the most common mistakes                     |
| ocr-postprocess     | every text line with its language and a quality label: `Clear`, `Noisy`, `Trash` (illegible), `Non-text` or `Empty` | short lines without Czech diacritics labelled `Clear`, since some are OCR garbage; lines in languages other than Czech, which are scored less reliably |
| digital-convert     | the pages and lines in reading order, with headings and tables; for a PDF, where each line sits on the page         | tables without ruling lines, which are read column by column; letter-spaced captions and map labels, which come apart; pages marked for OCR            |
| nlp-enrich          | base forms, parts of speech, grammar and names, in a TEITOK file that can be searched and shown over the scan       | it works on Czech only; its name recogniser is a general model, not one trained on archaeological texts                                                |
| keyword-extract     | keywords for each document and page; optionally, terms from AMČR's keyword lists and the TEATER thesaurus           | the vocabulary-based keywords are experimental and not yet evaluated                                                                                   |
| translator          | the same XML document in English                                                                                    | no person has checked the translations yet; where a record must stay valid AMČR, use the default "replace" mode                                        |

Each tool's own README lists its limits in full, under "Limits and maturity".

## How reliable the results are

The tools' tests check that the programs do what their documentation says. They do not measure how
often the results are right. That has been measured for two tools only:

- **page-classification** was measured on about 4,800 pages per model that the model had never seen.
  It names the right page type first for 94.6–95.9 % of them, and among its first three for
  99.8–99.9 %. Born-digital pages, and documents unlike the archaeological reports it was trained on,
  were not measured ([what was measured](https://github.com/ufal/atrium-page-classification/blob/test/docs/evaluation/results.md)).
- **ocr-postprocess** was checked against 2,067 lines labelled by hand, and its rule changes were
  measured over both collections: 113,101 documents and 71.8 million lines from ARÚP and ARÚB. One
  weakness is counted: about 26,000 lines of OCR garbage read `Clear`. The labels have not been
  validated in full ([what was measured](https://github.com/ufal/atrium-ocr-postprocess/blob/test/docs/evaluation/categorization.md)).
- **digital-convert** was tried on 15 AMČR excavation reports, 2,514 pages. What went wrong there was
  fixed or is listed as a limit; there is no accuracy figure
  ([the AMČR samples](https://github.com/ufal/atrium-digital-convert/blob/test/docs/evaluation/amcr-samples.md)).
- **nlp-enrich, the translator, and keyword-extract's vocabulary-based keywords** have not been
  measured on archival documents.

## What leaves your institution

The services run on your own infrastructure. Three of them send document text to another service
while they work:

| Tool                | Sends document text out                                                                                                                                    | Downloads when it first starts               |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| page-classification | no                                                                                                                                                         | its five models, from the Hugging Face Hub   |
| ocr-postprocess     | no                                                                                                                                                         | two of its models, from the Hugging Face Hub |
| digital-convert     | no                                                                                                                                                         | nothing                                      |
| nlp-enrich          | **yes**: every line, to LINDAT's UDPipe and NameTag, or to copies of them that you run                                                                     | nothing                                      |
| keyword-extract     | only for vocabulary-based keywords: to the language-model service the deployment names                                                                     | its keyword model, from the Hugging Face Hub |
| translator          | **yes**: the text to translate, to LINDAT's translation service by default (and, with a vocabulary, to LINDAT's UDPipe), or to a model server that you run | nothing                                      |

- **A download sends no document data.** A deployment without internet access can supply the models
  in advance; each service's runbook says how.
- **LINDAT** is a public research service run by ÚFAL, Charles University, under its
  [terms of use](https://lindat.mff.cuni.cz/en/terms-of-use).
- **Planned:** each document will carry its own permission, and a document without one will not be
  sent to an external service. AMČR agreed to this on 22 October 2026; the tools do not enforce it
  yet ([Licences and paradata](ecosystem/licences.md#what-changes)).

## Who holds the rights in the results

The tools record every component they used, each with its own licence or terms of use. They do not
decide the rights in what they produce. Those depend first on the source document, which no tool
knows. AMČR states the rights of the outputs it publishes. The full explanation is on
[Licences and paradata](ecosystem/licences.md).

## Whom to ask

- **About a tool, or a result that looks wrong:** that tool's issue tracker, linked from the
  [S2 pilot handover](pilot.md#the-six-services).
- **About the pilot:** the contacts listed on the [S2 pilot handover](pilot.md#contacts).

## Sources

| Source                                                                                                | What was taken from it                                         |
|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| the six tools' `README.md`, "Limits and maturity", at their 10-29 patch releases                      | the stages, what each gives back, what to check                |
| the six tools' `service/README.md`, "Models and caches"                                               | what each service downloads and calls                          |
| page-classification `docs/evaluation/results.md`; ocr-postprocess `docs/evaluation/categorization.md` | the measured figures                                           |
| digital-convert `docs/evaluation/amcr-samples.md`                                                     | the 15 AMČR reports; mixed documents                           |
| [Licences and paradata](ecosystem/licences.md)                                                        | the rights in the results; the planned per-document permission |
