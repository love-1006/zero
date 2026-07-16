import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealLog(Base):
    """Diet Service 소유 — service.meal_logs.

    input_type: VISION | MANUAL | PRODUCT | RECIPE (실제 DB CHECK 제약)
    analysis_status: PENDING | PROCESSING | COMPLETED | FAILED (실제 DB CHECK 제약)
    meal_type: BREAKFAST | LUNCH | DINNER | SNACK | OTHER (실제 DB CHECK 제약 —
      'DAILY'는 허용되지 않는다. "하루 식단" 업로드는 OTHER로 매핑한다,
      app/routers/diet.py 참고)
    """

    __tablename__ = "meal_logs"
    __table_args__ = {"schema": "service"}

    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(nullable=False)           # FK → public.users(id), 소프트 참조
    input_type: Mapped[str] = mapped_column(String(20), default="VISION")
    meal_type: Mapped[str] = mapped_column(String(20), default="SNACK")
    # 실제 컬럼명은 image_object_key (image_url이 아님)
    image_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
