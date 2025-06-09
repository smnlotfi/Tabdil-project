from rest_framework.permissions import BasePermission

class IsSellerUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_seller
# Then use it in your action:
