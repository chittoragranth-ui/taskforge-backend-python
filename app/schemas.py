from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str | None = None
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class JobCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0, le=10)


class JobUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str | None = Field(default=None, min_length=1)
    payload: dict[str, Any] | None = None
    status: Literal["queued", "processing", "completed", "failed"] | None = None
    priority: int | None = Field(default=None, ge=0, le=10)


class JobStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["queued", "processing", "completed", "failed"]


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    payload: dict[str, Any]
    status: str
    priority: int = 0
    result: dict[str, Any] | None = None
    error_message: str | None = None


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


class UserStatsResponse(BaseModel):
    total_jobs: int
    queued_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    recent_jobs: list[JobResponse]
