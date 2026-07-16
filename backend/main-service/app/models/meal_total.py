import uuid
from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealTotal(Base):
    """Diet Service owns this view (service.v_meal_totals) — main-service only
    reads it. meal_log_id isn't a real PK (it's a view), marked primary_key
    here only so SQLAlchemy can map the class; never written to."""

    __tablename__ = "v_meal_totals"
    __table_args__ = {"schema": "service"}

    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    total_calories: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_sugars: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
