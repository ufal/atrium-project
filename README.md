# ATRIUM Project

The planning and documentation hub of ÚFAL's tools for the ATRIUM project: the issues and the
[project board](https://github.com/orgs/ufal/projects/21), the documentation site, the code shared by
the tools, and the CI the tools call.

ATRIUM is an EU project (https://atrium-research.eu). Its goal (Advancing fronTier Research In the arts and
hUManities) is to bridge leading research infrastructures in arts and humanities (DARIAH), archaeology
(ARIADNE), language technologies (CLARIN) and open scholarly communication (OPERAS).

## The tools

Each tool is its own repository, release and service image:

| Repository                                                                       | What it does                                                         |
|----------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [atrium-page-classification](https://github.com/ufal/atrium-page-classification) | sorts scanned pages into content categories                          |
| [atrium-ocr-postprocess](https://github.com/ufal/atrium-ocr-postprocess)         | turns OCR output and text files into lines with language and quality |
| [atrium-digital-convert](https://github.com/ufal/atrium-digital-convert)         | converts born-digital files into the same record                     |
| [atrium-nlp-enrich](https://github.com/ufal/atrium-nlp-enrich)                   | adds morphology, named entities and the TEITOK layout                |
| [atrium-keyword-extract](https://github.com/ufal/atrium-keyword-extract)         | extracts keywords, statistically or from the AMČR vocabulary         |
| [atrium-translator](https://github.com/ufal/atrium-translator)                   | writes the English metadata                                          |

`atrium-ocr-postprocess` continues `atrium-alto-postprocess`; `atrium-keyword-extract` and
`atrium-digital-convert` continue `atrium-llm-enrich`. The old repositories have been archived (read-only)
since 2026-10-19.

## Documentation

| To                                                  | Read                                                                                                                                                     |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| see how the tools fit together, and each workflow   | the [documentation site](https://ufal.github.io/atrium-project/)                                                                                         |
| deploy the services and accept them on Kubernetes   | [docs/k8s_deployment.md](docs/k8s_deployment.md), [docs/k8s_acceptance_runbook.md](docs/k8s_acceptance_runbook.md)                                       |
| change code shared by the tools                     | [docs/shared_components.md](docs/shared_components.md)                                                                                                   |
| add or change a CI check                            | [docs/ci_policy.md](docs/ci_policy.md)                                                                                                                   |
| write or restructure a tool's documentation         | [docs/documentation-style.md](docs/documentation-style.md)                                                                                               |
| look up the record, paradata and RO-Crate contracts | [docs/document_schema.md](docs/document_schema.md), [docs/paradata_schema.md](docs/paradata_schema.md), [docs/rocrate_export.md](docs/rocrate_export.md) |
| see every hub document                              | [INDEX.md](INDEX.md)                                                                                                                                     |

Presentation of the project (March 2026): [Google Slides](https://docs.google.com/presentation/d/13Be8n7tgebw3GVEgJuB3m1FdnrfKvAGHWvYHA9X4Ma4/edit?usp=sharing) · [Zenodo](https://zenodo.org/records/19500212)
