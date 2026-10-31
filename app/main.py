from fastapi import FastAPI

from .routes import jobs

app = FastAPI(title="TaskForge API")

app.include_router(jobs.router)


@app.get("/")
def home():
    return {"message": "Welcome to TaskForge API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

