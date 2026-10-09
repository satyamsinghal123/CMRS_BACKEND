from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from customers.models import Customer
from loans.models import Loan, RepaymentSchedule
from core.models import Branch
from accounts.models import User

class Repayment(models.Model):
    class PaymentType(models.TextChoices):
        FULL = "FULL", "Full"
        PARTIAL = "PARTIAL", "Partial"
        OVER_COLLECTION = "OVER_COLLECTION", "Over Collection"

    class Status(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"
        SUBMITTED = "SUBMITTED", "Submitted"
        RECONCILED = "RECONCILED", "Reconciled"
        REJECTED = "REJECTED", "Rejected"

    receipt_number = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="repayments")
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name="repayments")
    schedule = models.ForeignKey(RepaymentSchedule, null=True, blank=True, on_delete=models.PROTECT, related_name="repayments")
    agent = models.ForeignKey(User, on_delete=models.PROTECT, related_name="repayments")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="repayments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    collection_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COLLECTED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
         

    def clean(self):
        if self.amount <= Decimal("0.00"):
            raise ValidationError("Collection amount must be greater than zero.")

        if self.expected_amount > 0 and self.amount > self.expected_amount:
            self.payment_type = self.PaymentType.OVER_COLLECTION
        elif self.expected_amount > 0 and self.amount < self.expected_amount:
            self.payment_type = self.PaymentType.PARTIAL
        else:
            self.payment_type = self.PaymentType.FULL

    def __str__(self):
        return self.receipt_number

class AgentCashSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    submission_number = models.CharField(max_length=40, unique=True)
    agent = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cash_submissions")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="cash_submissions")
    submission_date = models.DateField(default=timezone.localdate)
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    received_amount = models.DecimalField(max_digits=14, decimal_places=2)
    discrepancy = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="reviewed_submissions")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.discrepancy = self.received_amount - self.expected_amount
        super().save(*args, **kwargs)

    @property
    def has_discrepancy(self):
        return self.discrepancy != Decimal("0.00")

    def __str__(self):
        return self.submission_number

class CollectionAttempt(models.Model):
    class Outcome(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"
        PARTIAL = "PARTIAL", "Partial Payment"
        NOT_AVAILABLE = "NOT_AVAILABLE", "Customer Unavailable"
        REFUSED = "REFUSED", "Payment Refused"
        PROMISED = "PROMISED", "Promised to Pay"

    schedule = models.ForeignKey(RepaymentSchedule, on_delete=models.PROTECT, related_name="collection_attempts")
    agent = models.ForeignKey(User, on_delete=models.PROTECT, related_name="collection_attempts")
    attempt_date = models.DateField(default=timezone.localdate)
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempt_date", "-created_at"]

    def __str__(self):
        return f"{self.schedule_id} - {self.outcome}"
