from decimal import Decimal
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .chapa_service import ChapaService
from .models import (Address, Cart, CartItem, Category, Inventory, Order,
                     OrderItem, Product, Purchase, PurchaseVerification,
                     Review)
from .serializers import (CategorySerializer, InventorySerializer,
                          OrderItemSerializer, ProductSerializer,
                          PurchaseSerializer, ReviewSerializer)

TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

TEST_REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class CategoryTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:product-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.category = Category.objects.create(name="Electronics")

    def test_list_categories_unauthenticated(self):
        url = reverse("products:categories-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("products:categories-list")
        response = self.client.post(url, {"name": "Books"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Books")

    def test_create_category_unauthenticated(self):
        url = reverse("products:categories-list")
        response = self.client.post(url, {"name": "Books"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_category_detail(self):
        url = reverse("products:categories-detail", args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Electronics")

    def test_category_tree(self):
        child = Category.objects.create(name="Phones", parent=self.category)
        url = reverse("products:category-tree")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]["children"]), 1)
        self.assertEqual(response.data[0]["children"][0]["name"], "Phones")

    def test_update_category(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("products:categories-detail", args=[self.category.id])
        response = self.client.patch(
            url, {"name": "Updated Electronics"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Electronics")

    def test_delete_category(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("products:categories-detail", args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class ProductTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:product-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            slug="laptop",
            price=999.99,
        )
        self.product.categories.add(self.category)

    def test_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_product_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.list_url,
            {
                "name": "Mouse",
                "description": "Wireless mouse",
                "slug": "wireless-mouse",
                "price": 49.99,
                "categories": [str(self.category.id)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Mouse")

    def test_create_product_unauthenticated(self):
        response = self.client.post(
            self.list_url,
            {
                "name": "Mouse",
                "description": "Wireless",
                "slug": "mouse",
                "price": 49.99,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_detail(self):
        url = reverse("products:product-detail", args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Laptop")

    def test_product_search(self):
        url = reverse("products:product-search")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, {"q": "Laptop"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_product_search_empty(self):
        url = reverse("products:product-search")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, {"q": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_product_search_no_match(self):
        url = reverse("products:product-search")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, {"q": "Nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_update_product(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("products:product-detail", args=[self.product.id])
        response = self.client.patch(url, {"price": 899.99}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["price"]), "899.99")

    def test_delete_product(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("products:product-detail", args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_product_price_validation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.list_url,
            {
                "name": "Free Item",
                "description": "Should fail",
                "slug": "free-item",
                "price": 0,
                "categories": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class AddressTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:address-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )
        self.client.force_authenticate(user=self.user)

    def test_list_addresses(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_addresses_only_own(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_create_address(self):
        response = self.client.post(
            self.list_url,
            {
                "street": "456 Oak Ave",
                "city": "Yaounde",
                "state": "Centre",
                "country": "Cameroon",
                "postal_code": "67890",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_address_detail_only_own(self):
        url = reverse("products:address-detail", args=[self.address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_other_users_address(self):
        other_address = Address.objects.create(
            customer=self.other_user,
            street="999 Other St",
            city="Buea",
            state="SW",
            country="Cameroon",
            postal_code="00000",
        )
        url = reverse("products:address-detail", args=[other_address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_address(self):
        url = reverse("products:address-detail", args=[self.address.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=999.99,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=10)
        self.client.force_authenticate(user=self.user)

    def test_get_cart_creates_if_not_exists(self):
        url = reverse("products:cart")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Cart.objects.filter(customer=self.user).exists())

    def test_add_to_cart(self):
        url = reverse("products:add-to-cart")
        response = self.client.post(
            url,
            {"product_id": str(self.product.id), "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        cart = Cart.objects.get(customer=self.user)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_increments_existing(self):
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=1, created_by=self.user
        )
        url = reverse("products:add-to-cart")
        response = self.client.post(
            url,
            {"product_id": str(self.product.id), "quantity": 3},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 4)

    def test_add_to_cart_no_product_id(self):
        url = reverse("products:add-to-cart")
        response = self.client.post(url, {"quantity": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_to_cart_nonexistent_product(self):
        url = reverse("products:add-to-cart")
        response = self.client.post(
            url,
            {"product_id": "00000000-0000-0000-0000-000000000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_to_cart_insufficient_inventory(self):
        url = reverse("products:add-to-cart")
        response = self.client.post(
            url,
            {"product_id": str(self.product.id), "quantity": 100},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_total_price(self):
        product2 = Product.objects.create(
            name="Mouse", description="A mouse", slug="mouse", price=49.99
        )
        Inventory.objects.create(product=product2, quantity=10)
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, created_by=self.user
        )
        CartItem.objects.create(
            cart=cart, product=product2, quantity=1, created_by=self.user
        )
        expected = Decimal("2049.97")
        self.assertEqual(cart.total_price, expected)

    def test_remove_from_cart(self):
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart, product=self.product, quantity=1, created_by=self.user
        )
        url = reverse("products:remove-from-cart", args=[item.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_remove_nonexistent_item(self):
        url = reverse(
            "products:remove-from-cart", args=["00000000-0000-0000-0000-000000000000"]
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_cart_item_quantity(self):
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart, product=self.product, quantity=1, created_by=self.user
        )
        url = reverse("products:update-cart-item", args=[item.id])
        response = self.client.post(url, {"quantity": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_update_cart_item_removes_if_zero(self):
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart, product=self.product, quantity=1, created_by=self.user
        )
        url = reverse("products:update-cart-item", args=[item.id])
        response = self.client.post(url, {"quantity": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_clear_cart(self):
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, created_by=self.user
        )
        url = reverse("products:clear-cart")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cart.items.count(), 0)

    def test_cart_items_list(self):
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=1, created_by=self.user
        )
        url = reverse("products:cart-items-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_unauthenticated_cart_access(self):
        self.client.force_authenticate(user=None)
        url = reverse("products:cart")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class CheckoutTests(APITestCase):
    def setUp(self):
        self.url = reverse("products:checkout")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=999.99,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=10)
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )
        self.client.force_authenticate(user=self.user)
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2, created_by=self.user
        )

    def test_checkout_success(self):
        response = self.client.post(
            self.url, {"shipping_address_id": str(self.address.id)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("order", response.data)
        self.assertEqual(response.data["order"]["status"], "pending")
        self.assertEqual(str(response.data["order"]["total_price"]), "1999.98")
        self.assertFalse(Cart.objects.get(customer=self.user).items.exists())

    def test_checkout_empty_cart(self):
        Cart.objects.get(customer=self.user).items.all().delete()
        response = self.client.post(
            self.url, {"shipping_address_id": str(self.address.id)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_no_address(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_invalid_address(self):
        response = self.client.post(
            self.url,
            {"shipping_address_id": "00000000-0000-0000-0000-000000000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_checkout_creates_order_items(self):
        response = self.client.post(
            self.url, {"shipping_address_id": str(self.address.id)}, format="json"
        )
        order_id = response.data["order"]["id"]
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price_at_purchase, Decimal("999.99"))

    def test_checkout_reserves_inventory(self):
        response = self.client.post(
            self.url, {"shipping_address_id": str(self.address.id)}, format="json"
        )
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.reserved_quantity, 2)

    def test_checkout_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url, {"shipping_address_id": str(self.address.id)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class OrderTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:order-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        self.product = Product.objects.create(
            name="Laptop", description="A laptop", slug="laptop", price=999.99
        )
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )
        self.order = Order.objects.create(
            customer=self.user,
            shipping_address=self.address,
            total_price=999.99,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_orders(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_orders_only_own(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_order_detail(self):
        url = reverse("products:order-detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["total_price"]), "999.99")

    def test_cannot_access_other_users_order(self):
        url = reverse("products:order-detail", args=[self.order.id])
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_sees_all_orders(self):
        staff = User.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_order(self):
        response = self.client.post(
            self.list_url,
            {
                "shipping_address": str(self.address.id),
                "total_price": 199.99,
                "currency": "CFA",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class ReviewTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:reviews-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=999.99,
        )
        self.client.force_authenticate(user=self.user)

    def test_create_review(self):
        response = self.client.post(
            self.list_url,
            {
                "product": str(self.product.id),
                "rating": 5,
                "title": "Great!",
                "comment": "Excellent product",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 5)

    def test_create_review_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.list_url,
            {
                "product": str(self.product.id),
                "rating": 4,
                "comment": "Good",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unique_review_per_product(self):
        Review.objects.create(
            product=self.product,
            customer=self.user,
            rating=5,
            comment="First review",
        )
        response = self.client.post(
            self.list_url,
            {
                "product": str(self.product.id),
                "rating": 3,
                "comment": "Second review",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_rating_validation(self):
        response = self.client.post(
            self.list_url,
            {
                "product": str(self.product.id),
                "rating": 10,
                "comment": "Invalid rating",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_reviews(self):
        Review.objects.create(
            product=self.product,
            customer=self.user,
            rating=4,
            comment="Nice",
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_delete_review(self):
        review = Review.objects.create(
            product=self.product,
            customer=self.user,
            rating=3,
            comment="Okay",
        )
        url = reverse("products:reviews-detail", args=[review.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class InventoryTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("products:inventory-list")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=999.99,
        )
        self.inventory = Inventory.objects.create(product=self.product, quantity=10)
        self.client.force_authenticate(user=self.user)

    def test_list_inventory(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_inventory_detail(self):
        url = reverse("products:inventory-detail", args=[self.inventory.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 10)

    def test_available_quantity(self):
        self.inventory.reserved_quantity = 3
        self.inventory.save()
        self.assertEqual(self.inventory.available_quantity(), 7)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=TEST_CACHES, REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class PaymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=500.00,
        )
        Inventory.objects.create(product=self.product, quantity=10)
        self.order = Order.objects.create(
            customer=self.user,
            shipping_address=self.address,
            total_price=500.00,
        )
        self.client.force_authenticate(user=self.user)

    @patch("products.views.ChapaService.initiate_payment")
    def test_initiate_payment_success(self, mock_initiate):
        mock_initiate.return_value = {
            "status": "success",
            "data": {"checkout_url": "https://checkout.chapa.co/test"},
        }
        url = reverse("products:purchase-list")
        response = self.client.post(
            url,
            {
                "order_id": str(self.order.id),
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("checkout_url", response.data)
        self.assertIn("tx_ref", response.data)
        self.assertIn("purchase_id", response.data)
        self.assertTrue(
            Purchase.objects.filter(
                transaction_reference=response.data["tx_ref"]
            ).exists()
        )

    def test_initiate_payment_missing_fields(self):
        url = reverse("products:purchase-list")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_initiate_payment_invalid_order(self):
        url = reverse("products:purchase-list")
        response = self.client.post(
            url,
            {
                "order_id": "00000000-0000-0000-0000-000000000000",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_initiate_payment_order_already_paid(self):
        self.order.status = "paid"
        self.order.save()
        url = reverse("products:purchase-list")
        response = self.client.post(
            url,
            {
                "order_id": str(self.order.id),
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("products.views.ChapaService.initiate_payment")
    def test_initiate_payment_chapa_fails(self, mock_initiate):
        mock_initiate.return_value = {"status": "error", "message": "Auth failed"}
        url = reverse("products:purchase-list")
        response = self.client.post(
            url,
            {
                "order_id": str(self.order.id),
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("products.chapa_service.ChapaService.verify_payment")
    @patch("products.tasks.generate_and_send_receipt_email.delay")
    def test_verify_payment_success(self, mock_receipt, mock_verify):
        mock_verify.return_value = {
            "status": "success",
            "data": {"status": "completed"},
        }
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="pending",
            transaction_reference="TX-TEST1234ABCD",
            created_by=self.user,
        )
        url = reverse("products:purchase-verify-payment", args=["TX-TEST1234ABCD"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, "completed")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertTrue(
            PurchaseVerification.objects.filter(
                purchase=purchase, is_verified=True
            ).exists()
        )
        mock_receipt.assert_called_once_with(str(purchase.id))

    @patch("products.chapa_service.ChapaService.verify_payment")
    def test_verify_payment_failed(self, mock_verify):
        mock_verify.return_value = {
            "status": "success",
            "data": {"status": "failed"},
        }
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="pending",
            transaction_reference="TX-TESTFAILED",
            created_by=self.user,
        )
        url = reverse("products:purchase-verify-payment", args=["TX-TESTFAILED"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, "failed")

    @patch("products.chapa_service.ChapaService.verify_payment")
    def test_verify_payment_api_error(self, mock_verify):
        mock_verify.return_value = {"status": "error", "message": "Not found"}
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="pending",
            transaction_reference="TX-APIERROR",
            created_by=self.user,
        )
        url = reverse("products:purchase-verify-payment", args=["TX-APIERROR"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, "failed")

    def test_verify_payment_not_found(self):
        url = reverse("products:purchase-verify-payment", args=["TX-NONEXISTENT"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("products.cart_service.ChapaService.initiate_payment")
    def test_payment_test_endpoint(self, mock_initiate):
        mock_initiate.return_value = {
            "status": "success",
            "data": {"checkout_url": "https://checkout.chapa.co/test"},
        }
        url = reverse("products:payment-test")
        response = self.client.post(
            url,
            {"order_id": str(self.order.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("checkout_url", response.data)

    def test_purchase_list_only_own(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        other_address = Address.objects.create(
            customer=other_user,
            street="999 Other St",
            city="Buea",
            state="SW",
            country="Cameroon",
            postal_code="00000",
        )
        other_order = Order.objects.create(
            customer=other_user,
            shipping_address=other_address,
            total_price=100.00,
        )
        Purchase.objects.create(
            order=other_order,
            provider="chapa",
            amount=100.00,
            status="pending",
            created_by=other_user,
        )
        url = reverse("products:purchase-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_purchase_model_str(self):
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="pending",
            created_by=self.user,
        )
        self.assertIn(str(self.order.id), str(purchase))
        self.assertIn("pending", str(purchase))


class CeleryTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=500.00,
        )
        self.order = Order.objects.create(
            customer=self.user,
            shipping_address=self.address,
            total_price=500.00,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price_at_purchase=500.00,
            subtotal=500.00,
        )

    @patch("products.tasks.generate_pdf_receipt")
    @patch("products.tasks.EmailMultiAlternatives")
    def test_generate_and_send_receipt_email(self, mock_email, mock_generate_pdf):
        from io import BytesIO

        mock_generate_pdf.return_value = BytesIO(b"fake-pdf-content")

        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="completed",
            transaction_reference="TX-RECEIPTTEST",
            created_by=self.user,
        )

        from products.tasks import generate_and_send_receipt_email

        result = generate_and_send_receipt_email(str(purchase.id))
        self.assertTrue(result)
        mock_generate_pdf.assert_called_once()

    @patch("products.tasks.generate_pdf_receipt")
    def test_generate_receipt_for_non_completed_purchase(self, mock_generate_pdf):
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="pending",
            transaction_reference="TX-PENDINGTEST",
            created_by=self.user,
        )
        from products.tasks import generate_and_send_receipt_email

        result = generate_and_send_receipt_email(str(purchase.id))
        self.assertFalse(result)
        mock_generate_pdf.assert_not_called()

    def test_generate_receipt_nonexistent_purchase(self):
        from products.tasks import generate_and_send_receipt_email

        result = generate_and_send_receipt_email("00000000-0000-0000-0000-000000000000")
        self.assertFalse(result)

    @patch("products.tasks.generate_pdf_receipt", side_effect=Exception("PDF error"))
    def test_generate_receipt_pdf_error(self, mock_generate_pdf):
        purchase = Purchase.objects.create(
            order=self.order,
            provider="chapa",
            amount=500.00,
            status="completed",
            transaction_reference="TX-PDFERROR",
            created_by=self.user,
        )
        from products.tasks import generate_and_send_receipt_email

        result = generate_and_send_receipt_email(str(purchase.id))
        self.assertFalse(result)


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.address = Address.objects.create(
            customer=self.user,
            street="123 Main St",
            city="Douala",
            state="Littoral",
            country="Cameroon",
            postal_code="12345",
        )

    def test_order_status_choices(self):
        for status_value, _ in Order.ORDER_STATUS:
            order = Order.objects.create(
                customer=self.user,
                shipping_address=self.address,
                total_price=100.00,
                status=status_value,
            )
            self.assertEqual(order.status, status_value)

    def test_order_str(self):
        order = Order.objects.create(
            customer=self.user,
            shipping_address=self.address,
            total_price=99.99,
        )
        self.assertIn(str(order.id), str(order))


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Cat")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            slug="test-product",
            price=29.99,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Test Cat")

    def test_address_str(self):
        user = User.objects.create_user(
            email="addr@example.com",
            password="testpass123",
            first_name="Addr",
            last_name="User",
        )
        address = Address.objects.create(
            customer=user,
            street="10 Downing St",
            city="London",
            state="England",
            country="UK",
            postal_code="SW1A",
        )
        self.assertIn("10 Downing St", str(address))
        self.assertIn("London", str(address))

    def test_inventory_str(self):
        inventory = Inventory.objects.create(product=self.product, quantity=5)
        self.assertIn("Test Product", str(inventory))
        self.assertIn("5", str(inventory))

    def test_review_str(self):
        user = User.objects.create_user(
            email="reviewer@example.com",
            password="testpass123",
            first_name="Rev",
            last_name="User",
        )
        review = Review.objects.create(
            product=self.product,
            customer=user,
            rating=4,
            comment="Good",
        )
        self.assertIn("Test Product", str(review))
        self.assertIn(str(user), str(review))


# ===========================
# 🧪 Serializer Validation Tests
# ===========================
class SerializerValidationTests(TestCase):
    """Direct tests for serializer field validators"""

    def test_product_serializer_price_zero_invalid(self):
        """❌ Price of 0 should fail validation"""
        serializer = ProductSerializer(
            data={
                "name": "Free Item",
                "description": "Should fail",
                "slug": "free-item",
                "price": 0,
                "categories": [],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_product_serializer_price_negative_invalid(self):
        """❌ Negative price should fail validation"""
        serializer = ProductSerializer(
            data={
                "name": "Negative",
                "description": "Should fail",
                "slug": "negative",
                "price": -10,
                "categories": [],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_order_item_serializer_quantity_zero_invalid(self):
        """❌ Quantity of 0 should fail validation"""
        serializer = OrderItemSerializer(
            data={
                "product": "00000000-0000-0000-0000-000000000000",
                "quantity": 0,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_purchase_serializer_amount_zero_invalid(self):
        """❌ Amount of 0 should fail validation"""
        serializer = PurchaseSerializer(
            data={
                "order": "00000000-0000-0000-0000-000000000000",
                "amount": 0,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_purchase_serializer_currency_uppercased(self):
        """✅ Currency is uppercased on validation"""
        serializer = PurchaseSerializer()
        result = serializer.validate_currency("etb")
        self.assertEqual(result, "ETB")

        result = serializer.validate_currency("Cfa")
        self.assertEqual(result, "CFA")

    def test_review_serializer_rating_above_5_invalid(self):
        """❌ Rating > 5 should fail"""
        serializer = ReviewSerializer(
            data={
                "product": "00000000-0000-0000-0000-000000000000",
                "rating": 6,
                "comment": "Too high",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_review_serializer_rating_below_1_invalid(self):
        """❌ Rating < 1 should fail"""
        serializer = ReviewSerializer(
            data={
                "product": "00000000-0000-0000-0000-000000000000",
                "rating": 0,
                "comment": "Too low",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_category_serializer_children_field(self):
        """✅ Category serializer includes nested children"""
        parent = Category.objects.create(name="Parent Cat")
        child = Category.objects.create(name="Child Cat", parent=parent)
        serializer = CategorySerializer(parent)
        self.assertIn("children", serializer.data)
        self.assertEqual(len(serializer.data["children"]), 1)
        self.assertEqual(serializer.data["children"][0]["name"], "Child Cat")

    def test_category_serializer_no_children(self):
        """✅ Category with no children returns empty list"""
        cat = Category.objects.create(name="Lonely Cat")
        serializer = CategorySerializer(cat)
        self.assertEqual(serializer.data["children"], [])


# ===========================
# 🧪 ChapaService Unit Tests
# ===========================
class ChapaServiceTests(TestCase):
    """Direct unit tests for products/chapa_service.py"""

    @patch("products.chapa_service.requests.post")
    def test_initiate_payment_success(self, mock_post):
        """✅ Payment initiation returns checkout URL"""
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "status": "success",
            "data": {"checkout_url": "https://checkout.chapa.co/test"},
        }
        mock_response.raise_for_status.return_value = None
        service = ChapaService()
        result = service.initiate_payment(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            amount=100.00,
            tx_ref="TX-TEST123",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("checkout_url", result["data"])

    @patch(
        "products.chapa_service.requests.post",
        side_effect=requests.exceptions.RequestException("Connection refused"),
    )
    def test_initiate_payment_network_error(self, mock_post):
        """❌ Network error returns error status"""
        service = ChapaService()
        result = service.initiate_payment(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            amount=100.00,
            tx_ref="TX-FAIL",
        )
        self.assertEqual(result["status"], "error")

    @patch("products.chapa_service.requests.get")
    def test_verify_payment_success(self, mock_get):
        """✅ Payment verification returns status"""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "status": "success",
            "data": {"status": "completed"},
        }
        mock_response.raise_for_status.return_value = None
        service = ChapaService()
        result = service.verify_payment("TX-TEST123")
        self.assertEqual(result["status"], "success")

    @patch(
        "products.chapa_service.requests.get",
        side_effect=requests.exceptions.RequestException("Not found"),
    )
    def test_verify_payment_network_error(self, mock_get):
        """❌ Network error during verification returns error"""
        service = ChapaService()
        result = service.verify_payment("TX-INVALID")
        self.assertEqual(result["status"], "error")


# ===========================
# 🧪 Additional Model Tests
# ===========================
class ExtraModelTests(TestCase):
    """Model edge cases and properties"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="test12345",
            first_name="Test",
            last_name="User",
        )
        self.product = Product.objects.create(
            name="Laptop",
            description="A laptop",
            slug="laptop",
            price=Decimal("999.99"),
        )

    def test_cart_item_subtotal_property(self):
        """✅ CartItem.subtotal = quantity * product.price"""
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=3,
            created_by=self.user,
        )
        expected = Decimal("2999.97")  # 3 * 999.99
        self.assertEqual(item.subtotal, expected)

    def test_cart_item_subtotal_updates_with_quantity(self):
        """✅ CartItem.subtotal changes when quantity changes"""
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            created_by=self.user,
        )
        self.assertEqual(item.subtotal, Decimal("1999.98"))
        # Change quantity
        item.quantity = 5
        item.save()
        self.assertEqual(item.subtotal, Decimal("4999.95"))

    def test_cart_item_str(self):
        """✅ CartItem.__str__ contains product name and quantity"""
        cart = Cart.objects.create(customer=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            created_by=self.user,
        )
        self.assertIn("Laptop", str(item))
        self.assertIn("2", str(item))

    def test_order_item_str(self):
        """✅ OrderItem.__str__ contains product and order info"""
        address = Address.objects.create(
            customer=self.user,
            street="123 St",
            city="City",
            state="State",
            country="Country",
            postal_code="12345",
        )
        order = Order.objects.create(
            customer=self.user,
            shipping_address=address,
            total_price=999.99,
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price_at_purchase=999.99,
            subtotal=999.99,
        )
        self.assertIn("Laptop", str(item))
        self.assertIn(str(order.id), str(item))

    def test_purchase_str(self):
        """✅ Purchase.__str__ contains order ID and status"""
        address = Address.objects.create(
            customer=self.user,
            street="123 St",
            city="City",
            state="State",
            country="Country",
            postal_code="12345",
        )
        order = Order.objects.create(
            customer=self.user,
            shipping_address=address,
            total_price=500.00,
        )
        purchase = Purchase.objects.create(
            order=order,
            provider="chapa",
            amount=500.00,
            status="pending",
            created_by=self.user,
        )
        self.assertIn(str(order.id), str(purchase))
        self.assertIn("pending", str(purchase))

    def test_purchase_verification_str(self):
        """✅ PurchaseVerification.__str__ shows verification status"""
        address = Address.objects.create(
            customer=self.user,
            street="123 St",
            city="City",
            state="State",
            country="Country",
            postal_code="12345",
        )
        order = Order.objects.create(
            customer=self.user,
            shipping_address=address,
            total_price=500.00,
        )
        purchase = Purchase.objects.create(
            order=order,
            provider="chapa",
            amount=500.00,
            status="completed",
            created_by=self.user,
        )
        verification = PurchaseVerification.objects.create(
            purchase=purchase,
            is_verified=True,
            created_by=self.user,
        )
        self.assertIn("Verified: True", str(verification))

    def test_purchase_verification_str_not_verified(self):
        """✅ PurchaseVerification shows False when not verified"""
        address = Address.objects.create(
            customer=self.user,
            street="123 St",
            city="City",
            state="State",
            country="Country",
            postal_code="12345",
        )
        order = Order.objects.create(
            customer=self.user,
            shipping_address=address,
            total_price=500.00,
        )
        purchase = Purchase.objects.create(
            order=order,
            provider="chapa",
            amount=500.00,
            status="pending",
            created_by=self.user,
        )
        verification = PurchaseVerification.objects.create(
            purchase=purchase,
            is_verified=False,
            created_by=self.user,
        )
        self.assertIn("Verified: False", str(verification))

    def test_inventory_available_quantity_no_reservation(self):
        """✅ available_quantity = quantity when nothing reserved"""
        inventory = Inventory.objects.create(product=self.product, quantity=10)
        self.assertEqual(inventory.available_quantity(), 10)

    def test_inventory_available_quantity_with_reservation(self):
        """✅ available_quantity = quantity - reserved_quantity"""
        inventory = Inventory.objects.create(
            product=self.product, quantity=10, reserved_quantity=3
        )
        self.assertEqual(inventory.available_quantity(), 7)
