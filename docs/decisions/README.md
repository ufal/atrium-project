# Decision records

> **Status:** index, added 2026-10-25 for [#81](https://github.com/ufal/atrium-project/issues/81).
> **Scope:** the hub's dated decisions and history: its CI workflows, and the records moved out of its
> reference pages.

Dated notes on why the hub's workflows are built the way they are: the incidents, superseded designs
and decisions that used to live in workflow comments. A workflow keeps its intent and invariants in
short comments and points here for the history ([`ci_policy.md`](../ci_policy.md), Workflow shape).

- [`docker-tool-reusable.md`](docker-tool-reusable.md): `docker-tool.reusable.yml`, the tool
  repositories' test, container probe, publishing and CVE gate.
- [`e2e-lanes.md`](e2e-lanes.md): `e2e-pipeline-smoke.yml` and `e2e-digital-smoke.yml`, the scanned and
  born-digital end-to-end lanes.
- [`release-trust-log.md`](release-trust-log.md): the recorded states of rulesets, releases and pins, the
  release-gate rollout of October 2026 and the Trivy database incidents.
- [`document-schema-history.md`](document-schema-history.md): the dated changelog of the document record
  schema, July to November 2026.
- [`agent-skills.md`](agent-skills.md): the planning decisions, work plans and rollout of the Agent Skills.
