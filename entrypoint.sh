#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Celery worker in background if broker is configured
if [ -n "$CELERY_BROKER_URL" ]; then
    echo "Starting Celery worker..."
    celery -A e_commerce_api worker --loglevel=info --concurrency=2 &
fi

echo "Starting Gunicorn..."
exec gunicorn e_commerce_api.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2
