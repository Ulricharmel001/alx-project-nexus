from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile

User = get_user_model()


class RegistrationTests(TestCase):
    """Tests for user registration endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/accounts/register/"

    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "testuser@example.com")

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",
            "password2": "differentpassword",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_short_password(self):
        """Test registration with password less than 8 characters"""
        data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "pass123",
            "password2": "pass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_numeric_password(self):
        """Test registration with entirely numeric password"""
        data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "12345678",
            "password2": "12345678",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email="existing@example.com",
            password="testpass123",
            first_name="Existing",
            last_name="User",
        )
        data = {
            "email": "existing@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_creates_profile(self):
        """Test that registration automatically creates a user profile"""
        data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="testuser@example.com")
        self.assertTrue(hasattr(user, "userprofile"))


class LoginTests(TestCase):
    """Tests for user login endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/v1/accounts/login/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_successful_login(self):
        """Test successful user login"""
        data = {"email": "testuser@example.com", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_email(self):
        """Test login with invalid email"""
        data = {"email": "nonexistent@example.com", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_password(self):
        """Test login with invalid password"""
        data = {"email": "testuser@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        data = {"email": "testuser@example.com", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        data = {"email": "testuser@example.com"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutTests(TestCase):
    """Tests for user logout endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = "/api/v1/accounts/logout/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_successful_logout(self):
        """Test successful logout"""
        self.client.force_authenticate(user=self.user)
        data = {"refresh": str(self.refresh_token)}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logout successful")

    def test_logout_without_authentication(self):
        """Test logout without authentication"""
        data = {"refresh": str(self.refresh_token)}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailTests(TestCase):
    """Tests for user detail endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user_url = "/api/v1/accounts/user/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_get_user_details(self):
        """Test retrieving user details"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_get_user_details_unauthorized(self):
        """Test retrieving user details without authentication"""
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_details(self):
        """Test updating user details"""
        self.client.force_authenticate(user=self.user)
        data = {"first_name": "Updated"}
        response = self.client.put(self.user_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


class ChangePasswordTests(TestCase):
    """Tests for change password endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.change_password_url = "/api/v1/accounts/password/change/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="oldpassword123",
            first_name="Test",
            last_name="User",
        )

    def test_successful_password_change(self):
        """Test successful password change"""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "oldpassword123",
            "new_password": "newpassword123",
            "new_password2": "newpassword123",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "new_password2": "newpassword123",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_mismatch(self):
        """Test password change with mismatched new passwords"""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "oldpassword123",
            "new_password": "newpassword123",
            "new_password2": "differentpassword",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_same_as_old(self):
        """Test password change with same password as old"""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "oldpassword123",
            "new_password": "oldpassword123",
            "new_password2": "oldpassword123",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_unauthorized(self):
        """Test password change without authentication"""
        data = {
            "old_password": "oldpassword123",
            "new_password": "newpassword123",
            "new_password2": "newpassword123",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(TestCase):
    """Tests for password reset endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.reset_request_url = "/api/v1/accounts/password/reset/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_password_reset_request_valid_email(self):
        """Test password reset request with valid email"""
        data = {"email": "testuser@example.com"}
        response = self.client.post(self.reset_request_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email"""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.reset_request_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTests(TestCase):
    """Tests for user profile endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.profile_url = "/api/v1/accounts/user/profile/"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_get_user_profile(self):
        """Test retrieving user profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        data = {"bio": "Test bio", "phone_number": "1234567890"}
        response = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.bio, "Test bio")

    def test_update_profile_unauthorized(self):
        """Test updating profile without authentication"""
        data = {"bio": "Test bio"}
        response = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
