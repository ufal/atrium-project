# ATRIUM NLP enrichment: Galaxy tool

`nlp_enrich.xml` runs the batch image of [ufal/atrium-nlp-enrich](https://github.com/ufal/atrium-nlp-enrich) at
release `1.3.4-beta` (`ghcr.io/ufal/atrium-nlp-enrich:1.3.4-beta`). It annotates the text lines of one Czech document
per job with LINDAT UDPipe 2 and NameTag 3 and, with the document's ALTO, writes TEITOK with each word's position. A
collection maps over the tool, one job per document.

`1.3.4-beta` is the first release whose entry point runs Galaxy's job script, through the hub-canonical
`container_entrypoint.py`; the job calls `python3 /app/run_pipeline.py` by its absolute path.

## Inputs, parameters, outputs

| Inputs     | a line table (`csv` with a `text` column; also `txt`, `xlsx`); optionally the same document's ALTO (`xml`) and a baseline record (`json`)                                    |
|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters | leave out the lines that ATRIUM OCR line quality marked Trash, Garbage, Inverted or Empty                                                                                    |
| Outputs    | CoNLL-U with `NER=` per word (`tabular`: DARIAH's Galaxy has no `conllu`); tokens (`csv`); entities per page (`csv`); TEITOK (`tei`); the record (`json`); paradata (`json`) |

- **The line table** of *ATRIUM OCR post-processing* (`file,page_num,line_num,text,page_label`, CRLF) is read as it
  is; so is ocr-postprocess's own `DOC_LINE_CATEG` table.
- **Names.** The table is linked as `in/<element identifier>.csv` (a `.csv` or `.lines.csv` in the identifier
  dropped) and its ALTO as `layout/alto/<same id>.alto.xml`: the pipeline pairs them by that id. Two collections
  mapped together must list the documents in the same order.
- **The config.** The pipeline reads every path from `config_api.txt`, so the job writes a copy of the image's one
  with the same keys moved into the job directory that the image's own service moves per request
  (`service/enrichment.py`, `_derive_config`). The stages run from `/app` and write nothing there.
- **No entities.** A document in which NameTag finds none has no summary table; the *entities per page* dataset is
  then empty.
- `--strict-empty` makes a run that annotated nothing fail (exit 1) instead of succeeding with empty outputs.

## Network

Every job calls LINDAT UDPipe (`https://lindat.mff.cuni.cz/services/udpipe/api/process`) and NameTag
(`https://lindat.mff.cuni.cz/services/nametag/api/recognize`), no key. The runners need outbound HTTPS to
`lindat.mff.cuni.cz`. Exit 6, 7 or 8 says that LINDAT did not answer, timed out or refused the request. The
`UDPIPE_URL` and `NAMETAG_URL` environment variables, if the destination sets them, point the job at another
instance of the services.

## Tests

```bash
planemo lint nlp_enrich.xml
planemo test --docker --galaxy_branch v26.1.1 nlp_enrich.xml
```

Three tests: a line table with its ALTO (the UDPipe model, a lemma, TEITOK with a word's bounding box); the line
table that *ATRIUM OCR post-processing* writes for a two-page CSV, without ALTO; a table without a `text` column
(exit 1, before any call to LINDAT). The entities themselves depend on the model LINDAT serves and are not compared.

`test-data/` holds one of the tool's synthetic documents (`data_samples/`, CC BY-NC 4.0, as `test-data/LICENSE`
says), `CTX000000006.lines.csv` (the ocr-postprocess wrapper's output for its `CTX000000006.csv`, same licence), and
`no_text_column.csv`, written for the error test.

## Licences

The code is MIT; the UDPipe and NameTag models are CC BY-NC-SA. The paradata of each run lists the components and
their licences.
