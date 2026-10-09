from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from loans.models import Loan, RepaymentSchedule
from cashcollections.models import Repayment, AgentCashSubmission
from reconciliation.models import Reconciliation
from deposits.models import BankDeposit, Settlement

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    today = timezone.localdate()

    expected = RepaymentSchedule.objects.filter(
        due_date=today
    ).aggregate(total=Sum("expected_amount"))["total"] or Decimal("0.00")

    collected = Repayment.objects.filter(
        collection_date=today
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    agent_held = AgentCashSubmission.objects.filter(
        submission_date=today,
        status="PENDING"
    ).aggregate(total=Sum("received_amount"))["total"] or Decimal("0.00")

    branch_received = AgentCashSubmission.objects.filter(
        submission_date=today,
        status="APPROVED"
    ).aggregate(total=Sum("received_amount"))["total"] or Decimal("0.00")

    deposits = BankDeposit.objects.filter(
        deposit_date=today
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    settled = Settlement.objects.filter(
        deposit__deposit_date=today,
        status="SETTLED"
    ).aggregate(total=Sum("settled_amount"))["total"] or Decimal("0.00")

    discrepancies = Reconciliation.objects.filter(
        status="PENDING"
    ).exclude(difference=Decimal("0.00")).count()

    outstanding = Loan.objects.filter(
        status__in=["ACTIVE", "OVERDUE"]
    ).aggregate(total=Sum("outstanding_amount"))["total"] or Decimal("0.00")

    return Response({
        "date": today,
        "expected_collections": expected,
        "total_collected": collected,
        "collection_rate": round(float((collected / expected) * 100), 2) if expected else 0,
        "cash_held_by_agents": agent_held,
        "cash_received_at_branch": branch_received,
        "bank_deposits": deposits,
        "settled_amount": settled,
        "outstanding_loan_amount": outstanding,
        "reconciliation_discrepancies": discrepancies,
        "lifecycle": {
            "expected": expected,
            "collected": collected,
            "branch_received": branch_received,
            "bank_deposited": deposits,
            "settled": settled,
        },
    })
