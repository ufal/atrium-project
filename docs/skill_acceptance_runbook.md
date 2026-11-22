# Agent-skill acceptance runbook

How to accept the six `agent-skill` branches end to end: the server starts, the service contract holds,
the client's round trip works on the branch's own samples, and an agent completes a task with the
`SKILL.md` alone. The skills themselves, and the service each branch carries, are described on the site's
[Agent skills](../docs_site/agent-skills.md#the-six-skills) page. Record the results in the table at the end.

**You need:** Docker, or Python 3.11 for the `--local` start; `git`, `curl` and `python3`. The first start
of page-classification, ocr-postprocess and keyword-extract downloads models and takes minutes;
nlp-enrich and the translator call LINDAT, so they need outbound HTTPS to `lindat.mff.cuni.cz`.

## Shared procedure (every branch)

```bash
git clone -b agent-skill https://github.com/ufal/<repo>.git && cd <repo>

# 1. Start the server and wait until it is ready (scripts/server.sh waits for /ready itself)
bash scripts/server.sh                     # or --local for a virtual environment; --gpu where offered
curl -fsS localhost:8000/ready

# 2. The service contract
curl -fsS localhost:8000/info | python3 -m json.tool   # service, version, endpoints, limits
curl -fsS localhost:8000/health                        # {"status": "ok"}
curl -sS -o /dev/null -w "%{http_code}\n" "localhost:8000/health?deep=true"   # 200, or 503 with a reason

# 3. The client: what the server offers, then the round trip of the branch (below)
python3 scripts/atrium_<verb>.py --info
```

Then the clean-room test: clone the branch into an agent's skills directory
(`~/.claude/skills/<skill-name>` for Claude Code), give a fresh session only a task, and confirm that the agent
chooses the skill, starts the server, runs the client and reads its output with the `SKILL.md` alone.

**Acceptance bar:** `/ready` answers 200 after the start; `/info` carries `service`, `version`, `endpoints`
and `limits`; the client exits `0` on each sample below; the clean-room agent completes its task.

## Per-branch round trips

The commands are those of each branch's `SKILL.md`, on the samples the branch carries.

### atrium-page-classification

```bash
python3 scripts/atrium_classify.py small_data_samples/DRAW/atrium-34.png
python3 scripts/atrium_classify.py small_data_samples/LINE_HW/pages_online_6.png --topn 5 --format csv
```

Expect `FILE,PAGE,RANK,LABEL,SCORE` rows.

### atrium-ocr-postprocess

```bash
python3 scripts/atrium_postprocess.py small_data_samples/CTX000000001-1.alto.xml
python3 scripts/atrium_postprocess.py small_data_samples/CTX000000001-1.txt --format csv
```

Expect each line with its language, quality score and category.

### atrium-digital-convert

```bash
python3 scripts/atrium_convert.py small_data_samples/enrichable.pdf
python3 scripts/atrium_convert.py small_data_samples/image_only.pdf
python3 scripts/atrium_convert.py small_data_samples/minimal.docx --markdown --out-dir out/
```

Expect the converted document with a verdict for every page; the image-only PDF's pages need the ATR. The
client's `--describe`, the per-page assessment, is parked during the AMČR pilot and is not part of the
acceptance.

### atrium-nlp-enrich

```bash
python3 scripts/atrium_enrich.py small_data_samples/CTX000000001.csv
python3 scripts/atrium_enrich.py small_data_samples/lines_sample.txt --format csv
```

Expect the named entities of each page, and in JSON the TEITOK file and the paradata.

### atrium-keyword-extract

```bash
python3 scripts/atrium_keywords.py small_data_samples/report.document.json
python3 scripts/atrium_keywords.py small_data_samples/report.txt --kind statistical --format csv
```

Expect the statistical keywords of the document and its pages. The controlled kind needs a backend
(`OPENROUTER_API_KEY` and `OPENROUTER_MODEL`, or a local Ollama) when the server starts; without one,
`kind=controlled` answers 501.

### atrium-translator

```bash
python3 scripts/atrium_translate.py small_data_samples/MTX201501307_anon.alto.xml
python3 scripts/atrium_translate.py small_data_samples/C-202000543A-DT-27.xml --no-alto --source-lang cs
```

Expect the translated XML under the server's proposed name; check that it parses. The client sends no field
list: the metadata call works against the service the branch carries, which reads its list from its own
configuration, and is refused by a 2.0.0-beta service (422, `cause` `missing_xpaths`).

## Results (fill in)

| Branch              | Branch commit | `server.sh` and `/ready` | `/info` and `/health` | Client round trip | Clean-room agent | Notes |
|---------------------|---------------|--------------------------|-----------------------|-------------------|------------------|-------|
| page-classification |               | ☐                        | ☐                     | ☐                 | ☐                |       |
| ocr-postprocess     |               | ☐                        | ☐                     | ☐                 | ☐                |       |
| digital-convert     |               | ☐                        | ☐                     | ☐                 | ☐                |       |
| nlp-enrich          |               | ☐                        | ☐                     | ☐                 | ☐                |       |
| keyword-extract     |               | ☐                        | ☐                     | ☐                 | ☐                |       |
| translator          |               | ☐                        | ☐                     | ☐                 | ☐                |       |

A host without a GPU or without access to the models can run the translator and nlp-enrich round trips
(their work is at LINDAT) and the contract checks; record where each row was run.
