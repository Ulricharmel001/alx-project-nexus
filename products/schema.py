import graphene
from graphene_django import DjangoObjectType

from accounts.models import CustomUser

from .models import (Address, Category, Inventory, Order, OrderItem, Payment,
                     Product, Review)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ("id", "name", "parent", "created_at", "updated_at", "is_active")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = (
            "id",
            "categories",
            "name",
            "description",
            "slug",
            "price",
            "currency",
            "is_active",
            "created_at",
            "updated_at",
        )


class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        fields = (
            "id",
            "customer",
            "street",
            "city",
            "state",
            "country",
            "postal_code",
            "is_default",
            "created_at",
            "updated_at",
        )


class InventoryType(DjangoObjectType):
    class Meta:
        model = Inventory
        fields = (
            "id",
            "product",
            "quantity",
            "reserved_quantity",
            "created_at",
            "updated_at",
        )

    def resolve_available_quantity(self, info):
        return self.available_quantity()


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "shipping_address",
            "status",
            "total_price",
            "currency",
            "created_at",
            "updated_at",
        )


class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "order",
            "product",
            "quantity",
            "unit_price_at_purchase",
            "subtotal",
            "created_at",
            "updated_at",
        )


class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "provider",
            "amount",
            "currency",
            "status",
            "transaction_reference",
            "payment_date",
            "payment_method",
            "payment_details",
            "created_at",
            "updated_at",
        )


class ReviewType(DjangoObjectType):
    class Meta:
        model = Review
        fields = (
            "id",
            "title",
            "content",
            "product",
            "customer",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )


class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, id=graphene.ID(required=True))

    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))

    addresses = graphene.List(AddressType)
    address = graphene.Field(AddressType, id=graphene.ID(required=True))

    inventories = graphene.List(InventoryType)
    inventory = graphene.Field(InventoryType, id=graphene.ID(required=True))

    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    payments = graphene.List(PaymentType)
    payment = graphene.Field(PaymentType, id=graphene.ID(required=True))

    reviews = graphene.List(ReviewType)
    review = graphene.Field(ReviewType, id=graphene.ID(required=True))

    def resolve_categories(self, info):
        return Category.objects.all()

    def resolve_category(self, info, id):
        return Category.objects.get(pk=id)

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_product(self, info, id):
        return Product.objects.get(pk=id)

    def resolve_addresses(self, info):
        return Address.objects.all()

    def resolve_address(self, info, id):
        return Address.objects.get(pk=id)

    def resolve_inventories(self, info):
        return Inventory.objects.all()

    def resolve_inventory(self, info, id):
        return Inventory.objects.get(pk=id)

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_order(self, info, id):
        return Order.objects.get(pk=id)

    def resolve_payments(self, info):
        return Payment.objects.all()

    def resolve_payment(self, info, id):
        return Payment.objects.get(pk=id)

    def resolve_reviews(self, info):
        return Review.objects.all()

    def resolve_review(self, info, id):
        return Review.objects.get(pk=id)


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        currency = graphene.String(default_value="CFA")
        category_ids = graphene.List(graphene.ID)

    def mutate(self, info, name, description, price, currency, category_ids=None):
        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            currency=currency,
            slug=name.lower().replace(" ", "-"),
        )

        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            product.categories.set(categories)

        return CreateProduct(
            product=product, success=True, message="Product created successfully"
        )


class CreateCategory(graphene.Mutation):
    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        parent_id = graphene.ID()

    def mutate(self, info, name, parent_id=None):
        parent = None
        if parent_id:
            parent = Category.objects.get(pk=parent_id)

        category = Category.objects.create(name=name, parent=parent)
        return CreateCategory(
            category=category, success=True, message="Category created successfully"
        )


class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
    create_category = CreateCategory.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
