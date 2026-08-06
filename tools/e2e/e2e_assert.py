"""Contract assertions for the cross-repo E2E pipeline smoke test.

WHY THIS FILE IS THE ECOSYSTEM'S REAL CONTRACT GATE. Each of the five tools
tests its own half of the document record against its own fixtures. Nothing
tested the record that comes out the far end of five real GHCR images —
`e2e-pipeline-smoke.yml` is the only place a document JSON is threaded through
every stage, so it is the only place where "did stage N erase stage N-1?" can be
asked at all.

Three issue #10 findings shaped what runs below:

  * **G5** — `assert "enrichment" in doc` was UNCONDITIONAL, on the exact path
    the workflow makes optional: `e2e-pipeline-smoke.yml` skips stage 5 and
    prints a notice when `OPENROUTER_KEY` is absent, then falls back to
    `4_nlp.json`, a record llm-enrich never touched. It had not fired only
    because the secret stayed present on push events; it was a guaranteed
    AssertionError the moment it was not, or on any future `pull_request`
    trigger. The gate's `enabled` output is now threaded in as
    `--llm-stage-ran`.
  * **D4** — `validate_document()` had ZERO call sites in CI, so the schema was
    exercised against neither the committed fixture nor real pipeline output.
    It is now the FIRST assertion here: an invalid record is a contract
    violation regardless of which blocks it happens to carry.
  * **D1/D2** — both were doc_id forks (`Path.stem` on a multi-dot name), which
    re-key the record and make the next stage inherit nothing. A per-repo test
    can only prove one repo derives the id consistently with itself;
    `--stages` asserts one identical `doc_id` across all five, which is the half
    no single repo can check.

Usage:
    python tools/e2e/e2e_assert.py work/doc_json/5_llm.json \\
        --llm-stage-ran true \\
        --stages work/doc_json/1_pc.json ... work/doc_json/5_llm.json
"""

import argparse
import json
import sys
from pathlib import Path

# The canonical atrium_document.py lives in docs/templates/shared/ here (the tool
# repos vendor it at their root, held byte-identical by para-drift). Importing the
# canonical copy rather than re-implementing the schema check is the point: this
# job must validate against exactly the contract the hub publishes.
_SHARED_DIR = Path(__file__).resolve().parents[2] / "docs" / "templates" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from atrium_document import validate_document  # noqa: E402  (needs the path above)


