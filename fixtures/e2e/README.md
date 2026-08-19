# 🧪 E2E pipeline smoke fixture — `CTX000000003`

One **single-page, synthetic Czech** document that travels the whole ATRIUM tool chain in CI
(issue [#18](https://github.com/ufal/atrium-project/issues/18) follow-up — the
"end-to-end integration smoke test" proposed 2026-06-26):

```
pc → alto → translate → nlp → llm → TEITOK
```

Driven by [`.github/workflows/e2e-pipeline-smoke.yml`](../../.github/workflows/e2e-pipeline-smoke.yml)
with helpers in [`tools/e2e/`](../../tools/e2e/). Every job boundary is one cross-repo interface;
assertions check **formats and contracts, never model quality**.

> ⚠️ **What a green run actually covers.** Each stage runs a *published image* (selected by the
> `image-tag` input) but mounts *source checked out with no `ref:`* — i.e. each tool repo's **default
> branch**, not the branch or tag the image was built from. Only the hub checkout is pinned (`@v1`).
> So a run does **not** describe one coherent artifact, and this file previously claimed "all tool
> repos are checked out at the same ref (default `test`)", which was never true of the workflow as
> written. Treat a green run as "default-branch source is compatible with the `image-tag` runtime",
> and read the two together. Coupling `ref:` to `image-tag` (a `tool-ref` input) is the real fix and
> is filed separately — it is a behaviour change to what the gate means, not a doc correction.

## 📄 Contents & provenance

Both files are **byte-identical drop-in copies** from `atrium-alto-postprocess` at `test` HEAD —
the same distribution model as the canonical shared files (`atrium_paradata.py` et al.):

| File                              | Copied from                                                            | Role                                                                                                                                              |
|-----------------------------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| `ALTO/CTX000000003.alto.xml`      | `atrium-alto-postprocess/data_samples/ALTO/CTX000000003.alto.xml`      | 🇨🇿 Source of truth: the single-page synthetic calibration sample (1 page, 2 lines: *„Náčrt sondy."* + *„1998"*), ALTO v3, `LANG="cs"`.          |
| `DOC_LINE_CATEG/CTX000000003.csv` | `atrium-alto-postprocess/data_samples/DOC_LINE_CATEG/CTX000000003.csv` | 🌉 The **GPU bridge**: the real `classify`-stage output for that page in alto HEAD's `CSV_HEADER` format (37 columns; 1× `Clear`, 1× `Non-text`). |

There is **no committed page image** — the pc stage renders one from the ALTO at runtime
(`tools/e2e/render_alto_page.py`), keeping the whole smoke anchored to one fixture.

### 🏷️ No vocabulary fixture (removed 2026-08-19)

`VOCAB/teater_nested_vocab.json` used to live here, on the stated grounds that "llm-enrich
intentionally ships no `data_samples` of its own". That stopped being true: llm-enrich now builds
and commits a union of the AMCR and TEATER thesauri under `data_samples/vocab/`, and the hub copy
silently became a snapshot of a file that no longer exists upstream.

Stage 5 already checks out llm-enrich into `work/atrium-llm-enrich-main` and runs from it, so it now
reads `data_samples/vocab/union_nested.json` straight out of that checkout. A fixture the hub has to
re-copy by hand whenever another repo rebuilds its vocabulary is a drift source, and this one drifted
undetected until run [32208408456](https://github.com/ufal/atrium-project/actions/runs/32208408456)
— where a missing vocabulary caused a live AMCR harvest, a one-term category enum, and an
`enrichment` block that never got written.

Unlike the ALTO and CSV above, nothing here needs a *pinned* copy of the vocabulary: those two are
fixed inputs whose content the assertions depend on, whereas the vocabulary is a moving upstream
artifact the smoke test should track rather than freeze.

## 🌉 Why the DOC_LINE_CATEG bridge exists

`langID_classify.py` hard-requires CUDA
