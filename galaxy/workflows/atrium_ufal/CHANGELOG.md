# Changelog

## [0.2.0] - 2026-11-07

Added `ATRIUM_ocr_nlp_keywords` (ALTO → OCR post-processing → NLP enrichment → keyword extraction) and
`ATRIUM_born_digital_keywords` (born-digital converter → keyword extraction), for ocr-postprocess
`1.15.4-beta+galaxy0`, nlp-enrich `1.3.4-beta+galaxy0`, keyword-extract `1.6.5-beta+galaxy0` and digital-convert
`1.4.5-beta+galaxy0`. The folder moved to `workflows/atrium_ufal/`, so that it sits beside the workflows of
DARIAH-ERIC/atrium-galaxy-tools without replacing their README; the four earlier workflows are unchanged but for
their release.

## [0.1.2] - 2026-11-06

The translator steps run `1.7.8-beta+galaxy0`: `v1.7.7-beta` was tagged before the commit that removed the
translator's old entry point, and its release stopped in the test job.

## [0.1.1] - 2026-11-06

The translator steps run `1.7.7-beta+galaxy0`: `v1.7.6-beta` was tagged on the commit before its version bump
and never released.

## [0.1.0] - 2026-11-05

First release: `ATRIUM_page_classification_images`, `ATRIUM_page_classification_pdfs`, `ATRIUM_translate_xml` and
`ATRIUM_classify_ocr_translate`, for page-classification `1.12.3-beta+galaxy0`, translator `1.7.6-beta+galaxy0`
and IUC Tesseract `5.5.3+galaxy0`.
