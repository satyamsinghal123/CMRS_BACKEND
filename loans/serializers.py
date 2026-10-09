from rest_framework import serializers
from .models import Loan, RepaymentSchedule
from django.utils import timezone

class LoanSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_code = serializers.CharField(source="customer.customer_id", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "loan_id", "customer", "customer_name", "customer_code", "branch", "branch_name", "principal_amount", "outstanding_amount", "monthly_due", "interest_rate", "start_date", "maturity_date", "status", "created_at"]
        read_only_fields = ["id", "loan_id", "created_at"]

    def create(self, validated_data):
        # Generate a unique loan ID on the server instead of requiring manual entry.
        today = timezone.localdate()
        prefix = f"LN-{today:%Y%m%d}-"
        last_loan = Loan.objects.filter(loan_id__startswith=prefix).order_by("-loan_id").first()
        sequence = 1
        if last_loan:
            try:
                sequence = int(last_loan.loan_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                sequence = Loan.objects.filter(loan_id__startswith=prefix).count() + 1
        validated_data["loan_id"] = f"{prefix}{sequence:04d}"
        return super().create(validated_data)


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    loan_code = serializers.CharField(source="loan.loan_id", read_only=True)
    customer_id = serializers.CharField(source="loan.customer.customer_id", read_only=True)
    customer_name = serializers.CharField(source="loan.customer.full_name", read_only=True)
    customer_phone = serializers.CharField(source="loan.customer.phone", read_only=True)
    assigned_agent = serializers.IntegerField(source="loan.customer.assigned_agent_id", read_only=True)
    
    customer_pk = serializers.IntegerField(
    source="loan.customer.pk",
    read_only=True
    )
    loan_pk = serializers.IntegerField(
        source="loan.pk",
        read_only=True
    )
    schedule_pk = serializers.IntegerField(
        source="pk",
        read_only=True
    )
    customer_name = serializers.CharField(
        source="loan.customer.full_name",
        read_only=True
    )
    customer_code = serializers.CharField(
        source="loan.customer.customer_id",
        read_only=True
    )
    customer_phone = serializers.CharField(
        source="loan.customer.phone",
        read_only=True
    )
    loan_code = serializers.CharField(
        source="loan.loan_id",
        read_only=True
    )

    class Meta:
        model = RepaymentSchedule
        fields = "__all__"  