def _load(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assert_schema_valid(doc, json_path):
    """Layer D, against real pipeline output rather than a hand-written fixture.

    A missing `jsonschema` is a HARD failure here, deliberately unlike the
    per-repo write path (where the documented policy is one loud warning and
    carry on, so an upstream defect cannot stall a whole pipeline). This is a CI
    gate whose only job is to check the contract: degrading it to a warning would
    turn the one place the schema is enforced into a step that passes for the
    wrong reason. `jsonschema` travels with this script in
    tools/e2e/requirements.txt, so a RuntimeError here means the E2E environment
    is broken, not that the record is fine.
    """
    try:
        validate_document(doc)
    except RuntimeError as exc:
        raise SystemExit(
            f"❌ cannot validate {json_path}: {exc}\n"
            f"   jsonschema is declared in tools/e2e/requirements.txt — install step broken?"
        ) from exc
    print(f"✅ schema: {json_path} validates against atrium_document.schema.json")


def assert_doc_id_stable(stage_paths, final_doc, final_path):
    """`doc_id` is the accretion key: fork it and the next stage inherits nothing.

    D1 (llm) and D2 (alto) were both this defect — `Path.stem` on
    `CTX000000001.teitok.xml` / `.alto.xml` keeps the inner extension, so the
    stage looked for a baseline nobody wrote, fell back to rule 3 and emitted an
    orphan under a wrong id. Every block still validated; the record was simply
    the wrong record. Nothing in a single repo's test suite can see that.
    """
    if not stage_paths:
        print("⚠️  doc_id chain: no --stages given, skipping the cross-stage check")
        return

    seen = {}
    for path in stage_paths:
        assert Path(path).is_file(), (
            f"❌ stage record {path} is missing: the stage ran but wrote no document JSON "
            f"(a swallowed document-hook failure looks exactly like this)"
        )
        doc_id = _load(path).get("doc_id")
        assert doc_id, f"❌ stage record {path} has no doc_id"
        seen[path] = doc_id

    distinct = sorted(set(seen.values()))
    assert len(distinct) == 1, (
        f"❌ doc_id forked across the pipeline: {json.dumps(seen, indent=2)}\n"
        f"   Every stage must derive it with canonical_doc_id() from the SAME original "
        f"filename; a stage with its own derivation re-keys the record and orphans it."
    )
    assert final_doc.get("doc_id") == distinct[0], (
        f"❌ final record {final_path} carries doc_id {final_doc.get('doc_id')!r}, "
        f"but the stage records all carry {distinct[0]!r}"
    )
    print(f"✅ doc_id: {distinct[0]!r} unchanged across {len(seen)} stage record(s)")


def assert_document_contract(json_path, llm_stage_ran="auto", stage_paths=()):
    doc = _load(json_path)

    # 0. The contract itself, before any block-by-block check: a record that does
    #    not validate is broken whatever else it contains (D4).
    assert_schema_valid(doc, json_path)
    assert_doc_id_stable(list(stage_paths), doc, json_path)

    # 1. ALTO Postprocess: merge_blocks vs set_blocks regression check
    # 'pages' and 'content' must exist from alto-postprocess.
    # 'page_categories' must survive from page-classification.
    # (Note: 'lines' is legitimately absent because SKIP_CLASSIFY=true in E2E)
    assert "pages" in doc, "❌ 'pages' block missing: Contributions were erased"
    assert "page_categories" in doc, "❌ 'page_categories' block missing: ALTO merge_blocks failed and erased Stage 1"
    assert "content" in doc, "❌ 'content' block missing from ALTO postprocess"

    # 2. NLP Enrich: CoNLL-U Entity Structure
    entities_found = False
    assert "entities" in doc, "❌ 'entities' block missing. run_document_hook() failed or baseline was dropped."

    for entity in doc.get("entities", []):
        entities_found = True

        # Prevent the hardcoded char_span=None bug from collapsing entities
        assert "char_span" in entity, f"❌ Entity missing 'char_span' key: {entity}"
        assert entity["char_span"] is not None, "❌ 'char_span' is None (collapsed co-located entities)"
        assert isinstance(entity["char_span"], (list, tuple)) and len(entity["char_span"]) == 2, \
            f"❌ 'char_span' must be a coordinate pair, got {entity['char_span']}"

        # Prevent the nonexistent span["type"] key regression
        assert "type_onto" in entity or "type_cnec" in entity or "type_teitok" in entity, f"❌ Entity missing type keys: {entity}"

    assert entities_found, "❌ No entities found in document. run_document_hook() may be failing silently."

    # 3. Translator: Schema enforcement
    assert "translations" in doc, "❌ 'translations' block missing: Baseline was dropped during the pipeline!"
    trans_block = doc["translations"]
    if isinstance(trans_block, dict):
        trans_block = [trans_block]

    for trans in trans_block:
        # Prevent writing the entire translated corpus text
        assert "source_lang" in trans, "❌ Translation missing 'source_lang'"
        assert "target_lang" in trans, "❌ Translation missing 'target_lang'"
        assert "backend" in trans, "❌ Translation missing 'backend'"
        assert "text" not in trans, "❌ 'translations' contains raw corpus text instead of metadata schema"

    # 4. LLM Enrich: API Util Regeneration — conditional on stage 5 having run (G5).
    #    `assembled.blocks` is the record's own account of which tool wrote what,
    #    so it distinguishes "llm-enrich contributed" from "the key happened to be
    #    there", which a bare `in doc` cannot.
    stamped = ((doc.get("assembled") or {}).get("blocks") or {})
    if llm_stage_ran == "auto":
        llm_stage_ran = "enrichment" in stamped
        print(f"ℹ️  --llm-stage-ran not given; inferring stage 5 {'ran' if llm_stage_ran else 'was skipped'} "
              f"from assembled.blocks. CI always passes the gate's value explicitly.")
    if llm_stage_ran:
        assert "enrichment" in doc, "❌ 'enrichment' block missing from llm-enrich stage"
        assert "enrichment" in stamped, (
            "❌ 'enrichment' present but not recorded in assembled.blocks: it was not written "
            "through DocumentRecord.set_block(), so it carries no program/paradata stamp"
        )
    else:
        print("ℹ️  stage 5 (llm-enrich) did not run — 'enrichment' block not required. "
              "This is the OPENROUTER_KEY-absent path e2e-pipeline-smoke.yml allows.")

    print(f"✅ e2e_assert.py: Document contract verified successfully for {json_path}")


def _tri_state(value):
    """`true`/`false` from a GitHub step output, or `auto` for a manual run."""
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no", ""}:
        return False
    if lowered == "auto":
        return "auto"
    raise argparse.ArgumentTypeError(f"expected true/false/auto, got {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="the FINAL document JSON to assert against")
    parser.add_argument(
        "--llm-stage-ran", type=_tri_state, default="auto",
        help="pass e2e-pipeline-smoke.yml's gate output here. false = the "
             "'enrichment' block is not required (G5); auto = infer from "
             "assembled.blocks, for a manual run against a downloaded artifact.",
    )
    parser.add_argument(
        "--stages", nargs="*", default=[], metavar="RECORD",
        help="every per-stage record in pipeline order. doc_id must be identical "
             "across all of them and equal to the final record's.",
    )
    args = parser.parse_args(argv)

    assert_document_contract(args.record, llm_stage_ran=args.llm_stage_ran, stage_paths=args.stages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
