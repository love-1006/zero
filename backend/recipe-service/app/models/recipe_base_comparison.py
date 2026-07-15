from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecipeBaseComparison(Base):
    """읽기 전용 — 데이터팀 파이프라인 소유. base_type='product'인 경우
    base_product_id는 실제 FK가 없다(base_products 테이블이 아직 없음) —
    억지로 조인하지 않고 원시 값 그대로 노출한다."""

    __tablename__ = "recipe_base_comparisons"
    __table_args__ = {"schema": "service"}

    id: Mapped[int] = mapped_column(primary_key=True)
    substituted_ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("service.recipe_ingredients.id"), unique=True
    )
    base_type: Mapped[str] = mapped_column(String(20))  # 'raw_ingredient' | 'product'
    base_name: Mapped[str] = mapped_column(String(255))
    base_food_code: Mapped[str | None] = mapped_column(
        ForeignKey("service.raw_ingredient_nutrients.food_code"), nullable=True
    )
    base_product_id: Mapped[int | None] = mapped_column(nullable=True)  # FK 없음 — 의도된 느슨한 참조
    base_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    base_kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
