import logging
import uuid
from decimal import Decimal

from django.db import models
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .chapa_service import ChapaService
from .models import (Address, Category, Inventory, Order, Product, Purchase,
                     PurchaseVerification, Review)
from .serializers import (AddressSerializer, CategorySerializer,
                          InventorySerializer, OrderSerializer,
                          ProductSerializer, PurchaseSerializer,
                          PurchaseVerificationSerializer, ReviewSerializer)
from .tasks import generate_and_send_receipt_email

logger = logging.getLogger(__name__)

# --- Categories ---


@swagger_auto_schema(
    operation_summary="List all categories",
    operation_description="Retrieve a list of all product categories. Supports filtering, searching, and ordering.",
    responses={200: CategorySerializer(many=True)}
)
class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
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


@swagger_auto_schema(
    operation_summary="Get, update or delete a category",
    operation_description="Retrieve, update or delete a specific product category by its UUID.",
    responses={
        200: CategorySerializer,
        404: "Category not found"
    }
)
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@swagger_auto_schema(
    method='get',
    operation_summary="Get category hierarchy",
    operation_description="Retrieve the hierarchical structure of all categories.",
    responses={200: CategorySerializer(many=True)}
)
@api_view(["GET"])
def category_tree(request):
    """Return category hierarchy"""
    roots = Category.objects.filter(parent=None)
    serializer = CategorySerializer(roots, many=True, context={"request": request})
    return Response(serializer.data)


# --- Products ---


@swagger_auto_schema(
    operation_summary="List all products",
    operation_description="Retrieve a list of all products. Supports filtering, searching, and ordering.",
    responses={200: ProductSerializer(many=True)}
)
class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "description", "categories__name"]
    ordering_fields = ["created_at", "name", "price"]
    ordering = ["-created_at"]


@swagger_auto_schema(
    operation_summary="Get, update or delete a product",
    operation_description="Retrieve, update or delete a specific product by its UUID.",
    responses={
        200: ProductSerializer,
        404: "Product not found"
    }
)
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@swagger_auto_schema(
    method='get',
    operation_summary="Search products",
    operation_description="Search for products by name or description.",
    manual_parameters=[
        openapi.Parameter(
            'q',
            openapi.IN_QUERY,
            description="Search query string",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={200: ProductSerializer(many=True)}
)
@api_view(["GET"])
def product_search(request):
    query = request.GET.get("q")
    products = (
        Product.objects.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query)
        )
        if query
        else Product.objects.none()
    )
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


# --- Addresses ---


@swagger_auto_schema(
    operation_summary="List user addresses",
    operation_description="Retrieve a list of addresses for the authenticated user.",
    responses={200: AddressSerializer(many=True)}
)
class AddressListView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


@swagger_auto_schema(
    operation_summary="Get, update or delete an address",
    operation_description="Retrieve, update or delete a specific address for the authenticated user.",
    responses={
        200: AddressSerializer,
        404: "Address not found"
    }
)
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)


# --- Orders ---


@swagger_auto_schema(
    operation_summary="List user orders",
    operation_description="Retrieve a list of orders for the authenticated user. Staff users can see all orders.",
    responses={200: OrderSerializer(many=True)}
)
class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Order.objects.all()
            if user.is_staff
            else Order.objects.filter(customer=user)
        )

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


@swagger_auto_schema(
    operation_summary="Get, update or delete an order",
    operation_description="Retrieve, update or delete a specific order for the authenticated user. Staff users can access all orders.",
    responses={
        200: OrderSerializer,
        404: "Order not found"
    }
)
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Order.objects.all()
            if user.is_staff
            else Order.objects.filter(customer=user)
        )


# --- Purchases & Payments ---


