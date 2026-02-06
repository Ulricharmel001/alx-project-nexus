import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django_ratelimit.decorators import ratelimit

from products.models import Product


@ratelimit(key="ip", rate="5/m", block=True)
def checkout_view(request):
    if request.method == "POST":
        return JsonResponse(
            {"status": "success", "message": "Checkout processed successfully"}
        )
    else:
        return render(request, "checkout.html")


@ratelimit(key="ip", rate="10/m", block=True)
def login_view(request):
    if request.method == "POST":
        return JsonResponse({"status": "success", "message": "Login processed"})
    else:
        return render(request, "login.html")


@login_required
@ratelimit(key="ip", rate="20/m", block=True)
def account_view(request):
    return render(request, "account.html")


@ratelimit(key="ip", rate="30/m", block=True)
def product_detail_view(request, product_id):
    try:
        uuid_obj = uuid.UUID(product_id)
        product = get_object_or_404(Product, id=uuid_obj)
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid product ID"})

    return render(request, "product_detail.html", {"product": product})


@ratelimit(key="ip", rate="15/m", block=True)
def add_to_cart_view(request, product_id):
    try:
        uuid_obj = uuid.UUID(product_id)
        product = get_object_or_404(Product, id=uuid_obj)
        return JsonResponse(
            {"status": "success", "message": f"Added {product.name} to cart"}
        )
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid product ID"})


@ratelimit(key="ip", rate="20/m", block=True)
def apply_coupon_view(request):
    if request.method == "POST":
        return JsonResponse({"status": "success", "message": "Coupon applied"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"})
