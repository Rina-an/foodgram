import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки картинки в Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, imgstr = data.split(';base64,')
                ext = header.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'{uuid.uuid4().hex}.{ext}'
                )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Некорректная картинка в формате Base64.'
                )
        return super().to_internal_value(data)
