"""Tests for tools/e2e/e2e_assert.py — the cross-repo contract gate (issue #10).

WHY THIS EXISTS. `e2e_assert.py` is the only thing in the ecosystem that looks at a
document record after all five tools have written to it, and it runs in exactly one
place: `e2e-pipeline-smoke.yml`, roughly every third night, with `OPENROUTER_KEY`
present. That is why **G5** survived — `assert "enrichment" in doc` was unconditional
while the workflow makes stage 5 optional, so the failing branch was the one branch CI
never took. A gate whose own error paths are untested is a gate that reports on its
happy path only.

So the cases below are deliberately the ones the nightly E2E cannot reach:

  * stage 5 skipped (the `OPENROUTER_KEY`-absent path, and the future
    `pull_request` trigger) — must PASS without an `enrichment` block;
  * stage 5 ran but wrote no `enrichment` — must FAIL;
  * `doc_id` forked between two stages — must FAIL (this is D1/D2, the finding no
    single repo's tests can see);
  * a schema-invalid record — must FAIL on the schema, BEFORE any block assertion,
    because "which blocks are present" is meaningless for a record that is not a
    valid record (D4).

Run: pytest tests/test_e2e_assert.py
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_HUB_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _HUB_ROOT / "tools" / "e2e" / "e2e_assert.py"
_FIXTURE = _HUB_ROOT / "fixtures" / "atrium_document.example.json"

jsonschema = pytest.importorskip(
    "jsonschema",
    reason="e2e_assert.py's first assertion is validate_document(); without jsonschema it "
    "raises RuntimeError by design and there is nothing to test here",
)


def _load_script():
    """Import the E2E asserter by path (tools/ is not a package)."""
    spec = importlib.util.spec_from_file_location("e2e_assert", _SCRIPT)
    assert spec and spec.loader, f"cannot load {_SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    sys.modules["e2e_assert"] = module
    spec.loader.exec_module(module)
    return module


e2e_assert = _load_script()


@pytest.fixture
def record():
    """A full, valid five-stage record — the committed example."""
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _stage_chain(tmp_path, record, doc_ids):
    """One record per stage, each carrying the given doc_id."""
    paths = []
    for index, doc_id in enumerate(doc_ids, start=1):
        stage = copy.deepcopy(record)
        stage["doc_id"] = doc_id
        paths.append(_write(tmp_path, f"{index}_stage.json", stage))
    return paths


def test_full_record_passes_with_all_five_stages(tmp_path, record):
    final = _write(tmp_path, "5_llm.json", record)
    stages = _stage_chain(tmp_path, record, [record["doc_id"]] * 5)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=stages)


def test_skipped_llm_stage_does_not_require_enrichment(tmp_path, record):
    """G5: the OPENROUTER_KEY-absent path asserted a block only stage 5 writes.

    The workflow falls back to `4_nlp.json`, a record llm-enrich never touched, so this
    used to be a guaranteed AssertionError the moment the secret was absent.
    """
    del record["enrichment"]
    del record["assembled"]["blocks"]["enrichment"]
    final = _write(tmp_path, "4_nlp.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=False, stage_paths=[final])


def test_llm_stage_that_ran_must_produce_enrichment(tmp_path, record):
    """The other half of G5: relaxing the check must not disarm it when stage 5 DID run."""
    del record["enrichment"]
    del record["assembled"]["blocks"]["enrichment"]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(AssertionError, match="enrichment"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])


def test_unstamped_enrichment_block_is_rejected(tmp_path, record):
    """A block present but absent from assembled.blocks was not written via set_block()."""
    del record["assembled"]["blocks"]["enrichment"]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(AssertionError, match="assembled.blocks"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])


def test_auto_mode_infers_the_stage_from_the_stamp(tmp_path, record):
    """`auto` is for a manual run against a downloaded artifact; CI always passes the gate."""
    del record["enrichment"]
    del record["assembled"]["blocks"]["enrichment"]
    final = _write(tmp_path, "4_nlp.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran="auto", stage_paths=[final])


def test_forked_doc_id_across_stages_fails(tmp_path, record):
    """D1/D2: `Path.stem` on `X.teitok.xml` keeps `.teitok`, re-keying the record.

    Every block still validates and every per-repo test still passes — the record is
    simply the wrong record, inheriting nothing. Only a cross-stage comparison sees it.
    """
    final = _write(tmp_path, "5_llm.json", record)
    stages = _stage_chain(
        tmp_path,
        record,
        ["CTX000000001", "CTX000000001", "CTX000000001", "CTX000000001", "CTX000000001.teitok"],
    )
    with pytest.raises(AssertionError, match="doc_id forked"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=stages)


def test_final_record_disagreeing_with_the_chain_fails(tmp_path, record):
    forked = copy.deepcopy(record)
    forked["doc_id"] = "CTX000000001.document"
    final = _write(tmp_path, "5_llm.json", forked)
    stages = _stage_chain(tmp_path, record, [record["doc_id"]] * 4)
    with pytest.raises(AssertionError, match="but the stage records all carry"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=stages)


def test_missing_stage_record_fails_by_name(tmp_path, record):
    """J4: a swallowed document-hook failure leaves the promised file unwritten, exit 0."""
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(AssertionError, match="4_nlp.json is missing"):
        e2e_assert.assert_document_contract(
            final,
            llm_stage_ran=True,
            stage_paths=[final, str(tmp_path / "4_nlp.json")],
        )


def test_schema_invalid_record_fails_on_the_schema_first(tmp_path, record):
    """D4: validation is assertion zero — before any block check, so the diagnosis is honest.

    The record here is BOTH schema-invalid and missing `pages`; the failure must name the
    schema violation, otherwise the block assertions are reporting on a record that was
    never valid in the first place.
    """
    record["doc_id"] = 42  # schema says string
    del record["pages"]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(SystemExit) as exc:
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[])
    message = str(exc.value)
    assert "does not validate" in message
    assert "doc_id" in message
    # ...and NOT the missing-block error, which is the whole point of ordering.
    assert "pages" not in message.split("violation(s)")[0].replace("doc_id", "")


def test_every_schema_violation_is_reported_not_just_the_first(tmp_path, record):
    """All violations in one run, each attributed to the repo that must fix it.

    The stages run as PUBLISHED IMAGES and `:latest` moves only on a release tag, so each
    violation costs a release of the owning repo to clear. Reporting one at a time turns a
    single bad record into a serialised chain of release cycles — which is exactly what hub
    run 31075185518 would have cost: nlp-enrich's released v0.18.2 wrote
    `entities[].type_cnec: null` against a `{"type": "string"}` schema.
    """
    record["entities"] = [
        {"page": "1", "line": 0, "char_span": [0, 4], "surface": "Praha", "type_cnec": None}
    ]
    record["pages"] = [{"page": "1", "quality_score": "not-a-number"}]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(SystemExit) as exc:
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[])
    message = str(exc.value)

    assert "entities/0/type_cnec" in message
    assert "pages/0/quality_score" in message
    assert "2 violation(s)" in message
    # Each line names the repo that owns the block, so the report is directly actionable.
    assert "[owned by nlp-enrich]" in message
    assert "[owned by alto-postprocess or digital-convert]" in message


def test_cli_accepts_the_workflow_invocation(tmp_path, record):
    """The exact argument shape e2e-pipeline-smoke.yml passes must keep parsing."""
    final = _write(tmp_path, "5_llm.json", record)
    stages = _stage_chain(tmp_path, record, [record["doc_id"]] * 5)
    assert e2e_assert.main([final, "--llm-stage-ran", "true", "--stages", *stages]) == 0
    assert e2e_assert.main([final, "--llm-stage-ran", "false", "--stages", *stages]) == 0
