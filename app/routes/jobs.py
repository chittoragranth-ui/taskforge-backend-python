from typing import Any

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session

from ..models import Job

from ..database import get_db
from ..schemas import (
    JobCreate,
    JobStatusUpdate,
    JobCreateResponse,
    JobListResponse,
    JobUpdateResponse,
)
from ..services.job_service import (
    create_job,
    get_all_jobs,
    get_job_by_id,
    update_job_status,
)

router = APIRouter()


# Convert SQLAlchemy Job object into a dictionary
def serialize_job(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "payload": job.payload,
        "status": job.status,
    }


# Create a new job
@router.post(
    "/api/v1/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobCreateResponse,
)
def create_job_route(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    db_job = create_job(
        db,
        job_data.type,
        job_data.payload,
    )

    return {
        "message": "Job created successfully",
        "job": serialize_job(db_job),
    }


# Get all jobs
@router.get(
    "/api/v1/jobs",
    response_model=JobListResponse,
)
def get_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, jobs = get_all_jobs(db, skip, limit)

    return {
        "count": total,
        "skip": skip,
        "limit": limit,
        "jobs": [serialize_job(job) for job in jobs],
    }


# Get a specific job
@router.get("/api/v1/jobs/{job_id}")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return {"job": serialize_job(job)}


# Update job status
@router.patch(
    "/api/v1/jobs/{job_id}/status",
    response_model=JobUpdateResponse,
)
def update_job_status_route(
    job_id: str,
    status_data: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    job = update_job_status(db, job_id, status_data.status)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return {
        "message": "Job status updated successfully",
        "job": serialize_job(job),
    }
