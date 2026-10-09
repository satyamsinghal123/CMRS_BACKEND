from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Branch, BankAccount
from reconciliation.models import Reconciliation
from accounts.models import User

class BankDeposit(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        SUBMITTED = "SUBMITTED", "Submitted"
        SETTLED = "SETTLED", "Settled"
        MISMATCH = "MISMATCH", "Mismatch"

    deposit_number = models.CharField(max_length=40, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="deposits")
    reconciliation = models.ForeignKey(Reconciliation, on_delete=models.PROTECT, related_name="deposits")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="deposits")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    deposit_date = models.DateField(default=timezone.localdate)
    bank_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_deposits")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.reconciliation.status != "APPROVED":
            raise ValidationError("Only approved reconciliation can be deposited.")
        if self.amount <= 0:
            raise ValidationError("Deposit amount must be greater than zero.")
        if self.amount > self.reconciliation.received_amount:
            raise ValidationError("Deposit cannot exceed reconciled received amount.")

    def __str__(self):
        return self.deposit_number

class Settlement(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SETTLED = "SETTLED", "Settled"
        MISMATCH = "MISMATCH", "Mismatch"
        FAILED = "FAILED", "Failed"

    deposit = models.OneToOneField(BankDeposit, on_delete=models.PROTECT, related_name="settlement")
    settled_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    settlement_date = models.DateTimeField(null=True, blank=True)
    settlement_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def difference(self):
        return self.settled_amount - self.deposit.amount
