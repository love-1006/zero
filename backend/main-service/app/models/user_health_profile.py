from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserHealthProfile(Base):
    __tablename__ = "user_health_profiles"
    __table_args__ = {"schema": "service"}

    # FK to public.users(id), ON DELETE CASCADE — enforced by the DB. Not
    # declared as a SQLAlchemy ForeignKey since login-service's User model
    # (the actual owner of that table) isn't part of this codebase.
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    birth_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    health_goal: Mapped[str | None] = mapped_column(String(30), nullable=True)
    daily_calorie_target: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    daily_sugar_target_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # DB default 'DEFAULT'; becomes 'USER' once someone submits a target directly
    # (see health_profile_store.upsert_health_profile). 'CALCULATED' is reserved
    # for a future formula-based target — not implemented here.
    target_source: Mapped[str] = mapped_column(String(20), server_default="DEFAULT")
    health_data_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
