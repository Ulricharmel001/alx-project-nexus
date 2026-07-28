from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Send a test email to a user or to the configured FROM_EMAIL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Target email address (if omitted, uses the first active user in DB)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send to a specific user by ID",
        )
        parser.add_argument(
            "--type",
            default="test",
            choices=["test", "welcome", "verification"],
            help="Type of test email to send",
        )

    def handle(self, *args, **options):
        target_email = options.get("email")
        user_id = options.get("user_id")
        email_type = options.get("type")

        if target_email:
            pass
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
                target_email = user.email
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"User with id {user_id} not found"))
                return
        else:
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stderr.write(self.style.ERROR("No active users found in DB"))
                return
            target_email = user.email

        self.stdout.write("Email settings:")
        self.stdout.write(f"  BACKEND:     {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  HOST:        {settings.EMAIL_HOST}")
        self.stdout.write(f"  PORT:        {settings.EMAIL_PORT}")
        self.stdout.write(f"  USE_TLS:     {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  FROM:        {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  TO:          {target_email}")
        self.stdout.write(f"  TIMEOUT:     {settings.EMAIL_TIMEOUT}")
        self.stdout.write("")

        if email_type == "welcome":
            subject = "Test Welcome Email - Nexus"
            message = "Hello!\n\nThis is a test welcome email from the Nexus platform.\n\nBest regards,\nNexus Team"
        elif email_type == "verification":
            subject = "Test Verification Code - Nexus"
            message = "Hello!\n\nYour test verification code is: TEST-123456\n\nBest regards,\nNexus Team"
        else:
            subject = "Test Email from Nexus"
            message = (
                "This is a test email to verify the email sending system.\n\n"
                "If you received this, email sending is working correctly.\n\n"
                "Best regards,\nNexus Platform"
            )

        self.stdout.write(f"Sending '{email_type}' email to {target_email}...")
        self.stdout.flush()

        try:
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_email],
                fail_silently=False,
            )
            if sent:
                self.stdout.write(
                    self.style.SUCCESS(f"Email sent successfully to {target_email}")
                )
            else:
                self.stderr.write(
                    self.style.WARNING("Email send returned 0 (not sent)")
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to send email: {e}"))
