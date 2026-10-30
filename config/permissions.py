from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthenticatedUnlessDebug(BasePermission):
    def has_permission(self, request, view):
        return settings.DEBUG or bool(request.user and request.user.is_authenticated)