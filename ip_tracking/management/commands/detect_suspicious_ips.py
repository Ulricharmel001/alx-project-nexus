from collections import Counter
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ip_tracking.models import RequestLog, SuspiciousIP


class Command(BaseCommand):
    help = "Detect suspicious IP addresses based on request patterns"

    def handle(self, *args, **options):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_logs = RequestLog.objects.filter(timestamp__gte=one_hour_ago)

        ip_counts = Counter(log.ip_address for log in recent_logs)

        flagged_count = 0
        for ip, count in ip_counts.items():
            if count > 50:  # Threshold for suspicious activity
                suspicious, created = SuspiciousIP.objects.get_or_create(
                    ip_address=ip,
                    defaults={
                        "reason": f"Suspected bot activity: {count} requests in 1 hour"
                    },
                )
                if created:
                    flagged_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Flagged suspicious IP: {ip} ({count} requests)"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Detection complete. {flagged_count} IPs flagged as suspicious."
            )
        )
