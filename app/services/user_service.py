from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import Job, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_stats(db: Session, user_id: str) -> dict[str, Any]:
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
    total_jobs = len(jobs)
    queued_jobs = sum(1 for job in jobs if job.status == "queued")
    processing_jobs = sum(1 for job in jobs if job.status == "processing")
    completed_jobs = sum(1 for job in jobs if job.status == "completed")
    failed_jobs = sum(1 for job in jobs if job.status == "failed")
    recent_jobs = jobs[:5]
    return {
        "total_jobs": total_jobs,
        "queued_jobs": queued_jobs,
        "processing_jobs": processing_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "recent_jobs": recent_jobs,
    }
