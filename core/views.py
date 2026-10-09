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
