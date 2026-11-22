"""Shared repo facts for the #57 landing-card generator.

Every value here was read out of the repository tree, not invented: titles from each
README's `#` line, taglines from the GitHub repo description, chips from each README's
own badge block, default branches from the repo metadata (first read 2026-09-18;
re-read 2026-10-07 for the repositories of the 1 October split; the digital-convert and
keyword-extract titles 2026-10-22, the nlp-enrich, page-classification and translator titles
2026-10-25, after their READMEs moved to the #79 skeleton; all six titles and roles 2026-11-21, after
the documentation round for the AMČR pilot's route). The
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

# The order of the AMČR pilot's route (the hub's Pipelines page, "The route through the
# pipeline"): digital-convert or the ATR gives the layout, ocr-postprocess builds the record,
# the others add to it; the translator runs apart, when a record is archived.
REPOS = [
    {
        "slug": "atrium-digital-convert",
        "short": "digital-convert",
        "docs_path": "workflows/digital-convert/",
        "stage": 1,
        "default_branch": "main",
        "title": "Born-digital documents into docproc layout",
        "subtitle": "PDF · DOCX · ODT · ODS · XLSX · RTF · DOC · XLS → docproc, a verdict per page",
        "tagline": "Digital-born documents transformed into JSON records, and page content information "
        "for the pages that still need OCR.",
        "role": "The first step. Reads the text layer, gives every page a verdict; a page that needs it sends the document to the ATR.",
        "chips": [
            ("python", "3.11+", "https://www.python.org/downloads/", "py"),
            (
                "layout",
                "docproc",
                "https://github.com/ufal/atrium-digital-convert/blob/test/schemas/docproc/README.md",
                "data",
            ),
            ("SSH OMP", "jGxgQI", "https://marketplace.sshopencloud.eu/tool-or-service/jGxgQI", "sshomp"),
            ("license", "MIT", "https://opensource.org/license/mit/", "lic"),
            ("funded by", "ATRIUM", "https://atrium-research.eu/", "atr"),
        ],
    },
    {
        "slug": "atrium-page-classification",
        "short": "page-classification",
        "docs_path": "workflows/page-classification/",
        "stage": 2,
        "default_branch": "vit",
        "title": "Scanned archive pages sorted into eleven page types",
        "subtitle": "what each page holds, beside the ATR",
        "tagline": "Classification of historical page images using ViT and CNN — decides which "
        "downstream pipeline each page is worth sending to.",
        "role": "Page types. Classifies the pages that go to the ATR; the categories join the record's pages.",
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
        "stage": 3,
        "default_branch": "master",
        "title": "The document record, with every text line sorted into five quality categories",
        "subtitle": "docproc → the record · language · quality",
        "tagline": "Post-processing of OCR output — ALTO XML, and also PAGE XML, hOCR, PDF, office and "
        "text files — into extracted text and a scored line-quality table, plus per-page ALTO.",
        "role": "The record builder. Builds the record from docproc and scores every line; research "
        "batches over ALTO and other OCR output.",
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
        "slug": "atrium-nlp-enrich",
        "short": "nlp-enrich",
        "docs_path": "workflows/nlp-enrich/",
        "stage": 4,
        "default_branch": "master",
        "title": "Lemmas, syntax and named entities of text lines, as TEITOK",
        "subtitle": "UDPipe · NameTag · TEITOK",
        "tagline": "NLP enrichment of text lines from ALTO XML — morphology, named entities and "
        "TEITOK XML with bounding boxes preserved.",
        "role": "Morphosyntax and named entities. Reads the record, adds its linguistic layer, writes TEITOK.",
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
        "slug": "atrium-translator",
        "short": "translator",
        "docs_path": "workflows/translator/",
        "stage": 6,
        "default_branch": "master",
        "title": "XML documents translated in place, AMČR metadata records and ALTO pages",
        "subtitle": "metadata → metadata-en, in place",
        "tagline": "In-place translation of XML (ALTO/AMCR) files into English, preserving every "
        "tag, namespace and coordinate.",
        "role": "A record-level job. Turns an archived record's metadata into English; ALTO for research.",
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
]

BY_SHORT = {r["short"]: r for r in REPOS}
