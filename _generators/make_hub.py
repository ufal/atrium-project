#!/usr/bin/env python3
"""Generate the hub site tree DRAFTS (issue #57, round 2).

Every page is a SHELL: frontmatter, purpose, a sources table, and an outline whose
sections carry `<!-- ASSEMBLER: -->` markers. No prose is copied from any source --
that is next round's work, and "nothing moves" forbids copying anyway.

Source pointers are produced by READING the repositories with a fence-aware heading
parser (headings.py), not from memory, so a marker cannot name a section that does
not exist.
"""

from __future__ import annotations

import pathlib

from headings import headings, phantom_count  # noqa: E402
from hub_spec import EXTRA_DOCS, EXTRA_SECTIONS, ROLE_PURPOSE, route  # noqa: E402
from repos import REPOS  # noqa: E402

TREE = pathlib.Path("/home/user")
OUT = pathlib.Path(__file__).parent.parent / "hub"
SITE = OUT / "docs_site"
GENERATED = "2026-09-19"
HUB = "atrium-project"

DRAFT_BANNER = """!!! warning "Draft shell — issue #57, round 2 ({generated})"
    This page carries its **outline and source pointers only**. The prose is
    assembled at build time from the sources listed below, or authored in round 3
    where the table says `AUTHORED`. Nothing on this page is copied from a source
    file: `README.md` and `CONTRIBUTING.md` stay canonical and full-length in their
    own repositories, and the split is regenerated on every build so it cannot
    drift from what it came from.
"""


def fm(title: str, nav: int, **extra) -> str:
    lines = ["---", f"title: {title}", f"nav_order: {nav}", "status: draft", "round: 2", "issue: 57"]
    for k, v in extra.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def sources_table(rows: list[tuple[str, str, str, str]]) -> str:
    if not rows:
        return (
            "| Source | Section | Depth | Treatment |\n|---|---|---|---|\n"
            "| _none_ | — | — | **AUTHORED** — no existing source; written in round 3 |\n"
        )
    out = ["| Source | Section | Depth | Treatment |", "|---|---|---|---|"]
    for src, section, depth, treat in rows:
        # An em-dash marks "no source file" (an AUTHORED page). Backticking it would
        # render a code span around a dash and make it look like a path.
        cell = "—" if src == "—" else f"`{src}`"
        out.append(f"| {cell} | {section} | {depth} | {treat} |")
    return "\n".join(out) + "\n"


def marker(src: str, section: str, depth: str, note: str = "") -> str:
    bits = [f'source="{src}"', f'section="{section}"', f"depth={depth}"]
    if note:
        bits.append(f'note="{note}"')
    return f"<!-- ASSEMBLER: {' '.join(bits)} -->"


def page(title, nav, purpose, src_rows, outline, extra_fm=None, tail="") -> str:
    parts = [
        fm(title, nav, **(extra_fm or {})),
        "",
        f"# {title}",
        "",
        DRAFT_BANNER.format(generated=GENERATED),
        "",
        "## Purpose",
        "",
        purpose,
        "",
        "## Sources",
        "",
        sources_table(src_rows),
        "",
        "## Outline",
        "",
    ]
    parts.extend(outline)
    if tail:
        parts += ["", tail]
    parts.append("")
    return "\n".join(parts)


def write(rel: pathlib.Path, text: str) -> None:
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_text(text)


# ---------------------------------------------------------------- hub pages


