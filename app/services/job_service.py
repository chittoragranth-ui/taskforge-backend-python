from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Job, JobExecution

VALID_STATUS_TRANSITIONS = {
    "queued": {"queued", "processing"},
    "processing": {"processing", "completed", "failed"},
    "completed": {"completed"},
    "failed": {"failed"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_job(
    db: Session,
    job_type: str,
    payload: dict,
    user_id: str | None = None,
    priority: int = 0,
):
    try:
        db_job = Job(
            job_type=job_type,
            payload=payload,
            user_id=user_id,
            status="queued",
            priority=priority,
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        db_execution = JobExecution(
            job_id=db_job.id,
            attempt_number=1,
            status="queued",
            started_at=_now(),
        )
        db.add(db_execution)
        db.commit()
        return db_job
    except Exception:
        db.rollback()
        raise


def get_all_jobs(
    db: Session,
    user_id: str,
    skip: int,
    limit: int,
    status: str | None = None,
    job_type: str | None = None,
):
    query = db.query(Job).filter(Job.user_id == user_id)
    if status is not None:
        query = query.filter(Job.status == status)
    if job_type is not None:
        query = query.filter(Job.job_type == job_type)
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return total, jobs


def get_job_by_id(db: Session, job_id: str, user_id: str | None = None):
    query = db.query(Job).filter(Job.id == job_id)
    if user_id is not None:
        query = query.filter(Job.user_id == user_id)
    return query.first()


def update_job_status(db: Session, job_id: str, new_status: str, user_id: str | None = None):
    job = get_job_by_id(db, job_id, user_id=user_id)
    if job is None:
        return None

    normalized_new = str(new_status).strip().lower()
    normalized_current = str(job.status).strip().lower()
    allowed = VALID_STATUS_TRANSITIONS.get(normalized_current, set())
    if normalized_new not in allowed:
        raise ValueError(f"Invalid job status transition from '{job.status}' to '{new_status}'")

    try:
        job.status = normalized_new
        if normalized_new == "processing" and job.started_at is None:
            job.started_at = _now()
        if normalized_new in {"completed", "failed"} and job.completed_at is None:
            job.completed_at = _now()
        db.commit()
        db.refresh(job)
        return job
    except Exception:
        db.rollback()
        raise


def add_job_execution(
    db: Session,
    job_id: str,
    attempt_number: int,
    status: str,
    error_message: str | None = None,
):
    execution = JobExecution(
        job_id=job_id,
        attempt_number=attempt_number,
        status=status,
        started_at=_now() if status in {"queued", "processing"} else None,
        completed_at=_now() if status in {"completed", "failed"} else None,
        error_message=error_message,
    )
    db.add(execution)
    db.commit()
    return execution
