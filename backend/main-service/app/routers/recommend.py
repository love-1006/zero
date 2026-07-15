from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.services.recommend_store import get_recommended_products

router = APIRouter(prefix="/home")


@router.get("/user-recommend")
async def get_user_recommendations(usr: str, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    user = get_current_user_from_token(usr)
    products = await get_recommended_products(db, user.user_id)

    return {
        "listProducts": [
            {
                "name": product.product_name,
                "brand": product.brand_name,
                "image": product.image_url,
                "url": product.purchase_url,
            }
            for product in products
        ]
    }
