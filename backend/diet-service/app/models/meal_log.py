import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealLog(Base):
    """Diet Service 소유 — service.meal_logs.

    input_type: VISION (한끼/하루 사진) | MANUAL (수동 입력)
    analysis_status: PENDING | COMPLETED | FAILED
    meal_type: BREAKFAST | LUNCH | DINNER | SNACK | DAILY
    """

    __tablename__ = "meal_logs"
    __table_args__ = {"schema": "service"}

    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(nullable=False)           # FK → public.users(id), 소프트 참조
    input_type: Mapped[str] = mapped_column(String(20), default="VISION")
    meal_type: Mapped[str] = mapped_column(String(20), default="SNACK")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
