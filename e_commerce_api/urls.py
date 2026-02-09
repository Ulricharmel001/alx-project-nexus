from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version="v1",
        description="""
E-Commerce Platform REST API

**Features:**
- User Authentication & Management
- Product Catalog Management
- Order Processing & Cart Management
- Payment Integration (Chapa)
- Inventory Tracking

**Authentication:** JWT Bearer Token
Include in Authorization header: `Bearer <token>`

**Base URL:** `/api/v1/`
        """,
        contact=openapi.Contact(
            name="Support",
            email=getattr(settings, 'SUPPORT_EMAIL', 'support@example.com'),
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API v1
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/products/", include("products.urls")),
    
    # API Documentation
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0)),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0)),
    path("openapi.json", schema_view.without_ui(cache_timeout=0)),
]
