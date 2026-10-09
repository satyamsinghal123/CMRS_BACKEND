from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("loans", "0001_initial"),
    ]
    operations = [
        migrations.AlterField(
            model_name="loan", name="status",
            field=models.CharField(choices=[("PENDING_APPROVAL", "Pending Approval"), ("REJECTED", "Rejected"), ("ACTIVE", "Active"), ("OVERDUE", "Overdue"), ("CLOSED", "Closed")], default="PENDING_APPROVAL", max_length=20),
        ),
        migrations.AddField(model_name="loan", name="approved_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="loan", name="rejection_reason", field=models.TextField(blank=True)),
        migrations.AddField(model_name="loan", name="approved_by", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="loans_approved", to="accounts.user")),
    ]
