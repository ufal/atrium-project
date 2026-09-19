"""Page specifications for the hub site tree (issue #57, round 2 drafts)."""

# Which README h2 goes to which tool-section page. Ordered rules, first match wins.
# Keys are lowercase substrings matched against the heading text.
ROUTE = [
    ("table of contents", "drop"),
    ("setup", "guide"),
    ("how to install", "guide"),
    ("prerequisites", "guide"),
    ("how to run", "guide"),
    ("usage", "guide"),
    ("workflow stages", "guide"),
    ("data preparation", "guide"),
    ("docker", "guide"),
    ("deployment", "guide"),
    ("configuration", "guide"),
    ("vocabulary harvesting", "guide"),
    ("local inference", "guide"),
    ("remote inference", "guide"),
    ("lightweight local", "guide"),
    ("document-level input", "guide"),
    ("visually-rich", "guide"),
    ("extra:", "guide"),
    ("logic overview", "reference"),
    ("paradata", "reference"),
    ("api service", "reference"),
    ("environment variables", "reference"),
    ("model registry", "reference"),
    ("inputs and outputs", "reference"),
    ("for developers", "reference"),
    ("csv logs", "reference"),
    ("benchmark", "reference"),
    ("vendored code", "reference"),
    ("project structure", "reference"),
    ("results", "index"),
    ("model description", "index"),
    ("versions", "index"),
    ("features", "index"),
    ("backends at a glance", "index"),
    ("teitok xml", "index"),
    ("acknowledg", "index"),
    ("license", "index"),
    ("citation", "index"),
    ("contacts", "index"),
    ("appendix", "index"),
]

DEFAULT_ROUTE = "reference"


def route(heading: str) -> str:
    h = heading.lower()
    for needle, target in ROUTE:
        if needle in h:
            return target
    return DEFAULT_ROUTE


# Extra publishable docs per tool repo, and how the site treats them.
# treatment: render | transclude:<owner> | exclude:<reason>
EXTRA_DOCS = {
    "atrium-page-classification": [
        ("service/README.md", "render", "REST service contract"),
    ],
    "atrium-alto-postprocess": [
        ("docs/categorization_logic.md", "render", "the composite quality score, in full"),
        (
            "docs/issue30_gold_ab_findings.md",
            "render",
            "Research section — gold-scored parameter-run findings (issue #30)",
        ),
        ("service/README.md", "render", "REST service contract"),
        ("tools/RULE_COVERAGE.md", "render", "Research section"),
        ("tools/SWEEP_NOTES.md", "render", "Research section"),
        ("tools/gold/GOLD.md", "render", "Research section"),
        ("tools/quality_model/README.md", "render", "Research section"),
        ("data_samples/README.md", "render", "sample corpus notes"),
        ("LICENSES/README.md", "render", "vendored-component licences"),
        ("tools/quality_model/EXPERIMENTS.md", "exclude:unfilled results table", ""),
    ],
    "atrium-translator": [
        ("docs/translation-backends.md", "render", "Backend evaluation section"),
        ("service/README.md", "render", "REST service contract"),
        ("data_samples/README.md", "render", "sample corpus notes"),
    ],
    "atrium-nlp-enrich": [
        ("service/README.md", "render", "REST service contract"),
        ("schemas/teitok/README.md", "render", "TEITOK schema notes"),
        ("annotation/README.md", "render", "Annotation section"),
        ("annotation/GUIDELINES.md", "render", "Annotation section"),
        ("prompts/RUNBOOK.md", "render", "OWNER of this file; llm-enrich transcludes it"),
        ("data_samples/vocab/RUNBOOK.md", "render", "OWNER of this file; llm-enrich transcludes it"),
        ("data_samples/vocab/6.D-eval.decision-package.md", "exclude:open memo addressed to named individuals", ""),
        ("data_samples/vocab/6.O3O4.decision-package.md", "exclude:open memo addressed to named individuals", ""),
    ],
    "atrium-llm-enrich": [
        ("service/README.md", "render", "REST service contract"),
        ("prompts/RUNBOOK.md", "transclude:atrium-nlp-enrich", "byte-identical, 19,948 B — rendered once, linked here"),
        (
            "data_samples/vocab/RUNBOOK.md",
            "transclude:atrium-nlp-enrich",
            "byte-identical, 28,939 B — rendered once, linked here",
        ),
        ("digital_born/README.md", "exclude:self-declared Phase 0 scratch space", ""),
        ("data_samples/vocab/6.D-eval.decision-package.md", "exclude:open memo addressed to named individuals", ""),
        ("data_samples/vocab/6.O3O4.decision-package.md", "exclude:open memo addressed to named individuals", ""),
    ],
}

# Repo-specific additive sections on reference.md (shape stays Home/Guide/Reference/
# Changelog/History -- these are sections, not extra pages).
EXTRA_SECTIONS = {
    "atrium-alto-postprocess": [
        (
            "Research",
            [
                "tools/RULE_COVERAGE.md",
                "tools/SWEEP_NOTES.md",
                "tools/gold/GOLD.md",
                "tools/quality_model/README.md",
                "docs/issue30_gold_ab_findings.md",
            ],
        ),
        ("Categorization logic", ["docs/categorization_logic.md"]),
    ],
    "atrium-translator": [
        ("Backend evaluation", ["docs/translation-backends.md"]),
    ],
    "atrium-nlp-enrich": [
        ("Annotation", ["annotation/README.md", "annotation/GUIDELINES.md"]),
        ("Vocabulary & prompts", ["data_samples/vocab/RUNBOOK.md", "prompts/RUNBOOK.md"]),
        ("TEITOK schema", ["schemas/teitok/README.md"]),
    ],
    "atrium-llm-enrich": [
        ("Benchmark", ["README.md#-document-understanding-benchmark"]),
    ],
    "atrium-page-classification": [],
}

ROLE_PURPOSE = {
    "index": "Land here from the pipeline strip or the repository map and leave knowing "
    "what {short} does, what it takes in, what it hands on, and where to go next.",
    "guide": "Get {short} running — install, configure, invoke — without reading the code.",
    "reference": "Look up a flag, an environment variable, an endpoint or an output field "
    "for {short} and stop reading as soon as you have it.",
    "changelog": "Find what changed in {short} between two versions, and link to a single release.",
    "history": "Understand why {short} is shaped the way it is, in the order it happened.",
}
