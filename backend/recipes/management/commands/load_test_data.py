import io
import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()

TAGS = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
)

USERS = (
    {
        'email': 'admin@foodgram.ru',
        'username': 'admin',
        'first_name': 'Админ',
        'last_name': 'Фудграмов',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'moderator@foodgram.ru',
        'username': 'moderator',
        'first_name': 'Мария',
        'last_name': 'Модераторова',
        'is_staff': True,
        'is_superuser': False,
    },
    {
        'email': 'ivan@foodgram.ru',
        'username': 'ivan',
        'first_name': 'Иван',
        'last_name': 'Петров',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'email': 'olga@foodgram.ru',
        'username': 'olga',
        'first_name': 'Ольга',
        'last_name': 'Смирнова',
        'is_staff': False,
        'is_superuser': False,
    },
)

RECIPES = (
    {
        'author': 'admin',
        'name': 'Сырники со сметаной',
        'text': 'Смешайте творог, яйцо и муку, сформируйте сырники '
                'и обжарьте на сливочном масле до золотистой корочки.',
        'cooking_time': 25,
        'tags': ('breakfast',),
        'ingredients': (('творог', 400), ('яйца куриные', 60),
                        ('мука', 60), ('сметана', 100)),
        'color': (244, 196, 120),
    },
    {
        'author': 'moderator',
        'name': 'Борщ',
        'text': 'Сварите бульон, добавьте свёклу, капусту, картофель '
                'и морковь. Подавайте со сметаной.',
        'cooking_time': 120,
        'tags': ('lunch',),
        'ingredients': (('свекла', 300), ('капуста белокочанная', 300),
                        ('картофель', 400), ('морковь', 150)),
        'color': (170, 40, 60),
    },
    {
        'author': 'ivan',
        'name': 'Паста с томатным соусом',
        'text': 'Отварите спагетти, обжарьте чеснок, добавьте томаты '
                'и потушите 10 минут. Смешайте с пастой.',
        'cooking_time': 30,
        'tags': ('lunch', 'dinner'),
        'ingredients': (('паста', 250), ('помидоры', 400),
                        ('чеснок', 10)),
        'color': (220, 80, 50),
    },
    {
        'author': 'olga',
        'name': 'Овсяная каша с ягодами',
        'text': 'Сварите овсяные хлопья на молоке, добавьте ягоды и мёд.',
        'cooking_time': 15,
        'tags': ('breakfast',),
        'ingredients': (('овсяные хлопья', 80), ('молоко', 250),
                        ('мед', 20)),
        'color': (120, 90, 160),
    },
    {
        'author': 'ivan',
        'name': 'Омлет с сыром',
        'text': 'Взбейте яйца с молоком, вылейте на сковороду, '
                'посыпьте тёртым сыром и готовьте под крышкой.',
        'cooking_time': 10,
        'tags': ('breakfast',),
        'ingredients': (('яйца куриные', 120), ('молоко', 50),
                        ('сыр', 40)),
        'color': (250, 220, 90),
    },
    {
        'author': 'ivan',
        'name': 'Гречка с грибами',
        'text': 'Обжарьте лук и шампиньоны, добавьте отваренную '
                'гречневую крупу и перемешайте.',
        'cooking_time': 35,
        'tags': ('lunch', 'dinner'),
        'ingredients': (('гречневая крупа', 200), ('шампиньоны', 250),
                        ('лук репчатый', 80)),
        'color': (140, 100, 60),
    },
    {
        'author': 'ivan',
        'name': 'Куриный суп',
        'text': 'Сварите бульон из курицы, добавьте картофель, морковь '
                'и лук, варите до готовности овощей.',
        'cooking_time': 60,
        'tags': ('lunch',),
        'ingredients': (('курица', 500), ('картофель', 300),
                        ('морковь', 100), ('лук репчатый', 80)),
        'color': (230, 180, 70),
    },
)


class Command(BaseCommand):
    """Наполняет базу тестовыми тегами, пользователями и рецептами."""

    @staticmethod
    def make_image(color):
        """Метод генерирует однотонную картинку для рецепта."""
        buffer = io.BytesIO()
        Image.new('RGB', (600, 400), color).save(buffer, format='PNG')
        return ContentFile(buffer.getvalue(), name='recipe.png')

    @staticmethod
    def find_ingredient(name):
        """Метод ищет ингредиент по началу названия."""
        return Ingredient.objects.filter(name__istartswith=name).first()

    def create_users(self, password):
        """Метод создаёт пользователей с разными уровнями доступа."""
        users = {}
        for data in USERS:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults=data
            )
            if created:
                user.set_password(password)
                user.save()
            users[user.username] = user
        return users

    def create_recipe(self, data, author):
        """Метод создаёт рецепт с тегами и ингредиентами."""
        if Recipe.objects.filter(author=author, name=data['name']).exists():
            return
        recipe = Recipe.objects.create(
            author=author,
            name=data['name'],
            text=data['text'],
            cooking_time=data['cooking_time'],
            image=self.make_image(data['color'])
        )
        recipe.tags.set(Tag.objects.filter(slug__in=data['tags']))
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )
            for ingredient, amount in (
                (self.find_ingredient(name), amount)
                for name, amount in data['ingredients']
            )
            if ingredient
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not Ingredient.objects.exists():
            call_command('load_ingredients')
        for name, slug in TAGS:
            Tag.objects.get_or_create(slug=slug, defaults={'name': name})
        password = os.getenv('TEST_USERS_PASSWORD', 'Foodgram2026!')
        users = self.create_users(password)
        for data in RECIPES:
            self.create_recipe(data, users[data['author']])
        self.stdout.write(self.style.SUCCESS(
            'Тестовые данные созданы. Пользователи: '
            + ', '.join(item['email'] for item in USERS)
        ))
