from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import cart_service, views

app_name = "products"

router = DefaultRouter()
router.register(r"purchases", views.PurchaseViewSet, basename="purchase")

urlpatterns = [
    # Products (browsing)
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path(
        "products/<uuid:pk>/", views.ProductDetailView.as_view(), name="product-detail"
    ),
    path("products/search/", views.product_search, name="product-search"),
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<uuid:pk>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("categories/tree/", views.category_tree, name="category-tree"),
    # Cart functionality
    path("cart/", cart_service.CartView.as_view(), name="cart"),
    path("cart/items/", cart_service.CartItemView.as_view(), name="cart-items"),
    path(
        "cart/items/<uuid:pk>/",
        cart_service.CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path("cart/add/", cart_service.add_to_cart, name="add-to-cart"),
    path(
        "cart/remove/<uuid:item_id>/",
        cart_service.remove_from_cart,
        name="remove-from-cart",
    ),
    path(
        "cart/update/<uuid:item_id>/",
        cart_service.update_cart_item,
        name="update-cart-item",
    ),
    path("cart/clear/", cart_service.clear_cart, name="clear-cart"),
    path("addresses/", views.AddressListView.as_view(), name="address-list"),
    path(
        "addresses/<uuid:pk>/", views.AddressDetailView.as_view(), name="address-detail"
    ),
    # Checkout and orders
    path("checkout/", cart_service.checkout, name="checkout"),
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    # Purchases and payments
    path("", include(router.urls)),
    path("payment-test/", cart_service.initiate_payment_test, name="payment-test"),
    # Reviews
    path("reviews/", views.ReviewListView.as_view(), name="review-list"),
    path("reviews/<uuid:pk>/", views.ReviewDetailView.as_view(), name="review-detail"),
    # Inventory (admin only)
    path("inventory/", views.InventoryListView.as_view(), name="inventory-list"),
    path(
        "inventory/<uuid:pk>/",
        views.InventoryDetailView.as_view(),
        name="inventory-detail",
    ),
]
