import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.constants import (DATA_DIR_NAME,
                               INGREDIENTS_FILE,
                               INGREDIENTS_PATHS,
                               )
from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из JSON или CSV файла."""

    help = (
        f'Загрузка ингредиентов из {DATA_DIR_NAME}/{INGREDIENTS_FILE} '
        '(или файла, указанного в --path, в формате JSON или CSV)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=Path,
            help='Путь к файлу ингредиентов (.json или .csv)'
        )

    def get_path(self, path):
        """Метод находит файл с ингредиентами."""
        if path:
            if not path.exists():
                raise CommandError(f'Файл {path} не найден.')
            return path
        for default_path in INGREDIENTS_PATHS:
            if default_path.exists():
                return default_path
        raise CommandError(
            f'Файл {INGREDIENTS_FILE} не найден, укажите --path.'
        )

    @staticmethod
    def read_rows(path):
        """Метод читает пары (название, единица измерения) из файла."""
        with open(path, encoding='utf-8') as file:
            if path.suffix == '.csv':
                return [tuple(row) for row in csv.reader(file) if row]
            return [
                (item['name'], item['measurement_unit'])
                for item in json.load(file)
            ]

    def handle(self, *args, **options):
        path = self.get_path(options['path'])
        Ingredient.objects.bulk_create(
            (
                Ingredient(name=name, measurement_unit=unit)
                for name, unit in self.read_rows(path)
            ),
            ignore_conflicts=True
        )
        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты загружены из {path.name}. '
            f'Всего в базе: {Ingredient.objects.count()}.'
        ))
