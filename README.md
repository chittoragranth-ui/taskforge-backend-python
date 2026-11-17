# TaskForge

TaskForge is a FastAPI backend for managing authenticated jobs and background processing.

## Features
- User registration and login with password hashing and JWT
- Authenticated user profile and stats endpoints
- Job creation, listing, filtering, status updates, and history
- SQLAlchemy models and PostgreSQL persistence
- Alembic migrations
- Celery + Redis worker tasks for safe job execution
- Docker Compose support for API, worker, PostgreSQL, and Redis

## Local setup
1. Create a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and adjust values as needed.
4. Start PostgreSQL and Redis locally.
5. Run database migrations:
   `alembic upgrade head`
6. Start the API:
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
7. Start the worker:
   `celery -A app.workers.celery_app worker --loglevel=info`

## Testing
- Run the full suite:
  `pytest -q`

## Docker
- Build and start services:
  `docker compose up --build`

## macOS notes
- PostgreSQL can run via local service or Docker
- Redis can run via Docker or local install
- For local development, ensure `DATABASE_URL` and `REDIS_URL` match your environment
