"""Shared repo facts for the #57 landing-card generator.

Every value here was read out of the repository tree, not invented: titles from each
README's `#` line, taglines from the GitHub repo description, chips from each README's
own badge block, default branches from the repo metadata (first read 2026-09-18;
re-read 2026-10-07 for the repositories of the 1 October split; the digital-convert and
keyword-extract titles 2026-10-22, the nlp-enrich, page-classification and translator titles
2026-10-25, after their READMEs moved to the #79 skeleton). The
Python chip follows the version the images and CI use; a README badge that lags it is a
finding for that repository, not a reason to publish the old value.

`docs_path` is where the card's "Documentation" button lands, relative to HUB_SITE: the
tool's workflow page, which links the tool's own documentation. Since atrium-project#79
(2026-10-25) a tool's guides and references live in its repository, so the hub keeps no
tool sections. The "SSH OMP" chip links the tool's SSH Open Marketplace record (#4).
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
        "docs_path": "workflows/page-classification/",
        "stage": 1,
        "default_branch": "vit",
        "title": "Scanned archive pages sorted into eleven page types",
        "subtitle": "for historical document routing",
        "tagline": "Classification of historical page images using ViT and CNN — decides which "
        "downstream pipeline each page is worth sending to.",
        "role": "Structural perception. Eleven page categories that route the rest of the pipeline.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("🤗 HF", "vit-historical-page", "https://huggingface.co/ufal/vit-historical-page", "hf"),
            ("dataset", "LINDAT", "http://hdl.handle.net/20.500.12800/1-6184", "data"),
            ("SSH OMP", "RER7Fw", "https://marketplace.sshopencloud.eu/tool-or-service/RER7Fw", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-ocr-postprocess",
        "short": "ocr-postprocess",
        "docs_path": "workflows/ocr-postprocess/",
        "stage": 2,
        "default_branch": "master",
        "title": "OCR Output Postprocessing Pipeline",
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
            ("SSH OMP", "YParYU", "https://marketplace.sshopencloud.eu/tool-or-service/YParYU", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-translator",
        "short": "translator",
        "docs_path": "workflows/translator/",
        "stage": 3,
        "default_branch": "master",
        "title": "XML documents translated in place, ALTO pages and AMČR metadata",
        "subtitle": "in-place translation of ALTO / AMCR XML",
        "tagline": "In-place translation of XML (ALTO/AMCR) files into English, preserving every "
        "tag, namespace and coordinate.",
        "role": "Protected translation. A terminal branch — its output is recorded, not consumed.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("API", "LINDAT Translation", "https://lindat.mff.cuni.cz/services/translation/", "api"),
            ("API", "UDPipe 2", "https://lindat.mff.cuni.cz/services/udpipe/", "api"),
            ("🤗 HF", "fasttext-langID", "https://huggingface.co/facebook/fasttext-language-identification", "hf"),
            ("SSH OMP", "CizIUW", "https://marketplace.sshopencloud.eu/tool-or-service/CizIUW", "sshomp"),
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
        "title": "Lemmas, syntax and named entities of text lines, as TEITOK",
        "subtitle": "UDPipe · NameTag · TEITOK",
        "tagline": "NLP enrichment of text lines from ALTO XML — morphology, named entities and "
        "TEITOK XML with bounding boxes preserved.",
        "role": "Morphosyntax and named entities. Produces the TEITOK corpus format.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("API", "UDPipe 2", "https://lindat.mff.cuni.cz/services/udpipe/api-reference.php", "api"),
            ("API", "NameTag 3", "https://lindat.mff.cuni.cz/services/nametag/api-reference.php", "api"),
            ("SSH OMP", "EMhu3X", "https://marketplace.sshopencloud.eu/tool-or-service/EMhu3X", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-keyword-extract",
        "short": "keyword-extract",
        "docs_path": "workflows/keyword-extract/",
        "stage": 5,
        "default_branch": "master",
        "title": "Keywords of archival documents, statistical and vocabulary-controlled",
        "subtitle": "KeyBERT · YAKE · KER · AMČR and TEATER",
        "tagline": "Extraction of statistical and vocabulary-controlled keywords from text-containing "
        "documents, with the method and score of every keyword.",
        "role": "Keywords of both kinds, kept apart. Reads the record after nlp-enrich.",
        "chips": [
            ("python", "3.11", "https://www.python.org/downloads/", "py"),
            ("keywords", "KeyBERT · YAKE", "https://github.com/MaartenGr/KeyBERT", "dep"),
            ("vocabulary", "AMČR · TEATER (CC0)", "https://teater.aiscr.cz/", "data"),
            ("SSH OMP", "j9fqxo", "https://marketplace.sshopencloud.eu/tool-or-service/j9fqxo", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-digital-convert",
        "short": "digital-convert",
        "docs_path": "workflows/digital-convert/",
        "stage": 6,
        "default_branch": "main",
        "title": "Born-digital documents into ATRIUM document records",
        "subtitle": "PDF · DOCX · ODT · ODS · XLSX · RTF · DOC · XLS → the document record",
        "tagline": "Digital-born documents transformed into JSON records, and page content information "
        "for the pages that still need OCR.",
        "role": "The born-digital route's first stage: reads the text layer, flags the pages that need OCR.",
        "chips": [
            ("python", "3.11+", "https://www.python.org/downloads/", "py"),
            (
                "record",
                "atrium_document 1.0",
                "https://github.com/ufal/atrium-project/blob/main/docs/document_schema.md",
                "data",
            ),
            ("SSH OMP", "jGxgQI", "https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
]

BY_SHORT = {r["short"]: r for r in REPOS}
