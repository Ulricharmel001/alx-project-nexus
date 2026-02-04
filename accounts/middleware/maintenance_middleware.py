from django.http import HttpResponse
from django.contrib.auth import get_user_model
from accounts.models import MaintenanceMode

User = get_user_model()


class MaintenanceModeMiddleware:
    """
    Middleware to handle maintenance mode.
    Allows admin users to access the site during maintenance,
    while showing a maintenance message to regular users.
    """

    def __init__(self, get_response):
        self.get_response = get_response
      
    def __call__(self, request):
        maintenance_mode = MaintenanceMode.is_maintenance_mode()
        if not maintenance_mode:
            return self.get_response(request)

        # Process the request through the rest of the middleware chain first
        # This ensures authentication runs before our check
        response = self.get_response(request)

        # Check if user is authenticated admin (staff or superuser)
        user_is_admin = (
            hasattr(request, 'user') and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )

        # If user is admin, allow access and return normal response
        if user_is_admin:
            return response
        
        try:
            maintenance_obj = MaintenanceMode.objects.first()
            if maintenance_obj:
                maintenance_message = maintenance_obj.message
            else:
                maintenance_message = "We are currently performing scheduled maintenance. We'll be back soon!"
        except:
            maintenance_message = "We are currently performing scheduled maintenance. We'll be back soon!"

        return HttpResponse(
            maintenance_message,
            status=503,  # HTTP 503: Service Unavailable
            content_type='text/html'
        )