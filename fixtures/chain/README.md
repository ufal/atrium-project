# A chain sample — `CTX000000003` through four tools

One document through the AMČR pilot's route, run with the four tools' `v2.0.0-beta` code: the record built from
docproc and each tool's step on it, with the paradata 3.0 of every step. It is what the
[E2E pipeline lane](../../.github/workflows/e2e-pipeline-smoke.yml) checks on every run, kept as files: the lane
uploads its own only when it fails.

The input is the lane's default fixture, [`../e2e/docproc/CTX000000003.atr.docproc.json`](../e2e/docproc/), the ATR
stand-in, and the page image rendered from [`../e2e/ALTO/CTX000000003.alto.xml`](../e2e/ALTO/) by
[`tools/e2e/render_alto_page.py`](../../tools/e2e/render_alto_page.py). The steps ran from each tool's checkout on
ÚFAL's cluster, with the same arguments as the lane's images, and the files are as the tools wrote them (the
whitespace hooks leave this folder alone, so the SHA-512s in the paradata still match):

| Step                | What ran                                                                                     | Files in `CTX000000003/`                                |
|---------------------|----------------------------------------------------------------------------------------------|---------------------------------------------------------|
| ocr-postprocess     | `build_record.py` on the docproc: the record, every line scored                              | `records/1_record.json`, `paradata/ocr-postprocess/`    |
| page-classification | `run.py -f <page image> -rev v4.4` with the record: `page_categories` and the page rows      | `records/2_pc.json`, `paradata/page-classification/`    |
| nlp-enrich          | `run_pipeline.py --text-from-record` on LINDAT: lemmas, entities, the TEITOK file            | `records/3_nlp.json`, `teitok/`, `paradata/nlp-enrich/` |
| keyword-extract     | `keywords.py -m keybert --per-page` on the record: the `keywords` block                      | `records/4_kw.json`, `paradata/keyword-extract/`        |

Each step's paradata name the record it read and the record it wrote by `atrium/document-json` and SHA-512, with the
blocks and fields written. The last record passed
[`tools/e2e/e2e_assert.py`](../../tools/e2e/e2e_assert.py) against the docproc, and the record with all four steps'
paradata passed [`tools/ci/rocrate_check.py`](../../tools/ci/rocrate_check.py) (RO-Crate 1.2, Process Run Crate 0.5);
the crate it built is in `crate/`.

The outputs made through LINDAT (the linguistic layer, the entities, the TEITOK file) are samples of the format: AMČR
does not publish such outputs until LINDAT's terms are settled
([atrium-project#78](https://github.com/ufal/atrium-project/issues/78)).
