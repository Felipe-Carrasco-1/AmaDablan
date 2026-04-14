# tienda/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """Solo administradores pueden acceder."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'admin')


class IsAdminOrReadOnly(BasePermission):
    """Admins pueden todo; clientes y anónimos solo lectura."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'admin')