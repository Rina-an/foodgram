from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from recipes.constants import (MAX_AMOUNT,
                               MAX_COOKING_TIME,
                               MIN_AMOUNT,
                               MIN_COOKING_TIME,
                               )
from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            RecipeIngredient,
                            ShoppingCart,
                            Tag,
                            )
from users.models import Subscription

User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """
    Класс сериалайзера для пользователя.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, author):
        """Метод проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=author).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для аватара пользователя.
    """

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для тегов.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для чтения ингредиентов в рецепте.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """
    Класс сериалайзера для записи ингредиентов в рецепт.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT
    )


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для краткого представления рецепта.
    """

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для чтения рецептов.
    """

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def check_user_relation(self, recipe, model):
        """Метод проверяет связь текущего пользователя с рецептом."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        """Метод проверяет, находится ли рецепт в избранном."""
        return self.check_user_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        """Метод проверяет, находится ли рецепт в списке покупок."""
        return self.check_user_relation(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для создания и изменения рецептов.
    """

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_image(self, value):
        """Метод для проверки картинки на пустоту."""
        if not value:
            raise serializers.ValidationError(
                'Поле изображения не может быть пустым.'
            )
        return value

    def validate(self, data):
        """
        Метод проверяет ингредиенты и теги.

        Поля обязательны и при частичном обновлении,
        не могут быть пустыми и не должны повторяться.
        """
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужно указать хотя бы один ингредиент.'}
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужно указать хотя бы один тег.'}
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        return data

    def save_ingredients(self, recipe, ingredients):
        """Метод сохраняет ингредиенты рецепта с количеством."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients
        )

    def create(self, validated_data):
        """Метод создаёт рецепт вместе с тегами и ингредиентами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        with transaction.atomic():
            recipe = super().create(validated_data)
            recipe.tags.set(tags)
            self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        """Метод обновляет рецепт, заменяя теги и ингредиенты."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        with transaction.atomic():
            recipe.tags.set(tags)
            recipe.recipe_ingredients.all().delete()
            self.save_ingredients(recipe, ingredients)
            return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class UserRecipeSerializer(serializers.ModelSerializer):
    """
    Базовый класс сериалайзера для связи пользователя и рецепта.

    Используется для избранного и списка покупок.
    """

    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(UserRecipeSerializer):
    """
    Класс сериалайзера для избранного.
    """

    class Meta(UserRecipeSerializer.Meta):
        model = Favorite
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            ),
        )


class ShoppingCartSerializer(UserRecipeSerializer):
    """
    Класс сериалайзера для списка покупок.
    """

    class Meta(UserRecipeSerializer.Meta):
        model = ShoppingCart
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок.'
            ),
        )


class UserWithRecipesSerializer(UserSerializer):
    """
    Класс сериалайзера для автора с его рецептами.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, author):
        """Метод возвращает рецепты автора с учётом recipes_limit."""
        recipes = author.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Класс сериалайзера для оформления подписки.
    """

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя.'
            ),
        )

    def validate(self, data):
        """Метод для проверки самоподписки."""
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return data

    def to_representation(self, instance):
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context
        ).data
