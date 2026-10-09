import calendar
from datetime import date
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Loan, RepaymentSchedule, LoanStatus
from .serializers import LoanSerializer, RepaymentScheduleSerializer
from accounts.permissions import IsManagerOrOperations
from accounts.models import Role

def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.select_related("customer", "branch", "approved_by").all()
    serializer_class = LoanSerializer
    permission_classes = [IsManagerOrOperations]
    filter_backends = [filters.SearchFilter]
    search_fields = ["loan_id", "customer__full_name", "customer__customer_id"]

    def perform_create(self, serializer):
        if self.request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER} and not self.request.user.is_superuser:
            raise PermissionDenied("Only an admin or branch manager can create loan applications.")
        serializer.save(status=LoanStatus.PENDING_APPROVAL)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if request.user.role != Role.ADMIN and not request.user.is_superuser:
            raise PermissionDenied("Only an admin can approve loan applications.")
        with transaction.atomic():
            loan = self.get_object()
            if loan.status != LoanStatus.PENDING_APPROVAL:
                return Response({"detail": "Only pending loan applications can be approved."}, status=status.HTTP_400_BAD_REQUEST)
            if not loan.maturity_date:
                return Response({"detail": "Set a maturity date before approving this loan."}, status=status.HTTP_400_BAD_REQUEST)
            months = (loan.maturity_date.year - loan.start_date.year) * 12 + loan.maturity_date.month - loan.start_date.month + 1
            if months < 1 or months > 600:
                return Response({"detail": "Invalid repayment period."}, status=status.HTTP_400_BAD_REQUEST)
            for i in range(months):
                due = add_months(loan.start_date, i)
                RepaymentSchedule.objects.get_or_create(loan=loan, installment_number=i + 1, defaults={"due_date": due, "expected_amount": loan.monthly_due})
            loan.status = LoanStatus.ACTIVE
            loan.approved_by = request.user
            loan.approved_at = timezone.now()
            loan.rejection_reason = ""
            loan.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason"])
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if request.user.role != Role.ADMIN and not request.user.is_superuser:
            raise PermissionDenied("Only an admin can reject loan applications.")
        loan = self.get_object()
        if loan.status != LoanStatus.PENDING_APPROVAL:
            return Response({"detail": "Only pending loan applications can be rejected."}, status=400)
        loan.status = "REJECTED"
        loan.rejection_reason = str(request.data.get("reason", "Loan application rejected"))[:2000]
        loan.approved_by = request.user
        loan.approved_at = timezone.now()
        loan.save(update_fields=["status", "rejection_reason", "approved_by", "approved_at"])
        return Response(self.get_serializer(loan).data)

class RepaymentScheduleViewSet(viewsets.ModelViewSet):
    queryset = RepaymentSchedule.objects.select_related("loan", "loan__customer").all()
    serializer_class = RepaymentScheduleSerializer
    permission_classes = [IsManagerOrOperations]
    filterset_fields = ["loan", "status"]



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def collection_tasks(request):
    """
    Return repayment schedules that need collection follow-up.
    Agents only see schedules for customers assigned to them.
    Admins and branch managers can review schedules across their permitted scope.
    """
    today = timezone.localdate()
    queryset = RepaymentSchedule.objects.select_related(
        "loan", "loan__customer", "loan__branch"
    ).filter(
        status__in=[
            RepaymentSchedule.Status.PENDING,
            RepaymentSchedule.Status.PARTIAL,
            RepaymentSchedule.Status.OVERDUE,
        ],
        due_date__lte=today,
        loan__status=LoanStatus.ACTIVE,
    )

    user = request.user
    if user.role == Role.COLLECTION_AGENT:
        queryset = queryset.filter(loan__customer__assigned_agent=user)
    elif user.role == Role.BRANCH_MANAGER:
        if getattr(user, "branch_id", None):
            queryset = queryset.filter(loan__branch_id=user.branch_id)
    elif user.role not in {Role.ADMIN, Role.BRANCH_OPERATOR} and not user.is_superuser:
        raise PermissionDenied("You do not have permission to view collection tasks.")

    serializer = RepaymentScheduleSerializer(queryset.order_by("due_date"), many=True)
    return Response(serializer.data)
