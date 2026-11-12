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
  * stage 5 ran, reached the model and it located nothing — must PASS on a stamped
    `items: []`, and say out loud that it was empty (atrium-project#49);
  * `doc_id` forked between two stages — must FAIL (this is D1/D2, the finding no
    single repo's tests can see);
  * a schema-invalid record — must FAIL on the schema, BEFORE any block assertion,
    because "which blocks are present" is meaningless for a record that is not a
    valid record (D4);
  * born-digital `--expect-layout` (llm-enrich#18) on a record whose lines name no docproc
    block, or one block only — must FAIL, so the D1d/D1e smoke stages cannot pass on a
    converter that flattened the layout; and on a scanned record — must FAIL rather than
    silently check nothing;
  * record schema 2.0 (atrium-project#84): run data in a 2.0 record — must FAIL on the schema;
    a 1.x record from an image older than #84 — must PASS as the record it migrates to, and
    FAIL under `--require-current-major`, the E2E half of the doc-schema-v2 proof gate.

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
_FIXTURE_V1 = _HUB_ROOT / "fixtures" / "atrium_document.v1.example.json"

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
    """A full, valid 2.0 record — the committed example."""
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def record_v1():
    """The 1.x worked example, as an image older than atrium-project#84 writes it."""
    return json.loads(_FIXTURE_V1.read_text(encoding="utf-8"))


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
    final = _write(tmp_path, "4_nlp.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=False, stage_paths=[final])


def test_llm_stage_that_ran_must_produce_enrichment(tmp_path, record):
    """The other half of G5: relaxing the check must not disarm it when stage 5 DID run."""
    del record["enrichment"]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(AssertionError, match="enrichment"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])


def test_empty_enrichment_passes_and_warns(tmp_path, record, capsys):
    """atrium-project#49: "ran and found nothing" is a PASS, and must be visible as one.

    llm-enrich writes its block whenever it reached the model, with `items: []` when the
    model located nothing — the only way the record can distinguish that from "the stage
    never ran". This gate owns the integration contract, so an empty block satisfies it; asserting a live model finds archaeology in a fixture would make the
    nightly flap on provider drift and vocabulary changes.

    But it is not silent. A smoke that enriches zero passages every night is proving only
    that the plumbing connects, and that is exactly how #49 went unread for a fortnight —
    so the empty case prints a warning naming the fixture as the thing to check.
    """
    record["enrichment"] = {"items": []}
    final = _write(tmp_path, "5_llm.json", record)

    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])

    out = capsys.readouterr().out
    assert "EMPTY" in out and "atrium-project#49" in out
    assert "item(s)" not in out


def test_non_empty_enrichment_reports_its_item_count(tmp_path, record, capsys):
    """The counterpart: a real enrichment says how much it found, so a drop to zero is
    readable in the run log rather than only in a downloaded artifact."""
    final = _write(tmp_path, "5_llm.json", record)

    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])

    out = capsys.readouterr().out
    assert "enrichment: 1 item(s)" in out
    assert "EMPTY" not in out


