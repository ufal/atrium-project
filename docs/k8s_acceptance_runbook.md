# Kubernetes acceptance runbook (S2 handover)

How AMČR operators accept the six ATRIUM `-api` images on their own Kubernetes before the S2 pilot
(atrium-project#77; the procedure was first written for #55). It runs the reference manifest
[`templates/k8s/atrium-service.deployment.yaml`](templates/k8s/atrium-service.deployment.yaml), not the
bare image: Kubernetes reads probes from the manifest, never from a Dockerfile `HEALTHCHECK`. The reasons
behind each field are in [`k8s_deployment.md`](k8s_deployment.md).

**You need:** a Kubernetes namespace you can deploy to, `kubectl`, `curl`, `python3`, a checkout of
`atrium-project`, the six approved images (§"Image identity") and one test input per service
(§"Per-service smoke request"). The commands run from the root of the checkout.

**Who runs it:** the receiving operators, on the receiving cluster. ÚFAL CI does not run it and never needs
access to AMČR infrastructure (#40). The nearest check ÚFAL runs is the container probe in
`docker-tool.reusable.yml` (`docker run`, health, `SIGTERM`), which steps 1–3 below mirror for one
container; the rolling-restart checks need a real Deployment.

## Handover rules

These hold for this runbook and for every operator page linked from the S2 pilot page.

1. **Examples are acceptance artifacts.** From a clean checkout and the prerequisites above, every command
   works with only the named substitutions (`TOOL`, `VERSION`, `DIGEST`, the input files). A failing HTTP
   response is a failed check, never a green step: every `curl` here uses `--fail-with-body` or compares the
   status code it prints.
2. **One configuration authority.** What a service enforces is what its code resolves, in this order:
   the code default (`tool_limits.py`, `service/api.py`) → the repository's `.env.example`, which documents
   those defaults → a Compose override → the Deployment's `env` and Secrets. `GET /info` reports the
   effective values; when a document disagrees with `/info`, `/info` is right and the document is a bug.
   Deployment knobs (ports, limits, timeouts, endpoints) are not research parameters (model choice,
   thresholds), and only the former belong in a manifest.
3. **Prerequisites and boundaries are stated per service.** Model download and cache, storage, egress,
   backing services, secrets, limits, and single-replica or non-durable-job restrictions are in
   [`k8s_deployment.md`](k8s_deployment.md) (Table A, Table B, "Known limits") and in each service's
   `service/README.md`. This runbook links them rather than repeating them. The manifest is an example, not
   an AMČR production deployment.
4. **Handover needs evidence.** Record the image digest each pod actually ran and the observed result of
   each check in the results table below. "Instructions were followed" is not a result.
5. **Someone who did not write a service walks its path** before it is handed over: from its README to a
   passing smoke request. Cluster rollout and drain verification stay with AMČR operators.
6. **Keep it checkable.** `tests/test_k8s_handover.py` fails when a service drops out of these tables, when
   a `curl` here can pass on an HTTP error, when the port-forward target is not an object of the manifest, or
   when an image tag carries a leading `v`.

## Image identity

| What                 | Form                                    | Example                                              | Mutable?                           |
|----------------------|-----------------------------------------|------------------------------------------------------|------------------------------------|
| Source release       | Git tag `vX.Y.Z[-suffix]`               | `v1.2.1-beta`                                        | no (tag rules, immutable releases) |
| Image tag            | the release **without** its leading `v` | `ghcr.io/ufal/atrium-digital-convert-api:1.2.1-beta` | can be re-pushed                   |
| Image identity       | the manifest digest                     | `…-api:1.2.1-beta@sha256:<64 hex>`                   | no                                 |
| Development channels | `test`, `latest`                        | `…-api:latest`                                       | yes, by design                     |

`test` and `latest` move with every build and are never a pilot baseline. The S2 set is the six digests
approved for the pilot. Read a digest with
`docker buildx imagetools inspect ghcr.io/ufal/atrium-<tool>-api:<version>` (the `Digest:` line). With
`DIGEST` set below, Kubernetes pulls by digest, and the tag only labels it. Tag protection and immutable
releases are in [`release_trust.md`](release_trust.md). Which releases passed the hub's E2E lanes together
is in each run's `e2e-manifest` artifact ([`ci_policy.md`](ci_policy.md)).

## Before you start

1. **Upload limits differ per service.** `MAX_UPLOAD_MB` defaults: digital-convert 200, translator 50,
   ocr-postprocess 25, keyword-extract 10, page-classification 10, **nlp-enrich 5**. A smoke file over the
   limit returns 413 at once, the request is no longer in flight when the restart lands, and the restart
   check proves nothing. Keep each input under its limit.
2. **keyword-extract's controlled kind needs a backend.** Without `OPENROUTER_API_KEY` and
   `OPENROUTER_MODEL` (for `LLM_BACKEND=openrouter`) the service starts, `GET /info` reports
   `controlled.ready: false` with the reason, and `kind=controlled` answers 501. The smoke request below uses
   the statistical kind, which needs no key. To accept the controlled kind as well, create the Secret and
   uncomment its `secretKeyRef` stanza first (`k8s_deployment.md` §"Environment variables").
3. **digital-convert's `/describe` calls two other stages.** Set `PAGE_CLASSIFICATION_URL` and
   `OCR_POSTPROCESS_URL` to their Services (`http://atrium-page-classification-api:8000`,
   `http://atrium-ocr-postprocess-api:8000`) to run them. Unset, each stage is reported `not_configured` and
   the request still succeeds. `/reformat` calls neither. With stages configured, raise `STAGE_TIMEOUT_S`,
   `GRACEFUL_SHUTDOWN_S` and `terminationGracePeriodSeconds` together (`k8s_deployment.md` Table B).
4. **`ALLOWED_ORIGINS` defaults to `*`.** Set it in the manifest before applying if the cluster is reachable
   from browsers on a network where that matters.
5. **`replicas: 1` stays 1 for nlp-enrich.** Its job registry is in memory, per replica (`service/jobs.py`),
   so `GET /jobs/<id>` on another replica answers 404. The other five may scale once your load balancing is in
   place. See `k8s_deployment.md` §"Known limits".

## Shared procedure (every service)

Set the three variables and the per-service request (§"Per-service smoke request"), then run the steps in
order. `set -u` stops on a variable you forgot.

```bash
set -u
TOOL=digital-convert        # page-classification | ocr-postprocess | translator | nlp-enrich | keyword-extract | digital-convert
VERSION=1.2.1-beta          # the approved release, without its leading v
DIGEST=                     # sha256:… of the approved image; empty pulls by tag
IMAGE="ghcr.io/ufal/atrium-${TOOL}-api:${VERSION}${DIGEST:+@${DIGEST}}"
DEPLOY="deployment/atrium-${TOOL}-api"

assert_json() {  # assert_json FILE KEY...: the body parses as JSON and has every KEY
  python3 -c 'import json,sys; b=json.load(open(sys.argv[1])); m=[k for k in sys.argv[2:] if k not in b]; sys.exit("missing: " + ", ".join(m) if m else 0)' "$@"
}

# 1. Apply the manifest (Deployment + Service) with the image substituted.
sed -e "s|ghcr.io/ufal/atrium-<tool>-api:<version>|${IMAGE}|" -e "s/<tool>/${TOOL}/g" \
    docs/templates/k8s/atrium-service.deployment.yaml | kubectl apply -f -

# 2. Wait for the startupProbe (minutes on a first pull or model download).
kubectl rollout status "$DEPLOY" --timeout=10m

# 3. The probe contract from inside the pod, readiness, and the digest the pod runs.
kubectl exec "$DEPLOY" -- python /app/service/healthcheck.py
kubectl get pod -l "app.kubernetes.io/name=atrium-${TOOL}-api" \
    -o jsonpath='{.items[0].status.containerStatuses[0].ready}{"\n"}{.items[0].status.containerStatuses[0].imageID}{"\n"}'
#    → "true", then the image reference with its digest: record the digest in the results table.

# 4. One smoke request through the Service; it must answer 200 with the expected body.
kubectl port-forward "svc/atrium-${TOOL}-api" 8000:8000 >/dev/null & PF_PID=$!
sleep 2
code=$(curl --fail-with-body -sS -o smoke.json -w '%{http_code}' -X POST "localhost:8000${ENDPOINT}" "${FORM[@]}")
if [ "$code" = 200 ] && assert_json smoke.json "${KEYS[@]}"; then echo "PASS smoke"
else echo "FAIL smoke: HTTP ${code:-none}: $(head -c 300 smoke.json)"; fi

# 5. Rolling restart while a request is in flight. The check is only valid if the request is still
#    running when the restart starts, so that is tested first.
( c=$(curl --fail-with-body -sS -o restart.json -w '%{http_code}' -X POST "localhost:8000${ENDPOINT}" "${FORM[@]}"); echo "$c" > restart.code ) &
REQ_PID=$!
sleep "${LEAD:-2}"
if ! kill -0 "$REQ_PID" 2>/dev/null; then
  echo "INVALID: the request ended before the restart; use a slower input (see the table)"
else
  echo "restart begins $(date -u +%T), request still running"
  kubectl rollout restart "$DEPLOY"
  wait "$REQ_PID"
  code=$(cat restart.code)
  if [ "$code" = 200 ] && assert_json restart.json "${KEYS[@]}"; then echo "PASS restart: in-flight request answered 200 at $(date -u +%T)"
  else echo "FAIL restart: HTTP ${code:-none}: $(head -c 300 restart.json)"; fi
fi
kubectl rollout status "$DEPLOY" --timeout=5m
kill "$PF_PID" 2>/dev/null   # a port-forward follows one pod; start a new one for further requests
```

Step 5 proves the **drain**: a request already being served when its pod is told to stop is completed by
that pod. It does not prove that new requests are routed away from a stopping pod. For that, run this
in-cluster loop in a second terminal while you repeat the restart. Every line must print `200`:

```bash
kubectl run atrium-probe --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- \
  sh -c 'for i in $(seq 60); do curl -sS -o /dev/null -w "%{http_code}\n" http://atrium-'"$TOOL"'-api:8000/info || echo FAIL; sleep 1; done'
```

### Acceptance criteria (per service)

1. **Probes behave as documented.** `startupProbe` passes on a cold pod without a restart during model
   warmup. `livenessProbe` does not fire during the rolling restart: check `kubectl get events` for
   `Killing` or `Unhealthy` during step 5, not only before it. `readinessProbe` turns not-ready within a
   few seconds of the restart.
2. **A rolling restart drops no in-flight request.** Step 5 prints `PASS restart`. `INVALID` is not a pass;
   retry with a slower input.
3. **A non-default `PORT` is honoured** (#58). Set `PORT` to `9000` in the manifest's `env:` and
   `containerPort` to match (the probes and the Service use the port name and follow). The pod reaches
   Ready, and the probe inside it reaches the new port:

   ```bash
   kubectl rollout status "$DEPLOY" --timeout=5m
   kubectl exec "$DEPLOY" -- python /app/service/healthcheck.py
   # → healthy: http://127.0.0.1:9000/health returned HTTP 200
   ```

   Run `healthcheck.py` inside the pod. A `curl` through a port-forward passes even when the probe looks at
   the wrong port, which is the failure this criterion exists to catch.
4. **The declared environment is the one the process sees** (#60). Set `LOG_LEVEL: "DEBUG"`,
   `ALLOWED_ORIGINS: "https://acceptance.invalid"` and `MAX_UPLOAD_MB: "1"`, roll out, start a port-forward,
   then:

   ```bash
   kubectl logs "$DEPLOY" | head -20 | grep -q DEBUG && echo "PASS log level" || echo "FAIL log level"
   curl --fail-with-body -sS -D allowed.hdr -o /dev/null -H 'Origin: https://acceptance.invalid' localhost:8000/info \
     && grep -qi '^access-control-allow-origin' allowed.hdr && echo "PASS origin allowed" || echo "FAIL origin allowed"
   curl --fail-with-body -sS -D refused.hdr -o /dev/null -H 'Origin: https://not-allowed.invalid' localhost:8000/info \
     && ! grep -qi '^access-control-allow-origin' refused.hdr && echo "PASS origin refused" || echo "FAIL origin refused"
   code=$(curl -sS -o big.json -w '%{http_code}' -X POST "localhost:8000${ENDPOINT}" -F "${UPLOAD_FIELD}=@<a 2 MB file>")
   [ "$code" = 413 ] && grep -q limit_exceeded big.json && echo "PASS upload limit" || echo "FAIL upload limit: HTTP $code"
   ```

   `ALLOWED_ORIGINS` is the setting whose misconfiguration the server cannot see, so the refused-origin
   check matters more than the allowed one. Reset the three values before the other criteria.

## Per-service smoke request

Each row gives `ENDPOINT`, the form fields (`FORM`), the keys the body must have (`KEYS`) and the form
field of the upload (`UPLOAD_FIELD`, for criterion 4). The input must take several seconds, so the request
is still running when step 5's restart begins; raise `LEAD` for services that take long to read the upload.

```bash
# page-classification: one inference per page, in sequence
ENDPOINT=/predict_document; UPLOAD_FIELD=file
FORM=(-F "file=@<multi-page.pdf>"); KEYS=(type pages limits_applied)

# ocr-postprocess: language identification and quality per line
ENDPOINT=/process; UPLOAD_FIELD=file
FORM=(-F "file=@<large.alto.xml>"); KEYS=(type cleaned_lines limits_applied paradata)

# translator: one retried LINDAT call per 4,000-character chunk (needs egress to LINDAT)
ENDPOINT=/translate; UPLOAD_FIELD=file
FORM=(-F "file=@<large.alto.xml>" -F response_format=json); KEYS=(type content limits_applied paradata)

# nlp-enrich: UDPipe and NameTag at LINDAT, synchronous (needs egress to LINDAT)
ENDPOINT=/enrich; UPLOAD_FIELD=file
FORM=(-F "file=@<lines.csv>" -F lang=cs); KEYS=(doc_id stages teitok_xml limits_applied paradata)

# keyword-extract: the statistical kind, per page
ENDPOINT=/extract_keywords; UPLOAD_FIELD=document_json
FORM=(-F "document_json=@<record.json>" -F kind=statistical); KEYS=(doc_id keywords limits_applied paradata)

# digital-convert: the converter only
ENDPOINT=/reformat; UPLOAD_FIELD=file
FORM=(-F "file=@<born-digital.pdf>"); KEYS=(service doc_id document_json limits_applied paradata)

# digital-convert: the converter plus the stages of "Before you start" item 3
ENDPOINT=/describe; UPLOAD_FIELD=file
FORM=(-F "file=@<born-digital.pdf>"); KEYS=(service doc_id document_json pages summary stages)
```

Run digital-convert's procedure once per endpoint. For `/describe`, also record each stage's status from
`stages` in the body (`ok`, `partial`, `not_configured`, `unavailable`, …; the full list is in the
service's `service/openapi.json`).

### nlp-enrich: jobs are not durable

The restart check uses the synchronous `/enrich`. The asynchronous `/jobs` flow is checked **without** a
restart: `POST /jobs` → `job_id`; poll `GET /jobs/<id>` until `status` is `done`; `GET /jobs/<id>/result`.

```bash
code=$(curl --fail-with-body -sS -o job.json -w '%{http_code}' -X POST localhost:8000/jobs -F "file=@<lines.csv>")
[ "$code" = 200 ] && JOB=$(python3 -c 'import json; print(json.load(open("job.json"))["job_id"])') || echo "FAIL submit: HTTP $code"
curl --fail-with-body -sS -o status.json -w '%{http_code}\n' "localhost:8000/jobs/${JOB}"   # repeat until "status": "done"
```

A graceful shutdown lets a running job finish, but the registry and the workspace are lost with the pod: after
a restart, `GET /jobs/<id>` for a job of the old pod answers 404, even if it completed while draining.
Durable job status and results are **not supported**; a client re-submits. Record this row as "not
supported", not as a failure.

## Results (fill in)

| Service             | Image digest | Deploys | Probes | Smoke | Restart in flight | `PORT` | Env contract | Observed / notes                         |
|---------------------|--------------|---------|--------|-------|-------------------|--------|--------------|------------------------------------------|
| page-classification |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            |                                          |
| ocr-postprocess     |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            |                                          |
| translator          |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            |                                          |
| nlp-enrich          |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            | jobs across a restart: not supported     |
| keyword-extract     |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            | kind used:                               |
| digital-convert     |              | ☐       | ☐      | ☐     | ☐                 | ☐      | ☐            | `/describe` stages:                      |

In "Observed / notes", write what the step printed (`PASS`, `FAIL` with the HTTP code, `INVALID`), the
values set for criterion 4, and anything you had to change. Send the table to the contacts in
[`arub-p_contacts.md`](arub-p_contacts.md); the completed copy is linked from the S2 pilot page.
