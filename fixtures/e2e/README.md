# 🧪 E2E pipeline smoke fixture — `CTX000000003`

One **single-page, synthetic Czech** document that travels the whole ATRIUM tool chain in CI
(issue [#18](https://github.com/ufal/atrium-project/issues/18) follow-up — the
"end-to-end integration smoke test" proposed 2026-06-26):

```
pc → alto → translate → nlp → llm → TEITOK
```

Driven by [`.github/workflows/e2e-pipeline-smoke.yml`](../../.github/workflows/e2e-pipeline-smoke.yml)
with helpers in [`tools/e2e/`](../../tools/e2e/). Every job boundary is one cross-repo interface;
assertions check **formats and contracts, never model quality**. All tool repos are checked out at
the same ref (default `test`), so any repo's push that breaks a neighbour surfaces here within a day.

## 📄 Contents & provenance

Both files are **byte-identical drop-in copies** from `atrium-alto-postprocess` at `test` HEAD —
the same distribution model as the canonical shared files (`atrium_paradata.py` et al.):

| File                              | Copied from (in `ufal/atrium-alto-postprocess`) | Role                                                                                                                                              |
|-----------------------------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `ALTO/CTX000000003.alto.xml`      | `data_samples/ALTO/CTX000000003.alto.xml`       | 🇨🇿 Source of truth: the single-page synthetic calibration sample (1 page, 2 lines: *„Náčrt sondy."* + *„1998"*), ALTO v3, `LANG="cs"`.          |
| `DOC_LINE_CATEG/CTX000000003.csv` | `data_samples/DOC_LINE_CATEG/CTX000000003.csv`  | 🌉 The **GPU bridge**: the real `classify`-stage output for that page in alto HEAD's `CSV_HEADER` format (37 columns; 1× `Clear`, 1× `Non-text`). |

There is **no committed page image** — the pc stage renders one from the ALTO at runtime
(`tools/e2e/render_alto_page.py`), keeping the whole smoke anchored to one fixture.

## 🌉 Why the DOC_LINE_CATEG bridge exists

`langID_classify.py` hard-requires CUDA