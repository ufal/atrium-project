# Release trust: the recorded states and the release-gate rollout

> **In short.** Dated records moved out of `release_trust.md` and `ci_policy.md` on 2026-11-21: what the rulesets,
> releases and hub pins were on 29 October, 4 November and 6 November 2026; the tags that no release certifies; how
> the release gate was rolled out in October 2026; and the Trivy database incidents. The rules themselves are in
> [`../release_trust.md`](../release_trust.md) and [`../ci_policy.md`](../ci_policy.md). Nothing here describes the
> current state: read that with `python3 scripts/release_trust.py status`.

## The release-gate rollout (October 2026)

- **Rollout:** digital-convert first: `v1.2.2-beta` (10-22) was released this way. Its two dispatched dry runs
  of 10-25 are the demonstration: one with a simulated probe failure (`simulate-probe-failure`), which ended
  at the probe with nothing pushed or released
  ([run](https://github.com/ufal/atrium-digital-convert/actions/runs/40215852852)), and one clean
  ([run](https://github.com/ufal/atrium-digital-convert/actions/runs/40215872101)). The other five were
  checked on their first gated tags instead of dry runs (the maintainer's decision of 10-26): nlp-enrich
  `v1.2.0-beta` (10-26), page-classification, ocr-postprocess and keyword-extract (10-27), the translator
  (10-28). All six pilot releases of 29 October carry `images.json`.
- **What a published image does not promise:** steps that run after the images are promoted (the release
  bundle, the vocabulary stamps) can still fail. The version then has published images but no GitHub
  Release, and it is not a release: use a version only when its GitHub Release exists and names the
  digest. Between 26 and 28 October, tags in four repositories ended this way (page-classification
  `v1.10.0`–`v1.10.4`, ocr-postprocess `v1.13.0`, keyword-extract `v1.5.0`, translator `v1.6.0`). Each
  cause now fails on every push (#72), and the fix of a release is a new patch version, never a moved tag.

Before the gate, a release and its image ran independently: four releases of October 2026 had no
image, or an image no release described (#81, 10-20). One was page-classification `v1.9.6-beta`, whose
images the CVE gate stopped after the release was published.

## Trivy database failures (October and November 2026)

A scan that fails before it scans, because Trivy cannot download its vulnerability database, is not a finding:
on 2026-10-26 `mirror.gcr.io` answered 404 for the database layer and three weekly scans failed in the same
four minutes. Trivy moves on to its second registry only on a 429 or 5xx answer, so the registry list did not
prevent it. Since `b07090f` (10-29) both report-only scans, the release job's and the weekly one, retry the
download once from `ghcr.io` alone, and the CVE release gate reads the database already on disk
([Trivy DB retry](docker-tool-reusable.md#trivy-db-retry)). An outage of both registries still
fails the job, and that run is re-run once. The weekly scans of 2 November are the retry's first scheduled
run. On 2026-11-04 two release jobs failed the same way in other places: Trivy's own download (exit 6, translator)
and the CVE gate's pull of an image layer (keyword-extract `llm`). Since then the scan's retry waits 30 s, and the
gate runs once more after 30 s; the gate's retry is blocking, so a fixable CRITICAL fails both.

## State on 2026-11-06

The five releases of 11-06 (#66) change only the batch image's entry point (the hub-canonical
`container_entrypoint.py`) and the version stamps; page-classification stays at `v1.12.3-beta`. Every caller and
`hub-ref` in the six tool repositories is pinned to `da7a066` (`v1`). No repository has a branch ruleset or branch
protection, and the hub has no ruleset at all (`GET /repos/ufal/atrium-project/rulesets` returns `[]`).

| Repository          | Tag ruleset on `v*` | Latest release, immutable, with `images.json` | Hub references by commit (`da7a066`) |
|---------------------|---------------------|-----------------------------------------------|--------------------------------------|
| page-classification | yes                 | yes (`v1.12.3-beta`, 11-04)                   | all callers and action steps         |
| ocr-postprocess     | yes                 | yes (`v1.15.4-beta`)                          | all                                  |
| digital-convert     | yes                 | yes (`v1.4.5-beta`)                           | all                                  |
| nlp-enrich          | yes                 | yes (`v1.3.4-beta`)                           | all                                  |
| keyword-extract     | yes                 | yes (`v1.6.5-beta`)                           | all                                  |
| translator          | yes                 | yes (`v1.7.8-beta`)                           | all                                  |
| hub                 | `doc-schema-v*`: no | —                                             | —                                    |

The pilot set on [#77](https://github.com/ufal/atrium-project/issues/77) is the 11-04 one below.

## State on 2026-11-04

Read on 11-04 with the public API (the pilot releases' `immutable` flag and assets) and the `test` trees (the
callers). These are the six pilot releases, final on [#77](https://github.com/ufal/atrium-project/issues/77). The
callers' column assumes the 11-04 pin sweep of page-classification, ocr-postprocess and nlp-enrich to `51aad6c`
(`v1`); the other three were pinned there with their releases.

| Repository          | Tag ruleset on `v*` | Pilot release, immutable, with `images.json` | Hub references by commit (`51aad6c`) |
|---------------------|---------------------|----------------------------------------------|--------------------------------------|
| page-classification | yes                 | yes (`v1.12.3-beta`)                         | 8 of 8 callers, 1 of 1 action steps  |
| ocr-postprocess     | yes                 | yes (`v1.15.3-beta`)                         | 8 of 8, 1 of 1                       |
| digital-convert     | yes                 | yes (`v1.4.4-beta`)                          | 8 of 8, 1 of 1                       |
| nlp-enrich          | yes                 | yes (`v1.3.3-beta`)                          | 8 of 8, 2 of 2                       |
| keyword-extract     | yes                 | yes (`v1.6.4-beta`)                          | 8 of 8, 3 of 3                       |
| translator          | yes                 | yes (`v1.7.5-beta`)                          | 8 of 8, 2 of 2                       |

**Tags without a release.** Seven `v*` tags of the pilot round exist that no GitHub Release certifies, and by
`ci_policy.md` they are not releases (older tags without a release, such as page-classification
`v1.10.0-beta`–`v1.10.4-beta` or the `v0.*` history, predate immutable releases and are not listed):
- digital-convert `v1.4.3-beta`: its tag push started no workflow run;
- keyword-extract `v1.6.3.-beta`: a mistyped tag, which started no run;
- keyword-extract `v1.6.3-beta`: its CVE gate stopped on a registry error;
- translator `v1.7.3-beta`: Trivy's own download failed;
- translator `v1.7.4-beta`: its tag push started no workflow run.
- translator `v1.7.6-beta` (11-05): created on `5b25f83`, the commit before its version bump, and pushed
  with that commit; Release Bundle 42103826703 stopped at the version gate (tag 1.7.6, CITATION 1.7.5).
  `v1.7.8-beta` carries it ([Tagging a release](../release_trust.md#tagging-a-release)).
- translator `v1.7.7-beta` (11-06): tagged on `ec694d3`, three minutes after Docker Build & Push had failed there
  on a leftover test; Release Bundle 42200410454 stopped in the same test job. `v1.7.8-beta` carries it.

The next patch number shipped the same code each time. Some of their images were published before the failure
(translator's `:latest` pointed at the `1.7.3-beta` image until `v1.7.5-beta` replaced it on 11-04). The tag rule
refuses their deletion to everyone: its bypass list is empty, so an admin would have to disable it first, which the
organisation's audit log records.

## State on 2026-10-29

Read with the public API and the `test` trees (no admin rights needed): the rulesets with
`GET /repos/ufal/<repo>/rulesets`, the releases' `immutable` flag, and the callers in each
`.github/workflows/`. The four rulesets stranak added on 10-29 (10:18–10:19 UTC,
[#72](https://github.com/ufal/atrium-project/issues/72)) came before that day's six tags, so every pilot
release is covered. The callers' column is the pin sweep of 10-29 (12:15–12:17 UTC): every caller and
action step at the hub commit `b07090f` (`v1` then), with `require-sha-pins` on; no reference to `@v1` is
left.

| Repository          | Tag ruleset on `v*`                  | Latest release immutable, with `images.json` | Hub references by commit (`b07090f`) |
|---------------------|--------------------------------------|----------------------------------------------|--------------------------------------|
| page-classification | yes (`Protect v* Tags`, 10-19)       | yes (`v1.12.0-beta`)                         | 8 of 8 callers, 1 of 1 action steps  |
| ocr-postprocess     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.15.0-beta`)                         | 8 of 8, 1 of 1                       |
| digital-convert     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.4.0-beta`)                          | 8 of 8, 1 of 1                       |
| nlp-enrich          | yes (`Protect v* Tags`, 10-19)       | yes (`v1.3.0-beta`)                          | 8 of 8, 2 of 2                       |
| keyword-extract     | yes (`Protect v* Tags`, 10-29)       | yes (`v1.6.0-beta`)                          | 8 of 8, 3 of 3                       |
| translator          | yes (`Protect v* Tags`, 10-29)       | yes (`v1.7.0-beta`)                          | 8 of 8, 2 of 2                       |
| hub                 | `doc-schema-v*`: **no**              | —                                            | —                                    |

An action step is a step that runs one of the hub's composite actions
(`ufal/atrium-project/.github/actions/lane-failure-issue`, #81); step 7 pins it with the callers.

Releases from before immutability was switched on stay mutable (page-classification up to
`v1.9.4-beta`, nlp-enrich up to `v1.1.0-beta`, translator up to `v1.4.0-beta`); AMČR mirrors only
the immutable ones. The six hand-made rulesets refuse update, deletion and non-fast-forward on
`refs/tags/v*`, so `tag-rules` keeps them and updates them in place.
