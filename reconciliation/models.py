from decimal import Decimal
from django.db import models
from django.utils import timezone
from cashcollections.models import AgentCashSubmission
from accounts.models import User
from core.models import Branch

class Reconciliation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    submission = models.OneToOneField(AgentCashSubmission, on_delete=models.PROTECT, related_name="reconciliation")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="reconciliations")
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    received_amount = models.DecimalField(max_digits=14, decimal_places=2)
    difference = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discrepancy_reason = models.CharField(max_length=120, blank=True)
    manager_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="reconciliations_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.difference = self.received_amount - self.expected_amount
        super().save(*args, **kwargs)

    def lock(self, user):
        self.status = self.Status.APPROVED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.locked_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "locked_at"])
