---
title: Contributing standards
nav_order: 12
status: partial
round: 4
issue: 57
---

# Contributing standards

The family contribution standard — branch model, commit convention, pull-request format — read
once, and then where each repository actually deviates from it.

!!! info "Compared so far: page-classification and translator"
    The standard applies to all five tool repositories. The per-repository comparison below covers
    the two documented so far.

!!! warning "The standard is a skeleton, not a shared file"
    The hub keeps a template at `docs/templates/CONTRIBUTING.md`, with «placeholders» for each
    repository to fill. It is **not vendored**: it is not in `MANIFEST.json`, `revendor_shared.sh`
    does not copy it, and `para-drift` does not check it. Each repository's `CONTRIBUTING.md` is its
    own file, and they have drifted — which is why this page compares them instead of assuming them.

## The family standard

### Branches

| Branch   | Environment          | Rule                                                                                       |
|----------|----------------------|--------------------------------------------------------------------------------------------|
| `test`   | Staging              | The base for all development. Always branch from `test`, and open pull requests against it |
| `master` | Stable / integration | Merged only by a human reviewer. No pull requests directly into `master`                   |

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

This table is **byte-identical** in the skeleton and in both documented repositories.

### Releases

There is no release branch. A release is a **`v*` tag**, and three version strings must agree
before it can publish: the tag, `CITATION.cff`'s `version`, and `para_config.txt`'s
`[tool] version`. The hub's `check_version.py` — vendored into every tool — enforces it in each
repository's release workflow, and `security.reusable.yml` checks it again. So a release is cut by
bumping two files and tagging, never by hand-editing one.

## What the two repositories share, exactly

Comparing each `##` section of the two `CONTRIBUTING.md` files byte for byte:

| Section                                          | page-classification vs translator               |
|--------------------------------------------------|-------------------------------------------------|
| Contributor Workflow                             | **identical**                                   |
| Pull Request Format                              | **identical**                                   |
| Commit Messages                                  | **identical**                                   |
| Repository Documentation Management              | **identical**                                   |
| Branches & Environments                          | identical except the three branch-name examples |
| Code Conventions & Testing                       | differs — see below                             |
| Release History, Project Contributions, Contacts | repository-specific by design                   |

The four identical sections are themselves *not* identical to the skeleton — the wording differs
in small ways (a one-line `git` command, a separate Draft-PR line, a shorter issue-tracking note) —
so the skeleton states the family's intent, and these two files are close, unenforced copies of it.

Both repositories answer "who owns which document?" the same way, and it is worth following:
`README.md` is for visitors — overview, workflow, quick start; `CONTRIBUTING.md` is for
developers — conventions, branches, pull requests, testing. A rule lives in one of them, and the
other links to it.

## Where each repository deviates

=== "page-classification"

    | Topic                          | This repository                                                                                                    |
    |--------------------------------|--------------------------------------------------------------------------------------------------------------------|
    | Branch-name examples           | `feature-new-model`, `bugfix-truncated-image`, `hotfix-flags-priority`                                             |
    | Minimum checks before a commit | `python -m compileall -q .` then `ruff check .` — no `pre-commit` step                                             |
    | Test requirements              | `pip install -r setup/requirements-test.txt`                                                                       |
    | Fast / full / coverage         | `pytest -m "not slow" --tb=short` · `pytest --tb=short` · `pytest -m "not slow" --cov=. --cov-report=term-missing` |
    | Lint configuration             | `ruff.toml`: line length 120, `py311`, rules `E, F, W, I`, `E501` ignored                                          |
    | Pre-commit hooks               | pre-commit-hooks v6.0.0, ruff v0.15.18 (`--fix` + format), shellcheck v0.11.0                                      |
    | Config file                    | `setup/para_config.txt` — not at the root                                                                          |