@pytest.mark.parametrize("present", [True, False])
def test_auto_mode_infers_the_stage_from_the_block(tmp_path, record, capsys, present):
    """`auto` is for a manual run against a downloaded artifact; CI always passes the gate.
    A 2.0 record has no stamp, so the block itself is the evidence."""
    if not present:
        del record["enrichment"]
    final = _write(tmp_path, "4_nlp.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran="auto", stage_paths=[final])
    assert f"inferring the llm stage {'ran' if present else 'was skipped'}" in capsys.readouterr().out


@pytest.mark.parametrize(
    "mutate, where",
    [
        (lambda r: r.update(provenance={"contributors": []}), "provenance"),
        (lambda r: r.update(assembled={"blocks": {}}), "assembled"),
        (lambda r: r.update(derived_from={"teitok": "TEITOK/x.teitok.xml"}), "derived_from"),
        (lambda r: r.update(tables=[]), "tables"),
        (lambda r: r["source"].update(sha256="3b" * 32), "source"),
        (lambda r: r["pages"][0].update(needs_ocr=False), "pages/0"),
        (lambda r: r["lines"][0].update(style={"heading_level": 1}), "lines/0"),
    ],
)
def test_run_data_and_layout_in_a_2_0_record_fail_the_schema(tmp_path, record, mutate, where):
    """atrium-project#84: a 2.0 record is content only. Run data, licence, page verdicts and the
    layout (docproc's since D26) are refused by the schema, so they cannot creep back in."""
    mutate(record)
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(SystemExit) as exc:
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])
    assert "does not validate" in str(exc.value) and f"• {where}" in str(exc.value)


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

    The record here is BOTH schema-invalid and missing `pages`; the failure must come from the
    schema, otherwise the block assertions are reporting on a record that was never valid in
    the first place.

    **Ordering is proven by the exception TYPE, not by string matching.** `assert_schema_valid()`
    raises SystemExit; every block assertion below it raises AssertionError. So
    `pytest.raises(SystemExit)` cannot be satisfied by a run that reached a block check — that
    is the load-bearing half of this test, and it is why the negative assertion below is
    belt-and-braces rather than the substance.

    A 2.0 record has no stamps, so a missing block is no schema fault on its own; the second
    fault here is run data (`provenance`, removed in 2.0). Both are reported together, in one
    run, which is exactly the economics assert_schema_valid() exists for: one release round per
    repo, not one per field. The negative assertion matches the block assertion's OWN wording.
    """
    record["doc_id"] = 42  # schema says string
    record["provenance"] = {"contributors": []}  # run data: removed in 2.0
    del record["pages"]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(SystemExit) as exc:
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[])
    message = str(exc.value)
    assert "does not validate" in message
    assert "doc_id" in message
    assert "2 violation(s)" in message, "both faults must be reported in one run, not serialised"
    # ...and NOT the block assertion, which is the whole point of ordering.
    assert "Contributions were erased" not in message


def test_every_schema_violation_is_reported_not_just_the_first(tmp_path, record):
    """All violations in one run, each attributed to the repo that must fix it.

    The stages run as PUBLISHED IMAGES and `:latest` moves only on a release tag, so each
    violation costs a release of the owning repo to clear. Reporting one at a time turns a
    single bad record into a serialised chain of release cycles — which is exactly what hub
    run 31075185518 would have cost: nlp-enrich's released v0.18.2 wrote
    `entities[].type_cnec: null` against a `{"type": "string"}` schema.
    """
    record["entities"] = [{"page": "1", "line": 1, "char_span": [0, 4], "surface": "Praha", "type_cnec": None}]
    record["pages"] = [{"page": "1", "page_index": 1, "quality_score": "not-a-number"}]
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(SystemExit) as exc:
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[])
    message = str(exc.value)

    assert "entities/0/type_cnec" in message
    assert "pages/0/quality_score" in message
    assert "2 violation(s)" in message
    # Each line names the repo that owns the block, so the report is directly actionable.
    assert "[owned by nlp-enrich]" in message
    assert "[owned by ocr-postprocess]" in message


def test_cli_accepts_the_workflow_invocation(tmp_path, record):
    """The exact argument shape e2e-pipeline-smoke.yml passes must keep parsing."""
    final = _write(tmp_path, "5_llm.json", record)
    stages = _stage_chain(tmp_path, record, [record["doc_id"]] * 5)
    assert e2e_assert.main([final, "--llm-stage-ran", "true", "--stages", *stages]) == 0
    assert e2e_assert.main([final, "--llm-stage-ran", "false", "--stages", *stages]) == 0


# ── --teitok-dir: the TEITOK file must contain every id the record points into ────────────


def _teitok(
    tmp_path,
    *,
    version="teitok-2",
    surfaces=("facs-1", "facs-2"),
    names=("n-5",),
    toks=1,
    page="1",
    close="</name>",
):
    app = (
        f'<application ident="atrium-nlp-enrich" version="{version}"><label>w</label></application>' if version else ""
    )
    facsimile = "".join(f'<surface id="{s}"><graphic url="x.png"/></surface>' for s in surfaces)
    tokens = " ".join(f'<tok id="w-{i}">t{i}</tok>' for i in range(1, toks + 1))
    body = "".join(f'<name id="{n}" type="LOC">' for n in names) + tokens + close * len(names)
    d = tmp_path / "TEITOK"
    d.mkdir(exist_ok=True)
    (d / "CTX000000001.teitok.xml").write_text(
        f'<TEI xmlnsoff="http://www.tei-c.org/ns/1.0"><teiHeader><encodingDesc><appInfo>{app}'
        f"</appInfo></encodingDesc></teiHeader><facsimile>{facsimile}</facsimile>"
        f'<text><body><pb n="{page}" id="pb-{page}"/>'
        f'<div type="TextBlock" id="b-{page}.1"><s id="s-3">{body}</s></div></body></text></TEI>',
        encoding="utf-8",
    )
    return str(d)


def test_teitok_that_matches_the_record_passes(tmp_path, record, capsys):
    teitok_dir = _teitok(tmp_path)
    final = _write(tmp_path, "final.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)
    assert "✅ teitok: CTX000000001.teitok.xml (teitok-2)" in capsys.readouterr().out


def test_missing_teitok_file_fails(tmp_path, record):
    (tmp_path / "TEITOK").mkdir()
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="no CTX000000001.teitok.xml"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=str(tmp_path / "TEITOK"))


def test_teitok_without_tokens_fails(tmp_path, record):
    teitok_dir = _teitok(tmp_path, toks=0, names=())
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="no <tok>"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)


def test_unresolved_teitok_surface_fails(tmp_path, record):
    """pages[].teitok_surface pointing at no <surface> -- e.g. a record written with one
    id scheme next to a TEITOK file written with another."""
    teitok_dir = _teitok(tmp_path, surfaces=("CTX000000001.surface1",))
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="teitok_surface = 'facs-1'"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)


def test_unresolved_entity_ref_fails_for_teitok_format_2(tmp_path, record):
    teitok_dir = _teitok(tmp_path, names=("n-1",))
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="teitok_ref"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)


def test_unresolved_entity_ref_only_warns_for_format_1(tmp_path, record, capsys):
    """Released images before TEITOK format 2 numbered entities in two places; the check
    reports a mismatch there without failing the lane."""
    teitok_dir = _teitok(tmp_path, version=None, names=("n-1",))
    final = _write(tmp_path, "final.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)
    assert "do not resolve" in capsys.readouterr().out


def test_entity_on_another_page_than_its_name_fails_for_teitok_format_2(tmp_path, record):
    """The check that would have caught nlp-enrich#38: the record put an entity on page 1
    (its page from UDPipe's chunks) while the TEITOK had it under the <pb> of page 2."""
    teitok_dir = _teitok(tmp_path, page="2")
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="another page"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)


