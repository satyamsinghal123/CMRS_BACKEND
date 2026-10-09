from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "full_name", "phone", "branch", "assigned_agent", "is_active")
    search_fields = ("customer_id", "full_name", "phone")
    list_filter = ("branch", "is_active")
