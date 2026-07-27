import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update an admin superuser"

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@nexus.com", help="Admin email")
        parser.add_argument(
            "--password",
            help="Admin password (prompted securely if omitted)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"] or getpass.getpass("Password: ")
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
