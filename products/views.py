import logging
import uuid
from decimal import Decimal

from django.db import models
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
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


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@api_view(["GET"])
def category_tree(request):
    """Return category hierarchy"""
    roots = Category.objects.filter(parent=None)
    serializer = CategorySerializer(roots, many=True, context={"request": request})
    return Response(serializer.data)


# --- Products ---


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


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


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


class AddressListView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(customer=self.request.user)


# --- Orders ---


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


class ReviewListView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# --- Inventory ---


class InventoryListView(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "quantity"]
    ordering = ["-created_at"]


class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
