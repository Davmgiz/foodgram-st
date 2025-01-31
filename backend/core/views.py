from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from core.models import Recipe


def recipe_redirect(request, recipe_id):
    """Редиректит на страницу рецепта по короткому ID."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return HttpResponseRedirect(f'/recipes/{recipe.id}')
