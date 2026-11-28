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

## How a document goes through the tools

In the AMČR pilot, a document uploaded to AMČR goes through the tools in one job:

1. **digital-convert** reads a PDF or an office file directly, with no OCR, and gives each page a
   verdict: is its text usable? It never refuses a document. An office file's text is always its own;
   only a page that holds nothing but a picture, such as a pasted scan, needs text recognition. Every
   picture, chart or drawing is marked with its place on the page.
2. **The ATR**, the text-recognition service of AIS CR, reads what has no usable text: an image, or a
   whole document of which any page needs text recognition, with those pages marked.
   **page-classification** looks at those pages, and at the pages that show pictures, charts or drawings,
   and says what kind of page each is: one of eleven types, such as typed text, a handwritten table, a
   drawing or a photograph.
3. **ocr-postprocess** builds the record of the document from the page layout, keeping the born-digital
   text where it is good, and labels every line's quality. You see which lines can be used as they
   are, and which cannot be read.
4. **nlp-enrich** adds grammar and names: each word's base form and part of speech, and the names of
   people, places and organisations.
5. **keyword-extract** adds keywords to the document and its pages.

Most of the AMČR reports tried so far mix born-digital text and scanned pages, so each page gets its
own verdict. A step that cannot finish fails the job, and nothing of it is stored: there is no
partial result.

**Translation.** The **translator** writes an English version of an AMČR metadata record when the
record is archived: the free-text fields AMČR names. Every tag of the record stays where it was; only
the text changes.

Everything a document gains is kept in one file per document, the **record**. What each run read,
wrote and used is kept beside it, in the **paradata**. Until the terms of LINDAT's services are settled
([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)), AMČR does not publish outputs
made through them: the linguistic layer, the entities, the TEITOK file and the English metadata.

## What you get back, and what a person should check

| Stage               | What you get back                                                                                                              | What a person should check                                                                                                                             |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| page-classification | a page type for every page, with a score, and the next likely types                                                            | pages with a low score; typed text taken for mixed text, and handwritten tables taken for typed ones, are the most common mistakes                     |
| ocr-postprocess     | every text line with its language and a quality label: `Clear`, `Noisy`, `Trash` (illegible), `Non-text` or `Empty`            | short lines without Czech diacritics labelled `Clear`, since some are OCR garbage; lines in languages other than Czech, which are scored less reliably |
| digital-convert     | the pages and lines in reading order, with headings and tables, and where each line sits on the page; a verdict for every page | tables without ruling lines, which are read column by column; letter-spaced captions and map labels, which come apart; pages marked for the ATR        |
| nlp-enrich          | base forms, parts of speech, grammar and names, in a TEITOK file that can be searched and shown over the scan                  | it works on Czech only; its name recogniser is a general model, not one trained on archaeological texts                                                |
| keyword-extract     | keywords for each document and page; optionally, terms from AMČR's keyword lists and the TEATER thesaurus                      | the vocabulary-based keywords are experimental and not yet evaluated                                                                                   |
| translator          | the metadata record, its free-text fields in English                                                                           | no person has checked the translations yet; where a record must stay valid AMČR, use the default "replace" mode                                        |

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

The services run on your own infrastructure. Two of them send document text to another service while
they work, and keyword-extract does for one kind of keyword. The ATR is AIS CR's own service, which
AMČR's pipeline calls for the scanned pages.

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
  sent to an external service. AMČR has agreed to this; the tools do not enforce it yet ([Licences and paradata](ecosystem/licences.md#what-may-leave-the-archive)).

## Who holds the rights in the results

Each run lists the components it used, each with its own licence or terms. No licence of an output
is computed: the rights in an output follow the source document, which no tool knows. AMČR states the
rights of the outputs it publishes. The full explanation is on
[Licences and paradata](ecosystem/licences.md).

## Whom to ask

- **About a tool, or a result that looks wrong:** that tool's issue tracker, linked from the
  [Production pilot](pilot.md#the-six-services).
- **About the pilot:** the contacts listed on the [Production pilot](pilot.md#contacts) page.

## Sources

| Source                                                                                                       | What was taken from it                                         |
|--------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| the six tools' `README.md`, "Limits and maturity", on their `test` branches (release 2.0.0-beta), 2026-11-21 | the stages, what each gives back, what to check                |
| the six tools' `service/README.md`, "Models and caches"                                                      | what each service downloads and calls                          |
| page-classification `docs/evaluation/results.md`; ocr-postprocess `docs/evaluation/categorization.md`        | the measured figures                                           |
| digital-convert `docs/evaluation/amcr-samples.md`                                                            | the 15 AMČR reports; mixed documents                           |
| [Licences and paradata](ecosystem/licences.md)                                                               | the rights in the results; the planned per-document permission |
