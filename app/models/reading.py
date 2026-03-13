from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tag import Tag


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Raw string value for non-numeric types
    raw_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # OPC-UA quality: Good, Bad, Uncertain
    quality: Mapped[str] = mapped_column(String(50), nullable=False, default="Good")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    tag: Mapped[Tag] = relationship("Tag", back_populates="readings")
