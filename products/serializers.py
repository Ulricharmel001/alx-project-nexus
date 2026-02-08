from decimal import Decimal

from rest_framework import serializers

from .models import (Address, Cart, CartItem, Category, Inventory, Order,
                     OrderItem, Product, Purchase, PurchaseVerification,
                     Review)


# CATEGORY
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "children",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "children", "created_at", "updated_at"]

    def get_children(self, obj):
        return CategorySerializer(obj.children.all(), many=True).data


# PRODUCT
class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "categories",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


# ADDRESS
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "street",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


# INVENTORY (ADMIN-ONLY)
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = [
            "id",
            "product",
            "quantity",
            "reserved_quantity",
            "updated_at",
        ]
        read_only_fields = ["id", "reserved_quantity", "updated_at"]


# =========================
# ORDER ITEM
# =========================
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price_at_purchase",
            "subtotal",
        ]
        read_only_fields = [
            "id",
            "unit_price_at_purchase",
            "subtotal",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


# ORDER


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "total_price",
            "currency",
            "shipping_address",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


# PURCHASE (PAYMENT)
class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = [
            "id",
            "order",
            "amount",
            "currency",
            "provider",
            "transaction_reference",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "transaction_reference",
            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_currency(self, value):
        return value.upper()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["status"] = "pending"
        return super().create(validated_data)


# CART
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_price",
            "quantity",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "subtotal", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "customer",
            "items",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "customer", "total_price", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


# PURCHASE VERIFICATION
class PurchaseVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseVerification
        fields = [
            "id",
            "purchase",
            "verified_by",
            "verified_at",
        ]
        read_only_fields = ["id", "verified_by", "verified_at"]

    def create(self, validated_data):
        validated_data["verified_by"] = self.context["request"].user
        return super().create(validated_data)


# REVIEW
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "rating",
            "title",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
