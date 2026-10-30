import uuid
from typing import Any

from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
    )

