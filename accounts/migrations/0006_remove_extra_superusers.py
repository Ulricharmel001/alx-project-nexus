from django.db import migrations


def remove_extra_superusers(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    CustomUser.objects.filter(is_superuser=True).exclude(
        email="admin@nexus.com"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_auto_20260208_0432"),
    ]

    operations = [
        migrations.RunPython(remove_extra_superusers, migrations.RunPython.noop),
    ]
