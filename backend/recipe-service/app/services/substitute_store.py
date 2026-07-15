from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_ingredient_product import RecipeIngredientProduct


async def get_substitutes_for_recipe(
    db: AsyncSession, recipe_id: int
) -> list[tuple[RecipeIngredient, list[tuple[RecipeIngredientProduct, Product]]]]:
    """저당/저칼로리 대체 상품 추천 (RC-0109). recipe_ingredient_products는
    데이터팀의 pgvector 매칭 워커가 채워둔 결과를 그대로 읽기만 한다 — 이
    서비스가 실시간으로 유사도를 계산하지 않는다."""
    ingredient_stmt = (
        select(RecipeIngredient)
        .where(RecipeIngredient.recipe_id == recipe_id, RecipeIngredient.ingredient_type == "substituted")
        .order_by(RecipeIngredient.id)
    )
    ingredients = (await db.execute(ingredient_stmt)).scalars().all()
    if not ingredients:
        return []

    ingredient_ids = [ingredient.id for ingredient in ingredients]
    match_stmt = (
        select(RecipeIngredientProduct, Product)
        .join(Product, Product.product_id == RecipeIngredientProduct.product_id)
        .where(RecipeIngredientProduct.recipe_ingredient_id.in_(ingredient_ids))
        .order_by(RecipeIngredientProduct.is_primary.desc(), RecipeIngredientProduct.match_score.desc())
    )
    matches = (await db.execute(match_stmt)).all()

    matches_by_ingredient: dict[int, list[tuple[RecipeIngredientProduct, Product]]] = {}
    for match, product in matches:
        matches_by_ingredient.setdefault(match.recipe_ingredient_id, []).append((match, product))

    return [(ingredient, matches_by_ingredient.get(ingredient.id, [])) for ingredient in ingredients]
