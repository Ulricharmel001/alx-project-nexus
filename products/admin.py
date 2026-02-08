from django.contrib import admin

from .models import (Address, Cart, CartItem, Category, Inventory, Order,
                     OrderItem, Product, Purchase, PurchaseVerification,
                     Review)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "parent", "created_at", "updated_at")
    search_fields = ("name",)
    list_editable = ("is_active",)
    # Removed prepopulated_fields because Category has no slug


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "currency",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "categories", "currency", "created_at", "updated_at")
    search_fields = ("name", "description", "slug")
    list_editable = ("is_active", "price", "currency")
    filter_horizontal = ("categories",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "street",
        "city",
        "state",
        "country",
        "postal_code",
        "is_default",
        "is_active",
    )
    list_filter = ("country", "state", "is_default", "is_active", "created_at")
    search_fields = (
        "street",
        "city",
        "state",
        "country",
        "postal_code",
        "customer__email",
    )
    list_editable = ("is_default", "is_active")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "quantity",
        "reserved_quantity",
        "available_quantity",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("product__name",)
    list_editable = ("quantity", "reserved_quantity", "is_active")

    def available_quantity(self, obj):
        return obj.available_quantity()

    available_quantity.short_description = "Available Quantity"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "status",
        "total_price",
        "currency",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "currency", "created_at", "updated_at", "customer")
    search_fields = ("customer__email", "id")
    list_editable = ("status", "total_price", "currency")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price_at_purchase",
        "subtotal",
        "created_at",
        "updated_at",
    )
    list_filter = ("order", "product", "created_at", "updated_at")
    search_fields = ("order__id", "product__name")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "provider",
        "amount",
        "currency",
        "status",
        "purchase_date",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "provider",
        "currency",
        "purchase_date",
        "created_at",
        "updated_at",
    )
    search_fields = ("order__id", "transaction_reference", "provider")
    list_editable = ("status",)


@admin.register(PurchaseVerification)
class PurchaseVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "purchase",
        "is_verified",
        "verified_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_verified", "verified_at", "created_at", "updated_at")
    search_fields = ("purchase__order__id", "purchase__transaction_reference")
    list_editable = ("is_verified",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "customer",
        "title",
        "rating",
        "created_at",
        "updated_at",
    )
    list_filter = ("rating", "created_at", "updated_at", "product", "customer")
    search_fields = ("product__name", "customer__email", "title", "content")
    list_editable = ("rating",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("customer", "total_price", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at", "customer")
    search_fields = ("customer__email",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "product",
        "quantity",
        "subtotal",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at", "cart", "product")
    search_fields = ("cart__customer__email", "product__name")
