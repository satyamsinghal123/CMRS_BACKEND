from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BankDeposit, Settlement
from .serializers import BankDepositSerializer, SettlementSerializer
from accounts.models import Role
from accounts.permissions import IsManagerOrOperations

class BankDepositViewSet(viewsets.ModelViewSet):
    queryset = BankDeposit.objects.select_related("branch", "reconciliation", "bank_account", "created_by").all()
    serializer_class = BankDepositSerializer
    permission_classes = [IsManagerOrOperations]
    filterset_fields = ["branch", "status", "deposit_date"]

class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.select_related("deposit").all()
    serializer_class = SettlementSerializer
    permission_classes = [IsManagerOrOperations]
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"])
    def mark_settled(self, request, pk=None):
        if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER, Role.BRANCH_OPERATOR}:
            return Response({"detail": "You do not have permission."}, status=403)
        settlement = self.get_object()
        amount = request.data.get("settled_amount")
        reference = request.data.get("settlement_reference")
        if amount is None or not reference:
            return Response({"detail": "settled_amount and settlement_reference are required."}, status=400)
        settlement.settled_amount = amount
        settlement.settlement_reference = reference
        settlement.settlement_date = timezone.now()
        settlement.status = "SETTLED" if str(amount) == str(settlement.deposit.amount) else "MISMATCH"
        settlement.save()
        settlement.deposit.status = "SETTLED" if settlement.status == "SETTLED" else "MISMATCH"
        settlement.deposit.save(update_fields=["status"])
        return Response(self.get_serializer(settlement).data)
