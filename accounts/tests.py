import time
import unittest
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.email_utils import (CODE_EXPIRATION_TIME, RESEND_COOLDOWN_TIME,
                                  VERIFICATION_CODES, can_resend_code,
                                  generate_verification_code,
                                  send_password_reset_email,
                                  send_verification_email, send_welcome_email,
                                  store_verification_code, verify_code)
from accounts.middleware.maintenance_middleware import \
    MaintenanceModeMiddleware
from accounts.models import CustomUser, MaintenanceMode, UserProfile
from accounts.serializers import (GoogleAuthSerializer,
                                  GoogleCallbackSerializer, LoginSerializer,
                                  PasswordResetConfirmSerializer,
                                  PasswordResetRequestSerializer,
                                  RegistrationSerializer,
                                  ResendVerificationEmailSerializer,
                                  validate_password_strength)

try:
    from accounts.google_oauth import GoogleAuthHandler

    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GoogleAuthHandler = None  # type: ignore
    GOOGLE_AUTH_AVAILABLE = False

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

TEST_REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

User = get_user_model()


class MaintenanceModeMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )

        def dummy_get_response(request):
            return HttpResponse("Normal Response")

        self.get_response = dummy_get_response

    def test_maintenance_mode_blocks_non_admin_users(self):
        MaintenanceMode.objects.create(is_enabled=True)
        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get("/")
        request.user = self.user
        response = middleware(request)
        self.assertEqual(response.status_code, 503)
        self.assertIn("maintenance", response.content.decode().lower())

    def test_maintenance_mode_allows_admin_users(self):
        MaintenanceMode.objects.create(is_enabled=True)
        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get("/")
        request.user = self.admin_user
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Normal Response")

    def test_normal_operation_when_maintenance_disabled(self):
        middleware = MaintenanceModeMiddleware(self.get_response)
        request = self.factory.get("/")
        request.user = self.user
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Normal Response")


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:register")

    @patch("accounts.views.send_verification_email")
    def test_registration_success(self, mock_send):
        mock_send.return_value = (True, "Email queued")
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "strongpass123",
            "password2": "strongpass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["email_verification_required"], True)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())
        mock_send.assert_called_once()

    def test_registration_duplicate_email(self):
        User.objects.create_user(
            email="existing@example.com",
            password="pass12345",
            first_name="Existing",
            last_name="User",
        )
        data = {
            "email": "existing@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "strongpass123",
            "password2": "strongpass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_password_mismatch(self):
        data = {
            "email": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "strongpass123",
            "password2": "differentpass456",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_weak_password(self):
        data = {
            "email": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "12345678",
            "password2": "12345678",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_missing_fields(self):
        response = self.client.post(
            self.url, {"email": "test@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_profile_created_via_signal(self):
        data = {
            "email": "profiletest@example.com",
            "first_name": "Profile",
            "last_name": "Test",
            "password": "strongpass123",
            "password2": "strongpass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="profiletest@example.com")
        self.assertTrue(hasattr(user, "userprofile"))


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            email="login@example.com",
            password="testpass123",
            first_name="Login",
            last_name="User",
        )

    def test_login_success(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["message"], "Login successful")

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self):
        response = self.client.post(
            self.url,
            {"email": "nobody@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_user_data(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "login@example.com")


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class UserDetailTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:user")
        self.user = User.objects.create_user(
            email="detail@example.com",
            password="testpass123",
            first_name="Detail",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_detail(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "detail@example.com")
        self.assertEqual(response.data["first_name"], "Detail")
        self.assertIn("profile", response.data)

    def test_update_user_detail(self):
        response = self.client.put(self.url, {"first_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_get_user_detail_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class UserProfileTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:user-profile")
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="testpass123",
            first_name="Profile",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile(self):
        response = self.client.put(
            self.url,
            {"bio": "This is my bio", "phone_number": "+237600000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.bio, "This is my bio")

    def test_get_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PasswordChangeTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:password-change")
        self.user = User.objects.create_user(
            email="changepass@example.com",
            password="oldpass12345",
            first_name="Change",
            last_name="Pass",
        )
        self.client.force_authenticate(user=self.user)

    def test_password_change_success(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "oldpass12345",
                "new_password": "newpass12345",
                "new_password2": "newpass12345",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass12345"))

    def test_password_change_wrong_old_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "wrongpass123",
                "new_password": "newpass12345",
                "new_password2": "newpass12345",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_mismatch(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "oldpass12345",
                "new_password": "newpass12345",
                "new_password2": "differentpass",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_same_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "oldpass12345",
                "new_password": "oldpass12345",
                "new_password2": "oldpass12345",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PasswordResetTests(APITestCase):
    def setUp(self):
        self.request_url = reverse("accounts:password-reset")
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="testpass123",
            first_name="Reset",
            last_name="User",
        )

    @patch("accounts.email_utils.send_password_reset_email")
    def test_password_reset_request_success(self, mock_send):
        response = self.client.post(
            self.request_url, {"email": "reset@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send.assert_called_once()

    def test_password_reset_request_nonexistent_email(self):
        response = self.client.post(
            self.request_url, {"email": "nobody@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_success(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse("accounts:password-reset-confirm", args=[uid, token])
        response = self.client.post(
            url,
            {"password": "newstrongpass123", "password2": "newstrongpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_mismatch(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse("accounts:password-reset-confirm", args=[uid, token])
        response = self.client.post(
            url,
            {"password": "newpass12345", "password2": "mismatch"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class EmailVerificationTests(APITestCase):
    def setUp(self):
        self.verify_url = reverse("accounts:email-verify")
        self.resend_url = reverse("accounts:email-resend")
        self.user = User.objects.create_user(
            email="verify@example.com",
            password="testpass123",
            first_name="Verify",
            last_name="User",
        )

    def test_email_verify_success(self):
        code = store_verification_code("verify@example.com")
        response = self.client.post(
            self.verify_url,
            {"email": "verify@example.com", "code": code},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)

    def test_email_verify_invalid_code(self):
        store_verification_code("verify@example.com")
        response = self.client.post(
            self.verify_url,
            {"email": "verify@example.com", "code": "000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_verify_no_code_stored(self):
        response = self.client.post(
            self.verify_url,
            {"email": "verify@example.com", "code": "123456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.views.send_verification_email")
    def test_resend_verification_success(self, mock_send):
        mock_send.return_value = (True, "Email queued")
        VERIFICATION_CODES.pop("verify@example.com", None)
        response = self.client.post(
            self.resend_url, {"email": "verify@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("code_expires_in", response.data)

    def test_resend_verification_nonexistent_email(self):
        response = self.client.post(
            self.resend_url, {"email": "nobody@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_rate_limited(self):
        now = time.time()
        VERIFICATION_CODES["verify@example.com"] = {
            "code": "123456",
            "created_at": now - 120,  # 2 min ago (not expired)
            "resend_at": now - 10,  # 10s ago (still in cooldown)
        }
        response = self.client.post(
            self.resend_url, {"email": "verify@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_refresh")
        self.user = User.objects.create_user(
            email="token@example.com",
            password="testpass123",
            first_name="Token",
            last_name="User",
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_token_refresh_success(self):
        response = self.client.post(
            self.url, {"refresh": str(self.refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid(self):
        response = self.client.post(
            self.url, {"refresh": "invalidtoken"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class LogoutTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:logout")
        self.user = User.objects.create_user(
            email="logout@example.com",
            password="testpass123",
            first_name="Logout",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)
        self.refresh = RefreshToken.for_user(self.user)

    def test_logout_success(self):
        response = self.client.post(
            self.url, {"refresh": str(self.refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url, {"refresh": str(self.refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class GoogleOAuthTests(APITestCase):
    def test_google_login_url(self):
        url = reverse("accounts:google-login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("authorization_url", response.data)
        self.assertIn("accounts.google.com", response.data["authorization_url"])

    @patch("accounts.google_oauth.GoogleAuthHandler.exchange_code_for_token")
    @patch("accounts.google_oauth.GoogleAuthHandler.verify_google_token")
    @patch("accounts.google_oauth.GoogleAuthHandler.get_or_create_user")
    @patch("accounts.google_oauth.GoogleAuthHandler.get_tokens_for_user")
    def test_google_callback_success(
        self, mock_tokens, mock_get_or_create, mock_verify, mock_exchange
    ):
        mock_exchange.return_value = {"id_token": "fake_id_token"}
        mock_verify.return_value = {
            "email": "google@example.com",
            "given_name": "Google",
            "family_name": "User",
        }
        user = User.objects.create_user(
            email="google@example.com",
            password="testpass123",
            first_name="Google",
            last_name="User",
        )
        mock_get_or_create.return_value = (user, False)
        mock_tokens.return_value = {
            "access": "fake_access_token",
            "refresh": "fake_refresh_token",
        }

        url = reverse("accounts:google-callback")
        response = self.client.post(url, {"code": "fake_auth_code"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Google login successful")
        self.assertIn("access", response.data)

    def test_google_callback_missing_code(self):
        url = reverse("accounts:google-callback")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.google_oauth.GoogleAuthHandler.exchange_code_for_token")
    def test_google_callback_exchange_fails(self, mock_exchange):
        mock_exchange.return_value = None
        url = reverse("accounts:google-callback")
        response = self.client.post(url, {"code": "bad_code"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.google_oauth.GoogleAuthHandler.verify_google_token")
    def test_google_token_success(self, mock_verify):
        mock_verify.return_value = {
            "email": "googleuser@example.com",
            "given_name": "Google",
            "family_name": "User",
        }
        url = reverse("accounts:google-token")
        response = self.client.post(url, {"token": "fake_google_token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_google_token_missing(self):
        url = reverse("accounts:google-token")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="model@example.com",
            password="testpass123",
            first_name="Model",
            last_name="User",
        )
        self.assertEqual(user.email, "model@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_email_unique(self):
        User.objects.create_user(
            email="unique@example.com",
            password="testpass123",
            first_name="First",
            last_name="User",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="unique@example.com",
                password="testpass456",
                first_name="Second",
                last_name="User",
            )

    def test_user_str(self):
        user = User.objects.create_user(
            email="strtest@example.com",
            password="testpass123",
            first_name="Str",
            last_name="Test",
        )
        self.assertIn("Str", str(user))
        self.assertIn("Test", str(user))


class CeleryTaskTests(TestCase):
    @patch("accounts.tasks.send_mail")
    def test_send_verification_email_task(self, mock_send_mail):
        from accounts.tasks import send_verification_email_task

        result = send_verification_email_task("test@example.com", "123456")
        mock_send_mail.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch("accounts.tasks.send_mail")
    def test_send_password_reset_email_task(self, mock_send_mail):
        from accounts.tasks import send_password_reset_email_task

        result = send_password_reset_email_task(
            "test@example.com", "TestUser", "reset-token-123", "uid-abc"
        )
        mock_send_mail.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch("accounts.tasks.send_mail")
    def test_send_welcome_email_task(self, mock_send_mail):
        from accounts.tasks import send_welcome_email_task

        result = send_welcome_email_task("test@example.com", "TestUser")
        mock_send_mail.assert_called_once()
        self.assertEqual(result["status"], "success")


# ===========================
# 🧪 Serializer Validation Tests
# ===========================
class SerializerValidationTests(TestCase):
    """Test serializer validation logic directly (not through views)"""

    # --- RegistrationSerializer ---
    def test_registration_password_mismatch_validation(self):
        """❌ Passwords don't match -> should fail"""
        serializer = RegistrationSerializer(
            data={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "strongpass123",
                "password2": "differentpass456",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_strength_too_short(self):
        """❌ Password < 8 chars -> ValidationError"""
        with self.assertRaises(Exception):
            validate_password_strength("abc")

    def test_password_strength_all_numeric(self):
        """❌ Numeric-only password -> ValidationError"""
        with self.assertRaises(Exception):
            validate_password_strength("12345678")

    # --- LoginSerializer ---
    def test_login_serializer_missing_fields(self):
        """❌ No email/password -> invalid"""
        serializer = LoginSerializer(data={})
        self.assertFalse(serializer.is_valid())

    # --- PasswordResetRequestSerializer ---
    def test_reset_request_serializer_nonexistent_email(self):
        """❌ Email not registered -> invalid"""
        serializer = PasswordResetRequestSerializer(
            data={"email": "nobody@example.com"}
        )
        self.assertFalse(serializer.is_valid())

    # --- PasswordResetConfirmSerializer ---
    def test_reset_confirm_password_mismatch(self):
        """❌ password != password2 -> invalid"""
        serializer = PasswordResetConfirmSerializer(
            data={
                "password": "newpass123",
                "password2": "mismatch",
            }
        )
        self.assertFalse(serializer.is_valid())

    # --- GoogleAuthSerializer ---
    def test_google_auth_serializer_empty_token(self):
        """❌ Empty token -> invalid"""
        serializer = GoogleAuthSerializer(data={"token": ""})
        self.assertFalse(serializer.is_valid())

    # --- GoogleCallbackSerializer ---
    def test_google_callback_serializer_empty_code(self):
        """❌ Empty code -> invalid"""
        serializer = GoogleCallbackSerializer(data={"code": ""})
        self.assertFalse(serializer.is_valid())

    # --- ResendVerificationEmailSerializer ---
    def test_resend_verification_serializer_nonexistent_email(self):
        """❌ Email not found -> invalid"""
        serializer = ResendVerificationEmailSerializer(
            data={"email": "nobody@example.com"}
        )
        self.assertFalse(serializer.is_valid())


# ===========================
# 🧪 Email Utility Tests
# ===========================
@override_settings(CACHES=TEST_CACHES)
class EmailUtilsTests(TestCase):
    """Direct unit tests for accounts/email_utils.py"""

    def setUp(self):
        """🧹 Clean slate before each test"""
        VERIFICATION_CODES.clear()

    # --- generate_verification_code ---
    def test_generate_code_returns_6_digits(self):
        """🔢 Code is exactly 6 numeric digits"""
        code = generate_verification_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    # --- store_verification_code ---
    def test_store_code_adds_to_dict(self):
        """📦 Code is stored in VERIFICATION_CODES"""
        code = store_verification_code("store@example.com")
        self.assertEqual(len(code), 6)
        self.assertIn("store@example.com", VERIFICATION_CODES)

    def test_store_code_overwrites_existing(self):
        """📦 Storing a second code overwrites the first"""
        code1 = store_verification_code("dup@example.com")
        code2 = store_verification_code("dup@example.com")
        self.assertEqual(len(code2), 6)
        self.assertIn("dup@example.com", VERIFICATION_CODES)
        # should NOT equal the old one (new random code)
        self.assertNotEqual(code1, code2)

    # --- verify_code ---
    def test_verify_code_success(self):
        """✅ Correct code verifies and is removed"""
        code = store_verification_code("verify@example.com")
        is_valid, message = verify_code("verify@example.com", code)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Code verified successfully")
        self.assertNotIn("verify@example.com", VERIFICATION_CODES)

    def test_verify_code_invalid(self):
        """❌ Wrong code -> rejected"""
        store_verification_code("verify@example.com")
        is_valid, message = verify_code("verify@example.com", "000000")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Invalid verification code")

    def test_verify_code_no_code_stored(self):
        """❌ No code ever stored for this email"""
        is_valid, message = verify_code("nobody@example.com", "123456")
        self.assertFalse(is_valid)
        self.assertIn("No verification code", message)

    def test_verify_code_expired(self):
        """⏰ Code older than 5 minutes -> expired"""
        VERIFICATION_CODES["expired@example.com"] = {
            "code": "123456",
            "created_at": time.time() - CODE_EXPIRATION_TIME - 60,
            "resend_at": None,
        }
        is_valid, message = verify_code("expired@example.com", "123456")
        self.assertFalse(is_valid)
        self.assertIn("expired", message.lower())

    # --- can_resend_code ---
    def test_can_resend_no_code_stored(self):
        """📤 No stored code -> can resend"""
        can, wait = can_resend_code("fresh@example.com")
        self.assertTrue(can)
        self.assertEqual(wait, 0)

    def test_can_resend_rate_limited(self):
        """⏳ Within 60s cooldown -> blocked"""
        VERIFICATION_CODES["limited@example.com"] = {
            "code": "123456",
            "created_at": time.time() - 30,
            "resend_at": time.time() - 10,  # 10s ago, still within cooldown
        }
        can, wait = can_resend_code("limited@example.com")
        self.assertFalse(can)
        self.assertGreater(wait, 0)

    def test_can_resend_after_cooldown(self):
        """✅ After 60s cooldown -> can resend"""
        VERIFICATION_CODES["cooldown@example.com"] = {
            "code": "123456",
            "created_at": time.time() - 120,
            "resend_at": time.time() - 70,  # 70s ago, past the 60s cooldown
        }
        can, wait = can_resend_code("cooldown@example.com")
        self.assertTrue(can)

    # --- send_verification_email ---
    @patch("accounts.tasks.send_verification_email_task")
    def test_send_verification_email_queues_task(self, mock_task):
        """📧 Verification email task is queued"""
        mock_task.delay.return_value.id = "task-123"
        success, message = send_verification_email("test@example.com", "123456")
        self.assertTrue(success)
        mock_task.delay.assert_called_once_with("test@example.com", "123456")

    @patch(
        "accounts.tasks.send_verification_email_task.delay",
        side_effect=Exception("Queue failed"),
    )
    def test_send_verification_email_failure(self, mock_delay):
        """📧 Queue failure returns error"""
        success, message = send_verification_email("test@example.com", "123456")
        self.assertFalse(success)
        self.assertIn("fail", message.lower())

    # --- send_password_reset_email ---
    @patch("accounts.tasks.send_password_reset_email_task")
    def test_send_password_reset_email_queues_task(self, mock_task):
        """📧 Password reset email task is queued"""
        user = User.objects.create_user(
            email="reset_test@example.com",
            password="test12345",
            first_name="Reset",
            last_name="Tester",
        )
        mock_task.delay.return_value.id = "task-456"
        success, message = send_password_reset_email(user, "token123", "uid456")
        self.assertTrue(success)
        mock_task.delay.assert_called_once_with(
            "reset_test@example.com", "Reset", "token123", "uid456"
        )

    # --- send_welcome_email ---
    @patch("accounts.tasks.send_welcome_email_task")
    def test_send_welcome_email_queues_task(self, mock_task):
        """📧 Welcome email task is queued"""
        mock_task.delay.return_value.id = "task-789"
        success, message = send_welcome_email("test@example.com", "Test")
        self.assertTrue(success)
        mock_task.delay.assert_called_once_with("test@example.com", "Test")


# ===========================
# 🧪 GoogleAuthHandler Unit Tests
# ===========================
class GoogleAuthHandlerTests(TestCase):
    """Direct unit tests for accounts/google_oauth.py"""

    def setUp(self):
        self.user_data = {
            "email": "google@example.com",
            "given_name": "Google",
            "family_name": "User",
        }

    # --- verify_google_token ---
    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_verify_google_token_success(self, mock_verify):
        """✅ Valid Google token returns user info"""
        mock_verify.return_value = {
            "iss": "accounts.google.com",
            "email": "test@example.com",
        }
        result = GoogleAuthHandler.verify_google_token("fake-token")
        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "test@example.com")

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_verify_google_token_wrong_issuer(self, mock_verify):
        """❌ Token from wrong issuer -> None"""
        mock_verify.return_value = {"iss": "malicious-site.com"}
        result = GoogleAuthHandler.verify_google_token("fake-token")
        self.assertIsNone(result)

    @patch(
        "google.oauth2.id_token.verify_oauth2_token",
        side_effect=ValueError("Invalid token"),
    )
    def test_verify_google_token_exception(self, mock_verify):
        """❌ Exception during verification -> None"""
        result = GoogleAuthHandler.verify_google_token("bad-token")
        self.assertIsNone(result)

    # --- get_or_create_user ---
    def test_get_or_create_user_new(self):
        """✅ New Google user is created"""
        user, created = GoogleAuthHandler.get_or_create_user(self.user_data)
        self.assertTrue(created)
        self.assertEqual(user.email, "google@example.com")
        self.assertEqual(user.first_name, "Google")
        self.assertEqual(user.last_name, "User")

    def test_get_or_create_user_existing(self):
        """✅ Existing user is returned, not re-created"""
        User.objects.create_user(
            email="google@example.com",
            password="test12345",
            first_name="Existing",
            last_name="User",
        )
        user, created = GoogleAuthHandler.get_or_create_user(self.user_data)
        self.assertFalse(created)
        self.assertEqual(user.email, "google@example.com")
        # Existing name preserved (not overwritten)
        self.assertEqual(user.first_name, "Existing")

    def test_get_or_create_user_no_email(self):
        """❌ Missing email raises ValueError"""
        with self.assertRaises(ValueError):
            GoogleAuthHandler.get_or_create_user({})

    # --- get_tokens_for_user ---
    def test_get_tokens_for_user(self):
        """✅ JWT tokens are generated for a user"""
        user = User.objects.create_user(
            email="tokenuser@example.com",
            password="test12345",
            first_name="Token",
            last_name="User",
        )
        tokens = GoogleAuthHandler.get_tokens_for_user(user)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)
        self.assertTrue(len(tokens["access"]) > 0)
        self.assertTrue(len(tokens["refresh"]) > 0)

    # --- exchange_code_for_token ---
    @patch("accounts.google_oauth.requests.post")
    def test_exchange_code_success(self, mock_post):
        """✅ Authorization code exchanged for tokens"""
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "access_token": "fake_access",
            "id_token": "fake_id",
        }
        mock_response.raise_for_status.return_value = None
        result = GoogleAuthHandler.exchange_code_for_token(
            "auth-code", "http://localhost/redirect"
        )
        self.assertIsNotNone(result)
        self.assertIn("access_token", result)
        self.assertIn("id_token", result)

    @patch(
        "accounts.google_oauth.requests.post",
        side_effect=requests.exceptions.HTTPError("401 Unauthorized"),
    )
    def test_exchange_code_http_error(self, mock_post):
        """❌ HTTP error during exchange -> None"""
        result = GoogleAuthHandler.exchange_code_for_token(
            "bad-code", "http://localhost/redirect"
        )
        self.assertIsNone(result)

    @patch(
        "accounts.google_oauth.requests.post",
        side_effect=requests.exceptions.RequestException("Network down"),
    )
    def test_exchange_code_request_error(self, mock_post):
        """❌ Network error during exchange -> None"""
        result = GoogleAuthHandler.exchange_code_for_token(
            "bad-code", "http://localhost/redirect"
        )
        self.assertIsNone(result)


# ===========================
# 🧪 Signal Tests
# ===========================
class SignalTests(TestCase):
    """Test Django signals (auto-creation of profiles)"""

    def test_profile_created_on_user_creation(self):
        """✅ UserProfile auto-created when CustomUser is created"""
        user = User.objects.create_user(
            email="signaltest@example.com",
            password="test12345",
            first_name="Signal",
            last_name="Test",
        )
        self.assertTrue(hasattr(user, "userprofile"))
        self.assertIsInstance(user.userprofile, UserProfile)

    def test_profile_str(self):
        """✅ UserProfile.__str__ contains user email"""
        user = User.objects.create_user(
            email="profilestr@example.com",
            password="test12345",
            first_name="Profile",
            last_name="Str",
        )
        self.assertIn(user.email, str(user.userprofile))


# ===========================
# 🧪 Additional Model Tests
# ===========================
class ExtraModelTests(TestCase):
    """Edge case model tests"""

    def test_custom_user_manager_no_email_raises_error(self):
        """❌ Creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email="", password="test12345")

    def test_maintenance_mode_str_on(self):
        """✅ __str__ shows ON when enabled"""
        mode = MaintenanceMode.objects.create(is_enabled=True)
        self.assertIn("ON", str(mode))

    def test_maintenance_mode_str_off(self):
        """✅ __str__ shows OFF when disabled"""
        mode = MaintenanceMode.objects.create(is_enabled=False)
        self.assertIn("OFF", str(mode))

    def test_maintenance_mode_is_maintenance_enabled(self):
        """✅ is_maintenance_mode returns True when enabled"""
        MaintenanceMode.objects.create(is_enabled=True)
        self.assertTrue(MaintenanceMode.is_maintenance_mode())

    def test_maintenance_mode_is_maintenance_disabled(self):
        """✅ is_maintenance_mode returns False when disabled"""
        MaintenanceMode.objects.create(is_enabled=False)
        self.assertFalse(MaintenanceMode.is_maintenance_mode())

    def test_maintenance_mode_is_maintenance_no_entries(self):
        """✅ is_maintenance_mode returns False when no rows exist"""
        self.assertFalse(MaintenanceMode.is_maintenance_mode())
