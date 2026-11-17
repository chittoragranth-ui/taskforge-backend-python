from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Job, User
from ..schemas import JobResponse, UserProfile, UserStatsResponse
from ..services.user_service import get_user_stats

router = APIRouter(prefix="/api/v1", tags=["users"])


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)


@router.get("/users/me", response_model=UserProfile)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/users/me", response_model=UserProfile)
def update_current_user_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None
    if payload.email is not None:
        normalized_email = payload.email.strip().lower()
        if "@" not in normalized_email:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email format")
        if db.query(User).filter(User.email == normalized_email, User.id != current_user.id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        current_user.email = normalized_email
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users/me/stats", response_model=UserStatsResponse)
def get_user_stats_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stats = get_user_stats(db, current_user.id)
    recent_jobs = [JobResponse.model_validate(job) for job in stats["recent_jobs"]]
    return {
        "total_jobs": stats["total_jobs"],
        "queued_jobs": stats["queued_jobs"],
        "processing_jobs": stats["processing_jobs"],
        "completed_jobs": stats["completed_jobs"],
        "failed_jobs": stats["failed_jobs"],
        "recent_jobs": recent_jobs,
    }
