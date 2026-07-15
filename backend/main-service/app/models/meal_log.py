import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealLog(Base):
    """Diet Service owns this table — main-service only reads it, to sum a
    user's daily calorie/sugar intake for the home-screen gauge."""

    __tablename__ = "meal_logs"
    __table_args__ = {"schema": "service"}

    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
