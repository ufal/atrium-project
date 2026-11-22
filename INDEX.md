# Index of the hub's documents

Every Markdown document in `atrium-project`, by where it lives, with one line on what it answers. The published
site is built from `docs_site/`; everything else is read in the repository. The maintainers' working records in
`agent_dev_logs/` are not listed: [Development history](docs_site/development-history.md#the-working-records)
describes them.

## At the root

| Document                           | What it answers                                                                              |
|------------------------------------|----------------------------------------------------------------------------------------------|
| [README.md](README.md)             | what the hub is, the seven repositories, and where to read next                              |
| [INDEX.md](INDEX.md)               | this list                                                                                    |
| [PAGES_SETUP.md](PAGES_SETUP.md)   | how the hub's site and the tools' landing cards are built and published                      |

## The published site, `docs_site/`

| Page                                                                       | What it answers                                                                        |
|----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [index.md](docs_site/index.md)                                             | what the tools do, how they work together, where each reader starts                    |
| [for-archives.md](docs_site/for-archives.md)                               | what happens to an archive's documents, what comes back, what leaves the institution   |
| [status.md](docs_site/status.md)                                           | what each tool is ready for, the pilot's timeline, what is open or parked              |
| [pilot.md](docs_site/pilot.md)                                             | the production pilot: the services, their runbooks, the limits met first, the contacts |
| [pipelines.md](docs_site/pipelines.md)                                     | the route through the pipeline, what passes between the stages, the workflows W1–W13   |
| [workflows/](docs_site/workflows/index.md)                                 | one page per tool: its purpose, steps, licences and place on the route                 |
| [ecosystem/architecture.md](docs_site/ecosystem/architecture.md)           | the hub and the tools, the shared code, the CI federation                              |
| [ecosystem/repository-map.md](docs_site/ecosystem/repository-map.md)       | which repository owns what                                                             |
| [ecosystem/document-contract.md](docs_site/ecosystem/document-contract.md) | the ATRIUM record, field by field and owner by owner                                   |
| [ecosystem/licences.md](docs_site/ecosystem/licences.md)                   | paradata, components and their licences, the rights in an output                       |
| [contracts/schemas.md](docs_site/contracts/schemas.md)                     | the schema files and their versions                                                    |
| [contracts/skos.md](docs_site/contracts/skos.md)                           | the controlled vocabulary and its SKOS form                                            |
| [contracts/rocrate.md](docs_site/contracts/rocrate.md)                     | RO-Crate export and the paradata of a run                                              |
| [agent-skills.md](docs_site/agent-skills.md)                               | the six agent skills and how to install one                                            |
| [operations.md](docs_site/operations.md)                                   | images and tags, the release gate, the container checks, Kubernetes                    |
| [contributing-standards.md](docs_site/contributing-standards.md)           | the working agreement, branches, pull requests, releases                               |
| [development-history.md](docs_site/development-history.md)                 | the chronology, the per-repository histories, the decision records                     |
| [glossary.md](docs_site/glossary.md)                                       | the terms the pages use                                                                |
| [external-tools.md](docs_site/external-tools.md)                           | the standards, models, services and institutions the tools depend on                   |
| `tools/page-classification/*`, `tools/translator/*`                        | ten short pages that point old addresses to the tools' own documentation               |

## The hub's references, `docs/`

| Document                                                                              | What it answers                                                                               |
|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [documentation-style.md](docs/documentation-style.md)                                 | how the documentation of all seven repositories is written and checked                        |
| [ci_policy.md](docs/ci_policy.md)                                                     | when CI runs, what each check proves, how a check is added                                    |
| [docker_gha.md](docs/docker_gha.md)                                                   | the Docker and GitHub Actions workflows, images and probes                                    |
| [release_trust.md](docs/release_trust.md)                                             | tags, rulesets and pins, and how a release is tagged                                          |
| [shared_components.md](docs/shared_components.md)                                     | who owns each shared file, and how a consumer adopts a change                                 |
| [document_schema.md](docs/document_schema.md)                                         | the record schema 2.0, reading 1.x records, the freeze of `doc-schema-v1`                     |
| [paradata_schema.md](docs/paradata_schema.md)                                         | the paradata schema 3.0                                                                       |
| [rocrate_export.md](docs/rocrate_export.md)                                           | the RO-Crate export and one run's `CreateAction`                                              |
| [skos_strategy.md](docs/skos_strategy.md)                                             | the SKOS registry of the ATRIUM vocabulary                                                    |
| [agent_skill_strategy.md](docs/agent_skill_strategy.md)                               | the service contract every tool meets, and the rules for skill branches                       |
| [k8s_deployment.md](docs/k8s_deployment.md)                                           | the reference Kubernetes manifest, its settings and known limits                              |
| [k8s_acceptance_runbook.md](docs/k8s_acceptance_runbook.md)                           | the acceptance of the six services on a receiving cluster                                     |
| [skill_acceptance_runbook.md](docs/skill_acceptance_runbook.md)                       | the acceptance of the six skill branches                                                      |
| [proposals/rights-and-policy.md](docs/proposals/rights-and-policy.md)                 | the closed proposal on run evidence, processing policy and output rights, and what came of it |
| [evaluation/du-benchmarks-and-models.md](docs/evaluation/du-benchmarks-and-models.md) | the research note on document-understanding benchmarks and models, for #22 after the pilot    |
| [docker_gha_roadmap.md](docs/docker_gha_roadmap.md)                                   | the closed Docker and CI plan of August to October 2026, kept as history                      |
| `arub-p_contacts.md`                                                                  | partner contacts, internal                                                                    |

## Decision records, `docs/decisions/`

Dated: why the hub is built the way it is. [The list](docs/decisions/README.md) says what each record covers:
the CI workflows, the end-to-end lanes, the release-trust log, the record schema's changelog, the agent skills,
the site's rounds, the publishing setup and the repository review of July 2026.

## Templates, `docs/templates/`

| Document                                                                          | What it is                                                   |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------|
| [CONTRIBUTING.md](docs/templates/CONTRIBUTING.md)                                 | the contribution standard each tool fills in                 |
| [README.template.md](docs/templates/README.template.md)                           | the shape of a tool README                                   |
| [skill/README.md](docs/templates/skill/README.md)                                 | the skill templates, and how to use them                     |
| [skill/SKILL.template.md](docs/templates/skill/SKILL.template.md)                 | the `SKILL.md` of a skill branch                             |
| [skill/serviceREADME.template.md](docs/templates/skill/serviceREADME.template.md) | the service runbook every tool's `service/README.md` follows |

## Elsewhere

| Document                                                                         | What it answers                                                                        |
|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [fixtures/e2e/README.md](fixtures/e2e/README.md)                                 | the fixtures of the end-to-end lanes                                                   |
| [galaxy/README.md](galaxy/README.md)                                             | the Galaxy wrappers handed to DARIAH; further Galaxy work is parked                    |
| `galaxy/tools/atrium_*/README.md`                                                | one per wrapped tool                                                                   |
| [galaxy/workflows/atrium_ufal/README.md](galaxy/workflows/atrium_ufal/README.md) | the Galaxy workflows, and their [changelog](galaxy/workflows/atrium_ufal/CHANGELOG.md) |
