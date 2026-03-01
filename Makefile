.PHONY: backend-install backend-test backend-run worker cleanup frontend-install frontend-dev frontend-build

backend-install:
	py -3.11 -m pip install -r backend/requirements.txt

backend-test:
	cd backend && py -3.11 -m pytest -q

backend-run:
	cd backend && py -3.11 -m uvicorn app.main:app --reload --port 8000

worker:
	cd backend && py -3.11 -m celery -A app.celery_app.celery_app worker --loglevel=info

cleanup:
	cd backend && py -3.11 -m app.scripts.cleanup_expired

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build