def test_an_entity_running_over_a_page_break_keeps_its_first_page(tmp_path, record):
    """A <pb/> inside the <name> (nlp-enrich puts it before the token on the new page)
    does not move the entity: its page is where the <name> starts."""
    teitok_dir = Path(_teitok(tmp_path, toks=2))
    path = teitok_dir / "CTX000000001.teitok.xml"
    path.write_text(
        path.read_text(encoding="utf-8").replace('<tok id="w-2">', '<pb n="2" id="pb-2"/><tok id="w-2">'),
        encoding="utf-8",
    )
    final = _write(tmp_path, "final.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=str(teitok_dir))


def test_entity_ref_must_name_a_name_element(tmp_path, record):
    """teitok_ref "n-5" resolving to a <tok> (an id scheme mix-up) is not a match."""
    teitok_dir = _teitok(tmp_path, names=())
    path = Path(teitok_dir) / "CTX000000001.teitok.xml"
    path.write_text(
        path.read_text(encoding="utf-8").replace('<tok id="w-1">', '<tok id="n-5">'),
        encoding="utf-8",
    )
    final = _write(tmp_path, "final.json", record)
    with pytest.raises(AssertionError, match="wrong element"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)


def test_legacy_name_close_tag_is_repaired_before_parsing(tmp_path, record, capsys):
    teitok_dir = _teitok(tmp_path, version=None, close="</n>")
    final = _write(tmp_path, "final.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, teitok_dir=teitok_dir)
    assert "legacy </n> close tag(s) repaired" in capsys.readouterr().out


def test_cli_accepts_teitok_dir(tmp_path, record):
    teitok_dir = _teitok(tmp_path)
    final = _write(tmp_path, "final.json", record)
    assert e2e_assert.main([final, "--llm-stage-ran", "true", "--teitok-dir", teitok_dir]) == 0


# ── born-digital branch: ATR pages and --expect-layout (llm-enrich#18, D26) ─────────────────


def _digital_record():
    """A valid 2.0 born-digital record: the record builder's rows from a rich.docx docproc.

    The branch is chosen from `source.origin` (`digital`). Each line keeps the docproc block it
    came from (`lines[].block`). No `enrichment`, so the cases below run with
    `llm_stage_ran=False`.
    """

    def line(page, number, text, block, source="text-layer"):
        return {"page": page, "line": number, "text": text, "block": block, "text_source": source}

    return {
        "schema_version": "2.0",
        "record_type": "atrium-document",
        "doc_id": "rich",
        "source": {
            "sha512": "8" * 128,
            "filename": "rich.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital",
            "page_count": 2,
        },
        "pages": [
            {"page": "1", "page_index": 1, "content_status": "text"},
            {"page": "2", "page_index": 2, "content_status": "text"},
        ],
        "lines": [
            line("1", 1, "Nálezová zpráva", "p1-b1"),
            line("1", 2, "Hradiště u Horní Mezi", "p1-b2"),
            line("1", 3, "Katalog je v archivu.", "p1-b3"),
            line("2", 1, "Nálezy", "p2-b1"),
        ],
        "content": {"text": "Hradiště u Horní Mezi\n\nKatalog je v archivu.\n\nNálezy"},
    }


def _with_atr_page(record):
    """Page 2 went to the ATR (the route step's call) and came back as ATR lines."""
    record["lines"][-1]["text_source"] = "atr"
    return record


def test_born_digital_record_passes_without_the_layout_flag(tmp_path, capsys):
    final = _write(tmp_path, "rich.json", _digital_record())
    e2e_assert.assert_document_contract(final, llm_stage_ran=False)
    assert "no page went to the ATR" in capsys.readouterr().out


def test_pages_re_acquired_by_the_atr_pass_when_expected(tmp_path, capsys):
    """The garbled lane: the pages the ATR re-acquired are read off the lines (D25)."""
    final = _write(tmp_path, "garbled.json", _with_atr_page(_digital_record()))
    e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_atr_pages=True)
    assert "page(s) ['2'] re-acquired by the ATR" in capsys.readouterr().out


def test_expected_atr_pages_cannot_pass_vacuously(tmp_path):
    final = _write(tmp_path, "clean.json", _digital_record())
    with pytest.raises(AssertionError, match="at least one page re-acquired by the ATR"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_atr_pages=True)


def test_atr_pages_on_the_happy_path_fail(tmp_path):
    final = _write(tmp_path, "rich.json", _with_atr_page(_digital_record()))
    with pytest.raises(AssertionError, match="unexpectedly went to the ATR"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False)


def test_layout_lines_joined_to_several_blocks_pass(tmp_path, capsys):
    final = _write(tmp_path, "rich.json", _digital_record())
    e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_layout=True)
    assert "4 line(s) joined to 4 docproc block(s)" in capsys.readouterr().out


