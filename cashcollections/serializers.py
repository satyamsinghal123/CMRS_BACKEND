from rest_framework import serializers
from django.db import IntegrityError
from django.utils import timezone
from .models import Repayment, AgentCashSubmission
from loans.models import Loan, RepaymentSchedule
from reconciliation.models import Reconciliation
from .models import Repayment, AgentCashSubmission, CollectionAttempt

class RepaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    loan_code = serializers.CharField(source="loan.loan_id", read_only=True)

    class Meta:
        model = Repayment
        fields = "__all__"
        read_only_fields = [
            "id", "receipt_number", "agent", "branch", "status", "created_at",
            "payment_type", "expected_amount"
        ]

    def validate(self, attrs):
        request = self.context["request"]
        customer = attrs["customer"]
        loan = attrs["loan"]
        schedule = attrs.get("schedule")
        amount = attrs.get("amount")

        if loan.customer_id != customer.id:
            raise serializers.ValidationError("Selected loan does not belong to this customer.")
        if loan.status == "CLOSED":
            raise serializers.ValidationError("Cannot collect against a closed loan.")
        if not customer.is_active:
            raise serializers.ValidationError("Cannot collect from an inactive customer.")
        if amount is None or amount <= 0:
            raise serializers.ValidationError({"amount": "Payment amount must be greater than zero."})
        if request.user.role == "COLLECTION_AGENT" and customer.assigned_agent_id != request.user.id:
            raise serializers.ValidationError("You can only record payments for customers assigned to you.")
        if schedule:
            if schedule.loan_id != loan.id:
                raise serializers.ValidationError("The selected installment does not belong to this loan.")
            if schedule.status == RepaymentSchedule.Status.PAID or schedule.paid_amount >= schedule.expected_amount:
                raise serializers.ValidationError("This installment has already been paid.")
            expected = max(schedule.expected_amount - schedule.paid_amount, 0)
        else:
            expected = loan.monthly_due

        attrs["agent"] = request.user
        attrs["branch"] = loan.branch
        attrs["expected_amount"] = expected
        attrs["collection_date"] = attrs.get("collection_date") or timezone.localdate()
        if amount > expected:
            attrs["payment_type"] = Repayment.PaymentType.OVER_COLLECTION
        elif amount < expected:
            attrs["payment_type"] = Repayment.PaymentType.PARTIAL
        else:
            attrs["payment_type"] = Repayment.PaymentType.FULL
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from django.db.models import F
        from decimal import Decimal

        with transaction.atomic():
            schedule = validated_data.get("schedule")
            loan = Loan.objects.select_for_update().get(pk=validated_data["loan"].pk)
            if schedule:
                schedule = RepaymentSchedule.objects.select_for_update().get(pk=schedule.pk)
                remaining = max(schedule.expected_amount - schedule.paid_amount, Decimal("0.00"))
                if schedule.status == RepaymentSchedule.Status.PAID or remaining <= 0:
                    raise serializers.ValidationError({"schedule": "This installment has already been paid."})
                if validated_data["amount"] <= 0:
                    raise serializers.ValidationError({"amount": "Payment amount must be greater than zero."})
                validated_data["schedule"] = schedule
                validated_data["expected_amount"] = remaining
                if validated_data["amount"] > remaining:
                    validated_data["payment_type"] = Repayment.PaymentType.OVER_COLLECTION
                elif validated_data["amount"] < remaining:
                    validated_data["payment_type"] = Repayment.PaymentType.PARTIAL
                else:
                    validated_data["payment_type"] = Repayment.PaymentType.FULL

            today = validated_data.get("collection_date", timezone.localdate())
            receipt_number = f"RC-{today:%Y%m%d}-{Repayment.objects.select_for_update().filter(collection_date=today).count()+1:04d}"
            validated_data["receipt_number"] = receipt_number
            validated_data["loan"] = loan

            repayment = Repayment(**validated_data)
            repayment.full_clean()
            repayment.save()

            if schedule:
                schedule.paid_amount += repayment.amount
                if schedule.paid_amount >= schedule.expected_amount:
                    schedule.paid_amount = schedule.expected_amount
                    schedule.status = RepaymentSchedule.Status.PAID
                elif schedule.due_date < timezone.localdate():
                    schedule.status = RepaymentSchedule.Status.OVERDUE
                else:
                    schedule.status = RepaymentSchedule.Status.PARTIAL
                schedule.save(update_fields=["paid_amount", "status"])

            # This project treats recorded collections as repayments against the outstanding loan balance.
            loan.outstanding_amount = max(loan.outstanding_amount - repayment.amount, Decimal("0.00"))
            if loan.outstanding_amount <= 0:
                loan.outstanding_amount = Decimal("0.00")
                loan.status = "CLOSED"
            loan.save(update_fields=["outstanding_amount", "status"])
            return repayment

class AgentCashSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentCashSubmission
        fields = "__all__"
        read_only_fields = ["id", "submission_number", "discrepancy", "status", "reviewed_by", "reviewed_at", "created_at"]

    def create(self, validated_data):
        today = validated_data.get("submission_date", timezone.localdate())
        validated_data["submission_number"] = f"SUB-{today:%Y%m%d}-{AgentCashSubmission.objects.filter(submission_date=today).count()+1:03d}"
        from django.db import transaction
        with transaction.atomic():
            submission = AgentCashSubmission.objects.create(**validated_data)
            Reconciliation.objects.create(
                submission=submission,
                branch=submission.branch,
                expected_amount=submission.received_amount,
                received_amount=0,
                manager_notes="Awaiting branch confirmation of physical cash received.",
            )
            return submission


class CollectionAttemptSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="schedule.loan.customer.full_name",
        read_only=True
    )
    loan_code = serializers.CharField(
        source="schedule.loan.loan_id",
        read_only=True
    )

    class Meta:
        model = CollectionAttempt
        fields = "__all__"
        read_only_fields = ["id", "agent", "created_at"]

    def validate_schedule(self, schedule):
        request = self.context["request"]

        if request.user.role == "COLLECTION_AGENT":
            if schedule.loan.customer.assigned_agent_id != request.user.id:
                raise serializers.ValidationError(
                    "You can only record attempts for customers assigned to you."
                )

        return schedule

    def create(self, validated_data):
        validated_data["agent"] = self.context["request"].user
        return super().create(validated_data)
