from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Role, User
from accounts.permissions import IsManagerOrOperations
from .models import Customer
from .serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["customer_id", "full_name", "phone"]

    def get_queryset(self):
        qs = Customer.objects.select_related("branch", "assigned_agent").all()
        user = self.request.user
        if user.role == Role.COLLECTION_AGENT:
            return qs.filter(assigned_agent=user, is_active=True)
        if user.role in {Role.ADMIN, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR} or user.is_superuser:
            return qs
        return qs.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsManagerOrOperations()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        agent = serializer.validated_data.get("assigned_agent")
        if agent and agent.role != Role.COLLECTION_AGENT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"assigned_agent": "Select a collection agent account."})
        serializer.save()

    def perform_update(self, serializer):
        agent = serializer.validated_data.get("assigned_agent", getattr(serializer.instance, "assigned_agent", None))
        if agent and agent.role != Role.COLLECTION_AGENT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"assigned_agent": "Select a collection agent account."})
        serializer.save()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def collection_agents(request):
    if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR} and not request.user.is_superuser:
        return Response({"detail": "Only managers and operations can view agent choices."}, status=403)
    agents = User.objects.filter(role=Role.COLLECTION_AGENT, is_active=True).order_by("username")
    return Response([{"id": user.id, "username": user.username, "name": user.get_full_name() or user.username, "branch_id": getattr(user, "branch_id", None)} for user in agents])
