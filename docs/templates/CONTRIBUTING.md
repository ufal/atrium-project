# 🤝 Contributing to «Repository Display Name» (ATRIUM)

Welcome! Thank you for your interest in contributing. This repository [^repo] provides
«one-sentence statement of what the tool does and where it sits in the ATRIUM pipeline:
page-classification → alto-postprocess → nlp-enrich → translator».

This document describes the project's capabilities, development workflow, code
conventions, and rules for contributors. ATRIUM-wide conventions (branching, commit
types, the test/lint standard) are identical across all repositories; anything
repo-specific is called out explicitly.

## 📦 Release History

| Version     | Key Features & Fixes                                             | Release Type |
|-------------|-----------------------------------------------------------------|--------------|
| **vX.Y.Z**  | «headline change — one line»                                     | Pre-release  |
| …           | …                                                               | …            |

> **vX.Y.0 — «subsystem» (detail).** Use a block-quote immediately under the table to
> expand on a release that introduced non-trivial logic. State *what* changed, *why*, and
> *which tests cover it* (e.g. `tests/test_<module>.py`). Keep the table row to one line
> and put the depth here.

**Versioning rules (enforced by CI):** the `[tool] version` in `para_config.txt`,
`version:` in `CITATION.cff`, and the git tag MUST agree — `security.reusable.yml`
fails the build otherwise. The API service reports this same value (see Code
Conventions → *Single source of truth for the version*). Update `date-released:` in
`CITATION.cff` to the actual release date on every version bump.

---

## 🏗️ Project Contributions & Capabilities

«Describe the 2–4 major capabilities this tool contributes, cross-referencing
`README.md` rather than duplicating it. One subsection per capability.»

---

## 🌿 Branches & Environments

| Branch   | Environment          | Rule                                                                            |
|----------|----------------------|---------------------------------------------------------------------------------|
| `test`   | Staging              | Base for all development. Always branch from `test`.                            |
| `master` | Stable / Integration | Merged exclusively by a human reviewer. Do not open PRs directly into `master`. |

```text
test    ←  feature-<name>
test    ←  bugfix-<name>
master  ←  (humans only, after test stabilises)
```

### 🏷️ Branch Naming

| Type             | Pattern          | Example                   |
|------------------|------------------|---------------------------|
| New feature      | `feature-<name>` | `feature-amcr-validation` |
| Bug fix          | `bugfix-<name>`  | `bugfix-chunk-truncation` |
| Hotfix on master | `hotfix-<name>`  | `hotfix-api-timeout`      |

---

## 🔁 Contributor Workflow

1. **Create an issue** (or find an existing one) describing the problem or feature.
2. **Branch from `test`:**
   ```bash
   git checkout test && git pull origin test
   git checkout -b feature-<name>
   ```
3. **Implement** following the code conventions below.
4. **Run the fast checks** (see Testing) before every commit.
5. **Open a Pull Request** targeting `test`. Use a **Draft PR** while work is in progress.

---

## 📋 Pull Request Format

Every PR must include:

* **Issue link:** `Closes #<number>` or `Refs #<number>`
* **Motivation:** why the change is needed
* **Description of change:** what changed and how
* **Testing:** what was run, what passed, what could not be executed (and why)

**Do not open PRs into `master`** — merging into `master` is the maintainers' responsibility.

> **Issue tracking:** issues reference the commits/PRs that resolved them, not the other
> way around. Commit messages say *what changed*; the issue records *why*.

---

## ✏️ Commit Messages

Format: `[type] concise description of what changed`

| Type       | When to use                           |
|------------|---------------------------------------|
| `add`      | Added content (general)               |
| `edit`     | Edited existing content (general)     |
| `remove`   | Removed existing content (general)    |
| `fix`      | Bug fix                               |
| `refactor` | Refactoring without behaviour change  |
| `test`     | Adding or updating tests              |
| `docs`     | Documentation only                    |
| `chore`    | Build, dependencies, CI configuration |
| `style`    | Formatting, no logic change           |
| `perf`     | Performance optimisation              |

