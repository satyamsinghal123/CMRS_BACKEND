from django.contrib import admin
from .models import Loan, RepaymentSchedule

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("loan_id", "customer", "principal_amount", "outstanding_amount", "status", "approved_by")
    list_filter = ("status", "branch")
    search_fields = ("loan_id", "customer__full_name", "customer__customer_id")

@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ("loan", "installment_number", "due_date", "expected_amount", "paid_amount", "status")
    list_filter = ("status", "due_date")
