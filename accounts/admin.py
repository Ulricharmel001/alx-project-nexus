from django.contrib import admin

from .models import CustomUser, MaintenanceMode, UserProfile


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
    list_display = ("bio", "phone_number", "address")
    search_fields = ("address", "phone_number")
    ordering = ("phone_number",)


@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ("id", "is_enabled", "updated_at")
    list_editable = ("is_enabled",)
    readonly_fields = ("updated_at",)
    fieldsets = (
        (None, {"fields": ("is_enabled",)}),
        ("Message", {"fields": ("message",)}),
        ("Timestamps", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        count = MaintenanceMode.objects.count()
        if count > 0:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return True
