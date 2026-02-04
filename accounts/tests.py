from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from accounts.middleware.maintenance_middleware import MaintenanceModeMiddleware
from accounts.models import MaintenanceMode

User = get_user_model()


class MaintenanceModeMiddlewareTest(TestCase):
    """
    Test the maintenance mode middleware functionality
    """

    def setUp(self):
        self.factory = RequestFactory()

        # Create a regular user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass',
            first_name='Test',
            last_name='User'
        )

        # Create an admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )

        def dummy_get_response(request):
            return HttpResponse("Normal Response")

        self.get_response = dummy_get_response

    def test_maintenance_mode_blocks_non_admin_users(self):
        """Test that non-admin users receive maintenance message during maintenance"""
        # Enable maintenance mode
        MaintenanceMode.objects.create(is_enabled=True)

        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get('/')
        request.user = self.user  # Regular user

        response = middleware(request)

        self.assertEqual(response.status_code, 503)
        self.assertIn("maintenance", response.content.decode().lower())

    def test_maintenance_mode_allows_admin_users(self):
        """Test that admin users can access site during maintenance"""
        # Enable maintenance mode
        MaintenanceMode.objects.create(is_enabled=True)

        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get('/')
        request.user = self.admin_user  # Admin user

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Normal Response")

    def test_normal_operation_when_maintenance_disabled(self):
        """Test that all users get normal response when maintenance is disabled"""
        # Disable maintenance mode (or don't create it - defaults to disabled)
        # MaintenanceMode.objects.create(is_enabled=False)  # Not needed since default is False

        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get('/')
        request.user = self.user  # Regular user

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Normal Response")