import logging
import uuid
from decimal import Decimal

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .chapa_service import ChapaService
from .models import (Address, Cart, CartItem, Inventory, Order, OrderItem,
                     Product)
from .serializers import CartItemSerializer, CartSerializer, OrderSerializer
from .tasks import generate_and_send_receipt_email

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    operation_summary="Get or update user's cart",
    operation_description="Retrieve or update the authenticated user's shopping cart.",
    responses={200: CartSerializer}
)
class CartView(generics.RetrieveUpdateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(customer=self.request.user)
        return cart


@swagger_auto_schema(
    operation_summary="List or add items to cart",
    operation_description="Retrieve list of items in the user's cart or add a new item to the cart.",
    responses={200: CartItemSerializer(many=True)}
)
class CartItemView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(customer=self.request.user)
        return cart.items.all()

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(customer=self.request.user)
        product = serializer.validated_data["product"]

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": serializer.validated_data["quantity"],
                "created_by": self.request.user,
            },
        )

        if not created:
            cart_item.quantity += serializer.validated_data["quantity"]
            cart_item.updated_by = self.request.user
            cart_item.save()


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(customer=self.request.user)
        return cart.items.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@api_view(["POST"])
def add_to_cart(request):
    """
    Add a product to the user's cart
    Expected data: {product_id, quantity}
    """
    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))

    if not product_id:
        return Response({"error": "Product ID is required"}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(customer=request.user)

    # Check inventory availability
    try:
        inventory = product.inventory
        if inventory.available_quantity() < quantity:
            return Response(
                {
                    "error": f"Insufficient inventory. Only {inventory.available_quantity()} available."
                },
                status=400,
            )
    except Inventory.DoesNotExist:
        return Response({"error": "Product inventory not found"}, status=400)

    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity, "created_by": request.user},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.updated_by = request.user
        cart_item.save()

    serializer = CartItemSerializer(cart_item)
    return Response(
        {
            "message": "Product added to cart successfully",
            "item": serializer.data,
            "cart_total": cart.total_price,
        }
    )


@api_view(["DELETE"])
def remove_from_cart(request, item_id):
    """
    Remove an item from the user's cart
    """
    try:
        cart = Cart.objects.get(customer=request.user)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        return Response({"message": "Item removed from cart successfully"})
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=404)
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=404)


@api_view(["POST"])
def update_cart_item(request, item_id):
    """
    Update quantity of a cart item
    Expected data: {quantity}
    """
    try:
        cart = Cart.objects.get(customer=request.user)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        quantity = int(request.data.get("quantity", 1))

        if quantity <= 0:
            cart_item.delete()
            return Response({"message": "Item removed from cart (quantity <= 0)"})

        # Check inventory availability
        if cart_item.product.inventory.available_quantity() < quantity:
            return Response(
                {
                    "error": f"Insufficient inventory. Only {cart_item.product.inventory.available_quantity()} available."
                },
                status=400,
            )

        cart_item.quantity = quantity
        cart_item.updated_by = request.user
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(
            {
                "message": "Cart item updated successfully",
                "item": serializer.data,
                "cart_total": cart.total_price,
            }
        )
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=404)
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=404)


@api_view(["POST"])
def clear_cart(request):
    """
    Clear all items from the user's cart
    """
    try:
        cart = Cart.objects.get(customer=request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared successfully"})
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=404)


@api_view(["POST"])
def checkout(request):
    """
    Create an order from the user's cart and initiate payment
    Expected data: {shipping_address_id}
    """
    try:
        cart = Cart.objects.get(customer=request.user)

        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        shipping_address_id = request.data.get("shipping_address_id")
        if not shipping_address_id:
            return Response({"error": "Shipping address is required"}, status=400)

        try:
            shipping_address = Address.objects.get(
                id=shipping_address_id, customer=request.user
            )
        except Address.DoesNotExist:
            return Response({"error": "Invalid shipping address"}, status=404)

        # Create order
        order = Order.objects.create(
            customer=request.user,
            shipping_address=shipping_address,
            total_price=cart.total_price,
            currency="CFA",
            created_by=request.user,
        )

        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price_at_purchase=cart_item.product.price,
                subtotal=cart_item.subtotal,
                created_by=request.user,
            )

            # Reserve inventory
            inventory = cart_item.product.inventory
            inventory.reserved_quantity += cart_item.quantity
            inventory.save()

        # Clear the cart
        cart.items.all().delete()

        # Return order details for payment processing
        order_serializer = OrderSerializer(order)
        return Response(
            {
                "message": "Order created successfully",
                "order": order_serializer.data,
                "checkout_url": f"/api/products/purchases/create/?order_id={order.id}",
            }
        )

    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=404)
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        return Response({"error": "An error occurred during checkout"}, status=500)


@api_view(["POST"])
def initiate_payment_test(request):
    """
    Test endpoint to initiate payment for an order
    Expected data: {order_id, first_name, last_name, email}
    """
    order_id = request.data.get("order_id")
    first_name = request.data.get("first_name", "Test")
    last_name = request.data.get("last_name", "User")
    email = request.data.get("email", request.user.email)

    if not order_id:
        return Response({"error": "Order ID is required"}, status=400)

    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.status == "paid":
        return Response({"error": "Order already paid"}, status=400)

    tx_ref = f"TX-{uuid.uuid4().hex[:12].upper()}"
    chapa = ChapaService()
    response = chapa.initiate_payment(
        first_name=first_name,
        last_name=last_name,
        email=email,
        amount=Decimal(order.total_price),
        tx_ref=tx_ref,
    )

    if response.get("status") != "success":
        return Response({"error": "Payment initiation failed"}, status=400)

    from .models import Purchase

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
            "message": "Payment initiated successfully. Redirect to checkout_url to complete payment.",
        }
    )
