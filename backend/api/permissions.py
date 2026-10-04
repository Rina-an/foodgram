from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """
    Класс для доступа к изменениям только автору, просмотр доступен всем.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsCurrentUserOrAdminOrReadOnly(BasePermission):
    """
    Класс для доступа к изменению профиля только владельцу или админу.

    Просмотр профилей доступен всем.
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj == request.user
            or request.user.is_staff
        )
