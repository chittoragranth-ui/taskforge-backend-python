from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


# Schema for creating a job
class JobCreate(BaseModel):
    type: str = Field(min_length=1)
    payload: dict[str, Any]


# Schema for updating job status
class JobStatusUpdate(BaseModel):
    status: Literal[
        "queued",
        "processing",
        "completed",
        "failed",
    ]


# Schema for returning job data
class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    payload: dict[str, Any]
    status: str

class JobCreateResponse(BaseModel):
    message: str
    job: JobResponse


class JobListResponse(BaseModel):
    count: int
    skip: int
    limit: int
    jobs: list[JobResponse]


class JobUpdateResponse(BaseModel):
    message: str
    job: JobResponse