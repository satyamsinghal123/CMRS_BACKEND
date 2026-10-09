from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role
from .models import Repayment, AgentCashSubmission, CollectionAttempt
from .serializers import (
    RepaymentSerializer,
    AgentCashSubmissionSerializer,
    CollectionAttemptSerializer,
)
from .permissions import CollectionPermission


class RepaymentViewSet(viewsets.ModelViewSet):
    serializer_class = RepaymentSerializer
    permission_classes = [CollectionPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["receipt_number", "customer__full_name", "loan__loan_id"]
    ordering_fields = ["collection_date", "amount", "created_at"]

    def get_queryset(self):
        queryset = Repayment.objects.select_related(
            "customer", "loan", "agent", "branch", "schedule"
        ).all()

        if self.request.user.role == Role.COLLECTION_AGENT:
            return queryset.filter(agent=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save()


class CollectionAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionAttemptSerializer
    permission_classes = [CollectionPermission]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = CollectionAttempt.objects.select_related(
            "schedule",
            "schedule__loan",
            "schedule__loan__customer",
            "agent",
        )

        if self.request.user.role == Role.COLLECTION_AGENT:
            return queryset.filter(agent=self.request.user)

        return queryset


class AgentCashSubmissionViewSet(viewsets.ModelViewSet):
    queryset = AgentCashSubmission.objects.select_related(
        "agent", "branch", "reviewed_by"
    ).all()
    serializer_class = AgentCashSubmissionSerializer
    permission_classes = [CollectionPermission]
    filterset_fields = ["branch", "agent", "status", "submission_date"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.role == Role.COLLECTION_AGENT:
            return queryset.filter(agent=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)

    
    @action(detail=False, methods=["post"], url_path="submit-cash")
    def submit_cash(self, request):
        if request.user.role != Role.COLLECTION_AGENT:
            return Response(
                {"detail": "Only collection agents can submit collected cash."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from reconciliation.models import Reconciliation

        with transaction.atomic():
            # Lock actual repayment rows using a simple query.
            locked_payments = list(
                Repayment.objects.select_for_update()
                .filter(
                    agent=request.user,
                    status=Repayment.Status.COLLECTED,
                )
                .order_by("id")
            )

            if not locked_payments:
                return Response(
                    {"detail": "There are no unsubmitted collections to submit."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Group the already-locked rows in Python.
            branch_totals = {}
            for payment in locked_payments:
                branch_totals[payment.branch_id] = (
                    branch_totals.get(payment.branch_id, Decimal("0.00"))
                    + payment.amount
                )

            today = timezone.localdate()
            created_submissions = []

            for branch_id, total in sorted(branch_totals.items()):
                if total <= Decimal("0.00"):
                    continue

                # Lock-free count; generate a unique number for this submission.
                submission_count = (
                    AgentCashSubmission.objects.filter(
                        submission_date=today
                    ).count()
                    + 1
                )

                submission = AgentCashSubmission.objects.create(
                    submission_number=(
                        f"SUB-{today:%Y%m%d}-{submission_count:03d}"
                    ),
                    agent=request.user,
                    branch_id=branch_id,
                    submission_date=today,
                    expected_amount=total,
                    received_amount=total,
                    notes="Agent submitted collected cash for branch reconciliation.",
                )

                Reconciliation.objects.create(
                    submission=submission,
                    branch_id=branch_id,
                    expected_amount=total,
                    received_amount=Decimal("0.00"),
                    manager_notes=(
                        "Awaiting branch confirmation of physical cash received."
                    ),
                )

                # Update only the payments included in this branch's submission.
                payment_ids = [
                    payment.id
                    for payment in locked_payments
                    if payment.branch_id == branch_id
                ]

                Repayment.objects.filter(
                    id__in=payment_ids,
                    status=Repayment.Status.COLLECTED,
                ).update(status=Repayment.Status.SUBMITTED)

                created_submissions.append(
                    AgentCashSubmissionSerializer(submission).data
                )

        return Response(
            {
                "detail": "Collected cash submitted successfully.",
                "submissions": created_submissions,
                "count": len(created_submissions),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER}:
            return Response(
                {"detail": "Only branch managers can approve submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = self.get_object()

        if submission.status != AgentCashSubmission.Status.PENDING:
            return Response(
                {"detail": "Only pending submissions can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.status = AgentCashSubmission.Status.APPROVED
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save(
            update_fields=["status", "reviewed_by", "reviewed_at"]
        )

        return Response(AgentCashSubmissionSerializer(submission).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER}:
            return Response(
                {"detail": "Only branch managers can reject submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = self.get_object()

        if submission.status != AgentCashSubmission.Status.PENDING:
            return Response(
                {"detail": "Only pending submissions can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.status = AgentCashSubmission.Status.REJECTED
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.notes = request.data.get("notes", submission.notes)
        submission.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "notes",
            ]
        )

        return Response(AgentCashSubmissionSerializer(submission).data)