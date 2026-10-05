from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        )
from rest_framework.response import Response

from api.permissions import IsCurrentUserOrAdminOrReadOnly
from api.serializers import (AvatarSerializer,
                             SubscriptionSerializer,
                             UserWithRecipesSerializer,
                             )

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """
    Вьюсет для пользователей на основе Djoser.

    Добавляет аватар, подписки и список подписок.
    """

    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsCurrentUserOrAdminOrReadOnly,
                          )

    def get_permissions(self):
        """Метод закрывает эндпоинт me для анонимных пользователей."""
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=False,
            methods=('put',),
            url_path='me/avatar',
            permission_classes=(IsAuthenticated,)
            )
    def avatar(self, request):
        """Метод добавляет или заменяет аватар текущего пользователя."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Метод удаляет аватар текущего пользователя."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,)
            )
    def subscriptions(self, request):
        """Метод возвращает авторов, на которых подписан пользователь."""
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,)
            )
    def subscribe(self, request, id=None):
        """Метод оформляет подписку на автора."""
        author = get_object_or_404(User, pk=id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Метод отменяет подписку на автора."""
        author = get_object_or_404(User, pk=id)
        deleted, _ = request.user.subscriptions.filter(
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
