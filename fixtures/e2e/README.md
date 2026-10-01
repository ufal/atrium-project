# 🧪 E2E pipeline smoke fixtures — default `CTX000000003`

Five fixture pairs; the default is one **single-page, synthetic Czech** document that travels the whole
ATRIUM tool chain in CI (issue [#18](https://github.com/ufal/atrium-project/issues/18) follow-up — the
"end-to-end integration smoke test" proposed 2026-06-26):

```
pc → alto → translate → nlp → llm → TEITOK
```

Driven by [`.github/workflows/e2e-pipeline-smoke.yml`](../../.github/workflows/e2e-pipeline-smoke.yml)
with helpers in [`tools/e2e/`](../../tools/e2e/). Every job boundary is one cross-repo interface;
assertions check **formats and contracts, never model quality**.

The fixture is the workflow's `e2e-doc` input (atrium-project#69, roadmap S6). A manual dispatch offers
all five; push and schedule runs use `CTX000000003`. The other four are multi-page, and Stages 1
(page-classification) and 3 (translator) see **page 1 only** — the workflow renders and translates
`<id>-1` — while alto, nlp and llm see the whole document.

> ⚠️ **What a green run actually covers.** Each stage runs a *published image* (selected by the
> `image-tag` input) but mounts *source checked out with no `ref:`* — i.e. each tool repo's **default
> branch**, not the branch or tag the image was built from. The hub checkout is not pinned either:
> since 2026-09-11 it is the workflow's own commit, so the fixtures and `tools/e2e/` always come from
> the ref being run (it used to be pinned at `v1`, which let the workflow and its fixtures drift apart).
> So a run does **not** describe one coherent artifact, and this file previously claimed "all tool
> repos are checked out at the same ref (default `test`)", which was never true of the workflow as
> written. Treat a green run as "default-branch source is compatible with the `image-tag` runtime",
> and read the two together. Coupling `ref:` to `image-tag` (a `tool-ref` input) is the real fix and
> is filed separately — it is a behaviour change to what the gate means, not a doc correction.

## 📄 Contents & provenance

Each fixture is a pair: `ALTO/<id>.alto.xml` (the input) and `DOC_LINE_CATEG/<id>.csv` (the GPU
bridge, below). The three synthetic ALTO files are byte-identical to
`atrium-ocr-postprocess/data_samples/ALTO/` at `test` HEAD (the repository was `atrium-alto-postprocess` until 2026-10-01). **The CSVs are snapshots, not copies:**
they are in an older `CSV_HEADER` (40 columns; the two real scans 37) than alto's current
`data_samples/DOC_LINE_CATEG/` (42), which the downstream stages read by column name.

| Fixture        | Pages | ALTO lines | CSV rows | CSV columns | What it is                                                                                            |
|----------------|-------|------------|----------|-------------|-------------------------------------------------------------------------------------------------------|
| `CTX000000003` | 1     | 2          | 2        | 40          | 🇨🇿 **The default.** Synthetic calibration sample: *„Náčrt sondy."* + *„1998"*, ALTO v3, `LANG="cs"` |
| `CTX000000001` | 2     | 4          | 4        | 40          | synthetic, from alto's `data_samples/ALTO/`                                                           |
| `CTX000000002` | 4     | 10         | 9        | 40          | synthetic, from alto's `data_samples/ALTO/`                                                           |
| `CTX192100040` | 16    | 305        | 372      | 37          | a real scan                                                                                           |
| `CTX192601143` | 13    | 379        | 485      | 37          | a real scan                                                                                           |

There is **no committed page image** — the pc stage renders one from the ALTO at runtime
(`tools/e2e/render_alto_page.py`, page 1), keeping the whole smoke anchored to one fixture pair.

### 🌱 The AMČR seed (atrium-project#71)

By default the chain starts the way the AMČR pilot does: from a **seed**, the record the archive
writes before the first stage. The `Write the AMČR seed` step makes it at run time with
[`tools/e2e/make_seed.py`](../../tools/e2e/make_seed.py), so no seed is committed per fixture:

* `doc_id` is `AMCR-F-<id>`, unlike every file name in the chain, which is the AMČR situation
  (its file id is not the upload's name);
* `source.sha512` is the digest of the fixture's ALTO, standing in for the archive's digest of
  the original, with the file name and media type of that ALTO;
* there is no `source.origin`: the stage that reads the source records it.

`e2e_assert.py --seed` then fails any stage that changes the four values, or names the origin
without being the program that reads the source. The `seed` input set to false reproduces the
unseeded chain. A worked example of a seed is
[`fixtures/atrium_document.seed.example.json`](../atrium_document.seed.example.json).

After the assertions, the final record and every stage's paradata file are turned into the
record's RO-Crate fragment and checked by the RO-Crate validator, against RO-Crate 1.2 and Process
Run Crate 0.5 ([`tools/ci/rocrate_check.py`](../../tools/ci/rocrate_check.py)).

### 🏷️ No vocabulary fixture (unused since 2026-08-19)

`VOCAB/teater_nested_vocab.json` is still in this directory, but **no workflow, script or test reads it**
(checked 2026-09-29); delete it rather than start using it again. It used to be the vocabulary, on the stated grounds that "llm-enrich
intentionally ships no `data_samples` of its own". That stopped being true: llm-enrich now builds
and commits a union of the AMCR and TEATER thesauri under `data_samples/vocab/`, and the hub copy
silently became a snapshot of a file that no longer exists upstream.

Until 2026-10-01 Stage 5 checked out llm-enrich into `work/atrium-llm-enrich-main` and read
`data_samples/vocab/union_nested.json` straight out of that checkout. That stage is gone from the lane (the controlled keywords
move to keyword-extract, which will publish the vocabulary as a versioned CC0 release asset for the lane to read). A fixture the hub has to
re-copy by hand whenever another repo rebuilds its vocabulary is a drift source, and this one drifted
undetected until run [32208408456](https://github.com/ufal/atrium-project/actions/runs/32208408456)
— where a missing vocabulary caused a live AMCR harvest, a one-term category enum, and an
`enrichment` block that never got written.

Unlike the ALTO and CSV above, nothing here needs a *pinned* copy of the vocabulary: those two are
fixed inputs whose content the assertions depend on, whereas the vocabulary is a moving upstream
artifact the smoke test should track rather than freeze.

## 🌉 Why the DOC_LINE_CATEG bridge exists

alto-postprocess's classify stage (`classify_TEXT.py`, which replaced `langID_classify.py`) scores
perplexity on a GPU and **aborts** when CUDA is unavailable (`classify_TEXT.py:431-440`), because on CPU
it is ~100–400× slower. A GitHub-hosted runner has no GPU, so Stage 2 runs with `SKIP_CLASSIFY = true`
and the committed CSV stands in for that stage's output: Stage 4 (nlp-enrich) reads it through
`INPUT_TABLES_DIR`, and Stage 5 (llm-enrich) takes it as `--input`. The bridge goes away when the
classify stage has a GPU lane to run in (deferred with
[#40](https://github.com/ufal/atrium-project/issues/40)).
