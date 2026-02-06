from django.core.management.base import BaseCommand

from ip_tracking.models import BlockedIP


class Command(BaseCommand):
    help = "Block an IP address"

    def add_arguments(self, parser):
        parser.add_argument("ip", type=str)
        parser.add_argument("--reason", type=str, default="Blocked manually")

    def handle(self, *args, **kwargs):
        ip = kwargs["ip"]
        reason = kwargs["reason"]
        blocked, created = BlockedIP.objects.get_or_create(
            ip_address=ip, defaults={"reason": reason}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"IP {ip} blocked successfully"))
        else:
            self.stdout.write(f"IP {ip} is already blocked")
