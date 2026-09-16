# agent-skill branches — categorised work plan (2026-09-16)

All five branches were last touched **2026-09-09**; every `test` branch moved on **2026-09-16**.
`skill_drift_check.py` reports **0/5 aligned**. Scope of this round: the three branches with
confirmed breakage (nlp-enrich, llm-enrich, page-classification). translator and alto-postprocess
are reported here without file deliverables.

**No `skill-v*` tag exists in any remote.** §12.2 step 5 has never been executed, so agents have
nothing to pin.

---

## ⚠️ Two findings to read before anything else

### 1. `DOCUMENTED_DIVERGENCES` is suppressing a memory-exhaustion fix (translator)

`skill_drift_check.py:96-98` records translator's `service/api.py` divergence as *"adds the
`.exists()`-guarded /frontend StaticFiles mount"*. That is true of **16 lines**. The entry keys on
`(repo, path)` and therefore suppresses the **whole file** — 288 lines of drift, including the
upload-size fix.

On the skill branch (`service/api.py:160`):

```python
if len(content) > MAX_UPLOAD_BYTES:
    raise HTTPException(status_code=413, detail=...)
```

The body has already been read into `content` before the size is checked, so the 413 is unreachable
for exactly the inputs it exists to refuse — an unauthenticated caller can drive the container to
OOM. `test` replaced this with `_reject_oversized_envelope()` (early reject on declared
`Content-Length`) plus `_read_bounded()` (chunked enforcement).

`skill_drift_check` prints this file as a green `· documented divergence` note. **translator is out
of this round's scope, but this one item should not wait for the rest.**

