from decimal import Decimal
from django.db import models
from customers.models import Customer
from core.models import Branch

class LoanStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    REJECTED = "REJECTED", "Rejected"
    ACTIVE = "ACTIVE", "Active"
    OVERDUE = "OVERDUE", "Overdue"
    CLOSED = "CLOSED", "Closed"

class Loan(models.Model):
    loan_id = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="loans")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="loans")
    principal_amount = models.DecimalField(max_digits=14, decimal_places=2)
    outstanding_amount = models.DecimalField(max_digits=14, decimal_places=2)
    monthly_due = models.DecimalField(max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    start_date = models.DateField()
    maturity_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.PENDING_APPROVAL)
    approved_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="loans_approved")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loan_id

class RepaymentSchedule(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"

    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name="schedule")
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["loan", "installment_number"], name="unique_loan_installment")
        ]
        ordering = ["due_date"]

    @property
    def remaining_amount(self):
        return max(self.expected_amount - self.paid_amount, Decimal("0.00"))
