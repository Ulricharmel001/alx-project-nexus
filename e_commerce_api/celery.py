"""
Celery configuration and initialization for the project
Handles asynchronous task queuing and background job processing
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_api.settings')

# Create Celery app instance
app = Celery('e_commerce_api')

# Load configuration from Django settings with namespace
# All Celery settings in Django must start with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
# Looks for tasks.py in each app directory
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery setup
    Used to verify worker is running and connected to broker
    """
    print(f'Request: {self.request!r}')
