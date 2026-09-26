---
title: Contributing standards
nav_order: 12
status: partial
round: 6
issue: 57
---

# Contributing standards

The family contribution standard — branch model, commit convention, pull-request format,
releases — read once, and then each repository's own conventions.

!!! info "Scope"
    The standard applies to all five tool repositories. The per-repository conventions below
    are page-classification's and the translator's.

!!! note "A template, filled in per repository"
    The hub keeps the standard as a template, `docs/templates/CONTRIBUTING.md`, with
    «placeholders» for each repository to fill. Unlike the shared code, it is not vendored:
    each repository's `CONTRIBUTING.md` is its own file, adapted to its code, and is the
    authority for that repository.

## The family standard

### Branches

| Branch  | Environment          | Rule                                                                                       |
|---------|----------------------|--------------------------------------------------------------------------------------------|
| `test`  | Staging              | The base for all development. Always branch from `test`, and open pull requests against it |
| default | Stable / integration | Merged only by a human reviewer. No pull requests directly into it                         |

The stable branch is the repository's default branch — `master` in the translator, `vit` in
page-classification, whose branch names follow its model families.

Branch names follow three patterns:

| Type                        | Pattern          |
|-----------------------------|------------------|
| New feature                 | `feature-<name>` |
| Bug fix                     | `bugfix-<name>`  |
| Hotfix on the stable branch | `hotfix-<name>`  |

### The workflow

1. Open an issue, or find the existing one.
2. Branch from `test`: `git checkout test && git pull origin test`, then `git checkout -b feature-<name>`.
3. Implement, following the repository's code conventions.
4. Run the fast checks before every commit.
5. Open a pull request against `test` — as a **Draft** while work is in progress.

### What a pull request contains

* **Issue link** — `Closes #<n>` or `Refs #<n>`
* **Motivation** — why the change is needed
* **Description of change** — what changed and how
* **Testing** — what was run, what passed, and what could not be run, and why

Issues reference the commits that resolved them, not the other way round: a commit message says
*what* changed; the issue records *why*.

### Commit messages

`[type] concise description of what changed`, with one of ten types:

| Type       | When                                      |
|------------|-------------------------------------------|
| `add`      | added content                             |
| `edit`     | edited existing content                   |
| `remove`   | removed existing content                  |
| `fix`      | a bug fix                                 |
| `refactor` | restructuring with no change in behaviour |
| `test`     | adding or updating tests                  |
| `docs`     | documentation only                        |
| `chore`    | build, dependencies, CI configuration     |
| `style`    | formatting, no logic change               |
| `perf`     | a performance improvement                 |

### Releases

There is no release branch. A release is a **`v*` tag**, and three version strings must agree
before it can publish: the tag, `CITATION.cff`'s `version`, and `para_config.txt`'s
`[tool] version`. The hub's `check_version.py` — vendored into every tool — enforces it in each
repository's release workflow, and `security.reusable.yml` checks it again. Cutting a release:

1. Bump `version` and `date-released` in `CITATION.cff`, and `[tool] version` in
   `para_config.txt`, to the same value.
2. Add the release to the *Release History* table in `CONTRIBUTING.md`.
3. Merge through `test` into the default branch.
4. Tag the merge commit `v<version>` and push the tag.
5. CI checks the three versions, builds the images, runs the release gate and — only if it
   passes — publishes `<version>` and `latest`. See [Operations](operations.md#the-release-gate).

### Shared code

The nineteen files listed in
[Architecture](ecosystem/architecture.md#what-is-canonical-and-what-is-vendored) are **never
edited in a tool repository**: CI fails on a single changed byte. A change to shared code is
made in the hub and copied out with `scripts/revendor_shared.sh`, and the tool repositories'
copies land together. Everything else in a tool repository is its own.

### Which document owns what

`README.md` is for visitors — overview, workflow, quick start; `CONTRIBUTING.md` is for
developers — conventions, branches, pull requests, testing, the release history. A rule lives in
one of them, and the other links to it.

## Per-repository conventions

=== "page-classification"

    | Topic                          | This repository                                                                                                    |
    |--------------------------------|--------------------------------------------------------------------------------------------------------------------|
    | Branch-name examples           | `feature-new-model`, `bugfix-truncated-image`, `hotfix-flags-priority`                                             |
    | Minimum checks before a commit | `python -m compileall -q .` then `ruff check .`                                                                    |
    | Test requirements              | `pip install -r setup/requirements-test.txt`                                                                       |
    | Fast / full / coverage         | `pytest -m "not slow" --tb=short` · `pytest --tb=short` · `pytest -m "not slow" --cov=. --cov-report=term-missing` |
    | Lint configuration             | `ruff.toml`: line length 120, `py311`, rules `E, F, W, I`, `E501` ignored                                          |
    | Pre-commit hooks               | whitespace and YAML checks, ruff (`--fix` + format), shellcheck for the data scripts                               |
    | Config file                    | `setup/para_config.txt` — not at the root                                                                          |

=== "translator"

    | Topic                          | This repository                                                            |
    |--------------------------------|----------------------------------------------------------------------------|
    | Branch-name examples           | `feature-amcr-validation`, `bugfix-chunk-truncation`, `hotfix-api-timeout` |
    | Minimum checks before a commit | `python -m compileall -q .` then `pre-commit run --all-files`              |
    | Test requirements              | `pip install -r requirements-test.txt`                                     |
    | Fast / full / coverage         | the same three commands                                                    |
    | Lint configuration             | `ruff.toml`: line length 120, `py311`, rules `E, F, W, I`, `E501` ignored  |
    | Pre-commit hooks               | whitespace and YAML checks, ruff (`--fix` + format)                        |
    | Config file                    | `para_config.txt` at the root                                              |

## What CI runs on a pull request

Every pull request against `test` runs the repository's caller workflows — the fast test lane
and a container smoke test (`docker.yml`), the service contract (`api-contract.yml`), byte
parity of the shared files (`para-drift.yml`), `pre-commit`, workflow lint, CodeQL and the
version check. [Architecture → The CI federation](ecosystem/architecture.md#the-ci-federation)
lists them. A pull request is ready for review when all of them are green.

## Contributing to this site

The site is built from `docs_site/` in the hub with MkDocs Material. A page:

* starts with front matter — `title`, `nav_order`, `status`, `issue`, and `repo` / `role` on
  a tool page — and is listed in `mkdocs.yml`'s `nav`;
* is **written**, not generated: it explains and connects, and leaves the full-length manual to
  the tool's own `README.md`;
* states lasting facts — what a tool is, how it works, how to use it — and keeps
  time-bound findings out of the page;
* ends with a `## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                         | What was taken from it              |
|----------------------------------------------------------------|-------------------------------------|
| `atrium-project/docs/templates/CONTRIBUTING.md`                | the family standard                 |
| `atrium-page-classification/CONTRIBUTING.md` @ `vit` `adee922` | its conventions and release history |
| `atrium-translator/CONTRIBUTING.md` @ `master` `71feaef`       | the same                            |
| each repository's `ruff.toml` and `.pre-commit-config.yaml`    | the lint and hook tables            |
| `atrium-project/mkdocs.yml`, `tools/docs/requirements.txt`     | the site conventions and build      |

Contact details are deliberately not reproduced here; each repository's own
*Contacts & Acknowledgements* section is the place to find them.
