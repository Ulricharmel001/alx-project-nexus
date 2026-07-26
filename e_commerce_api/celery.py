import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_commerce_api.settings")

app = Celery("e_commerce_api")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.update(
    task_routes={
        "accounts.tasks.*": {"queue": "email"},
        "products.tasks.*": {"queue": "default"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=86400,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_concurrency=4,
)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