def hub_pages() -> list[tuple[pathlib.Path, str]]:
    _D = f"{HUB}/docs"
    out = []

    out.append(
        (
            SITE / "index.md",
            page(
                "ATRIUM — UFAL documentation",
                1,
                "The portal. A reader arriving cold leaves knowing what ATRIUM is, which six "
                "repositories exist, what each one does, and which of the three entry points "
                "(Pipelines, External tools, a tool section) answers their question.",
                [
                    (
                        f"{HUB}/README.md",
                        "whole file (1,094 B)",
                        "—",
                        "render — the hub README is short enough to render whole",
                    ),
                    ("—", "portal copy, the six-card grid, the pipeline strip", "—", "**AUTHORED**"),
                ],
                [
                    marker(f"{HUB}/README.md", "*", "2", "whole file"),
                    "",
                    "### What ATRIUM is",
                    "",
                    "### The six repositories",
                    "",
                    "### Start here",
                    "",
                    "- **[Pipelines](pipelines.md)** — what the tools do, end to end",
                    "- **[External tools & services](external-tools.md)** — the glossary, if a name is unfamiliar",
                    "- **[Repository map](ecosystem/repository-map.md)** — which repo owns what",
                    "",
                    "### How this site is built",
                    "",
                    "<!-- one paragraph: derived at build time from untouched sources; link to issue #57 -->",
                ],
            ),
        )
    )

    out.append(
        (
            SITE / "pipelines.md",
            page(
                "Pipelines",
                2,
                "Understand every ATRIUM workflow from beginning to end — what goes in, what "
                "each stage does, what comes out, and what the point of it is. This is the page "
                "issue #57's 2026-09-17 TODO asks for.",
                [
                    ("—", "the two-layer model and all 13 workflows", "—", "**AUTHORED** — see note below"),
                    (f"{HUB}/docs/document_schema.md", "`## ` the accretion rules", "2", "reference, not copied"),
                    ("atrium-alto-postprocess/README.md", "`## 🛤️ Workflow Stages` (42,775 B)", "3", "reference"),
                    ("atrium-translator/README.md", "`## 🧠 Logic Overview`", "3", "reference"),
                    ("atrium-nlp-enrich/README.md", "`## Workflow Stages`", "3", "reference"),
                    (
                        f"{HUB}/.github/workflows/e2e-pipeline-smoke.yml",
                        "header + stage steps",
                        "—",
                        "reference (the real integration contract)",
                    ),
                    (f"{HUB}/.github/workflows/e2e-digital-smoke.yml", "header", "—", "reference (born-digital path)"),
                ],
                [
                    "### The correction this page makes",
                    "",
                    "<!-- AUTHORED. Every existing diagram in the corpus draws five boxes with arrows",
                    "     between them. Verified against the tree 2026-09-17:",
                    "       * no repo reads TRANSLATED/  (0 hits in all four downstream repos)",
                    "       * nlp-enrich reads DOC_LINE_CATEG/ + the ORIGINAL ALTO/ (config_api.txt:2,15)",
                    "       * alto never consumes page_categories (hits are vendored schema only)",
                    "     So the file topology is a DAG that fans out from alto and terminates at the",
                    "     translator; what is linear is the RECORD. Draw both layers. -->",
                    "",
                    "### Layer 1 — the file DAG",
                    "",
                    '!!! note "Diagram — authored in round 3"',
                    "    A Mermaid `flowchart LR` fanning out from `alto-postprocess`, with the",
                    "    translator drawn as a terminal branch. It is written as a note rather than",
                    "    an empty ```` ```mermaid ```` fence on purpose: mermaid.js throws a visible",
                    "    parse error on a fence with no nodes, and `mkdocs build --strict` cannot",
                    "    see it, so an empty fence ships a red error box to every reader.",
                    "",
                    "### Layer 2 — the record accretion chain",
                    "",
                    '!!! note "Diagram — authored in round 3"',
                    "    A linear Mermaid chain: each stage writes only the block it owns and",
                    "    deep-copies the rest. Held as a note for the same reason as Layer 1.",
                    "",
                    "### The thirteen workflows",
                    "",
                    *[
                        f"#### W{i} — {name}"
                        + "\n\n<!-- purpose -> inputs -> stages -> outputs -> what the user gets -->\n"
                        for i, name in enumerate(
                            [
                                "Scanned / OCR document pipeline",
                                "Born-digital pipeline",
                                "Digital → OCR re-origination hand-off",
                                "Containerised service / API",
                                "Agent-Skill workflow",
                                "E2E smoke / integration contract",
                                "Vocabulary harvesting & review",
                                "Training / evaluation (page-classification)",
                                "Parameter optimisation / rule coverage (alto)",
                                "Document-understanding benchmark (llm-enrich)",
                                "Format adaptation via flexiconv",
                                "Annotation round trip",
                                "RO-Crate export / FAIR publication",
                            ],
                            start=1,
                        )
                    ],
                    "### Two gaps this page must state, not paper over",
                    "",
                    "<!-- 1. There is no cross-service orchestration: atrium-project/compose/",
                    "        docker-compose.pipeline.yml does not exist. Reproduce the E2E's",
                    "        invocations as the de-facto recipe.",
                    "     2. fixtures/e2e/README.md is truncated mid-sentence at the",
                    "        'Why the DOC_LINE_CATEG bridge exists' section. -->",
                ],
                extra_fm={"authored": "true"},
            ),
        )
    )

    cats = [
        (
            "Metadata standards & serialisations",
            "SKOS · RO-Crate 1.1 + Process Run Crate · JSON-LD · schema.org · Turtle/RDF · "
            "Dublin Core · JSON Schema · SPDX & Creative Commons · ORCID · CITATION.cff · w3id.org",
        ),
        ("Domain vocabularies", "AMCR heslář · TEATER · CNEC 2.0 · Getty AAT · OAI-PMH"),
        (
            "Data & OCR formats",
            "ALTO XML v1–v4 · PAGE XML · hOCR · METS · TEI P5 · TEITOK · CoNLL-U / UD · IOB2 · "
            "the `source.origin` originator set",
        ),
        (
            "Hosting, repository & registration",
            "LINDAT/CLARIAH-CZ · Handle System / PID · Zenodo & DOI · SSH Open Marketplace · "
            "DOG & CLARIN Switchboard · Hugging Face Hub · GHCR · OpenRouter · Label Studio / Doccano",
        ),
        (
            "Models",
            "`ufal/vit-historical-page` · `facebook/fasttext-language-identification` · "
            "`Qwen/Qwen2.5-0.5B` · `hantian/layoutreader` · `THUDM/glm-4v-9b` · the LLM registry · "
            "CUBBITT · UDPipe 2 · NameTag 3 · Korektor · KER / YAKE / KeyBERT",
        ),
        (
            "Runtime & infrastructure",
            "Docker & Compose · Kubernetes · GitHub Actions · vLLM · Ollama · FastAPI · flexiconv · "
            "alto-tools · ruff / pre-commit / Dependabot · Trivy / CodeQL / Codecov",
        ),
        (
            "The ATRIUM project itself",
            "the four bridged infrastructures (DARIAH · ARIADNE · CLARIN · OPERAS) · UFAL · "
            "ARÚP / ARÚB / AISCR · the work packages · the DMP",
        ),
    ]
    gaps = [
        ("Handle System / PID", "`hdl.handle.net/20.500.12800/1-6184` is the project's primary dataset citation"),
        ("LINDAT/CLARIAH-CZ as an institution", "four live API services plus the dataset repository depend on it"),
        ("OAI-PMH", "the AMCR harvest protocol, never named as a protocol"),
        ("Dublin Core", '`dcterms:` is emitted; the string "Dublin Core" appears in **zero** files'),
        (
            "Korektor",
            "a live LINDAT call in `tools/quality_model/correct.py:55`, absent from every Acknowledgements section",
        ),
        ("ARÚP / ARÚB / AISCR", "**the acronyms are never expanded anywhere in the ecosystem**"),
        ("Work packages & the DMP", "cited as the authority for RO-Crate, SKOS and DOG; no WP table exists"),
        ("Trivy / CodeQL / SARIF / Codecov", "gate every release; named only as action refs"),
        ("DOG / CLARIN Switchboard", "DMP-mandated, zero code, planned under #56"),
    ]
    out.append(
        (
            SITE / "external-tools.md",
            page(
                "External tools & services",
                3,
                "Meet every external standard, service, model and piece of infrastructure ATRIUM "
                "depends on, in two sentences each, with a pointer to where it is used. Written for "
                "a reader who has never seen SKOS, RO-Crate or LINDAT.",
                [
                    ("—", "~60 entries in 7 categories", "—", "**AUTHORED**, but ~60 % lifts existing prose"),
                    (f"{HUB}/docs/skos_strategy.md", "§1 §3 §5", "—", "lift — written for exactly this reader"),
                    (
                        f"{HUB}/docs/rocrate_export.md",
                        '§2 "RO-Crate from zero"',
                        "—",
                        "lift — an explicit from-scratch tutorial",
                    ),
                    ("atrium-translator/docs/translation-backends.md", "comparison table", "—", "lift"),
                    (f"{HUB}/docs/k8s_deployment.md", "probe table", "—", "lift"),
                ],
                [
                    "<!-- Each entry: what it is (2 sentences) | where ATRIUM uses it (file paths) | link onward -->",
                    "",
                    *[f"### {name}\n\n<!-- {items} -->\n" for name, items in cats],
                    "### Named in the DMP, deliberately not implemented",
                    "",
                    "<!-- CIDOC-CRM, PROV-O, PeriodO, DataCite, IIIF — rocrate_export.md §3 is the",
                    "     definitive statement and deserves surfacing rather than burying. -->",
                    "",
                    "### Entries with no existing prose anywhere (write fresh)",
                    "",
                    "| Gap | Why it matters |",
                    "|---|---|",
                    *[f"| {n} | {w} |" for n, w in gaps],
                ],
                extra_fm={"authored": "true"},
            ),
        )
    )

    simple = [
        (
            SITE / "ecosystem/architecture.md",
            "Architecture",
            4,
            "See how the six repositories fit together as one system: what is shared, what is "
            "federated, and where the boundaries are.",
            [
                (
                    f"{HUB}/agent_dev_logs/digests/project_state_2706.md",
                    "§2",
                    "—",
                    "**INTERNAL — rewritten from, never published raw**",
                ),
                (
                    f"{HUB}/agent_dev_logs/digests/project_state_1307.md",
                    '§2 "The Meaning-Making Pipeline"',
                    "—",
                    "**INTERNAL — rewritten from**",
                ),
                (f"{HUB}/docs/templates/shared/MANIFEST.json", "the 17 canonical files", "—", "reference"),
            ],
            [
                "### The hub-and-spokes shape",
                "",
                "### What is canonical and what is vendored",
                "",
                "### The CI federation",
                "",
                "### Where the boundaries are",
            ],
        ),
        (
            SITE / "ecosystem/repository-map.md",
            "Repository map",
            5,
            "Find the right repository in one look: what each of the six owns, which document "
            "blocks it writes, and what it hands on.",
            [],
            [
                "### The six at a glance",
                "",
                "<!-- AUTHORED: table — repo | role | owns (document blocks) | default branch | docs -->",
                "",
                "### Who writes which block of the document record",
                "",
                "<!-- from atrium_document.py BLOCK_OWNERS (:108-118) and ORIGIN_ORIGINATORS (:138-145) -->",
            ],
        ),
        (
            SITE / "ecosystem/document-contract.md",
            "The document contract",
            6,
            "Understand the `atrium_document` record that travels through the pipeline: what it "
            "holds, who may write which block, and how provenance accretes.",
            [
                (f"{HUB}/docs/document_schema.md", "all `## ` sections (45,746 B)", "2", "split at depth 2"),
                (f"{HUB}/docs/paradata_schema.md", "whole file (1,560 B)", "—", "render whole — it is 19 lines"),
                (f"{HUB}/fixtures/atrium_document.example.json", "—", "—", "render as a worked example"),
            ],
            [
                "### The object",
                "",
                "### One owner per block",
                "",
                "### The six accretion rules",
                "",
                "### How paradata accumulates",
                "",
                "### Reference discipline",
            ],
        ),
        (
            SITE / "contracts/rocrate.md",
            "RO-Crate export",
            7,
            "Learn what ATRIUM publishes as an RO-Crate, how the accretion record maps into it, "
            "and what a crate cannot yet say.",
            [(f"{HUB}/docs/rocrate_export.md", "all `## ` sections (28,413 B, 11 h2)", "2", "split at depth 2")],
            [
                "### RO-Crate from zero",
                "",
                "### The mapping",
                "",
                "### Distribution",
                "",
                "### What a crate cannot yet say",
            ],
        ),
        (
            SITE / "contracts/skos.md",
            "SKOS & the ATRIUM vocabulary",
            8,
            "Learn how ATRIUM mints concept URIs, what the vocabulary contains, and why "
            "`broader` means two different things.",
            [(f"{HUB}/docs/skos_strategy.md", "all `## ` sections (34,047 B, 9 h2)", "2", "split at depth 2")],
            [
                "### Why this document exists",
                "",
                "### The URI policy",
                "",
                "### The vocabulary sources",
                "",
                "### Known defects",
            ],
        ),
        (
            SITE / "contracts/schemas.md",
            "Schemas",
            9,
            "Read the two JSON Schemas directly, with the fields annotated.",
            [
                (f"{HUB}/docs/templates/shared/atrium_document.schema.json", "—", "—", "render as annotated reference"),
                (f"{HUB}/docs/templates/shared/atrium_vocab.schema.json", "—", "—", "render as annotated reference"),
            ],
            ["### `atrium_document.schema.json`", "", "### `atrium_vocab.schema.json`", "", "### Version policy"],
        ),
        (
            SITE / "agent-skills.md",
            "Agent skills",
            10,
            "Install and use the five ATRIUM Agent Skills, and understand the contract they all implement.",
            [
                (f"{HUB}/docs/skills_catalog.md", "all 6 `## ` sections", "2", "split at depth 2"),
                (
                    f"{HUB}/docs/agent_skill_strategy.md",
                    "18 real `## ` sections",
                    "2",
                    "⚠️ **fence-aware split required** — a naive `^## ` regex finds 23 and shatters `## Appendix A`",
                ),
                (
                    f"{HUB}/docs/skill_acceptance_runbook.md",
                    "all `## `",
                    "2",
                    'render, minus the "Results log (fill in)" table',
                ),
            ],
            [
                "### The five skills",
                "",
                "### The server–client pattern",
                "",
                "### The service contract",
                "",
                "### Installing",
                "",
                "### Authoring a skill",
            ],
        ),
        (
            SITE / "operations.md",
            "Operations",
            11,
            "Build, ship and run the ATRIUM services: images, CI, Kubernetes, and the acceptance "
            "checks that say it worked.",
            [
                (f"{HUB}/docs/docker_gha.md", "7 `## ` sections (31,838 B)", "2", "split at depth 2"),
                (f"{HUB}/docs/k8s_deployment.md", "7 `## ` sections (31,806 B)", "2", "split at depth 2"),
                (
                    f"{HUB}/docs/k8s_acceptance_runbook.md",
                    "4 `## ` sections",
                    "2",
                    'render, minus the "Results log (fill in)" table',
                ),
                (f"{HUB}/docs/docker_gha_roadmap.md", "—", "—", "**EXCLUDED** — internal roadmap (97,253 B)"),
            ],
            [
                "### Images and the registry",
                "",
                "### The CI federation",
                "",
                "### Kubernetes deployment",
                "",
                "### Acceptance runbooks",
            ],
        ),
        (
            SITE / "contributing-standards.md",
            "Contributing standards",
            12,
            "Read the family contribution standard once — the branch model, the commit "
            "convention, the PR format — and see where each repository deviates.",
            [
                (
                    f"{HUB}/docs/templates/CONTRIBUTING.md",
                    "the 9,288 B skeleton",
                    "2",
                    "render as the family standard — **and say plainly that the five copies are unenforced**",
                ),
                (
                    "<5 tool repos>/CONTRIBUTING.md",
                    "`## 🔁 Contributor Workflow` (413 B, byte-identical ×4)",
                    "2",
                    "**render once**, link from 4",
                ),
                (
                    "<5 tool repos>/CONTRIBUTING.md",
                    "`## 📋 Pull Request Format` (688 B, byte-identical ×4)",
                    "2",
                    "**render once**, link from 4",
                ),
                (
                    "<5 tool repos>/CONTRIBUTING.md",
                    "`## ✏️ Commit Messages` (the 659 B type table is identical in all six)",
                    "2",
                    "**render once**, link from 5",
                ),
                (
                    "<5 tool repos>/CONTRIBUTING.md",
                    "`## 🌿 Branches & Environments` (970–998 B, similarity 0.75–0.91)",
                    "2",
                    "render once + a 3-row per-repo delta table",
                ),
                (
                    "atrium-llm-enrich/CONTRIBUTING.md",
                    '`## 🔗 Shared ("drop-in") code` (720 B)',
                    "2",
                    "**render once** — the only repo that documents the shared-code mechanism at all",
                ),
            ],
            [
                "### The family standard",
                "",
                "### Branches & environments",
                "",
                "<!-- ASSEMBLER: render once; per-repo delta is 3 example branch names + master/main -->",
                "",
                "### Contributor workflow",
                "",
                "### Pull request format",
                "",
                "### Commit messages",
                "",
                '### Shared ("drop-in") code',
                "",
                "### Where each repository deviates",
                "",
                "<!-- The five CONTRIBUTING copies are NOT vendored: docs/templates/CONTRIBUTING.md is a",
                "     9,288 B skeleton with «placeholders», absent from MANIFEST.json, revendor_shared.sh",
                "     and para-drift. Pairwise similarity of the five copies never exceeds 0.57. -->",
            ],
        ),
        (
            SITE / "development-history.md",
            "Development history",
            13,
            "Follow how the ecosystem got here, across all six repositories, in one chronology.",
            [
                (
                    f"{HUB}/agent_dev_logs/DEVLOG.md",
                    "the whole timeline (73,638 B)",
                    "2",
                    "**derived** — generated from the DEVLOG, never hand-written",
                ),
                (
                    f"{HUB}/agent_dev_logs/digests/",
                    "49 digests · 49 plans · 45 issue exports · 6 snapshots",
                    "—",
                    "**not published** — linked to GitHub only",
                ),
            ],
            [
                "### Timeline",
                "",
                "<!-- ASSEMBLER: derived from DEVLOG.md. Hand-written summaries go stale — that is",
                "     exactly what happened to page-classification's DEVLOG header. A derived page",
                "     cannot drift from its source. -->",
                "",
                "### Per-repository histories",
                "",
                "<!-- links to docs_site/tools/<repo>/history.md × 5 -->",
            ],
        ),
    ]
    for path, title, nav, purpose, rows, outline in simple:
        out.append((path, page(title, nav, purpose, rows, outline)))
    return out


