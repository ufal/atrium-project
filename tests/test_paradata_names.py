"""Batch paradata: settings in `config`, files as entries by name and SHA-512 (atrium-project#84, 1(c)).

WHY THIS EXISTS. The batch command lines of page-classification, ocr-postprocess, nlp-enrich, the
translator and keyword-extract wrote the folders and files they were given into paradata `config`.
A path describes the machine that ran the job, not the document. ARÚP's answer (decision 1(c),
comment 7): `config` holds only what shaped the output; a file the run read or wrote is an `inputs`
or `outputs` entry, by distribution name or else by file name, with its SHA-512 (decision 2).
`ParadataLogger.add_input_files()` / `add_output_files()` and the CLI's `input` / `output` without
`--name` are that rule; `name_only()` names the entries and a local model in `config`.

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

from atrium_paradata import RENDERED_PDF_DISTRIBUTION, ParadataLogger, name_only, sha512_of  # noqa: E402


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


def _logger(tmp_path):
    return ParadataLogger(
        program="ocr-postprocess", config={"model": "Qwen/Qwen2.5-0.5B"}, paradata_dir=str(tmp_path / "paradata")
    )


def test_files_become_entries_by_name_and_sha512(tmp_path):
    (tmp_path / "in").mkdir()
    page = tmp_path / "in" / "CTX01-1.txt"
    page.write_text("text", encoding="utf-8")
    logger = _logger(tmp_path)
    [entry] = logger.add_input_files(page)
    assert entry == {"name": "CTX01-1.txt", "sha512": sha512_of(path=str(page)), "stored": False}
    assert len(entry["sha512"]) == 128


def test_a_folder_adds_every_file_beneath_it_sorted_without_hidden_ones_or_the_paradata(tmp_path):
    out = tmp_path / "out"
    (out / "b").mkdir(parents=True)
    (out / "a.tsv").write_text("1", encoding="utf-8")
    (out / "b" / "c.tsv").write_text("2", encoding="utf-8")
    (out / ".state_x.json").write_text("{}", encoding="utf-8")
    (out / ".git").mkdir()
    (out / ".git" / "HEAD").write_text("x", encoding="utf-8")
    logger = ParadataLogger(program="nlp-enrich", config={}, paradata_dir=str(out / "paradata"))
    (out / "paradata" / "old.json").write_text("{}", encoding="utf-8")
    names = [e["name"] for e in logger.add_output_files(out)]
    assert names == ["a.tsv", "c.tsv"]


def test_two_files_may_share_a_name(tmp_path):
    for folder, text in (("d1", "one"), ("d2", "two")):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "page1.png").write_text(text, encoding="utf-8")
    entries = _logger(tmp_path).add_input_files(tmp_path / "d1", tmp_path / "d2")
    assert [e["name"] for e in entries] == ["page1.png", "page1.png"]
    assert entries[0]["sha512"] != entries[1]["sha512"]


def test_a_missing_file_fails_rather_than_being_left_out(tmp_path):
    with pytest.raises(FileNotFoundError):
        _logger(tmp_path).add_input_files(tmp_path / "nowhere.txt")


def test_the_record_names_no_path_anywhere(tmp_path):
    (tmp_path / "in").mkdir()
    (tmp_path / "in" / "a.xml").write_text("<a/>", encoding="utf-8")
    logger = _logger(tmp_path)
    logger.add_input_files(tmp_path / "in")
    logger.add_output_files(tmp_path / "in" / "a.xml")
    written = logger.finalize()
    record = json.loads(Path(written).read_text(encoding="utf-8"))
    assert str(tmp_path) not in json.dumps(record)
    assert record["config"] == {"model": "Qwen/Qwen2.5-0.5B"}
    assert [e["name"] for e in record["inputs"]] == ["a.xml"]


def _cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(_SHARED / "atrium_paradata.py"), *args], capture_output=True, text=True, cwd=cwd
    )


def test_the_shell_cli_names_several_files_and_folders_in_one_call(tmp_path):
    paradata = tmp_path / "paradata"
    (tmp_path / "UDP").mkdir()
    (tmp_path / "UDP" / "d1.conllu").write_text("# x", encoding="utf-8")
    (tmp_path / "UDP" / "d2.conllu").write_text("# y", encoding="utf-8")
    (tmp_path / "manifest.tsv").write_text("doc", encoding="utf-8")
    started = _cli(
        "start",
        "--program",
        "nlp-enrich",
        "--paradata-dir",
        str(paradata),
        "--config",
        "script=api_2_udp.sh",
        "model=czech-pdt-ud-2.15",
        cwd=_SHARED,
    )
    assert started.returncode == 0, started.stderr
    state = started.stdout.strip()
    done = _cli("input", "--state", state, "--file", str(tmp_path / "manifest.tsv"), cwd=_SHARED)
    assert done.returncode == 0, done.stderr
    done = _cli("output", "--state", state, "--file", str(tmp_path / "UDP"), cwd=_SHARED)
    assert done.returncode == 0, done.stderr
    data = json.loads(Path(state).read_text(encoding="utf-8"))
    assert data["config"] == {"script": "api_2_udp.sh", "model": "czech-pdt-ud-2.15"}
    assert [e["name"] for e in data["inputs"]] == ["manifest.tsv"]
    assert [e["name"] for e in data["outputs"]] == ["d1.conllu", "d2.conllu"]
    assert all(e["stored"] is False and len(e["sha512"]) == 128 for e in data["inputs"] + data["outputs"])


def test_the_shell_cli_keeps_distribution_entries_and_has_no_config_name(tmp_path):
    paradata = tmp_path / "paradata"
    record = tmp_path / "CTX01.json"
    record.write_text("{}", encoding="utf-8")
    state = _cli("start", "--program", "nlp-enrich", "--paradata-dir", str(paradata), cwd=_SHARED).stdout.strip()
    done = _cli("output", "--state", state, "--name", "atrium/document-json", "--file", str(record), cwd=_SHARED)
    assert done.returncode == 0, done.stderr
    entry = json.loads(Path(state).read_text(encoding="utf-8"))["outputs"][0]
    assert entry["name"] == "atrium/document-json" and entry["stored"] is True
    two = _cli(
        "output", "--state", state, "--name", "atrium/document-json", "--file", str(record), str(record), cwd=_SHARED
    )
    assert two.returncode == 2
    gone = _cli("start", "--program", "x", "--paradata-dir", str(paradata), "--config-name", "a=b", cwd=_SHARED)
    assert gone.returncode != 0
