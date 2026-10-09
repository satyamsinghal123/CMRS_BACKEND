from rest_framework.permissions import BasePermission
from .models import Role

class RolePermission(BasePermission):
    allowed_roles = set()

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.role in self.allowed_roles
        )

class IsAdmin(RolePermission):
    allowed_roles = {Role.ADMIN}

class IsBranchManager(RolePermission):
    allowed_roles = {Role.ADMIN, Role.BRANCH_MANAGER}

class IsAgent(RolePermission):
    allowed_roles = {Role.ADMIN, Role.COLLECTION_AGENT}

class IsOperations(RolePermission):
    allowed_roles = {Role.ADMIN, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR}

class IsManagerOrOperations(RolePermission):
    allowed_roles = {Role.ADMIN, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR}
