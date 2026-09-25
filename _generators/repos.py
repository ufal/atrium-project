"""Shared repo facts for the #57 landing-card generator.

Every value here was read out of the repository tree, not invented: titles from each
README's `#` line, taglines from the GitHub repo description, chips from each README's
own badge block, default branches from the repo metadata (first read 2026-09-18). The
Python chip follows the version the images and CI use; a README badge that lags it is a
finding for that repository, not a reason to publish the old value.

`docs_path` is where the card's "Documentation" button lands, relative to HUB_SITE: the
tool's section when the hub has one, its workflow page until then. It is the one value
to change when a tool section is written.
"""

HUB = "atrium-project"
HUB_SITE = "https://ufal.github.io/atrium-project"
ORG = "https://github.com/ufal"

# Pipeline order is the accretion order the document record travels in,
# NOT a file-handoff chain -- see 57.plan.md D.2.
REPOS = [
    {
        "slug": "atrium-page-classification",
        "short": "page-classification",
        "docs_path": "tools/page-classification/",
        "stage": 1,
        "default_branch": "vit",
        "title": "Image classification using fine-tuned ViT, RegNetY or EffNetV2",
        "subtitle": "for historical document routing",
        "tagline": "Classification of historical page images using ViT and CNN — decides which "
        "downstream pipeline each page is worth sending to.",
        "role": "Structural perception. Eleven page categories that route the rest of the pipeline.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("🤗 HF", "vit-historical-page", "https://huggingface.co/ufal/vit-historical-page", "hf"),
            ("dataset", "LINDAT", "http://hdl.handle.net/20.500.12800/1-6184", "data"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-alto-postprocess",
        "short": "alto-postprocess",
        "docs_path": "workflows/alto-postprocess/",
        "stage": 2,
        "default_branch": "master",
        "title": "ALTO XML Files Postprocessing Pipeline",
        "subtitle": "split · stats · extract · classify · aggregate",
        "tagline": "Post-processing of OCR output — ALTO XML, and also PAGE XML, hOCR, PDF, office and "
        "text files — into extracted text and a scored line-quality table, plus per-page ALTO.",
        "role": "Deserialisation of ALTO and every other OCR or text-bearing input, and OCR quality "
        "control. The fan-out point of the whole pipeline.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("🤗 HF", "fasttext-langID", "https://huggingface.co/facebook/fasttext-language-identification", "hf"),
            ("🤗 HF", "Qwen2.5-0.5B", "https://huggingface.co/Qwen/Qwen2.5-0.5B", "hf"),
            ("vendored", "alto-tools", "https://github.com/cneud/alto-tools", "dep"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-translator",
        "short": "translator",
        "docs_path": "tools/translator/",
        "stage": 3,
        "default_branch": "master",
        "title": "ATRIUM — LINDAT Translation Wrapper",
        "subtitle": "in-place translation of ALTO / AMCR XML",
        "tagline": "In-place translation of XML (ALTO/AMCR) files into English, preserving every "
        "tag, namespace and coordinate.",
        "role": "Protected translation. A terminal branch — its output is recorded, not consumed.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("API", "LINDAT Translation", "https://lindat.mff.cuni.cz/services/translation/", "api"),
            ("API", "UDPipe 2", "https://lindat.mff.cuni.cz/services/udpipe/", "api"),
            ("🤗 HF", "fasttext-langID", "https://huggingface.co/facebook/fasttext-language-identification", "hf"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-nlp-enrich",
        "short": "nlp-enrich",
        "docs_path": "workflows/nlp-enrich/",
        "stage": 4,
        "default_branch": "master",
        "title": "ALTO XML Postprocessing — NLP Enrichment of text",
        "subtitle": "UDPipe · NameTag · TEITOK",
        "tagline": "NLP enrichment of text lines from ALTO XML — morphology, named entities and "
        "TEITOK XML with bounding boxes preserved.",
        "role": "Morphosyntax and named entities. Produces the TEITOK corpus format.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("API", "UDPipe 2", "https://lindat.mff.cuni.cz/services/udpipe/api-reference.php", "api"),
            ("API", "NameTag 3", "https://lindat.mff.cuni.cz/services/nametag/api-reference.php", "api"),
            ("keywords", "YAKE · KeyBERT", "https://github.com/LIAAD/yake", "dep"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-llm-enrich",
        "short": "llm-enrich",
        "docs_path": "workflows/llm-enrich/",
        "stage": 5,
        "default_branch": "main",
        "title": "ATRIUM LLM Enricher",
        "subtitle": "local (multi-GPU) & remote semantic enrichment",
        "tagline": "Application of LLMs for digitized document enrichment — keywords and "
        "vocabulary mapping, local or remote.",
        "role": "Semantic enrichment against the ATRIUM controlled vocabulary.",
        "chips": [
            ("python", "3.11+", "https://www.python.org/downloads/", "py"),
            ("backend", "transformers | vLLM", "https://github.com/vllm-project/vllm", "dep"),
            ("remote", "OpenRouter", "https://openrouter.ai/", "api"),
            ("local-light", "Ollama", "https://ollama.com/", "api"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
]

BY_SHORT = {r["short"]: r for r in REPOS}
