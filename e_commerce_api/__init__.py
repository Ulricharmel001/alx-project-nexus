"""
E-commerce API package initialization
Loads Celery app on Django startup for background task processing
"""
# Import Celery app to ensure it's loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
