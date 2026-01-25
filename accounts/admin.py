from django.contrib import admin
from .models import CustomUser, UserProfile
# Register your models here.
# customizing the admin interface for CustomUser model
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('bio', 'phone_number', 'address')
    search_fields = ('address', 'phone_number')
    ordering = ('phone_number',)
