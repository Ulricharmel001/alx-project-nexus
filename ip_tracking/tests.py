import uuid

from django.test import TestCase

from ip_tracking.models import BlockedIP, RequestLog, SuspiciousIP


class IPTrackingModelsTest(TestCase):
    def setUp(self):
        self.valid_ip = "192.168.1.1"
        self.valid_path = "/test-path/"
        self.valid_uuid = str(uuid.uuid4())

    def test_request_log_creation(self):
        log = RequestLog.objects.create(
            ip_address=self.valid_ip,
            path=self.valid_path,
            country="US",
            city="New York",
            user_id=1,
            product_id=self.valid_uuid,
        )

        self.assertEqual(log.ip_address, self.valid_ip)
        self.assertEqual(log.path, self.valid_path)
        self.assertEqual(log.country, "US")
        self.assertEqual(log.city, "New York")
        self.assertEqual(log.user_id, 1)
        self.assertEqual(log.product_id, self.valid_uuid)
        self.assertIsNotNone(log.timestamp)

    def test_blocked_ip_creation(self):
        blocked_ip = BlockedIP.objects.create(
            ip_address=self.valid_ip, reason="Testing purposes"
        )

        self.assertEqual(blocked_ip.ip_address, self.valid_ip)
        self.assertEqual(blocked_ip.reason, "Testing purposes")
        self.assertIsNotNone(blocked_ip.blocked_at)

    def test_suspicious_ip_creation(self):
        suspicious_ip = SuspiciousIP.objects.create(
            ip_address=self.valid_ip, reason="Multiple failed login attempts"
        )

        self.assertEqual(suspicious_ip.ip_address, self.valid_ip)
        self.assertEqual(suspicious_ip.reason, "Multiple failed login attempts")
        self.assertIsNotNone(suspicious_ip.flagged_at)
        self.assertFalse(suspicious_ip.resolved)

    def test_model_str_methods(self):
        log = RequestLog.objects.create(ip_address=self.valid_ip, path=self.valid_path)

        blocked_ip = BlockedIP.objects.create(
            ip_address=self.valid_ip, reason="Testing"
        )

        suspicious_ip = SuspiciousIP.objects.create(
            ip_address=self.valid_ip, reason="Testing"
        )

        self.assertIn(self.valid_ip, str(log))
        self.assertIn(self.valid_path, str(log))
        self.assertEqual(str(blocked_ip), self.valid_ip)
        self.assertIn(self.valid_ip, str(suspicious_ip))
        self.assertIn("Testing", str(suspicious_ip))
