from django.db import migrations, models


def normalize_pending_status(apps, schema_editor):
    Complains = apps.get_model("apartments", "Complains")
    Complains.objects.using(schema_editor.connection.alias).filter(
        status="Pending"
    ).update(status="PENDING")


class Migration(migrations.Migration):
    dependencies = [
        ("apartments", "0005_complains_received_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complains",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("RESOLVED", "Resolved"),
                    ("IGNORED", "Ignored"),
                ],
                default="PENDING",
                max_length=10,
            ),
        ),
        migrations.RunPython(normalize_pending_status, migrations.RunPython.noop),
    ]
