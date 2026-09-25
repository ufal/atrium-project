# 🔗 ATRIUM SKOS Strategy — vocabularies as an internal alignment framework

_Issue: [ufal/atrium-project#51](https://github.com/ufal/atrium-project/issues/51) · Milestone: Q3 [WP8 / WP7] · Date: 2026-09-08_
_Status: **normative for the vocabulary layer of all six repos.** Supersedes
[`../agent_dev_logs/plans/51.plan.md`](../agent_dev_logs/plans/51.plan.md) §A ("do nothing")._
_Companion documents: [`document_schema.md`](document_schema.md) (the record these terms travel in) ·
[`paradata_schema.md`](paradata_schema.md) (how a run that used them is described)._

Decisions fixed at planning time:

1. **No namespace is requested, from here or anywhere.** Issue #51 asked for a DARIAH Vocabs
   namespace. @motyc's answer removed that from this repo's plate for ~18 months and pointed at
   what is left: *"This does not prevent using SKOS as framework to align the data internally. It
   is definitely desirable."* That sentence is this document's entire mandate.
2. **Source concepts keep the sources' URIs.** AMCR and TEATER already mint resolvable
   identifiers. ATRIUM mints nothing for them — those are precisely the "current IDs" @motyc says
   *"will become PID references to the published SKOS compliant version"*.
3. **ATRIUM mints URIs only for what ATRIUM authors**, rooted in one swappable constant.
4. **Nothing is published.** This is an internal alignment framework. No external service is
   contacted, no vocabulary is republished, no registration is a prerequisite for any of it.

## 🎯 1. Why this document exists

Five tools exchange one JSON record, and several of its fields carry controlled terms **as bare
strings**: `pages[].category`, `page_categories`, `lines[].categ`, `pages[].quality_band`,
`entities[].type_teitok`, `entities[].type_cnec`, `enrichment.items[].teater_category`. Each label
set is declared in a different repository in a different form — a Python list, a set of `return`
statements, a JSON config, a dict literal — and until now nothing reconciled them.

That is not a tidiness complaint. It has produced live defects, catalogued in [§6](#-6-defect-register).
The most instructive: `lines[].categ` has **two** authorised originators emitting **disjoint** label
sets, and its only consumer filters on one of them — so on the OCR path the filter matches nothing
and garbage OCR lines reach the model. Nothing failed. No validator complained. The field is typed
`string` and every value was a valid string.

SKOS is the right frame for this because the problem is not serialisation, it is **meaning**: which
labels exist, which are the same thing, which is broader than which, and which external authority a
term corresponds to. Those are the four questions SKOS is designed to answer, and three of the six
repos already answer some of them — informally, in Python dicts, with no way to check the answers
against each other.

**Non-goals:** publishing anything; requesting a namespace; changing any pipeline's behaviour;
re-describing AMCR's or TEATER's concepts; adding an RDF library to any repo.

## 📐 2. What we already had (verified against the tree, not assumed)

| Asset                                           | Where                             | State                                      |
|-------------------------------------------------|-----------------------------------|--------------------------------------------|
| 1,460 AMCR concepts, 50 heslar lists            | `vocab_sources.harvest_amcr`      | ✅ harvested, with real URIs                |
| 4,134 TEATER concepts, 12 branches, cs/en/de    | `vocab_sources.harvest_teater`    | ✅ harvested, with real URIs                |
| 707 `skos:exactMatch` URIs on 668 AMCR concepts | `vocab_sources.py:203-208`        | ⚠️ captured, **never exported**            |
| A genuine broader/narrower tree (TEATER)        | `VocabRecord.broader`             | ⚠️ captured, never exported                |
| alt labels (2,707) and scope notes (2,330)      | `VocabRecord.alt_*`, `note_*`     | ⚠️ captured, dropped by `nested_keep`      |
| `entities[].pid.{wikidata,geonames,aat,amcr}`   | `atrium_document.schema.json`     | ❌ declared, **written by nothing**         |
| 11 page categories                              | `model_registry.py:5-17`          | ⚠️ bare strings, definitions in prose only |
| 5 + 2 line categories                           | two repos, disjoint               | ✅ registered; defect V-1 fixed 2026-09-25  |
| A second, divergent harvester                   | `atrium-translator/load_vocab.py` | ⚠️ discards every id it receives           |

`VocabRecord` (`vocab_sources.py:85-121`) is already a `skos:Concept` in all but name — `cs`/`en`/`de`
→ `prefLabel`, `alt_*` → `altLabel`, `note_*` → `scopeNote`, `source_id` → `notation`, `uri` → the
subject, `exact_match` → `exactMatch`. **The modelling work was already done.** What was missing was
a serialisation, a policy for the URIs ATRIUM has to mint itself, and one place to declare the label
sets that never came from a thesaurus at all.

The 707 Getty URIs are the sharpest illustration. They are harvested on every run, written into
`amcr_flat.json`, and read by exactly one consumer: a heuristic column in a reviewer spreadsheet.
The issue's own phrasing — *"already captures the AMCR `odkaz skos:exactMatch` URIs — nothing
exports them"* — was exactly right, and it needed no namespace to fix.

## 🧭 3. The URI policy (normative)

### 3.1 Four layers, three of which mint nothing

| Layer                  | Concepts                                 | URI                                                                               |
|------------------------|------------------------------------------|-----------------------------------------------------------------------------------|
| **L1 Source**          | 1,460 AMCR + 4,134 TEATER                | The sources' own: `https://api.aiscr.cz/id/HES-…`, `https://teater.aiscr.cz/id/…` |
| **L2 ATRIUM-authored** | 64 concepts in 6 schemes                 | Minted under `SKOS_BASE`                                                          |
| **L3 Mappings**        | 75 in the registry + 707 harvested       | Assertions **between** L1/L2/external. Mint nothing.                              |
| **L4 Propagation**     | `entities[].pid`, and the `*_uri` fields | Reference L1/L2. Mint nothing.                                                    |

### 3.2 The one swappable constant

```python
SKOS_BASE = "https://w3id.org/atrium/"  # atrium_vocab.py
```

Every ATRIUM-authored URI is derived from it by `concept_uri()` / `scheme_uri()` /
`collection_uri()`. **Nothing anywhere hard-codes a URI string.** When the SKOSification project
lands real PIDs there are two exits, and neither is a migration:

* repoint the `w3id.org/atrium` redirect — **zero** data changes; or
* change this one string and regenerate — one line, one `--skos` run.

`w3id.org` was chosen over the alternatives deliberately. The project domain
(`atrium-research.eu`) outlives neither the grant (ends December 2027) nor a site redesign; an
institutional domain would encode one partner as owner of a jointly-authored vocabulary; a
non-resolving `urn:` would make the eventual move a rewrite of stored values instead of a redirect.

**Registering the w3id redirect is optional and blocks nothing.** These URIs are identifiers first
and locations second; they identify correctly before any redirect exists. Registration is a
one-file pull request against the `w3id.org` repository whenever someone wants dereferencing, and
it is *not* a namespace request in the sense @motyc ruled out — it reserves a redirect, not a
vocabulary, and commits ARUP/ARUB to nothing.

### 3.3 What ATRIUM may and may not name

> **Rule.** ATRIUM mints a URI for a concept **only if ATRIUM authored the concept.** For anything
> harvested, the source's identifier is the identifier. Where a source has a scheme but no URI for
> it, ATRIUM may name **its own harvest** (`atrium:scheme/amcr-harvest`) — an artifact ATRIUM
> really does own — but never the concepts inside it.

This is what keeps @motyc's constraint satisfied by construction. There is no ATRIUM identifier for
an AMCR term to migrate off, because one was never created.

## 🏗️ 4. The registry — `atrium_vocab.py`

Hub-canonical, in `docs/templates/shared/`, vendored to all five tool repos and byte-enforced by
`para-drift.reusable.yml`. **Standard library only.** Contents:

| Scheme          | Concepts                  | Declared by                                                                |
|-----------------|---------------------------|----------------------------------------------------------------------------|
| `page-category` | 11 (+5 facet collections) | `atrium-page-classification/model_registry.py`                             |
| `line-category` | 7 (5 + 2, by originator)  | `alto-postprocess/text_util.py` + `llm-enrich/api_util/digital_to_json.py` |
| `quality-band`  | 3                         | `alto-postprocess/document_hook.py`                                        |
| `entity-type`   | 4                         | `nlp-enrich/api_util/teitok_alto.py`                                       |
| `cnec`          | 28                        | the subset `_CNEC_TO_CONLL` maps                                           |
| `theme`         | 11                        | `nlp-enrich/data_samples/taxonomy_config.json`                             |

Plus 75 mapping assertions: 28 CNEC→coarse type, 19 TEATER branch→theme, 27 heslář→theme, and one
`closeMatch` (see V-1). Renders to Turtle and JSON-LD; both are produced from **one** triple
generator, so the two views cannot disagree — they did, briefly, during authoring, which is the
whole argument in miniature.

**Why facets are `skos:Collection`, not `skos:broader`.** The page categories vary along three
orthogonal axes (graphics × text type × tabular layout). A concept belongs to all three at once and
has no single parent, so `skos:broader` would be false. `skos:Collection` asserts membership without
asserting hierarchy, which is exactly the claim being made.

**Why the CNEC codes carry no definitions.** Only the code→coarse-type mapping exists in the
codebase; nobody wrote glosses. Inventing them would be worse than omitting them, so `prefLabel` is
the code itself and `dct:source` points at the CNEC 2.0 documentation. See [§7](#-7-follow-ups).

**Validation is advisory, never fatal.** `validate_labels()` reports and returns findings; it never
raises. This matches the idiom already established in `atrium_document.py` — abstain with a `NOTE`
on stderr rather than refuse a document — and it is why the registry could be wired into five repos
without risking a single pipeline.

## 📤 5. The SKOS view of the source vocabularies

`vocab_build.py --skos` writes `data_samples/vocab/union.skos.ttl`: **5,594 concepts, 55,188
triples, 5.2 MB**, deterministic, gated by the existing `--check` drift mechanism.

### 5.1 What it is built from, and why that matters

Emitted from the **raw harvest**, not from `merged` or `filtered_source`:

* `merged` is label-keyed and deduplicated — one winner per Czech label. Correct for a prompt
  glossary; **data loss** for a concept graph. 624 collisions means 624 concepts would vanish.
* `filtered_source` has the `__exclude__` lists removed. Exclusion decides what to *offer a model*,
  not what exists. Dropping `zeme` because the prompt does not need country names would make the
  graph lie about AMCR's contents.

Curation decisions stay where they belong: in the nested artifacts the pipeline reads.

### 5.2 `broader` means two different things, and neither is `skos:broader`

This was the single most consequential finding, and it was only visible by measuring:

| Source                 | Edges  | Cross-scheme     | Verdict                                                    |
|------------------------|--------|------------------|------------------------------------------------------------|
| AMCR `hierarchie_vyse` | 1,176  | **1,176 (100%)** | associative → `skos:related`                               |
| TEATER `broader`       | 14,684 | **0**            | real hierarchy → `skos:broader` + `skos:broaderTransitive` |

`obývání` — an *activity* — declares 22 "superior" terms, and every one is an `areal`, a site type.
That is "this activity is recorded for these site types", not a thesaurus hierarchy. Emitting it as
`skos:broader` would have given one concept 22 parents and stated something false.

TEATER's is a genuine hierarchy, but the field holds the **whole ancestor chain root-first** (up to
12 deep). `skos:broader` is defined as the *direct* link, so only the last element becomes
`skos:broader`; the rest become `skos:broaderTransitive`.

> ⚠️ **Neither mistake would have failed a validator.** `skos:broader` across 22 cross-facet parents
> is well-formed RDF; it is merely untrue. That asymmetry — syntax passes, meaning is wrong — is why
> the reasoning lives in a comment next to the code that emits it, and is pinned by a test.

### 5.3 Citations are not mappings

TEATER hangs `quotes` off each label equivalent, and some point at Getty AAT. The parser walked past
them; they are now harvested into `citation_uri` and serialised as **`dcterms:source`**.

They are **not** `skos:exactMatch`. A quote is bibliographic support for a label — "this English
equivalent is attested in AAT" — not a claim that two concepts are the same thing. Promoting them
would manufacture identity claims TEATER never made, which is exactly the over-claim the AMCR side
already avoids by refusing to promote `broadMatch`. Upgrading any of them is an editorial act for
the vocabulary curators, not a parsing decision.

The same discipline governs `same_as` (`vocab_manager.py:1192`): a label-shape heuristic, scoped to
scoring, explicitly *"changes nothing about the prompt or the schema"*. **It is not serialised as
`skos:exactMatch` or `owl:sameAs`.**

### 5.4 Mapping relations are no longer discarded

`vocab_sources.py` tested `relation == "skos:exactMatch"` and dropped everything else. The narrowing
was right — a `broadMatch` in a field named `exact_match` would be a lie — but the fix for "this URI
means something weaker" is a field for the weaker thing, not silence. `AMCR_MAPPING_RELATIONS` now
routes all four SKOS mapping properties to their own fields. `exact_match` keeps its name and its
exact previous contents, so every existing consumer is untouched.

### 5.5 Getting the URIs to runtime without touching the prompt

The obvious route — adding `exact_match` to `_settings.nested_keep` — is **wrong**, and this is worth
recording because it looks right. `VocabularyManager.get_prompt_string()` serialises the *entire*
nested structure into the model's system prompt, so that one config edit would inject 707 Getty URIs
plus 5,594 source URIs verbatim into every request. This repo maintains a whole reviewer sheet
(`context_budget.csv`) about how much vocabulary survives a context window; spending it on
identifiers a model can neither read nor use would be a poor trade, and it would change model
behaviour — which populating a provenance field must never do.

Instead `vocab_manager.concept_index()` / `resolve_pid()` read the flat artifacts directly (stdlib
`json` only, so the service import path stays free of `lxml`). 4,952 labels indexed; 432 resolve to
a Getty AAT concept. `entities[].pid` — declared since schema 1.0, described as *"the
ARIADNE/GoTriple hook"*, written by nothing — is now fillable:

```
resolve_pid("keramika") -> {"wikidata": None, "geonames": None,
                            "aat":   "http://vocab.getty.edu/aat/300235507",
                            "amcr":  "https://api.aiscr.cz/id/HES-000933"}
```

`wikidata` and `geonames` stay `None`: nothing in these repos resolves them, and a guess in a FAIR
cross-reference field is worse than a null. A hook that lies is not a hook.

## 🐞 6. Defect register

Found while mapping the vocabulary layer. Each is a case of an uncontrolled label crossing a repo
boundary. **V-1 was documented, not fixed, by explicit decision** — fixing it changes what text
reaches the model on the OCR path, a pipeline behaviour change with an owner. The owner took it on
2026-09-25 (atrium-alto-postprocess#31, see F1).

### V-1 — `DROP_CATEGORIES` never matched on the OCR path ✅ fixed 2026-09-25

`atrium-llm-enrich/api_util/json_to_md.py`'s `DROP_CATEGORIES` filtered
`frozenset({"Garbage", "Inverted"})`. Those are `digital-convert`'s labels. `alto-postprocess` emits `Clear`/`Empty`/`Noisy`/`Non-text`/`Trash`
(`text_util.py:1152-1385` → `service/text_inference.py:363` → `service/text_api.py:196`). The sets
are disjoint, so **every OCR-path document passed its garbage lines straight to the model.**

Three separate places asserted the opposite, and all three are corrected here: the schema's `categ`
description, `alto-postprocess/service/text_api.py:177-179`, and `json_to_md.py`'s own comment,
which credited the values to *"alto-postprocess's compute_quality_score"*.

**The fix, taken 2026-09-25** (`json_to_md.DROP_CATEGORIES`; pinned by atrium-llm-enrich
`tests/test_json_to_md.py::test_convert_drops_trash_lines_on_the_ocr_path`):

```python
from atrium_vocab import UNTRUSTWORTHY_LINE_CATEGORIES

DROP_CATEGORIES = frozenset(UNTRUSTWORTHY_LINE_CATEGORIES)  # {"Garbage", "Inverted", "Trash"}
```

It needed an owner because it changes what the model sees. The registry made it one line and makes
the relationship machine-readable: `a-line-category:Trash skos:closeMatch
a-line-category:Garbage` — `closeMatch`, not `exactMatch`, because one is an OCR judgement over a
rendered image and the other a decode-sanity judgement over an embedded text layer. Close, not
identical, and deliberately not transitive.

### V-2 — `collect_images()` broke on its own shipped sample data ✅ fixed

`atrium-page-classification/utils.py` derived categories with `sorted(os.listdir(directory))`.
The shipped `small_data_samples/` contains a `LICENSE` **file**, which sorted into position 2. On
that tree the call **raised `NotADirectoryError`**; with a stray *directory* instead it silently
returned a 12-element list, shifting every class index after it out of step with
`model_registry.CATEGORIES`.

`collect_images()` now takes the categories from the dataset root's **sub-directories** only,
hidden ones (`.ipynb_checkpoints/`) excluded, so files such as `LICENSE` are ignored and the shipped
tree yields exactly the eleven declared labels. This does change what the function returns on a tree
that holds stray files; on a clean tree the list is the same. What a filter cannot catch is a stray
or missing category *directory* — an `unsorted/` holding pen, a mistyped label folder — so the
advisory check, `_advise_category_drift()`, still runs and names such an entry. Pinned by three
tests in `TestCollectImages`, one of them on the shipped `small_data_samples/`.

### V-3 — vocabulary harvesting is duplicated and divergent ⚠️ partially addressed

`atrium-translator/load_vocab.py` is a second harvester: AMCR over OAI-PMH (same as nlp-enrich) but
TEATER over **GraphQL** rather than the pinned snapshot, producing 5,087 rows against nlp-enrich's
4,723. It discarded every identifier it received. It now carries `source`, `source_id` and `uri`
through to a 5-column CSV, prefix-compatible with nlp-enrich's `*_flat.csv`. **The duplication
itself remains** — see [§7](#-7-follow-ups).

Also found and **not** fixed, since both predate this work and are out of scope:
`_download_and_parse_export()` is a stub returning `{}`, and the `main()`/CLI that
`atrium-translator/README.md:341-369` documents does not exist in the file.

### V-5 — `teater_category` is a source label, and two consumers read it as a theme ⚠️ mitigated

Found on 2026-09-16 while wiring F6. `CONCEPT_SCHEMES["theme"]` declares its field as
`enrichment.items[].teater_category` **"(indirectly, via the facet)"** — the eleven themes are
ATRIUM's own editorial grouping, and the parenthesis is doing load-bearing work. Production drops
it: `llm_client_shared.py:269` writes the model's raw **source** label (`kostel`), never a theme.

Two consumers then read the field as if it held a theme directly:

* `atrium_vocab.validate_labels("theme", …)` reports every real value as unknown — an advisory
  that cries wolf on correct data, which is how it came to be ignored;
* `atrium_rocrate.CONTROLLED_TERMS` mapped it to the `theme` scheme, so the crate minted
  `https://w3id.org/atrium/theme/kostel`: an ATRIUM-authored identifier for an **AMCR** concept,
  against §3's rule that ATRIUM mints nothing for a harvested concept, and one that resolves to
  nothing beside the real URI.

**Mitigated, not closed.** `document_crate()` now prefers the source URI as a term's `@id`
wherever the record carries one, so with F6 populated the crate identifies `kostel` as
`https://api.aiscr.cz/id/HES-000021` and mints nothing. That removes the false claim and the
dangling URI on the path that matters.

What is NOT decided, and needs an owner: whether `teater_category` should carry the source label
(and the theme be derived through `HESLAR_TO_THEME` / `TEATER_BRANCH_TO_THEME` when wanted), or
whether the field should hold the theme and the source label move to a sibling. Today the schema's
own description says "Single most relevant TEATER/AMCR vocabulary category", which agrees with
production — so the registry's `fields` entry and `validate_labels`' scheme choice are the two
things out of step, not the pipeline. Either way it is a contract change, not a freeze.

### V-4 — schema examples contradicted the label set ✅ fixed

`atrium_document.schema.json`'s `page_categories` examples were `{"1": "Text", "2": "Plate"}`.
Neither is in `CATEGORIES`.

## 🗂️ 7. Follow-ups (not done here, deliberately)

| #      | Item                                                                                        | Why not now                                                                                                                                                                                                                                                                                                                                                                     |
|--------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~~F1~~ | ~~Take the V-1 fix~~ ✅ **done 2026-09-25**                                                  | Taken. `DROP_CATEGORIES` now filters on `UNTRUSTWORTHY_LINE_CATEGORIES`, so `Trash` is dropped on the OCR path. **This changes what the model is shown.** Pinned by `test_convert_drops_trash_lines_on_the_ocr_path`. (This row said "done 2026-09-16" before the code carried it; atrium-alto-postprocess#31 found the constant unchanged and the test missing on 2026-09-25.) |
| ~~F2~~ | ~~Fix V-2 by filtering to directories~~ ✅ **done 2026-09-23**                               | Taken. `collect_images()` filters to directories, so the shipped `small_data_samples/` no longer raises and class indices cannot silently shift. Three tests in `TestCollectImages`.                                                                                                                                                                                            |
| F3     | Retire the translator's duplicate harvester in favour of nlp-enrich's artifacts             | ⚠️ **partly taken 2026-09-16** — see below. Full retirement still needs a release plan.                                                                                                                                                                                                                                                                                         |
| F4     | Add verified CNEC 2.0 glosses as `skos:definition`                                          | Needs the CNEC reference; inventing them would be worse than omitting                                                                                                                                                                                                                                                                                                           |
| F5     | Register the `w3id.org/atrium` redirect                                                     | Optional; blocks nothing                                                                                                                                                                                                                                                                                                                                                        |
| ~~F6~~ | ~~Add `*_uri` fields and populate `teater_category_uri`~~ ✅ **done 2026-09-16**             | `enrichment.items[].teater_category_uri` added (additive, no bump) and populated from `vocab_manager.concept_index()` — never through `nested_keep`, so the prompt is untouched. The crate now uses it as the term's `@id`; see V-5.                                                                                                                                            |
| F7     | Re-harvest so `close_match`/`broad_match`/`citation_uri` populate the committed artifacts   | Needs network; the parser is ready and tested                                                                                                                                                                                                                                                                                                                                   |
| ~~F8~~ | ~~Delete the orphaned `fixtures/e2e/VOCAB/teater_nested_vocab.json`~~ ✅ **done 2026-09-16** | Deleted. `fixtures/e2e/README.md` had described it as removed since 2026-08-19 while the file was still on disk.                                                                                                                                                                                                                                                                |

### F3, the half that was taken (2026-09-16)

`load_vocab.py` gained **`--from-flat DIR`**: it rebuilds `data_samples/vocabulary.csv` from
nlp-enrich's committed `amcr_flat.csv` / `teater_flat.csv` instead of harvesting. The two formats
were already prefix-compatible by construction, so this reads rather than converts. The harvester
is untouched and still the default — what changed is that reproducing the shipped vocabulary no
longer *requires* running it, which is the part of V-3 that was costing us two different answers.

The committed CSV was regenerated with it, and is now the five-column provenance form it had
supported for weeks without ever being rebuilt:

|         | before                                | after                        |
|---------|---------------------------------------|------------------------------|
| columns | 2 (`source_lemma,target_translation`) | 5 (`…,source,source_id,uri`) |
| rows    | 5,087                                 | 4,952                        |

⚠️ **This is a vocabulary content change, not just a format change.** Against the previous file:
**159 terms lost, 24 gained, 11 retranslated** (e.g. `cesta` "roads" → "path/road"; `dožínky`
"Dozhinki" → "harvest festival"). The losses are TEATER ethnology terms — `akulturace`, `bajka`,
`diaspora` and similar — that the live GraphQL API returns and the **pinned** snapshot
(`TEATER_SNAPSHOT_REF = 2106c59…`) does not. That is the trade V-3 names: one reproducible source
of truth instead of two that disagree. If the 159 matter more than reproducibility, the snapshot
ref is the thing to move, not this path.

> ⚠️ Unrelated but found in passing, and worth someone's attention:
> `docs/templates/workflows/update_issues.sh:92` contains a hardcoded GitHub PAT. It is committed.
> Not touched here; it should be revoked.

## ✅ 8. Verification

Everything below was run:

| Check                                                                             | Result                                                                                      |
|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `atrium_vocab.py --selftest`                                                      | 6 schemes, 64 concepts, 5 collections, 75 mappings — OK                                     |
| Turtle + JSON-LD parsed by `rdflib`                                               | 507 triples each, **isomorphic**                                                            |
| SKOS integrity (prefLabel uniqueness, inScheme, S27 broader/related disjointness) | 0 violations                                                                                |
| `atrium_vocab.schema.json` vs the JSON-LD                                         | 0 errors, 121 nodes                                                                         |
| `union.skos.ttl` parsed by `rdflib`                                               | 55,188 triples; 0 concepts with >1 direct `skos:broader`                                    |
| `vocab_build.py --from-flat --skos --check`                                       | rc 0 (clean)                                                                                |
| …with the SKOS artifact tampered                                                  | rc 1 (gate holds)                                                                           |
| Byte-stability across runs                                                        | identical sha256                                                                            |
| `revendor_shared.sh --check`                                                      | 11 canonical files in parity across 5 repos ¹                                               |
| hub suites (`tests/` + `docs/templates/shared/`)                                  | 190 passed                                                                                  |
| nlp-enrich vocab suites                                                           | 273 passed                                                                                  |
| llm-enrich full suite (`not slow`)                                                | 830 passed, 43 skipped                                                                      |
| alto-postprocess full suite (`not slow`)                                          | 814 passed, 9 skipped                                                                       |
| translator full suite                                                             | 452 passed, 2 skipped                                                                       |
| page-classification full suite                                                    | 382 passed, 16 skipped, 2 xfailed                                                           |
| alto behaviour-preservation                                                       | 32,400 paired calls, **0** mismatches                                                       |
| `entities[].pid` populated end-to-end                                             | 3 of 4 sample entities resolve; the person resolves to nothing and writes no row            |
| `ruff check`                                                                      | clean in all six repos                                                                      |
| Upstream `origin/test` re-fetched before finalising                               | hub moved `4053b48`→`193697e` (issue-log refresh only); **no overlap** with any edited file |

> ¹ The set has grown since this table was recorded — #54 and #60 each added canonical
> files after this verification pass. `docs/templates/shared/MANIFEST.json` is the current
> count (atrium-project#59); this row is a point-in-time record of what #51 verified, not a
> living total.

## 🔄 9. Maintenance

* **Editing a label set** means editing `docs/templates/shared/atrium_vocab.py` in the hub, running
  `scripts/revendor_shared.sh`, and committing all six repos in one window. `para-drift` fails
  otherwise. Never edit a vendored copy.
* **The three separate registrations this section describes below are now one.** As of
  atrium-project#59, `docs/templates/shared/MANIFEST.json` is the single row a new canonical file
  needs — `scripts/revendor_shared.sh`, `tools/skill_drift_check.py`, `para-drift.reusable.yml` and
  `docs/templates/ruff.toml`'s `[format] exclude`/`known-first-party` are all derived from it, checked
  by `tests/test_shared_manifest.py`. The mechanics below (why `atrium_vocab` needs each of the
  three) are still accurate history and still the reason the manifest carries these fields; they are
  no longer three places to remember by hand.
* **`REGISTRY_VERSION`** bumps when a concept is added, removed or renamed — label-set membership is
  a contract other repos read. Editing a definition, note or mapping is additive.
* **`atrium_vocab.py` is in every repo's `ruff.toml` `[format] exclude`.** Without it `ruff format`
  reflows the vendored copy to the local line length and breaks para-drift — the same trap
  `force-exclude = true` was added for.
* **`tests/test_atrium_vocab.py` is in every repo's `[format] exclude` too, and the file itself is
  written to be format-stable.** This was missed on the first pass and para-drift caught it in
  llm-enrich CI. The cause was not a new discovery — `docs/templates/ruff.toml`'s own `[format]`
  comment already spells it out: `line-length` is **100** in the two enrich repos and **120**
  everywhere else, so `ruff format` reflows a shared file to whatever the local width says and
  *"a shared file's byte content became a function of which repo committed it last"*. The
  exclusion is therefore mandatory, which is why `test_para_licenses.py` and
  `test_document_originators.py` were already in that list; the only mistake was not adding the
  third canonical test to it. Belt and
  braces: the file was also rewritten so every code line stays under 100 characters, making
  `ruff format` a no-op at *both* widths — verified — so parity no longer depends on the exclusion
  being remembered. Long comment lines are fine; ruff does not reflow comments or docstrings.
* **`atrium_vocab` is in `docs/templates/ruff.toml`'s `known-first-party`.** Omitting it reproduces
  the "unwinnable loop" that file already documents: `test_atrium_vocab.py` is byte-identical across
  six repos, isort classifies a bare `import atrium_vocab` as third-party in the hub (where the
  module lives under `docs/templates/shared/`, not an importable root) and first-party in a tool
  repo (where it sits at the root), and the two want mutually exclusive import formatting — so
  `ruff check --fix` in one place breaks the other, forever. Declaring the classification makes it
  layout-independent. This was hit during authoring, exactly as the comment predicted.
* **The registry is a view, never a second source of truth.** Each scheme names its authority in
  `rdfs:comment`; when the two disagree, the authority wins and the registry is wrong.