def test_a_line_without_its_block_fails_the_layout_check(tmp_path):
    record = _digital_record()
    del record["lines"][1]["block"]
    final = _write(tmp_path, "unjoined.json", record)
    with pytest.raises(AssertionError, match="name no docproc block"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_layout=True)


def test_minimal_pdf_shape_cannot_pass_the_layout_check(tmp_path):
    """The check must not pass vacuously on a fixture without layout: minimal.pdf's record is
    body lines of one block."""
    record = _digital_record()
    record["source"].update(filename="minimal.pdf", media_type="application/pdf", page_count=1)
    record["pages"] = [{"page": "1", "page_index": 1, "content_status": "text"}]
    record["lines"] = [
        {"page": "1", "line": n, "text": t, "block": "p1-b1", "text_source": "text-layer"}
        for n, t in ((1, "Zpráva o sondě."), (2, "Sonda 1."))
    ]
    record["content"] = {"text": "Zpráva o sondě. Sonda 1."}
    final = _write(tmp_path, "minimal.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=False)
    with pytest.raises(AssertionError, match="flattened"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_layout=True)


@pytest.mark.parametrize("flag", ["expect_layout", "expect_atr_pages"])
def test_born_digital_flags_on_a_scanned_record_fail_instead_of_doing_nothing(tmp_path, record, flag):
    final = _write(tmp_path, "5_llm.json", record)
    with pytest.raises(AssertionError, match="born-digital branch only"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, **{flag: True})


def test_cli_accepts_the_born_digital_flags(tmp_path):
    """The shapes e2e-digital-smoke.yml passes; `--expect-needs-ocr` is the 1.x name of
    `--expect-atr-pages`, kept so the workflows need no change."""
    final = _write(tmp_path, "rich.json", _digital_record())
    assert e2e_assert.main([final, "--llm-stage-ran", "false", "--expect-layout"]) == 0
    garbled = _write(tmp_path, "garbled.json", _with_atr_page(_digital_record()))
    assert e2e_assert.main([garbled, "--llm-stage-ran", "false", "--expect-needs-ocr"]) == 0
    assert e2e_assert.main([garbled, "--llm-stage-ran", "false", "--expect-atr-pages"]) == 0


# ── the positional blocks: one writer, checks across rows (D20, D25, D29) ────────────────────


def test_a_line_that_does_not_say_its_text_source_fails(tmp_path):
    record = _digital_record()
    del record["lines"][0]["text_source"]
    final = _write(tmp_path, "rich.json", record)
    with pytest.raises(AssertionError, match="without text_source"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False)


@pytest.mark.parametrize("page, status", [(0, "empty"), (1, "empty")])
def test_content_status_must_agree_with_the_lines(tmp_path, page, status):
    record = _digital_record()
    record["pages"][page]["content_status"] = status
    final = _write(tmp_path, "rich.json", record)
    with pytest.raises(AssertionError, match="content_status disagrees"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False)


def test_a_text_page_without_lines_fails(tmp_path):
    record = _digital_record()
    record["lines"] = [ln for ln in record["lines"] if ln["page"] == "1"]
    final = _write(tmp_path, "rich.json", record)
    with pytest.raises(AssertionError, match=r"content_status disagrees .*\('2', 'text'\)"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False)


# ── 1.x records: images older than atrium-project#84 ─────────────────────────────────────────


def _digital_record_1x():
    """A 1.x digital-convert record with its layout cues and a page it flagged for OCR."""
    return {
        "schema_version": "1.0",
        "record_type": "atrium-document",
        "doc_id": "rich",
        "provenance": {"license": "MIT", "contributors": []},
        "source": {
            "sha256": "8" * 64,
            "filename": "rich.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital-born-docx",
            "page_count": 2,
        },
        "pages": [
            {"page": "1", "page_index": 1},
            {"page": "2", "page_index": 2, "needs_ocr": True, "needs_ocr_reason": "no extractable text layer"},
        ],
        "lines": [
            {
                "page": "1",
                "line": 0,
                "text": "Nálezová zpráva",
                "group_id": "hdr0-0",
                "style": {"region": "page_header"},
            },
            {"page": "1", "line": 1, "text": "Hradiště u Horní Mezi", "group_id": "p0", "style": {"heading_level": 1}},
            {"page": "2", "line": 0, "text": "Nálezy", "group_id": "tbl0-r0c0"},
        ],
        "content": {"text": "Hradiště u Horní Mezi\n\nNálezy", "reading_order": "layout"},
        "tables": [
            {
                "table_id": "t0",
                "page": "2",
                "cells": [
                    {"row": 0, "col": 0, "group_id": "tbl0-r0c0"},
                    {"row": 0, "col": 1, "group_id": "tbl0-r0c1"},
                ],
            }
        ],
    }


def test_a_1x_record_is_checked_as_the_record_it_migrates_to(tmp_path, record_v1, capsys):
    final = _write(tmp_path, "5_llm.json", record_v1)
    stages = _stage_chain(tmp_path, record_v1, [record_v1["doc_id"]] * 5)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=stages)
    out = capsys.readouterr().out
    assert "(written at 1.x, migrated) validates" in out
    assert "read through migrate_document()" in out


