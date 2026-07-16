from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RawIngredientNutrient(Base):
    """읽기 전용 — 농진청/수산과학원 공공데이터, 데이터팀이 정제/적재."""

    __tablename__ = "raw_ingredient_nutrients"
    __table_args__ = {"schema": "service"}

    food_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    basis_unit: Mapped[str] = mapped_column(String(20))
    per100_sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    per100_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    per100_carb_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    per100_protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    per100_fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    source: Mapped[str] = mapped_column(String(20))
