from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_legacy_passwords(apps, schema_editor):
    User = apps.get_model("apartments", "User")
    users = User.objects.using(schema_editor.connection.alias).only("pk", "password")

    for user in users.iterator():
        if user.password.startswith("!"):
            continue

        try:
            identify_hasher(user.password)
        except ValueError:
            user.password = make_password(user.password or None)
            user.save(update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [
        ("apartments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(hash_legacy_passwords, migrations.RunPython.noop),
    ]
