from django.contrib import admin

from .models import BlockedIP, RequestLog, SuspiciousIP


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "path", "timestamp", "country", "city", "user_id")
    list_filter = ("timestamp", "country", "city")
    search_fields = ("ip_address", "path")
    readonly_fields = ("timestamp",)


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "reason", "blocked_at")
    search_fields = ("ip_address", "reason")


@admin.register(SuspiciousIP)
class SuspiciousIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "reason", "flagged_at")
    search_fields = ("ip_address", "reason")
