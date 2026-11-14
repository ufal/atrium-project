"""The Galaxy wrappers and workflows of galaxy/ agree with each other and with the releases they pin (#66).

What would go wrong unnoticed without this file:

  1. A wrapper whose <container> tag is not its own @TOOL_VERSION@: Galaxy shows one version and runs
     another image.
  2. A pin to a version the tool repository never released: the image does not exist, and nothing
     fails until a job is started on the instance.
  3. A data manager that downloads with another release than the tool that reads its table, or a
     table the two declare differently: the tool lists nothing, or reads a folder it cannot parse.
  4. A workflow step that names a wrapper at an old version, or a tool the DARIAH instance does not
     have: the import succeeds and the step is marked "tool not found".
  5. A workflow test that names an output label the workflow does not publish, or a test file that
     is not there: planemo fails only on the instance.
  6. A wrapper that is not in the toolbox list of galaxy/README.md: it is copied to the instance and
     never shown.

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
_WORKFLOWS = _GALAXY / "workflows" / "atrium_ufal"

# Wrapper file -> (the tool repository whose release it runs, the image name of that release).
_WRAPPERS = {
    "tools/atrium_page_classification/page_classification.xml": (
        "atrium-page-classification",
        "atrium-page-classification",
    ),
    "tools/atrium_translator/translator.xml": ("atrium-translator", "atrium-translator"),
    "tools/atrium_ocr_postprocess/ocr_postprocess.xml": ("atrium-ocr-postprocess", "atrium-ocr-postprocess"),
    "tools/atrium_ocr_postprocess/ocr_line_quality.xml": ("atrium-ocr-postprocess", "atrium-ocr-postprocess"),
    "tools/atrium_nlp_enrich/nlp_enrich.xml": ("atrium-nlp-enrich", "atrium-nlp-enrich"),
    "tools/atrium_keyword_extract/keyword_extract.xml": ("atrium-keyword-extract", "atrium-keyword-extract"),
    # The command-line build target of digital-convert is published as its own image (-digital).
    "tools/atrium_digital_convert/digital_convert.xml": ("atrium-digital-convert", "atrium-digital-convert-digital"),
    "data_managers/data_manager_atrium_page_models/data_manager/atrium_page_models.xml": (
        "atrium-page-classification",
        "atrium-page-classification",
    ),
    "data_managers/data_manager_atrium_hf_models/data_manager/atrium_hf_models.xml": (
        "atrium-keyword-extract",
        "atrium-keyword-extract",
    ),
}

# Data manager -> the tools that read its table.
_DATA_MANAGERS = {
    "data_managers/data_manager_atrium_page_models": ["tools/atrium_page_classification"],
    "data_managers/data_manager_atrium_hf_models": ["tools/atrium_ocr_postprocess", "tools/atrium_keyword_extract"],
}

# Tools a workflow may use that are not wrapped here: what DARIAH's test instance has installed
# (its /api/tools, read 2026-11-05).
_INSTANCE_TOOLS = {
    "__FILTER_FROM_FILE__": "1.0.0",
    "toolshed.g2.bx.psu.edu/repos/iuc/tesseract/tesseract/5.5.3+galaxy0": "5.5.3+galaxy0",
}


def _tool_files() -> list[str]:
    """Every tool XML under galaxy/tools/ (not macros.xml, not data-table configs)."""
    return sorted(
        str(p.relative_to(_GALAXY)) for p in _GALAXY.glob("tools/*/*.xml") if ET.parse(p).getroot().tag == "tool"
    )


def _imported(path: Path) -> list[ET.Element]:
    """The tool's root and the roots of the macro files it imports."""
    root = ET.parse(path).getroot()
    roots = [root]
    for imp in root.iter("import"):
        roots.append(ET.parse(path.parent / imp.text.strip()).getroot())
    return roots


def _tokens(roots: list[ET.Element]) -> dict[str, str]:
    return {t.get("name"): (t.text or "").strip() for r in roots for t in r.iter("token")}


def _expand(text: str, tokens: dict[str, str]) -> str:
    for name, value in tokens.items():
        text = text.replace(name, value)
    return text


def _wrapper(rel: str) -> dict:
    roots = _imported(_GALAXY / rel)
    tokens = _tokens(roots)
    containers = [c.text.strip() for r in roots for c in r.iter("container")]
    return {
        "id": roots[0].get("id"),
        "version": _expand(roots[0].get("version"), tokens),
        "tool_version": tokens.get("@TOOL_VERSION@"),
        "containers": [_expand(c, tokens) for c in containers],
    }


def _ours() -> dict[str, str]:
    """tool id -> version, for the wrappers of this folder."""
    return {w["id"]: w["version"] for w in map(_wrapper, _WRAPPERS)}


def _workflows() -> list[Path]:
    return sorted(_WORKFLOWS.glob("*.ga"))


def test_every_tool_is_in_the_wrapper_list():
    listed = {rel for rel in _WRAPPERS if rel.startswith("tools/")}
    assert set(_tool_files()) == listed, f"not in _WRAPPERS: {set(_tool_files()) - listed}"


