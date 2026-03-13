from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.reading import Reading


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # OPC-UA node identifier, e.g. "ns=2;i=1001"
    node_id: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # e.g. Float, Int, Bool, String
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Float")
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    equipment: Mapped[Equipment] = relationship(
        "Equipment", back_populates="tags"
    )
    readings: Mapped[list[Reading]] = relationship(
        "Reading", back_populates="tag", cascade="all, delete-orphan"
    )
