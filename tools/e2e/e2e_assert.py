import json
import sys


def assert_document_contract(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # 1. ALTO Postprocess: merge_blocks vs set_blocks regression check
    # If set_blocks is used incorrectly, these keys will be silently wiped out.
    assert "pages" in doc, "❌ 'pages' block missing: Contributions were erased (check merge_blocks)"
    assert "lines" in doc, "❌ 'lines' block missing: Contributions were erased (check merge_blocks)"

    # 2. NLP Enrich: Entity Structure
    # `entities` is its own top-level array block (owner: nlp-enrich; see
    # atrium_document.schema.json) with "page"/"line" reference fields — it is never
    # nested under `lines[].entities`, so check it there.
    entities_found = False
    for entity in doc.get("entities", []):
        entities_found = True

        # Prevent the hardcoded char_span=None bug from collapsing entities
        assert "char_span" in entity, f"❌ Entity missing 'char_span' key: {entity}"
        assert entity["char_span"] is not None, "❌ 'char_span' is None (collapsed co-located entities)"
        assert isinstance(entity["char_span"], (list, tuple)) and len(entity["char_span"]) == 2, \
            f"❌ 'char_span' must be a coordinate pair, got {entity['char_span']}"

        # Prevent the tagset-detection regression (entity typed under neither tagset):
        # the schema carries type_onto/type_cnec/type_teitok, no single "type" field —
        # exactly one of type_onto/type_cnec should be populated per entity.
        assert entity.get("type_onto") or entity.get("type_cnec"), \
            f"❌ Entity has neither 'type_onto' nor 'type_cnec' set (type mismatch): {entity}"

    assert entities_found, "❌ No entities found in document.entities. run_document_hook() may be failing silently."

    # 3. Translator: Schema enforcement
    if "translations" in doc:
        for trans in doc["translations"]:
            # Prevent writing the entire translated corpus text
            assert "source_lang" in trans, "❌ Translation missing 'source_lang'"
            assert "target_lang" in trans, "❌ Translation missing 'target_lang'"
            assert "backend" in trans, "❌ Translation missing 'backend'"
            assert "text" not in trans, "❌ 'translations' contains raw corpus text instead of metadata schema"

    # 4. LLM Enrich: API Util Regeneration
    if "regenerable" in doc:
        assert "markdown" in doc["regenerable"], "❌ 'regenerable.markdown' missing from llm-enrich stage"

    print(f"✅ e2e_assert.py: Document contract verified successfully for {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python e2e_assert.py <path_to_llm_json>")
        sys.exit(1)

    assert_document_contract(sys.argv[1])
