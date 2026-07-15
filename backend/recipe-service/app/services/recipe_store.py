from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.models.recipe_base_comparison import RecipeBaseComparison
from app.models.recipe_ingredient import RecipeIngredient


class RecipeNotFoundError(Exception):
    pass


async def list_recipes(db: AsyncSession) -> list[Recipe]:
    stmt = select(Recipe).order_by(Recipe.id.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_recipe(db: AsyncSession, recipe_id: int) -> Recipe:
    recipe = await db.get(Recipe, recipe_id)
    if recipe is None:
        raise RecipeNotFoundError("레시피를 찾을 수 없습니다.")
    return recipe


async def recipe_exists(db: AsyncSession, recipe_id: int) -> bool:
    return await db.get(Recipe, recipe_id) is not None


async def get_ingredients(db: AsyncSession, recipe_id: int) -> list[RecipeIngredient]:
    stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id).order_by(RecipeIngredient.id)
    return list((await db.execute(stmt)).scalars().all())


async def get_base_comparisons(db: AsyncSession, ingredient_ids: list[int]) -> dict[int, RecipeBaseComparison]:
    """substituted_ingredient_id -> RecipeBaseComparison, for whichever of the
    given ingredient ids actually have one (only 'substituted' ingredients do)."""
    if not ingredient_ids:
        return {}
    stmt = select(RecipeBaseComparison).where(RecipeBaseComparison.substituted_ingredient_id.in_(ingredient_ids))
    rows = (await db.execute(stmt)).scalars().all()
    return {row.substituted_ingredient_id: row for row in rows}
