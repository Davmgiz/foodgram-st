from django.shortcuts import redirect
from core.models import Recipe
from django.http import Http404


def recipe_redirect(request, recipe_id):
    """Редиректит на страницу рецепта по короткому ID."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f"Рецепта с ID={recipe_id} не существует")

    return redirect(f'/recipes/{recipe_id}')
