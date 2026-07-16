#!/usr/bin/env python3
"""
e2e_assert.py — cross-repo interface assertions for the e2e pipeline smoke test.

Each subcommand validates ONE stage boundary of the
pc -> alto -> translate -> nlp -> llm -> TEITOK chain (hub issue #18 follow-up).
The goal is catching cross-repo INTERFACE breakage, not scoring model quality:
assertions check file presence, formats, schemas, and text preservation — never
prediction correctness.

Subcommands
-----------
    pc            page-classification result table (FILE/PAGE/CLASS-n/SCORE-n)
    categ-header  fixture DOC_LINE_CATEG header == alto HEAD's CSV_HEADER (drift tripwire)
    alto          PAGE_ALTO split + stats CSV + PAGE_TXT text preservation
    translate     translated ALTO structure + per-line log CSV
    teitok        nlp TEITOK output (well-formed TEI, tokens, NLP application header)
    keywords      llm-enrich *_enriched.json record schema

Every subcommand exits 0 on success and non-zero with a `[e2e][FAIL]` message
otherwise. stdlib-only by design (runs in every stage's minimal environment).
"""

import argparse
import ast
import csv
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ALTO_NS = "{http://www.loc.gov/standards/alto/ns-v3#}"


def _local(tag: str) -> str:
    """Local element name, with or without a namespace prefix."""
    return tag.split("}")[-1] if "}" in tag else tag


