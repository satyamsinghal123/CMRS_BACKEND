from rest_framework import serializers
from .models import Reconciliation

class ReconciliationSerializer(serializers.ModelSerializer):
    submission_number = serializers.CharField(source="submission.submission_number", read_only=True)
    agent_name = serializers.CharField(source="submission.agent.username", read_only=True)

    class Meta:
        model = Reconciliation
        fields = "__all__"
        read_only_fields = ["id", "submission", "branch", "expected_amount", "difference", "status", "reviewed_by", "reviewed_at", "locked_at", "created_at"]

    def validate_received_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Received amount cannot be negative.")
        if self.instance and self.instance.status != Reconciliation.Status.PENDING:
            raise serializers.ValidationError("Only pending reconciliations can be edited.")
        return value