@swagger_auto_schema(
    operation_summary="Manage purchases",
    operation_description="Create, retrieve, update, or delete purchase records. Staff users can access all purchases.",
    responses={200: PurchaseSerializer(many=True)}
)
class PurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Purchase.objects.all()
            if user.is_staff
            else Purchase.objects.filter(created_by=user)
        )

    @swagger_auto_schema(
        operation_summary="Create a new purchase",
        operation_description="Initiate a payment for an order using Chapa payment gateway.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_id', 'first_name', 'last_name', 'email'],
            properties={
                'order_id': openapi.Schema(type=openapi.TYPE_STRING, description='UUID of the order to pay for'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Customer first name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Customer last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Customer email'),
            }
        ),
        responses={
            201: openapi.Response(
                description="Purchase created successfully",
                examples={
                    "application/json": {
                        "checkout_url": "https://checkout.chapa.co/...",
                        "tx_ref": "TX-ABC123DEF456",
                        "purchase_id": "123e4567-e89b-12d3-a456-426614174000"
                    }
                }
            ),
            400: "Bad Request - Missing required fields or order already paid"
        }
    )
    def create(self, request):
        data = request.data
        required_fields = ("order_id", "first_name", "last_name", "email")

        if not all(data.get(f) for f in required_fields):
            return Response({"error": "Missing required fields"}, status=400)

        order = get_object_or_404(Order, id=data["order_id"], customer=request.user)

        if order.status == "paid":
            return Response({"error": "Order already paid"}, status=400)

        tx_ref = f"TX-{uuid.uuid4().hex[:12].upper()}"
        chapa = ChapaService()
        response = chapa.initiate_payment(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            amount=Decimal(order.total_price),
            tx_ref=tx_ref,
        )

        if response.get("status") != "success":
            return Response({"error": "Payment initiation failed"}, status=400)

        purchase = Purchase.objects.create(
            order=order,
            provider="chapa",
            amount=order.total_price,
            currency="ETB",
            status="pending",
            transaction_reference=tx_ref,
            created_by=request.user,
        )

        return Response(
            {
                "checkout_url": response["data"]["checkout_url"],
                "tx_ref": tx_ref,
                "purchase_id": purchase.id,
            }
        )

    @swagger_auto_schema(
        method='get',
        operation_summary="Verify payment",
        operation_description="Verify the status of a payment transaction.",
        manual_parameters=[
            openapi.Parameter(
                'tx_ref',
                openapi.IN_PATH,
                description="Transaction reference ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment verification result",
                examples={
                    "application/json": {
                        "status": "completed"
                    }
                }
            ),
            400: "Bad Request - Verification failed",
            404: "Purchase not found"
        }
    )
    @action(detail=False, methods=["get"], url_path="verify/(?P<tx_ref>[^/.]+)")
    def verify_payment(self, request, tx_ref):
        purchase = get_object_or_404(
            Purchase, transaction_reference=tx_ref, created_by=request.user
        )

        chapa = ChapaService()
        response = chapa.verify_payment(tx_ref)

        if response.get("status") != "success":
            purchase.status = "failed"
            purchase.save()
            return Response({"error": "Verification failed"}, status=400)

        status_map = {"success": "completed", "failed": "failed", "pending": "pending"}
        chapa_status = response["data"].get("status", "").lower()
        purchase.status = status_map.get(chapa_status, "pending")
        purchase.payment_details = response["data"]
        purchase.save()

        if purchase.status == "completed":
            purchase.order.status = "paid"
            purchase.order.save()
            PurchaseVerification.objects.get_or_create(
                purchase=purchase,
                defaults={
                    "is_verified": True,
                    "verification_details": response["data"],
                    "created_by": request.user,
                },
            )
            generate_and_send_receipt_email.delay(str(purchase.id))

        return Response({"status": purchase.status})


# --- Reviews ---


@swagger_auto_schema(
    operation_summary="List all reviews",
    operation_description="Retrieve a list of all product reviews.",
    responses={200: ReviewSerializer(many=True)}
)
class ReviewListView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


@swagger_auto_schema(
    operation_summary="Get, update or delete a review",
    operation_description="Retrieve, update or delete a specific product review by its UUID.",
    responses={
        200: ReviewSerializer,
        404: "Review not found"
    }
)
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# --- Inventory ---


@swagger_auto_schema(
    operation_summary="List all inventory items",
    operation_description="Retrieve a list of all inventory items. Available to authenticated users only.",
    responses={200: InventorySerializer(many=True)}
)
class InventoryListView(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "quantity"]
    ordering = ["-created_at"]


@swagger_auto_schema(
    operation_summary="Get, update or delete inventory",
    operation_description="Retrieve, update or delete a specific inventory item by its UUID. Available to authenticated users only.",
    responses={
        200: InventorySerializer,
        404: "Inventory item not found"
    }
)
class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
