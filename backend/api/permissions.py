from rest_framework import permissions


class ReadOrAuthorOnly(permissions.BasePermission):
    """
    Безопасные запросы для анонимного пользователя.
    Или все запросы только для админа и суперпользователя.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author == request.user
