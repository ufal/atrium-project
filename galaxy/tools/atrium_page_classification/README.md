# ATRIUM page classification: Galaxy tool

`page_classification.xml` runs the batch image of
[ufal/atrium-page-classification](https://github.com/ufal/atrium-page-classification) at release
`1.12.3-beta` (`ghcr.io/ufal/atrium-page-classification:1.12.3-beta`). It sorts page images, or the pages of a PDF,
into eleven categories and writes the Top-N table, the paradata and the ATRIUM document record.

The image's entry point runs Galaxy's job script as given (since `v1.10.5-beta`): no `--entrypoint` setting is
needed on the destination.

## Inputs, parameters, outputs

| Inputs     | page images (`png`, `jpg`, `tiff`), best as a list collection; or one PDF (`pdf`), with a page selection and an optional baseline record (`json`)                                                                           |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters | one model (`v1.4`–`v5.4`, default `v4.4`) or the five-model ensemble; categories kept per page (1–11); the weights (downloaded in the job, or staged on the server); the categories whose pages are routed onward (images)  |
| Outputs    | Top-N table (`csv`); all scores (`csv`, optional, one model); votes per model (`csv`, ensemble); paradata (`json`); the document record (`json`, PDF) or records (a list of `json`, images); pages to route (`txt`, images) |

- **Page names.** A collection's element identifiers become file names; run.py reads `FILE` and `PAGE` from them,
  `<document>-<page>` (the number after the last `-` or `_`). An extension in the identifier is dropped, and
  characters other than letters, digits, `.`, `-` and `_` become `_`.
- **The `CATEGORY` column.** At one category per page the table has `FILE,PAGE,CLASS-1,SCORE-1,CATEGORY`;
  `CATEGORY` repeats `CLASS-1`, and the test checks that header (Mark A. Greenwood's fix of 2026-11-03).
- **Pages to route** lists the identifiers whose `CLASS-1` is one of the chosen categories (default `TEXT_P`,
  `TEXT_T`, `TEXT`). The workflow `ATRIUM_classify_ocr_translate.ga` uses it to send only text pages to OCR.

## Model weights

| Choice             | What the job does                                                                              | Cost                              |
|--------------------|------------------------------------------------------------------------------------------------|-----------------------------------|
| Download (default) | `run.py --hf` into the job's temporary directory; the ensemble downloads its five models first | about 0.5 GB per model, every job |
| Staged             | `run.py --models-dir <path from the atrium_page_models table>`, offline (`HF_HUB_OFFLINE=1`)   | none per job                      |

**Admin steps for *Staged*:**

1. Install the data manager `galaxy/data_managers/data_manager_atrium_page_models/` and run *ATRIUM
   page-classification models* once (all five revisions, about 2.5 GB). It fills the `atrium_page_models` table
   (`tool_data_table_conf.xml.sample`, `tool-data/atrium_page_models.loc.sample`).
2. Mount the data manager's data path into the tool's container, read-only. In the job configuration, for the
   destination that runs this tool, add to `docker_volumes`: `$galaxy_data_manager_data_path:ro` (or the absolute
   path that `galaxy_data_manager_data_path` names).
3. Optionally make *Staged* the default in the tool's `models` conditional.

## Tests

```bash
planemo lint page_classification.xml
planemo test --docker --galaxy_branch v26.1.1 page_classification.xml
```

Three tests: three page images with model `v4.4` at one category per page (the `CATEGORY` header, two records, the
routing list); a two-page PDF at three categories per page (a record with `page_categories`); a page past the end
of the PDF (exit 2). Each test downloads `v4.4` from the Hugging Face Hub (about 0.5 GB).

`test-data/` holds three pages of the tool's `small_data_samples/` and a PDF made from two more. They are
CC BY-NC 4.0, as `test-data/LICENSE` says.

## Licences

The code is MIT. The fine-tuned models are CC BY-NC 4.0, like the dataset they were trained on; the paradata of each
run lists the components and their licences.