# ---------------------------------------------------------- tool section pages


def tool_pages() -> list[tuple[pathlib.Path, str]]:
    out = []
    for repo in REPOS:
        slug, short = repo["slug"], repo["short"]
        readme = TREE / slug / "README.md"
        hs = headings(readme, 2)
        phantom = phantom_count(readme, 2)
        buckets: dict[str, list[tuple[str, int]]] = {"index": [], "guide": [], "reference": [], "drop": []}
        for text, size in hs:
            buckets[route(text)].append((text, size))
        extras = EXTRA_DOCS.get(slug, [])
        base_nav = 20 + repo["stage"] * 10

        for n, role in enumerate(["index", "guide", "reference", "changelog", "history"]):
            title = {
                "index": short,
                "guide": f"{short} — Guide",
                "reference": f"{short} — Reference",
                "changelog": f"{short} — Changelog",
                "history": f"{short} — History",
            }[role]
            purpose = ROLE_PURPOSE[role].format(short=short)
            rows: list[tuple[str, str, str, str]] = []
            outline: list[str] = []

            if role in ("index", "guide", "reference"):
                for text, size in buckets[role]:
                    rows.append((f"{slug}/README.md", f"`## {text}`", "3", f"split at depth 3 ({size:,} B)"))
                    outline.append(marker(f"{slug}/README.md", f"## {text}", "3"))
                    outline.append(f"### {text}")
                    outline.append("")
                if role == "reference":
                    for name, srcs in EXTRA_SECTIONS.get(slug, []):
                        outline.append(f"### {name}")
                        outline.append("")
                        for s in srcs:
                            outline.append(marker(f"{slug}/{s}", "*", "3"))
                        outline.append("")
                    for path, treatment, note in extras:
                        if treatment.startswith("exclude:"):
                            rows.append((f"{slug}/{path}", "—", "—", f"**EXCLUDED** — {treatment.split(':', 1)[1]}"))
                        elif treatment.startswith("transclude:"):
                            owner = treatment.split(":", 1)[1]
                            rows.append(
                                (f"{slug}/{path}", "whole file", "—", f"**transclude** from `{owner}` — {note}")
                            )
                        else:
                            rows.append((f"{slug}/{path}", "whole file", "3", f"render — {note}"))
                if role == "index":
                    outline = [
                        marker(f"{slug}/README.md", "preamble (before the first `##`)", "—"),
                        "### What it does",
                        "",
                        "### Inputs and outputs",
                        "",
                        "### Where it sits in the pipeline",
                        "",
                        "<!-- ASSEMBLER: pipeline strip, current repo highlighted -->",
                        "",
                    ] + outline
                    if buckets["drop"]:
                        rows.append(
                            (
                                f"{slug}/README.md",
                                " / ".join(f"`## {t}`" for t, _ in buckets["drop"]),
                                "—",
                                "**suppressed** — hand-written TOC; MkDocs generates nav + per-page TOC",
                            )
                        )

            elif role == "changelog":
                cpath = TREE / slug / "CONTRIBUTING.md"
                csize = cpath.stat().st_size if cpath.exists() else 0
                rows.append(
                    (
                        f"{slug}/CONTRIBUTING.md",
                        "`## 📦 Release History`",
                        "3",
                        f"**transposed** — one anchored `###` per version, newest first "
                        f"(section is {csize:,} B file total)",
                    )
                )
                outline = [
                    marker(
                        f"{slug}/CONTRIBUTING.md",
                        "## 📦 Release History",
                        "3",
                        "transpose: 3-col table -> one ### per version",
                    ),
                    "### Releases",
                    "",
                    "<!-- Two parsing hazards the transposer must survive:",
                    "       * page-classification's rows contain `|` inside code spans, so a naive",
                    "         split('|') reads a 3-column row as 5;",
                    "       * translator's section carries 17 non-table lines (block-quote",
                    "         expansions between rows) that a table-only transposer would drop.",
                    "     Assert row counts before and after. -->",
                ]

            else:  # history
                dpath = TREE / slug / "agent_dev_logs" / "DEVLOG.md"
                dsize = dpath.stat().st_size if dpath.exists() else 0
                ndig = (
                    len(list((TREE / slug / "agent_dev_logs" / "digests").glob("*.digest.md")))
                    if (TREE / slug / "agent_dev_logs" / "digests").exists()
                    else 0
                )
                nplan = (
                    len(list((TREE / slug / "agent_dev_logs" / "plans").glob("*.plan.md")))
                    if (TREE / slug / "agent_dev_logs" / "plans").exists()
                    else 0
                )
                rows.append(
                    (
                        f"{slug}/agent_dev_logs/DEVLOG.md",
                        "the whole timeline",
                        "2",
                        f"**derived**, never hand-written ({dsize:,} B)",
                    )
                )
                rows.append(
                    (
                        f"{slug}/agent_dev_logs/",
                        f"{ndig} digests · {nplan} plans",
                        "—",
                        "**not published** — linked to GitHub only",
                    )
                )
                outline = [
                    marker(f"{slug}/agent_dev_logs/DEVLOG.md", "*", "2", "derive timeline"),
                    "### Timeline",
                    "",
                    "### The record",
                    "",
                    f"<!-- {ndig} digests and {nplan} plans stay in-repo; link, do not publish. -->",
                ]

            tail = ""
            if role == "guide" and phantom:
                tail = (
                    f'!!! danger "Fence hazard"\n'
                    f"    `{slug}/README.md` has **{phantom} heading-looking line(s) inside fenced\n"
                    f"    code blocks** at this depth. The splitter must track fence state — a bare\n"
                    f"    `^## ` regex would emit phantom pages here. See `57.plan.md` §B.2.\n"
                )

            out.append(
                (
                    SITE / "tools" / short / f"{role}.md",
                    page(title, base_nav + n, purpose, rows, outline, extra_fm={"repo": slug, "role": role}, tail=tail),
                )
            )
    return out


