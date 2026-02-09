from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .email_utils import (can_resend_code, send_verification_email,
                          send_welcome_email, store_verification_code,
                          verify_code)
from .models import CustomUser, UserProfile
from .serializers import (ChangePasswordSerializer,
                          EmailVerificationSerializer, LoginSerializer,
                          PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer,
                          RegistrationSerializer,
                          ResendVerificationEmailSerializer,
                          UserDetailSerializer, UserProfileSerializer)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, format="email", description="User email"
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="First name"
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Last name"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, format="password", description="Password"
                ),
                "password2": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="password",
                    description="Confirm password",
                ),
            },
            required=["email", "first_name", "last_name", "password", "password2"],
        ),
        responses={
            201: openapi.Response(
                "User registered successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                        "email_verification_required": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN
                        ),
                    },
                ),
            ),
            400: "Bad Request",
        },
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate 6-digit verification code (stored in memory)
            code = store_verification_code(user.email)

            # Queue email send via Celery (returns immediately, email sent async)
            send_verification_email(user.email, code)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "User registered successfully. Please check your email for verification code.",
                    "user": UserDetailSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "email_verification_required": True,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """User login with JWT tokens"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Authenticate user and return JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, format="email", description="User email"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, format="password", description="Password"
                ),
            },
            required=["email", "password"],
        ),
        responses={
            200: openapi.Response(
                "Login successful",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request",
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful",
                    "user": UserDetailSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout - blacklist refresh token"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """Get and update authenticated user details"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change authenticated user password"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Save triggers token generation and email queueing
            serializer.save()
            return Response(
                {"message": "Password reset link sent to your email"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {"message": "Password reset successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Get and update authenticated user profile"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Profile updated successfully",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )


class EmailVerificationView(APIView):
    """Verify user email with code"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            code = serializer.validated_data["code"]
            is_valid, message = verify_code(email, code)
            if is_valid:
                try:
                    user = CustomUser.objects.get(email=email)

                    # Send welcome email after successful verification
                    send_welcome_email(user.email, user.first_name)

                    return Response(
                        {"message": message, "user": UserDetailSerializer(user).data},
                        status=status.HTTP_200_OK,
                    )
                except CustomUser.DoesNotExist:
                    return Response(
                        {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                email = serializer.validated_data["email"]

                # Check if user can resend (enforces 1-minute cooldown)
                can_resend, wait_time = can_resend_code(email)
                if not can_resend:
                    return Response(
                        {
                            "error": f"Please wait {wait_time} seconds before requesting a new code"
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

                # Generate new 6-digit code
                code = store_verification_code(email)

                # Queue email send via Celery (returns immediately, email sent async)
                success, message = send_verification_email(email, code)
                if success:
                    return Response(
                        {
                            "message": message,
                            "code_expires_in": 300,  # 5 minutes in seconds
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": message}, status=status.HTTP_400_BAD_REQUEST
                    )
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    """Get Google OAuth login authorization URL"""

    permission_classes = [AllowAny]

    def get(self, request):
        authorization_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_OAUTH2_CLIENT_ID}&"
            f"redirect_uri={settings.GOOGLE_OAUTH2_REDIRECT_URI}&"
            f"response_type=code&scope=email%20profile&access_type=offline"
        )
        return Response({"authorization_url": authorization_url})


class GoogleCallbackView(APIView):
    """Exchange Google authorization code for JWT tokens"""

    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings

        from .google_oauth import GoogleAuthHandler

        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token_data = GoogleAuthHandler.exchange_code_for_token(
                code, settings.GOOGLE_OAUTH2_REDIRECT_URI
            )
            if not token_data:
                return Response(
                    {"error": "Failed to exchange code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            google_user_data = GoogleAuthHandler.verify_google_token(
                token_data.get("id_token")
            )
            if not google_user_data:
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )
            user, created = GoogleAuthHandler.get_or_create_user(google_user_data)
            if created:
                # UserProfile will be created automatically by the signal
                code = store_verification_code(user.email)
                send_verification_email(user.email, code)
            tokens = GoogleAuthHandler.get_tokens_for_user(user)
            return Response(
                {
                    "message": "Google login successful",
                    "user": UserDetailSerializer(user).data,
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Authentication failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GoogleTokenView(APIView):
    """Verify Google token and login user"""

    permission_classes = [AllowAny]

    def post(self, request):
        from .google_oauth import GoogleAuthHandler

        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            google_user_data = GoogleAuthHandler.verify_google_token(token)
            if not google_user_data:
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )
            user, created = GoogleAuthHandler.get_or_create_user(google_user_data)
            if created:
                # UserProfile will be created automatically by the signal
                code = store_verification_code(user.email)
                send_verification_email(user.email, code)
            tokens = GoogleAuthHandler.get_tokens_for_user(user)
            return Response(
                {
                    "message": "Google login successful",
                    "user": UserDetailSerializer(user).data,
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Authentication failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
