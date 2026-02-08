import threading
import time

from django.core.management.base import BaseCommand

from products.data_seeder import DataSeeder


class Command(BaseCommand):
    help = "Bulk seed the database with millions of records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=1000, help="Number of users to create"
        )
        parser.add_argument(
            "--products", type=int, default=10000, help="Number of products to create"
        )
        parser.add_argument(
            "--orders", type=int, default=5000, help="Number of orders to create"
        )
        parser.add_argument(
            "--reviews", type=int, default=20000, help="Number of reviews to create"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk operations",
        )

    def handle(self, *args, **options):
        # Create multiple threads to speed up the process
        seeder = DataSeeder()

        # Run seeding in batches to avoid memory issues
        total_users = options["users"]
        total_products = options["products"]
        total_orders = options["orders"]
        total_reviews = options["reviews"]
        batch_size = options["batch_size"]

        self.stdout.write(
            f"Starting bulk seeding: {total_users} users, {total_products} products, {total_orders} orders, {total_reviews} reviews"
        )

        # Seed in phases to respect foreign key constraints
        start_time = time.time()

        # Phase 1: Categories (just once)
        self.stdout.write("Phase 1: Seeding categories...")
        seeder.seed_categories(100)

        # Phase 2: Users in batches
        self.stdout.write("Phase 2: Seeding users in batches...")
        for i in range(0, total_users, batch_size):
            batch_end = min(i + batch_size, total_users)
            seeder.seed_users(batch_end - i)
            self.stdout.write(f"  Seeded {batch_end}/{total_users} users...")

        # Phase 3: Products in batches
        self.stdout.write("Phase 3: Seeding products in batches...")
        for i in range(0, total_products, batch_size):
            batch_end = min(i + batch_size, total_products)
            seeder.seed_products(batch_end - i)
            self.stdout.write(f"  Seeded {batch_end}/{total_products} products...")

        # Phase 4: Inventories
        self.stdout.write("Phase 4: Seeding inventories...")
        seeder.seed_inventories()

        # Phase 5: Addresses
        self.stdout.write("Phase 5: Seeding addresses...")
        seeder.seed_addresses(
            min(1000, len(seeder.users))
        )  # Limit addresses to avoid too many

        # Phase 6: Orders in smaller batches
        self.stdout.write("Phase 6: Seeding orders in batches...")
        for i in range(0, total_orders, batch_size // 2):  # Smaller batch for orders
            batch_end = min(i + batch_size // 2, total_orders)
            seeder.seed_orders(batch_end - i)
            self.stdout.write(f"  Seeded {batch_end}/{total_orders} orders...")

        # Phase 7: Order items (these will be many!)
        self.stdout.write("Phase 7: Seeding order items...")
        # Calculate roughly how many order items we need based on orders
        avg_items_per_order = 4  # Average number of items per order
        total_order_items = total_orders * avg_items_per_order
        for i in range(0, total_order_items, batch_size):
            batch_end = min(i + batch_size, total_order_items)
            seeder.seed_order_items(batch_end - i)
            self.stdout.write(
                f"  Seeded {batch_end}/{total_order_items} order items..."
            )

        # Phase 8: Purchases
        self.stdout.write("Phase 8: Seeding purchases...")
        seeder.seed_purchases(
            min(total_orders, 4000)
        )  # Limit purchases to match orders

        # Phase 9: Reviews in batches
        self.stdout.write("Phase 9: Seeding reviews in batches...")
        for i in range(0, total_reviews, batch_size):
            batch_end = min(i + batch_size, total_reviews)
            seeder.seed_reviews(batch_end - i)
            self.stdout.write(f"  Seeded {batch_end}/{total_reviews} reviews...")

        # Phase 10: Purchase verifications
        self.stdout.write("Phase 10: Seeding purchase verifications...")
        seeder.seed_purchase_verifications()

        end_time = time.time()

        self.stdout.write(
            self.style.SUCCESS(
                f"Bulk seeding completed in {end_time - start_time:.2f} seconds!"
            )
        )

        # Print summary
        from accounts.models import CustomUser
        from products.models import (Category, Inventory, Order, OrderItem,
                                     Product, Purchase, PurchaseVerification,
                                     Review)

        self.stdout.write("\nFinal Summary:")
        self.stdout.write(f"- Users: {CustomUser.objects.count():,}")
        self.stdout.write(f"- Categories: {Category.objects.count():,}")
        self.stdout.write(f"- Products: {Product.objects.count():,}")
        self.stdout.write(f"- Inventories: {Inventory.objects.count():,}")
        self.stdout.write(f"- Orders: {Order.objects.count():,}")
        self.stdout.write(f"- Order Items: {OrderItem.objects.count():,}")
        self.stdout.write(f"- Purchases: {Purchase.objects.count():,}")
        self.stdout.write(f"- Reviews: {Review.objects.count():,}")
        self.stdout.write(
            f"- Purchase Verifications: {PurchaseVerification.objects.count():,}"
        )
