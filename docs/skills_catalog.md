# 🧩 ATRIUM Agent-Skills Catalog

_Installable [Agent Skills](https://agentskills.io) wrapping each ATRIUM service's API, per issue
[#31](https://github.com/ufal/atrium-project/issues/31). Normative standard:
[`agent_skill_strategy.md`](agent_skill_strategy.md) · templates: [`templates/skill/`](templates/skill/)._

Each skill lives on its repo's **`agent-skill` branch** as a flattened, trimmed derivative: a
`SKILL.md` contract + a zero-dependency stdlib client the agent runs + an idempotent
`scripts/server.sh` + the unchanged FastAPI `service/`. One artifact serves Claude Code, Codex,
Google Antigravity, Gemini CLI, and other Agent-Skill hosts.

## The six skills

| Skill (`name:`)              | Repo                                                                                       | Does                                                                                             | Primary endpoints                                       | Client                          | Env override    |
|------------------------------|--------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------|---------------------------------|-----------------|
| `atrium-page-classification` | [page-classification](https://github.com/ufal/atrium-page-classification/tree/agent-skill) | classify historical page images/PDFs into 11 structural categories                               | `POST /predict_image` · `POST /predict_document`        | `scripts/atrium_classify.py`    | `ATRIUM_PC_URL` |
| `atrium-ocr-postprocess`     | [ocr-postprocess](https://github.com/ufal/atrium-ocr-postprocess/tree/agent-skill)         | per-line OCR language ID + quality classification                                                | `POST /process`                                         | `scripts/atrium_postprocess.py` | `ATRIUM_AP_URL` |
| `atrium-translator`          | [translator](https://github.com/ufal/atrium-translator/tree/agent-skill)                   | structure-preserving translation of ALTO/AMCR XML                                                | `POST /translate`                                       | `scripts/atrium_translate.py`   | `ATRIUM_TR_URL` |
| `atrium-nlp-enrich`          | [nlp-enrich](https://github.com/ufal/atrium-nlp-enrich/tree/agent-skill)                   | UDPipe + NameTag enrichment → TEITOK XML                                                         | `POST /enrich` · `/enrich_text` · `/rescale` · jobs API | `scripts/atrium_enrich.py`      | `ATRIUM_NE_URL` |
| `atrium-keyword-extract`     | [keyword-extract](https://github.com/ufal/atrium-keyword-extract/tree/agent-skill)         | statistical keywords (KeyBERT, YAKE, lemma counts); vocabulary-guided LLM keywords (TEATER/AMČR) | `POST /extract_keywords` · `/extract_keywords_text`     | `scripts/atrium_keywords.py`    | `ATRIUM_KW_URL` |
| `atrium-digital-convert`     | [digital-convert](https://github.com/ufal/atrium-digital-convert/tree/agent-skill)         | born-digital documents → the ATRIUM record; per-page text-layer verdict and route                | `POST /reformat` · `POST /describe`                     | `scripts/atrium_convert.py`     | `ATRIUM_DC_URL` |

All six also expose the standardized meta-contract: **`GET /info`**
(`service`/`version`/`endpoints`/`limits` + capabilities), **`GET /health`** (liveness; `?deep=true` for
a dependency check), and **`GET /ready`** (readiness — issue #55: 503 until warm-up completes or once a
shutdown signal arrives, which is what `scripts/server.sh` now polls instead of `/info`). Full
request/response schemas: fetch `GET /openapi.json` (Swagger UI at `/docs`) from a running server.

## Typical pipeline order

```
scan → page-classification → ocr-postprocess (quality filter) → translator ─┐
                                                                         ├─→ nlp-enrich → keyword-extract
                                                                     (Clear lines only)
```

Route only `Clear`/`Noisy` lines from ocr-postprocess into the downstream NLP and keyword stages.

> **Names (2026-10-21):** the skills were first written for `alto-postprocess` and `llm-enrich`, whose repositories
> are archived. ocr-postprocess's skill now carries its own name; keyword-extract's and digital-convert's skills are
> new, built from the skeleton for their own endpoints (keyword-extract takes a record or plain text, not llm-enrich's
> CSV of lines). Use `ATRIUM_KW_URL` for keyword-extract; `ATRIUM_LE_URL` belonged to llm-enrich.

## Install (any host)

```bash
# Claude Code
git clone -b agent-skill https://github.com/ufal/<repo>.git ~/.claude/skills/<skill-name>
# OpenAI Codex
git clone -b agent-skill https://github.com/ufal/<repo>.git ~/.codex/skills/<skill-name>
# Google Antigravity: clone anywhere, point AGENTS.md at <skill>/SKILL.md
```

Update = `git pull` in the installed clone. Each skill's own branch `README.md` carries the
per-host detail and the server quick-start (`bash scripts/server.sh`).

## AGENTS.md pointer (Antigravity / generic)

```
Use the ATRIUM <tool> skill from `<skill-name>/SKILL.md`.
Start the server with `bash <skill-name>/scripts/server.sh`, then run
`python3 <skill-name>/scripts/atrium_<verb>.py [FILES...]`.
```

## Contract & conventions (from [`agent_skill_strategy.md`](agent_skill_strategy.md))

- **Client**: Python 3 stdlib only; `--base-url` / `ATRIUM_<XX>_URL`; `--format table|csv|json`
  (except translator, which returns an XML attachment via `-o`); 3× retry on 503/504 and on a 502
  that is not final (`upstream_unavailable` or a proxy; not `reason: null`); exit
  codes `0` ok · `1` usage/input · `2` unreachable · `3` server error.
- **Errors**: `413` too large · `415` unsupported type · `422` unusable input · `429` busy ·
  `500` failure · `502` `upstream_unavailable` (retry) or without a reason (no retry) ·
  `503/504` warming up (retry).
- **Version**: read from `para_config.txt` `[tool]`, surfaced via `/info` — never hard-coded.
- **Provenance**: services that write paradata route agents through the API so runs stay logged
  (a skill claims this only if its branch actually writes it).

## Status & tracking

Implemented on five `agent-skill` branches on 2026-07-18, and on digital-convert's on 2026-10-21. Each is kept in
step with its repo's `test` branch by hand, per [`agent_skill_strategy.md`](agent_skill_strategy.md) §12.2, with
`tools/skill_ify.py` deriving the tree and `tools/skill_drift_check.py` checking it.

**Last sync: 2026-10-21** (atrium-project#77 C), from the `test` heads of that morning. `skill_drift_check.py`
reports **6/6 aligned**; each `service/README.md` is the repo's runbook with the trimmed parts pointed at `test`,
declared in `DOCUMENTED_DIVERGENCES`. In that pass:

- every client retries a `502` only when it is not final (`RETRY_502_REASONS`), exits `1` on a usage error, and
  every `scripts/server.sh` waits for `/ready`; `skill_drift_check.py` now fails a client that retries every `502`;
- keyword-extract and digital-convert got skills of their own, replacing the llm-enrich and nlp-enrich copies;
  ocr-postprocess's skill is named `atrium-ocr-postprocess`; nlp-enrich's no longer offers keywords (they left it
  in 1.0.0);
- `skill_ify.py apply` keeps the files only the skill branch carries, and their file modes.

Treat any snapshot here as perishable: run the tool rather than trusting this line.

Refinement still open: one green `skill-validate` run per branch with the repaired callers,
live end-to-end acceptance round-trips, and release tags. The per-repo `agent-skill: <repo>`
sub-issues under #31 (§13) have **not** been created — tracking is in the hub logs meanwhile:
[`agent_dev_logs/plans/31.plan.md`](../agent_dev_logs/plans/31.plan.md) ·
[`agent_dev_logs/digests/31.digest.md`](../agent_dev_logs/digests/31.digest.md).