def test_require_current_major_refuses_a_1x_record(tmp_path, record, record_v1):
    """The E2E half of the doc-schema-v2 proof gate (D12): valid only after migration is not proven."""
    stage = _write(tmp_path, "2_alto.json", record_v1)
    final = _write(tmp_path, "5_llm.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[stage, final])
    with pytest.raises(AssertionError, match=r"2_alto.json \(1.x\)"):
        e2e_assert.assert_document_contract(
            final, llm_stage_ran=True, stage_paths=[stage, final], require_current_major=True
        )
    assert e2e_assert.main([final, "--llm-stage-ran", "true", "--stages", final, "--require-current-major"]) == 0


def test_a_1x_born_digital_record_keeps_its_own_evidence(tmp_path, capsys):
    """needs_ocr, style and tables left the record in 2.0; a 1.x record is checked on them."""
    final = _write(tmp_path, "rich_1x.json", _digital_record_1x())
    e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_atr_pages=True, expect_layout=True)
    out = capsys.readouterr().out
    assert "page(s) ['2'] re-acquired by the ATR" in out
    assert "1 heading line(s); regions {'page_header': 1} (1.x record)" in out


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda r: r["lines"][1].pop("style"), "heading_level"),
        (lambda r: r["lines"][0].pop("style"), "style.region"),
        (lambda r: r["lines"][2].update(group_id="p9"), "table 't0' on page '2'"),
    ],
)
def test_a_flattened_1x_layout_fails(tmp_path, mutate, message):
    record = _digital_record_1x()
    mutate(record)
    final = _write(tmp_path, "flat_1x.json", record)
    with pytest.raises(AssertionError, match=message):
        e2e_assert.assert_document_contract(final, llm_stage_ran=False, expect_atr_pages=True, expect_layout=True)


