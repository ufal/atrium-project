"""The Galaxy wrappers and workflows of galaxy/ agree with each other and with the releases they pin (#66).

What would go wrong unnoticed without this file:

  1. A wrapper whose <container> tag is not its own @TOOL_VERSION@: Galaxy shows one version and runs
     another image.
  2. A pin to a version the tool repository never released: the image does not exist, and nothing
     fails until a job is started on the instance.
  3. A workflow step that names a wrapper at an old version, or a tool the DARIAH instance does not
     have: the import succeeds and the step is marked "tool not found".
  4. A workflow test that names an output label the workflow does not publish, or a test file that
     is not there: planemo fails only on the instance.

Planemo's own lint (`planemo lint`, `planemo workflow_lint --iwc`) checks the Galaxy side; this file
checks the ATRIUM side, without planemo. Run: pytest tests/test_galaxy_wrappers.py
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

_HUB_ROOT = Path(__file__).resolve().parents[1]
_GALAXY = _HUB_ROOT / "galaxy"
_WORKFLOWS = _GALAXY / "workflows"

# Wrapper file -> the tool repository whose batch image it runs.
_WRAPPERS = {
    "tools/atrium_page_classification/page_classification.xml": "atrium-page-classification",
    "tools/atrium_translator/translator.xml": "atrium-translator",
    "data_managers/data_manager_atrium_page_models/data_manager/atrium_page_models.xml": "atrium-page-classification",
}

# Tools a workflow may use that are not wrapped here: what DARIAH's test instance has installed
# (its /api/tools, read 2026-11-05).
_INSTANCE_TOOLS = {
    "__FILTER_FROM_FILE__": "1.0.0",
    "toolshed.g2.bx.psu.edu/repos/iuc/tesseract/tesseract/5.5.3+galaxy0": "5.5.3+galaxy0",
}


def _tokens(root: ET.Element) -> dict[str, str]:
    return {t.get("name"): (t.text or "").strip() for t in root.iter("token")}


def _expand(text: str, tokens: dict[str, str]) -> str:
    for name, value in tokens.items():
        text = text.replace(name, value)
    return text


def _wrapper(rel: str) -> dict:
    root = ET.parse(_GALAXY / rel).getroot()
    tokens = _tokens(root)
    containers = [c.text.strip() for c in root.iter("container")]
    return {
        "id": root.get("id"),
        "version": _expand(root.get("version"), tokens),
        "tool_version": tokens.get("@TOOL_VERSION@"),
        "containers": [_expand(c, tokens) for c in containers],
    }


def _ours() -> dict[str, str]:
    """tool id -> version, for the wrappers of this folder."""
    return {w["id"]: w["version"] for w in map(_wrapper, _WRAPPERS)}


def _workflows() -> list[Path]:
    return sorted(_WORKFLOWS.glob("*.ga"))


@pytest.mark.parametrize("rel", sorted(_WRAPPERS))
def test_the_container_is_the_pinned_release(rel):
    wrapper = _wrapper(rel)
    assert wrapper["tool_version"], f"{rel}: no @TOOL_VERSION@ token"
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[a-z]+)?", wrapper["tool_version"]), wrapper["tool_version"]
    image = f"ghcr.io/ufal/{_WRAPPERS[rel]}:{wrapper['tool_version']}"
    assert wrapper["containers"] == [image], f"{rel}: runs {wrapper['containers']}, expected [{image}]"
    assert re.fullmatch(re.escape(wrapper["tool_version"]) + r"\+galaxy\d+", wrapper["version"]), wrapper["version"]


def _version_key(version: str) -> tuple[int, ...]:
    """`1.7.7-beta` -> (1, 7, 7): the numeric part, which orders the releases of one repository."""
    return tuple(int(part) for part in re.findall(r"\d+", version.split("-", 1)[0]))


def _citation_version(repo: Path) -> str | None:
    match = re.search(r'^version:\s*["\']?v?([^"\'\s]+)', (repo / "CITATION.cff").read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else None


@pytest.mark.parametrize("rel", sorted(_WRAPPERS))
def test_the_pinned_release_is_in_the_tool_repository(rel):
    """Checked where the tool repository is checked out beside the hub (as tools/docs_check.py expects).

    Hub Self-Check checks the tool repositories out at their `test` heads. The hub commit that moves a
    pin is often pushed first, because the tools' pin sweep needs it on GitHub; on 2026-11-05 and
    11-06 the check went red for that alone. So a tool repository still at an OLDER version than the
    pin is reported as a skip, with the reason; at the pinned version or later, the release history
    must name the pin (a typo, or a version that was never prepared, still fails).
    """
    repo = _HUB_ROOT.parent / _WRAPPERS[rel]
    contributing = repo / "CONTRIBUTING.md"
    if not contributing.is_file():
        pytest.skip(f"{_WRAPPERS[rel]} is not checked out beside the hub")
    version = _wrapper(rel)["tool_version"]
    rows = re.findall(r"^\|\s*\*\*v([^*]+)\*\*", contributing.read_text(encoding="utf-8"), flags=re.M)
    if version in rows:
        return
    current = _citation_version(repo) if (repo / "CITATION.cff").is_file() else None
    if current and _version_key(current) < _version_key(version):
        pytest.skip(
            f"{_WRAPPERS[rel]} is at {current}, older than the pinned {version}: the hub was pushed before the "
            f"tool repository; re-run once its test branch carries v{version}"
        )
    pytest.fail(f"{rel} pins {version}; {_WRAPPERS[rel]}'s release history has no v{version} (it is at {current})")


def test_the_data_manager_downloads_with_the_tools_release():
    tool = _wrapper("tools/atrium_page_classification/page_classification.xml")
    manager = _wrapper("data_managers/data_manager_atrium_page_models/data_manager/atrium_page_models.xml")
    assert manager["tool_version"] == tool["tool_version"]


def test_the_data_table_is_declared_alike_for_tool_and_data_manager():
    tool = _GALAXY / "tools/atrium_page_classification/tool_data_table_conf.xml.sample"
    manager = _GALAXY / "data_managers/data_manager_atrium_page_models/tool_data_table_conf.xml.sample"
    assert tool.read_bytes() == manager.read_bytes()
    columns = ET.parse(tool).getroot().find("table/columns").text
    conf = ET.parse(_GALAXY / "data_managers/data_manager_atrium_page_models/data_manager_conf.xml").getroot()
    assert [c.strip() for c in columns.split(",")] == [c.get("name") for c in conf.iter("column")]


def test_there_are_workflows():
    assert _workflows(), "galaxy/workflows/ holds no .ga file"


@pytest.mark.parametrize("path", _workflows(), ids=lambda p: p.name)
def test_every_step_names_a_tool_galaxy_has(path):
    ours = _ours()
    steps = json.loads(path.read_text(encoding="utf-8"))["steps"].values()
    for step in (s for s in steps if s["type"] == "tool"):
        tool_id, version = step["tool_id"], step["tool_version"]
        expected = ours.get(tool_id, _INSTANCE_TOOLS.get(tool_id))
        assert expected is not None, f"{path.name}: step {step['label']!r} uses {tool_id}, which no Galaxy here has"
        assert version == expected, f"{path.name}: step {step['label']!r} runs {tool_id} {version}, not {expected}"
        assert step["content_id"] == tool_id


@pytest.mark.parametrize("path", _workflows(), ids=lambda p: p.name)
def test_the_workflow_test_matches_the_workflow(path):
    tests_file = path.with_name(f"{path.stem}-tests.yml")
    assert tests_file.is_file(), f"{path.name} has no {tests_file.name}"
    workflow = json.loads(path.read_text(encoding="utf-8"))
    inputs = {s["label"] for s in workflow["steps"].values() if s["type"].endswith("_input")}
    outputs = {o["label"] for s in workflow["steps"].values() for o in s["workflow_outputs"]}
    for case in yaml.safe_load(tests_file.read_text(encoding="utf-8")):
        assert set(case["job"]) <= inputs, f"{tests_file.name}: unknown inputs {set(case['job']) - inputs}"
        assert set(case["outputs"]) <= outputs, f"{tests_file.name}: unknown outputs {set(case['outputs']) - outputs}"
        for value in case["job"].values():
            for element in value.get("elements", [value]):
                if "path" in element:
                    assert (_WORKFLOWS / element["path"]).is_file(), f"{tests_file.name}: no {element['path']}"


@pytest.mark.parametrize("rel", sorted(r for r in _WRAPPERS if r.startswith("tools/")))
def test_every_tool_test_file_is_there(rel):
    root = ET.parse(_GALAXY / rel).getroot()
    test_data = (_GALAXY / rel).parent / "test-data"
    for param in root.iter("param"):
        if param.get("ftype") and param.get("value"):
            for name in param.get("value").split(","):
                assert (test_data / name).is_file(), f"{rel}: test file {name} is not in test-data/"
