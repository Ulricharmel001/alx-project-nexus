from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser, UserProfile


def validate_password_strength(value):
    """Validate password strength: min 8 chars and not entirely numeric"""
    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )
    if value.isdigit():
        raise serializers.ValidationError("Password cannot be entirely numeric.")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["bio", "profile_picture", "phone_number", "address"]


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password, validate_password_strength],
        min_length=8,
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
    )

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name", "password", "password2"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(**validated_data)
        # UserProfile will be created automatically by the signal
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        email, password = data.get("email"), data.get("password")
        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        data["user"] = user
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source="userprofile", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "date_joined"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password, validate_password_strength],
        min_length=8,
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
    )

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        if data["new_password"] != data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "Passwords didn't match."}
            )
        if data.get("old_password") == data["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must differ from old password."}
            )
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset requests
    - Validates email exists
    - Generates reset token
    - Queues password reset email via Celery
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that user with email exists"""
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def save(self):
        """
        Generate reset token and queue email via Celery
        Called after validation passes
        """
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from accounts.email_utils import send_password_reset_email
        
        email = self.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        # Generate reset token and UID
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_token = default_token_generator.make_token(user)
        
        # Queue password reset email via Celery (async, non-blocking)
        send_password_reset_email(user, reset_token, uid)
        
        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password, validate_password_strength],
        min_length=8,
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
    )

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return data


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication"""

    token = serializers.CharField(required=True, write_only=True)

    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Token cannot be empty.")
        return value


class GoogleCallbackSerializer(serializers.Serializer):
    """Serializer for Google OAuth callback"""

    code = serializers.CharField(required=True, write_only=True)

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Authorization code is required.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification with code"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for resending verification email"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