ACCOUNTED_BY_ROLE = {"README.md", "CONTRIBUTING.md"}


def assert_every_publishable_doc_is_accounted_for() -> None:
    """Every publishable .md in a tool repo is either routed or explicitly excluded.

    Bidirectional, like tests/test_shared_manifest.py: a file on disk with no spec
    row is as much a defect as a spec row naming a file that is gone. Without this,
    a doc added upstream silently never reaches the site -- which is exactly what
    happened on 2026-09-18 with alto-postprocess/docs/issue30_gold_ab_findings.md.
    """
    problems = []
    for repo in REPOS:
        slug = repo["slug"]
        root = TREE / slug
        on_disk = {
            p.relative_to(root).as_posix()
            for p in root.rglob("*.md")
            if ".git" not in p.parts and "agent_dev_logs" not in p.parts
        }
        spec = {path for path, _t, _n in EXTRA_DOCS.get(slug, [])}
        unaccounted = on_disk - spec - ACCOUNTED_BY_ROLE
        ghost = {s for s in spec if not (root / s).exists()}
        for f in sorted(unaccounted):
            problems.append(f"{slug}/{f}: publishable but in no EXTRA_DOCS row")
        for f in sorted(ghost):
            problems.append(f"{slug}/{f}: EXTRA_DOCS row names a file that does not exist")
    if problems:
        raise SystemExit("docs spec is out of step with the tree:\n  " + "\n  ".join(problems))
    print("  spec <-> tree: every publishable .md in all five tool repos is accounted for")


def main() -> int:
    assert_every_publishable_doc_is_accounted_for()
    pages = hub_pages() + tool_pages()
    for path, text in pages:
        write(path, text)
    print(f"  docs_site/: {len(pages)} page drafts")
    return len(pages)


if __name__ == "__main__":
    n = main()
    print(f"done: {n}")
