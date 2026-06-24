# 🧭 ATRIUM Ecosystem — Repository Review & Forward Strategy

_Maintainer: lutsai.k@gmail.com · Last reviewed: 2026-06-24_
_Repos: atrium-project (hub) · atrium-page-classification · atrium-alto-postprocess ·
atrium-nlp-enrich · atrium-translator_

## 🧭 1. Scope & method
This document is the single hub-level record of (a) the ecosystem's architecture, (b) the
standing cross-repo workstreams, and (c) the phased roadmap. Findings below were verified
against the live `test` branches (HEADs newer than earlier review baselines), not against
stale snapshots. Each open item carries a `repo:file:line` pointer.

## 🏗️ 2. Ecosystem architecture (as-built)
Five repositories, **not** a monorepo and **not** git-submodules:

```
atrium-project (hub)
  ├─ docs/templates/         ruff.toml, .pre-commit-config, CONTRIBUTING, shared/*
  └─ .github/workflows/*.reusable.yml   ← called by every tool repo via `@test`
Pipeline data flow (container images over a shared volume):
  page-classification → alto-postprocess → nlp-enrich → translator
```

* **CI is genuinely centralised.** Every tool repo calls the hub's reusable workflows
  (`security.reusable.yml`, lint, tests) pinned `@test`. This is the real, working
  federation point.
* **Shared *code* is NOT centralised.** `atrium_paradata.py` and `para_licenses.py` are
  **copy-pasted** into each repo and have **diverged** (see §5.H). There is no
  `.gitmodules`; the "submodule core" described in earlier notes does not exist.

**Decision (this review): adopt a "canonical drop-in + CI drift-check" model** — the hub
holds the canonical copies under `docs/templates/shared/`; a reusable drift-check workflow
fails any repo whose copy diverges. Real packaging (`atrium-core` on an index) is recorded
as a *future* option, not adopted now (keeps the zero-install, copy-paste ergonomics the
repos already rely on).

## 🔄 3. Baseline reconciliation
The tool branches advanced past the prior review baselines (mostly Dependabot bumps plus
targeted fixes), so several earlier findings are already closed — notably nlp Shellcheck
(now 0 findings on shellcheck 0.9.0 **and** 0.10.0) and nlp test-requirements. Verified
green ecosystem-wide today: **`compileall` OK** and **`ruff check` (shared config) → "All
checks passed!"** in all four tool repos.

## 📊 4. Status matrix (open items only)

| ID | Item                                                          | pc            | translator | alto        | nlp     |
|----|---------------------------------------------------------------|---------------|------------|-------------|---------|
| F1 | API `/info` version hard-coded, drifts from `para_config.txt` | ✗             | ✗          | ✗ (missing) | ✗       |
| F2 | `CITATION.cff` `date-released` stale (`2026-03-02`)           | ok            | ✗          | ✗           | ok      |
| G1 | Eager heavy imports break the no-model fast lane              | ✗             | ok         | ok          | ✗       |
| G2 | `requirements-test.txt` not at repo root                      | `setup/` only | ok         | ok          | ok      |
| H1 | `para_licenses.py` dedup logic diverged; **0 tests**          | ✗             | ✗          | ✓ blueprint | ✗       |
| H2 | `atrium_paradata.py` 4 diverged copies                        | ✗             | ✗          | ✗           | ✗       |
| I1 | `subprocess` CLI-smoke tests instead of in-process            | 1 file        | none       | 2 files     | 2 files |

Legend: ✗ open · ok already fine · ✓ source-of-truth to propagate.

## 🧩 5. Workstreams

### 🏷️ F — Release & version hygiene
* **F1:** Replace hard-coded API versions with `_read_tool_version()` reading
  `para_config.txt [tool] version` (the value `security.reusable.yml` already validates
  against `CITATION.cff` and the tag). Locations:
  `pc:service/api.py:39` (`1.4.0-beta`), `translator:service/api.py:47` (`0.6.2`),
  `nlp:service/api.py:59` (`0.11.0`), `alto:service/text_api.py:43` (no `version=` at all).
* **F2:** Set `date-released` to each tag's real date —
  `translator:CITATION.cff` and `alto:CITATION.cff` (both `2026-03-02`, versions 0.7.0 /
  0.19.2).

