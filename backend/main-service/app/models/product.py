import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    """Product Service owns this table — main-service only reads it, for
    home-screen recommendations/rankings/search.

    2026-07-16 데이터팀 재설계 반영 — publish_status/created_at 컬럼이 더 이상
    존재하지 않는다(실제 DB 재확인 완료).
    """

    __tablename__ = "products"
    __table_args__ = {"schema": "service"}

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255))
    brand_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    calories: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sugars: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    image_url: Mapped[str] = mapped_column(Text)
    purchase_url: Mapped[str | None] = mapped_column(Text, nullable=True)
