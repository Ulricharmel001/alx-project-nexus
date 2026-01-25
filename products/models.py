from django.db import models
from django.utils import timezone
import uuid

# Create your models here.

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at =  models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abtract = True

class Category(BaseModel):
    name = models.CharField(max_length=250, db_index=True)
    parent = models.ForeignKey(
        'self', 
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )

    
    class Meta:
        ordering = ('created_at', )

class Product(BaseModel):
    categories = models.ManyTomanyField(Category, related_name='products')
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_length=10, decimal_places=2)
    is_active = models.BooleanField(default=True, db_index=True)
    def __str__(self):
        return self.name



