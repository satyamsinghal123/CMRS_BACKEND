from django.contrib import admin
from .models import BankDeposit, Settlement

@admin.register(BankDeposit)
class BankDepositAdmin(admin.ModelAdmin):
    list_display = ("deposit_number", "bank_account", "amount", "bank_reference", "status", "deposit_date")
    list_filter = ("status", "branch")

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("deposit", "settled_amount", "status", "settlement_date")
    list_filter = ("status",)
