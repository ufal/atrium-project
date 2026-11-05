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
| `atrium_translator`          | `ghcr.io/ufal/atrium-translator:1.7.6-beta`           | an ALTO page or an XML metadata record → translated XML, log, paradata, record          | LINDAT translation and UDPipe   |

Each wrapper runs the release's **batch** image, one command per job. Galaxy starts the container as `docker run …
IMAGE /bin/sh tool_script.sh`; both images' entry points run that script as given (page-classification since
`v1.10.5-beta`, the translator since `v1.7.6-beta`), so no destination needs an entry-point override. Both run on
CPU. The other four ATRIUM tools (ocr-postprocess, nlp-enrich, keyword-extract, digital-convert) need the same
entry-point change before they can be wrapped.

The workflows: page images, PDFs, XML records, and the scanned-pages chain *classify → keep the text pages →
Tesseract (IUC, on the instance) → translate*. Details: [workflows/README.md](workflows/README.md).

## Getting it onto the DARIAH instance

1. The translator's tag `v1.7.6-beta` is pushed and its images are published (its wrapper needs that image).
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

1. In the tool XML, set `@TOOL_VERSION@` to the release without its `v`, and `@VERSION_SUFFIX@` back to `0`; a
   change to the wrapper alone raises `@VERSION_SUFFIX@`.
2. Update `tool_version` of that tool's steps in `workflows/*.ga`, and the `CHANGELOG.md` there.
3. Run the checks above, then copy the folder to `DARIAH-ERIC/atrium-galaxy-tools`.
