# Operations runbook — v2

## Supported operating mode

The verified small-instance configuration is a single Uvicorn process with
SQLite and local persistent storage. `COPYCAT_CELERY_TASK_ALWAYS_EAGER=true`
dispatches a FastAPI background task after the analysis response is sent. It
does not call Celery inline inside the route. The legacy setting name remains
for deployment compatibility. Use one API process: local-mode startup marks
interrupted work failed so the user can retry.

Redis/Celery dispatch remains available when that setting is false. For a
distributed deployment, validate queue recovery, shared storage, PostgreSQL
drivers/migrations, concurrency and task termination in that environment first.
It is not the default compose configuration or a tested scale-out claim. Celery
results are ignored: a second ungoverned copy of the report must not be kept in
Redis. The database is the report source of truth.

## Deployment requirements

- Python 3.11, current pinned `requirements.txt`, `requirements-image.txt` for
  image/video metrics; FFmpeg/ffprobe for video. No model downloads or OCR.
- One API process for local background mode; process supervision/restarts.
- Persistent database and upload/report roots on the same deployment's volume.
  Render's `/tmp` baseline configuration is ephemeral and remains a demo only.
- Exact `COPYCAT_FRONTEND_BASE_URL` origins (comma-separated if needed). The
  frontend's build-time API URL must match the reachable API deployment.
- HTTPS and an ingress proxy with request-size, request-rate, connection-timeout,
  and resource limits before accepting public traffic. Anonymous case creation
  is capability-based, not a multi-user account/tenant system.
- Application ingress caps JSON at 256 KiB and multipart at the largest configured
  media cap plus 256 KiB; per-media caps are checked after parsing. Upload access
  is checked before parsing. Limits also count chunked request bodies.
- Defaults: text 10 MB / 20,000 normalized tokens; still image 20 MB / 25 MP;
  video 100 MB / 300 seconds. PDF: unencrypted, at most 300 pages, with text layer.
  ZIP-expanded DOCX content is capped at 50 MB. Animated images are rejected.
- Capacity admission is a small-instance guard, not a globally atomic quota.
  Do load and isolation testing before exposing to untrusted multi-tenant load.

## Access and privacy

Creation returns a 256-bit random capability once. Only its SHA-256 is stored
with the case. Requests supply `X-Case-Token`; never put it in a query string or
log it. Wrong/missing keys and legacy unkeyed cases return 404. Users can save
the key locally. Browser storage is per-tab session storage; closing the tab can
lose access. There is no unauthenticated recovery endpoint.

Reports and previews are non-cacheable. Reports include the supplied legal notes
and source excerpts and must be handled with the same care as source files.
Fonts are served locally. No uploaded work or legal notes go to third-party AI.
The application does not claim PDPA compliance merely because it has a notice.

## Retention and deletion

Expiry runs from **case creation**, not the latest rerun. Access is denied after
24 hours by default. An in-process loop removes expired cases every 300 seconds;
it also runs at startup. It removes case rows, artifacts, metrics, jobs, reports,
PDFs and derived images/video frames. Running/queued/uploading cases are protected
from simultaneous deletion; access still expires. Local restart releases stale
states. Explicit deletion refuses while work is active.

Run manual cleanup using the same configuration and environment:

```sh
cd backend
python -m app.scripts.cleanup_expired
```

Physical erasure is not instantaneous at expiry and is not assured while the
service is stopped. Secure deletion from media, SQLite free pages, infrastructure
snapshots and backups is outside application-level deletion; define those policies
for the actual hosting arrangement. Never promise complete forensic erasure.

## Failure and recovery

### Live frontend cannot connect

If the Vercel site loads but the questionnaire does not, inspect the browser's
request to `/api/v1/cases/questionnaire`. A healthy `/health` response alone does
not verify browser access.

For the existing deployment, set the Render API service environment variable
`COPYCAT_FRONTEND_BASE_URL=https://copycat-mu.vercel.app` (no trailing slash),
then redeploy that service. The frontend uses
`NEXT_PUBLIC_API_BASE_URL=https://copycat-5wgw.onrender.com` at build time.
Changing `render.yaml` does not establish that an existing service's dashboard
environment was updated; check the running service's actual response.

Verify both a questionnaire GET and an OPTIONS preflight with the Vercel
`Origin`. Responses must include
`Access-Control-Allow-Origin: https://copycat-mu.vercel.app`; the preflight must
also permit `content-type` and `x-case-token`. Do not replace the allowlist with
a wildcard. On 15 September 2026 the deployed v2 API returned the questionnaire
but allowed localhost rather than the live Vercel origin, blocking the browser.

Initial connection attempts time out after 15 seconds and offer a retry. A
sleeping demo backend may take longer to start; retry after it wakes. Upload
requests retain their separate, longer timeout.

`GET /health` is liveness. Query `/api/v1/cases/questionnaire` to see available
media, limits and active legal rules. Failed extraction produces a failed job,
not a fabricated score. Users can rerun or start a new case with corrected files.
If dispatch fails, the job and case become failed. Repeated analysis/mutation
while a case is busy returns 409; capacity pressure returns 429. A context edit
invalidates the previous PDF/JSON. Download prior versions before revising.

Monitor process health, disk space, cleanup error logs, stuck jobs and storage
growth. In distributed mode, investigate orphaned queued/running states against
the worker before resetting them; do not blindly run the local recovery path.

## Migration and rollout

Deploy API and frontend together. This is a breaking v2 report/intake contract.
No database columns were added; intake and token hash use existing metadata JSON.
Old cases have no access secret and are intentionally inaccessible. Preserve any
required legacy reports through an operator-controlled export before rollout;
do not create a public legacy bypass. Old `legal_inputs`, booleans and generic
metadata are rejected. Remove `COPYCAT_RULE_PACK_VERSION=sg_v1` and old scoring
overrides from the deployment environment.

The branch is reviewable separately from main. Existing live baseline URLs are
not proof that v2 is deployed. The user authorised progressive GitHub pushes;
cloud deployment and main-branch merge are separate release operations.