def test_teitok_is_named_by_a_1x_records_derived_from(tmp_path, record_v1):
    """A 1.x record still names nlp-enrich's file; with two TEITOK files that settles which."""
    teitok_dir = Path(_teitok(tmp_path))
    (teitok_dir / "other.teitok.xml").write_text("<TEI/>", encoding="utf-8")
    migrated = e2e_assert.migrate_document(copy.deepcopy(record_v1))
    migrated["doc_id"] = "AMCR-F-1"
    e2e_assert.assert_teitok(migrated, str(teitok_dir), record_v1)
    with pytest.raises(AssertionError, match="not exactly one"):
        e2e_assert.assert_teitok(migrated, str(teitok_dir))


# ── the AMČR seed (atrium-project#71) ──────────────────────────────────────────

_SEED_SOURCE = {"sha512": "e" * 128, "filename": "zprava_1923.pdf", "media_type": "application/pdf"}
_DESCRIBED = {"origin": "legacy", "page_count": 2, "language": ["cs"]}


def _seeded_chain(tmp_path, record):
    """seed -> pc (identity only) -> the record builder (describes the source) -> final."""
    seed = {"record_type": "atrium-document", "doc_id": "AMCR-F-1", "source": _SEED_SOURCE}
    stages = []
    for described in ({}, _DESCRIBED):
        stage = copy.deepcopy(record)
        stage["doc_id"] = seed["doc_id"]
        stage["source"] = {**_SEED_SOURCE, **described}
        stages.append(stage)
    final = copy.deepcopy(record)
    final["doc_id"] = seed["doc_id"]
    final["source"] = {**_SEED_SOURCE, **_DESCRIBED}
    return (
        _write(tmp_path, "0_seed.json", seed),
        [_write(tmp_path, f"{i}_stage.json", s) for i, s in enumerate(stages, start=1)],
        final,
    )


def test_a_seeded_chain_that_keeps_the_seed_passes(tmp_path, record, capsys):
    seed, stages, final = _seeded_chain(tmp_path, record)
    final_path = _write(tmp_path, "5_llm.json", final)
    e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=stages, seed=seed)
    assert "seed: doc_id 'AMCR-F-1'" in capsys.readouterr().out


def test_a_stage_that_rewrites_the_digest_fails(tmp_path, record):
    seed, stages, final = _seeded_chain(tmp_path, record)
    final["source"]["sha512"] = "d" * 128
    final_path = _write(tmp_path, "5_llm.json", final)
    with pytest.raises(AssertionError, match="sha512"):
        e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=stages, seed=seed)


