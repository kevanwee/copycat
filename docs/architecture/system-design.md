# System Design

## Components
- Next.js frontend
- FastAPI API service
- Celery worker
- Redis queue/broker
- SQL database (SQLite dev, PostgreSQL-ready)
- Object storage abstraction (local dev; S3-compatible in deployment)

## Data Flow
1. Create case
2. Upload original + alleged artifacts
3. Start analyze job
4. Worker extracts and scores
5. Legal rule pack evaluation
6. JSON report persisted
7. PDF rendered and served

## Deterministic Surfaces
- preprocessing
- scoring weights
- legal node evaluation
- report id derivation from checksums and versions

## Retention
- cleanup script deletes artifacts/reports older than 24h

## Deployment Notes
- Single-tenant cloud target
- private network placement
- encrypted storage/DB