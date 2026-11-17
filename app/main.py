from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes.auth import router as auth_router
from .routes.jobs import router as jobs_router
from .routes.users import router as users_router

app = FastAPI(title="TaskForge API", version=settings.APP_VERSION)

origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(jobs_router)


@app.get("/")
def home():
    return {"message": "Welcome to TaskForge API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/ready")
def readiness_check():
    from sqlalchemy import text

    from .database import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        from redis import Redis

        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ready" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }
