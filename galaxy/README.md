# ATRIUM tools in Galaxy

Galaxy tool wrappers, a data manager and workflows for the ATRIUM tools ([#66](https://github.com/ufal/atrium-project/issues/66)).
The layout is that of [DARIAH-ERIC/atrium-galaxy-tools](https://github.com/DARIAH-ERIC/atrium-galaxy-tools), the
repository DARIAH's test Galaxy (<https://galaxy.acdh-dev.oeaw.ac.at/galaxy/>) installs from, so each folder copies
there unchanged. Galaxy is the sandbox for external users; the production chain stays Temporal-based.

```text
galaxy/
├── tools/atrium_page_classification/          page_classification.xml, test-data/, data-table samples
├── tools/atrium_translator/                   translator.xml, test-data/
├── data_managers/data_manager_atrium_page_models/   stages the classifier's models once per server
└── workflows/                                 four .ga workflows, their -tests.yml, README, CHANGELOG
```

## What is wrapped

| Tool                         | Image (batch)                                         | Inputs → outputs                                                                        | Network                         |
|------------------------------|-------------------------------------------------------|-----------------------------------------------------------------------------------------|---------------------------------|
| `atrium_page_classification` | `ghcr.io/ufal/atrium-page-classification:1.12.3-beta` | page images or a PDF → Top-N table, votes, paradata, document record(s), pages to route | Hugging Face Hub, unless staged |
| `atrium_translator`          | `ghcr.io/ufal/atrium-translator:1.7.8-beta`           | an ALTO page or an XML metadata record → translated XML, log, paradata, record          | LINDAT translation and UDPipe   |

Each wrapper runs the release's **batch** image, one command per job. Galaxy starts the container as `docker run …
IMAGE /bin/sh tool_script.sh`; both images' entry points run that script as given (page-classification since
`v1.10.5-beta`, the translator since `v1.7.8-beta`), so no destination needs an entry-point override. Both run on
CPU. The other four ATRIUM tools have the same entry point since their releases of 2026-11-06: [Ready to wrap](#ready-to-wrap).

The workflows: page images, PDFs, XML records, and the scanned-pages chain *classify → keep the text pages →
Tesseract (IUC, on the instance) → translate*. Details: [workflows/README.md](workflows/README.md).

## Ready to wrap

From these releases (prepared on 2026-11-06, tagged by the maintainer) the four batch images start through the
hub-canonical `container_entrypoint.py`, which runs Galaxy's job script as given; each image's own program is
named in its Dockerfile. Their Galaxy sheets on the documentation site's workflow pages list the datatypes,
container, network and test data.

| Tool            | Batch image (first release that runs a job script)       | What its wrapper has to handle                                                                                                                                                                                                                                                                                                                                        |
|-----------------|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ocr-postprocess | `ghcr.io/ufal/atrium-ocr-postprocess:1.15.4-beta`        | ALTO (`xml`) or a text-bearing file → line table (`csv`), page texts, record (`json`). The `classify` stage needs CUDA, so on CPU only split, stats and extract (`--skip-classify --skip-aggregate`), or `score_record.py` on records. The pipeline starts its stages by name from `/app`: the job script writes a config with absolute paths and runs it from `/app` |
| nlp-enrich      | `ghcr.io/ufal/atrium-nlp-enrich:1.3.4-beta`              | line tables (`csv`, `tabular`) with their ALTO → CoNLL-U (`tabular`: no `conllu` datatype on DARIAH), entities, TEITOK (`tei`), record. Paths come only from a config file, so the job script writes one; LINDAT UDPipe and NameTag over the network; Czech only                                                                                                      |
| keyword-extract | `ghcr.io/ufal/atrium-keyword-extract:1.6.5-beta`         | a folder of CoNLL-U, TEITOK, records, CSV or text → keyword tables, record. The statistical kind only: `yake` and `legacy` offline, `keybert` downloads its model (stage it, like the classifier's); `--workers ${GALAXY_SLOTS:-1}`; failed documents still exit 0                                                                                                    |
| digital-convert | `ghcr.io/ufal/atrium-digital-convert-digital:1.4.5-beta` | one PDF, DOCX or XLSX (ODT, ODS, RTF, DOC and XLS have no datatype on DARIAH) → record, Markdown. Light engine: no models, no network; exit 3 on an unsupported file or a PDF with an OCR layer, 4 on a broken one                                                                                                                                                    |

## Getting it onto the DARIAH instance

1. ~~The translator's tag `v1.7.8-beta` is pushed and its images are published~~: done 2026-11-06 (its wrapper needs that image).
2. Copy `tools/`, `data_managers/` and `workflows/` into `DARIAH-ERIC/atrium-galaxy-tools`; the instance picks
   up changes to that repository.
3. An administrator runs the data manager *ATRIUM page-classification models* and mounts its data path into the
   classifier's container (the tool's [README](tools/atrium_page_classification/README.md#model-weights)). Until
   then the classifier downloads its model in each job.
4. Import the workflows (*Workflows → Import*) and run them on the tools' `test-data/`.

## Checks

```bash
pip install planemo
planemo lint tools/atrium_page_classification/page_classification.xml tools/atrium_translator/translator.xml
planemo lint data_managers/data_manager_atrium_page_models/data_manager/atrium_page_models.xml
planemo workflow_lint --iwc workflows
planemo test --docker --galaxy_branch v26.1.1 tools/atrium_page_classification/page_classification.xml
planemo test --docker --galaxy_branch v26.1.1 tools/atrium_translator/translator.xml
```

The tool tests need Docker and the network above. `tests/test_galaxy_wrappers.py` (hub) checks that every
container tag is its wrapper's `@TOOL_VERSION@`, that the version is the release the tool repository declares, and
that each workflow step names a wrapper of this folder at its version, or a tool the DARIAH instance has.

## Moving to a new release

1. **The tool repository first, where you can.** Its `test` carries the release before the hub commit that pins
   it. `tests/test_galaxy_wrappers.py` reads the tool's release history at its `test` head: while the tool is still
   at an older version, the check is skipped with that reason (the hub often goes first, because the tools' pin
   sweep needs it on GitHub); once the tool is at the pinned version or later, its history must name it.
2. In the tool XML, set `@TOOL_VERSION@` to the release without its `v`, and `@VERSION_SUFFIX@` back to `0`; a
   change to the wrapper alone raises `@VERSION_SUFFIX@`.
3. Update `tool_version` of that tool's steps in `workflows/*.ga`, and the `CHANGELOG.md` there.
4. Run the checks above, then copy the folder to `DARIAH-ERIC/atrium-galaxy-tools`.
