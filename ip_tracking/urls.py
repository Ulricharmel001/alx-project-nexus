
from django.urls import path

from . import views

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("login/", views.login_view, name="login"),
    path("account/", views.account_view, name="account"),
    path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),
]
