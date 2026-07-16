from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_tag import ProductTag
from app.models.user_preference import UserPreference

_RECOMMEND_LIMIT = 20


async def get_recommended_products(db: AsyncSession, user_id: int) -> list[Product]:
    tag_stmt = select(UserPreference.tag_id).where(
        UserPreference.user_id == user_id, UserPreference.preference_type == "INTEREST_CATEGORY"
    )
    tag_ids = [row[0] for row in (await db.execute(tag_stmt)).all()]

    # publish_status/created_at 컬럼이 데이터팀 재설계로 삭제돼(2026-07-16)
    # "active만/최신순" 필터링이 더 이상 불가능 — 이름순으로 대체.
    if tag_ids:
        stmt = (
            select(Product)
            .join(ProductTag, ProductTag.product_id == Product.product_id)
            .where(ProductTag.tag_id.in_(tag_ids))
            .distinct()
            .order_by(Product.product_name)
            .limit(_RECOMMEND_LIMIT)
        )
    else:
        # No INTEREST_CATEGORY preferences set yet — fall back to a plain list.
        stmt = (
            select(Product)
            .order_by(Product.product_name)
            .limit(_RECOMMEND_LIMIT)
        )

    return list((await db.execute(stmt)).scalars().all())
