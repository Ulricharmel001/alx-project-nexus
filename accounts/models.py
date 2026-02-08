from django.contrib.auth.models import (AbstractUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):
    ROLES_CHOICES = [
        ("admin", "Admin"),
        ("user", "User"),
    ]

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES_CHOICES, default="user")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Profile of {self.user.email}"


class MaintenanceMode(models.Model):
    """
    Model to control maintenance mode status
    """

    is_enabled = models.BooleanField(
        default=False, help_text="Enable or disable maintenance mode"
    )
    message = models.TextField(
        default="We are currently performing scheduled maintenance. We'll be back soon!",
        help_text="Message to show to users during maintenance",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maintenance Mode"
        verbose_name_plural = "Maintenance Mode"

    def __str__(self):
        return f"Maintenance Mode: {'ON' if self.is_enabled else 'OFF'}"

    @classmethod
    def is_maintenance_mode(cls):
        """
        Class method to check if maintenance mode is enabled
        """
        try:
            maintenance_setting = cls.objects.first()
            if maintenance_setting:
                return maintenance_setting.is_enabled
            return False
        except:
            return False
