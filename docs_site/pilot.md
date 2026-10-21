---
title: S2 pilot handover
nav_order: 12
status: partial
issue: 77
---

# S2 pilot handover

AMČR colleagues run the six ATRIUM services themselves in the S2 pilot (December 2026 – January
2027). This page is where the handover starts: which images, which runbook for each, what to watch
for, and whom to ask. It follows the handover rules of the
[acceptance runbook](https://github.com/ufal/atrium-project/blob/main/docs/k8s_acceptance_runbook.md#handover-rules).

## The six services

The versions below are each tool's newest release on 20 October 2026. The **approved** set, named by
image digest, is proposed on 11 November and agreed with AMČR; until then the digest column stays
empty, and `latest` or `test` are never the baseline.

| Stage                              | Image                                         | Release       | Approved digest | Runbook                                                                                                    | Issues                                                               |
|------------------------------------|-----------------------------------------------|---------------|-----------------|------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| page categories                    | `ghcr.io/ufal/atrium-page-classification-api` | `1.9.5-beta`  | —               | [service/README.md](https://github.com/ufal/atrium-page-classification/blob/v1.9.5-beta/service/README.md) | [tracker](https://github.com/ufal/atrium-page-classification/issues) |
| OCR output and text files → lines  | `ghcr.io/ufal/atrium-ocr-postprocess-api`     | `1.12.1-beta` | —               | its runbook comes with the next release (model pre-fetch first)                                            | [tracker](https://github.com/ufal/atrium-ocr-postprocess/issues)     |
| born-digital files → the record    | `ghcr.io/ufal/atrium-digital-convert-api`     | `1.2.1-beta`  | —               | [service/README.md](https://github.com/ufal/atrium-digital-convert/blob/v1.2.1-beta/service/README.md)     | [tracker](https://github.com/ufal/atrium-digital-convert/issues)     |
| morphology, named entities, TEITOK | `ghcr.io/ufal/atrium-nlp-enrich-api`          | `1.1.2-beta`  | —               | [service/README.md](https://github.com/ufal/atrium-nlp-enrich/blob/v1.1.2-beta/service/README.md)          | [tracker](https://github.com/ufal/atrium-nlp-enrich/issues)          |
| keywords                           | `ghcr.io/ufal/atrium-keyword-extract-api`     | `1.4.0-beta`  | —               | [service/README.md](https://github.com/ufal/atrium-keyword-extract/blob/v1.4.0-beta/service/README.md)     | [tracker](https://github.com/ufal/atrium-keyword-extract/issues)     |
| English metadata                   | `ghcr.io/ufal/atrium-translator-api`          | `1.5.0-beta`  | —               | [service/README.md](https://github.com/ufal/atrium-translator/blob/v1.5.0-beta/service/README.md)          | [tracker](https://github.com/ufal/atrium-translator/issues)          |

The image tag is the release without its leading `v`. A digest is read with
`docker buildx imagetools inspect <image>:<tag>`. Every E2E run also records the digest and the source
ref of each image it ran (`e2e-manifest.json`, an artifact of the run): a green run at these release
tags shows which releases passed together. The lanes run the batch images for most stages, so the
approved digests are still those of the `-api` images of the same releases.

## Before you rely on a result

Each runbook ends with a **Known limits** section. The ones a pilot user meets first:

- **ocr-postprocess** scores language and quality line by line; its rules are tuned for Czech, so
  lines in other languages are scored less reliably.
- **translator** refuses a language pair its backend has no model for (422,
  `cause: unsupported_language_pair`) rather than routing it through another language; by default it
  calls LINDAT, whose output terms are open under [#78](https://github.com/ufal/atrium-project/issues/78).
- **digital-convert** reads born-digital files only: a PDF that carries an OCR text layer is refused,
  and pages whose text was extracted damaged are flagged for OCR. Its upload limit (200 MB) is raised per
  deployment for larger originals.
- **keyword-extract**'s vocabulary-controlled kind is experimental and not evaluated; its statistical
  kind needs no backend.
- **page-classification** classifies at most `MAX_PDF_PAGES` pages of a PDF per request (default 50);
  set it to the longest report when it runs behind digital-convert's `/describe`.
- **nlp-enrich** calls LINDAT's UDPipe and NameTag; its job registry does not survive a restart.

## Acceptance

The acceptance procedure and its results table are in the
[Kubernetes acceptance runbook](https://github.com/ufal/atrium-project/blob/main/docs/k8s_acceptance_runbook.md):
one row per service, with the digest each pod ran and what each check printed. The completed table is
linked here when AMČR returns it.

## Contacts

| Role                                       | Who                                    |
|--------------------------------------------|----------------------------------------|
| the six tools, their releases and runbooks | [@K4TEL](https://github.com/K4TEL)     |
| LINDAT services; ÚFAL repository settings  | [@stranak](https://github.com/stranak) |
| AMČR pilot lead                            | [@motyc](https://github.com/motyc)     |

Further AMČR contacts are added as AMČR names them. Questions go to the issue tracker of the service
concerned, or to [#77](https://github.com/ufal/atrium-project/issues/77) for the handover as a whole.
