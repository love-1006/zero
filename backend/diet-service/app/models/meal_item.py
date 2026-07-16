import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealItem(Base):
    """Diet Service 소유 — service.meal_items.

    이력 스냅샷 설계:
    - item_name / calories / sugars / carbohydrate 는 추가 당시 products 값 복제 저장
    - product_id 는 원본 링크용 (ON DELETE SET NULL)
    - product_id 와 external_recipe_id 는 동시에 채워질 수 없음 (CHECK 제약, DB 수준)

    실제 DB에는 protein/fat/sodium/raw_analysis 컬럼이 없다 — 원래 모델에
    있었는데, 이 서비스는 이 테이블에 DDL을 하지 않으므로(OWNED_TABLES라도
    이미 존재하는 실제 컬럼과 안 맞으면 그대로 에러가 난다) 실제 스키마에
    맞춰 제거했다. serving_value/serving_unit은 반대로 실제 DB엔 NOT NULL로
    있는데 이 모델엔 없었어서 추가했다.
    """

    __tablename__ = "meal_items"
    __table_args__ = {"schema": "service"}

    meal_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # FK → meal_logs
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # FK → products (SET NULL)
    external_recipe_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Recipe Service soft-ref

    # 스냅샷 컬럼
    item_name: Mapped[str] = mapped_column(String(200))
    serving_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    serving_unit: Mapped[str] = mapped_column(String(20))
    calories: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sugars: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbohydrate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
