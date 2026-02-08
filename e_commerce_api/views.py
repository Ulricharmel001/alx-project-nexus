from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    """
    Home view for the e-commerce API
    """
    return HttpResponse(
        "<h1>Welcome to the E-Commerce API</h1>"
        "<p>This is the home page of the API.</p>"
        "<p>Available endpoints:</p>"
        "<ul>"
        "<li><a href='/admin/'>Admin Panel</a></li>"
        "<li><a href='/api/v1/accounts/'>Accounts API</a></li>"
        "<li><a href='/api/v1/products/'>Products API</a></li>"
        "<li><a href='/swagger/'>Swagger Documentation</a></li>"
        "<li><a href='/redoc/'>ReDoc Documentation</a></li>"
        "<li><a href='/graphql/'>GraphQL Interface</a></li>"
        "</ul>"
    )


def health_check(request):
    """
    Simple health check endpoint
    """
    return HttpResponse("OK", status=200)