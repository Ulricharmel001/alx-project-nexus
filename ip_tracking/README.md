# IP Tracking Module for E-Commerce

This module provides IP tracking functionality for e-commerce applications, including logging, blacklisting, geolocation, and rate limiting.

## Features

- **Request Logging**: Logs all requests with IP, path, timestamp, geolocation, and user information
- **IP Blacklisting**: Blocks malicious IPs with manual and automatic blocking
- **Geolocation**: Tracks country and city of visitors
- **Rate Limiting**: Protects sensitive endpoints from abuse
- **Suspicious Activity Detection**: Identifies and flags suspicious IP addresses

## Installation

1. Add `'ip_tracking'` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'ip_tracking',
]
```

2. Add the middleware to your `MIDDLEWARE` in `settings.py`:

```python
MIDDLEWARE = [
    ...
    'ip_tracking.middleware.IPTrackingMiddleware',
    ...
]
```

3. Run migrations to create the necessary database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Install dependencies:

```bash
pip install -r ip_tracking/requirements.txt
```

## Usage

### Manual IP Blocking

Block an IP address from command line:

```bash
python manage.py block_ip 192.168.1.1 --reason "Suspicious activity"
```

### Automatic Suspicious IP Detection

Run the detection command periodically (e.g., via cron job):

```bash
python manage.py detect_suspicious_ips
```

### Rate Limited Views

The module includes rate-limited views for sensitive operations:

- `/checkout/` - Limited to 5 requests per minute
- `/login/` - Limited to 10 requests per minute
- `/product/<product_id>/` - Limited to 30 requests per minute
- `/add-to-cart/<product_id>/` - Limited to 15 requests per minute
- `/apply-coupon/` - Limited to 20 requests per minute

## Configuration

The module uses caching for geolocation data (cached for 24 hours) to reduce API calls to ipinfo.io.

Rate limits can be adjusted in the views.py file as needed for your specific use case.

## Models

- `RequestLog`: Stores all incoming requests with IP, path, timestamp, geolocation, and user information
- `BlockedIP`: Stores blacklisted IP addresses
- `SuspiciousIP`: Stores IPs flagged for suspicious activity
