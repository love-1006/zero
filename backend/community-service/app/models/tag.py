import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tag(Base):
    """Ingredients Service owns this table — community-service only reads it
    (tag_type='SWEETENER') for CM-0107/0108 감미료 정보. Never created/migrated
    here (see app/main.py: only the `community` schema's own tables are
    create_all()'d)."""

    __tablename__ = "tags"
    __table_args__ = {"schema": "service"}

    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tag_type: Mapped[str] = mapped_column(String(20))
    tag_code: Mapped[str] = mapped_column(String(50))
    tag_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    caution_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
