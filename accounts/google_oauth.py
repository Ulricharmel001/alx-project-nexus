import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class GoogleAuthHandler:
    """Handle Google OAuth authentication and token verification"""

    @staticmethod
    def verify_google_token(token):
        """
        Verify Google ID token and extract user information.

        Args:
            token: Google ID token

        Returns:
            dict: User information or None if verification fails
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID
            )

            # Token is valid
            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Wrong issuer.")

            return idinfo

        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            return None

    @staticmethod
    def get_or_create_user(google_user_data):
        """
        Get or create user from Google user data.

        Args:
            google_user_data: Dictionary containing Google user information

        Returns:
            tuple: (user, created) - User object and boolean indicating if it was created
        """
        email = google_user_data.get("email")
        first_name = google_user_data.get("given_name", "")
        last_name = google_user_data.get("family_name", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )

        return user, created

    @staticmethod
    def get_tokens_for_user(user):
        """Generate JWT tokens for authenticated user"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def exchange_code_for_token(code, redirect_uri):
        """
        Exchange Google authorization code for tokens.

        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in the authorization request

        Returns:
            dict: Token response or None if exchange fails
        """
        try:
            token_endpoint = "https://oauth2.googleapis.com/token"

            payload = {
                "code": code,
                "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            response = requests.post(token_endpoint, data=payload)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"Code exchange failed: {str(e)}")
            return None
