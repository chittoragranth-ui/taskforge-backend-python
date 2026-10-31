
from sqlalchemy.orm import Session
from ..models import Job


# Create a new job
def create_job(db: Session, job_type: str, payload: dict):
    try:
        db_job = Job(
            type=job_type,
            payload=payload,
        )

        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        return db_job

    except Exception:
        db.rollback()
        raise


# Get all jobs
def get_all_jobs(db: Session, skip: int, limit: int):
    total = db.query(Job).count()

    jobs = (
        db.query(Job)
        .order_by(Job.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return total, jobs


# Get a job by ID
def get_job_by_id(db: Session, job_id: str):
    job = db.query(Job).filter(Job.id == job_id).first()

    return job


# Update job status
def update_job_status(db: Session, job_id: str, new_status: str):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        return None

    try:
        job.status = new_status

        db.commit()
        db.refresh(job)

        return job

    except Exception:
        db.rollback()
        raise

    