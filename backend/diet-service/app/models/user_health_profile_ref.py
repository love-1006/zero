from decimal import Decimal

from sqlalchemy import Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserHealthProfileRef(Base):
    """Main Service 소유 — service.user_health_profiles. 읽기 전용 (당/칼로리 목표 조회용)."""

    __tablename__ = "user_health_profiles"
    __table_args__ = {"schema": "service"}

    user_id: Mapped[int] = mapped_column(primary_key=True)
    birth_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    daily_calorie_target: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    daily_sugar_target_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
