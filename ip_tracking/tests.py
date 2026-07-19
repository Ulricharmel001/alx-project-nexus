import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from ip_tracking.middleware import IPTrackingMiddleware
from ip_tracking.models import BlockedIP, RequestLog, SuspiciousIP

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

User = get_user_model()


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

    def test_request_log_with_method(self):
        log = RequestLog.objects.create(
            ip_address=self.valid_ip,
            path=self.valid_path,
            method="POST",
        )
        self.assertEqual(log.method, "POST")

    def test_request_log_default_method(self):
        log = RequestLog.objects.create(
            ip_address=self.valid_ip,
            path=self.valid_path,
        )
        self.assertEqual(log.method, "GET")

    def test_blocked_ip_expiry(self):
        from datetime import timedelta

        from django.utils import timezone

        blocked_ip = BlockedIP.objects.create(
            ip_address=self.valid_ip,
            reason="Temporary block",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertIsNotNone(blocked_ip.expires_at)
        self.assertTrue(blocked_ip.expires_at > timezone.now())

    def test_suspicious_ip_resolve(self):
        suspicious_ip = SuspiciousIP.objects.create(
            ip_address=self.valid_ip, reason="Testing"
        )
        suspicious_ip.resolved = True
        suspicious_ip.save()
        self.assertTrue(suspicious_ip.resolved)


@override_settings(CACHES=TEST_CACHES)
class IPTrackingMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        def get_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        self.get_response = get_response
        self.middleware = IPTrackingMiddleware(get_response)

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_creates_request_log(self, mock_get_ip):
        mock_get_ip.return_value = ("203.0.113.1", True)
        request = self.factory.get("/api/v1/products/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RequestLog.objects.filter(ip_address="203.0.113.1").exists())

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_blocks_blocked_ip(self, mock_get_ip):
        BlockedIP.objects.create(ip_address="10.0.0.99", reason="Blocked for testing")
        mock_get_ip.return_value = ("10.0.0.99", True)
        request = self.factory.get("/api/v1/products/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_allows_unblocked_ip(self, mock_get_ip):
        mock_get_ip.return_value = ("10.0.0.100", True)
        request = self.factory.get("/api/v1/products/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)


# ===========================
# 🧪 Middleware Edge Case Tests
# ===========================
class IPTrackingMiddlewareExtendedTests(TestCase):
    """Tests for middleware edge cases and extract_product_id"""

    def setUp(self):
        self.factory = RequestFactory()

        def get_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        self.get_response = get_response
        self.middleware = IPTrackingMiddleware(get_response)

    # --- extract_product_id ---
    def test_extract_product_id_uuid(self):
        """🔍 UUID in product URL path is extracted"""
        path = "/api/v1/products/123e4567-e89b-12d3-a456-426614174000/"
        result = self.middleware.extract_product_id(path)
        self.assertEqual(result, "123e4567-e89b-12d3-a456-426614174000")

    def test_extract_product_id_numeric(self):
        """🔍 Numeric ID in product URL path is extracted"""
        path = "/api/v1/products/42/"
        result = self.middleware.extract_product_id(path)
        self.assertEqual(result, 42)

    def test_extract_product_id_no_match(self):
        """🔍 Non-product URL returns None"""
        path = "/api/v1/categories/"
        result = self.middleware.extract_product_id(path)
        self.assertIsNone(result)

    def test_extract_product_id_invalid_uuid(self):
        """🔍 Malformed UUID falls through to None"""
        path = "/api/v1/products/not-a-valid-uuid-here/"
        result = self.middleware.extract_product_id(path)
        self.assertIsNone(result)

    def test_extract_product_id_products_substring(self):
        """🔍 Path containing 'products' but no ID returns None"""
        path = "/api/v1/product-suggestions/"
        result = self.middleware.extract_product_id(path)
        self.assertIsNone(result)

    # --- Middleware behavior ---
    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_no_ip_continues(self, mock_get_ip):
        """✅ No client IP -> request continues normally"""
        mock_get_ip.return_value = (None, False)
        request = self.factory.get("/api/v1/products/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_with_authenticated_user(self, mock_get_ip):
        """✅ Authenticated user's ID is logged in RequestLog"""
        mock_get_ip.return_value = ("203.0.113.1", True)
        user = User.objects.create_user(
            email="loguser@example.com",
            password="test12345",
            first_name="Log",
            last_name="User",
        )
        request = self.factory.get(
            "/api/v1/products/123e4567-e89b-12d3-a456-426614174000/"
        )
        request.user = user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        log = RequestLog.objects.filter(ip_address="203.0.113.1").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user_id, user.id)
        self.assertEqual(log.product_id, "123e4567-e89b-12d3-a456-426614174000")

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_logs_user_agent(self, mock_get_ip):
        """✅ User-Agent header is logged in RequestLog"""
        mock_get_ip.return_value = ("203.0.113.1", True)
        request = self.factory.get("/api/v1/products/", HTTP_USER_AGENT="TestBot/1.0")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        log = RequestLog.objects.filter(ip_address="203.0.113.1").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user_agent, "TestBot/1.0")

    @patch("ip_tracking.middleware.get_client_ip")
    def test_middleware_logs_request_method(self, mock_get_ip):
        """✅ HTTP method is logged in RequestLog"""
        mock_get_ip.return_value = ("203.0.113.1", True)
        request = self.factory.post("/api/v1/products/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        log = RequestLog.objects.filter(ip_address="203.0.113.1").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.method, "POST")
