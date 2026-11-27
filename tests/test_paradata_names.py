"""Batch paradata name files and folders, never their paths (atrium-project#84, decision 1).

WHY THIS EXISTS. The batch command lines of page-classification, ocr-postprocess, nlp-enrich, the
translator and keyword-extract wrote the folders and files they were given into paradata `config`.
A path describes the machine that ran the job, not the document, and the agreed paradata name
things by distribution name. `atrium_paradata.name_only()` is the one rule every tool applies, and
`start --config-name` is the same rule for the shell callers (nlp-enrich's `api_*.sh`).

Run: pytest tests/test_paradata_names.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SHARED = _HUB_ROOT / "docs" / "templates" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from atrium_paradata import RENDERED_PDF_DISTRIBUTION, name_only  # noqa: E402


@pytest.mark.parametrize(
    "value, expected",
    [
        ("data_samples/ALTO", "ALTO"),
        ("data_samples/ALTO/", "ALTO"),
        ("./data_samples/UDP", "UDP"),
        ("../_chain/nlp_out/UDP", "UDP"),
        ("/srv/jobs/42/in/report.pdf", "report.pdf"),
        ("model/model/model_v44", "model_v44"),
        ("config.txt", "config.txt"),
    ],
)
def test_a_path_becomes_its_name(value, expected):
    assert name_only(value) == expected


def test_a_pathlike_is_named_like_a_str(tmp_path):
    assert name_only(tmp_path / "out") == "out"


def test_the_working_folder_is_named_but_an_empty_value_stays_empty():
    assert name_only(".") == os.path.basename(os.getcwd())
    assert name_only("") == ""


@pytest.mark.parametrize("value", [None, 3, 0.5, True, "https://example.org/schemas/amcr.xsd"])
def test_what_is_not_a_local_path_is_kept(value):
    assert name_only(value) == value


def test_a_list_is_named_element_wise():
    assert name_only(["a/b", "c", "", None]) == ["b", "c", "", None]


def test_local_only_keeps_a_model_id_and_names_a_local_model(tmp_path, monkeypatch):
    assert name_only("Qwen/Qwen2.5-0.5B", local_only=True) == "Qwen/Qwen2.5-0.5B"
    assert name_only("ufal/robeczech-base", local_only=True) == "ufal/robeczech-base"
    assert name_only("/models/robeczech-base", local_only=True) == "robeczech-base"
    assert name_only("./models/robeczech-base", local_only=True) == "robeczech-base"
    assert name_only("~/models/robeczech-base", local_only=True) == "robeczech-base"
    model = tmp_path / "hantian" / "layoutreader"
    model.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    # A relative value that IS a local folder is a path: named.
    assert name_only("hantian/layoutreader", local_only=True) == "layoutreader"


def test_the_rendered_pdf_has_one_stand_in_name():
    assert RENDERED_PDF_DISTRIBUTION == "rendered-pdf"


def test_the_shell_start_records_config_name_values_by_name(tmp_path):
    paradata = tmp_path / "paradata"
    paradata.mkdir()
    started = subprocess.run(
        [
            sys.executable,
            str(_SHARED / "atrium_paradata.py"),
            "start",
            "--program",
            "nlp-enrich",
            "--paradata-dir",
            str(paradata),
            "--config",
            "script=api_2_udp.sh",
            "model=czech-pdt-ud-2.15",
            "--config-name",
            "manifest=./data_samples/manifest.tsv",
            f"output_dir={tmp_path}/out/UDP/",
            "empty=",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=_SHARED,
    )
    state = json.loads(Path(started.stdout.strip()).read_text(encoding="utf-8"))
    config = state["config"]
    assert config["script"] == "api_2_udp.sh"
    assert config["model"] == "czech-pdt-ud-2.15"
    assert config["manifest"] == "manifest.tsv"
    assert config["output_dir"] == "UDP"
    assert config["empty"] == ""
    assert not any(os.sep in str(v) for k, v in config.items() if k != "model")