The same over-broad entry exists for llm-enrich (hides the whole #58/#61/#55 entrypoint) and
page-classification (hides 40 lines of env documentation). After the ports below land, the residual
divergence really is just the mount / just the one paragraph, and the reason strings should be
tightened to say so.

### 2. Three classes of defect the tools structurally cannot see

| blind spot                                                  | consequence                                                                                                                                                                                                                                                        |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `skill_ify.derive()` protects anything not in `test`'s tree | it can never propose deleting an **orphan rename** — translator's root `translation_backends.md` (8 dangling refs to `docs/translation-backends.md`) and alto's `setup/config_langID.txt` (breaks `bash scripts/server.sh --local`, which sets no `LANGID_CONFIG`) |
| `OVERLAY_DIRS` protects `service/frontend/`                 | page-classification's `service/frontend/script.js` `$PORT` bug never appears in any `skill_ify plan`; only `skill_drift_check` sees it                                                                                                                             |
| `_script_refs_py` reads string literals, not path joins     | `api_util/validate_teitok_xml.py:47` builds its schema path with `Path(__file__).parent.parent / "schemas" / …`, so copying the module without `schemas/teitok/*.xsd` leaves the branch "clean" per the tool and broken in fact                                    |

---

## Category 1 — copy from `test` UNCHANGED (no authoring)

### atrium-nlp-enrich
| path                                                  | why byte-identical is correct                                                                                                                                                                    |
|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `api_util/teitok_read.py`                             | `keywords.py:55` module-level import. Only non-stdlib dep is `atrium_document`, already on branch. ⚠️ copy from **nlp-enrich's own** `test` — llm-enrich has a *different* file of the same name |
| `api_util/document_hook.py`                           | `api_util/summarize_nt_udp.py:588`. Deps `atrium_document` + `.teitok_alto`, both present                                                                                                        |
| `api_util/validate_teitok_xml.py`                     | `api_4_stats.sh:138` execs it; `service/api.py:122` imports `validate_xml_text`. `lxml` already in branch `requirements.txt`; missing-lxml degrades via a typed `LxmlMissing`                    |
| **`schemas/teitok/teitok.xsd`**                       | **required by the above** — without it the validator exits 1 on every request                                                                                                                    |
| **`schemas/teitok/xml.xsd`**                          | imported by `teitok.xsd:36-37`                                                                                                                                                                   |
| `schemas/teitok/README.md`                            | pinned-schema provenance                                                                                                                                                                         |
| `config_api.txt` + `service/enrichment.py`            | **must land together** — see Category 3                                                                                                                                                          |
| `api_util/call_udpipe.py`, `api_util/call_nametag.py` | #63 `UDPIPE_URL`/`NAMETAG_URL` with `or`-not-`default=` empty-env handling                                                                                                                       |
| `api_2_udp.sh`, `api_3_nt.sh`                         | #63 url passthrough + paradata field                                                                                                                                                             |
| `para_config.txt`, `CITATION.cff`                     | v0.20.1 → v0.20.2; `/info` reads it                                                                                                                                                              |
| `atrium_document.schema.json`, `.env.example`         | para-drift canonical; env table prerequisite                                                                                                                                                     |

### atrium-llm-enrich
| path                                                                                | why                                                                                                                                                                                                                                                                                     |
|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `api_util/layout_md.py`                                                             | **the shipped break.** `api_util/xml_to_md.py:31` module-level `from api_util import layout_md as L`, and `SKILL.md:130` tells the agent to run `xml_to_md.py`. `api_util/` has no `__init__.py`, so it is a namespace package and this is a hard `ImportError`. 295 lines, stdlib only |
| `api_util/doc_to_visual_md.py` + `json_to_md.py` + `docx_to_md.py` + `pdf_to_md.py` | **atomic 4-file set.** `doc_to_visual_md.py:38` imports all three at module level. Safe: `docx_to_md`/`pdf_to_md` probe `python-docx`/`pdfplumber` *inside* `docx_available()` / `pdfplumber_available()`, so the copy adds **no new requirements**                                     |
| `para_licenses.py`, `check_version.py`                                              | para-drift canonical **and** in this repo's service closure                                                                                                                                                                                                                             |
| `atrium_document.schema.json`, `.env.example`                                       | as above                                                                                                                                                                                                                                                                                |

### atrium-page-classification
| path                                                                      | why                                                                                                                                       |
|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `atrium_paradata.py`                                                      | para-drift canonical; blob already identical on the four other skill branches — this one is the sole outlier. `run.py:11` hard-imports it |
| `yolo_classifier.py`                                                      | `run.py:373`; `ultralytics` already in the branch's `setup/requirements.txt`, and `from ultralytics import YOLO` is try/except-guarded    |
| `service/inference.py`                                                    | #61 — removes `logging.basicConfig()` from a library module                                                                               |
| `service/frontend/script.js`                                              | #58 — the old `origin.includes('localhost') ? ':8000'` breaks under any non-default `PORT`. **`skill_ify` is blind to this**              |
| `model_registry.py`, `setup/requirements.txt`                             | staged `MODEL_STATIC` v*.4 rows (VRAM budgeting) + floor bumps                                                                            |
| `atrium_document.schema.json`, `.env.example`, `model_accuracies_new.csv` | canonical; env prerequisite; the CSV the new namespace comment is *about*                                                                 |

---

## Category 2 — CREATE on the skill branch (no verbatim source)

Each is a **section-level graft**, not a file copy: the surrounding `test` text cites `tests/` and
`data_samples/`, which §5 trims.

| repo · path                                                      | contents                                                                                                                                                                                                                                                                                                                    |
|------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| nlp-enrich · `service/README.md` → "Configuration (environment)" | `test`'s env table + the #63 precedence paragraph ("environment wins, the file is the default; the `${VAR:-default}` form is load-bearing"). **Drop** `test`'s Testing block (`pytest … tests/test_api_service.py`, `service/test_api.py`, `data_samples/…` — none exist here) and add the pair to `DOCUMENTED_DIVERGENCES` |
| nlp-enrich · `SKILL.md` → `/jobs` replica guideline              | An *agent* polling `/jobs/{id}` needs: "a 404 on a previously-accepted job id means the replica changed — resubmit, do not loop." `test` writes this for an operator, not an agent                                                                                                                                          |
| llm-enrich · `service/README.md` → env table                     | `python -m service.api  # honours PORT/HOST`, the 14-row env table, the `HOST=127.0.0.1` healthy-but-unreachable warning, and the `ENV GRACEFUL_SHUTDOWN_S=20` shutdown paragraph replacing the old ENTRYPOINT flag                                                                                                         |
| page-classification · `service/README.md` → env table            | Same graft. **Do not** copy the surrounding `test` text — the same commit rewrote the requirements note to cite `setup/requirements-test.txt` and `tests/test_service_runtime_deps.py`, which is exactly what `DOCUMENTED_DIVERGENCES` exists to keep off this branch                                                       |
| page-classification · `README.md` → "Maintenance notes"          | Name this branch as a required step of the v*.4 ensemble swap, mirroring `model_registry.py`'s own step 4                                                                                                                                                                                                                   |

---

## Category 3 — EXISTS but out of alignment

| repo · path                                                 | divergence                                                                                                                                               | class                            | action                                                                                                                                                                                                                 |
|-------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **llm-enrich · `service/api.py`**                           | skill has the guarded `/frontend` mount **but** a hardcoded `uvicorn.run(..., port=8000)`; `test` has the full #58/#61/#55 `__main__` block and no mount | **mixed**                        | ✅ **delivered** — `test`'s file with the 15-line mount grafted back. Verified: imports clean, PORT+HOST read, mount guard correctly skips where `service/frontend/` is absent (so it is forward-mergeable, not a fork) |
| **llm-enrich · `llm_client_shared.py`**                     | identical on both branches                                                                                                                               | hardening                        | ✅ **delivered** — forward-mergeable guard turning a bare `ModuleNotFoundError` into an actionable error. Now belt-and-braces rather than the fix, since the Category-1 4-file copy is the real resolution              |
| nlp-enrich · `service/api.py`                               | no module logger; bare `HTTPException(404, "Job not found")`; hardcoded port                                                                             | (a) defect                       | copy `test` byte-identical                                                                                                                                                                                             |
| **nlp-enrich · `config_api.txt` + `service/enrichment.py`** | `${VAR:-default}` unwrapping                                                                                                                             | (a) defect                       | **land together, never separately.** Porting `config_api.txt` alone sends the raw `${…}` string to `_deep_health`'s urllib call and **every deep probe reports "backend unreachable"**                                 |
| nlp-enrich · `setup_api_service.sh`                         | `on :8000` → `on ${PORT:-8000}`                                                                                                                          | (c) staleness                    | copy                                                                                                                                                                                                                   |
| page-classification · `service/api.py`                      | hardcoded `port=8000`                                                                                                                                    | (a) defect                       | copy `test` byte-identical (no mount on this branch)                                                                                                                                                                   |
| page-classification · `service/README.md`                   | see Category 2                                                                                                                                           | (b) deliberate, **under-stated** | after grafting, rewrite the `DOCUMENTED_DIVERGENCES` reason to name the specific paragraph                                                                                                                             |

---

## `skill_ify plan` — deletions and adds to reject

**Deletions that are NOT safe as proposed** (would turn skill-validate step 2 **red**, not merely
leave stale prose): page-classification and alto-postprocess `service/frontend-lindat/{index.html,script.js}`
— each is cited in that branch's `service/README.md` with a backticked token whose first segment
(`service/`) is a live directory. Delete the directory **and** edit those lines in one change.

**Safe:** nlp-enrich's two (mounted behind `.exists()`, no doc mentions them) and llm-enrich's
`api_util/teitok_alto.py` (nothing on-branch imports it; the `atrium_vocab.py` citations point at
*nlp-enrich's* copy).

**Adds to reject:** `setup/requirements-test.txt` (page-classification, alto) — a `skill_ify`
`TRIM_FILES` bug: it matches the bare path only, so the `setup/`-prefixed copy slips through.
`README.html` (178 KB). llm-enrich's `digital_born/sample.{pdf,docx}` + IR json (**5.2 MB of
binaries**, and the plan adds the samples without the `probe_*.py` scripts that explain them).
nlp-enrich's `api_util/__init__` (**no `.py`** — an empty-blob typo artefact on `test`; worth filing
against `test` rather than copying).

---

## Landing order (each step leaves the branch no worse)

1. All five: `atrium_document.schema.json` — one delta, five identical copies → kills 5 findings.
2. page-classification: `atrium_paradata.py` + `yolo_classifier.py` → kills "broken as shipped".
3. llm-enrich: the 4-file converter set + `layout_md.py` → kills "broken as shipped" and unbreaks
   the documented `SKILL.md:130` path.
4. nlp-enrich: the three `api_util/*.py` **+ `schemas/teitok/*`** → same.
5. nlp-enrich: `config_api.txt` **and** `service/enrichment.py` together.
6. The `service/api.py` ports (llm-enrich ✅ delivered, page-classification, translator), re-adding
   the guarded mounts, then tighten the three `DOCUMENTED_DIVERGENCES` reason strings.
7. Out of scope this round but queued: alto's `setup/config.txt` swap; translator's
   `docs/translation-backends.md` relocation and the v1.1.0-beta port **including the upload fix**.
8. Version bumps (`para_config.txt`, `CITATION.cff`) last, then `git tag skill-v<version>` — §12.2
   step 5, never yet run anywhere.
