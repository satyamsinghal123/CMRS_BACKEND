from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("cashcollections", "0001_initial"),
        ("loans", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="CollectionAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempt_date", models.DateField(default=django.utils.timezone.localdate)),
                ("outcome", models.CharField(choices=[("COLLECTED", "Collected"), ("PARTIAL", "Partial Payment"), ("NOT_AVAILABLE", "Customer Unavailable"), ("REFUSED", "Payment Refused"), ("PROMISED", "Promised to Pay")], max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("agent", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collection_attempts", to="accounts.user")),
                ("schedule", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collection_attempts", to="loans.repaymentschedule")),
            ],
            options={"ordering": ["-attempt_date", "-created_at"]},
        ),
    ]
