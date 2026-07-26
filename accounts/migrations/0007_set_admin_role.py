from django.db import migrations


def set_admin_role(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    CustomUser.objects.filter(is_superuser=True).update(role="admin")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_remove_extra_superusers"),
    ]

    operations = [
        migrations.RunPython(set_admin_role, migrations.RunPython.noop),
    ]
