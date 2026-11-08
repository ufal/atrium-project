# ATRIUM keyword extraction: Galaxy tool

`keyword_extract.xml` runs the batch image of
[ufal/atrium-keyword-extract](https://github.com/ufal/atrium-keyword-extract) at release `1.6.5-beta`
(`ghcr.io/ufal/atrium-keyword-extract:1.6.5-beta`, the `base` build target). It extracts the keywords of all the
documents given to it in one job, with one of the three statistical methods. The controlled-vocabulary kind (the
`llm` image, a language-model key per user, research output) is not offered.

`1.6.5-beta` is the first release whose entry point runs Galaxy's job script, through the hub-canonical
`container_entrypoint.py`; the job calls `python3 /app/keywords.py` by its absolute path.

## Inputs, parameters, outputs

| Inputs     | documents, many per job: CoNLL-U (`tabular`), TEITOK (`tei` or `xml`), ATRIUM records (`json`), line tables (`csv` with a `text` column), `txt`; optionally the records to add the keywords to (`json`)               |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters | the method (YAKE, the default; KeyBERT, with the model downloaded or staged, MMR and diversity; lemma frequency); keywords per document; the longest keyword in words; the language (YAKE's stop words); per page too |
| Outputs    | the keyword table (`csv`, `document_id,kw-1,score-1,…`); keywords per document and per page (lists of `csv`); the records with the `keywords` block (a list of `json`); paradata (`json`)                             |

- **Names.** Each document is linked as `input/<element identifier><suffix>`, the suffix saying its kind: `.conllu`
  for `tabular`, `.teitok.xml` for `tei`, `.document.json` for `json`. Its document id, the table's first column and
  the element names of the output lists, is that name. Records to add to are matched by the same name.
- **Failures.** The tool reports a document it cannot read on stderr and goes on, and exits 0 even when none could be
  read. The job script therefore fails (exit 1) when the tool's last line says no document was processed.
- **CRLF.** The per-document and per-page tables end their lines with CRLF; the tests use `has_text`.
- `--workers` is Galaxy's `GALAXY_SLOTS`. KeyBERT loads its model in each worker.

## The KeyBERT model

| Choice             | What the job does                                                                                                              | Cost                    |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------|-------------------------|
| Download (default) | `--keybert-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, into `HF_HOME` in the job's temporary directory | about 0.5 GB, every job |
| Staged             | `--keybert-model <path from the atrium_hf_models table>`, offline (`HF_HUB_OFFLINE=1`)                                         | none per job            |

**Admin steps for *Staged*:** install the data manager `galaxy/data_managers/data_manager_atrium_hf_models/` and run
*ATRIUM Hugging Face models* once with *paraphrase-multilingual-MiniLM-L12-v2*; mount the data manager's data path
into the tool's container, read-only, as for the page classifier's models.

## Network

YAKE and lemma frequency need none. KeyBERT downloads its model from the Hugging Face Hub unless it is staged.

## Tests

```bash
planemo lint keyword_extract.xml
planemo test --docker --galaxy_branch v26.1.1 keyword_extract.xml
```

Three tests: lemma frequency on a CoNLL-U file (the exact table `CTX000000003,náčrt,1.0,sonda,1.0,,`, a record); YAKE
on a TEITOK file and a record written by the born-digital converter's wrapper, per page too; a table without a `text`
column (exit 1). None needs the network.

`test-data/` holds two of the ATRIUM tools' synthetic documents (`CTX000000003.conllu` from this tool's
`data_samples/`, `CTX000000001.teitok.xml` from nlp-enrich's, CC BY-NC 4.0, as `test-data/LICENSE` says),
`rich.document.json` (the born-digital converter's record of its MIT `rich.docx` fixture) and `no_text_column.csv`.

## Licences

The code is MIT; YAKE is AGPL-3.0; the KeyBERT model is Apache-2.0. The paradata of each run lists the components and
their licences.
