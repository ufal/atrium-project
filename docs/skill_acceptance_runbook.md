# ✅ Agent-Skill acceptance runbook (issue #31 · W2)

Per-repo end-to-end acceptance for the `agent-skill` branches. Run in the order below (cheapest /
most foundational first). Each repo's block is self-contained; record PASS/FAIL + notes under that
repo's `agent_dev_logs/`. **Requires model downloads and a running server** — expect the first
start of the model-heavy services to take minutes (page-classification, alto-postprocess,
nlp-enrich, llm-enrich); translator is light (calls remote LINDAT).

## Shared procedure (every repo)

```bash
git clone -b agent-skill https://github.com/ufal/<repo>.git && cd <repo>

# 1. Server up (idempotent; Docker or --local venv fallback)
bash scripts/server.sh                     # or --gpu / --local

# 2. Meta-contract conforms
curl -s localhost:8000/info    | python3 -m json.tool   # must have service, version, endpoints, limits
curl -s localhost:8000/health                            # {"status":"ok"}
curl -s "localhost:8000/health?deep=true"                # 200 ready / 503 degraded

# 3. Client discovers capabilities, then does the primary round-trip (see per-repo below)
python3 scripts/atrium_<verb>.py --info
python3 scripts/atrium_<verb>.py <sample> [flags]        # expect exit 0 + rows/output

# 4. Clean-room agent test
git clone -b agent-skill https://github.com/ufal/<repo>.git ~/.claude/skills/<name>
#   → in a fresh Claude Code session, give ONLY a task; confirm the agent selects the skill,
#     starts the server, runs the client, and interprets output using only SKILL.md.
```

**Acceptance bar (all must hold):** `/info` carries `service`/`version`/`endpoints`/`limits`;
`/health` conforms; anti-pattern checklist green; client exits `0` on the sample; clean-room agent
completes the round-trip using only SKILL.md.

## Per-repo primary round-trips

### 1. atrium-page-classification
```bash
python3 scripts/atrium_classify.py small_data_samples/TEXT/atrium-01.png
python3 scripts/atrium_classify.py small_data_samples/DRAW/atrium-34.png --topn 5 --format csv
```
Expect `FILE,PAGE,RANK,LABEL,SCORE` rows; first start downloads ViT/RegNetY/EffNetV2 weights.

### 2. atrium-alto-postprocess
```bash
python3 scripts/atrium_postprocess.py small_data_samples/CTX000000001-1.alto.xml
python3 scripts/atrium_postprocess.py small_data_samples/CTX000000001-1.txt --format json
```
Expect `FILE,LINE,LANG,QUALITY,CATEGORY,TEXT`; JSON `reading_order` = `layout-reader` for the ALTO input.

### 3. atrium-translator (light — remote LINDAT)
```bash
python3 scripts/atrium_translate.py small_data_samples/MTX201501307_anon.alto.xml
python3 scripts/atrium_translate.py small_data_samples/C-202000543A-DT-27.xml --no-alto --source-lang cs
```
Expect a translated XML saved under the server-proposed name; validate it parses.

### 4. atrium-nlp-enrich
```bash
python3 scripts/atrium_enrich.py small_data_samples/CTX000000001.csv
python3 scripts/atrium_enrich.py small_data_samples/lines_sample.txt --kw-method yake --format json
python3 scripts/atrium_enrich.py small_data_samples/CTX000000001.csv --jobs   # async path
```
Expect `DOC,RANK,KEYWORD,SCORE`; JSON envelope carries `teitok_xml`/`ne_summary`/`paradata`.

### 5. atrium-llm-enrich (needs a backend)
```bash
export OPENROUTER_API_KEY=sk-or-...          # or run a local Ollama server
python3 scripts/atrium_keywords.py small_data_samples/lines_sample.txt --top-k 5
python3 scripts/atrium_keywords.py small_data_samples/lines_sample.csv --backend ollama --format json
```
Expect `DOC,PAGE,LINE,CATEGORY,CONF,KEYWORDS_CS`; first start auto-syncs the TEATER/AMCR vocabulary
(minutes). `backend=local` must answer HTTP 501.

## Results log (fill in)

| Repo | server.sh | /info+/health | client smoke | clean-room | notes |
|---|---|---|---|---|---|
| page-classification | ☐ | ☐ | ☐ | ☐ | |
| alto-postprocess | ☐ | ☐ | ☐ | ☐ | |
| translator | ☐ | ☐ | ☐ | ☐ | |
| nlp-enrich | ☐ | ☐ | ☐ | ☐ | |
| llm-enrich | ☐ | ☐ | ☐ | ☐ | |

> Environment note: CI/sandbox without GPU or outbound model access can only complete the
> translator round-trip (remote) and the meta-contract checks via `TestClient`; the model-heavy
> services need a host with weights + memory. Record which rows were run where.
