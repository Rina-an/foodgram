from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        )
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FavoriteSerializer,
                             IngredientSerializer,
                             RecipeReadSerializer,
                             RecipeWriteSerializer,
                             ShoppingCartSerializer,
                             TagSerializer,
                             )
from api.utils import generate_shopping_list
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.utils import encode_short_link


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов с поиском по началу названия.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для рецептов.

    Также отвечает за избранное, список покупок и короткие ссылки.
    """

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_ingredients__ingredient'
    )
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        """Метод выбирает сериалайзер для чтения или записи."""
        if self.request.method in ('POST', 'PATCH'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        """Метод пишет авторство автоматически при создании рецепта."""
        serializer.save(author=self.request.user)

    def add_to_list(self, serializer_class, request, pk):
        """Метод добавляет рецепт в избранное или список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, model, request, pk):
        """Метод удаляет рецепт из избранного или списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не был добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,)
            )
    def favorite(self, request, pk=None):
        """Метод добавляет рецепт в избранное."""
        return self.add_to_list(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Метод удаляет рецепт из избранного."""
        return self.remove_from_list(Favorite, request, pk)

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,)
            )
    def shopping_cart(self, request, pk=None):
        """Метод добавляет рецепт в список покупок."""
        return self.add_to_list(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Метод удаляет рецепт из списка покупок."""
        return self.remove_from_list(ShoppingCart, request, pk)

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,)
            )
    def download_shopping_cart(self, request):
        """Метод отдаёт список покупок текстовым файлом."""
        response = HttpResponse(
            generate_shopping_list(request.user),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True,
            methods=('get',),
            url_path='get-link',
            permission_classes=(AllowAny,)
            )
    def get_link(self, request, pk=None):
        """Метод возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('recipes:short_link', args=(encode_short_link(recipe.pk),))
        )
        return Response({'short-link': short_link})
