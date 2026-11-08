# ATRIUM OCR post-processing: Galaxy tools

Two tools run the batch image of [ufal/atrium-ocr-postprocess](https://github.com/ufal/atrium-ocr-postprocess) at
release `1.15.4-beta` (`ghcr.io/ufal/atrium-ocr-postprocess:1.15.4-beta`). Both take one document per job; a
collection maps over them.

| Tool                                                  | Stages                                       | Runs on |
|-------------------------------------------------------|----------------------------------------------|---------|
| `ocr_postprocess.xml`, *ATRIUM OCR post-processing*   | split, statistics, extract                   | CPU     |
| `ocr_line_quality.xml`, *ATRIUM OCR line quality*     | the same, then classify and aggregate        | **GPU** |

`macros.xml` holds what they share: the inputs, the job's first steps and the config writer.

## Inputs, parameters, outputs

| Inputs     | one document: ALTO or PAGE (`xml`), OCR JSON (`json`), `txt`, `csv`/`tsv`/`tabular` with a `text` column, hOCR (`html`), `pdf`, `docx`, `xlsx`, `markdown`; an optional baseline record (`json`)                                                                                                               |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters | the reading method (text lines, ALTO with alto-tools, OCR JSON); for text lines, fail on an unreadable file; line quality only: the expected languages, the perplexity model (downloaded or staged)                                                                                                            |
| Outputs    | page texts (a list of `txt`), page statistics (`csv`), the document record (`json`), paradata (`json`); text lines: the line table (`csv`) and, CPU tool, the pages report (`csv`); ALTO: one ALTO per page (a list of `xml`); line quality: lines with their category (`csv`) and categories per page (`csv`) |

- **The line table** (`file,page_num,line_num,text,page_label`) is what *ATRIUM NLP enrichment* reads. The text-lines
  method writes it for ALTO too.
- **Names.** The document is copied as `input/<element identifier>.<ext>`, a known extension in the identifier
  dropped; the document id, and so the page names `<document>-<page>`, come from it.
- **How the job runs the pipeline.** `run_pipeline.py` starts its stages by name from its working directory, and every
  stage writes its paradata to `paradata/` there. The job therefore runs it from a folder of links to `/app/*` with a
  `paradata/` of its own, and writes a copy of `/app/setup/config.txt` with every path in the job directory (all other
  keys, the classifier's thresholds among them, kept). Nothing is written into the image, so any user id works.
- **CRLF.** The line table and the pages report end their lines with CRLF; the tests use `has_text` on them.

## The line-quality tool needs a GPU

The classify stage measures each line's perplexity with Qwen2.5-0.5B on CUDA. On a runner without a GPU it stops
with exit 1 (`[GPU Engine] FATAL: CUDA is NOT available`). The tool declares
`<resource type="cuda_device_count_min">1</resource>`, which Galaxy does not act on yet: route the tool to a
destination that gives the container a GPU (TPV: `gpus: 1` for `atrium_ocr_line_quality`; plain Docker:
`docker_run_extra_arguments: --gpus all`). DARIAH's test instance has none, so the tool is for an instance with GPUs, such as
`ssh.usegalaxy.eu`.

**The model.** *Download* (default) fetches `Qwen/Qwen2.5-0.5B` (about 1 GB) into the job's temporary directory.
*Staged* reads the copy that the data manager *ATRIUM Hugging Face models* put in the `atrium_hf_models` table, offline
(`HF_HUB_OFFLINE=1`); the destination must mount the data manager's data path into the container, read-only, as for
the page classifier's models.

## Network

The CPU tool needs none. The line-quality tool downloads Qwen2.5-0.5B from the Hugging Face Hub unless it is staged.
The fastText language-identification model is in the image.

## Tests

```bash
planemo lint ocr_postprocess.xml ocr_line_quality.xml
planemo test --docker --galaxy_branch v26.1.1 ocr_postprocess.xml
planemo test --docker --galaxy_branch v26.1.1 ocr_line_quality.xml   # a GPU destination only
```

*OCR post-processing*, five tests: an ALTO page with alto-tools (one page text, one ALTO page, the statistics); the
same page as text lines (the line table); a two-page CSV; OCR JSON; an XML file that is not ALTO (exit 1).

*OCR line quality*, one test: the ALTO page, its first line `Clear` and `1998` `Non-text`. It needs a GPU.

`test-data/` holds four of the tool's synthetic `data_samples/` (CC BY-NC 4.0, as `test-data/LICENSE` says) and
`not_alto.xml`, written for the error test.

## Licences

The code is MIT; Qwen2.5-0.5B is Apache-2.0; the fastText model is CC BY-NC 4.0, as the tool's `para_config.txt`
declares it. The paradata of each run lists the components and their licences.
