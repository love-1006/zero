import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductRef(Base):
    """Product Service 소유 — service.products. 읽기 전용 스냅샷 복사용."""

    __tablename__ = "products"
    __table_args__ = {"schema": "service"}

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200))
    brand_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sugars: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    carbohydrate: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    protein: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    fat: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sodium: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_status: Mapped[str] = mapped_column(String(20))