def test_a_chain_rekeyed_off_its_file_names_fails_even_when_consistent(tmp_path, record):
    """Every stage agreeing on doc_id is not enough: it must be the SEED's."""
    seed, _, final = _seeded_chain(tmp_path, record)
    final["doc_id"] = "CTX000000001"
    final_path = _write(tmp_path, "5_llm.json", final)
    with pytest.raises(AssertionError, match="doc_id"):
        e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=[final_path], seed=seed)


@pytest.mark.parametrize("field, value", [("origin", "atr"), ("page_count", 3), ("language", ["de"])])
def test_a_later_stage_that_rewrites_a_described_source_field_fails(tmp_path, record, field, value):
    seed, stages, final = _seeded_chain(tmp_path, record)
    final["source"][field] = value
    final_path = _write(tmp_path, "5_llm.json", final)
    with pytest.raises(AssertionError, match=f"rewrote source.{field}"):
        e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=stages, seed=seed)


def test_a_1x_origin_is_compared_by_its_2_0_value(tmp_path, record):
    """A builder image older than #84 wrote `ABBYY-ALTO`; it reads as `legacy`, like the final record's."""
    seed, stages, final = _seeded_chain(tmp_path, record)
    older = json.loads(Path(stages[1]).read_text(encoding="utf-8"))
    older.update(schema_version="1.0")
    older["source"]["origin"] = "ABBYY-ALTO"
    Path(stages[1]).write_text(json.dumps(older), encoding="utf-8")
    final_path = _write(tmp_path, "5_llm.json", final)
    e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=stages, seed=seed)


def test_a_seed_that_names_the_origin_is_refused(tmp_path, record):
    seed, stages, final = _seeded_chain(tmp_path, record)
    bad = json.loads(Path(seed).read_text(encoding="utf-8"))
    bad["source"]["origin"] = "legacy"
    Path(seed).write_text(json.dumps(bad), encoding="utf-8")
    final_path = _write(tmp_path, "5_llm.json", final)
    with pytest.raises(AssertionError, match="not a valid AMČR seed"):
        e2e_assert.assert_document_contract(final_path, llm_stage_ran=True, stage_paths=stages, seed=seed)


def test_teitok_is_the_runs_one_file_when_doc_id_is_the_seeds(tmp_path, record, capsys):
    """nlp-enrich names its TEITOK after its own input; a seeded record's doc_id is AMČR's, and a
    2.0 record names no file. One document per run, so the one TEITOK file is the one."""
    teitok_dir = _teitok(tmp_path)
    record["doc_id"] = "AMCR-F-1"
    e2e_assert.assert_teitok(record, teitok_dir)
    assert "taking the run's one TEITOK file, CTX000000001.teitok.xml" in capsys.readouterr().out


def test_cli_accepts_seed(tmp_path, record):
    seed, stages, final = _seeded_chain(tmp_path, record)
    final_path = _write(tmp_path, "5_llm.json", final)
    assert e2e_assert.main([final_path, "--llm-stage-ran", "true", "--stages", *stages, "--seed", seed]) == 0


# ── atrium-project#73: `keywords` and `quality_summary` ─────────────────────────────────────


def _with_keywords(record, **overrides):
    """The example record after keyword-extract's statistical kind: a `keywords` block."""
    record = copy.deepcopy(record)
    record["keywords"] = {
        "document": [
            {"keyword": "gotický kostel", "method": "yake", "score": 1.0, "rank": 1},
            {"keyword": "základy", "method": "yake", "score": 0.4, "rank": 2},
        ],
        "pages": [{"page": "1", "keywords": [{"keyword": "kostel", "method": "yake", "score": 1.0, "rank": 1}]}],
    }
    record["keywords"].update(overrides)
    return record


def test_a_keywords_block_passes(tmp_path, record, capsys):
    final = _write(tmp_path, "5_kw_stat.json", _with_keywords(record))
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final], keywords_stage_ran=True)
    assert "2 document keyword(s) and 1 page list(s) by 'yake'" in capsys.readouterr().out


