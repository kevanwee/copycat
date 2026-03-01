# Copycat

Singapore-first copyright infringement triage tool with deterministic similarity scoring.

## Stack
- Frontend: Next.js (TypeScript)
- API: FastAPI
- Worker: Celery + Redis
- Database: SQLite (dev) / PostgreSQL-ready via SQLAlchemy
- Storage: Local filesystem (dev) / S3-compatible abstraction

## Runtime Notes
- Recommended runtime for full feature set (video + transcript): **Python 3.11**.
- `backend/requirements.txt` contains base dependencies.
- `backend/requirements-video.txt` contains optional video/ML extras.

## Quick start (docker)
```bash
docker compose up --build
```

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Local backend run
```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
# Optional for video metrics/transcription:
# pip install -r requirements-video.txt
uvicorn app.main:app --reload --port 8000
```

## Local worker run
```bash
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info
```

## Notes
- v1 is **triage only**. It is not legal advice.
- Uploaded source files are retained for 24h by default.