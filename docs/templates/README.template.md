# «atrium-tool»: «one line: what it produces from what»

<!--
README skeleton for an ATRIUM tool repository (atrium-project#79). The rules are in
atrium-project/docs/documentation-style.md. Aim for 100-250 lines; link to deeper pages instead of
growing this one. Leave out a section that does not matter for this tool rather than filling it.
The H1 above feeds the hub's landing card (_generators/repos.py): keep it to the tool's name and one
plain clause. Write the opening for a reader who is not a programmer: an archivist or a project manager
should understand it. No issue numbers, release numbers or repository history above the last section.
Delete this comment.
-->

«Two or three short sentences, in words a non-specialist follows: the problem this tool solves, for whom,
and what the result is used for. Say when to use it and, if useful, when not to.»

[Release «vX.Y.Z»](«release link») · [«Licence»](LICENSE) · [ATRIUM documentation](https://ufal.github.io/atrium-project/)

## Inputs and outputs

| Input                       | Output                                   |
|-----------------------------|------------------------------------------|
| «formats, and their limits» | «what the reader gets back, in a phrase» |

«One sentence on the ATRIUM document record, if the tool reads or writes it, linking the hub's
[document contract](https://ufal.github.io/atrium-project/ecosystem/document-contract/). Field lists
belong in docs/reference/, not here.»

## Quick start

**What you need:** «Docker, or Python X.Y and a checkout»; «network access to … (model downloads on the
first start, LINDAT, an LLM backend), or none»; «a GPU, or not».

«The shortest path to a real result: the published image, or the CLI.»

```bash
docker run --rm -p 8000:8000 ghcr.io/ufal/atrium-«tool»-api:«X.Y.Z»
curl --fail-with-body -sS -X POST localhost:8000/«endpoint» -F "file=@«sample in this repo»"
```

Expected result (abridged):

```json
{«the few fields a reader should check»}
```

«What the reader should see, in one sentence, and what happens when an external service is missing.»

## Where it fits in ATRIUM

«One paragraph: the stage before and after this one, linking the hub's workflow page for this tool.»

## Limits and maturity

- **«The limit, in one short sentence.»** «What it means for the reader, and what to do.» ([detail](«link»))
- **«What is experimental or not evaluated.»** «Measured on what, if at all.» ([what was measured](docs/evaluation/))

## Documentation

| For                 | To                                      | Read                                           |
|---------------------|-----------------------------------------|------------------------------------------------|
| using it            | run it locally or call the API          | [docs/usage.md](docs/usage.md)                 |
|                     | look up outputs, formats and fields     | [docs/reference/](docs/reference/)             |
| running the service | deploy and operate it, read its errors  | [service/README.md](service/README.md)         |
|                     | see the API contract                    | [service/openapi.json](service/openapi.json)   |
|                     | set every option                        | [docs/configuration.md](docs/configuration.md) |
| judging the results | see what was measured, on which data    | [docs/evaluation/](docs/evaluation/)           |
| changing the code   | understand how it works                 | [docs/how-it-works.md](docs/how-it-works.md)   |
|                     | set up, test, release; find the history | [docs/development.md](docs/development.md)     |
|                     | follow the conventions                  | [CONTRIBUTING.md](CONTRIBUTING.md)             |

Terms used across the tools are explained in the
[ATRIUM glossary](https://ufal.github.io/atrium-project/glossary/). The documentation follows the ATRIUM
[documentation style](https://github.com/ufal/atrium-project/blob/main/docs/documentation-style.md).

## Licence, citation and acknowledgements

«The code licence; the licences of models and data it uses, linked to their inventory (`para_config.txt`);
how to cite (`CITATION.cff`). Acknowledgements name ATRIUM (GA 101132163), the LINDAT/CLARIAH-CZ research
infrastructure and the AIS CR infrastructure (LM2023031); keep both infrastructures named (#79). The exact
wording of the LINDAT/CLARIAH-CZ acknowledgement is agreed with its coordinator.»

«If the repository had another name: "Formerly `«old name»`; its history is in
[docs/development.md](docs/development.md)." One line.»
