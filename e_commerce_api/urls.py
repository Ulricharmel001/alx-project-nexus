from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.static import serve as static_serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version="v1",
        description="E-Commerce Platform REST API",
        contact=openapi.Contact(
            email=getattr(settings, "SUPPORT_EMAIL", "support@example.com")
        ),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Docs
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    path(
        "openapi.json", schema_view.without_ui(cache_timeout=0), name="openapi-schema"
    ),
    path("", RedirectView.as_view(url="/swagger/", permanent=False)),
]


def serve_media(request, path):
    """Serve media files, returning a transparent pixel for missing files
    to avoid CORB from HTML 404 pages on cross-origin image loads."""
    from pathlib import Path

    file_path = Path(settings.MEDIA_ROOT) / path
    if file_path.exists():
        return static_serve(request, path, document_root=settings.MEDIA_ROOT)
    return HttpResponseNotFound(
        content="",
        content_type="text/plain",
    )


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [path("media/<path:path>", serve_media)]
