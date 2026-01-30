import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from accounts.models import CustomUser

# Create your models here.


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated"
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


class Product(BaseModel):
    categories = models.ManyToManyField(Category, related_name="products")
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    slug = models.SlugField()
    price = models.DecimalField(max_length=10, decimal_places=2)
    currency = models.CharField(max_length=15, default='CFA')
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name




# inventory of stock

class Inventory(BaseModel):
    product = models.OneToOneField(Product, related_name='inventory', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0, db_index=True)
    reserved_quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Inventory for {self.product.name} - Available: {self.quantity}, Reserved: {self.reserved_quantity}"



# order and orderItem
class Order(BaseModel):
    ORDER_STATUS = [
        ("pendind", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("dilivered", "Dilivered"),
        ("cancelled", "Cancelled")
    ]
    customer = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,  related_name="orders"
    )
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending")
    total_price = models.DateTimeField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, default="CFA")



    # OrderItems
class OrderItem(BaseModel):
    order =  models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product =  models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_at_purchase = models.DateTimeField(max_digits=12, decimal_places=2)
    subtotal = models.DateTimeField(max_digits=12, decimal_places=2)


    # Payment DB

class Payment(BaseModel):
    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded")

    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=12, default="CFA")
    status = models.CharField( max_length=200, choices=PAYMENT_STATUS, default="pending")
    transaction_reference = models.CharField(max_length=200, blank=True, null=True)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=200, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)
    


    # Review database

class Review(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True, null=True)



    