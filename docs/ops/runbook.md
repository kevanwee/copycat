# Operations Runbook

## Services
- API: `uvicorn app.main:app`
- Worker: `celery -A app.celery_app.celery_app worker --loglevel=info`
- Redis broker

## Startup
1. Ensure storage/report directories exist
2. Start Redis
3. Start API and worker
4. Verify `/health`

## Scheduled Tasks
- retention cleanup:
  - command: `python -m app.scripts.cleanup_expired`
  - frequency: hourly

## Incident Handling
- If jobs stuck in `queued`, check Redis and worker connectivity.
- If report missing, inspect worker logs for extraction/scoring exceptions.
- For deterministic drift, verify dependency versions and scoring constants.

## Rollback
- Deploy previous container image tags for API + worker in lockstep.
- Keep DB backups before schema migrations.