def test_every_tool_is_in_the_readme_toolbox_list():
    readme = (_GALAXY / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r'<tool file="/local_tools/([^"]+)"', readme))
    expected = {rel.removeprefix("tools/") for rel in _tool_files()}
    assert listed == expected, f"README toolbox list: missing {expected - listed}, extra {listed - expected}"


@pytest.mark.parametrize("rel", sorted(_WRAPPERS))
def test_the_container_is_the_pinned_release(rel):
    wrapper = _wrapper(rel)
    assert wrapper["tool_version"], f"{rel}: no @TOOL_VERSION@ token"
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[a-z]+)?", wrapper["tool_version"]), wrapper["tool_version"]
    image = f"ghcr.io/ufal/{_WRAPPERS[rel][1]}:{wrapper['tool_version']}"
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

    Hub Self-Check checks the tool repositories out at their `test` heads (on a PR labelled
    `siblings:<branch>`, at that branch where a tool has it). The hub commit that moves a
    pin is often pushed first, because the tools' pin sweep needs it on GitHub; on 2026-11-05 and
    11-06 the check went red for that alone. So a tool repository still at an OLDER version than the
    pin is reported as a skip, with the reason; at the pinned version or later, the release history
    must name the pin (a typo, or a version that was never prepared, still fails).
    """
    repo_name = _WRAPPERS[rel][0]
    repo = _HUB_ROOT.parent / repo_name
    contributing = repo / "CONTRIBUTING.md"
    if not contributing.is_file():
        pytest.skip(f"{repo_name} is not checked out beside the hub")
    version = _wrapper(rel)["tool_version"]
    rows = re.findall(r"^\|\s*\*\*v([^*]+)\*\*", contributing.read_text(encoding="utf-8"), flags=re.M)
    if version in rows:
        return
    current = _citation_version(repo) if (repo / "CITATION.cff").is_file() else None
    if current and _version_key(current) < _version_key(version):
        pytest.skip(
            f"{repo_name} is at {current}, older than the pinned {version}: the hub was pushed before the "
            f"tool repository; re-run once its test branch carries v{version}"
        )
    pytest.fail(f"{rel} pins {version}; {repo_name}'s release history has no v{version} (it is at {current})")


def _data_manager_xml(folder: str) -> str:
    conf = ET.parse(_GALAXY / folder / "data_manager_conf.xml").getroot()
    return f"{folder}/{conf.find('data_manager').get('tool_file')}"


@pytest.mark.parametrize("folder", sorted(_DATA_MANAGERS))
def test_the_data_manager_downloads_with_its_tools_release(folder):
    manager = _wrapper(_data_manager_xml(folder))
    for tool_folder in _DATA_MANAGERS[folder]:
        for rel in (r for r in _WRAPPERS if r.startswith(tool_folder + "/")):
            if _WRAPPERS[rel][0] == _WRAPPERS[_data_manager_xml(folder)][0]:
                assert _wrapper(rel)["tool_version"] == manager["tool_version"], f"{rel} and {folder}"


@pytest.mark.parametrize("folder", sorted(_DATA_MANAGERS))
def test_the_data_table_is_declared_alike_for_tools_and_data_manager(folder):
    manager = _GALAXY / folder
    sample = (manager / "tool_data_table_conf.xml.sample").read_bytes()
    assert (manager / "tool_data_table_conf.xml").read_bytes() == sample, f"{folder}: conf and .sample differ"
    table = ET.fromstring(sample).find("table")
    loc = Path(table.find("file").get("path")).name
    for tool_folder in _DATA_MANAGERS[folder]:
        tool = _GALAXY / tool_folder
        assert (tool / "tool_data_table_conf.xml.sample").read_bytes() == sample, f"{tool_folder}: another table"
        assert (tool / "tool-data" / f"{loc}.sample").read_bytes() == (
            manager / "tool-data" / f"{loc}.sample"
        ).read_bytes()
    columns = [c.strip() for c in table.find("columns").text.split(",")]
    conf = ET.parse(manager / "data_manager_conf.xml").getroot()
    assert conf.find(".//data_table").get("name") == table.get("name")
    assert columns == [c.get("name") for c in conf.iter("column")]


def test_there_are_workflows():
    assert _workflows(), "galaxy/workflows/atrium_ufal/ holds no .ga file"


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
def test_the_workflow_release_is_in_the_changelog(path):
    release = json.loads(path.read_text(encoding="utf-8"))["release"]
    changelog = (_WORKFLOWS / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(rf"^## \[{re.escape(release)}\]", changelog, re.M), (
        f"{path.name}: release {release} not in CHANGELOG.md"
    )


def test_every_workflow_is_on_dockstore():
    dockstore = yaml.safe_load((_WORKFLOWS / ".dockstore.yml").read_text(encoding="utf-8"))
    assert {w["primaryDescriptorPath"].lstrip("/") for w in dockstore["workflows"]} == {p.name for p in _workflows()}


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
    for tests in root.iter("tests"):
        for elem in tests.iter():
            if elem.tag in ("param", "element") and elem.get("ftype") and elem.get("value"):
                for name in elem.get("value").split(","):
                    assert (test_data / name).is_file(), f"{rel}: test file {name} is not in test-data/"
