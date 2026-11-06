# ATRIUM XML translator: Galaxy tool

`translator.xml` runs the batch image of [ufal/atrium-translator](https://github.com/ufal/atrium-translator) at
release `1.7.7-beta` (`ghcr.io/ufal/atrium-translator:1.7.7-beta`). It translates one XML document per job, an
AMČR metadata record or an ALTO page, and writes it back with its structure unchanged. A collection maps over the
tool, one job per document.

`1.7.7-beta` is the first release whose entry point runs Galaxy's job script (`docker run IMAGE /bin/sh
tool_script.sh`), through the hub-canonical `container_entrypoint.py`; earlier images fail with exit 2. (`v1.7.6-beta`
was tagged on the commit before its version bump and never released.) **The tag must be pushed and its images published before this
wrapper can run.**

## Inputs, parameters, outputs

| Inputs     | the document (`xml`); for metadata, an optional XPath list (`txt`) and XML schema (`xml`); an optional vocabulary (`csv`); an optional baseline record (`json`)                       |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Parameters | metadata or ALTO; source language (detected, or named) and the fallback for detection; target language; replace or append; the vocabulary (bundled, own, none); fast alignment (ALTO) |
| Outputs    | the translated document (`xml`); the translation log (`csv`); paradata (`json`); the document record (`json`)                                                                         |

- **Names.** The document is linked as `<element identifier>.xml` or `.alto.xml`; known extensions in the
  identifier (`.xml`, `.alto.xml`, and image extensions from OCR) are dropped. The log and the record are named
  after it.
- **Settings.** Every setting is passed on the command line, with an empty `--config`: the image's `config.txt`
  names paths relative to `/app`, and Galaxy starts the job in its own directory.
- **Backend.** Only `lindat` (LINDAT CUBBITT, no key). The `openai_compatible` backend needs an API key, which would
  come through Galaxy's user credentials; not offered yet.

## Network

Every job calls the LINDAT translation service; with a vocabulary, LINDAT UDPipe too. The fastText
language-identification model is in the image. The tests need the same access.

## Tests

```bash
planemo lint translator.xml
planemo test --docker --galaxy_branch v26.1.1 translator.xml
```

Three tests: an AMČR record, Czech to English, with the bundled fields and vocabulary; an ALTO page, the language
detected, the translation appended (`ALTERNATIVE PURPOSE="translation:en"`); German to Polish, a pair LINDAT has
no model for (exit 1, nothing translated). `test-data/` holds the translator's own test fixtures (MIT).

## Licences

The code is MIT. The fastText model is CC BY-NC 4.0; the paradata of each run lists the components and their
licences.
