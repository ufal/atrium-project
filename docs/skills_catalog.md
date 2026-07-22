# 🧩 ATRIUM Agent-Skills Catalog

_Installable [Agent Skills](https://agentskills.io) wrapping each ATRIUM service's API, per issue
[#31](https://github.com/ufal/atrium-project/issues/31). Normative standard:
[`agent_skill_strategy.md`](agent_skill_strategy.md) · templates: [`templates/skill/`](templates/skill/)._

Each skill lives on its repo's **`agent-skill` branch** as a flattened, trimmed derivative: a
`SKILL.md` contract + a zero-dependency stdlib client the agent runs + an idempotent
`scripts/server.sh` + the unchanged FastAPI `service/`. One artifact serves Claude Code, Codex,
Google Antigravity, Gemini CLI, and other Agent-Skill hosts.

## The five skills

| Skill (`name:`) | Repo | Does | Primary endpoints | Client | Env override |
|---|---|---|---|---|---|
| `atrium-page-classification` | [page-classification](https://github.com/ufal/atrium-page-classification/tree/agent-skill) | classify historical page images/PDFs into 11 structural categories | `POST /predict_image` · `POST /predict_document` | `scripts/atrium_classify.py` | `ATRIUM_PC_URL` |
| `atrium-alto-postprocess` | [alto-postprocess](https://github.com/ufal/atrium-alto-postprocess/tree/agent-skill) | per-line OCR language ID + quality classification | `POST /process` | `scripts/atrium_postprocess.py` | `ATRIUM_AP_URL` |
| `atrium-translator` | [translator](https://github.com/ufal/atrium-translator/tree/agent-skill) | structure-preserving translation of ALTO/AMCR XML | `POST /translate` | `scripts/atrium_translate.py` | `ATRIUM_TR_URL` |
| `atrium-nlp-enrich` | [nlp-enrich](https://github.com/ufal/atrium-nlp-enrich/tree/agent-skill) | UDPipe + NameTag + keyword enrichment → TEITOK XML | `POST /enrich` · `/enrich_text` · `/rescale` · jobs API | `scripts/atrium_enrich.py` | `ATRIUM_NE_URL` |
| `atrium-llm-enrich` | [llm-enrich](https://github.com/ufal/atrium-llm-enrich/tree/agent-skill) | vocabulary-guided LLM keyword extraction (TEATER/AMCR) | `POST /extract_keywords` · `/extract_keywords_text` | `scripts/atrium_keywords.py` | `ATRIUM_LE_URL` |

All five also expose the standardized meta-contract: **`GET /info`**
(`service`/`version`/`endpoints`/`limits` + capabilities) and **`GET /health`** (`?deep=true` for
readiness). Full request/response schemas: fetch `GET /openapi.json` (Swagger UI at `/docs`) from a
running server.

## Typical pipeline order

```
scan → page-classification → alto-postprocess (quality filter) → translator ─┐
                                                                             ├─→ nlp-enrich → llm-enrich
                                                                     (Clear lines only)
```

Route only `Clear`/`Noisy` lines from alto-postprocess into the downstream NLP/LLM enrichers.

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
  (except translator, which returns an XML attachment via `-o`); 3× retry on 502/503/504; exit
  codes `0` ok · `1` usage/input · `2` unreachable · `3` server error.
- **Errors**: `413` too large · `415` unsupported type · `422` unusable input · `429` busy ·
  `500` failure · `502/503/504` warming up (retry).
- **Version**: read from `para_config.txt` `[tool]`, surfaced via `/info` — never hard-coded.
- **Provenance**: services that write paradata route agents through the API so runs stay logged
  (a skill claims this only if its branch actually writes it).

## Status & tracking

Implemented on all five `agent-skill` branches (2026-07-18). Refinement stage: validation CI
(`skill-validate.yml` callers), contract tests, end-to-end acceptance, consistency, release tags.
Per-repo tracking: sub-issues `agent-skill: <repo>` under #31. Session log:
[`agent_dev_logs/plans/31.plan.md`](../agent_dev_logs/plans/31.plan.md) ·
[`agent_dev_logs/digests/31.digest.md`](../agent_dev_logs/digests/31.digest.md).
