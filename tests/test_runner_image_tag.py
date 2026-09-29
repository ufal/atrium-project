"""The image a build records in paradata is a tag the build publishes (roadmap B3, #69).

WHY THIS EXISTS. `docker-tool.reusable.yml` publishes `type=semver,pattern={{version}}`,
which strips the leading `v`: tag `v1.7.3-beta` becomes `ghcr.io/...:1.7.3-beta`. The
`ATRIUM_RUNNER_IMAGE` build arg was `:${{ github.ref_name }}`, i.e. `v1.7.3-beta`, so
every released image told its paradata it was a tag that does not exist in GHCR. On
2026-09-29 that held for the newest release of all five tools (alto `v1.6.0-beta`, pc
`v1.8.0-beta`, translator `v1.2.2-beta`, nlp `v0.22.0`, llm `v0.8.0`: GHCR carries
each without the `v`). #67 R2 names this image as every `CreateAction`'s `instrument`,
so the wrong name would have become part of the AMČR record.

The fix takes the tag from the step that computes it. These tests hold three properties
that nothing else would notice drifting:

  1. the build arg is derived from the metadata steps, not from `github.ref_name`;
  2. the step it reads exists and still emits the semver (without the `v`) and `test`;
  3. `ATRIUM_RUNNER_REF` keeps `github.ref_name` -- a git ref, where the `v` is right.

Parsed, not grepped: the comment above the build args quotes the old expression on
purpose, and PyYAML drops comments.

Run: pytest tests/test_runner_image_tag.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

_HUB_ROOT = Path(__file__).resolve().parents[1]
_DOCKER_TOOL = _HUB_ROOT / ".github" / "workflows" / "docker-tool.reusable.yml"


def _publish_steps() -> dict[str, dict]:
    doc = yaml.safe_load(_DOCKER_TOOL.read_text(encoding="utf-8"))
    steps = doc["jobs"]["build-and-push"]["steps"]
    return {step.get("id") or step.get("name"): step for step in steps}


def _build_args() -> dict[str, str]:
    raw = _publish_steps()["build"]["with"]["build-args"]
    args = {}
    for line in raw.strip().splitlines():
        key, _, value = line.strip().partition("=")
        args[key] = value
    return args


def test_runner_image_is_not_the_git_ref():
    image = _build_args()["ATRIUM_RUNNER_IMAGE"]
    assert "github.ref_name" not in image, (
        f"ATRIUM_RUNNER_IMAGE is {image!r}: `github.ref_name` keeps the tag's `v`, but GHCR "
        "carries the semver without it, so paradata would name an image that does not exist "
        "(roadmap B3)."
    )


def test_runner_image_reads_the_metadata_that_publishes_the_tag():
    image = _build_args()["ATRIUM_RUNNER_IMAGE"]
    assert "steps.meta-release.outputs.version" in image, image
    # With no release tag the only published name is the immutable sha-<short>.
    assert "steps.meta-immutable.outputs.version" in image, image


def test_the_metadata_still_emits_the_semver_and_test_channel():
    """If the tag rules move, the build arg silently follows them -- so pin them here."""
    steps = _publish_steps()
    release_tags = steps["meta-release"]["with"]["tags"]
    assert "type=semver,pattern={{version}}" in release_tags
    assert "type=raw,value=test" in release_tags
    assert "type=sha" in steps["meta-immutable"]["with"]["tags"]


def test_runner_ref_keeps_the_git_ref():
    assert _build_args()["ATRIUM_RUNNER_REF"] == "${{ github.ref_name }}"
