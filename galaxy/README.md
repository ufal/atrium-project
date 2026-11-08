# ATRIUM tools in Galaxy

Galaxy tool wrappers, data managers and workflows for the six ATRIUM tools of ÚFAL
([#66](https://github.com/ufal/atrium-project/issues/66)). The layout is that of
[DARIAH-ERIC/atrium-galaxy-tools](https://github.com/DARIAH-ERIC/atrium-galaxy-tools), the repository DARIAH's test
Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>) installs from, so every folder copies there unchanged. Galaxy
is the sandbox for external users; the production chain stays Temporal-based.

```text
galaxy/
├── tools/atrium_page_classification/        page images or a PDF → page categories (CPU)
├── tools/atrium_translator/                 ALTO pages, XML records → translated XML (CPU, LINDAT)
├── tools/atrium_ocr_postprocess/            OCR output → line table, page texts (CPU); line quality (GPU)
├── tools/atrium_nlp_enrich/                 line table (+ ALTO) → CoNLL-U, entities, TEITOK (CPU, LINDAT)
├── tools/atrium_keyword_extract/            CoNLL-U, TEITOK, records, text → keywords (CPU)
├── tools/atrium_digital_convert/            PDF, DOCX, XLSX → document record, Markdown (CPU)
├── data_managers/data_manager_atrium_page_models/   stages the page classifier's models
├── data_managers/data_manager_atrium_hf_models/     stages KeyBERT's and the line classifier's models
└── workflows/atrium_ufal/                   six .ga workflows, their -tests.yml, README, CHANGELOG
```

## What is wrapped

Each wrapper runs a released **batch** image of its tool, one command per job, and calls the tool's program by its
absolute path, so it runs under Docker (`docker run IMAGE /bin/sh tool_script.sh`; every image's entry point runs
that script as given) and where the destination replaces the image's command (Kubernetes). No job writes into the
image: every path is in the job directory, so any user id works.

| Tool id                      | Image                                                     | Inputs → outputs                                                                         | Network                         | Compute |
|------------------------------|-----------------------------------------------------------|------------------------------------------------------------------------------------------|---------------------------------|---------|
| `atrium_page_classification` | `ghcr.io/ufal/atrium-page-classification:1.12.3-beta`     | page images or a PDF → Top-N table, votes, paradata, record(s), pages to route           | Hugging Face Hub, unless staged | CPU     |
| `atrium_translator`          | `ghcr.io/ufal/atrium-translator:1.7.8-beta`               | an ALTO page or an XML record → translated XML, log, paradata, record                    | LINDAT translation and UDPipe   | CPU     |
| `atrium_ocr_postprocess`     | `ghcr.io/ufal/atrium-ocr-postprocess:1.15.4-beta`         | ALTO, OCR JSON or a text-bearing file → line table, page texts, ALTO pages, stats, record | none                            | CPU     |
| `atrium_ocr_line_quality`    | `ghcr.io/ufal/atrium-ocr-postprocess:1.15.4-beta`         | the same → lines with Clear/Noisy/Trash/Non-text/Empty, categories per page              | Hugging Face Hub, unless staged | **GPU** |
| `atrium_nlp_enrich`          | `ghcr.io/ufal/atrium-nlp-enrich:1.3.4-beta`               | a line table (+ ALTO) → CoNLL-U, tokens, entities, TEITOK, record                        | LINDAT UDPipe and NameTag       | CPU     |
| `atrium_keyword_extract`     | `ghcr.io/ufal/atrium-keyword-extract:1.6.5-beta`          | many documents per job → keyword table, per document and page, records                   | KeyBERT only, unless staged     | CPU     |
| `atrium_digital_convert`     | `ghcr.io/ufal/atrium-digital-convert-digital:1.4.5-beta`  | a PDF, DOCX or XLSX → record (pages needing OCR flagged), Markdown                       | none                            | CPU     |

| Data manager                     | Image                                                 | Stages                                                                                         | Table                |
|----------------------------------|-------------------------------------------------------|------------------------------------------------------------------------------------------------|----------------------|
| `data_manager_atrium_page_models` | `ghcr.io/ufal/atrium-page-classification:1.12.3-beta` | the five revisions of `ufal/vit-historical-page` (about 2.5 GB)                                 | `atrium_page_models` |
| `data_manager_atrium_hf_models`   | `ghcr.io/ufal/atrium-keyword-extract:1.6.5-beta`      | `paraphrase-multilingual-MiniLM-L12-v2` (KeyBERT, 0.5 GB); `Qwen/Qwen2.5-0.5B` (line quality, 1 GB), pinned revisions | `atrium_hf_models`   |

Each tool folder has a README with its inputs, parameters, outputs, tests and licences. The workflows:
[workflows/atrium_ufal/README.md](workflows/atrium_ufal/README.md).

## Uploading to DARIAH-ERIC/atrium-galaxy-tools

1. **Copy the folders** into the repository, at the same paths: `tools/atrium_*`, `data_managers/data_manager_atrium_*`
   and `workflows/atrium_ufal`. Nothing of DARIAH's own is replaced. (The archive attached to #66 holds exactly these,
   plus the updated `tools/atrium_tools.xml` of step 2.)
2. **List the tools** in the toolbox, `tools/atrium_tools.xml`, in the ATRIUM section:

   ```xml
   <tool file="/local_tools/atrium_page_classification/page_classification.xml" />
   <tool file="/local_tools/atrium_translator/translator.xml" />
   <tool file="/local_tools/atrium_ocr_postprocess/ocr_postprocess.xml" />
   <tool file="/local_tools/atrium_ocr_postprocess/ocr_line_quality.xml" />
   <tool file="/local_tools/atrium_nlp_enrich/nlp_enrich.xml" />
   <tool file="/local_tools/atrium_keyword_extract/keyword_extract.xml" />
   <tool file="/local_tools/atrium_digital_convert/digital_convert.xml" />
   ```

   Leave `atrium_ocr_line_quality` out on an instance without GPUs.
3. **Register the data managers** as the spaCy one is: their `data_manager_conf.xml` in Galaxy's
   `data_manager_config_file`, and their `tool_data_table_conf.xml` in `tool_data_table_config_path` (both take a
   comma-separated list):
   `/local_data_managers/data_manager_atrium_page_models/…` and `/local_data_managers/data_manager_atrium_hf_models/…`.
4. **Check the job destinations:**
   - **Containers.** Every wrapper declares its image with `<container type="docker">`. The destination that runs
     these tool ids must use it (Docker, or Kubernetes with containers), not the shared `atrium-runtime` image of
     DARIAH's own tools.
   - **Network.** `lindat.mff.cuni.cz` for the translator and NLP enrichment; `huggingface.co` (and its download CDN)
     for the *Download* modes and the data managers.
   - **Staged models.** The data managers' data path (`galaxy_data_manager_data_path`) must be readable inside the job
     containers: for Docker, `docker_volumes: $galaxy_data_manager_data_path:ro`; on Kubernetes, the volume it lies
     on mounted in the job pods.
   - **GPU.** Only `atrium_ocr_line_quality` (it declares `cuda_device_count_min` 1, which Galaxy does not act on yet:
     route it to a GPU destination, for example with TPV's `gpus: 1`).
5. **Stage the models** (optional, but each job downloads them otherwise): run *ATRIUM page-classification models*
   (all five revisions) and *ATRIUM Hugging Face models* (*paraphrase-multilingual-MiniLM-L12-v2*; *Qwen2.5-0.5B* on an
   instance with GPUs). Then set the tools' *Model weights* to *Staged*.
6. **Import the workflows** (*Workflows → Import*) and run them on the tools' `test-data/`.

## Checks

```bash
pip install planemo
planemo lint tools/atrium_*/*.xml data_managers/data_manager_atrium_*/data_manager/*.xml   # macros.xml is linted through the tools
planemo workflow_lint --iwc workflows/atrium_ufal
planemo test --docker --galaxy_branch v26.1.1 tools/atrium_digital_convert/digital_convert.xml
```

`planemo test` runs a tool's tests in its image; each tool README says what its tests need (Docker, LINDAT, the Hub,
a GPU for line quality). `tests/test_galaxy_wrappers.py` (hub) checks that every container tag is its wrapper's
`@TOOL_VERSION@`, that the version is a release of the tool repository, that each data manager runs its tool's
release, that tool and data manager declare their tables alike, that every tool is in the toolbox list above, and
that each workflow step names a wrapper of this folder at its version, or a tool the DARIAH instance has.

**Checked before the hand-off (2026-11-07).** `planemo lint` and `planemo workflow_lint --iwc` pass (the ToolShed
lookup of Tesseract's newest version aside). Every test of the four new tools ran as Galaxy runs it: the command and
config files rendered from the wrapper, `/bin/sh tool_script.sh` in a job directory as an unprivileged user, against
the tools' released code at `/app` (read-only), with Galaxy's own output assertions; NLP enrichment against a
stand-in for LINDAT. Not run here: the images themselves (ghcr.io's blobs are blocked in our build container), the
Hugging Face downloads, KeyBERT and the GPU tool. The first `planemo test` with the images is the instance's.

## Moving to a new release

1. **The tool repository first, where you can.** Its `test` carries the release before the hub commit that pins
   it. `tests/test_galaxy_wrappers.py` reads the tool's release history at its `test` head: while the tool is still
   at an older version, the check is skipped with that reason; once the tool is at the pinned version or later, its
   history must name it.
2. In the tool XML (or `macros.xml`), set `@TOOL_VERSION@` to the release without its `v`, and `@VERSION_SUFFIX@` back
   to `0`; a change to the wrapper alone raises `@VERSION_SUFFIX@`. A data manager runs the same release as its tool.
3. Update `tool_version` of that tool's steps in `workflows/atrium_ufal/*.ga`, their `release`, and the `CHANGELOG.md`
   there.
4. Run the checks above, then copy the folder to `DARIAH-ERIC/atrium-galaxy-tools`.
