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

A fourth check covers the one output that is not the record itself. With
``--teitok-dir``, nlp-enrich's TEITOK file for the document must exist, be TEI
with tokens, and contain every id the record points into:
``pages[].teitok_surface`` → ``<surface id>`` and ``entities[]``/``lines[].teitok_ref``
→ an element ``id``. See `assert_teitok()`.

RECORD SCHEMA 2.0 (atrium-project#84). Every record is read through
``migrate_document()``, so a stage image older than #84 (a 1.x record) is checked as the 2.0
record it migrates to; ``--require-current-major`` refuses any record not written at 2.x, which
is the E2E half of the proof gate before ``doc-schema-v2`` is tagged (D12). A 2.0 record carries
no run data: no ``provenance`` contributors and no ``assembled`` stamps, so a block's writer is
its grant (`BLOCK_OWNERS`), and who ran is the paradata's question, not this gate's.

With ``--seed``, the chain started from an AMČR seed (atrium-project#71), and every stage
must have kept its identity: the seed's ``doc_id``, ``source.sha512``, file name and media type.
The described ``source`` fields (origin, language, page count) are the record builder's: once a
stage record carries one, no later stage changes it. See `assert_seed_identity()`.

The branch follows ``source.origin``: ``digital`` is the born-digital branch
(`assert_digital_contract()`), anything else the scanned one. ``--expect-atr-pages`` asks for a
born-digital record some of whose pages the ATR re-acquired; ``--expect-layout`` for lines that
keep the docproc block they came from (``lines[].block``), from more than one block. A 1.x record
is checked on its own evidence (``needs_ocr`` pages; ``style`` and ``tables``), which 2.0 moved out
of the record.

The two read-outs of atrium-project#73 are checked on both branches. With
``--keywords-stage-ran true``, keyword-extract's statistical kind ran, so the record must carry
its ``keywords`` block: every keyword with its method, score and rank, one method per block,
ranks 1..n, pages that are pages of the record, and no controlled field in it
(`_assert_keywords()`). A ``quality_summary`` is checked whenever the record carries one
(``--quality-summary true`` requires it): no band anywhere in it, and equal to what
``atrium_document.quality_summary()`` computes from the stage record that last wrote it,
unchanged since (`_assert_quality_summary()`).

Usage:
    python tools/e2e/e2e_assert.py work/doc_json/5_llm.json \\
        --llm-stage-ran true \\
        --stages work/doc_json/1_pc.json ... work/doc_json/5_llm.json \\
        --teitok-dir work/nlp_out/TEITOK --seed work/seed.json
"""

import argparse
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
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
    SCHEMA_VERSION,
    SEED_SOURCE_REQUIRED,
    SOURCE_DESCRIBED_FIELDS,
    canonical_program,
    migrate_document,
    quality_summary,
    validate_document,
    validate_seed,
)

_CURRENT_MAJOR = int(SCHEMA_VERSION.split(".")[0])


def _load(json_path):
    """The record as the stage wrote it."""
    with open(json_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _major(record):
    """The MAJOR a record was written at (a record without `schema_version` counts as current)."""
    try:
        return int(str(record.get("schema_version", SCHEMA_VERSION)).split(".")[0])
    except (TypeError, ValueError):
        return _CURRENT_MAJOR


def _read(json_path):
    """`(as written, as read)`: the stage's record and the same record migrated to the current major."""
    raw = _load(json_path)
    return raw, migrate_document(copy.deepcopy(raw))


def assert_schema_valid(doc, json_path, written_major=None):
    """Layer D, against real pipeline output rather than a hand-written fixture.

    `doc` is the record as read: a record written at an older major (`written_major`) is
    validated after `migrate_document()`, which is how every 2.0 tool reads it.

    A missing `jsonschema` is a HARD failure here, deliberately unlike the
    per-repo write path (where the documented policy is one loud warning and
    carry on, so an upstream defect cannot stall a whole pipeline). This is a CI
    gate whose only job is to check the contract: degrading it to a warning would
    turn the one place the schema is enforced into a step that passes for the
    wrong reason. `jsonschema` travels with this script in
    tools/e2e/requirements.txt, so a RuntimeError here means the E2E environment
    is broken, not that the record is fine.
    """
    read_as = (
        f" (written at {written_major}.x, migrated)"
        if written_major is not None and written_major != _CURRENT_MAJOR
        else ""
    )
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
        lines = [f"❌ schema: {json_path}{read_as} does not validate against atrium_document.schema.json"]
        for err in errors:
            where = "/".join(str(p) for p in err.absolute_path) or "<root>"
            owner = _block_owner(err.absolute_path)
            lines.append(f"   • {where}: {err.message}" + (f"   [owned by {owner}]" if owner else ""))
        lines.append(f"   {len(errors)} violation(s). Each is fixed in the OWNING repo, then released —")
        lines.append("   `:latest` only moves on a version tag, so a fix on `test` cannot green this run.")
        raise SystemExit("\n".join(lines)) from None
    print(f"✅ schema: {json_path}{read_as} validates against atrium_document.schema.json {SCHEMA_VERSION}")


def assert_current_major(paths_and_majors, required):
    """Which major each record was written at; with `required`, every one must be the current one.

    Until each tool writes 2.0 the chain mixes majors, and the gate reads the older ones through
    `migrate_document()`. `--require-current-major` is the E2E half of the proof gate before the
    `doc-schema-v2` tag (D12): a record that only validates after migration has not been proven.
    """
    older = {path: major for path, major in paths_and_majors.items() if major != _CURRENT_MAJOR}
    if not older:
        print(f"✅ schema_version: every record written at {_CURRENT_MAJOR}.x")
        return
    listed = ", ".join(f"{Path(p).name} ({m}.x)" for p, m in older.items())
    assert not required, (
        f"❌ --require-current-major: written at an older major and only valid after migration: {listed}. "
        f"The stage images that wrote them have not adopted schema {SCHEMA_VERSION} yet."
    )
    print(f"ℹ️  schema_version: read through migrate_document(): {listed}")


def _block_owner(path):
    """Which tool owns the block a validation error sits in, so the report names the repo to fix.

    `path` is a jsonschema `absolute_path` deque like ``["entities", 0, "type_cnec"]``; only
    its first element identifies the block. Returns "" for structural keys, removed blocks and
    unknown blocks rather than guessing. A 2.0 record carries no stamp, so the grant
    (BLOCK_OWNERS) is the answer; for a field-split block it names the block's owner.
    """
    parts = list(path)
    if not parts:
        return ""
    owners = BLOCK_OWNERS.get(str(parts[0]))
    if not owners:
        return ""
    names = (owners,) if isinstance(owners, str) else owners
    # A predecessor and its successor (PROGRAM_SUCCESSORS) are one writer: name the current repo.
    return " or ".join(dict.fromkeys(canonical_program(n) for n in names))


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


def assert_seed_identity(seed_path, stage_paths, final_doc, final_path):
    """The AMČR seed's identity survives the whole chain (atrium-project#71).

    AMČR writes `doc_id` (its file id), `source.sha512` (the Fedora digest), the file name and the
    media type before the first stage. The fields that describe the original (`origin`,
    `language`, `page_count`) are the record builder's (contract §5). So, after every stage:

      * `doc_id` and the three identity fields are the seed's, unchanged;
      * a described field, once a stage record carries it, keeps its value in every later
        record: a stage that only passes the record on never rewrites it.

    The seed's `doc_id` deliberately differs from every file name in the chain (make_seed.py), so
    a stage that keys the record off its own input fails here, not in production. Records are
    compared as read (`migrate_document()`), so a 1.x origin is compared by its 2.0 value.
    """
    seed = _load(seed_path)
    try:
        validate_seed(seed)
    except RuntimeError as exc:
        raise SystemExit(f"❌ cannot validate the seed {seed_path}: {exc}") from exc
    except Exception as exc:
        raise AssertionError(f"❌ {seed_path} is not a valid AMČR seed: {exc}") from exc

    expected = {"doc_id": seed["doc_id"]}
    expected.update({f"source.{k}": seed["source"][k] for k in SEED_SOURCE_REQUIRED})
    paths = list(dict.fromkeys([*stage_paths, final_path]))
    described = {}
    for path in paths:
        doc = final_doc if path == final_path else _read(path)[1]
        source = doc.get("source") or {}
        got = {"doc_id": doc.get("doc_id")}
        got.update({f"source.{k}": source.get(k) for k in SEED_SOURCE_REQUIRED})
        changed = {k: (expected[k], got[k]) for k in expected if got[k] != expected[k]}
        assert not changed, (
            f"❌ {path} changed the seed's identity: "
            + "; ".join(f"{k}: seed {v[0]!r}, record {v[1]!r}" for k, v in sorted(changed.items()))
            + ". doc_id is inherited and source is first-writer-wins: no stage may rewrite either."
        )
        for field in SOURCE_DESCRIBED_FIELDS:
            if field not in source:
                continue
            first = described.setdefault(field, (path, source[field]))
            assert source[field] == first[1], (
                f"❌ {path} rewrote source.{field}: {first[1]!r} in {first[0]}, {source[field]!r} here. "
                f"It describes the original and is the record builder's; no later stage changes it."
            )

    origin = (final_doc.get("source") or {}).get("origin")
    print(
        f"✅ seed: doc_id {seed['doc_id']!r}, sha512, file name and media type kept across "
        f"{len(paths)} record(s); source.origin {origin!r}"
    )


# Older TEITOK exports (nlp-enrich format 1) close <name> with </n>: not well-formed XML.
_NAME_CLOSE = re.compile(r"</n\s*>")
_PB_ID = re.compile(r"pb-(\d+)")
#: The element a record's teitok_ref must name, per block.
_REF_TAGS = {"entities": "name", "lines": "s"}


def _local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""


def _parse_teitok(path):
    """The TEITOK root, after repairing the legacy ``</n>`` close tag (reported, not fatal)."""
    text, repaired = _NAME_CLOSE.subn("</name>", Path(path).read_text(encoding="utf-8"))
    if repaired:
        print(f"ℹ️  {Path(path).name}: {repaired} legacy </n> close tag(s) repaired before parsing")
    return ET.fromstring(text)


def _pages_in_force(root):
    """Element id -> the page of the ``<pb>`` in force where the element starts: the K of
    ``pb-K`` (the writer's page number, the one the record uses), else ``pb@n``. A ``<pb>``
    inside an element (a sentence or entity running over a page break) comes after its
    start, so the element stays on the page it starts on -- its first token's page."""
    page, out = None, {}
    for el in root.iter():
        if _local(el.tag) == "pb":
            m = _PB_ID.fullmatch(el.get("id") or "")
            page = m.group(1) if m else (el.get("n") or page)
        elif el.get("id"):
            out[el.get("id")] = page
    return out


def _teitok_format(root):
    """The writer's format stamp: ``<application ident="atrium-nlp-enrich" version=...>``."""
    for el in root.iter():
        if el.tag.split("}")[-1] == "application" and el.get("ident") == "atrium-nlp-enrich":
            return el.get("version")
    return None


def assert_teitok(doc, teitok_dir, written=None):
    """nlp-enrich's TEITOK file agrees with the record that points into it.

    The record's `pages[].teitok_surface` and `entities[].teitok_ref` are TEITOK-local
    ids (`facs-1`, `n-5`), so a record can only be read together with the file. Nothing
    else checks that the two agree: nlp-enrich's own XSD gate sees only the XML, and
    the schema sees only the record.

    Surfaces must always resolve. For TEITOK format 2 (`version="teitok-2"`), whose
    writer and document hook take their ids and pages from one parse, entity/line refs
    must resolve *to the right element* (`entities[]` to a `<name>`, `lines[]` to an `<s>`)
    and every entity's `page` must be the page of the `<pb>` in force where its `<name>`
    starts. That last check is the one that would have caught nlp-enrich#38: pages taken
    from UDPipe's chunks put entities on one page in the record and under another `<pb>` in
    the TEITOK. Format-1 files (older images) numbered entities in two places, so a
    mismatch there is reported but does not fail.

    Which file: nlp-enrich names it after its own input, which differs from `doc_id` whenever the
    record was seeded by an archive (atrium-project#71). A 2.0 record names no file (the paradata
    lists the outputs by distribution name), so the gate takes `<doc_id>.teitok.xml`, else the
    one TEITOK file of this single-document run; a 1.x record (`written`) still names it in
    `derived_from.teitok`.
    """
    doc_id = doc.get("doc_id")
    named = Path(str(((written or {}).get("derived_from") or {}).get("teitok") or "")).name
    names = [n for n in (named, f"{doc_id}.teitok.xml") if n]
    matches = []
    for name in names:
        matches = sorted(Path(teitok_dir).rglob(name))
        if matches:
            break
    if not matches:
        found = sorted(Path(teitok_dir).rglob("*.teitok.xml"))
        if len(found) == 1:
            matches = found
            print(f"ℹ️  teitok: no {' or '.join(names)}; taking the run's one TEITOK file, {found[0].name}")
    assert matches, (
        f"❌ no {' or '.join(names)} under {teitok_dir} (and not exactly one *.teitok.xml): nlp-enrich "
        f"ran with SAVE_TEITOK=true but wrote no TEITOK for this document"
    )
    path = matches[0]
    root = _parse_teitok(path)
    assert _local(root.tag) == "TEI", f"❌ {path}: root is <{root.tag}>, not <TEI>"
    tokens = [el for el in root.iter() if _local(el.tag) == "tok"]
    assert tokens, f"❌ {path}: no <tok> — the TEITOK carries no text"

    ids = {el.get("id"): _local(el.tag) for el in root.iter() if el.get("id")}
    surfaces = {el.get("id") for el in root.iter() if _local(el.tag) == "surface"}
    for page in doc.get("pages") or []:
        ref = page.get("teitok_surface")
        if ref is None:
            continue
        assert ref in surfaces, (
            f"❌ pages[{page.get('page')!r}].teitok_surface = {ref!r} is not a <surface id> in "
            f"{path.name} (surfaces: {sorted(surfaces)})"
        )

    fmt = _teitok_format(root)
    rows = [(block, row) for block in ("entities", "lines") for row in doc.get(block) or [] if row.get("teitok_ref")]
    refs = [(block, row["teitok_ref"]) for block, row in rows]
    missing = [(block, ref) for block, ref in refs if ref not in ids]
    wrong_kind = [(block, ref, ids[ref]) for block, ref in refs if ref in ids and ids[ref] != _REF_TAGS[block]]
    in_force = _pages_in_force(root)
    wrong_page = [
        (row["teitok_ref"], str(row.get("page")), in_force[row["teitok_ref"]])
        for block, row in rows
        if block == "entities"
        and in_force.get(row["teitok_ref"]) is not None
        and str(row.get("page")) != in_force[row["teitok_ref"]]
    ]
    if fmt == "teitok-2":
        problems = []
        if missing:
            problems.append(f"{len(missing)} teitok_ref(s) point at no element: {missing[:5]}")
        if wrong_kind:
            problems.append(
                f"{len(wrong_kind)} teitok_ref(s) point at the wrong element (entities -> <name>, "
                f"lines -> <s>): {wrong_kind[:5]}"
            )
        if wrong_page:
            problems.append(
                f"{len(wrong_page)} entit(y/ies) on another page than the <pb> in force at their "
                f"<name> — (ref, record page, TEITOK page): {wrong_page[:5]}"
            )
        if problems:
            raise AssertionError(f"❌ {path.name}: " + "; ".join(problems))
    elif missing or wrong_kind or wrong_page:
        print(
            f"⚠️  {path.name}: {len(missing)} unresolved, {len(wrong_kind)} mistyped and "
            f"{len(wrong_page)} mis-paged teitok_ref(s) of {len(refs)}; tolerated for a TEITOK "
            f"file without the teitok-2 stamp (format {fmt!r}) — they do not resolve reliably"
        )
    print(
        f"✅ teitok: {path.name} ({fmt or 'format 1'}) — {len(tokens)} token(s), "
        f"{len(surfaces)} surface(s), {len(refs) - len(missing)}/{len(refs)} ref(s) resolve"
    )


def _assert_enrichment(doc, llm_stage_ran):
    """The keyword-extract `enrichment` block check (formerly llm-enrich's), shared by both branches (G5).

    A 2.0 record carries no stamp, so "the stage ran" comes from the workflow's gate
    (`--llm-stage-ran`); `auto` infers it from the block itself, for a manual run.
    """
    if llm_stage_ran == "auto":
        llm_stage_ran = "enrichment" in doc
        print(
            f"ℹ️  --llm-stage-ran not given; inferring the llm stage {'ran' if llm_stage_ran else 'was skipped'} "
            f"from the record's blocks. CI always passes the gate's value explicitly."
        )
    if llm_stage_ran:
        assert "enrichment" in doc, (
            "❌ 'enrichment' block missing from the llm stage.\n"
            "   The stage is REQUIRED to write this block whenever it reached the model, "
            "including when the model located nothing — an empty `items` list is how 'ran and "
            "found nothing' is told apart from 'never ran'. A run that could NOT reach the "
            "model writes no record and exits non-zero instead, so it fails at its own step "
            "rather than here.\n"
            "   So a record arriving here without the block means one of: the image is older "
            "than that contract (atrium-project#49 — check the image tag this run pulled); or a "
            "tool downstream of it dropped the block; or the file handed to this assert is not "
            "the llm stage's output at all but the baseline that went into it."
        )
        # Reported, NOT asserted. Whether a live model finds archaeology in a fixture is a
        # model-quality question and pinning it would make the gate flap on provider drift;
        # what this gate owns is the integration contract. But a run that enriches zero
        # passages every night is a fixture problem worth seeing in the log rather than
        # discovering when someone finally reads the artifact — which is how #49 went.
        items = (doc.get("enrichment") or {}).get("items") or []
        if items:
            print(f"✅ enrichment: {len(items)} item(s)")
        else:
            print(
                "⚠️  enrichment: block present but EMPTY — the stage ran and located nothing. "
                "Valid, and not a failure, but if it is empty on every run the smoke is only "
                "proving the plumbing: check the fixture actually contains archaeological "
                "content (atrium-project#49)."
            )
    else:
        print(
            "ℹ️  the llm stage did not run — 'enrichment' block not required. "
            "This is the OPENROUTER_KEY-absent path the smoke workflows allow."
        )


#: Fields of a controlled `enrichment` item; none may appear on a statistical keyword.
_CONTROLLED_FIELDS = ("teater_category", "teater_category_ids", "extracted_keywords_cs", "extracted_keywords_en")


def _assert_keywords(doc, keywords_stage_ran):
    """keyword-extract's `keywords` block (atrium-project#73), when its statistical kind ran.

    Asserted: the block, the four fields of every keyword, ranks 1..n in each list, one method per
    block, page labels that are the record's, and the separation from `enrichment`.
    Reported: an empty document list (what a method finds in a fixture is not this gate's question).
    """
    if keywords_stage_ran == "auto":
        keywords_stage_ran = "keywords" in doc
        print(
            f"ℹ️  --keywords-stage-ran not given; inferring the statistical kind "
            f"{'ran' if keywords_stage_ran else 'did not run'} from the record's blocks."
        )
    if not keywords_stage_ran:
        print("ℹ️  keyword-extract's statistical kind did not run — 'keywords' block not required.")
        return
    block = doc.get("keywords")
    assert isinstance(block, dict), (
        "❌ 'keywords' block missing: keyword-extract's statistical kind ran on this record and did not "
        "write it (an image older than v1.2.0-beta?), or a later stage dropped it."
    )
    labels = {str(row.get("page")) for key in ("pages", "lines") for row in doc.get(key) or [] if isinstance(row, dict)}
    lists = [("document", block.get("document") or [])]
    for group in block.get("pages") or []:
        page = str(group.get("page"))
        assert page in labels, f"❌ keywords: page {page!r} is not a page of the record ({sorted(labels)})"
        lists.append((f"page {page}", group.get("keywords") or []))
    methods = set()
    for where, items in lists:
        for rank, item in enumerate(items, start=1):
            missing = [f for f in ("keyword", "method", "score", "rank") if f not in item]
            assert not missing, f"❌ keywords, {where}: {item} has no {missing}"
            assert item["rank"] == rank, (
                f"❌ keywords, {where}: the ranks are {[i.get('rank') for i in items]}, not 1..{len(items)} in order"
            )
            mixed = [f for f in _CONTROLLED_FIELDS if f in item]
            assert not mixed, (
                f"❌ keywords, {where}: {item['keyword']!r} carries {mixed}: the controlled kind belongs in "
                "'enrichment', and the two kinds are never one list"
            )
            methods.add(item["method"])
    assert len(methods) <= 1, f"❌ keywords: one run writes one method's lists, this block mixes {sorted(methods)}"
    for item in (doc.get("enrichment") or {}).get("items") or []:
        assert not {"method", "rank"} & set(item), f"❌ enrichment item {item} carries a statistical keyword's fields"
    method = next(iter(methods), None)
    if block.get("document"):
        print(
            f"✅ keywords: {len(block['document'])} document keyword(s) and {len(block.get('pages') or [])} "
            f"page list(s) by {method!r}"
        )
    else:
        print("⚠️  keywords: block present, but the document list is EMPTY")


def _keys(node):
    """Every mapping key at any depth of `node`."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


def _assert_quality_summary(doc, stage_paths, quality_summary_expected, written_major=None):
    """The record builder's `quality_summary` (atrium-project#73 R6), wherever a record carries one.

    The block has one writer, the record builder, which is the first stage that carries it. It
    must be what `quality_summary()` computes from that stage record, and the final record must
    carry it unchanged. Without stage records the final record is used, and a difference is
    reported, not asserted. A 1.x record's block is recomputed by `migrate_document()` (the
    migration rewrites the rows it reads), so it proves nothing about the writer and is not
    compared.
    """
    block = doc.get("quality_summary")
    if block is None:
        assert quality_summary_expected is not True, (
            "❌ 'quality_summary' missing: the record builder (ocr-postprocess) writes it whenever it "
            "writes or scores pages and lines"
        )
        print("ℹ️  no 'quality_summary' in this record")
        return
    bands = sorted({k for k in _keys(block) if "band" in str(k).lower()})
    assert not bands, f"❌ quality_summary carries {bands}: it is numbers, the bands are computed at index time"
    if written_major is not None and written_major != _CURRENT_MAJOR:
        print(
            f"ℹ️  quality_summary: recomputed by the {written_major}.x→{_CURRENT_MAJOR}.0 migration; the writer is not compared"
        )
        return
    writer = None
    for path in stage_paths:
        raw, record = _read(path)
        if record.get("quality_summary") is not None:
            writer = (Path(path).name, raw, record)
            break
    if writer is not None:
        name, raw, record = writer
        if _major(raw) == _CURRENT_MAJOR:
            expected = quality_summary(record)
            assert record.get("quality_summary") == expected, (
                f"❌ quality_summary in {name} is not quality_summary() of that record:\n"
                f"   written:  {record.get('quality_summary')}\n   computed: {expected}"
            )
        assert block == record.get("quality_summary"), f"❌ quality_summary changed after {name} wrote it"
        print(f"✅ quality_summary: {name}'s read-out of its pages and lines, unchanged since: {block}")
        return
    expected = quality_summary(doc)
    if block == expected:
        print(f"✅ quality_summary: this record's read-out of its pages and lines: {block}")
    else:
        print(
            "⚠️  quality_summary differs from quality_summary() of this record, and no --stages record "
            f"carries it to check it against: {block} vs {expected}"
        )


def _atr_pages(doc, written):
    """The pages of a born-digital record whose text the ATR re-acquired, as page labels.

    2.0: the pages of the lines whose `text_source` is `atr` (the route step sent them to the
    ATR, and the record builder kept the source of each line, D25). A 1.x record has no such
    field (its migration takes every line's source from `source.origin`), so its evidence is the
    converter's `needs_ocr` page verdict, which 2.0 moved out of the record.
    """
    if _major(written) == _CURRENT_MAJOR:
        pages = {str(ln.get("page")) for ln in doc.get("lines") or [] if ln.get("text_source") == "atr"}
    else:
        pages = {str(p.get("page")) for p in written.get("pages") or [] if p.get("needs_ocr")}
    return sorted(pages)


def assert_positional_blocks(doc):
    """What the one writer of the positional blocks (the record builder, D20) guarantees beyond the schema.

    The schema checks each row; these checks span rows. Every line says where its text came from
    (`text_source`); a page row and the lines agree on whether the page has text (an `empty` page
    has no line, a `text` page has one). Checked where the record carries lines: the scanned smoke
    skips line classification and has none.
    """
    lines = doc.get("lines")
    if not lines:
        print("ℹ️  positional: no lines[] on this record — the line checks are not exercised")
        return
    missing = [(ln.get("page"), ln.get("line")) for ln in lines if not ln.get("text_source")]
    assert not missing, (
        f"❌ {len(missing)} line(s) without text_source (page, line): {missing[:5]}. The record builder "
        "says for every line whether its text is the text layer, the ATR or legacy ALTO (D25)."
    )
    with_lines = {str(ln.get("page")) for ln in lines}
    disagree = [
        (p.get("page"), p.get("content_status"))
        for p in doc.get("pages") or []
        if p.get("content_status") in ("text", "empty")
        and (p.get("content_status") == "text") != (str(p.get("page")) in with_lines)
    ]
    assert not disagree, (
        f"❌ pages[].content_status disagrees with lines[] (page, status): {disagree[:5]}. "
        "An empty page has no lines and a page with text has some (D29)."
    )
    sources = sorted({ln["text_source"] for ln in lines})
    print(f"✅ positional: {len(lines)} line(s), text_source {sources}; content_status agrees with lines[]")


def assert_digital_contract(doc, json_path, written=None):
    """The born-digital branch (`source.origin: digital`).

    W10. This is NOT a shorter version of the scanned contract — it is a different
    one, and the difference is the point. A born-digital record can never carry
    `page_categories` (no page image exists to classify), `translations` or
    `entities` (translator and nlp-enrich both need the scanned branch's output,
    which never exists on this branch). Asserting the scanned blocks here would not
    be "stricter", it would be wrong.

    Since 2.0 the positional blocks have one writer, the record builder (D20): digital-convert
    writes docproc, and the route step, not the record, decides which pages go to the ATR. So
    there is no originator arbitration left to check; which pages the ATR re-acquired is read
    from the lines (`_atr_pages()`).
    """
    written = doc if written is None else written
    origin = (doc.get("source") or {}).get("origin")
    print(f"ℹ️  born-digital branch: source.origin = {origin!r}")

    assert "pages" in doc, "❌ 'pages' block missing: the record builder wrote no pages"
    assert "lines" in doc, "❌ 'lines' block missing: the record builder wrote no lines"

    # Blocks that CANNOT exist here. A record carrying them means either the branch
    # was fed a scanned document, or a tool wrote a block it does not own.
    for forbidden, why in (
        ("page_categories", "no page image exists to classify on this branch"),
        ("translations", "the translator needs the scanned branch's PAGE_ALTO output"),
        ("entities", "nlp-enrich needs the DOC_LINE_CATEG classify CSV and INPUT_ALTO_DIR"),
    ):
        assert forbidden not in doc, (
            f"❌ '{forbidden}' present on a born-digital record — {why}. Either the fixture "
            f"is not actually born-digital, or a tool wrote a block it does not own."
        )

    return doc.get("pages") or [], _atr_pages(doc, written)


def _assert_layout_1x(written):
    """A 1.x record's layout cues (llm-enrich#18): a heading and a region in `lines[].style`, and
    tables at least one cell of which joins a line by `group_id`. 2.0 moved all three to docproc."""
    lines = written.get("lines") or []
    headings = [ln for ln in lines if (ln.get("style") or {}).get("heading_level")]
    assert headings, (
        "❌ --expect-layout: no line carries style.heading_level. The converter recovered no "
        "heading from a fixture built to have them — the layout is being flattened."
    )
    regions = {}
    for line in lines:
        region = (line.get("style") or {}).get("region")
        if region:
            regions[region] = regions.get(region, 0) + 1
    assert regions, (
        "❌ --expect-layout: no line carries style.region. The fixture's running header, footer "
        "or footnote reached the record as body text."
    )
    print(f"✅ {len(headings)} heading line(s); regions {dict(sorted(regions.items()))} (1.x record)")
    line_groups = {ln.get("group_id") for ln in lines if ln.get("group_id")}
    for table in written.get("tables") or []:
        cell_groups = {cell.get("group_id") for cell in table.get("cells") or [] if cell.get("group_id")}
        assert cell_groups & line_groups, (
            f"❌ --expect-layout: table {table.get('table_id')!r} on page {table.get('page')!r} has "
            f"{len(cell_groups)} cell group_id(s) and none of them is carried by a line."
        )


def assert_layout(doc, written=None):
    """The born-digital layout, for a fixture that has one (llm-enrich#18; 2.0: D26).

    Since 2.0 the layout (headings, regions, tables, reading order) is docproc's, not the
    record's; the record keeps, for each line, the docproc block it came from (`lines[].block`),
    which is the join back to that layout. So a fixture built with a layout (`rich.docx`,
    `two_column.pdf`) must give lines that all name a block, from more than one block: a
    converter that flattened the page into one block fails, and so does `minimal.pdf`.
    A 1.x record is checked on its own cues (`_assert_layout_1x()`).
    """
    written = doc if written is None else written
    if _major(written) != _CURRENT_MAJOR:
        _assert_layout_1x(written)
        return
    lines = [ln for ln in doc.get("lines") or [] if ln.get("text")]
    unjoined = [(ln.get("page"), ln.get("line")) for ln in lines if not ln.get("block")]
    assert lines and not unjoined, (
        f"❌ --expect-layout: {len(unjoined)} of {len(lines)} line(s) name no docproc block (page, line): "
        f"{unjoined[:5]}. Without lines[].block the record cannot be joined back to the layout."
    )
    blocks = {(str(ln.get("page")), ln["block"]) for ln in lines}
    assert len(blocks) > 1, (
        f"❌ --expect-layout: every line comes from one block ({sorted(blocks)}): the layout of a fixture "
        "built to have one was flattened."
    )
    print(f"✅ layout: {len(lines)} line(s) joined to {len(blocks)} docproc block(s)")


def assert_document_contract(
    json_path,
    llm_stage_ran="auto",
    stage_paths=(),
    expect_atr_pages=False,
    teitok_dir=None,
    expect_layout=False,
    seed=None,
    keywords_stage_ran=False,
    quality_summary_expected="auto",
    require_current_major=False,
):
    written, doc = _read(json_path)
    written_major = _major(written)

    # 0. The contract itself, before any block-by-block check: a record that does
    #    not validate is broken whatever else it contains (D4).
    assert_schema_valid(doc, json_path, written_major)
    assert_doc_id_stable(list(stage_paths), doc, json_path)
    majors = {path: _major(_load(path)) for path in stage_paths}
    majors[json_path] = written_major
    assert_current_major(majors, require_current_major)
    if seed:
        assert_seed_identity(seed, list(stage_paths), doc, json_path)
    assert_positional_blocks(doc)

    # 0b. W10: which contract applies is derived from the RECORD, not from a flag:
    #     `source.origin` says how the text was obtained, and only the born-digital branch
    #     reads a text layer.
    origin = (doc.get("source") or {}).get("origin")
    if origin == "digital":
        pages, atr_pages = assert_digital_contract(doc, json_path, written)

        if expect_atr_pages:
            # The garbled fixture's whole purpose is to send pages to the ATR. This is the
            # assertion that must NOT be able to pass vacuously: a fixture whose text layer
            # decodes cleanly would satisfy "no page went to the ATR" trivially, and prove nothing.
            assert atr_pages, (
                "❌ expected at least one page re-acquired by the ATR, got none. The garbled "
                "fixture's whole purpose is to trip decode-sanity; if it stopped doing so, "
                "this gate is now vacuous and the hand-off to the ATR is untested."
            )
            print(f"✅ page(s) {atr_pages} re-acquired by the ATR")
        else:
            assert not atr_pages, (
                f"❌ page(s) {atr_pages} unexpectedly went to the ATR on the happy-path fixture. "
                "Either the fixture regressed or decode-sanity became over-eager."
            )
            for line in doc.get("lines") or []:
                assert line.get("text"), (
                    f"❌ line {line.get('line')!r} on page {line.get('page')!r} has no text on the "
                    "happy path; a born-digital PDF's text layer is the whole input."
                )
            print(f"✅ {len(pages)} page(s), all lines carry text, no page went to the ATR")

        if expect_layout:
            assert_layout(doc, written)

        _assert_enrichment(doc, llm_stage_ran)
        _assert_keywords(doc, keywords_stage_ran)
        _assert_quality_summary(doc, list(stage_paths), quality_summary_expected, written_major)
        print(f"✅ e2e_assert.py: born-digital contract verified for {json_path}")
        return

    # A flag that silently does nothing would let a mis-wired stage pass: both are born-digital
    # contracts, and a scanned record has nothing for them to check.
    for flag, given in (("--expect-layout", expect_layout), ("--expect-atr-pages", expect_atr_pages)):
        assert not given, (
            f"❌ {flag} applies to the born-digital branch only, but source.origin is {origin!r}. "
            f"The stage fed this check the wrong record."
        )

    # ── the scanned branch ──────────────────────────────────────────────────────

    # 1. The record builder: 'pages' and 'content' must exist, and 'page_categories'
    #    must survive from page-classification (a stage that set blocks rather than
    #    merging them erases it). 'lines' is legitimately absent: SKIP_CLASSIFY=true in E2E.
    assert "pages" in doc, "❌ 'pages' block missing: Contributions were erased"
    assert "page_categories" in doc, (
        "❌ 'page_categories' block missing: a later stage erased page-classification's block"
    )
    assert "content" in doc, "❌ 'content' block missing: the record builder wrote no content"

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

    # 3. Translator. `translations` is reserved since 2.0 (contract §5: the pilot translates the
    #    record-level metadata into its own distribution, never the full text), so it is not
    #    required; an image older than #84 still writes it, and then it must stay metadata.
    trans_block = doc.get("translations")
    if trans_block is None:
        print("ℹ️  no 'translations' block (reserved since schema 2.0; not required)")
    else:
        for trans in trans_block if isinstance(trans_block, list) else [trans_block]:
            assert "source_lang" in trans, "❌ Translation missing 'source_lang'"
            assert "target_lang" in trans, "❌ Translation missing 'target_lang'"
            assert "backend" in trans, "❌ Translation missing 'backend'"
            assert "text" not in trans, "❌ 'translations' contains raw corpus text instead of metadata schema"
        print("ℹ️  'translations' present (reserved since schema 2.0): metadata only, no text")

    # 4. The llm stage — conditional on it having run.
    _assert_enrichment(doc, llm_stage_ran)

    # 4b. atrium-project#73: keyword-extract's statistical keywords, the record builder's summary.
    _assert_keywords(doc, keywords_stage_ran)
    _assert_quality_summary(doc, list(stage_paths), quality_summary_expected, written_major)

    # 5. NLP Enrich: the TEITOK file the record points into (only when asked for).
    if teitok_dir:
        assert_teitok(doc, teitok_dir, written)

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
        "'enrichment' block is not required (G5); auto = infer from the "
        "record's blocks, for a manual run against a downloaded artifact.",
    )
    parser.add_argument(
        "--expect-atr-pages",
        "--expect-needs-ocr",
        dest="expect_atr_pages",
        action="store_true",
        help="born-digital branch only: require at least one page the ATR re-acquired (lines with "
        "text_source atr; a 1.x record's needs_ocr pages). Without this the happy path is asserted "
        "instead: no page went to the ATR and every line carries text. --expect-needs-ocr is the "
        "flag's 1.x name, kept for the existing workflows.",
    )
    parser.add_argument(
        "--expect-layout",
        action="store_true",
        help="born-digital branch only: require lines that name their docproc block (lines[].block), "
        "from more than one block; a 1.x record's style.heading_level, style.region and table joins. "
        "For fixtures built with a layout (rich.docx, two_column.pdf).",
    )
    parser.add_argument(
        "--stages",
        nargs="*",
        default=[],
        metavar="RECORD",
        help="every per-stage record in pipeline order. doc_id must be identical "
        "across all of them and equal to the final record's.",
    )
    parser.add_argument(
        "--teitok-dir",
        default=None,
        metavar="DIR",
        help="scanned branch: nlp-enrich's TEITOK_OUTPUT_DIR. The document's .teitok.xml "
        "must exist, be TEI with tokens, and contain every <surface id> / teitok_ref the "
        "record points at.",
    )
    parser.add_argument(
        "--seed",
        default=None,
        metavar="SEED",
        help="the AMČR seed the chain started from (tools/e2e/make_seed.py): every stage must keep its "
        "doc_id, source.sha512, file name and media type, and no stage may change a described source "
        "field (origin, language, page_count) once one carries it.",
    )
    parser.add_argument(
        "--keywords-stage-ran",
        type=_tri_state,
        default=False,
        help="true when keyword-extract's statistical kind ran on this record: its 'keywords' block "
        "(atrium-project#73) is then required and checked; auto = infer from the record's blocks.",
    )
    parser.add_argument(
        "--quality-summary",
        type=_tri_state,
        default="auto",
        help="true = ocr-postprocess's 'quality_summary' is required; auto (default) = checked when "
        "present; false = not required (still checked when present).",
    )
    parser.add_argument(
        "--require-current-major",
        action="store_true",
        help=f"every record (--stages and the final one) must be written at schema {SCHEMA_VERSION.split('.')[0]}.x, "
        "not only valid after migrate_document(): the E2E half of the doc-schema-v2 proof gate (D12).",
    )
    args = parser.parse_args(argv)

    assert_document_contract(
        args.record,
        llm_stage_ran=args.llm_stage_ran,
        stage_paths=args.stages,
        expect_atr_pages=args.expect_atr_pages,
        teitok_dir=args.teitok_dir,
        expect_layout=args.expect_layout,
        seed=args.seed,
        keywords_stage_ran=args.keywords_stage_ran,
        quality_summary_expected=args.quality_summary,
        require_current_major=args.require_current_major,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
