from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Branch, BankAccount
from .serializers import BranchSerializer, BankAccountSerializer
from accounts.permissions import IsManagerOrOperations

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsManagerOrOperations]

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.filter(is_active=True)
    serializer_class = BankAccountSerializer
    permission_classes = [IsManagerOrOperations]


from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "service": "cmrs-api"})
<<<<<<< HEAD
import os
from django.core.management import call_command
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(["POST"])
@permission_classes([AllowAny])
def seed_demo_data(request):
    expected_key = os.environ.get("SEED_API_KEY")
    provided_key = request.headers.get("X-Seed-Key")

    if not expected_key or provided_key != expected_key:
        return Response(
            {"detail": "Unauthorized"},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        call_command("seed_demo")
        return Response(
            {"detail": "Demo data created or updated successfully."},
            status=status.HTTP_200_OK,
        )
    except Exception:
        return Response(
            {"detail": "Seeding failed. Check the Render logs."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
=======
>>>>>>> 120e1d9eee648063b7d1519a57ed6c21f971a6a0
