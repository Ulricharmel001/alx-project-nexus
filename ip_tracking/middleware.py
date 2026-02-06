import re

import requests
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from ipware import get_client_ip

from .models import BlockedIP, RequestLog


class IPTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip, is_routable = get_client_ip(request)
        if not ip:
            return

        # Check if IP is blocked
        if (
            cache.get(f"blocked_{ip}")
            or BlockedIP.objects.filter(ip_address=ip).exists()
        ):
            return HttpResponseForbidden("Your IP has been blocked.")

        # Get geolocation with caching
        geo_data = cache.get(f"geo_{ip}")
        if not geo_data:
            try:
                response = requests.get(f"https://ipinfo.io/{ip}/json").json()
                geo_data = {
                    "country": response.get("country"),
                    "city": response.get("city"),
                }
            except:
                geo_data = {"country": None, "city": None}
            cache.set(f"geo_{ip}", geo_data, 60 * 60 * 24)  # Cache for 24 hours

        # Extract product ID from URL
        product_id = self.extract_product_id(request.path)

        # Log the request
        RequestLog.objects.create(
            ip_address=ip,
            path=request.path,
            method=request.method,
            country=geo_data.get("country"),
            city=geo_data.get("city"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product_id,
            session_key=request.session.session_key,
        )

    def extract_product_id(self, path):
        # Match UUID pattern in URL
        uuid_pattern = r"/products/([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})"
        match = re.search(uuid_pattern, path)
        if match:
            return match.group(1)

        # Fallback to numeric ID
        numeric_match = re.search(r"/products/(\d+)", path)
        if numeric_match:
            return int(numeric_match.group(1))

        return None
