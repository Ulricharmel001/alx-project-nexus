from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .models import (Address, Category, Inventory, Order, OrderItem, Payment,
                     Product, Review)
from .serializers import (AddressSerializer, CategorySerializer,
                          InventorySerializer, OrderItemSerializer,
                          OrderSerializer, PaymentSerializer,
                          ProductSerializer, ReviewSerializer)


class CategoryListView(generics.ListCreateAPIView):
    """List all categories or create a new category"""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProductListView(generics.ListCreateAPIView):
    """List all products or create a new product"""

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        # Filter by category
        category_id = self.request.query_params.get("category", None)
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        # Filter by price range
        min_price = self.request.query_params.get("min_price", None)
        max_price = self.request.query_params.get("max_price", None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a product"""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_search(request):
    """Search products by name or description"""
    query = request.GET.get("q", "")
    if query:
        products = Product.objects.filter(is_active=True).filter(
            name__icontains=query
        ) | Product.objects.filter(is_active=True).filter(description__icontains=query)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    else:
        return Response([], status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def category_tree(request):
    """Get category tree structure"""
    root_categories = Category.objects.filter(parent=None, is_active=True)
    serializer = CategorySerializer(root_categories, many=True)
    return Response(serializer.data)


class AddressListView(generics.ListCreateAPIView):
    """List all addresses or create a new address"""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["city", "state", "country"]
    ordering_fields = ["created_at", "city"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        return Address.objects.filter(customer=user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an address"""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Address.objects.filter(customer=user)


class InventoryListView(generics.ListCreateAPIView):
    """List all inventories or create a new inventory"""

    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["quantity", "created_at"]
    ordering = ["-created_at"]


class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an inventory"""

    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]


class OrderListView(generics.ListCreateAPIView):
    """List all orders or create a new order"""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["created_at", "total_price", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(customer=user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an order"""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(customer=user)


class PaymentListView(generics.ListCreateAPIView):
    """List all payments or create a new payment"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a payment"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


class ReviewListView(generics.ListCreateAPIView):
    """List all reviews or create a new review"""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["created_at", "rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Review.objects.all()

        product_id = self.request.query_params.get("product", None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        customer_id = self.request.query_params.get("customer", None)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        return queryset


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a review"""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
