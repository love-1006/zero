from app.models.product import Product
from app.models.raw_ingredient_nutrient import RawIngredientNutrient
from app.models.recipe import Recipe
from app.models.recipe_base_comparison import RecipeBaseComparison
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_ingredient_product import RecipeIngredientProduct

__all__ = [
    "Product",
    "RawIngredientNutrient",
    "Recipe",
    "RecipeBaseComparison",
    "RecipeIngredient",
    "RecipeIngredientProduct",
]

# This service owns none of these tables — everything here is read-only data
# from the data team's recipe pipeline (or, for Product, the Product Service).
# No create_all() anywhere in this app; this list exists only so importing
# app.models registers every mapped class before first query.
