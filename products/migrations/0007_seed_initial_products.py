from decimal import Decimal

from django.db import migrations
from django.utils.text import slugify


def seed_products(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")

    cats = list(Category.objects.filter(name="Electronics"))
    if cats:
        for dup in cats[1:]:
            dup.delete()
    else:
        Category.objects.create(name="Electronics")

    products_data = [
        (
            "Smartphone Test Product",
            "Latest generation smartphone with high-resolution display",
            299.99,
            "USD",
        ),
        (
            "Wireless Headphones",
            "Noise-cancelling Bluetooth headphones with 30-hour battery life",
            149.99,
            "USD",
        ),
        (
            "Smart Watch Pro",
            "Fitness tracking smartwatch with heart rate monitor and GPS",
            259.99,
            "USD",
        ),
        (
            "USB-C Hub 7-in-1",
            "Multi-port adapter with HDMI, USB 3.0, SD card reader",
            39.99,
            "USD",
        ),
        (
            "Mechanical Keyboard RGB",
            "Cherry MX switches with per-key RGB backlighting",
            119.99,
            "USD",
        ),
        (
            "Ergonomic Mouse Vertical",
            "Wireless vertical mouse for reduced wrist strain",
            34.99,
            "USD",
        ),
        (
            "4K Webcam Pro",
            "Ultra HD webcam with auto-focus and built-in microphone",
            89.99,
            "USD",
        ),
        (
            "Portable Bluetooth Speaker",
            "Waterproof speaker with 360-degree sound",
            59.99,
            "USD",
        ),
        (
            "Laptop Stand Aluminum",
            "Adjustable ergonomic laptop stand, fits 10-17 inch laptops",
            45.99,
            "USD",
        ),
        (
            "Noise Cancelling Earbuds",
            "True wireless earbuds with active noise cancellation",
            79.99,
            "USD",
        ),
        (
            "External SSD 1TB",
            "Portable solid state drive with USB-C, read speeds up to 1050MB/s",
            109.99,
            "USD",
        ),
    ]

    for name, desc, price, currency in products_data:
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        Product.objects.create(
            name=name,
            description=desc,
            slug=slug,
            price=Decimal(str(price)),
            currency=currency,
            is_active=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0006_add_product_image_model"),
    ]

    operations = [
        migrations.RunPython(seed_products, migrations.RunPython.noop),
    ]
