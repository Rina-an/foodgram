from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe
from recipes.utils import decode_short_link


def short_link_redirect(request, short_code):
    """Перенаправляет с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, pk=decode_short_link(short_code))
    return redirect(f'/recipes/{recipe.pk}/')
