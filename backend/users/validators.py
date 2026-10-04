from django.core.exceptions import ValidationError

from users.constants import FORBIDDEN_USERNAME


def validate_username_not_me(value):
    """Запрещает использовать зарезервированное имя пользователя."""
    if value.lower() == FORBIDDEN_USERNAME:
        raise ValidationError(
            f'Имя пользователя «{FORBIDDEN_USERNAME}» использовать нельзя.'
        )
    return value
