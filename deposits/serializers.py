from rest_framework import serializers
from .models import BankDeposit, Settlement

class BankDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDeposit
        fields = "__all__"
        read_only_fields = ["id", "deposit_number", "created_by", "created_at", "status"]

    def validate(self, attrs):
        reconciliation = attrs["reconciliation"]
        if reconciliation.status != "APPROVED":
            raise serializers.ValidationError("Only approved reconciliation can be deposited.")
        return attrs

    def create(self, validated_data):
        from django.utils import timezone
        from .models import BankDeposit
        request = self.context["request"]
        today = validated_data.get("deposit_date", timezone.localdate())
        validated_data["created_by"] = request.user
        validated_data["deposit_number"] = f"DEP-{today:%Y%m%d}-{BankDeposit.objects.filter(deposit_date=today).count()+1:03d}"
        deposit = BankDeposit(**validated_data)
        deposit.full_clean()
        deposit.save()
        return deposit

class SettlementSerializer(serializers.ModelSerializer):
    difference = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Settlement
        fields = ["id", "deposit", "settled_amount", "settlement_date", "settlement_reference", "status", "notes", "difference", "updated_at"]
        read_only_fields = ["id", "status", "difference", "updated_at"]
