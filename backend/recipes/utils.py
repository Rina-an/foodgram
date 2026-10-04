from django.http import Http404

from recipes.constants import SHORT_LINK_BASE


def encode_short_link(recipe_id):
    """Кодирует id рецепта в короткий код для ссылки."""
    return format(recipe_id, 'x')


def decode_short_link(short_code):
    """Декодирует короткий код обратно в id рецепта."""
    try:
        return int(short_code, SHORT_LINK_BASE)
    except ValueError:
        raise Http404('Некорректная короткая ссылка.')
