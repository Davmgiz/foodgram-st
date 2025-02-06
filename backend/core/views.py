from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from core.models import Recipe


def recipe_redirect(request, recipe_id):
    """Редиректит на страницу рецепта по короткому ID."""
    exists = Recipe.objects.filter(id=recipe_id).exists()
    if not exists:
        return HttpResponseRedirect('/404/')

    return redirect(f'/recipes/{recipe_id}')