=== "translator"

    | Topic                          | This repository                                                                                                                                |
    |--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
    | Branch-name examples           | `feature-amcr-validation`, `bugfix-chunk-truncation`, `hotfix-api-timeout` — the skeleton's own examples, which were evidently taken from here |
    | Minimum checks before a commit | `python -m compileall -q .` then `pre-commit run --all-files`                                                                                  |
    | Test requirements              | `pip install -r requirements-test.txt`                                                                                                         |
    | Fast / full / coverage         | the same three commands                                                                                                                        |
    | Lint configuration             | `ruff.toml`: line length 120, `py311`, rules `E, F, W, I`, `E501` ignored, no import-sorting block                                             |
    | Pre-commit hooks               | pre-commit-hooks v6.0.0, ruff v0.15.18 (`--fix` + format) — no shellcheck                                                                      |
    | Config file                    | `para_config.txt` at the root                                                                                                                  |

## Contradictions a contributor will hit

Each is quoted from the file at its default branch and recorded here, not fixed here — the
`CONTRIBUTING.md` files belong to their repositories.

**page-classification**

* **The branch model describes a repository that no longer exists.** `CONTRIBUTING.md` says to
  branch from `test` and that `master` is the stable branch. The default branch is **`vit`**,
  `test` currently equals `vit`, and `master` has not moved since 2026-06-26 — it still holds an
  older `vit/…` subdirectory layout. The README, meanwhile, tells users to check out `vit` or
  `clip`, which it treats as model-family lines. Someone who clones the default branch and follows
  `CONTRIBUTING.md` receives instructions that do not match what they cloned.
* A reference to "the recommended default (`main` branch)" means the **Hugging Face model
  revision** `main`, not a git branch — the repository has no `main` branch.

**translator**

* The **release-history table's column headers are swapped**: the header reads
  *Version · Release Type · Key Features & Fixes*, while every row is *version · features · type*.
* The "minimum checks" comment says pre-commit "runs black, isort, flake8, etc."; the configured
  hooks are whitespace and YAML checks plus ruff. The move to ruff is described two sections later.
* A footnote points at **`ARUP-CAS/atrium-translator`**; the repository is `ufal/atrium-translator`.
* `CONTRIBUTING.md` records alternative or locally hosted translation backends as "**not** in scope
  … a planned direction", while the README advertises a pluggable architecture with LLM and
  CTranslate2 backends. The code sides with the README — see
  [translator → Overview](tools/translator/index.md).

**Both**

* Both files call `tests/test_paradata.py` "shared across all repos". It is **not** one of the 17
  shared files, and the two copies differ from line 23 onward.
* Neither has the skeleton's *Shared ("drop-in") code* section, so neither tells a contributor that
  17 files must not be edited locally. [Architecture](ecosystem/architecture.md#what-is-canonical-and-what-is-vendored)
  is the place that says it.

**The skeleton itself**

The template that new copies would be made from has defects of its own: its one-line pipeline
order puts nlp-enrich before the translator and leaves out llm-enrich; it names 2 shared files
where there are 17; and it refers to `paradata-drift.reusable.yml` and `docs/paradata-schema.md`,
neither of which exists — the real names are `para-drift.reusable.yml` and
`docs/paradata_schema.md`.

## Sources

This table records **provenance**: what this page was written from, not a build instruction.

| Source                                                         | What was taken from it                             |
|----------------------------------------------------------------|----------------------------------------------------|
| `atrium-project/docs/templates/CONTRIBUTING.md`                | the family standard, and its defects               |
| `atrium-page-classification/CONTRIBUTING.md` @ `vit` `8c98a3d` | its sections, compared by hash, and its deviations |
| `atrium-translator/CONTRIBUTING.md` @ `master` `88242fe`       | the same                                           |
| each repository's `ruff.toml` and `.pre-commit-config.yaml`    | the lint and hook tables                           |
| `git ls-remote` on both repositories, 2026-09-22               | the branch facts                                   |
| `tests/test_paradata.py` in both repositories                  | byte comparison                                    |

Contact details are deliberately not reproduced here; each repository's own
*Contacts & Acknowledgements* section is the place to find them.
