from django.contrib import admin
from .models import Reconciliation

@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "expected_amount", "received_amount", "difference", "status")
    list_filter = ("status", "branch")