### 📦 G — Dependency isolation (fast lane)
* **G1 (pc, nlp):** `pc:run.py` and `pc:classifier.py:9` import `torch/pandas/sklearn` at
  module top; `nlp:tests/test_llm_utils.py` cannot collect because `llm_utils` builds a
  `torch.bfloat16` registry at import. Fix: lazy-load heavy deps inside the functions that
  use them; where a torch-free import is impractical, gate the test with
  `pytest.importorskip("torch")`.
* **G2 (pc):** add a root `requirements-test.txt` mirroring `setup/requirements-test.txt`.

### 🔗 H — Shared-code provenance
* **H1:** alto's `merge_effective_licenses` (`alto:para_licenses.py:167-188`) **dedups**
  the component union on `(name, license)` before resolving; pc/translator/nlp use the
  naive union (double-counts a component used in multiple stages). Propagate alto's version
  to all repos and add the shared `tests/test_para_licenses.py` (currently **zero**
  coverage of the license engine anywhere).
* **H2:** the four `atrium_paradata.py` copies differ (382/382/478/469 lines). Lift the
  superset into the hub canonical copy, re-sync all repos, and enforce with the drift-check
  (§8). No risky in-place merge of repo-specific logic this round.

### 🧪 I — Test quality (real coverage)
Replace `subprocess.run([...,"--help"])` CLI-smoke tests with in-process
`main([...])`/parser calls so the entrypoint actually counts toward coverage. Targets and
exact refactors are in `docs/refactors/subprocess-to-inprocess.md` (Part C of the review
delivery). Leave alone the two nlp tests that *mock* `subprocess.run`
(`test_api_service.py`, `test_flexiconv_convert.py`) — those are already correct in-process
tests.

## 🗂️ 6. Per-repository diagnostics
* **page-classification** — close F1, G1, G2, H1, I1; biggest single item is extracting
  `build_parser()`/`main(argv)` from the `run.py` `__main__` block (enables both G1 and I1).
  Confirm `img2jpeg_v3.py` stays README-referenced.
