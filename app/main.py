from typing import Any

from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Query,
    Depends,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import Job


app = FastAPI(title="TaskForge API")


# Request model for creating a job
class JobCreate(BaseModel):
    type: str = Field(min_length=1)
    payload: dict[str, Any]


# Request model for updating a job's status
class JobStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(queued|processing|completed|failed)$"
    )


# Convert database object into a dictionary
def serialize_job(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "payload": job.payload,
        "status": job.status,
    }


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to TaskForge",
        "status": "running",
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TaskForge API",
    }


# Create a new job
@app.post(
    "/api/v1/jobs",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
):
    db_job = Job(
        type=job.type,
        payload=job.payload,
        status="queued",
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return {
        "message": "Job created successfully",
        "job": serialize_job(db_job),
    }


# List all jobs
@app.get("/api/v1/jobs")
def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    total_count = query.count()

    jobs = (
        query.order_by(Job.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "count": total_count,
        "skip": skip,
        "limit": limit,
        "jobs": [serialize_job(job) for job in jobs],
    }


# Retrieve a job by its ID
@app.get("/api/v1/jobs/{job_id}")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return {"job": serialize_job(job)}


# Update a job's status
@app.patch("/api/v1/jobs/{job_id}/status")
def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job.status = update.status

    db.commit()
    db.refresh(job)

    return {
        "message": "Job status updated successfully",
        "job": serialize_job(job),
    }
