# 🔎 ATRIUM cross-repo state — after the 30 September meeting (the repository split)

**Date: 30 September 2026 · Scope: all six `ufal` repositories, `test` HEADs, the grounding report, every issue it names**

_Successor to [`project_state_2609.md`](project_state_2609.md) (2026-09-26). Prior baselines:
[`project_state_0709.md`](project_state_0709.md), [`project_state_3007.md`](project_state_3007.md),
[`project_state_0208.md`](project_state_0208.md), [`project_state_2207.md`](project_state_2207.md),
[`project_state_1307.md`](project_state_1307.md), [`project_state_2706.md`](project_state_2706.md). Covers the four days
09-26 → 09-30: #32 round 2 (typed contracts), #68 (seed read-back), #69 (CI roadmap), #70 (record extensions), the
split of #67 into #71, #72, #73 and atrium-llm-enrich#28 — and the meeting of 30 September, which renamed one tool,
split two others and made the record schema a pilot baseline._

---

## §0 — How this pass was made

- **The reference** is David Novák's (@motyc, ARÚP) grounding report for the meeting, in two versions: the DOCX (the
  first draft of 30 September) and the MD (updated before the meeting and edited after it). A sentence-level diff
  of the two gives every change; the yellow highlights the report mentions did not survive in either file.
- **The meeting's record** is the MD's post-meeting edits (§2.2 tool table) plus four items opened the same
  afternoon (Part A). The user confirmed there were no other decisions or dates.
- **Tree state** — the six local clones, whose working branch equals `origin/test` in every repository (checked
  2026-09-30).
- **Issue tracker** — read live, read-only: every issue the report names, the sub-issues of #67, and a probe of each
  repository's numbering up to its newest issue (hub #74, page-classification #54, alto-postprocess #56, translator
  #49, llm-enrich #29, nlp-enrich #40).
- **Code facts** — every `file:line` below was read in the clones, not taken from earlier logs.

## 🧭 Branch HEADs and releases (2026-09-30)

