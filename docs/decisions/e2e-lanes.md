# E2E lanes: decisions and history

> **Status:** decision record, added 2026-10-25 for [#81](https://github.com/ufal/atrium-project/issues/81)
> (B.1, workflow readability).
> **Scope:** the hub's two end-to-end lanes:
> [`e2e-pipeline-smoke.yml`](../../.github/workflows/e2e-pipeline-smoke.yml), the scanned-document
> chain, and [`e2e-digital-smoke.yml`](../../.github/workflows/e2e-digital-smoke.yml), the born-digital
> branch.

The workflows' comments say what each step does and which invariants it must keep. This page keeps
the reasoning and the incidents behind them. Each section quotes, verbatim, the comment that stood at
that place until 2026-10-25; sections follow each workflow's order. Dates, run numbers and "today" in
a quote are as of when it was written; the workflow is the authority on what holds now.

What each lane proves, and its gaps, is in the responsibility map of [`ci_policy.md`](../ci_policy.md);
the image side of both lanes is in [`docker-tool-reusable.md`](docker-tool-reusable.md).

## The scanned-document lane (e2e-pipeline-smoke.yml)

### What a pipeline run tests

The note above `concurrency:` (issue #10; corrected 2026-08-06). It explains why a run against
`latest` validates the last release, and why the default is still `latest`.

> WHAT THIS RUN IS ACTUALLY TESTING (issue #10)
>
> The stages below are PUBLISHED CONTAINER IMAGES, and `docker-tool.reusable.yml` moves
> `:latest` only on a version-tag push:
> `type=raw,value=latest,enable=${{ startsWith(github.ref, 'refs/tags/v') }}`
> A branch push publishes `sha-*` and `:test`, but never `:latest`.
>
> NOTE (corrected 2026-08-06): issue #10 added the `:test` TAG RULE, but until the
> `build-and-push` job gate was widened in the same round, that rule could never fire —
> the job ran only on `refs/tags/v*` or a `release` event, and `type=raw,value=test` is
> enabled only when `github.ref == 'refs/heads/test'`. The two conditions are mutually
> exclusive, so a branch push published NOTHING AT ALL, not even `sha-*` (that tag rule
> lives in the same job). Six green `test` pushes in llm-enrich on 2026-08-06 produced no
> image. The gate now includes `push` to `refs/heads/test`, which is what makes both this
> line and the `sha-<short>` claim below true.
>
> So with `image-tag: latest` this workflow validates THE LAST RELEASE of each tool, while
> being triggered by hub pushes and a cron. A defect it finds cannot be cleared by fixing
> the source: the owning repo has to cut a release before this can go green. That is not a
> flaw in the gate — it is the gate correctly reporting what is deployed — but it must be
> read that way, or a red run looks like "the pipeline is broken" when it means "the
> released images are older than the fix".
>
> Demonstrated 2026-08-06 (run 31075185518): the schema gate rejected
> `entities[].type_cnec: null` from nlp-enrich. The fix was already on `test`; `:latest`
> still pointed at the pre-fix v0.18.2, so no source change could have greened the run.
>
> Pass `image-tag: test` (workflow_dispatch) to validate what is about to be released
> instead. Flipping the DEFAULT to `test` is deliberately not done here: `:test` starts
> being published only once each repo has pushed a branch commit under the issue #10
> docker-tool change, so the tag does not exist for every repo yet. Flip it once
> `docker pull ghcr.io/ufal/atrium-<tool>:test` succeeds for every tool.

### Fixture choice

Above the workflow `env:` (W3; roadmap S6, atrium-project#69).

> W3's parameterised E2E (roadmap S6, atrium-project#69): five fixture pairs exist and
> one was ever used. Push and schedule runs have no inputs, so they keep CTX000000003.

### Hub checkout

Above "Checkout ATRIUM Hub Repository": why the lane uses the default checkout and not `v1`
(changed 2026-09-11; the born-digital lane changed on 2026-08-18, see
[its section](#hub-checkout-born-digital-lane)).

> NOT `repository: ufal/atrium-project` + `ref: v1`, which is what this step did
> until 2026-09-11 — the same defect e2e-digital-smoke.yml removed on 2026-08-18
> and recorded at length above its own checkout. This workflow LIVES in the hub,
> so the default checkout already gives the hub AT THE COMMIT BEING TESTED.
> Pinning it meant the workflow file came from the ref being run while
> `fixtures/e2e/` and `tools/e2e/e2e_assert.py` came from wherever `v1` pointed:
> a self-referencing checkout validated by tooling other than the tooling that
> ships with it, which is exactly what a smoke test must not do.
>
> It failed loudly once the `v1` tag was deleted (run 34591132140 — the fetch of
> `+refs/tags/v1*` matched nothing and checkout exited 1). That is the good
> outcome: a latent version skew surfaced as a hard error instead of quietly
> asserting today's pipeline against a tag's fixtures.
>
> Same reasoning codeql.yml and pre-commit.yml already record for preferring
> `uses: ./…` over `@v1`.

### TEITOK output

Above "Write nlp-enrich e2e config" (2026-09-23).

> SAVE_TEITOK=true (2026-09-23): the fixtures README advertises "... -> TEITOK", and
> the record's pages[].teitok_surface / entities[].teitok_ref are ids INSIDE that file,
> so with it off the lane checked references to a file nobody wrote. nlp-enrich's
> stats stage validates its own XSD before it finishes; the assert step below checks
> that the file and the record agree (--teitok-dir).

### Hugging Face model cache

Above "Cache HuggingFace models (Stage 1)" (2026-08-06), and on the `HF_TOKEN` of Stage 1.

> ── HuggingFace model cache (2026-08-06) ────────────────────────────────
> Stage 1 pulled `timm/regnety_160.swag_ft_in1k` from the Hub on EVERY run,
> anonymously and with no cache, and started failing on it:
>
> ```text
>   429 Client Error: Too Many Requests for
>   https://huggingface.co/timm/regnety_160.swag_ft_in1k/resolve/main/config.json
>   -> OSError: We couldn't connect to 'https://huggingface.co' ... and couldn't
>      find them in the cached files.
> ```
>
> (run 31116677390). Anonymous Hub requests share a low rate limit, and this
> workflow runs on push plus a 3-daily cron in a repo that also runs other
> model-pulling jobs — so the limit is reachable through ordinary use, not
> abuse. It surfaces as an OSError deep inside transformers, which reads like a
> broken image rather than a throttle; that misdirection is half the cost.
>
> Two independent mitigations, because either alone can still fail:
>   * the cache means a WARM run makes no Hub request at all;
>   * HF_TOKEN (optional) raises the limit when the cache misses — a new model,
>     or the 7-day eviction of an unused GitHub cache entry.
>
> The pc image declares HF_HOME=/cache/huggingface and runs as uid 10001, so the
> host directory is mounted there and made writable before the container starts.

> Optional. Absent -> anonymous, which is what hit the 429; present -> a much
> higher limit. Add an HF_TOKEN repository secret to harden this further.

### Stage 2: ocr-postprocess

Above "Stage 2 - OCR Postprocess": the removed `/bin/sh -c` shim (roadmap B9; #50, #62) and the
removed source checkout (#77 D).

> (B9 / #50, #62) Runs the image AS BUILT: no entrypoint override, and nothing
> fetched or installed at run time. This step used to wrap the stage in a
> `/bin/sh -c` shim that pulled `alto-tools` from a moving
> `refs/heads/master.zip` INSIDE the already-published image — overriding that
> image's own commit pin at the moment of testing it, so whatever the lane
> proved, it was not a property of the artefact we ship.
> ocr-postprocess (named alto-postprocess until 2026-10-01) vendored the two alto-tools code paths it used (its
> `alto_tools.py`, Apache-2.0), so there is nothing left to fetch and no `PATH`
> to re-export. `ENTRYPOINT ["python", "run_pipeline.py"]` (its Dockerfile,
> stage `base` — the unsuffixed tag pulled here) now runs the stage, with the
> arguments below appended to it, as in Stage 1.
>
> The image's own WORKDIR (/app) and code run (#77 D): no source checkout, no `-w`.
> Every path the stage reads or writes is absolute under /workspace (the config above).

### Stages 3 and 4 entrypoints

Above "Stage 3 - Translator": the removed entrypoint overrides (B9, #62).

> (B9 / #62) Stages 3 and 4 (and the former stage 5) each used to replace the image's entrypoint with a
> command BYTE-IDENTICAL IN EFFECT to the entrypoint it replaced. Three exact
> no-ops: they cost nothing at runtime and everything in assurance, because the
> lane then reported that it never exercised a real entrypoint -- while silently
> doing so in all three cases. Deleting them changes no behaviour and makes the
> lane honest about what it tests. Stage 1 has always had this shape.
>
> ```text
>   stage 3  translator  ENTRYPOINT ["python", "main.py"]          (base)
>   stage 4  nlp-enrich  ENTRYPOINT ["python", "run_pipeline.py"]  (base)
> ```
>
> SAFE AGAINST `:latest`, NOT JUST `test`. This lane defaults to the RELEASED
> image set (see the header note), so the deletions are only sound if the
> PUBLISHED images carry those entrypoints. Checked at each repo's newest release
> tag before landing: translator v0.10.5 and nlp-enrich v0.20.1 -- both declare exactly the
> lines above. (The former stage 5 is gone: see "Keyword Extract" below.)
>
> THE TRAP, and the one way to get this wrong: with the interpreter forced as the
> entrypoint, `main.py` was argv[1] TO PYTHON. Without it, ENTRYPOINT already
> supplies the script, so leaving `main.py` here would pass it as an argument TO
> main.py. Stages 3 and 4 therefore drop the script name along with the override;
> None of this is visible to YAML linting -- only to a run.
>
> The relative script names in those entrypoints resolve from the image's own
> WORKDIR (/app): the lane runs the code the image carries, not a checkout of the
> repository's default branch (#77 D; it used to pass `-w` into such a checkout, so a
> change that never reached the image still passed).
>
> tests/test_e2e_entrypoints.py is what stops a silent override returning.

### Keyword extract, statistical kind

Above "Keyword Extract (statistical kind)" (atrium-keyword-extract#1; atrium-project#73).

> ── Keyword Extract (atrium-keyword-extract#1) ───────────────────────────────────────
> Both keyword kinds moved out of nlp-enrich and llm-enrich into keyword-extract, whose one
> service is `POST /extract_keywords`. nlp-enrich's Stage 4 above no longer extracts
> keywords (`--stages manifest udp nt stats`), so this step is where the statistical kind
> is exercised: the production image, run as built (no entrypoint override), is handed the
> record Stage 4 wrote and must answer with keywords carrying a method and a score.
>
> Since keyword-extract v1.2.0-beta the statistical kind writes the record's `keywords`
> block (atrium-project#73), so the record it returns is `5_kw_stat.json`, the controlled
> step's input. An older image answers without the record: a warning, decided by the
> image's own /info version, so a newer image that drops the record fails. YAKE is
> requested here because KeyBERT would pull a sentence-transformers model from the Hub on
> every run (the 429 documented above): an explicit test choice, not the service default.
>
> The image is published from keyword-extract's first release (`latest`) or its first
> `test` push. Until then a missing image is a warning, and an error on the scheduled run,
> which is what is there to notice a stage that never got an image.

### Keyword extract, controlled kind

Above "Keyword Extract (controlled kind, OpenRouter)" (atrium-keyword-extract#1, #2).

> ── Keyword Extract, the controlled kind (atrium-keyword-extract#1, #2) ─────────────────
> The same production image, started with an LLM backend: the record after the statistical
> kind (`5_kw_stat.json`, or Stage 4's when the image predates it) goes in, and the record
> with keyword-extract's `enrichment` block (and `entities[].pid`) beside `keywords` comes out
> as `5_kw.json`. This is the one step of the lane that calls a paid, third-party model, so:
>   * it needs the OPENROUTER_KEY secret; without it the step is skipped with a warning, and
>     with an error on the scheduled run, which is there to notice a check that stopped;
>   * it makes one call per line the service sends, so it runs only on records of at most
>     E2E_CONTROLLED_MAX_LINES such lines (the two multi-page fixtures have hundreds);
>   * the model is `openrouter-model` (default openai/gpt-4o-mini). What it answers is
>     reported, not asserted: provider drift must not flap the gate. What is asserted is the
>     contract: the backend started, the call succeeded, the block is stamped by
>     keyword-extract, and the response's CreateAction is the stamp's run (atrium-project#71).
> keyword-extract's own live lane (controlled-live.yml) runs the same kind against a fixed
> record; this one is what proves it on the record the rest of the chain produced.

### Lane failure issue

Above "Open or update the lane's issue on scheduled failure" (atrium-project#81).

> One open issue per ongoing breakage, commented on each recurrence (atrium-project#81):
> the step used to open a new issue on every failing run, every third day.

## The born-digital lane (e2e-digital-smoke.yml)

### Why a separate lane

The file header (W10, issue #10), first part: why the born-digital branch cannot be a stage of the
scanned lane, and where the semantic stage went (2026-10-01, atrium-keyword-extract#1).

> atrium-project — E2E smoke for the BORN-DIGITAL branch (W10, issue #10 tail).
>
>     digital-convert
>
> One stage. This is a SIBLING of e2e-pipeline-smoke.yml, not a stage bolted onto it, and the
> data flow is what forces that — every scanned stage is structurally unreachable from a
> born-digital record:
>
> ```text
>   pc          needs a page image; a born-digital PDF has none, and no raster step
>               exists to make one.
>   ocr         MUST NOT run. atrium_document's `_assert_origin_consistent()`
>               refuses every positional `pages`/`lines` write against a record whose
>               `source.origin` is `digital-born-*`, pinned by
>               `test_without_needs_ocr_alto_is_still_refused`. Chaining ocr-postprocess
>               here would assert that the ownership rule is broken. (The one write it
>               lets through is a scoring-only merge of `SCORING_FIELDS`, ocr-postprocess's
>               `POST /score_record` — atrium-digital-convert#4 W3 — which adds no rows.)
>   translator  needs `PAGE_ALTO/`, which is ocr-postprocess's split output.
>   nlp         needs the DOC_LINE_CATEG classify CSV *and* `INPUT_ALTO_DIR`.
> ```
>
> The semantic stage that used to follow the converter here (llm-enrich's `/extract_keywords`
> over the record) moved with all keyword extraction to keyword-extract on 2026-10-01
> (atrium-keyword-extract#1). Its controlled kind joins this branch as a second stage when it
> ships there, reading the converter's record exactly as the old step did.
>
> `digital-convert` is this branch's ORIGINATOR — like page-classification on the
> scanned branch, it takes no `--document-json` baseline, it creates the record.

### What only this lane covers

The header, continued: the §1a arbitration, digital-convert#18 (Cases 4-6) and the service (Case 7,
atrium-digital-convert#2 H.1).

> ── What this covers that nothing else does ─────────────────────────────────────
> The §1a arbitration. A born-digital record normally locks ocr-postprocess (named
> alto-postprocess until 2026-10-01) out of `pages`/`lines` entirely; the ONE thing that
> re-authorises it is the converter setting `needs_ocr: true` — "there is a text layer here
> and I do not trust it". That handoff is the whole reason two originators can coexist, and
> until this workflow it was covered only by unit tests inside a single repo. Case 2 below
> asserts it against a real published image.
>
> ── And what digital-convert#18 added (Cases 4-6) ───────────────────────────────
> The converter stopped flattening: DOCX pages, headings, running headers/footers and
> footnotes in `lines[].style`, tables joined to their lines, two-column PDFs in
> reading order, and a PDF whose text layer is a prior OCR run refused (exit 3) rather
> than recorded as born-digital. Cases 4-6 smoke those through the published image.
> They run only when BOTH halves carry #18 — the generator that makes the fixtures and
> the image that converts them — because the two come from different places (below).
>
> ── And the service (Case 7, atrium-digital-convert#2 H.1) ──────────────────────
> Cases 1-6 run the `-digital` CLI image. The AMČR route calls the `-api` image's
> `POST /reformat`, so Case 7 asserts the contract once more through the service: the
> seed's identity, the run's CreateAction (atrium-project#71 R2), the `needs_ocr` /
> `text_layer` verdict, and the two refusals the route acts on (422
> `source_digest_mismatch`, 422 `ocr_text_layer`).

### Generated fixtures and sequencing

The header, end: the fixture generator, and when the images exist (the repository was created on
2026-10-01, atrium-project#72).

> ── Fixtures are GENERATED, never committed ─────────────────────────────────────
> `atrium-digital-convert/tests/fixtures/digital/make_fixtures.py` is a deterministic,
> pure-stdlib PDF/DOCX generator with sha256-pinned outputs — same design as this
> repo's own `tools/e2e/render_alto_page.py`, and it needs no Pillow, reportlab or
> pypdf. `--manifest` is pointed at the work dir on purpose: the generator REWRITES
> its manifest by default, and writing into a checkout mid-run is exactly the
> tree-mutation the docker reusable's `assert-clean-tree` now fails on.
>
> ── Sequencing ──────────────────────────────────────────────────────────────────
> The repository was created on 2026-10-01 (atrium-project#72), and its images are published
> under its own name: `ghcr.io/ufal/atrium-digital-convert-digital`. Until its first `test`
> push or release there is no image at any tag, and the preflight says `MISSING` rather than
> dying on a `denied` from the daemon. The predecessor's `atrium-llm-enrich-digital` images
> stay where they are for consumers pinned to them, and are no longer tested here.
>
> The `:test` channel moves on a push to the `test` branch (the `build-and-push` gate at `v1`
> of docker-tool.reusable.yml); `:latest` moves only on a release tag.

### Schedule

On the `cron:` of the schedule.

> 06:00, clear of e2e-pipeline-smoke.yml (02:00) and all-repos-smoke.yml (04:00).
> Three heavy jobs on one cron contend for runners and interleave three unrelated
> failure reports into one digest window.

### Image channel by event

Above `IMAGE_TAG` in the workflow `env:` (2026-08-18).

> Channel by EVENT, not one flat default (2026-08-18).
>
> `inputs.image-tag` is empty on every non-dispatch event, so `|| 'latest'`
> meant a PUSH smoked the RELEASED image. For `-digital` that is a guaranteed
> red — `:latest` exists only once a release tag carrying the digital build
> target is cut — and this workflow's own file is on the `paths` filter above.
> So every edit to this file re-ran it against an artifact the edit could not
> possibly have produced. Run 32130934621 is precisely that: a push of the
> workflow's own repair, failing on a missing release image.
>
>   push      -> `test`. A code push asks "does what we are about to release
>                still hold?", which is the pre-release channel's whole job.
>   schedule  -> `latest`. The nightly's job is the opposite question: does the
>                artifact consumers actually pull still work?
>   dispatch  -> whatever was chosen.

### Hub checkout, born-digital lane

Above "Checkout hub (fixtures, assert script)": why the lane uses the default checkout and not `v1`
(changed 2026-08-18).

> NOT `repository: ufal/atrium-project` + `ref: v1`, which is what this
> step did until 2026-08-18. This workflow LIVES in the hub, so the default
> checkout already gives the hub — pinning it to `v1` meant the workflow file
> came from the ref being run while `tools/e2e/e2e_assert.py` came from a tag
> cut 2026-08-06, and the two had already diverged:
>
>   `git show v1:tools/e2e/e2e_assert.py | grep -c expect-needs-ocr`  ->  0
>
> `--expect-needs-ocr` does not exist at v1, so the "Assert the needs_ocr
> handoff" step below would have died on `unrecognized arguments` the moment
> the image problem in front of it was cleared. v1 does not contain this
> workflow file at all, which is the tell: a self-referencing checkout pinned
> to a tag that predates the thing doing the checking.
>
> Same reasoning codeql.yml and pre-commit.yml already record for using
> `uses: ./…` over `@v1` — a ref being tested must be validated by the tooling
> that ships with it.

### Fixture generator checkout

Above "Checkout atrium-digital-convert (fixture generator only)".

> digital-convert is checked out ONLY for its fixture generator. The converter
> itself runs from the published image, which is the thing under test.
>
> The ref follows the image CHANNEL: `:test` is built from digital-convert's `test`
> branch, so the generator comes from there too. Every other channel takes the default
> branch, which is NOT the same thing as `:latest` — `:latest` moves only on a release
> tag, and the default branch can run ahead of it. That gap is why Cases 4-6 below also
> probe the image instead of trusting the fixture list; an empty ref is the checkout
> action's default branch.

### GHCR login

Above "Log in to GHCR".

> `packages: read` has been granted by this job since it was written, and
> nothing ever used it — every step went straight to `docker run`, which for
> an unauthenticated daemon can only reach PUBLIC packages. The other four
> ATRIUM images are public, so the sibling smokes get away with it; a GHCR
> package is PRIVATE on creation, so the first pull of a newly published
> image fails with `denied` no matter who is asking.

### Preflight

Above "Preflight - confirm the images exist at the requested tag", and the failed run that prompted it.

> ── Preflight: is there anything to test? ────────────────────────────────
> Run 31930694882 failed as:
>
> ```text
>   docker: Error response from daemon: Head
>   "https://ghcr.io/v2/ufal/atrium-llm-enrich-digital/manifests/latest": denied
>   (the predecessor's package; the same applies to atrium-digital-convert-digital)
> ```
>
> which reads as a permissions problem and is not one. At the time `-digital`
> had never been published at ANY tag, for two independent reasons (both
> resolved since, and kept here because they are what a MISSING below means):
>
>   * `:latest` moves only on `refs/tags/v*` (docker-tool.reusable.yml,
>     `type=raw,value=latest,enable=${{ startsWith(github.ref, 'refs/tags/v') }}`).
>     The `digital` build target was added to llm-enrich's docker.yml in
>     57d8073 (2026-08-06), after the then-newest tag v0.5.2. Every llm-enrich
>     release from v0.6.0 (2026-08-19) on carries it, so `-digital:latest` exists.
>   * The `:test` channel needed the `build-and-push` gate that admits `push` to
>     `refs/heads/test` to be at the `v1` tag the tool repos call. It is at `v1`
>     now; before that move a `test` push published nothing at all.
>
> So a MISSING here means: no release (for `latest`) or no `test` push since the
> gate reached `v1` (for `test`), or a package visibility problem (below).
> Failing here, by name, beats failing four steps later on a daemon error that
> names the wrong cause.

### Case 3: enrichable content

Above "Stage D1c - digital-convert (enrichable content)" (issue #49).

> ── Case 3: a record the semantic stage can actually read ───────────────
> enrichable.pdf — one page of diacritic-free Czech archaeological prose.
>
> This case exists because of run 34090340995 (issue #49). The semantic stage that used to
> follow the converter (now keyword-extract's controlled kind) was fed
> `minimal.document.json`, and minimal.pdf reads "Excavation report, block one,
> line one." — placeholder text chosen to make BLOCK BOUNDARIES reviewable, carrying
> no site, find, method, period or material. the LLM stage's own document-level prompt
> tells the model "If the document has no archaeologically relevant passages, return
> an empty items list", so `records enriched: 0` was the model obeying it. The smoke
> was asserting a semantic outcome against a fixture built to pin bboxes, and the
> failure it reported ("'enrichment' block missing") named neither cause.
>
> minimal.pdf keeps its two jobs from Case 1 and is deliberately NOT rewritten: its
> bytes are a geometry golden, and one fixture serving both a geometry and a semantic
> contract is how the two got confused. Asserting the born-digital contract on this
> record before D2 also proves the new fixture is a clean born-digital input rather
> than something D2's result could be blamed on later.

### Cases 4 to 6

Above "Probe the converter for the digital-convert#18 contract".

> ── Cases 4-6: the digital-convert#18 layout and refusal contract ─────────────
> Two things must both be true, and they come from different places:
>
>   * the IMAGE converts them — probed from its own `--help`, because `--engine`
>     arrived with #18 and a tag name says nothing about what is inside it;
>   * the GENERATOR made the fixtures — rich.docx, two_column.pdf and ocr_layer.pdf
>     exist only from digital-convert c3575f5 on.
>
> Either one missing SKIPS the case with a notice rather than failing: the nightly
> on `:latest` = v0.7.0 has the new generator (default branch) and the old image,
> and asserting #18 against a release that predates it would be red for a reason no
> commit could fix. Once a release carries #18, the probe turns the cases on by
> itself — nothing here needs editing.

### Lane failure issue, born-digital lane

Above "Open or update the lane's issue on scheduled failure" (2026-08-18; atrium-project#81).

> De-duplicated as of 2026-08-18, and since atrium-project#81 through the shared action
> every scheduled lane uses: one open issue per ongoing breakage, commented on each
> recurrence. The legacy marker keeps an issue this step opened before the move.
