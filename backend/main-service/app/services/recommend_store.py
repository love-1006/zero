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

    if tag_ids:
        stmt = (
            select(Product)
            .join(ProductTag, ProductTag.product_id == Product.product_id)
            .where(Product.publish_status == "ACTIVE", ProductTag.tag_id.in_(tag_ids))
            .distinct()
            .order_by(Product.created_at.desc())
            .limit(_RECOMMEND_LIMIT)
        )
    else:
        # No INTEREST_CATEGORY preferences set yet — newest active products
        # instead of an empty list.
        stmt = (
            select(Product)
            .where(Product.publish_status == "ACTIVE")
            .order_by(Product.created_at.desc())
            .limit(_RECOMMEND_LIMIT)
        )

    return list((await db.execute(stmt)).scalars().all())
