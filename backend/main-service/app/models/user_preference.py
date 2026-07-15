import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = {"schema": "service"}

    preference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    # FK to public.users(id) — enforced by the DB, not declared here (see
    # UserHealthProfile.user_id for why).
    user_id: Mapped[int] = mapped_column(Integer)
    # One of INTEREST_CATEGORY / ALLERGEN / CAUTION_INGREDIENT (DB CHECK
    # constraint ck_preferences_type). INTEREST_CATEGORY/ALLERGEN require
    # tag_id (and forbid custom_value); CAUTION_INGREDIENT is the reverse
    # (ck_preferences_type_value / ck_preferences_value) — enforced in
    # app/services/preference_store.py before insert, not just relied on
    # via the DB constraint, so callers get a clean 4xx instead of a raw
    # IntegrityError.
    preference_type: Mapped[str] = mapped_column(String(30))
    tag_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service.tags.tag_id"), nullable=True
    )
    custom_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
