

from rest_framework.permissions import  BasePermission


class IsManager(BasePermission):
    """
    Check if user belongs to the Manager Group
    """
    def has_permission(self, request, view):
        user = request.user
        if not user:
            return False
        return user.groups.filter(name='Manager').exists() or user.is_superuser

class IsNotCustomer(BasePermission):
    """
    Check if user is not a customer
    """
    def has_permission(self, request, view):
        user = request.user
        if not user:
            return False
        if user.is_superuser:
            return True
        return user.groups.count() > 0

