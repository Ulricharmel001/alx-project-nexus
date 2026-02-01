from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/search/', views.product_search, name='product-search'),
    path('categories/tree/', views.category_tree, name='category-tree'),
    
    # Address URLs
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<uuid:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    
    # Inventory URLs
    path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<uuid:pk>/', views.InventoryDetailView.as_view(), name='inventory-detail'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    
    # Payment URLs
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    
    # Review URLs
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
]