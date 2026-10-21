"""tests/test_k8s_handover.py — the S2 handover runbook stays executable (issue #77).

`docs/k8s_acceptance_runbook.md` is an acceptance artifact: its commands are copied and run by
AMČR operators, so a gap in it shows up as a wrong result on their cluster, not as a red build
here. These checks catch the defects of the 10-20 review before they recur:

* a service missing from the smoke requests or the results table (digital-convert was);
* a `curl` that can exit 0 on an HTTP error (no `--fail-with-body`, no printed status);
* a `port-forward` to an object the reference manifest does not create (its Service was
  commented out);
* an image tag with the source tag's leading `v` (`:v1.2.0` is never published).

HUB-LOCAL, NOT VENDORED: both files are hub documents.

Run: pytest tests/test_k8s_handover.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = REPO_ROOT / "docs" / "k8s_acceptance_runbook.md"
MANIFEST = REPO_ROOT / "docs" / "templates" / "k8s" / "atrium-service.deployment.yaml"
DEPLOYMENT_DOC = REPO_ROOT / "docs" / "k8s_deployment.md"

SERVICES = (
    "page-classification",
    "ocr-postprocess",
    "translator",
    "nlp-enrich",
    "keyword-extract",
    "digital-convert",
)


def _section(text: str, heading: str) -> str:
    """The body of the level-2 `## heading` section, up to the next level-2 heading."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"{RUNBOOK.name} lost its '## {heading}' section"
    return match.group(1)


def _shell_lines(text: str) -> list[str]:
    """The lines inside ```bash fences, with backslash continuations joined."""
    lines: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
        joined = re.sub(r"\\\n\s*", " ", block)
        lines.extend(line.strip() for line in joined.splitlines() if line.strip())
    return lines


@pytest.fixture(scope="module")
def runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


@pytest.mark.parametrize("service", SERVICES)
def test_every_service_has_a_smoke_request(runbook, service):
    smoke = _section(runbook, "Per-service smoke request")
    assert re.search(rf"^# {re.escape(service)}:", smoke, re.MULTILINE), (
        f"no smoke request for {service} in §'Per-service smoke request'"
    )


@pytest.mark.parametrize("service", SERVICES)
def test_every_service_has_a_results_row(runbook, service):
    results = _section(runbook, "Results (fill in)")
    assert re.search(rf"^\|\s*{re.escape(service)}\s*\|", results, re.MULTILINE), (
        f"no row for {service} in §'Results (fill in)'"
    )


def test_every_curl_reports_http_failure(runbook):
    """A `curl` passes on an HTTP error unless it fails on one or prints the status it got."""
    silent = [
        line
        for line in _shell_lines(runbook)
        if re.search(r"\bcurl\b", line)
        and "--fail-with-body" not in line
        and "%{http_code}" not in line
        and not line.startswith("#")
    ]
    assert not silent, "curl without --fail-with-body or a %{http_code} check:\n" + "\n".join(silent)


def test_the_restart_check_proves_the_request_was_in_flight(runbook):
    procedure = _section(runbook, "Shared procedure (every service)")
    restart = procedure.index("rollout restart")
    assert 'kill -0 "$REQ_PID"' in procedure[:restart], (
        "the restart step must check that the request is still running before it restarts the pod"
    )


def _manifest_objects() -> list[tuple[str, str]]:
    """(kind, metadata.name) of every object the manifest creates."""
    text = MANIFEST.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:  # the fallback reads the uncommented top-level keys of each document
        objects = []
        for doc in re.split(r"^---\s*$", text, flags=re.MULTILINE):
            kind = re.search(r"^kind:\s*(\S+)", doc, re.MULTILINE)
            name = re.search(r"^metadata:\n\s+name:\s*(\S+)", doc, re.MULTILINE)
            if kind and name:
                objects.append((kind.group(1), name.group(1)))
        return objects
    return [(doc["kind"], doc["metadata"]["name"]) for doc in yaml.safe_load_all(text) if doc]


def test_the_manifest_creates_a_deployment_and_a_service():
    kinds = sorted(kind for kind, _name in _manifest_objects())
    assert kinds == ["Deployment", "Service"], f"the reference manifest creates {kinds}"


def test_port_forward_targets_exist_in_the_manifest(runbook):
    objects = {(kind.lower(), name) for kind, name in _manifest_objects()}
    short = {"svc": "service", "deploy": "deployment", "deployment": "deployment", "service": "service"}
    targets = re.findall(r"port-forward\s+\"?(svc|service|deploy|deployment)/([^\s\"]+)", runbook)
    assert targets, "the runbook has no port-forward step"
    for kind, name in targets:
        name = name.replace("${TOOL}", "<tool>")
        assert (short[kind], name) in objects, f"port-forward {kind}/{name}: not an object of {MANIFEST.name}"


@pytest.mark.parametrize("path", [RUNBOOK, MANIFEST, DEPLOYMENT_DOC], ids=lambda p: p.name)
def test_no_image_tag_has_a_leading_v(path):
    text = path.read_text(encoding="utf-8")
    bad = re.findall(r"ghcr\.io/ufal/atrium-[a-z-]+:v\d[^\s`'\"]*", text)
    bad += re.findall(r"<version>[/|]v\d[^/|\s]*", text)  # a sed substitution of the template's tag
    assert not bad, f"image tags carry the source tag's leading v: {bad}"
