import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import CustomUser


# Create your models here.
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=250, db_index=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return self.name


class Product(BaseModel):
    categories = models.ManyToManyField(Category, related_name="products")
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    slug = models.SlugField(unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=15, default="CFA")
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name


# Address model needed for orders
class Address(BaseModel):
    customer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=20, db_index=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"


# inventory of stock
class Inventory(BaseModel):
    product = models.OneToOneField(
        Product, related_name="inventory", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=0, db_index=True)
    reserved_quantity = models.PositiveIntegerField(default=0)

    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"Inventory for {self.product.name} - Available: {self.available_quantity()}, Reserved: {self.reserved_quantity}"


# order and orderItem
class Order(BaseModel):
    ORDER_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    customer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="orders"
    )
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, default="CFA")

    def __str__(self):
        return f"Order {self.id} - {self.customer} - {self.status}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order {self.order.id}"


# Purchase
class Purchase(BaseModel):
    PURCHASE_STATUS = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("verified", "Verified"),
    ]
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="purchase"
    )
    provider = models.CharField(max_length=200, default="chapa")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, default="ETB")
    status = models.CharField(max_length=20, choices=PURCHASE_STATUS, default="pending")
    transaction_reference = models.CharField(max_length=200, blank=True, null=True)
    purchase_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=200, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Purchase for order {self.order.id} - {self.status}"


class PurchaseVerification(BaseModel):
    purchase = models.OneToOneField(
        Purchase, on_delete=models.CASCADE, related_name="verification"
    )
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_details = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Verification for purchase {self.purchase.id} - Verified: {self.is_verified}"


# Cart model
class Cart(BaseModel):
    customer = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="cart"
    )

    def __str__(self):
        return f"Cart for {self.customer.username}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"

    @property
    def subtotal(self):
        return self.quantity * self.product.price


# Review database
class Review(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    customer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )  # Rating from 1 to 5
    comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("product", "customer")  # One review per customer per product

    def __str__(self):
        return f"Review for {self.product.name} by {self.customer}"
