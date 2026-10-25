# Decision records

> **Status:** index, added 2026-10-25 for [#81](https://github.com/ufal/atrium-project/issues/81).
> **Scope:** the hub's CI workflows.

Dated notes on why the hub's workflows are built the way they are: the incidents, superseded designs
and decisions that used to live in workflow comments. A workflow keeps its intent and invariants in
short comments and points here for the history ([`ci_policy.md`](../ci_policy.md), Workflow shape).

- [`docker-tool-reusable.md`](docker-tool-reusable.md): `docker-tool.reusable.yml`, the tool
  repositories' test, container probe, publishing and CVE gate.
- [`e2e-lanes.md`](e2e-lanes.md): `e2e-pipeline-smoke.yml` and `e2e-digital-smoke.yml`, the scanned and
  born-digital end-to-end lanes.