def fail(msg: str) -> None:
    print(f"[e2e][FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"[e2e][OK] {msg}")


def _parse_xml(path: Path) -> ET.ElementTree:
    try:
        return ET.parse(path)
    except ET.ParseError as exc:
        fail(f"{path} is not well-formed XML: {exc}")
        raise  # unreachable — fail() exits


def _alto_strings(path: Path) -> list:
    tree = _parse_xml(path)
    return [s.get("CONTENT", "") for s in tree.getroot().iter(f"{ALTO_NS}String")]


# ── pc ─────────────────────────────────────────────────────────────────────────


def check_pc(args) -> None:
    """One TOP-N result CSV exists, with FILE/PAGE/CLASS-1/SCORE-1 columns and a valid score."""
    tables = sorted(Path(args.tables).glob("*_TOP-*.csv"))
    if len(tables) != 1:
        fail(f"expected exactly 1 TOP-N result CSV in {args.tables}, found {len(tables)}: {[t.name for t in tables]}")
    with open(tables[0], encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        fail(f"{tables[0].name} has no data rows")
    required = {"FILE", "PAGE", "CLASS-1", "SCORE-1"}
    missing = required - set(rows[0].keys())
    if missing:
        fail(f"{tables[0].name} is missing columns {sorted(missing)}; has {sorted(rows[0].keys())}")
    row = rows[0]
    if not row["CLASS-1"].strip():
        fail(f"{tables[0].name}: empty CLASS-1 prediction")
    try:
        score = float(row["SCORE-1"])
    except ValueError:
        fail(f"{tables[0].name}: SCORE-1 {row['SCORE-1']!r} is not a float")
    if not 0.0 < score <= 1.0:
        fail(f"{tables[0].name}: SCORE-1 {score} outside (0, 1]")
    ok(f"pc interface: {tables[0].name} -> {row['FILE']} p{row['PAGE']} = {row['CLASS-1']} ({score})")


# ── categ-header ───────────────────────────────────────────────────────────────


def read_csv_header_from_source(langid_path: Path) -> list:
    """Extract CSV_HEADER from langID_classify.py by AST — no torch/pandas import."""
    tree = ast.parse(langid_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "CSV_HEADER":
                    return [ast.literal_eval(elt) for elt in node.value.elts]
    fail(f"CSV_HEADER not found in {langid_path}")
    return []  # unreachable


def check_categ_header(args) -> None:
    """The committed fixture DOC_LINE_CATEG header must equal alto HEAD's CSV_HEADER.

    The classify stage needs a GPU (perplexity engine fails fast on CPU-only
    runners), so CI bridges alto -> nlp with the committed fixture CSV. This
    tripwire fails the smoke the moment alto's line-CSV schema changes, forcing
    a fixture regeneration instead of silently testing nlp against a stale format.
    """
    expected = read_csv_header_from_source(Path(args.langid))
    with open(args.fixture, encoding="utf-8") as fh:
        actual = next(csv.reader(fh))
    if actual != expected:
        only_fixture = [c for c in actual if c not in expected]
        only_head = [c for c in expected if c not in actual]
        fail(
            "fixture DOC_LINE_CATEG header diverged from alto HEAD CSV_HEADER — regenerate the fixture. "
            f"fixture-only: {only_fixture}; HEAD-only: {only_head}; "
            f"order mismatch: {actual != expected and not only_fixture and not only_head}"
        )
    ok(f"categ header in sync with alto HEAD ({len(expected)} columns)")


# ── alto ───────────────────────────────────────────────────────────────────────


def check_alto(args) -> None:
    """PAGE_ALTO holds exactly the expected single page; stats CSV lists it; PAGE_TXT preserves every token."""
    doc = args.doc
    page_dir = Path(args.page_alto) / doc
    pages = sorted(page_dir.glob(f"{doc}-*.alto.xml")) if page_dir.is_dir() else []
    if len(pages) != 1:
        fail(f"expected exactly 1 per-page ALTO in {page_dir}, found {len(pages)}")
    page_strings = [s for s in _alto_strings(pages[0]) if s]
    if not page_strings:
        fail(f"{pages[0].name}: no <String> CONTENT survived the split")

    stats = Path(args.stats_csv)
    if not stats.is_file() or stats.stat().st_size == 0:
        fail(f"stats CSV missing or empty: {stats}")
    with open(stats, encoding="utf-8") as fh:
        stat_rows = [r for r in csv.DictReader(fh) if r.get("file") == doc]
    if len(stat_rows) != 1:
        fail(f"stats CSV: expected 1 row for {doc}, found {len(stat_rows)}")

    txt_files = sorted(Path(args.page_txt).rglob(f"{doc}-*.txt"))
    if len(txt_files) != 1:
        fail(f"expected exactly 1 extracted text file for {doc} under {args.page_txt}, found {len(txt_files)}")
    extracted = txt_files[0].read_text(encoding="utf-8")
    # De-hyphenation may merge tokens across line breaks, so check containment
    # per source token against the whitespace-flattened text.
    flat = " ".join(extracted.split())
    missing = [tok for tok in page_strings if tok not in flat]
    if missing:
        fail(f"{txt_files[0].name}: extracted text lost source tokens {missing[:5]} (of {len(missing)})")
    ok(f"alto interface: 1 page split, stats row present, all {len(page_strings)} tokens preserved in extract")


# ── translate ──────────────────────────────────────────────────────────────────


def check_translate(args) -> None:
    """Translated ALTO exists, is well-formed, keeps page/line structure, and changed the text; log CSV matches."""
    src = Path(args.source)
    out_dir = Path(args.out_dir)
    base = src.name[: -len(".alto.xml")]
    translated = out_dir / f"{base}_{args.target_lang}.alto.xml"
    if not translated.is_file():
        found = sorted(p.name for p in out_dir.glob("*.alto.xml"))
        fail(f"translated ALTO not found: {translated} (dir has: {found})")

    src_tree, out_tree = _parse_xml(src), _parse_xml(translated)
    for tag in ("Page", "TextLine"):
        n_src = len(list(src_tree.getroot().iter(f"{ALTO_NS}{tag}")))
        n_out = len(list(out_tree.getroot().iter(f"{ALTO_NS}{tag}")))
        if n_src != n_out:
            fail(f"{translated.name}: <{tag}> count changed {n_src} -> {n_out} (in-place structure broken)")

    src_text = " ".join(s for s in _alto_strings(src) if s)
    out_text = " ".join(s for s in _alto_strings(translated) if s)
    if not out_text:
        fail(f"{translated.name}: no <String> CONTENT in output")
    if out_text == src_text:
        fail(f"{translated.name}: CONTENT identical to source — nothing was translated")

    logs = sorted(out_dir.glob(f"{base}_log.csv"))
    if len(logs) != 1:
        fail(f"expected 1 translation log CSV {base}_log.csv in {out_dir}, found {len(logs)}")
    with open(logs[0], encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    expected = ["file", "page_num", "line_num", f"text_{args.source_lang}", f"text_{args.target_lang}"]
    if header != expected:
        fail(f"{logs[0].name}: header {header} != {expected}")
    ok(f"translate interface: {translated.name} structure preserved, text changed, log CSV schema OK")


# ── teitok ─────────────────────────────────────────────────────────────────────


def check_teitok(args) -> None:
    """TEITOK output is well-formed TEI with the expected language, tokens, and an NLP application header.

    Matching is namespace-agnostic on purpose: the live writer (nlp-enrich
    api_util/teitok_alto.py) currently emits namespace-LESS TEI —
    `<TEI xmlnsoff="http://www.tei-c.org/ns/1.0" lang="cs">` (note `xmlnsoff`
    and plain `lang`, not `xml:lang`) — while the committed data_samples carry
    the TEI namespace and `xml:lang`. This check accepts both, so it keeps
    working when the repo-side cleanup lands either way.
    """
    doc = args.doc
    matches = sorted(Path(args.teitok_dir).rglob(f"{doc}.teitok.xml"))
    if len(matches) != 1:
        fail(f"expected exactly 1 {doc}.teitok.xml under {args.teitok_dir}, found {len(matches)}")
    path = matches[0]
    root = _parse_xml(path).getroot()
    if _local(root.tag) != "TEI":
        fail(f"{path.name}: root element is {root.tag}, expected TEI")
    lang = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("lang") or ""
    if args.lang and lang != args.lang:
        fail(f"{path.name}: document language is {lang!r} (xml:lang/lang), expected {args.lang!r}")

    apps: set = set()
    toks = 0
    named = 0
    for el in root.iter():
        name = _local(el.tag)
        if name == "application":
            apps.add(el.get("ident", ""))
        elif name == "tok":
            toks += 1
        elif name == "name":
            named += 1

    if "udpipe" not in apps:
        fail(f"{path.name}: no <application ident='udpipe'> in teiHeader (found {sorted(apps)})")
    if toks == 0:
        fail(f"{path.name}: no <tok> elements — UDPipe enrichment missing")
    note = f", {named} <name> entities" if named else ", no <name> entities (NameTag found none)"
    ok(f"teitok interface: {path.name} well-formed TEI, lang={lang}, {toks} tokens{note}")
    if args.require_entities and not named:
        fail(f"{path.name}: --require-entities set but no <name> elements present")


# ── keywords ───────────────────────────────────────────────────────────────────


def check_keywords(args) -> None:
    """llm-enrich *_enriched.json is a non-empty list of records with the enrichment schema."""
    doc = args.doc
    path = Path(args.llm_dir) / f"{doc}_enriched.json"
    if not path.is_file():
        # openrouter_client suffixes OUTPUT_DIR with the model slug when --output-dir
        # is not forced; accept a recursive match as a fallback.
        matches = sorted(Path(args.llm_dir).rglob(f"{doc}_enriched.json"))
        if len(matches) != 1:
            fail(f"expected {doc}_enriched.json under {args.llm_dir}, found {len(matches)}")
        path = matches[0]
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        fail(f"{path.name}: expected a non-empty JSON list of records")
    required = {"file_id", "page", "line", "original_text", "enrichment"}
    for i, rec in enumerate(records):
        missing = required - set(rec)
        if missing:
            fail(f"{path.name}: record {i} missing keys {sorted(missing)}")
        enrichment = rec["enrichment"]
        for key in ("extracted_keywords_cs", "extracted_keywords_en", "teater_category"):
            if key not in enrichment:
                fail(f"{path.name}: record {i} enrichment missing {key!r}")
        if not isinstance(enrichment["extracted_keywords_cs"], list):
            fail(f"{path.name}: record {i} extracted_keywords_cs is not a list")
    ok(f"keywords interface: {path.name} has {len(records)} schema-valid enrichment records")


# ── CLI ────────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pc", help="page-classification result table")
    p.add_argument("--tables", required=True, help="pc result/tables directory")
    p.set_defaults(func=check_pc)

    p = sub.add_parser("categ-header", help="fixture DOC_LINE_CATEG header vs alto HEAD CSV_HEADER")
    p.add_argument("--fixture", required=True, help="fixture DOC_LINE_CATEG CSV")
    p.add_argument("--langid", required=True, help="path to alto-postprocess langID_classify.py at HEAD")
    p.set_defaults(func=check_categ_header)

    p = sub.add_parser("alto", help="split + stats + extract outputs")
    p.add_argument("--doc", required=True, help="document id (e.g. CTX000000003)")
    p.add_argument("--page-alto", required=True, help="PAGE_ALTO output directory")
    p.add_argument("--stats-csv", required=True, help="alto stats CSV path")
    p.add_argument("--page-txt", required=True, help="PAGE_TXT output directory")
    p.set_defaults(func=check_alto)

    p = sub.add_parser("translate", help="translated ALTO + log CSV")
    p.add_argument("--source", required=True, help="source per-page ALTO file")
    p.add_argument("--out-dir", required=True, help="translator output directory")
    p.add_argument("--source-lang", default="cs")
    p.add_argument("--target-lang", default="en")
    p.set_defaults(func=check_translate)

    p = sub.add_parser("teitok", help="nlp TEITOK output")
    p.add_argument("--doc", required=True)
    p.add_argument("--teitok-dir", required=True, help="nlp TEITOK output directory")
    p.add_argument("--lang", default="cs", help="expected document language (default cs; '' disables)")
    p.add_argument("--require-entities", action="store_true", help="fail when no <name> elements are present")
    p.set_defaults(func=check_teitok)

    p = sub.add_parser("keywords", help="llm-enrich enriched JSON")
    p.add_argument("--doc", required=True)
    p.add_argument("--llm-dir", required=True, help="llm-enrich output directory")
    p.set_defaults(func=check_keywords)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())