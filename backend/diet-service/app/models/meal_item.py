import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealItem(Base):
    """Diet Service 소유 — service.meal_items.

    이력 스냅샷 설계:
    - item_name / calories / sugars / carbohydrate 는 추가 당시 products 값 복제 저장
    - product_id 는 원본 링크용 (ON DELETE SET NULL)
    - product_id 와 external_recipe_id 는 동시에 채워질 수 없음 (CHECK 제약, DB 수준)
    """

    __tablename__ = "meal_items"
    __table_args__ = {"schema": "service"}

    meal_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # FK → meal_logs
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # FK → products (SET NULL)
    external_recipe_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Recipe Service soft-ref

    # 스냅샷 컬럼
    item_name: Mapped[str] = mapped_column(String(200))
    calories: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sugars: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    carbohydrate: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    protein: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    fat: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sodium: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # AI 분석 결과 원문 (Vision/OCR 분석 응답 JSON 저장용)
    raw_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
