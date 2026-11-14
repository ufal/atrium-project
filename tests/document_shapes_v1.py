"""The record shapes 1.x producers wrote, kept as data for the doc-schema-v1 checks.

Record schema 2.0 (atrium-project#84) replaced these shapes; `doc-schema-v1` stays published and
cited, so tests/test_schema_freeze_records.py checks that every shape here is still valid under the
frozen v1 copy, that the floor still refuses the defect shapes there, and that each valid one
migrates to a valid 2.0 record (`atrium_document.migrate_document`). The enumeration is the one
tests/test_document_required.py held until 2026-11-12, traced from the 1.x call sites; it is not a
test module and is not edited further.
"""

from __future__ import annotations

from typing import Any, Dict

#: A run's stable id as atrium_paradata mints it (atrium-project#71).
_RUN_UUID = "urn:uuid:4f1c2e3a-5b6d-4e7f-8a9b-0c1d2e3f4a5b"


def _stamp(*names: str, run_uuid: str = "") -> Dict[str, Any]:
    """An `assembled` block stamped for `names`, shaped exactly as `_stamp()` writes it; with
    `run_uuid` as a run that carries one (atrium-project#71) writes it."""
    stamp = {"program": "p", "run_id": "260909-000000"}
    if run_uuid:
        stamp["run_uuid"] = run_uuid
    stamp.update({"paradata_ref": run_uuid, "updated_at": "2026-09-09T00:00:00+00:00"})
    return {
        "blocks": {n: dict(stamp) for n in names},
        "had_baseline": False,
        "note": "Blocks reflect CONTRIBUTED steps only; a block is absent until its tool has run.",
    }


def _handoff_stamp() -> Dict[str, Any]:
    """`assembled` after ocr-postprocess's OCR hand-off (atrium-digital-convert#4 W4): its `pages`
    and `lines` stamps carry `contribution: "ocr-handoff"`; `content` is still the converter's."""
    assembled = _stamp("pages", "lines", "content", run_uuid=_RUN_UUID)
    for name in ("pages", "lines"):
        assembled["blocks"][name].update(program="ocr-postprocess", contribution="ocr-handoff")
    assembled["blocks"]["content"]["program"] = "digital-convert"
    return assembled


def _unstamped() -> Dict[str, Any]:
    """`assembled` as a record that only ever had set_source() carries it: no `blocks` key at all
    (checked against a real alto-postprocess page_split/text_split record)."""
    return {
        "had_baseline": False,
        "note": "Blocks reflect CONTRIBUTED steps only; a block is absent until its tool has run.",
    }


#: The five keys `DocumentRecord.to_dict()` emits on every path, with no branch that can skip one.
#: `schema_version`/`record_type` are setdefault in __init__, `doc_id` is assigned there
#: unconditionally, and `to_dict()` itself always assigns `provenance` and `assembled`.
_FLOOR: Dict[str, Any] = {
    "schema_version": "1.0",
    "record_type": "atrium-document",
    "doc_id": "CTX000000001",
    "provenance": {
        "license": "CC BY-NC 4.0",
        "license_url": "https://x",
        "license_basis": "calculated",
        "contributors": [],
    },
}


