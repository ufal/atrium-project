---
title: Production pilot
nav_order: 12
status: partial
issue: 77
---

# Production pilot

AMČR colleagues run the six ATRIUM services themselves in the AMČR pilot, from December 2026 to January
2027. This page is where the handover starts: which images, which runbook for each, what to watch for,
and whom to ask. It follows the handover rules of the
[acceptance runbook](https://github.com/ufal/atrium-project/blob/main/docs/k8s_acceptance_runbook.md#handover-rules).
What each service does with the documents, in plain words: [For archives](for-archives.md). What is
measured and what is experimental: [Status](status.md).

## The six services

The pilot is assembled step by step: each step joins the chain with the release that is proven when it is
put together, which may be newer than the ones below. The release set agreed in
[#77](https://github.com/ufal/atrium-project/issues/77) is the starting point. The route these pages
describe, with record schema 2.0 and docproc, comes with the 2.0.0-beta releases of 26 November 2026; AMČR
chooses when each step moves to them. Each tool's command line and service give the same results from
the same input; what still differs, and why, is in one table in each tool's `docs/usage.md`.

The digest of each `-api` image is entered here when its step joins the chain; `latest` and `test` are never
the baseline. Acceptance on AMČR's cluster is separate (below).

| Step                                             | Image                                         | Starting release | Digest | Runbook                                                                                                     | Issues                                                               |
|--------------------------------------------------|-----------------------------------------------|------------------|--------|-------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| born-digital files → docproc, a verdict per page | `ghcr.io/ufal/atrium-digital-convert-api`     | `1.4.4-beta`     | —      | [service/README.md](https://github.com/ufal/atrium-digital-convert/blob/v1.4.4-beta/service/README.md)      | [tracker](https://github.com/ufal/atrium-digital-convert/issues)     |
| page categories, beside the ATR                  | `ghcr.io/ufal/atrium-page-classification-api` | `1.12.3-beta`    | —      | [service/README.md](https://github.com/ufal/atrium-page-classification/blob/v1.12.3-beta/service/README.md) | [tracker](https://github.com/ufal/atrium-page-classification/issues) |
| the record, every line scored                    | `ghcr.io/ufal/atrium-ocr-postprocess-api`     | `1.15.3-beta`    | —      | [service/README.md](https://github.com/ufal/atrium-ocr-postprocess/blob/v1.15.3-beta/service/README.md)     | [tracker](https://github.com/ufal/atrium-ocr-postprocess/issues)     |
| morphology, named entities, TEITOK               | `ghcr.io/ufal/atrium-nlp-enrich-api`          | `1.3.3-beta`     | —      | [service/README.md](https://github.com/ufal/atrium-nlp-enrich/blob/v1.3.3-beta/service/README.md)           | [tracker](https://github.com/ufal/atrium-nlp-enrich/issues)          |
| keywords                                         | `ghcr.io/ufal/atrium-keyword-extract-api`     | `1.6.4-beta`     | —      | [service/README.md](https://github.com/ufal/atrium-keyword-extract/blob/v1.6.4-beta/service/README.md)      | [tracker](https://github.com/ufal/atrium-keyword-extract/issues)     |
| English metadata, on archiving                   | `ghcr.io/ufal/atrium-translator-api`          | `1.7.5-beta`     | —      | [service/README.md](https://github.com/ufal/atrium-translator/blob/v1.7.5-beta/service/README.md)           | [tracker](https://github.com/ufal/atrium-translator/issues)          |

The ATR, the text-recognition service between digital-convert and ocr-postprocess, is AIS CR's own and is not
listed here.

**For operators: finding a digest.**

- Each release lists the digest of every image it published in its `images.json` asset. The image tag is
  the release without its leading `v`.
- Read a digest from that file, or with `docker buildx imagetools inspect <image>:<tag>`.
- Every end-to-end run records the digest and source of each image it ran (`e2e-manifest.json`, an
  artifact of the run). A green run at these release tags shows which releases passed together.
- The end-to-end lanes run the batch images for most stages. The digests to record are those of the
  `-api` images of the same releases.

## Before you rely on a result

Each runbook has a **Known limits** section. These are the ones a pilot user meets first:

- **ocr-postprocess** scores language and quality line by line; its rules are tuned for Czech, so
  lines in other languages are scored less reliably.
- **translator** needs the field list with each metadata request (`xpaths`); without it the request is
  refused (422, `cause: missing_xpaths`) in release 2.0.0-beta. It refuses a language pair its backend has
  no model for (422, `cause: unsupported_language_pair`) rather than routing it through another language.
- **digital-convert** never refuses a document in release 2.0.0-beta: it gives every page a verdict, and a
  page without usable text sends the whole document through the ATR. The starting release `1.4.4-beta`
  still refuses a PDF that carries an OCR text layer. Its upload limit is 250 MB; a deployment can raise it
  for larger originals, but files up to 1.5 GB are not yet tested for memory, concurrency and timeouts.
- **keyword-extract**'s vocabulary-controlled kind is experimental and not evaluated; its statistical
  kind needs no backend.
- **page-classification** classifies at most `MAX_PDF_PAGES` pages of a PDF per request (default 50);
  raise it to the longest document the deployment sends.
- **nlp-enrich** calls LINDAT's UDPipe and NameTag. Its `/jobs` are kept in memory: a restart loses them, and
  the caller submits a lost job again (accepted for the pilot).
- **LINDAT.** Until the terms of LINDAT's services are settled
  ([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)), AMČR does not publish outputs made
  through them: the linguistic layer, the entities, the TEITOK file and the English metadata.

## Acceptance

AMČR's acceptance on its own cluster was planned for the **second half of November**, before the December
pilot, coordinated with [@rharasim](https://github.com/rharasim). The procedure and its results table are in
the [Kubernetes acceptance runbook](https://github.com/ufal/atrium-project/blob/main/docs/k8s_acceptance_runbook.md).
The table has one row per service: the digest each pod ran and what each check printed, and for the
translator a run on real AMČR metadata. The completed table is linked here when AMČR returns it.

## Contacts

| Role                                       | Who                                      |
|--------------------------------------------|------------------------------------------|
| the six tools, their releases and runbooks | [@K4TEL](https://github.com/K4TEL)       |
| LINDAT services; ÚFAL repository settings  | [@stranak](https://github.com/stranak)   |
| AMČR pilot lead                            | [@motyc](https://github.com/motyc)       |
| AMČR acceptance on the cluster             | [@rharasim](https://github.com/rharasim) |

Further AMČR contacts are added as AMČR names them. Questions go to the issue tracker of the service
concerned, or to [#77](https://github.com/ufal/atrium-project/issues/77) for the handover as a whole.
