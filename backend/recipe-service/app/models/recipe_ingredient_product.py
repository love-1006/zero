import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecipeIngredientProduct(Base):
    """읽기 전용 — 데이터팀의 pgvector 유사도 매칭 워커가 적재 (score>=0.7만
    행이 생성됨, 임계값은 워커 쿼리 조건이라 여기엔 없음)."""

    __tablename__ = "recipe_ingredient_products"
    __table_args__ = {"schema": "service"}

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_ingredient_id: Mapped[int] = mapped_column(ForeignKey("service.recipe_ingredients.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("service.products.product_id"))
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
