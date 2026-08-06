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
    no single repo can check. It earned its keep on 2026-08-06 (run 31076188660)
    by catching a fork nobody had predicted, from a stage whose derivation was
    right: see `assert_doc_id_stable()`.

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

from atrium_document import (  # noqa: E402  (needs the path above)
    BLOCK_OWNERS,
    resolve_originator,
    validate_document,
)


def _load(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
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
    except Exception:
        # Report EVERY violation, not just the first.
        #
        # `jsonschema.validate()` raises on the best-match error and stops. That is the
        # wrong economics here: the stages run as PUBLISHED IMAGES, and `:latest` moves
        # only on a release tag (docker-tool.reusable.yml: `enable=startsWith(github.ref,
        # 'refs/tags/v')`). So every violation this gate reports costs a release of the
        # owning repo to clear, and one-error-at-a-time turns a single bad record into a
        # serialised chain of release cycles. Listing all of them means one release round
        # per repo instead of one per field.
        #
        # First observed 2026-08-06 (hub run 31075185518): nlp-enrich's released v0.18.2
        # wrote `entities[].type_cnec: null` against a `{"type": "string"}` schema. The
        # fix was already on `test` — but `:latest` still pointed at the pre-fix release,
        # so the gate could not go green from source alone.
        import jsonschema  # already imported by validate_document; local to keep the happy path clean

        from atrium_document import load_schema

        errors = sorted(
            jsonschema.Draft202012Validator(load_schema()).iter_errors(doc),
            key=lambda e: list(e.absolute_path),
        )
        lines = [f"❌ schema: {json_path} does not validate against atrium_document.schema.json"]
        for err in errors:
            where = "/".join(str(p) for p in err.absolute_path) or "<root>"
            owner = _block_owner(err.absolute_path)
            lines.append(f"   • {where}: {err.message}" + (f"   [owned by {owner}]" if owner else ""))
        lines.append(f"   {len(errors)} violation(s). Each is fixed in the OWNING repo, then released —")
        lines.append("   `:latest` only moves on a version tag, so a fix on `test` cannot green this run.")
        raise SystemExit("\n".join(lines)) from None
    print(f"✅ schema: {json_path} validates against atrium_document.schema.json")


def _block_owner(path):
    """Which tool owns the block a validation error sits in, so the report names the repo to fix.

    `path` is a jsonschema `absolute_path` deque like ``["entities", 0, "type_cnec"]``; only
    its first element identifies the block. Returns "" for structural keys and unknown blocks
    rather than guessing — BLOCK_OWNERS authorises writes, and for a field-split block the
    read-time answer is `assembled.blocks[<block>].program` (see docs/document_schema.md).
    """
    parts = list(path)
    if not parts:
        return ""
    owners = BLOCK_OWNERS.get(str(parts[0]))
    if not owners:
        return ""
    return owners if isinstance(owners, str) else " or ".join(owners)


def assert_doc_id_stable(stage_paths, final_doc, final_path):
    """`doc_id` is the accretion key: fork it and the next stage inherits nothing.

    D1 (llm) and D2 (alto) were both this defect — `Path.stem` on
    `CTX000000001.teitok.xml` / `.alto.xml` keeps the inner extension, so the
    stage looked for a baseline nobody wrote, fell back to rule 3 and emitted an
    orphan under a wrong id. Every block still validated; the record was simply
    the wrong record. Nothing in a single repo's test suite can see that.

    THE FIRST REAL CATCH (run 31076188660) was a third variant, and the one that
    settled what the rule has to be. The translator derived `CTX000000003-1` while
    the other four stages said `CTX000000003` — and its derivation was *correct*:
    `canonical_doc_id()` had been handed `PAGE_ALTO/CTX000000003/CTX000000003-1.alto.xml`,
    the page alto-postprocess split out, and answered accurately for that file.
    Deriving harder cannot fix that (`sbn.2019-1` is a legal document name, so no
    filename rule tells a page label from a document's own last segment); only
    inheriting can, so `DocumentRecord` now keeps the baseline's `doc_id` and the
    caller's guess is used for nothing but the caller's own output filenames.
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
        f"   The ORIGINATOR derives it once with canonical_doc_id(); every stage after it "
        f"INHERITS that value from the baseline it was handed, and re-derives nothing. A "
        f"stage that keys the record off its own input filename forks it — and it will, "
        f"because a stage's input is usually not the original document (the translator reads "
        f"PAGE_ALTO/<doc>/<doc>-1.alto.xml, for which canonical_doc_id() correctly answers "
        f"<doc>-1). DocumentRecord enforces the inheritance; a fork reaching here means a "
        f"stage wrote its record without one, or wrote it under a baseline it was not given."
    )
    assert final_doc.get("doc_id") == distinct[0], (
        f"❌ final record {final_path} carries doc_id {final_doc.get('doc_id')!r}, "
        f"but the stage records all carry {distinct[0]!r}"
    )
    print(f"✅ doc_id: {distinct[0]!r} unchanged across {len(seen)} stage record(s)")


def _assert_enrichment(doc, llm_stage_ran):
    """The llm-enrich block check, shared by both branches (G5).

    `assembled.blocks` is the record's own account of which tool wrote what, so it
    distinguishes "llm-enrich contributed" from "the key happened to be there",
    which a bare `in doc` cannot.
    """
    stamped = (doc.get("assembled") or {}).get("blocks") or {}
    if llm_stage_ran == "auto":
        llm_stage_ran = "enrichment" in stamped
        print(
            f"ℹ️  --llm-stage-ran not given; inferring the llm stage {'ran' if llm_stage_ran else 'was skipped'} "
            f"from assembled.blocks. CI always passes the gate's value explicitly."
        )
    if llm_stage_ran:
        assert "enrichment" in doc, "❌ 'enrichment' block missing from llm-enrich stage"
        assert "enrichment" in stamped, (
            "❌ 'enrichment' present but not recorded in assembled.blocks: it was not written "
            "through DocumentRecord.set_block(), so it carries no program/paradata stamp"
        )
    else:
        print(
            "ℹ️  the llm-enrich stage did not run — 'enrichment' block not required. "
            "This is the OPENROUTER_KEY-absent path the smoke workflows allow."
        )


def assert_digital_contract(doc, json_path):
    """The born-digital branch: `digital-convert -> llm-enrich`.

    W10. This is NOT a shorter version of the scanned contract — it is a different
    one, and the difference is the point. A born-digital record can never carry
    `page_categories` (no page image exists to classify), `translations` or
    `entities` (translator and nlp-enrich both need alto-postprocess's PAGE_ALTO /
    DOC_LINE_CATEG output, which never exists on this branch). Asserting the scanned
    blocks here would not be "stricter", it would be wrong.

    What this branch uniquely proves is the §1a ORIGINATOR ARBITRATION: alto-
    postprocess refuses to write `pages`/`lines` onto a record whose
    `source.origin` is digital-born (`_assert_origin_consistent`), and the ONE
    thing that legitimately re-opens that door is `needs_ocr: true` — the converter
    finding a text layer it does not trust. Until now that handoff was covered only
    by unit tests inside one repo.
    """
    origin = (doc.get("source") or {}).get("origin")
    print(f"ℹ️  born-digital branch: source.origin = {origin!r}")

    # Blocks digital-convert owns outright.
    assert "pages" in doc, "❌ 'pages' block missing from digital-convert"
    assert "lines" in doc, "❌ 'lines' block missing from digital-convert"

    stamped = (doc.get("assembled") or {}).get("blocks") or {}
    lines_program = (stamped.get("lines") or {}).get("program")
    assert lines_program == "digital-convert", (
        f"❌ 'lines' was written by {lines_program!r}, expected 'digital-convert'. On the "
        "born-digital branch alto-postprocess must never originate lines (§1a)."
    )

    # Blocks that CANNOT exist here. A record carrying them means either the branch
    # was fed a scanned document, or a tool wrote a block it does not own.
    for forbidden, why in (
        ("page_categories", "no page image exists to classify on this branch"),
        ("translations", "the translator needs alto-postprocess's PAGE_ALTO output"),
        ("entities", "nlp-enrich needs the DOC_LINE_CATEG classify CSV and INPUT_ALTO_DIR"),
    ):
        assert forbidden not in doc, (
            f"❌ '{forbidden}' present on a born-digital record — {why}. Either the fixture "
            f"is not actually born-digital, or a tool wrote a block it does not own."
        )

    pages = doc.get("pages") or []
    needs_ocr_pages = [p for p in pages if p.get("needs_ocr")]
    return pages, needs_ocr_pages


def assert_document_contract(json_path, llm_stage_ran="auto", stage_paths=(), expect_needs_ocr=False):
    doc = _load(json_path)

    # 0. The contract itself, before any block-by-block check: a record that does
    #    not validate is broken whatever else it contains (D4).
    assert_schema_valid(doc, json_path)
    assert_doc_id_stable(list(stage_paths), doc, json_path)

    # 0b. W10: which contract applies is derived from the RECORD, not from a flag.
    #     `source.origin` already names the originator, and `resolve_originator()`
    #     is the same function alto-postprocess uses to decide whether it may write
    #     `pages`/`lines` at all — so the assert and the tool agree by construction
    #     rather than by a CI argument someone has to remember to pass. Same lesson
    #     as doc_id inheritance: the record carries the answer.
    origin = (doc.get("source") or {}).get("origin")
    originator = resolve_originator(origin) if origin else None
    if originator == "digital-convert":
        pages, needs_ocr_pages = assert_digital_contract(doc, json_path)

        if expect_needs_ocr:
            # The §1a handoff case. This is the assertion that must NOT be able to
            # pass vacuously: a fixture whose text layer decodes cleanly would
            # satisfy "no page needs OCR" trivially, and prove nothing.
            assert needs_ocr_pages, (
                "❌ expected at least one page with needs_ocr: true, got none. The garbled "
                "fixture's whole purpose is to trip decode-sanity; if it stopped doing so, "
                "this gate is now vacuous and the §1a arbitration is untested."
            )
            for page in needs_ocr_pages:
                reason = page.get("needs_ocr_reason")
                assert reason, (
                    f"❌ page {page.get('page')!r} sets needs_ocr: true with no "
                    "'needs_ocr_reason'. The reason is what tells alto-postprocess (and a "
                    "human) WHY re-origination is authorised."
                )
                print(f"✅ needs_ocr page {page.get('page')!r}: {reason[:90]}…")
            # At least one line must be flagged Garbage. NOT "all lines" — the
            # converter flags per line, and the garbled fixture deliberately mixes
            # decodable and undecodable lines (1 of 3), so an all-lines assert would
            # fail against correct behaviour.
            garbage = [ln for ln in (doc.get("lines") or []) if ln.get("categ") == "Garbage"]
            assert garbage, (
                "❌ needs_ocr is set but no line carries categ 'Garbage' — the page-level "
                "verdict and the line-level evidence disagree."
            )
            print(f"✅ {len(garbage)} line(s) flagged Garbage, consistent with the page verdict")
        else:
            assert not needs_ocr_pages, (
                f"❌ {len(needs_ocr_pages)} page(s) unexpectedly set needs_ocr on the happy-path "
                "fixture. Either the fixture regressed or decode-sanity became over-eager."
            )
            for line in doc.get("lines") or []:
                assert line.get("text"), (
                    f"❌ line {line.get('line')!r} on page {line.get('page')!r} has no text on the "
                    "happy path; a born-digital PDF's text layer is the whole input."
                )
            print(f"✅ {len(pages)} page(s), all lines carry text, no page needs OCR")

        _assert_enrichment(doc, llm_stage_ran)
        print(f"✅ e2e_assert.py: born-digital contract verified for {json_path}")
        return

    # ── the scanned branch (pc -> alto -> translate -> nlp -> llm) ──────────────

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
        assert isinstance(entity["char_span"], (list, tuple)) and len(entity["char_span"]) == 2, (
            f"❌ 'char_span' must be a coordinate pair, got {entity['char_span']}"
        )

        # Prevent the nonexistent span["type"] key regression
        assert "type_onto" in entity or "type_cnec" in entity or "type_teitok" in entity, (
            f"❌ Entity missing type keys: {entity}"
        )

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

    # 4. LLM Enrich: API Util Regeneration — conditional on the llm stage having run.
    _assert_enrichment(doc, llm_stage_ran)

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
        "--llm-stage-ran",
        type=_tri_state,
        default="auto",
        help="pass e2e-pipeline-smoke.yml's gate output here. false = the "
        "'enrichment' block is not required (G5); auto = infer from "
        "assembled.blocks, for a manual run against a downloaded artifact.",
    )
    parser.add_argument(
        "--expect-needs-ocr",
        action="store_true",
        help="born-digital branch only: require at least one page with needs_ocr: true "
        "and a matching Garbage line (the §1a handoff that authorises alto-postprocess "
        "to re-originate). Without this the happy path is asserted instead: no page "
        "needs OCR and every line carries text.",
    )
    parser.add_argument(
        "--stages",
        nargs="*",
        default=[],
        metavar="RECORD",
        help="every per-stage record in pipeline order. doc_id must be identical "
        "across all of them and equal to the final record's.",
    )
    args = parser.parse_args(argv)

    assert_document_contract(
        args.record,
        llm_stage_ran=args.llm_stage_ran,
        stage_paths=args.stages,
        expect_needs_ocr=args.expect_needs_ocr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
