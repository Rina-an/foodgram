from datetime import date

from django.db.models import Sum

from recipes.models import RecipeIngredient


def generate_shopping_list(user):
    """
    Формирует текст списка покупок пользователя.

    Одинаковые ингредиенты из разных рецептов суммируются.
    """
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shopping_carts__user=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes = user.shopping_carts.select_related('recipe').values_list(
        'recipe__name',
        flat=True
    )
    lines = [
        f'Список покупок от {date.today():%d.%m.%Y}',
        '',
        'Продукты:',
    ]
    lines.extend(
        f'{number}. {item["ingredient__name"].capitalize()} '
        f'({item["ingredient__measurement_unit"]}) — '
        f'{item["total_amount"]}'
        for number, item in enumerate(ingredients, start=1)
    )
    lines.extend(['', 'Для рецептов:'])
    lines.extend(f'- {name}' for name in recipes)
    return '\n'.join(lines)
