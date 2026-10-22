# «atrium-tool»: «one line: what it produces from what»

<!--
README skeleton for an ATRIUM tool repository (atrium-project#79). The rules are in
atrium-project/docs/documentation-style.md. Aim for 100-250 lines; link to deeper pages instead of
growing this one. Leave out a section that does not matter for this tool rather than filling it.
The H1 above feeds the hub's landing card (_generators/repos.py): keep it to the tool's name and one
plain clause. Delete this comment.
-->

«Two or three sentences: the problem this tool solves, for whom, and what the result is used for.
Say when to use it and, if useful, when not to.»

[Release «vX.Y.Z»](«release link») · [«Licence»](LICENSE) · [ATRIUM documentation](https://ufal.github.io/atrium-project/)

## Inputs and outputs

| Input                       | Output                                   |
|-----------------------------|------------------------------------------|
| «formats, and their limits» | «the record fields or files it writes»   |

«One sentence on the ATRIUM document record, if the tool reads or writes it, linking the hub's
[document contract](https://ufal.github.io/atrium-project/ecosystem/document-contract/).»

## Quick start

«The shortest path to a real result: the published image, or the CLI.»

```bash
docker run --rm -p 8000:8000 ghcr.io/ufal/atrium-«tool»-api:«X.Y.Z»
curl --fail-with-body -sS -X POST localhost:8000/«endpoint» -F "file=@«sample in this repo»"
```

Expected result (abridged):

```json
{«the few fields a reader should check»}
```

«Name any external service the example calls (LINDAT, an LLM backend) and what happens without it.»

## Where it fits in ATRIUM

«One paragraph: the stage before and after this one, linking the hub's workflow page for this tool.»

## Limits and maturity

- «A limit a user meets, stated plainly, linked to its detail.»
- «What is experimental or not evaluated.»

## Documentation

| To                                      | Read                                               |
|-----------------------------------------|----------------------------------------------------|
| run it locally or call the API          | [docs/usage.md](docs/usage.md)                     |
| deploy and operate the service          | [service/README.md](service/README.md)             |
| see the API contract                    | [service/openapi.json](service/openapi.json)       |
| set every option                        | [docs/configuration.md](docs/configuration.md)     |
| understand how it works                 | [docs/how-it-works.md](docs/how-it-works.md)       |
| look up rules, formats and fields       | [docs/reference/](docs/reference/)                 |
| see what was measured                   | [docs/evaluation/](docs/evaluation/)               |
| contribute, test, release               | [CONTRIBUTING.md](CONTRIBUTING.md)                 |

The documentation follows the ATRIUM
[documentation style](https://github.com/ufal/atrium-project/blob/main/docs/documentation-style.md).

## Licence, citation and acknowledgements

«The code licence; the licences of models and data it uses, linked to their inventory (`para_config.txt`);
how to cite (`CITATION.cff`). Acknowledgements name ATRIUM (GA 101132163), the LINDAT/CLARIAH-CZ research
infrastructure and the AIS CR infrastructure (LM2023031); keep both infrastructures named (#79). The exact
wording of the LINDAT/CLARIAH-CZ acknowledgement is agreed with its coordinator.»