---

## 🧪 Code Conventions & Testing

### Code conventions
* **Comments:** short and informative; add one when the function name doesn't fully explain intent.
* **Argument types:** give every function argument a default type (`int`, `list`, …).
* **Console flags:** every new CLI flag ships with a `help=` message.
* **Config files:** when the set of config variables changes, reflect it in the repo docs.
* **Generated code:** always run and check it manually before pushing.

### Single source of truth for the version
The API service must report its version from `para_config.txt` (the value CI validates),
never a hard-coded string — this keeps `/info`, `CITATION.cff`, and releases from drifting:
```python
def _read_tool_version(default: str = "0.0.0") -> str:
    import configparser
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    for cand in (root / "para_config.txt", root / "setup" / "para_config.txt"):
        if cand.exists():
            cp = configparser.ConfigParser(); cp.read(cand, encoding="utf-8")
            v = cp.get("tool", "version", fallback=None)
            if v:
                return v[1:] if v.lower().startswith("v") else v
    return default
# FastAPI(title="…", version=_read_tool_version())
```

### Minimum checks before every commit
```bash
python -m compileall -q .                 # 1. compiles
pre-commit run --all-files                # 2. ruff (shared ruff.toml) + shellcheck
pytest -m "not slow" --tb=short           # 3. fast lane — no models, no GPU, no network
```

### Running the test suite
The fast lane requires **no ML models, GPU, or network** — those tests are marked
`@pytest.mark.slow` and excluded by default.
```bash
pip install -r requirements-test.txt                     # pytest>=8.0, pytest-cov only
pytest -m "not slow" --tb=short                          # before every commit
pytest -m "not slow" --cov=. --cov-report=term-missing   # with coverage
pytest --tb=short                                        # full suite (needs model setup)
```

**Shared, drop-in test files (keep byte-identical across repos):**
* `tests/test_paradata.py` — `ParadataLogger`, `_sanitise`
* `tests/test_para_licenses.py` — `resolve_effective_license`, `merge_effective_licenses`

**Rules:**
* Any test that loads a checkpoint, hits the network, or needs a GPU **must** be
  `@pytest.mark.slow`, and the PR must say which resource it needs.
* **Prefer in-process tests over `subprocess`.** Import the entrypoint
  (`from run import main`) and call `main([...])` so coverage is real. Reserve at most
  one thin `subprocess` smoke per entrypoint, marked `@pytest.mark.slow`.
* Fixtures are small, self-contained files under `tests/fixtures/`; never read
  `data_samples/` directly.

### Linting
Ruff is the ATRIUM standard (we migrated off black/isort/flake8). Run `ruff check .`
against the shared `ruff.toml` template before opening a PR.

---

## 🔗 Shared ("drop-in") code
`atrium_paradata.py` and `para_licenses.py` are **canonical** in
`ufal/atrium-project/docs/templates/shared/` and copied verbatim into each repo. Do not
fork their logic locally — edit the canonical copy, then re-sync. CI
(`paradata-drift.reusable.yml`) fails if a repo's copy diverges from canonical.

---

## 📁 Repository Documentation Management

| File              | Audience        | Responsibility                                 |
|-------------------|-----------------|------------------------------------------------|
| `README.md`       | GitHub visitors | Project overview, workflow stages, quick start |
| `CONTRIBUTING.md` | Developers      | Code conventions, branches, PRs, testing       |

Do not duplicate rules across files — cross-reference the canonical source.

---

## 📞 Contacts & Acknowledgements
Maintainer: **«email»** [^repo] · Developed by UFAL [^ufal] · Funded by ATRIUM [^atrium]

**©️ 2026 UFAL & ATRIUM**

[^repo]: https://github.com/ufal/«repo»
[^ufal]: https://ufal.mff.cuni.cz/home-page
[^atrium]: https://atrium-research.eu/
