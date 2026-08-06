"""A record's `doc_id` is inherited, never re-derived (issue #10, D1/D3).

WHY THIS EXISTS. `doc_id` is the accretion key. `DocumentRecord.__init__` deep-copies the
baseline and then wrote `self._data["doc_id"] = doc_id` — the caller's value, unconditionally,
with no comparison against the key the baseline had arrived under. Every block in that copy was
written under the baseline's id, so a caller whose derivation differed by so much as one
character handed the next stage a record whose contents belong to a document it has never heard
of. Nothing raises, nothing is dropped, and the record still validates: the failure mode is a
document that quietly stops accumulating.

The E2E gate caught it on 2026-08-06 (run 31076188660):

    "work/doc_json/2_alto.json":      "CTX000000003"
    "work/doc_json/3_translate.json": "CTX000000003-1"
    "work/doc_json/4_nlp.json":       "CTX000000003"

and the stage in the middle had derived its id CORRECTLY — its input was
`PAGE_ALTO/CTX000000003/CTX000000003-1.alto.xml`, a page alto-postprocess had split out, and
`canonical_doc_id()` answers accurately for that file. That is what makes inheritance the only
available rule: `sbn.2019-1` is a legal document name, so no filename heuristic can separate a
page label from a document's own last segment, while the baseline simply carries the answer.

These tests live in the hub because the guarantee belongs to the canonical module rather than to
any one tool — the fix is precisely that a tool cannot fork the key even by being careless at its
own call site. `tests/test_e2e_assert.py` covers the gate that detects a fork; this covers the
mechanism that prevents one.

Run: pytest tests/test_document_record_doc_id.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


def _shared_dir() -> Path:
    """Locate docs/templates/shared/ by walking up, not by counting `parents[N]`.

    `parents[1]` is correct from tests/ and silently wrong from anywhere else — dropped into
    tools/e2e/ it resolves to `<hub>/tools/docs/templates/shared`, which does not exist, and
    the module-level import below then fails at COLLECTION time. That is a worse failure than
    it sounds: `Hub Self-Check` collects `tests/` and `docs/templates/shared/` and nothing
    else, so a copy living outside those two directories does not run at all — the error
    stays invisible and the coverage is silently absent. Walking up removes both halves of
    that trap: the file works wherever it is put, and where it is put still decides whether
    CI runs it.
    """
    for candidate in Path(__file__).resolve().parents:
        shared = candidate / "docs" / "templates" / "shared"
        if (shared / "atrium_document.py").is_file():
            return shared
    raise RuntimeError(
        "docs/templates/shared/atrium_document.py not found above "
        f"{Path(__file__).resolve()} — is this file outside the hub checkout?"
    )


# The canonical module is not an installed package and not importable from the repo root, so
# the directory holding it goes on sys.path — the same resolution the `shared-tests` job gets
# for free by running pytest from inside that directory. See tests/test_fixture_schema.py.
_SHARED = _shared_dir()
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from atrium_document import DocumentRecord, canonical_doc_id  # noqa: E402  (needs the path above)

DOC_ID = "CTX000000003"
PAGE_KEY = f"{DOC_ID}-1"  # what canonical_doc_id() answers for a page split out of that document


@pytest.fixture
def baseline(tmp_path):
    """An upstream record, keyed on the document, carrying a block only it could have written."""
    path = tmp_path / f"{DOC_ID}.document.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "record_type": "atrium-document",
                "doc_id": DOC_ID,
                "pages": [{"page": "1", "quality_score": 0.98}],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_canonical_doc_id_is_right_about_the_file_and_wrong_about_the_document():
    """The premise: the derivation is not buggy, so the repair cannot be a better derivation."""
    assert canonical_doc_id(f"PAGE_ALTO/{DOC_ID}/{PAGE_KEY}.alto.xml") == PAGE_KEY


def test_baseline_doc_id_wins_over_the_callers_derivation(tmp_path, baseline):
    with DocumentRecord.open(doc_id=PAGE_KEY, program="translator", baseline=str(baseline)) as doc:
        assert doc.doc_id == DOC_ID
        doc.set_block("translations", {"source_lang": "cs", "target_lang": "en", "backend": "lindat"})
        out = doc.finalize(str(tmp_path / "3_translate.json"))

    record = json.loads(Path(out).read_text(encoding="utf-8"))
    assert record["doc_id"] == DOC_ID
    # The inherited block is still there, and now still reachable: same key, same document.
    assert record["pages"][0]["quality_score"] == 0.98


def test_the_callers_derivation_is_kept_for_its_own_output_names(baseline):
    """A tool still names `<file>_log.csv` after the FILE it read; only the record is re-keyed.

    Losing that value would trade one defect for another — every page of a batch writing over
    the previous page's per-file outputs.
    """
    doc = DocumentRecord(PAGE_KEY, "translator", baseline=json.loads(baseline.read_text(encoding="utf-8")))
    assert doc.derived_doc_id == PAGE_KEY
    assert doc.doc_id == DOC_ID


def test_the_divergence_is_reported_but_never_fatal(baseline, capsys):
    """Loud enough to debug a naming disagreement; never a reason to stall a pipeline.

    Not even under `strict=True`: strictness exists to refuse a record that would be WRONG, and
    this one has just been made right. Contrast `merge_document_records()`, which does raise on
    differing doc_ids — there the ids come from two independent records, so a disagreement means
    two documents rather than two names for one.
    """
    doc = DocumentRecord(
        PAGE_KEY,
        "translator",
        baseline=json.loads(baseline.read_text(encoding="utf-8")),
        strict=True,
    )
    assert doc.doc_id == DOC_ID

    message = capsys.readouterr().err
    assert PAGE_KEY in message and DOC_ID in message


def test_no_baseline_keeps_the_derived_id(tmp_path):
    """Rule 3: a standalone run has no document context, so the filename is all there is."""
    with DocumentRecord.open(doc_id=PAGE_KEY, program="translator") as doc:
        assert doc.doc_id == PAGE_KEY
        doc.set_block("translations", {"source_lang": "cs", "target_lang": "en", "backend": "lindat"})
        out = doc.finalize(str(tmp_path / "standalone.json"))

    assert json.loads(Path(out).read_text(encoding="utf-8"))["doc_id"] == PAGE_KEY


def test_an_id_less_baseline_keeps_the_derived_id(tmp_path):
    """A baseline with no `doc_id` has nothing to inherit — the caller's value stands."""
    path = tmp_path / "partial.document.json"
    path.write_text(json.dumps({"schema_version": "1.0", "pages": [{"page": "1"}]}), encoding="utf-8")

    with DocumentRecord.open(doc_id=PAGE_KEY, program="translator", baseline=str(path)) as doc:
        assert doc.doc_id == PAGE_KEY
        doc.set_block("translations", {"source_lang": "cs", "target_lang": "en", "backend": "lindat"})
        doc.finalize(str(tmp_path / "out.json"))


def test_matching_ids_say_nothing(baseline, capsys):
    """The common case stays silent, or the note becomes noise nobody reads."""
    DocumentRecord(DOC_ID, "translator", baseline=json.loads(baseline.read_text(encoding="utf-8")))
    assert "doc_id" not in capsys.readouterr().err


def test_finalize_names_the_record_after_the_document(tmp_path, baseline):
    """Rule 1's default output name follows the record's key, so name and content agree."""
    with DocumentRecord.open(
        doc_id=PAGE_KEY,
        program="translator",
        baseline=str(baseline),
        out_dir=str(tmp_path / "out"),
    ) as doc:
        doc.set_block("translations", {"source_lang": "cs", "target_lang": "en", "backend": "lindat"})
        out = doc.finalize()

    assert Path(out).name == f"{DOC_ID}.document.json"