| Repository                   | `test` = working branch | Latest release (CITATION.cff)   | After the meeting                                             |
|------------------------------|-------------------------|---------------------------------|---------------------------------------------------------------|
| `atrium-project` (hub)       | `9bffcea`               | — (tags: `v1`, `doc-schema-v1`) | `doc-schema-v1` to be read as the *pilot baseline* (#71 TODO) |
| `atrium-page-classification` | `eed2522`               | **1.9.0-beta** (09-29)          | unchanged                                                     |
| `atrium-alto-postprocess`    | `b3b4401`               | **1.6.0-beta** (09-25)          | → **`atrium-ocr-postprocess`** (alto#56)                      |
| `atrium-translator`          | `8d74c4c`               | **1.3.0-beta** (09-29)          | unchanged                                                     |
| `atrium-llm-enrich`          | `5cacf0b`               | **0.8.0** (09-27)               | → **`atrium-digital-born-convertor`** (llm#29)                |
| `atrium-nlp-enrich`          | `b21fc5c`               | **0.22.0** (09-25)              | LINDAT calls only; keywords leave (nlp#40)                    |
| `atrium-keyword-extractor`   | —                       | —                               | **new** (nlp#40): keywords from nlp-enrich and llm-enrich     |

---

## Part A — What the meeting changed

### A.1 The report's own edits (MD against DOCX)
Before the meeting (both versions share them): #67's requests became issues of their own — #71 (record, paradata,
RO-Crate), #72 (architecture, dependencies, release hardening), #73 (keywords, quality summary) and
atrium-llm-enrich#28 (`api-digital`); items 4 and 10 settled on both sides; #55 closed; the compute-server questions
collected in aiscr-docs-pipeline#9.

After the meeting, in the §2.2 tool table only:

| Row                               | DOCX                            | MD                                                                                                            |
|-----------------------------------|---------------------------------|---------------------------------------------------------------------------------------------------------------|
| `alto-postprocess`                | `alto-postprocess`              | **`ocr-postprocess`** (the MD shows the edit as `ocralto-postprocess`)                                        |
| (new)                             | —                               | **`keyword-extractor`** · `/extract_keywords` · *"combined repo for keywords from nlp-enrich and llm-enrich"* |
| `llm-enrich`                      | `/extract_keywords`             | **`/reformat`** (the "what it adds" cell still reads *vocabulary keywords, entity links*)                     |
| `digital-convert` (in llm-enrich) | *none yet; api-digital is next* | unchanged                                                                                                     |

### A.2 The four items opened after the meeting

| When (UTC) | Issue                                                                                   | What it says                                                                                                                                                                |
|------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 13:46      | [#71 comment](https://github.com/ufal/atrium-project/issues/71#issuecomment-5912586914) | *"The current doc-schema-v1 tag should be treated as beta-doc-schema-v1 and not as a final version of the document contract. Each tool edits its own block(s) in the JSON"* |
| 13:50      | [atrium-nlp-enrich#40](https://github.com/ufal/atrium-nlp-enrich/issues/40)             | statistical keywords (KER, KeyBERT) and the LLM controlled-vocabulary terms move to a new `ufal/atrium-keyword-extractor`; nlp-enrich keeps only LINDAT calls               |
| 13:53      | [atrium-llm-enrich#29](https://github.com/ufal/atrium-llm-enrich/issues/29)             | the repository becomes `atrium-digital-born-convertor`: a PDF to JSON of per-page blocks; possibly calling ocr-postprocess and page-classification to describe pages        |
| 15:13      | [atrium-alto-postprocess#56](https://github.com/ufal/atrium-alto-postprocess/issues/56) | rename to `ufal/atrium-ocr-postprocess`; the focus moves from ALTO to any text-bearing file, the pipeline is kept                                                           |

**Superseded by them:** #67's 09-30 06:56 comment (*"Statistical keywords belong to `nlp-enrich`"*), #73's scope line
(*"a dedicated statistical-keyword block owned by `nlp-enrich`"*) and #72's scope line (*"remove the duplicate
LLM/vocabulary implementation from `nlp-enrich`"* — now: move both copies out).

---

## Part B — The service map after the split

| Stage (Temporal activity) | Repository (today → target)             | Service · endpoint                   | Program id in the record (today → target) | Blocks it writes                                                      | GPU                                  |
|---------------------------|-----------------------------------------|--------------------------------------|-------------------------------------------|-----------------------------------------------------------------------|--------------------------------------|
| route: born-digital       | llm-enrich → **digital-born-convertor** | `api-digital` · **`/reformat`**      | `digital-convert` (unchanged)             | `source`, `pages`, `content`, `lines`, `tables`                       | —                                    |
| route: scans / stored OCR | alto-postprocess → **ocr-postprocess**  | `api` · `/process`                   | `alto-postprocess` → `ocr-postprocess`    | `pages`, `content`, `lines`, `tables`; scores born-digital lines (W3) | GPU 1                                |
| page categories           | page-classification                     | `api` · `/predict_document`          | `page-classification`                     | `page_categories`, `pages[].category*`                                | GPU 1                                |
| morphology, NER, TEITOK   | nlp-enrich (LINDAT only)                | `api` · `/enrich`, `/project_record` | `nlp-enrich`                              | `entities`, `lines[].lemma/upos/feats/teitok_ref`                     | — (CPU)                              |
| keywords                  | — → **keyword-extractor**               | `api` · **`/extract_keywords`**      | `llm-enrich` → `keyword-extractor`        | `keywords` (new), `enrichment`, `entities[].pid`                      | GPU 1 (KeyBERT); LLM server on GPU 2 |
| English metadata          | translator                              | `api` · `/translate`                 | `translator`                              | `translations`                                                        | — (LINDAT)                           |

Consequences, each carried by one plan:
- **The nlp/llm duplication disappears by construction.** Both copies of the LLM engine and the vocabulary code
  (`llm_utils.py`, `llm_run.py`, `vocab_*.py`, `prompt_template.py`, `corpus_review.py`, `llm_config.txt`: ~360 KB per
  copy; `llm_utils.py` differs by 404 diff lines, `vocab_build.py` by 43, `llm_run.py` by 11, the rest identical) leave
  both repositories for one: keyword-extractor ([`../plans/72.plan.md`](../plans/72.plan.md) B).
- **nlp-enrich becomes a CPU-only LINDAT client**: `yake`, `keybert`, `sentence-transformers` leave
  `requirements.txt:7-9`, and with them torch. Removing `kw_method` from `/enrich` is a breaking spec change, so
  under #32's rule nlp-enrich's next release is **1.0.0** (atrium-nlp-enrich `40.plan.md`).
- **The digital converter keeps its program id.** It has always written as `digital-convert`
  (`api_util/digital_to_json.py:171`, `PROGRAM = "digital-convert"`), so turning llm-enrich into the dbc repository does not touch the record.
- **Program ids are part of the record contract.** `BLOCK_OWNERS`, `BLOCK_FIELD_OWNERS` and `ORIGIN_ORIGINATORS`
  (`docs/templates/shared/atrium_document.py:108-280`; llm-enrich holds the `entities[].pid` grant at `:278`), `LINE_CATEGORY_ORIGINATORS` (`atrium_vocab.py:329`), the
  schema's block descriptions and TEITOK's `@resp` (`atrium-nlp-enrich/api_util/teitok_project.py:22-31`) name the
  tools. The decision of this pass: **rename with a read-time alias map** (`alto-postprocess` → `ocr-postprocess`,
  `llm-enrich` → `keyword-extractor`), in one round with #71's `sha512` and #73's `keywords` — see Part E.
- **No service calls another.** llm#29 floats calls from the converter to ocr-postprocess and page-classification;
  in the AMČR architecture Temporal chains the stages, so the converter's pages are described by the next two
  activities, not by the converter (atrium-llm-enrich `29.plan.md` §C).

---

## Part C — The report against the issues and the dev logs

### C.1 Decisions of §4

| Item                               | Report's *Needs*                   | ÚFAL issue                                          | Pair (after this pass)                       | Gap left                                               |
|------------------------------------|------------------------------------|-----------------------------------------------------|----------------------------------------------|--------------------------------------------------------|
| 1 Paradata shape, RO-Crate version | a date                             | #71                                                 | 🔄 refined                                   | date; `contentSize`; fragment validation               |
| 2 Identity seeded by AMČR          | a date                             | #71 (#68 closed)                                    | 🔄 refined                                   | date; seeded E2E not built                             |
| 3 Paradata from every service      | a date                             | #71 (slot from #32)                                 | 🔄 refined (six services, new names)         | date; builder not built                                |
| 4 Record-only mode                 | nothing                            | #67, #71 (out of scope)                             | —                                            | none                                                   |
| 5 Architecture cleanup             | order and dates                    | #72, #6                                             | ✍️ **rewritten**                             | order and dates; the split adds three repository moves |
| 6 Core per tool, the baseline      | amendments; close #57              | #67, #69, #57, alto #2 #3 #4 #30                    | 🔄 #67 refined; banners on the rest          | #57 cleanup; the time-box release (16 Oct)             |
| 7 Trust gate                       | a date for immutable releases      | #40, #72                                            | — (#72 D)                                    | date; the ARUP-CAS forks of the renamed repositories   |
| 8 Orchestration, hosting, limits   | Ronald Harasim's answers           | #32, #53, #58                                       | banner on #32                                | the two new services join #32/#53/#58's conventions    |
| 9 LINDAT and the licence switch    | Pavel Straňák's answer or an owner | translator #46, #4; **no issue for the permission** | —                                            | **proposed new issue** (translator)                    |
| 10 Galaxy                          | nothing                            | #66                                                 | banner on #66                                | image names change with the renames                    |
| 11 Born-digital path               | dates                              | llm #10, #28 (+ #29)                                | ✍️ #28 rewritten; #10 §13; #29 new           | dates; `/reformat` vs `/convert`; the repository move  |
| 12 Discovery scope                 | agreement                          | #73                                                 | ✍️ **written from scratch** (was #71's text) | block owner moved to keyword-extractor                 |
| 13 Owners per named state          | the table in §9                    | —                                                   | —                                            | not an issue                                           |

### C.2 Requests of §6

| #  | Request                                  | Issue                   | State (2026-09-30, code)                                                                                               |
|----|------------------------------------------|-------------------------|------------------------------------------------------------------------------------------------------------------------|
| 1  | Seeded baseline, `source.sha512` through | #71                     | read-back fixed (#68); a bare seed opens; `sha512` survives but is not in the schema                                   |
| 2  | Paradata as `CreateAction`               | #71                     | typed slot in every response (#32); filled by none                                                                     |
| 3  | Record-only mode                         | #71 (out of scope)      | deferred on both sides                                                                                                 |
| 4  | `atrium_rocrate.py` aligned              | #71                     | still RO-Crate 1.1; Process Run Crate already 0.5                                                                      |
| 5  | A `keywords` block                       | #73 → keyword-extractor | no block in the schema; statistical keywords only in `/enrich`'s response and in the TEITOK projection                 |
| 6  | Document quality summary (optional)      | #73                     | none; page and line quality exist                                                                                      |
| 7  | Architecture cleanup                     | #72                     | not started; the split changes its shape                                                                               |
| 8  | Born-digital path                        | llm #10, #28            | converter released (0.8.0) as a CLI; `ocr_text_layer` registered; no service                                           |
| 9  | Release hygiene                          | #40, #72                | immutable releases not on                                                                                              |
| 10 | Limits                                   | #53                     | done in the five tools; closes with #58                                                                                |
| 11 | PyMuPDF; flexiconv licence               | #6, #72                 | PyMuPDF still in page-classification; flexiconv confirmation to record                                                 |
| 12 | Vocabularies CC0                         | #6, #72                 | ✅ **done on `test`** in nlp-enrich (`para_config.txt:51-52`) and llm-enrich (`:82-83`); the translator from 1.2.2-beta |

### C.3 Where the report and the tracker still disagree
- **Request 12** is done on `test` in both repositories the report still lists as pending; the report's *"pending
  in #72"* is one release behind.
- **#73's owner.** The report (item 12) and #73 say nlp-enrich owns the statistical keywords; nlp#40 moves them. The
  report's §2.2 row already reflects the move; item 12 and request 5 do not.
- **The default keyword method.** The report settles *KeyBERT by default*. The service does so
  (`atrium-nlp-enrich/service/api.py:97`), the CLI does not (`keywords.py:80`, `DEFAULT_METHOD = "yake"`).
- **The born-digital endpoint.** llm#10 W1 names it `POST /convert`; the report's table after the meeting says
  `/reformat`.
- **`doc-schema-v1`.** The report (§2.2) says *"frozen … additive changes continue"*; #71's TODO calls it beta.
  `docs/document_schema.md` (*Changing the schema after the freeze*) makes a re-attributed block a MAJOR bump; Part E
  shows how the split stays inside the rules.

---

## Part D — Dev-log pairs: what this pass changed

| Repository       | Pair                                         | Before                                | This pass                                                       |
|------------------|----------------------------------------------|---------------------------------------|-----------------------------------------------------------------|
| hub              | `73.*`                                       | **#71's content under #73's number**  | ✍️ written from scratch                                         |
| hub              | `72.*`                                       | generic, no code evidence, pre-split  | ✍️ rewritten                                                    |
| hub              | `71.*`                                       | good (09-30, pre-meeting)             | 🔄 post-meeting section: beta baseline, six services, new names |
| hub              | `67.*`                                       | 09-26, pre-meeting                    | 🔄 umbrella after the split; superseded lines marked            |
| hub              | `6.*`, `32.*`, `66.*`, `57.*`, `4.*`, `17.*` | per their last round                  | 🧭 post-meeting banner                                          |
| llm-enrich       | `29.*`                                       | —                                     | 🆕 incl. the dbc design options                                 |
| llm-enrich       | `28.*`                                       | thin draft, off-format                | ✍️ rewritten                                                    |
| llm-enrich       | `10.*`                                       | 09-26 (§12)                           | 🔄 §13: the repository becomes dbc; W1–W6 carried by #28        |
| llm-enrich       | `11.*`                                       | deferred                              | 🧭 banner (the LLM engine moves to keyword-extractor)           |
| nlp-enrich       | `40.*`                                       | —                                     | 🆕                                                              |
| nlp-enrich       | `6.*`                                        | deferred                              | 🔄 status: the code moves to keyword-extractor                  |
| nlp-enrich       | `7.*`, `18.*`                                | deferred                              | 🧭 banner (custom NER stays; served through NameTag)            |
| nlp-enrich       | `teitok_conformance_plan.md`                 | Stage 9: nlp-enrich writes `keywords` | 🔄 Stage 9 marked superseded (the block moves with #40)         |
| alto-postprocess | `56.*`                                       | —                                     | 🆕                                                              |
| alto-postprocess | `2.*`, `3.*`, `4.*`, `30.*`, `23.*`          | finish / defer                        | 🧭 banner (the rename, after the time-box release)              |

**Still on disk for closed issues** (remove with the next export): hub `68.*`; nlp-enrich `11.*`, `19.*`;
alto-postprocess `31.*`, `37.*`; page-classification `48.*`.

**Exports pending** (`docs/templates/workflows/update_issues.sh` has not run since 14:39): #73, llm#29, nlp#40,
alto#56. The new digests name the paths the script will write. The script's `REPOS` list and
`scripts/revendor_shared.sh:69-72` both need the new repository names (alto#56 plan).

---

## Part E — The record contract after the split (#71's TODO)

The rules in `docs/document_schema.md` (*Changing the schema after the freeze*): an additive change is registered
under `doc-schema-v1`; *"removing or renaming a declared field, or re-attributing a written block, is a MAJOR bump"*.
The split needs neither, if it is done this way:

1. **The tag stays.** `doc-schema-v1` is never moved or re-cut (#40's immutability applies to it too). What changes is
   its *reading*: `document_schema.md` calls it **the pilot baseline**, and names the moment the contract becomes
   final — **before S2 pins the tool versions** — as either "v1 plus its register" or `doc-schema-v2`.
2. **A new program is authorised, not a written block re-attributed.** `BLOCK_OWNERS` already allows several
   candidate writers per block (`pages`, `content`, `lines`, `tables`). The successors are added beside their
   predecessors; records already written keep the stamps they have, which stay true.
3. **One alias map** in `atrium_document.py`, `PROGRAM_SUCCESSORS = {"alto-postprocess": "ocr-postprocess",
   "llm-enrich": "keyword-extractor"}`, used wherever a program is compared (origin check, field grants, the merge),
   never to rewrite a stamp. `digital-convert` is unchanged.
4. **One round**, one changelog date, one re-vendor, one `v1` move: `source.sha512` and the seed profile (#71), the
   `keywords` block and the optional quality summary (#73), the successors (alto#56, nlp#40). The predecessors leave
   the tables at the final freeze, which is the only step that may need `doc-schema-v2`.
5. **AMČR agrees first.** David accepted `doc-schema-v1` as the frozen reference on #54; the proposed new hub issue
   (*`doc-schema-v1` as the pilot baseline*) carries this to him.

---

## ✅ Verdict

The report and the tracker agree on the pilot's substance; they disagree on **who** does three things, because the
meeting moved them after the report's text was written: statistical keywords, the controlled vocabulary and the
born-digital service each change repository. Nothing in the record has to break for it — the converter keeps its
program id, the other two renames fit the existing multi-writer rule with one alias map — but three things must
happen in order: the schema round (Part E), then the repository moves, then the S2 pins. The dates the report asks
for are still open for items 1–3, 5, 7 and 11.

## Recommended actions, in order
1. **Post** the comments and open the three new issues of the drafts file (repository split umbrella; the pilot
   baseline of the schema; the LINDAT permission). Replace the bodies of alto#56, nlp#40 and llm#29 with the proposed
   ones.
2. **Agree with AMČR** on Part E (the pilot baseline and the successor map) — it gates the schema round.
3. **Schema round** in the hub: `sha512`, seed profile, `keywords`, quality summary, successors; re-vendor; move `v1`.
4. **alto-postprocess's time-box release** (16 October), *then* its rename (alto#56).
5. **keyword-extractor**: create the repository with history (llm-enrich's LLM and vocabulary code, nlp-enrich's
   `keywords.py`), then `/extract_keywords`; nlp-enrich 1.0.0 without them.
6. **llm-enrich → digital-born-convertor**: `api-digital` (#28) is built **now**, in parallel, under its final service
   id and its own spec asset; the repository move follows — the LLM code out first, then the rename, so no release of
   the renamed repository ships the LLM stack.
7. **#71's builder, validator and seeded E2E**, against the renamed services.
8. **Before S2 pins versions:** the final freeze (Part E.4), immutable releases (#40), the ARUP-CAS forks renamed.
