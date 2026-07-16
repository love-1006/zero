import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductTag(Base):
    """Product Service owns this table — main-service only reads it, to filter
    products by the tags a user is interested in (user_preferences.tag_id)."""

    __tablename__ = "product_tags"
    __table_args__ = {"schema": "service"}

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
