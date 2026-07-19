#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Celery worker..."
nohup celery -A e_commerce_api worker -l info -c 1 -Q email,default > /var/log/celery.log 2>&1 &
echo "Celery worker PID: $!"

echo "Starting Gunicorn..."
exec gunicorn e_commerce_api.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2
