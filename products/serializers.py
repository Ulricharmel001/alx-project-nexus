from rest_framework import serializers
from decimal import Decimal

from .models import (Address, Category, Inventory, Order, OrderItem, Purchase,
                     Product, Review, PurchaseVerification)


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        if value > 999999.99:
            raise serializers.ValidationError("Price is too high.")
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

    def validate_postal_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Postal code cannot be empty.")
        return value

    def validate_country(self, value):
        if not value.strip():
            raise serializers.ValidationError("Country cannot be empty.")
        return value

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError("City cannot be empty.")
        return value

    def validate_state(self, value):
        if not value.strip():
            raise serializers.ValidationError("State cannot be empty.")
        return value

    def validate_street(self, value):
        if not value.strip():
            raise serializers.ValidationError("Street cannot be empty.")
        return value


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = "__all__"

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate_reserved_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Reserved quantity cannot be negative.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price_at_purchase(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value

    def validate_subtotal(self, value):
        if value <= 0:
            raise serializers.ValidationError("Subtotal must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def validate_total_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total price must be greater than zero.")
        return value

    def validate_status(self, value):
        valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']
        if value.lower() not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value.lower()


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = "__all__"

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if value > 999999.99:
            raise serializers.ValidationError("Amount is too high.")
        return value

    def validate_currency(self, value):
        # Validate common currency codes
        valid_currencies = ['ETB', 'USD', 'EUR', 'GBP', 'CFA']
        if value.upper() not in valid_currencies:
            raise serializers.ValidationError(f"Currency must be one of: {', '.join(valid_currencies)}")
        return value.upper()

    def validate_provider(self, value):
        if not value.strip():
            raise serializers.ValidationError("Provider cannot be empty.")
        return value.strip()

    def validate_transaction_reference(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Transaction reference must be at least 3 characters long.")
        return value

    def validate_status(self, value):
        valid_statuses = ['pending', 'completed', 'failed', 'refunded', 'verified']
        if value.lower() not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value.lower()


class PurchaseVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseVerification
        fields = "__all__"

    def validate(self, attrs):
        # Ensure the purchase exists and is valid
        purchase = attrs.get('purchase')
        if purchase and purchase.status != 'completed':
            raise serializers.ValidationError("Cannot verify a purchase that is not completed.")
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_title(self, value):
        if value and len(value) > 255:
            raise serializers.ValidationError("Title cannot exceed 255 characters.")
        return value

    def validate_comment(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError("Comment cannot exceed 1000 characters.")
        return value
