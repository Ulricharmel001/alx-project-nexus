from decimal import Decimal

from django.db import migrations
from django.utils.text import slugify


def seed_products(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")
    Inventory = apps.get_model("products", "Inventory")

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
            50,
        ),
        (
            "Wireless Headphones",
            "Noise-cancelling Bluetooth headphones with 30-hour battery life",
            149.99,
            "USD",
            100,
        ),
        (
            "Smart Watch Pro",
            "Fitness tracking smartwatch with heart rate monitor and GPS",
            259.99,
            "USD",
            75,
        ),
        (
            "USB-C Hub 7-in-1",
            "Multi-port adapter with HDMI, USB 3.0, SD card reader",
            39.99,
            "USD",
            200,
        ),
        (
            "Mechanical Keyboard RGB",
            "Cherry MX switches with per-key RGB backlighting",
            119.99,
            "USD",
            60,
        ),
        (
            "Ergonomic Mouse Vertical",
            "Wireless vertical mouse for reduced wrist strain",
            34.99,
            "USD",
            150,
        ),
        (
            "4K Webcam Pro",
            "Ultra HD webcam with auto-focus and built-in microphone",
            89.99,
            "USD",
            80,
        ),
        (
            "Portable Bluetooth Speaker",
            "Waterproof speaker with 360-degree sound",
            59.99,
            "USD",
            120,
        ),
        (
            "Laptop Stand Aluminum",
            "Adjustable ergonomic laptop stand, fits 10-17 inch laptops",
            45.99,
            "USD",
            90,
        ),
        (
            "Noise Cancelling Earbuds",
            "True wireless earbuds with active noise cancellation",
            79.99,
            "USD",
            110,
        ),
        (
            "External SSD 1TB",
            "Portable solid state drive with USB-C, read speeds up to 1050MB/s",
            109.99,
            "USD",
            70,
        ),
    ]

    for name, desc, price, currency, stock_qty in products_data:
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        product = Product.objects.create(
            name=name,
            description=desc,
            slug=slug,
            price=Decimal(str(price)),
            currency=currency,
            is_active=True,
        )
        Inventory.objects.create(product=product, quantity=stock_qty)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0006_add_product_image_model"),
    ]

    operations = [
        migrations.RunPython(seed_products, migrations.RunPython.noop),
    ]
