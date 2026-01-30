from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version="v1",
        description="""
        E-Commerce Platform API with user authentication and order management.
        
        **Authentication:** JWT Bearer Token at `/api/v1/accounts/login/`
        
        **Features:**
        - User Registration & Email Verification
        - JWT Authentication
        - Email Notifications & Password Reset
        - Product & Order Management
        - OAuth2 Google Integration
        """,
        contact=openapi.Contact(
            name="Support Team",
            email=settings.SUPPORT_EMAIL,
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("accounts.urls")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0)),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0)),
    path("openapi.json", schema_view.without_ui(cache_timeout=0)),
]
