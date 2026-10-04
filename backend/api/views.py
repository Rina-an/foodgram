from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import generics, status, viewsets
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        )
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarSerializer,
                             FavoriteSerializer,
                             IngredientSerializer,
                             RecipeReadSerializer,
                             RecipeWriteSerializer,
                             ShoppingCartSerializer,
                             SubscriptionSerializer,
                             TagSerializer,
                             UserWithRecipesSerializer,
                             )
from api.utils import generate_shopping_list
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.utils import encode_short_link

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """
    Вьюсет для пользователей на основе Djoser.
    """

    def get_permissions(self):
        """Метод закрывает эндпоинт me для анонимных пользователей."""
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()


class AvatarView(APIView):
    """
    Вью для добавления и удаления аватара текущего пользователя.
    """

    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """Метод добавляет или заменяет аватар."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        """Метод удаляет аватар."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(generics.ListAPIView):
    """
    Вью для списка авторов, на которых подписан пользователь.
    """

    serializer_class = UserWithRecipesSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Метод для получения авторов из подписок пользователя."""
        return User.objects.filter(subscribers__user=self.request.user)


class SubscribeView(APIView):
    """
    Вью для оформления и отмены подписки на автора.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, user_id):
        """Метод оформляет подписку на автора."""
        author = get_object_or_404(User, pk=user_id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        """Метод отменяет подписку на автора."""
        author = get_object_or_404(User, pk=user_id)
        deleted, _ = request.user.subscriptions.filter(
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class UserRecipeView(APIView):
    """
    Базовая вью для добавления рецепта в список пользователя и удаления.

    Наследники задают serializer_class и model.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = None
    model = None

    def post(self, request, recipe_id):
        """Метод добавляет рецепт в список пользователя."""
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        serializer = self.serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        """Метод удаляет рецепт из списка пользователя."""
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        deleted, _ = self.model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не был добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(UserRecipeView):
    """
    Вью для избранного.
    """

    serializer_class = FavoriteSerializer
    model = Favorite


class ShoppingCartView(UserRecipeView):
    """
    Вью для списка покупок.
    """

    serializer_class = ShoppingCartSerializer
    model = ShoppingCart


class DownloadShoppingCartView(APIView):
    """
    Вью для скачивания списка покупок текстовым файлом.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Метод отдаёт файл со списком покупок."""
        response = HttpResponse(
            generate_shopping_list(request.user),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class RecipeShortLinkView(APIView):
    """
    Вью для получения короткой ссылки на рецепт.
    """

    permission_classes = (AllowAny,)

    def get(self, request, recipe_id):
        """Метод возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        short_link = request.build_absolute_uri(
            reverse('recipes:short_link', args=(encode_short_link(recipe.pk),))
        )
        return Response({'short-link': short_link})
