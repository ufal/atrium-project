# Skill-branch templates (issue #31)

Validated versions of [`docs/agent_skill_strategy.md`](../../agent_skill_strategy.md)
Appendices A–D, promoted here after the first full rollout run across all five
service repos (page-classification hardening + nlp-enrich / alto-postprocess /
translator / llm-enrich skill layers). Copy, then replace every `<placeholder>`.

| File | Appendix | Purpose |
|------|----------|---------|
| [`SKILL.template.md`](SKILL.template.md) | A | the `SKILL.md` skeleton (frontmatter + required section order) |
| [`atrium_client.skeleton.py`](atrium_client.skeleton.py) | B | runnable zero-dependency client skeleton (§6 contract) |
| [`server.template.sh`](server.template.sh) | C | idempotent `scripts/server.sh` launcher |
| [`serviceREADME.template.md`](serviceREADME.template.md) | D | `service/README.md` outline |

CI guard for the finished branch:
[`skill-validate.reusable.yml`](../../../.github/workflows/skill-validate.reusable.yml)
(caller example in
[`../workflows/skill-validate.caller.example.yml`](../workflows/skill-validate.caller.example.yml)).

## Corrections surfaced by the first rollout run

Deviations from the original appendices, learned by building the real branches:

1. **Read timeouts are service-specific.** 300 s suits model inference
   (page-classification); pipeline services need more (nlp-enrich 900 s), and
   LLM extraction needs much more (llm-enrich 1800 s). Encode the ceiling in
   the client's default timeout, not in agent patience.
2. **429-aware messaging is part of the client contract** for services with a
   concurrency guard (nlp-enrich, llm-enrich): print an actionable hint
   (async jobs / retry later) instead of the generic server-error line.
3. **Non-tabular outputs drop `--format`.** The translator returns an XML
   attachment, so its client uses `-o FILE` / `-o -` semantics instead of
   `--format table|csv|json`; forcing the tabular surface onto it would be
   cosmetic conformance.
4. **Emit CSV via the `csv` module** whenever a free-text column (line text,
   keyword lists) is included — hand-joined commas break on real archival text.
5. **`server.sh --local` must match the repo's actual venv/provisioning**
   (`venv`, `venv-nlp`, `venv-api`; setup script names differ per repo) —
   don't copy the launcher blindly.
6. **Per-line/state summaries go to stderr**, keeping stdout clean for
   `--format csv|json` consumers.
