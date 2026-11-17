from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.database import SessionLocal
from app.models import Job, JobExecution
from app.workers.celery_app import celery_app


def _safe_text_transform(value: str) -> dict[str, Any]:
    text_value = str(value)
    return {
        "original": text_value,
        "uppercase": text_value.upper(),
        "word_count": len(text_value.split()),
        "char_count": len(text_value),
    }


def _safe_data_transform(payload: dict[str, Any]) -> dict[str, Any]:
    record = dict(payload)
    return {
        "keys": sorted(str(key) for key in record.keys()),
        "values": [record[key] for key in record.keys()],
        "count": len(record),
    }


def _safe_math_compute(payload: dict[str, Any]) -> dict[str, Any]:
    operation = str(payload.get("operation", "add")).lower()
    left = float(payload.get("left", 0))
    right = float(payload.get("right", 0))
    if operation == "add":
        result = left + right
    elif operation == "subtract":
        result = left - right
    elif operation == "multiply":
        result = left * right
    elif operation == "divide":
        if right == 0:
            raise ValueError("Division by zero is not allowed")
        result = left / right
    else:
        raise ValueError(f"Unsupported operation: {operation}")
    return {"operation": operation, "left": left, "right": right, "result": result}


@celery_app.task(name="taskforge.process_job")
def process_job(job_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        execution = JobExecution(
            job_id=job_id,
            attempt_number=(db.query(JobExecution).filter(JobExecution.job_id == job_id).count() + 1),
            status="processing",
            started_at=datetime.now(timezone.utc),
        )
        db.add(execution)
        db.commit()

        job.status = "processing"
        db.commit()

        if job_type == "text_processing":
            result = _safe_text_transform(str(payload.get("text", "")))
        elif job_type == "data_transformation":
            result = _safe_data_transform(dict(payload))
        elif job_type == "math":
            result = _safe_math_compute(dict(payload))
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        completed_at = datetime.now(timezone.utc)
        job.result = result
        job.status = "completed"
        job.completed_at = completed_at
        job.error_message = None
        execution.status = "completed"
        execution.completed_at = completed_at
        db.commit()
        return result
    except Exception as exc:
        failed_at = datetime.now(timezone.utc)
        job = db.query(Job).filter(Job.id == job_id).first()
        if job is not None:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = failed_at
        execution = db.query(JobExecution).filter(JobExecution.job_id == job_id).order_by(JobExecution.attempt_number.desc()).first()
        if execution is not None:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = failed_at
        db.commit()
        raise
    finally:
        db.close()
