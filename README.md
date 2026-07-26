<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/DRF-3.16-A30000?logo=django&logoColor=white" alt="DRF">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/JWT-Auth-000000?logo=jsonwebtokens&logoColor=white" alt="JWT">
  <img src="https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white" alt="Celery">
  <img src="https://img.shields.io/badge/Redis-UPSTASH-FF4438?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?logo=render&logoColor=white" alt="Render">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" alt="React">
</p>

<h1 align="center">🛒 Nexus — E-Commerce Platform</h1>

<p align="center">
  <strong>ALX Africa ProDev Capstone Project</strong><br>
  A production-grade full-stack e-commerce platform with JWT auth, product management, cart/checkout flow, Chapa payments, and background task processing.
</p>

<p align="center">
  <a href="https://nexus-sparkle-04.vercel.app"><strong>🌐 Frontend</strong></a> ·
  <a href="https://alx-project-nexus-1-q1us.onrender.com/swagger/"><strong>📖 API Docs (Swagger)</strong></a> ·
  <a href="https://alx-project-nexus-1-q1us.onrender.com"><strong>⚡ Live API</strong></a> ·
  <a href="https://github.com/Ulricharmel001/nexus-sparkle-04"><strong>🎨 Frontend Repo</strong></a>
</p>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Live Demo](#live-demo)
- [API Overview](#api-overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributors](#contributors)
- [License](#license)

---

## Overview

Nexus is a full-stack e-commerce platform built as a capstone project for the **ALX Africa ProDev program**. It demonstrates production-ready backend engineering practices including:

- **Secure JWT authentication** with sliding session expiration (30-min inactivity timeout)
- **RESTful API design** with filtering, sorting, pagination, and Swagger documentation
- **Background task processing** via Celery (email notifications, receipt generation)
- **Redis caching** through Upstash for performance optimization
- **File uploads** for product images and category banners
- **Payment integration** with Chapa gateway
- **CI/CD pipeline** with pre-commit hooks, linting, and automated deployment

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, Django 5.2.11, Django REST Framework 3.16 |
| **Database** | PostgreSQL (Neon) |
| **Authentication** | JWT (djangorestframework-simplejwt), Google OAuth2 |
| **Task Queue** | Celery with Redis broker (Upstash) |
| **Caching** | django-redis (Upstash) |
| **File Storage** | Django media uploads |
| **API Documentation** | Swagger (drf-yasg), Redoc |
| **Deployment** | Render (backend), Vercel (frontend) |
| **Frontend** | React 19, TanStack Start 1.168, Tailwind CSS, Axios |
| **DevOps** | Docker, Docker Compose, pre-commit, flake8, black, isort |

---

## Key Features

- **🔐 JWT Authentication** — Access + refresh tokens with 30-min sliding window; active users stay logged in indefinitely; inactive users auto-logout after 30 min
- **📦 Product Management** — Full CRUD with multi-image upload, categories assignment, active/inactive toggle
- **🏷️ Category Management** — Nested hierarchy (parent/child), banner image upload, description
- **🛒 Shopping Cart** — Authenticated user cart + guest cart support
- **📋 Order Management** — Full lifecycle (pending → paid → shipped → delivered), admin oversight
- **💳 Payment Gateway** — Chapa integration with payment initiation and verification webhook
- **👤 User Management** — Registration with email verification, login/logout, password reset, profile management
- **🔑 Google OAuth** — Social login via Google
- **📧 Email Notifications** — Welcome emails, verification codes, password reset, receipt generation (Celery)
- **📊 Admin Dashboard** — Stats overview (products, categories, users, orders, revenue, low stock)
- **🔍 API Features** — Full-text search, filtering, sorting, pagination on product endpoints
- **📖 API Documentation** — Interactive Swagger UI at `/swagger/`
- **🛡️ Security** — JWT token blacklisting, rate limiting, CORS, IP tracking & suspicious activity detection
- **⚙️ Background Tasks** — Celery workers for async email sending and receipt generation

---

## Live Demo

| Resource | URL |
|----------|-----|
| **Frontend Application** | [nexus-sparkle-04.vercel.app](https://nexus-sparkle-04.vercel.app) |
| **API Base URL** | [alx-project-nexus-1-q1us.onrender.com](https://alx-project-nexus-1-q1us.onrender.com) |
| **Swagger API Docs** | [alx-project-nexus-1-q1us.onrender.com/swagger/](https://alx-project-nexus-1-q1us.onrender.com/swagger/) |
| **Redoc API Docs** | [alx-project-nexus-1-q1us.onrender.com/redoc/](https://alx-project-nexus-1-q1us.onrender.com/redoc/) |
| **Frontend Repository** | [github.com/Ulricharmel001/nexus-sparkle-04](https://github.com/Ulricharmel001/nexus-sparkle-04) |

---

## API Overview

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/accounts/register/` | Create account | ❌ |
| POST | `/api/v1/accounts/login/` | Sign in (returns JWT) | ❌ |
| POST | `/api/v1/accounts/logout/` | Sign out (blacklists token) | ✅ |
| GET | `/api/v1/accounts/user/` | Get profile | ✅ |
| PATCH | `/api/v1/accounts/user/` | Update profile | ✅ |
| PATCH | `/api/v1/accounts/user/profile/` | Update profile image | ✅ |
| GET | `/api/v1/products/` | List products (filter, sort, search, paginate) | ❌ |
| POST | `/api/v1/products/` | Create product | ✅ Admin |
| GET | `/api/v1/products/categories/` | List categories | ❌ |
| POST | `/api/v1/products/categories/` | Create category | ✅ Admin |
| GET | `/api/v1/products/categories/tree/` | Category hierarchy | ❌ |
| GET/POST | `/api/v1/products/cart/` | Shopping cart | ✅ |
| GET | `/api/v1/products/orders/` | User orders | ✅ |
| POST | `/api/v1/products/checkout/` | Checkout | ✅ |
| GET | `/api/v1/products/admin/dashboard/` | Dashboard stats | ✅ Admin |
| GET | `/api/v1/accounts/admin/users/` | List users | ✅ Admin |
| POST | `/api/v1/token/` | Obtain JWT | ❌ |
| POST | `/api/v1/token/refresh/` | Refresh JWT | ❌ |

> Full interactive documentation available at **`/swagger/`**.

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis (optional — falls back to local memory cache)
- Docker (optional)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Ulricharmel001/alx-project-nexus.git
cd alx-project-nexus

# Create and activate virtual environment
python3 -m venv nexus-env
source nexus-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env-template.txt .env
# Edit .env with your local database credentials, secret key, etc.

# Run database migrations
python3 manage.py migrate

# Create an admin user
python3 manage.py createsuperuser

# Start the development server
python3 manage.py runserver
```

Visit **http://localhost:8000/swagger/** for interactive API documentation.

### Docker Setup

```bash
docker compose up --build
```

Services:
- **App:** http://localhost:8000
- **Adminer:** http://localhost:8080

---

## Project Structure

```
alx-project-nexus/
├── accounts/                 # User authentication, registration, OAuth
│   ├── middleware/           # Maintenance mode middleware
│   ├── migrations/
│   ├── models.py             # CustomUser model
│   ├── serializers.py
│   ├── views.py              # Auth views (login, register, logout, etc.)
│   ├── google_oauth.py       # Google OAuth2 handler
│   └── tasks.py              # Celery tasks (emails)
├── e_commerce_api/           # Django project configuration
│   ├── settings.py           # All settings (DB, JWT, CORS, Celery, etc.)
│   ├── urls.py               # Root URL configuration
│   └── celery.py             # Celery app configuration
├── products/                 # Core e-commerce logic
│   ├── models.py             # Product, Category, ProductImage, Cart, Order, etc.
│   ├── serializers.py
│   ├── views.py              # All API views
│   ├── urls.py
│   ├── cart_service.py       # Cart & checkout logic
│   ├── chapa_service.py      # Chapa payment gateway integration
│   └── tasks.py              # Receipt generation tasks
├── ip_tracking/              # Security — IP logging & blocking
├── templates/                # HTML email templates
├── media/                    # Uploaded images (products, categories)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env-template.txt
└── README.md
```

---

## Environment Variables

Copy `.env-template.txt` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DEBUG` | ✅ | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | ✅ | Comma-separated allowed hosts |
| `DATABASE_URL` | ✅ | PostgreSQL connection string (e.g., `postgres://user:pass@host:5432/db`) |
| `CELERY_BROKER_URL` | ⚠️ | Redis URL for Celery (Upstash recommended for production) |
| `CELERY_RESULT_BACKEND` | ⚠️ | Redis URL for Celery results |
| `FRONTEND_URL` | ✅ | Frontend URL for CORS configuration |
| `GOOGLE_OAUTH2_CLIENT_ID` | ⚠️ | Google OAuth client ID (for social login) |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | ⚠️ | Google OAuth client secret |
| `CHAPA_SECRET_KEY` | ⚠️ | Chapa payment secret key |
| `CHAPA_PUBLIC_KEY` | ⚠️ | Chapa payment public key |
| `EMAIL_HOST_USER` | ⚠️ | SMTP email for sending emails |
| `EMAIL_HOST_PASSWORD` | ⚠️ | SMTP email password/app password |

> ✅ = Required &nbsp;&nbsp; ⚠️ = Optional (feature-dependent)

---

## Deployment

### Backend — Render

1. Push to GitHub (main branch)
2. Create a new **Web Service** on Render connected to the repo
3. Set the **build command** to `./entrypoint.sh`
4. Configure all environment variables in Render dashboard
5. Deploy — Render auto-deploys from `main` on each push

A `render.yaml` file is included for infrastructure-as-code deployment.

### Frontend — Vercel

1. Go to [vercel.com](https://vercel.com) and import the [frontend repo](https://github.com/Ulricharmel001/nexus-sparkle-04)
2. Set the `VITE_API_BASE` environment variable to the backend URL
3. Deploy — auto-deploys from `main`

---

## Testing

```bash
# Run all tests
python3 manage.py test

# Test specific apps
python3 manage.py test accounts
python3 manage.py test products

# With coverage (if installed)
coverage run manage.py test && coverage report
```

---

## Contributors

| Avatar | Name | Role |
|--------|------|------|
| <img src="https://github.com/Ulricharmel001.png" width="40" height="40" style="border-radius:50%"> | **Ulricharmel001** | Backend & Frontend Developer |
| <img src="https://github.com/qwencoder.png" width="40" height="40" style="border-radius:50%"> | **qwencoder** | Project Partner |

---

## License

This project is developed as part of the **ALX Africa ProDev program** and is available under the MIT License.