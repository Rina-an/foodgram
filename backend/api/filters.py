from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр ингредиентов по началу названия."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов по автору, тегам, избранному и списку покупок."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_user_relation(self, queryset, value, relation):
        """Оставляет рецепты, связанные с текущим пользователем."""
        user = self.request.user
        if not value or not user.is_authenticated:
            return queryset
        return queryset.filter(**{f'{relation}__user': user})

    def filter_is_favorited(self, queryset, name, value):
        """Метод для фильтрации рецептов из избранного."""
        return self.filter_user_relation(queryset, value, 'favorites')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод для фильтрации рецептов из списка покупок."""
        return self.filter_user_relation(queryset, value, 'shopping_carts')
