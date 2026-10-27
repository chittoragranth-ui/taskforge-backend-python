
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, status , Query
from pydantic import BaseModel, Field


app = FastAPI(title="TaskForge API")

# Temporary in-memory storage for jobs
jobs: dict[str, dict[str, Any]] = {}


# Request model for creating a job
class JobCreate(BaseModel):
    type: str = Field(min_length=1)
    payload: dict[str, Any]


# Request model for updating a job's status
class JobStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(queued|processing|completed|failed)$"
    )


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
def create_job(job: JobCreate):
    job_id = str(uuid.uuid4())

    job_data = {
        "id": job_id,
        "type": job.type,
        "payload": job.payload,
        "status": "queued",
    }

    jobs[job_id] = job_data

    return {
        "message": "Job created successfully",
        "job": job_data,
    }


# List all jobs


@app.get("/api/v1/jobs")
def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    all_jobs = list(jobs.values())
    paginated_jobs = all_jobs[skip : skip + limit]

    return {
        "count": len(all_jobs),
        "skip": skip,
        "limit": limit,
        "jobs": paginated_jobs,
    }




# Retrieve a job by its ID
@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return {"job": job}


# Update a job's status
@app.patch("/api/v1/jobs/{job_id}/status")
def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
):
    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job["status"] = update.status

    return {
        "message": "Job status updated successfully",
        "job": job,
    }
