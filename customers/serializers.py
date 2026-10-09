from decimal import Decimal
from rest_framework import serializers
from .models import Customer
from django.utils import timezone

class CustomerSerializer(serializers.ModelSerializer):
    outstanding_amount = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    assigned_agent_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ["id", "customer_id", "full_name", "phone", "email", "address", "branch", "branch_name", "assigned_agent", "assigned_agent_name", "is_active", "outstanding_amount", "created_at", "updated_at"]
        read_only_fields = ["id", "customer_id", "created_at", "updated_at", "outstanding_amount", "branch_name", "assigned_agent_name"]

    def create(self, validated_data):
        # Generate a readable unique customer ID on the server to prevent manual-entry mistakes.
        today = timezone.localdate()
        prefix = f"CUS-{today:%Y%m%d}-"
        last_customer = Customer.objects.filter(customer_id__startswith=prefix).order_by("-customer_id").first()
        sequence = 1
        if last_customer:
            try:
                sequence = int(last_customer.customer_id.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                sequence = Customer.objects.filter(customer_id__startswith=prefix).count() + 1
        validated_data["customer_id"] = f"{prefix}{sequence:04d}"
        return super().create(validated_data)

    def get_outstanding_amount(self, obj):
        from loans.models import Loan
        return sum(Loan.objects.filter(customer=obj, status__in=["ACTIVE", "OVERDUE"]).values_list("outstanding_amount", flat=True), Decimal("0.00"))

    def get_assigned_agent_name(self, obj):
        return obj.assigned_agent.get_full_name() or obj.assigned_agent.username if obj.assigned_agent else None
