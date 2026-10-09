from rest_framework.permissions import BasePermission
from accounts.models import Role

class CollectionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if view.action in ["create"]:
            return request.user.role in {Role.ADMIN, Role.COLLECTION_AGENT}
        return request.user.role in {
            Role.ADMIN, Role.COLLECTION_AGENT, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR
        }