# ── the shapes production code actually writes ────────────────────────────────
#
# Each entry names the call site it was traced from, as <repo>/<file>::<function> (line numbers
# drifted with every edit of the tools; the function does not). If you change one of those call
# sites so it emits a different shape, change it here in the same commit -- that is the whole
# point of the file.
VALID_SHAPES = {
    # alto-postprocess/page_split.py::main -- the scanned originator. set_source() deliberately does
    # NOT stamp, so this record has no `assembled.blocks` key at all. It is the reason the schema
    # says "source OR a stamped block" rather than "a stamped block".
    "alto page_split (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "a" * 64,
            "filename": "CTX000000001.alto.xml",
            "media_type": "application/alto+xml",
            "page_count": 1,
            "origin": "ABBYY-ALTO",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/page_split.py::main again, for --method json-keys: the same call with the
    # JSON media type and the `ocr:generic` origin.
    "alto page_split, json-keys (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "d" * 64,
            "filename": "CTX000000015.json",
            "media_type": "application/json",
            "page_count": 2,
            "origin": "ocr:generic",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/text_split.py::main -- the --method text-lines originator (atrium-alto-
    # postprocess#31): source only, like page_split; `page_count` only for formats with real pages.
    "alto text_split (source only, no stamp)": {
        **_FLOOR,
        "source": {
            "sha256": "e" * 64,
            "filename": "CTX000000012.pdf",
            "media_type": "application/pdf",
            "page_count": 1,
            "origin": "ocr:pdf-text-layer",
        },
        "assembled": _unstamped(),
    },
    # alto-postprocess/text_split.py::main for a born-digital input: a `digital-born-*` origin
    # hands the positional blocks to digital-convert, so every later stage of alto-postprocess
    # holds them back and this `source` stays the record's only contribution from that repo.
    "alto text_split, born-digital (source only, no positional block)": {
        **_FLOOR,
        "source": {
            "sha256": "f" * 64,
            "filename": "CTX000000010.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital-born-docx",
        },
        "assembled": _unstamped(),
    },
    # The AMČR-seeded path (atrium-project#71), as it leaves the reading stage:
    # alto-postprocess/document_hook.py::write_document_block on a seed. The seed's doc_id (an AMČR
    # file id), sha512, file name and media type are kept; the stage added the origin (its sha256
    # is of the ALTO it read, not of the original, so it is dropped) and stamped its run_uuid on
    # its blocks and its contributor entry.
    "AMČR seed after the reading stage (sha512 kept, run_uuid stamped)": {
        **_FLOOR,
        "doc_id": "AMCR-F-CTX000000001",
        "source": {
            "sha512": "c" * 128,
            "filename": "CTX000000001.pdf",
            "media_type": "application/pdf",
            "origin": "ABBYY-ALTO",
        },
        "provenance": {
            **_FLOOR["provenance"],
            "contributors": [
                {
                    "program": "alto-postprocess",
                    "run_id": "261001-000000",
                    "run_uuid": _RUN_UUID,
                    "paradata_ref": _RUN_UUID,
                    "blocks": "pages,lines",
                    "at": "2026-10-01T00:00:00+00:00",
                }
            ],
        },
        "assembled": _stamp("pages", "lines", run_uuid=_RUN_UUID),
        "pages": [{"page": "1", "quality_band": "Clear"}],
        "lines": [{"page": "1", "line": 0, "text": "Náčrt sondy.", "categ": "Clear"}],
    },
    # alto-postprocess/extract_ALTO_2_TXT.py::main (and its four twins: extract_LytRdr_ALTO_2_TXT,
    # extract_LLM_ALTO_2_TXT, extract_JSON_2_TXT and, for --method text-lines, extract_TEXT_2_TXT)
    "alto extract (pages + content)": {
        **_FLOOR,
        "assembled": _stamp("pages", "content"),
        "pages": [{"page": "1"}],
        "content": {"text": "Náčrt sondy."},
    },
    # alto-postprocess/classify_TEXT.py::process_document
    "alto classify_TEXT (lines)": {
        **_FLOOR,
        "assembled": _stamp("lines"),
        "lines": [{"page": "1", "line": 0, "text": "Náčrt sondy.", "categ": "Clear"}],
    },
    # alto-postprocess/aggregate_STAT.py::main
    "alto aggregate_STAT (pages)": {
        **_FLOOR,
        "assembled": _stamp("pages"),
        "pages": [{"page": "1", "quality_score": 0.9, "quality_band": "Clear"}],
    },
    # page-classification/atrium_document_adapter.py::_write_one -- stage 1 of the scanned pipeline, and
    # it never calls set_source(). This is why `source` is NOT in the floor.
    "page-classification standalone": {
        **_FLOOR,
        "assembled": _stamp("page_categories", "pages", "derived_from"),
        "derived_from": {"classification": "CATEG/CTX000000001.csv"},
        "page_categories": {"1": "TEXT"},
        "pages": [{"page": "1", "category": "TEXT", "category_confidence": 0.98}],
    },
    # translator/main.py::process_single_file -- add_derived_from() is unconditional inside the `with`, so a
    # standalone translator record is seven keys, not six.
    "translator standalone": {
        **_FLOOR,
        "assembled": _stamp("translations", "derived_from"),
        "derived_from": {"translated_xml": "TRANSLATED/CTX000000001.alto.xml"},
        "translations": {"source_lang": "cs", "target_lang": "en", "backend": "lindat"},
    },
    # nlp-enrich/api_util/document_hook.py::run_document_hook -- both merges are unconditional, so both blocks
    # are present even when empty. An empty list is a contribution; no key is not.
    "nlp-enrich standalone (empty entities list)": {
        **_FLOOR,
        "assembled": _stamp("entities", "pages"),
        "entities": [],
        "pages": [],
    },
    # llm-enrich/llm_client_shared.py::write_document_record
    "llm-enrich standalone": {
        **_FLOOR,
        "assembled": _stamp("enrichment", "derived_from", "regenerable"),
        "derived_from": {"enriched": "KW_PER_DOC_LLM/CTX000000001_enriched.json"},
        "regenerable": {"markdown": {"from": "CTX000000001.document.json", "converter": "json_to_md@1.0"}},
        "enrichment": {"items": [], "summary": None, "topics": []},
    },
    # digital-convert/api_util/digital_to_json.py::to_record -- the digital-born originator, which DOES call
    # set_source() first, deliberately. Every page row carries `text_layer` since v1.1.1-beta.
    "digital-convert originator": {
        **_FLOOR,
        "source": {"sha256": "b" * 64, "media_type": "application/pdf", "origin": "digital-born-pdf"},
        "assembled": _stamp("pages", "lines", "content", "tables"),
        "pages": [{"page": "1", "page_index": 1, "text_layer": "digital"}],
        "lines": [{"page": "1", "line": 0, "text": "t"}],
        "content": {"text": "t"},
        "tables": [{"table_id": "t1", "page": "1"}],
    },
    # digital-convert/api_util/digital_to_json.py::to_record for a DOCX (llm-enrich#18), trimmed from a real
    # rich.docx record: no bbox and no canvas (a DOCX has no page geometry), a counted page_count,
    # and the layout cues in lines[].style -- heading_level, and `region` for the running header and
    # the footnote. `region` was written before the schema declared it (additionalProperties: true);
    # declaring it as a closed enum is only additive because this shape still validates.
    "digital-convert originator, DOCX with layout cues": {
        **_FLOOR,
        "source": {
            "sha256": "8" * 64,
            "filename": "rich.docx",
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "origin": "digital-born-docx",
            "page_count": 2,
        },
        "assembled": _stamp("pages", "lines", "content", "tables"),
        "pages": [
            {"page": "1", "page_index": 1, "quality_score": 1.0, "quality_band": "Clear"},
            {"page": "2", "page_index": 2, "quality_score": 1.0, "quality_band": "Clear"},
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
            {"page": "1", "line": 2, "text": "Sonda II", "group_id": "p1", "style": {"bold": True}},
            {
                "page": "1",
                "line": 3,
                "text": "Katalog je v archivu.",
                "group_id": "fn1",
                "style": {"region": "footnote"},
            },
            {"page": "2", "line": 0, "text": "Nálezy", "group_id": "tbl0-r0c0"},
            {"page": "2", "line": 1, "text": "Strana 2", "group_id": "ftr0-0", "style": {"region": "page_footer"}},
        ],
        "content": {
            "text": "Hradiště u Horní Mezi\n\nSonda II\n\nKatalog je v archivu.\n\nNálezy",
            "reading_order": "layout",
        },
        "tables": [
            {
                "table_id": "t0",
                "page": "2",
                "caption": "",
                "n_rows": 1,
                "n_cols": 1,
                "group_id": "tbl0",
                "cells": [{"row": 0, "col": 0, "is_header": True, "group_id": "tbl0-r0c0"}],
            }
        ],
    },
    # ocr-postprocess/service/text_api.py::process_document -> document_hook.write_document_block ->
    # DocumentRecord.replace_page_rows (atrium-digital-convert#4 W4): a born-digital PDF whose page ii
    # did not decode, after its ATR ALTO came back. Page ii holds the OCR lines only and gains `ocr`;
    # `needs_ocr`, `text_layer`, `canvas` and `category` stay; `source` and `content` are the converter's.
    "ocr-postprocess W4 hand-off on a born-digital PDF": {
        **_FLOOR,
        "source": {
            "sha256": "d" * 64,
            "sha512": "e" * 128,
            "filename": "C-202000543A-DT-27.pdf",
            "media_type": "application/pdf",
            "origin": "digital-born-pdf",
            "page_count": 2,
        },
        "assembled": _handoff_stamp(),
        "pages": [
            {"page": "i", "page_index": 1, "quality_score": 1.0, "quality_band": "Clear", "text_layer": "digital"},
            {
                "page": "ii",
                "page_index": 2,
                "canvas": {"width": 595.0, "height": 842.0, "unit": "pt"},
                "needs_ocr": True,
                "needs_ocr_reason": "embedded text layer does not decode: 2 of 2 lines carry CP1250 bytes",
                "text_layer": "garbled",
                "category": "TEXT_P",
                "category_confidence": 0.93,
                "quality_score": 0.9,
                "quality_band": "Clear",
                "ocr": {"engine": "ocr:pero"},
            },
        ],
        "lines": [
            {"page": "i", "line": 0, "text": "Nálezová zpráva", "bbox": [72.0, 64.0, 388.0, 80.0]},
            {"page": "ii", "line": 1, "text": "sondě", "categ": "Clear", "quality_score": 0.91, "lang": "ces"},
            {"page": "ii", "line": 2, "text": "hřeby", "categ": "Clear", "quality_score": 0.88, "lang": "ces"},
        ],
        "content": {"text": "Nálezová zpráva", "reading_order": "layout"},
    },
    # keyword-extract/service/api.py::_run -> llm_client_shared.write_document_record(keywords=...)
    # (atrium-project#73): the statistical kind on the record nlp-enrich wrote, document and pages.
    "keyword-extract statistical keywords (keywords block)": {
        **_FLOOR,
        "source": {"sha256": "a" * 64, "filename": "CTX000000001.alto.xml", "origin": "ABBYY-ALTO"},
        "assembled": _stamp("lines", "keywords", run_uuid=_RUN_UUID),
        "lines": [{"page": "1", "line": 0, "text": "Hradiště u Horní Mezi", "categ": "Clear"}],
        "keywords": {
            "document": [
                {"keyword": "hradiště", "method": "yake", "score": 1.0, "rank": 1},
                {"keyword": "horní mez", "method": "yake", "score": 0.42, "rank": 2},
            ],
            "pages": [{"page": "1", "keywords": [{"keyword": "hradiště", "method": "yake", "score": 1.0, "rank": 1}]}],
        },
    },
    # The same call with kind=both: `keywords` and `enrichment` side by side, never one list.
    "keyword-extract both kinds (keywords beside enrichment)": {
        **_FLOOR,
        "source": {"sha256": "a" * 64, "filename": "CTX000000001.alto.xml", "origin": "ABBYY-ALTO"},
        "assembled": _stamp("keywords", "enrichment", run_uuid=_RUN_UUID),
        "keywords": {"document": [{"keyword": "sonda", "method": "keybert", "score": 0.64, "rank": 1}], "pages": []},
        "enrichment": {
            "items": [
                {
                    "page": "1",
                    "line": 0,
                    "extracted_keywords_cs": ["hradiště"],
                    "extracted_keywords_en": ["hillfort"],
                    "teater_category": "hradiště",
                    "confidence_score": 0.9,
                    "citation": "[Source: CTX000000001, Page 1]",
                }
            ]
        },
    },
    # ocr-postprocess/document_hook.py::write_document_block (and ::write_scores) after its pages and
    # lines (atrium-project#73 R6): the summary is recomputed from them on every such write.
    "ocr-postprocess quality summary (quality_summary block)": {
        **_FLOOR,
        "source": {"sha256": "a" * 64, "filename": "CTX000000001.alto.xml", "origin": "ABBYY-ALTO"},
        "assembled": _stamp("pages", "lines", "quality_summary", run_uuid=_RUN_UUID),
        "pages": [{"page": "1", "quality_score": 0.75, "quality_band": "Clear"}],
        "lines": [
            {"page": "1", "line": 0, "text": "Hradiště u Horní Mezi", "categ": "Clear", "quality_score": 0.9},
            {"page": "1", "line": 1, "text": "||| ..", "categ": "Trash", "quality_score": 0.1},
        ],
        "quality_summary": {
            "pages": {"total": 1, "scored": 1, "mean": 0.75, "median": 0.75, "min": 0.75, "max": 0.75},
            "lines": {"total": 2, "by_categ": {"Clear": 1, "Trash": 1}},
        },
    },
    # The same writer on a born-digital record no page of which was scored: no statistics.
    "ocr-postprocess quality summary, nothing scored": {
        **_FLOOR,
        "source": {"sha256": "d" * 64, "filename": "x.pdf", "origin": "digital-born-pdf"},
        "assembled": _stamp("pages", "quality_summary", run_uuid=_RUN_UUID),
        "pages": [{"page": "i", "page_index": 1, "text_layer": "blank"}],
        "quality_summary": {"pages": {"total": 1, "scored": 0}, "lines": {"total": 0, "by_categ": {}}},
    },
    # atrium_document.merge_document_records() -- record_type differs, and `blocks` may legitimately
    # be {} when every input was a source-only record. That is why minProperties lives inside the
    # anyOf branch rather than on assembled.blocks itself.
    "merge_document_records output (source-only inputs)": {
        **_FLOOR,
        "record_type": "atrium-document-merged",
        "source": {"sha256": "c" * 64},
        "assembled": {"blocks": {}, "merged_from": 2, "merged_at": "2026-09-09T00:00:00+00:00", "note": "…"},
    },
}


# ── the defect classes the freeze exists to catch ─────────────────────────────
INVALID_SHAPES = {
    # What `required` accepted before the freeze. nlp-enrich/tests/test_run_pipeline.py (the
    # `_fake_stage` of its --document-json-out test) wrote literally this.
    "today's two-key minimum": {"schema_version": "1.0", "doc_id": "CTX000000001"},
    # The issue's own words: "a stage that produces nothing still validates". finalize() already
    # prints WARNING - <program> contributed no block; this promotes it to a failure.
    # Live instance: alto-postprocess/classify_TEXT.py::process_document on an empty CSV, whose
    # hook call sits outside the `if not df.empty` guard.
    "a stage that contributed nothing (no source, no stamp)": {**_FLOOR, "assembled": _stamp()},
    # A stamp is written by _stamp(), which only runs where the payload is written in the same
    # call -- so a stamp without a payload cannot come from the module. It means the record was
    # hand-built, truncated in transit, or field-filtered down to nothing.
    "stamp without payload": {**_FLOOR, "assembled": _stamp("lines")},
    "record_type missing": {
        k: v for k, v in {**_FLOOR, "assembled": _stamp("pages"), "pages": []}.items() if k != "record_type"
    },
    "provenance missing": {
        k: v for k, v in {**_FLOOR, "assembled": _stamp("pages"), "pages": []}.items() if k != "provenance"
    },
}
