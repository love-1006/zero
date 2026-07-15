from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecipeIngredient(Base):
    """읽기 전용 — 데이터팀 파이프라인 소유."""

    __tablename__ = "recipe_ingredients"
    __table_args__ = {"schema": "service"}

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("service.recipes.id"))
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # 'common' | 'substituted' — substituted만 recipe_base_comparisons/
    # recipe_ingredient_products에 대응 행이 있을 수 있다.
    ingredient_type: Mapped[str] = mapped_column(String(20))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
