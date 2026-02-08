from django.core.management.base import BaseCommand

from products.data_seeder import DataSeeder


class Command(BaseCommand):
    help = "Seed the database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=100, help="Number of users to create"
        )
        parser.add_argument(
            "--categories", type=int, default=20, help="Number of categories to create"
        )
        parser.add_argument(
            "--products", type=int, default=1000, help="Number of products to create"
        )
        parser.add_argument(
            "--orders", type=int, default=500, help="Number of orders to create"
        )
        parser.add_argument(
            "--order-items",
            type=int,
            default=2000,
            help="Number of order items to create",
        )
        parser.add_argument(
            "--purchases", type=int, default=400, help="Number of purchases to create"
        )
        parser.add_argument(
            "--reviews", type=int, default=300, help="Number of reviews to create"
        )

    def handle(self, *args, **options):
        seeder = DataSeeder()
        seeder.run_seeding(
            users_count=options["users"],
            categories_count=options["categories"],
            products_count=options["products"],
            orders_count=options["orders"],
            order_items_count=options["order_items"],
            purchases_count=options["purchases"],
            reviews_count=options["reviews"],
        )
        self.stdout.write(
            self.style.SUCCESS("Successfully seeded the database with test data!")
        )