def test_the_statistical_kind_that_ran_must_leave_its_block(tmp_path, record):
    final = _write(tmp_path, "5_kw_stat.json", record)
    with pytest.raises(AssertionError, match="'keywords' block missing"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final], keywords_stage_ran=True)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final], keywords_stage_ran=False)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda r: r["keywords"]["document"][1].update(rank=3), "not 1..2 in order"),
        (lambda r: r["keywords"]["document"][1].update(method="keybert"), "mixes"),
        (lambda r: r["keywords"]["pages"][0].update(page="9"), "not a page of the record"),
        (lambda r: r["keywords"]["document"][0].update(teater_category="kostel"), "never one list"),
        (lambda r: r["enrichment"]["items"][0].update(rank=1), "statistical keyword's fields"),
    ],
)
def test_a_wrong_keywords_block_fails(tmp_path, record, mutate, message):
    shaped = _with_keywords(record)
    mutate(shaped)
    final = _write(tmp_path, "5_kw_stat.json", shaped)
    with pytest.raises(AssertionError, match=message):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final], keywords_stage_ran=True)


def _with_summary(record):
    """The example record as the record builder leaves it: its pages' and lines' read-out."""
    record = copy.deepcopy(record)
    record["quality_summary"] = e2e_assert.quality_summary(record)
    return record


def test_a_quality_summary_is_checked_against_the_stage_that_wrote_it(tmp_path, record, capsys):
    """The first stage that carries the block is its writer, the record builder."""
    upstream = copy.deepcopy(record)
    del upstream["quality_summary"]
    first = _write(tmp_path, "1_pc.json", upstream)
    stage = _write(tmp_path, "2_alto.json", _with_summary(record))
    later = _with_summary(record)
    later["lines"][0]["upos"] = "PROPN"  # nlp-enrich's field contribution leaves the read-out as it was
    final = _write(tmp_path, "4_nlp.json", later)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[first, stage, final])
    assert "✅ quality_summary: 2_alto.json's read-out" in capsys.readouterr().out


def test_a_quality_summary_that_is_not_the_read_out_fails(tmp_path, record):
    written = _with_summary(record)
    written["quality_summary"]["pages"]["mean"] = 0.5
    final = _write(tmp_path, "2_alto.json", written)
    with pytest.raises(AssertionError, match="is not quality_summary"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])


def test_a_quality_summary_changed_downstream_fails(tmp_path, record):
    written = _with_summary(record)
    stage = _write(tmp_path, "2_alto.json", written)
    changed = copy.deepcopy(written)
    changed["quality_summary"]["lines"]["total"] = 99
    final = _write(tmp_path, "4_nlp.json", changed)
    with pytest.raises(AssertionError, match="changed after 2_alto.json"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[stage, final])


def test_a_quality_summary_with_a_band_fails(tmp_path, record):
    banded = _with_summary(record)
    banded["quality_summary"]["pages"]["band"] = "Clear"
    final = _write(tmp_path, "2_alto.json", banded)
    with pytest.raises(AssertionError, match="it is numbers"):
        e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])


def test_a_1x_quality_summary_is_the_migrations_read_out(tmp_path, record_v1, capsys):
    """The migration rewrites the rows the block reads (categ, empty pages), so it recomputes it."""
    record_v1["quality_summary"] = {"pages": {"total": 2, "scored": 2}, "lines": {"total": 1, "by_categ": {}}}
    final = _write(tmp_path, "2_alto.json", record_v1)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])
    assert "recomputed by the 1.x→2.0 migration" in capsys.readouterr().out


def test_a_required_quality_summary_must_be_there(tmp_path, record):
    del record["quality_summary"]
    final = _write(tmp_path, "4_nlp.json", record)
    e2e_assert.assert_document_contract(final, llm_stage_ran=True, stage_paths=[final])
    with pytest.raises(AssertionError, match="'quality_summary' missing"):
        e2e_assert.assert_document_contract(
            final, llm_stage_ran=True, stage_paths=[final], quality_summary_expected=True
        )


def test_cli_accepts_the_73_flags(tmp_path, record):
    final = _write(tmp_path, "5_kw.json", _with_summary(_with_keywords(record)))
    assert (
        e2e_assert.main(
            [
                final,
                "--llm-stage-ran",
                "true",
                "--keywords-stage-ran",
                "true",
                "--quality-summary",
                "true",
                "--stages",
                final,
            ]
        )
        == 0
    )
