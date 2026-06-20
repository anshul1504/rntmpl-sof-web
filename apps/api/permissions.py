from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedReadOnly(BasePermission):
    """Allow authenticated users to read current operational API resources."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and bool(request.user and request.user.is_authenticated)
