from django.contrib import admin
from .models import Branch, BankAccount, AuditEvent

admin.site.register(Branch)
admin.site.register(BankAccount)
admin.site.register(AuditEvent)
