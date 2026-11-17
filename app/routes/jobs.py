from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Job, User
from ..schemas import (
    JobCreate,
    JobCreateResponse,
    JobListResponse,
    JobResponse,
    JobStatusUpdate,
    JobUpdate,
    JobUpdateResponse,
)
from app.workers.tasks import process_job

from ..services.job_service import create_job, get_all_jobs, get_job_by_id, update_job_status

router = APIRouter(prefix="/api/v1", tags=["jobs"])


def serialize_job(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "payload": job.payload,
        "status": job.status,
        "priority": getattr(job, "priority", 0),
        "result": getattr(job, "result", None),
        "error_message": getattr(job, "error_message", None),
    }


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreateResponse)
def create_job_route(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_job = create_job(db, job_data.type, job_data.payload, user_id=current_user.id, priority=job_data.priority)
    try:
        process_job.apply_async(args=[db_job.id, db_job.type, db_job.payload], queue="default")
    except Exception:
        pass
    return {"message": "Job created successfully", "job": JobResponse.model_validate(db_job)}


@router.get("/jobs", response_model=JobListResponse)
def get_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, jobs = get_all_jobs(db, current_user.id, skip, limit, status=status, job_type=job_type)
    return {
        "count": total,
        "skip": skip,
        "limit": limit,
        "jobs": [JobResponse.model_validate(job) for job in jobs],
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = get_job_by_id(db, job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"job": serialize_job(job)}


@router.patch("/jobs/{job_id}", response_model=JobUpdateResponse)
def update_job_route(
    job_id: str,
    update_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_job_by_id(db, job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if update_data.type is not None:
        job.type = update_data.type
    if update_data.payload is not None:
        job.payload = update_data.payload
    if update_data.priority is not None:
        job.priority = update_data.priority
    if update_data.status is not None:
        try:
            job = update_job_status(db, job_id, update_data.status, user_id=current_user.id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    db.commit()
    db.refresh(job)
    return {"message": "Job updated successfully", "job": JobResponse.model_validate(job)}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = get_job_by_id(db, job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully", "job_id": job_id}


@router.patch("/jobs/{job_id}/status", response_model=JobUpdateResponse)
def update_job_status_route(
    job_id: str,
    status_data: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        job = update_job_status(db, job_id, status_data.status, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"message": "Job status updated successfully", "job": JobResponse.model_validate(job)}


@router.get("/jobs/{job_id}/executions")
def get_job_executions(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = get_job_by_id(db, job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {
        "job_id": job_id,
        "executions": [
            {
                "id": execution.id,
                "job_id": execution.job_id,
                "attempt_number": execution.attempt_number,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "error_message": execution.error_message,
            }
            for execution in job.executions
        ],
    }
