"""
URL configuration for e_commerce_api project.

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version="v1",
        description="API documentation for authentication and services",
        contact=openapi.Contact(email=settings.SUPPORT_EMAIL),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API routes
    path("api/v1/accounts/", include("accounts.urls")),
    # API Documentation
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0)),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0)),
]
