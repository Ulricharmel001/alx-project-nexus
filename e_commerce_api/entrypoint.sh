#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Celery worker in background..."
celery -A e_commerce_api worker --loglevel=info --concurrency=4 &

echo "Starting Gunicorn..."
exec gunicorn e_commerce_api.wsgi:application --bind 0.0.0.0:8000 --workers 4
