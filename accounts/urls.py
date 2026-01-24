from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication endpoints
    path(
        "register/",
        views.RegistrationView.as_view(),
        name="register",
    ),
    path(
        "login/",
        views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout",
    ),
    # Token management
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "token/blacklist/",
        TokenBlacklistView.as_view(),
        name="token-blacklist",
    ),
    # User management
    path(
        "user/",
        views.UserDetailView.as_view(),
        name="user-detail",
    ),
    path(
        "user/profile/",
        views.UserProfileView.as_view(),
        name="user-profile",
    ),
    # Password management
    path(
        "password/change/",
        views.ChangePasswordView.as_view(),
        name="password-change",
    ),
    path(
        "password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password/reset/confirm/<str:uidb64>/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
