from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Manager"
    COLLECTION_AGENT = "COLLECTION_AGENT", "Collection Agent"
    BRANCH_OPERATOR = "BRANCH_OPERATOR", "Branch Operator"

class User(AbstractUser):
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.BRANCH_OPERATOR)
    phone = models.CharField(max_length=20, blank=True)
    employee_code = models.CharField(max_length=30, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
