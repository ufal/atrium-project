"""The AMČR seed and the run's stable id: atrium-project#71's record contract.

WHY THIS EXISTS. AMČR writes the record before the first ATRIUM stage: `doc_id` (its file id),
and a `source` with the Fedora digest (`sha512`), the file name and the media type. Every stage
must keep those four values and only add to them. #68 fixed the read-back half of that path, and
the behaviour held in `DocumentRecord`, but nothing stated it or tested it, and two things were
wrong around it:

  * every tool's inherited-baseline gate validated a seed against the FULL schema, which
    requires `provenance` and `assembled`. So the seed was reported as an invalid baseline, and
    the tool demoted its own output check to a warning, on exactly the path the pilot uses
    (`validate_baseline()` fixes it);
  * `set_source()` reported the seed's file name differing from the tool's local one as a
    conflict, on nearly every call, and refused it outright for a strict writer (digital-convert).

`run_uuid` is the run's stable id, minted by `atrium_paradata` and stamped into the record. It is
the `@id` of the run's CreateAction; `run_id` has one-second resolution and can collide.

Run: pytest tests/test_document_seed.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SHARED = _HUB_ROOT / "docs" / "templates" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import atrium_document as ad  # noqa: E402
from atrium_paradata import ParadataLogger, merge_run_paradata  # noqa: E402

jsonschema = pytest.importorskip("jsonschema", reason="the seed profile and the schema need jsonschema")

_SHA512 = "f" * 128


def _seed(**source: Any) -> Dict[str, Any]:
    base = {"sha512": _SHA512, "filename": "zprava_1923.pdf", "media_type": "application/pdf"}
    base.update(source)
    return {"schema_version": "1.0", "record_type": "atrium-document", "doc_id": "AMCR-F-0042", "source": base}


@pytest.fixture(autouse=True)
def _records_land_in_a_scratch_dir(tmp_path_factory, monkeypatch):
    """A record opened as a context manager is written on exit, by default to the working
    directory: keep that in a scratch directory, never in the checkout the tests run from."""
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd"))


@pytest.fixture
def seed_path(tmp_path):
    path = tmp_path / "AMCR-F-0042.document.json"
    path.write_text(json.dumps(_seed()), encoding="utf-8")
    return path


def _run_uuid() -> str:
    return ParadataLogger("t", {}, paradata_dir=None).run_uuid


# ── the seed profile ─────────────────────────────────────────────────────────


def test_a_seed_is_a_record_nothing_has_been_written_to():
    assert ad.is_seed(_seed())
    assert ad.is_seed({"doc_id": "x"})  # a bad seed is still a seed; validate_seed() says it is bad
    assert not ad.is_seed({**_seed(), "provenance": {}})
    assert not ad.is_seed({})
    assert not ad.is_seed(["doc_id"])


def test_the_seed_profile_accepts_amcrs_seed():
    ad.validate_seed(_seed())
    ad.validate_baseline(_seed())


@pytest.mark.parametrize(
    "seed",
    [
        pytest.param({k: v for k, v in _seed().items() if k != "doc_id"}, id="no doc_id"),
        pytest.param({**_seed(), "source": {"filename": "x.pdf", "media_type": "application/pdf"}}, id="no sha512"),
        pytest.param(_seed(sha512="F" * 128), id="upper-case digest"),
        pytest.param(_seed(sha512="f" * 64), id="a sha256 where sha512 belongs"),
        pytest.param(_seed(origin="ABBYY-ALTO"), id="origin, which belongs to the reader"),
        pytest.param({**_seed(), "record_type": "atrium-document-merged"}, id="a merged seed"),
        pytest.param({**_seed(), "pages": []}, id="a block"),
    ],
)
def test_the_seed_profile_refuses(seed):
    with pytest.raises(jsonschema.ValidationError):
        ad.validate_seed(seed)


def test_the_seed_profile_is_built_from_the_record_schema():
    """Each property is the record schema's own subschema, so a change there reaches the seed."""
    seed_schema, full = ad.seed_schema(), ad.load_schema()
    assert seed_schema["properties"]["doc_id"] == full["properties"]["doc_id"]
    assert (
        seed_schema["properties"]["source"]["properties"]["sha512"]
        == full["properties"]["source"]["properties"]["sha512"]
    )
    jsonschema.Draft202012Validator.check_schema(seed_schema)


def test_seed_schema_is_printed_for_a_caller_without_python():
    proc = subprocess.run(
        [sys.executable, str(_SHARED / "atrium_document.py"), "seed-schema"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc.stdout) == ad.seed_schema()


def test_validate_baseline_still_checks_a_written_record_in_full():
    with pytest.raises(jsonschema.ValidationError):
        ad.validate_baseline({**_seed(), "assembled": {"blocks": {"lines": {"program": "p"}}}})


# ── a seed through a stage ───────────────────────────────────────────────────


def test_a_seed_keeps_its_identity_through_a_strict_reading_stage(seed_path, capsys):
    run_uuid = _run_uuid()
    with ad.DocumentRecord.open(
        "CTX000000042",  # what the stage derives from the file it reads
        "alto-postprocess",
        baseline=str(seed_path),
        run_id="261001-101010",
        run_uuid=run_uuid,
        strict=True,
    ) as doc:
        doc.set_source(
            sha256="a" * 64, filename="CTX000000042.alto.xml", media_type="application/alto+xml", origin="ABBYY-ALTO"
        )
        doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}])
        record = doc.to_dict()

    ad.validate_document(record)
    assert record["doc_id"] == "AMCR-F-0042"
    assert {k: record["source"][k] for k in ad.SEED_SOURCE_REQUIRED} == _seed()["source"]
    assert record["source"]["origin"] == "ABBYY-ALTO"
    # The stage digested the ALTO it read, not the archive's original: no second digest.
    assert "sha256" not in record["source"]
    err = capsys.readouterr().err
    assert "NOTE" in err and "zprava_1923.pdf" in err and "a" * 64 in err
    assert "WARNING" not in err


