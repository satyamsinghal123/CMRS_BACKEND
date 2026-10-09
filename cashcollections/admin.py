from django.contrib import admin
from .models import Repayment, AgentCashSubmission, CollectionAttempt

@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "customer", "agent", "amount", "payment_type", "status", "collection_date")
    search_fields = ("receipt_number", "customer__full_name", "loan__loan_id")
    list_filter = ("status", "payment_type", "branch", "collection_date")

@admin.register(AgentCashSubmission)
class AgentCashSubmissionAdmin(admin.ModelAdmin):
    list_display = ("submission_number", "agent", "expected_amount", "received_amount", "discrepancy", "status")
    list_filter = ("status", "branch", "submission_date")

@admin.register(CollectionAttempt)
class CollectionAttemptAdmin(admin.ModelAdmin):
    list_display = ("schedule", "agent", "attempt_date", "outcome")
    list_filter = ("outcome", "attempt_date")
