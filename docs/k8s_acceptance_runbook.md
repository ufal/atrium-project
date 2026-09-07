# ✅ Kubernetes deployment acceptance runbook (issue #55)

Per-repo acceptance of the `-api` images running unattended on ARÚP/ARÚB's own Kubernetes —
the exact criterion issue #55 was opened against: *"ARÚP/ARÚB confirm the images run cleanly
on their Kubernetes."* Run against
[`templates/k8s/atrium-service.deployment.yaml`](templates/k8s/atrium-service.deployment.yaml)
(rationale: [`k8s_deployment.md`](k8s_deployment.md)), not against the bare image — there is
nothing in a `HEALTHCHECK` directive Kubernetes reads on its own (see `k8s_deployment.md`'s
opening section). **Requires a Kubernetes cluster and the five published `-api` images**;
this is a partner-side procedure, not something this repo's CI can run — the boundary
decided on 2026-08-02 (#40, motyc) is exactly "a Docker image, run at ARÚP/ARÚB's own
Kubernetes," so validating it is necessarily out-of-band.

## Shared procedure (every repo)

```bash
# 1. Substitute <tool>/<version> and apply the reference manifest.
sed -e 's/<tool>/nlp-enrich/g' -e 's/<version>/v1.2.0/g' \
    templates/k8s/atrium-service.deployment.yaml | kubectl apply -f -

# 2. Wait for the startupProbe to pass (may take minutes on first pull / model warmup).
kubectl rollout status deployment/atrium-nlp-enrich-api --timeout=10m

# 3. Confirm the probe contract from inside the cluster.
kubectl exec deploy/atrium-nlp-enrich-api -- python /app/service/healthcheck.py
kubectl get pod -l app.kubernetes.io/name=atrium-nlp-enrich-api \
    -o jsonpath='{.items[0].status.containerStatuses[0].ready}'   # must print "true"

# 4. Send real traffic through the Service, then trigger a rolling restart mid-flight, and
#    confirm nothing routed to it fails. Adjust the request per repo (see §"Per-repo smoke
#    request" below) — the point is a request that takes long enough to still be running
#    when the restart lands, not a specific endpoint.
kubectl port-forward svc/atrium-nlp-enrich-api 8000:8000 &
PF_PID=$!
<per-repo smoke request, backgrounded> &
REQ_PID=$!
sleep 1   # let the request actually start before the restart lands
kubectl rollout restart deployment/atrium-nlp-enrich-api
wait $REQ_PID   # must exit 0 — a nonzero exit here is exactly issue #55's
                # "a rolling restart kills in-flight work"
kubectl rollout status deployment/atrium-nlp-enrich-api --timeout=5m
kill $PF_PID
```

**Acceptance bar (both must hold, per repo):**
1. **The startup/liveness/readiness probes behave as documented** — `startupProbe` passes on
   a cold pod without flapping into a restart during model warmup; `livenessProbe` does not
   fire during a routine rolling restart (check `kubectl get events` for an unexpected
   `Killing`/`Unhealthy` during step 4, not just before it); `readinessProbe` reports not-
   ready within a few seconds of the restart being triggered.
2. **A rolling restart drops no in-flight request** — the backgrounded smoke request from
   step 4 completes successfully (`$?` = 0, expected response body) despite the restart
   landing mid-request.

## Per-repo smoke request

Use a request that legitimately takes several seconds, so it is still in flight when
`kubectl rollout restart` lands in step 4 above — a request that already returned before the
restart proves nothing about draining.

| Repo                | Smoke request                                                                                                  | Why it's slow enough to matter                                                                                             |
|---------------------|----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| page-classification | `curl -s -X POST localhost:8000/predict_document -F "file=@<multi-page.pdf>"`                                  | Multi-page PDF: one inference per page, in sequence                                                                        |
| alto-postprocess    | `curl -s -X POST localhost:8000/process -F "file=@<large.alto.xml>"`                                           | Per-line language ID + quality classification over a large file                                                            |
| translator          | `curl -s -X POST localhost:8000/translate -F "file=@<large.alto.xml>"`                                         | One retried remote LINDAT call per chunk — the slowest request shape in the fleet                                          |
| nlp-enrich          | `curl -s -X POST localhost:8000/jobs -F "file=@<large.csv>"` then poll `GET /jobs/<id>` until `status=="done"` | The one repo with a background job queue — this is the request shape issue #55's `state.track()` fix specifically protects |
| llm-enrich          | `curl -s -X POST localhost:8000/extract_keywords -F "file=@<many-lines.csv>"`                                  | One remote LLM call per line — can legitimately run for minutes                                                            |

## Results log (fill in)

| Repo                | Deploys clean | Probes behave | Rolling restart drops nothing | Notes |
|---------------------|---------------|---------------|-------------------------------|-------|
| page-classification | ☐             | ☐             | ☐                             |       |
| alto-postprocess    | ☐             | ☐             | ☐                             |       |
| translator          | ☐             | ☐             | ☐                             |       |
| nlp-enrich          | ☐             | ☐             | ☐                             |       |
| llm-enrich          | ☐             | ☐             | ☐                             |       |

> Environment note: this runbook cannot be run from this session or from any hub CI job —
> there is no Kubernetes cluster in scope here, by design (#40). The nearest in-repo proxy is
> `docker-tool.reusable.yml`'s container smoke (`docker run` + `HEALTHCHECK` + `SIGTERM`,
> opt-in per repo via `probe-targets`), which this runbook's steps 1–3 mirror at the
> single-container level; step 4's rolling-restart assertion needs a real Deployment and can
> only be run where one exists.
>
> Send results to the ARÚP/ARÚB contacts in [`arub-p_contacts.md`](arub-p_contacts.md), and
> record the completed table here (or link a copy under `agent_dev_logs/`) once returned.