def test_an_unseeded_source_still_takes_the_readers_sha256():
    with ad.DocumentRecord.open("CTX000000042", "alto-postprocess", baseline=None, strict=True) as doc:
        doc.set_source(sha256="a" * 64, filename="CTX000000042.alto.xml", origin="ABBYY-ALTO")
        doc.merge_block("pages", [{"page": "1", "quality_band": "Clear"}])
        record = doc.to_dict()
    assert record["source"]["sha256"] == "a" * 64


def test_a_stage_may_not_rewrite_the_seeds_digest_or_an_origin(seed_path):
    doc = ad.DocumentRecord.open("x", "alto-postprocess", baseline=str(seed_path), strict=True)
    with pytest.raises(ValueError, match="sha512"):
        doc.set_source(sha512="0" * 128)
    doc.set_source(origin="ABBYY-ALTO")
    with pytest.raises(ValueError, match="origin"):
        doc.set_source(origin="digital-born-pdf")


# ── run_uuid ─────────────────────────────────────────────────────────────────


def test_run_uuid_is_stamped_on_every_block_and_the_contributor(seed_path):
    run_uuid = _run_uuid()
    with ad.DocumentRecord.open("x", "nlp-enrich", baseline=str(seed_path), run_uuid=run_uuid) as doc:
        doc.merge_block("entities", [{"page": "1", "line": 0, "char_span": [0, 5], "surface": "Praha"}])
        doc.add_derived_from("teitok", "TEITOK/x.teitok.xml")
        record = doc.to_dict()
    assert {s["run_uuid"] for s in record["assembled"]["blocks"].values()} == {run_uuid}
    assert record["provenance"]["contributors"][-1]["run_uuid"] == run_uuid
    ad.validate_document(record)


def test_a_record_without_run_uuid_carries_no_empty_one(seed_path):
    with ad.DocumentRecord.open("x", "nlp-enrich", baseline=str(seed_path)) as doc:
        doc.add_derived_from("teitok", "TEITOK/x.teitok.xml")
        record = doc.to_dict()
    assert "run_uuid" not in record["assembled"]["blocks"]["derived_from"]
    assert "run_uuid" not in record["provenance"]["contributors"][-1]


def test_a_malformed_run_uuid_is_refused_before_anything_is_written():
    with pytest.raises(ValueError, match="run_uuid"):
        ad.DocumentRecord("x", "nlp-enrich", run_uuid="260724-101112")


def test_the_schema_refuses_a_malformed_run_uuid_or_digest():
    record = {**_seed(), "provenance": {"contributors": [{"program": "p", "run_uuid": "nope"}]}, "assembled": {}}
    with pytest.raises(jsonschema.ValidationError):
        ad.validate_document(record)
    with pytest.raises(jsonschema.ValidationError):
        ad.validate_document({**_seed(sha512="xyz"), "provenance": {}, "assembled": {}})


# ── the paradata side ────────────────────────────────────────────────────────


def test_a_service_logger_writes_nothing_and_keeps_its_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATRIUM_RUN_AGENT", "https://ror.org/00example")
    logger = ParadataLogger("page-classification", {}, paradata_dir=None)
    assert ad.RUN_UUID_PATTERN.match(logger.run_uuid)
    assert logger.paradata_ref == logger.run_uuid
    assert logger.finalize() == ""
    assert list(tmp_path.iterdir()) == []
    assert logger.record["run_uuid"] == logger.run_uuid
    assert logger.record["run_agent"] == "https://ror.org/00example"


def test_a_cli_logger_names_its_file_and_records_its_run_uuid(tmp_path):
    logger = ParadataLogger("translator", {}, paradata_dir=str(tmp_path / "paradata"))
    path = logger.finalize()
    assert path == logger.paradata_ref
    assert json.loads(Path(path).read_text(encoding="utf-8"))["run_uuid"] == logger.run_uuid


def test_two_loggers_started_together_have_two_run_uuids():
    """Two parallel workers started in one second share a run_id; never a run_uuid."""
    a, b = ParadataLogger("x", {}, paradata_dir=None), ParadataLogger("x", {}, paradata_dir=None)
    assert a.run_uuid != b.run_uuid


def test_the_cli_state_file_keeps_the_run_uuid(tmp_path):
    """A shell-driven stage's step reads its run from the `start` state file: the same ids and
    the same paradata file as the logger that wrote it."""
    logger = ParadataLogger("nlp-enrich", {}, paradata_dir=str(tmp_path))
    state = tmp_path / ".state.json"
    state.write_text(json.dumps(logger._to_state_dict()), encoding="utf-8")
    restored = ParadataLogger.from_state_file(str(state))
    assert (restored.run_id, restored.run_uuid) == (logger.run_id, logger.run_uuid)
    assert restored.paradata_ref == logger.paradata_ref


def test_a_merged_run_carries_each_stages_run_uuid_and_its_own(tmp_path):
    paths = []
    for program in ("udp", "nt"):
        logger = ParadataLogger(program, {}, paradata_dir=str(tmp_path))
        paths.append(logger.finalize())
    merged = json.loads(Path(merge_run_paradata(paths, str(tmp_path / "run.json"))).read_text(encoding="utf-8"))
    stage_uuids = [s["run_uuid"] for s in merged["pipeline_stages"]]
    assert all(ad.RUN_UUID_PATTERN.match(u) for u in stage_uuids)
    assert ad.RUN_UUID_PATTERN.match(merged["run_uuid"]) and merged["run_uuid"] not in stage_uuids
