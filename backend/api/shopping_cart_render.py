from django.utils.timezone import now
from core.models import RecipeIngredient, Recipe
from django.db.models import Sum
from io import BytesIO


def render_shopping_cart(user):
    """Генерирует текст для списка покупок пользователя."""

    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shopping_carts__user=user)  
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    recipes = Recipe.objects.filter(shopping_carts__user=user)

    shopping_cart_header = (
        f"Список покупок для {user.username}\n"
        f"Дата составления: {now().strftime('%d-%m-%Y %H:%M:%S')}\n"
    )

    ingredient_lines = [
        f"{idx}. {item['ingredient__name'].capitalize()} "
        f"({item['ingredient__measurement_unit']}) - {item['total_amount']}"
        for idx, item in enumerate(ingredients, start=1)
    ]

    recipe_lines = [
        f"- {recipe.name} (@{recipe.author.username})"
        for recipe in recipes
    ]

    shopping_cart_text = '\n'.join([
        shopping_cart_header,
        'Продукты:\n',
        *ingredient_lines,
        '\nРецепты, использующие эти продукты:\n',
        *recipe_lines,
    ])

    shopping_cart_file = BytesIO()
    shopping_cart_file.write(shopping_cart_text.encode('utf-8'))
    shopping_cart_file.seek(0)

    return shopping_cart_file
