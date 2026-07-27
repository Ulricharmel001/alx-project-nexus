from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create an admin superuser"

    def handle(self, *args, **options):
        User = get_user_model()
        email = "admin@nexus.com"
        password = "nexus12345"  # pragma: allowlist secret
        try:
            user = User.objects.get(email=email)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Admin user '{email}' updated to superuser")
            )
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                email=email, password=password, first_name="Admin", last_name="Nexus"
            )
            self.stdout.write(self.style.SUCCESS(f"Admin user '{email}' created"))