* **translator** — strongest repo (lazy fasttext, vocabulary tested, no subprocess tests).
  Close F1, F2, H1. Next: LLM-backend parity tests (issue #4).
* **alto-postprocess** — the `para_licenses` blueprint; export it to the hub. Close F1
  (add `version=` to `text_api.py`), F2, I1 (2 files). Keep the `PERPLEXITY_THRESHOLD_MAX`
  Qwen guard (advisory, not a bug).
* **nlp-enrich** — Shellcheck already green. Flip ruff pre-commit to advisory
  (`--fix`, drop `--exit-non-zero-on-fix`) to match the other repos; G1 test guard; H1;
  I1 (the subprocess twin in `test_cli.py` is redundant with the existing in-process test).

## 🛣️ 7. Phased roadmap
* **Phase 0 — hygiene (mechanical):** F1, F2, nlp ruff advisory. Low risk.
* **Phase 1 — dependency isolation:** G1, G2. Restores an honest fast lane.
* **Phase 2 — provenance & coverage:** H1 (+ shared resolver tests), H2 convergence, I1.
* **Phase 3 — orchestration & gates:** pipeline compose scaffold (§8), drift-check
  workflow, and **ratchet ruff to blocking in all 4 repos** (safe: all currently at 0
  findings) + set `fail_under` to each repo's measured fast-lane coverage.
* **Phase 4 — blocked (documented, not actioned):** gitleaks secret-scan (needs
  ARUB/ARUP policy sign-off); GPU-runner workflows (needs self-hosted `[self-hosted,gpu]`).

## 🔁 8. Cross-service orchestration (Issue #18)
`atrium-project/compose/docker-compose.pipeline.yml` chains the published GHCR images
pc → alto → nlp → translator over a shared `atrium_data` volume, each stage gated on the
previous completing successfully (`depends_on: condition: service_completed_successfully`).
Plus `compose/README.md` documenting the `/data` stage contract, image tags, and a GPU
override. Scaffold — per-tool CLI flags to be reconciled with each entrypoint.

## 🛡️ 9. Drift-check (enforces §2 decision)
`atrium-project/.github/workflows/paradata-drift.reusable.yml`: hash each repo's
`para_licenses.py` / `atrium_paradata.py` against `docs/templates/shared/*`; fail on
divergence (allow-list genuinely repo-specific blocks). Each repo adds a ~12-line caller.

## 📍 10. Exact change locations
| Item          | Path:line                                            |
|---------------|------------------------------------------------------|
| F1 pc         | `atrium-page-classification/service/api.py:39`       |
| F1 translator | `atrium-translator/service/api.py:47`                |
| F1 nlp        | `atrium-nlp-enrich/service/api.py:59`                |
| F1 alto       | `atrium-alto-postprocess/service/text_api.py:43`     |
| F2            | `{translator,alto}/CITATION.cff` (date-released)     |
| G1 pc         | `run.py` top imports; `classifier.py:9`; `run.py:10` |
| G1 nlp        | `tests/test_llm_utils.py` (importorskip)             |
| H1 blueprint  | `atrium-alto-postprocess/para_licenses.py:167-188`   |
| nlp ruff      | `atrium-nlp-enrich/.pre-commit-config.yaml:6`        |

---


## 🧪 Appendix B — Exact subprocess → in-process refactors

**Scope:** 5 files / 10 subprocess invocations. **Leave untouched:** nlp `test_api_service.py` and `test_flexiconv_convert.py` — they *mock* `subprocess.run` to test in-process logic and are already correct.

### C1 — nlp `tests/test_cli.py` (simplest: delete the redundant twin)
The in-process test already exists (`test_manifest_generation_direct` → `cli_main(["--stages","manifest"])`). The `@slow` subprocess copy tests nothing new.

```diff
-from __future__ import annotations
-
-import subprocess
-import sys
-from pathlib import Path
-
-import pytest
-
-# Update this to your actual module path
 from run_pipeline import main as cli_main


 def test_manifest_generation_direct(monkeypatch, tmp_path: Path):
     """Unit-style test: call the CLI entry point directly."""
     rc = cli_main(["--stages", "manifest"])
     assert rc == 0
-
-@pytest.mark.slow
-def test_manifest_generation_smoke_subprocess(tmp_path: Path):
-    result = subprocess.run(
-        [sys.executable, "run_pipeline.py", "--stages", "manifest"],
-        capture_output=True, text=True, check=False,
-    )
-    assert result.returncode == 0, result.stderr
```
*(Keep `from pathlib import Path` if `tmp_path` typing is retained — here the direct test doesn't use it, so it's removed.)*

### C2 — alto `alto_stats_create.py` + `tests/test_alto_stats_create.py`
**Entrypoint (1-line change):** make `main` accept argv.
```diff
# alto_stats_create.py
-def main():
+def main(argv=None):
     parser = argparse.ArgumentParser()
     parser.add_argument("input_folder", help="Folder containing ALTO XML files or subfolders with them")
     parser.add_argument("-o", "--output", default="alto_stats.csv", help="Output CSV file path")
     ...
-    args = parser.parse_args()
+    args = parser.parse_args(argv)
```
**Test (in-process):**
```python
import pytest
from alto_stats_create import main

def test_alto_stats_cli_help(capsys):
    with pytest.raises(SystemExit) as e:      # argparse exits 0 on --help
        main(["--help"])
    assert e.value.code == 0
    assert "input_folder" in capsys.readouterr().out

def test_alto_stats_missing_args(capsys):
    with pytest.raises(SystemExit) as e:      # missing required positional → exit 2
        main([])
    assert e.value.code == 2
    assert "required" in capsys.readouterr().err.lower()
```

### C3 — alto `page_split.py` + `tests/test_page_split.py`
Identical shape (two required positionals `input_dir`, `output_dir`).
```diff
# page_split.py
-def main():
+def main(argv=None):
     parser = argparse.ArgumentParser(...)
     parser.add_argument("input_dir", ...)
     parser.add_argument("output_dir", ...)
     ...
-    args = parser.parse_args()
+    args = parser.parse_args(argv)
```
```python
import pytest
from page_split import main

def test_page_split_cli_help(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    assert "input_dir" in capsys.readouterr().out

def test_page_split_cli_missing_args():
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code == 2
```

### C4 — nlp `summarize_nt_udp.py` + `tests/test_teitok_integraion.py`
**Entrypoint:** extract the parser so tests can introspect flags without a subprocess.
```diff
# api_util/summarize_nt_udp.py
-def main():
-    parser = argparse.ArgumentParser()
+def build_parser():
+    parser = argparse.ArgumentParser()
     ...
     parser.add_argument("--dpi", type=_float_or_none, default=os.environ.get("IMAGE_DPI"), ...)
     parser.add_argument("--alto-dpi", type=_float_or_none, default=os.environ.get("ALTO_DPI"), help="Source ALTO DPI")
     ...
+    return parser
+
+def main(argv=None):
+    args = build_parser().parse_args(argv)
     ...
```
**Test (replaces the subprocess `--help` block; the threading test below it stays):**
```python
from api_util.summarize_nt_udp import build_parser

def test_cli_argparse_dpi_support():
    """summarize_nt_udp must expose --dpi and --alto-dpi."""
    help_text = build_parser().format_help()
    assert "--dpi" in help_text
    assert "--alto-dpi" in help_text
```
*(Drops `import subprocess`, `import os`, the `PYTHONPATH` env juggling, and the `script_path` lookup.)*

### C5 — pc `run.py` + `tests/test_run.py` (the invasive one)
`run.py` has no functions — everything is under `if __name__ == "__main__":` (line 23) and the top imports are heavy. Refactor in three moves:

**(i) Lazy heavy imports** — move `import pandas as pd`, `import numpy as np`, `from sklearn… `, `from classifier import …`, `from yolo_classifier import …` out of module top into the functions/`main` that use them, so `import run` is cheap.

**(ii) Extract `build_parser()` and `main(argv)`:**
```python
def build_parser(defaults) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Page sorter based on ViT / YOLO-cls")
    # ... lines 65–166 verbatim, reading defaults.* instead of module locals ...
    return parser

def main(argv=None) -> int:
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "setup", "config.txt"))
    defaults = _read_defaults(config)              # the block currently at lines 25–63
    args = build_parser(defaults).parse_args(argv)
    # ... existing body (lines 176→end) ...
    #   line 196:  raise ValueError(f"Revision {args.revision} is not supported…")  ← unchanged
    #   line 276:  return 0   # was sys.exit(0) on the empty-dir guard
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**(iii) Test (in-process):**
```python
import pytest
import run

def test_cli_help_flag(capsys):
    with pytest.raises(SystemExit) as e:
        run.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "Page sorter based on ViT" in out and "--topn" in out and "--best" in out

def test_cli_invalid_revision():
    # validation at run.py:196 raises before any model load → fast, no torch needed
    with pytest.raises(ValueError, match="Revision v99.9 is not supported"):
        run.main(["-rev", "v99.9", "--eval"])

def test_cli_missing_input(tmp_path):
    empty = tmp_path / "empty"; empty.mkdir()
    with pytest.raises(SystemExit) as e:   # empty-dir guard returns 0 (run.py:276)
        run.main(["-d", str(empty)])
    assert e.value.code == 0
```
**Note on the old `--topn 999` test:** `--topn` is `type=int` with no argparse bound, so 999 parses fine and only fails deep in classification — a poor *fast* unit test. Recommended: add an explicit early guard in `main()` (`if args.topn > len(CATEGORIES): raise ValueError(...)`) and unit-test that raise in-process; otherwise keep a single `@pytest.mark.slow` subprocess smoke for the full run. Flag for your call.

---

### 📋 Summary — what changes where
| File                                                   | Entrypoint change                                         | Test change                                        |
|--------------------------------------------------------|-----------------------------------------------------------|----------------------------------------------------|
| nlp `test_cli.py`                                      | none                                                      | delete redundant `@slow` subprocess twin           |
| alto `alto_stats_create.py`                            | `main(argv=None)` + `parse_args(argv)`                    | help/missing-args in-process                       |
| alto `page_split.py`                                   | `main(argv=None)` + `parse_args(argv)`                    | help/missing-args in-process                       |
| nlp `summarize_nt_udp.py`                              | extract `build_parser()`                                  | `--dpi/--alto-dpi` via `format_help()`             |
| pc `run.py`                                            | extract `build_parser()`+`main(argv)`, lazy heavy imports | 3 in-process tests (+topn decision)                |
| nlp `test_api_service.py`, `test_flexiconv_convert.py` | —                                                         | **leave as-is (mock subprocess, already correct)** |