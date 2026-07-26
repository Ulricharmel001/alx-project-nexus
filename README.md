# Nexus — E-Commerce Platform

**Live API:** https://alx-project-nexus-1-q1us.onrender.com  
**Swagger Docs:** https://alx-project-nexus-1-q1us.onrender.com/swagger/  
**Frontend:** https://nexus-sparkle-04.vercel.app  
**Frontend Repo:** https://github.com/Ulricharmel001/nexus-sparkle-04

Full-stack e-commerce platform built with Django REST Framework (backend) and React + TanStack Start (frontend). Features JWT authentication, product/category management, cart/checkout flow with Chapa payments, Google OAuth, Redis caching, and Celery background tasks. Developed as a capstone project for the ALX Africa ProDev program.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5.2, DRF 3.16 |
| Database | PostgreSQL |
| Auth | JWT (simplejwt), Google OAuth2 |
| Cache / Queue | Redis (Upstash), Celery |
| File Storage | Django media uploads |
| Deploy | Render (backend), Vercel (frontend) |
| Frontend | React 19, TanStack Start, Tailwind CSS, Axios |

---

## Features

- JWT authentication with 30-min sliding expiration (active users stay logged in, idle users auto-logout)
- Product CRUD with multi-image upload
- Category CRUD with nested hierarchy and banner image upload
- Shopping cart (authenticated + guest)
- Order management (pending -> paid -> shipped -> delivered)
- Chapa payment gateway integration
- Google OAuth social login
- Email verification and password reset
- Admin dashboard with stats
- Swagger API documentation at /swagger/
- Rate limiting and IP tracking
- Celery background tasks for email and receipt generation

---

## API Overview

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/accounts/register/ | Create account | No |
| POST | /api/v1/accounts/login/ | Sign in (returns JWT) | No |
| POST | /api/v1/accounts/logout/ | Sign out (blacklists token) | Yes |
| GET | /api/v1/accounts/user/ | Get profile | Yes |
| PATCH | /api/v1/accounts/user/ | Update profile | Yes |
| GET | /api/v1/products/ | List products | No |
| POST | /api/v1/products/ | Create product | Admin |
| GET | /api/v1/products/categories/ | List categories | No |
| POST | /api/v1/products/categories/ | Create category | Admin |
| GET | /api/v1/products/categories/tree/ | Category hierarchy | No |
| GET/POST | /api/v1/products/cart/ | Shopping cart | Yes |
| GET | /api/v1/products/orders/ | User orders | Yes |
| POST | /api/v1/products/checkout/ | Checkout | Yes |
| GET | /api/v1/products/admin/dashboard/ | Dashboard stats | Admin |
| GET | /api/v1/accounts/admin/users/ | List users | Admin |
| POST | /api/v1/token/ | Obtain JWT | No |
| POST | /api/v1/token/refresh/ | Refresh JWT | No |

Full interactive docs at /swagger/ when running.

---

## Quick Start

```bash
git clone https://github.com/Ulricharmel001/alx-project-nexus.git
cd alx-project-nexus

python3 -m venv nexus-env
source nexus-env/bin/activate

pip install -r requirements.txt

cp .env-template.txt .env
# Edit .env with your configuration

python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

### Docker

```bash
docker compose up --build
```

---

## Project Structure

```
alx-project-nexus/
├── accounts/             # Auth, user management, OAuth
├── e_commerce_api/       # Django settings, URL config, Celery
├── products/             # Product, category, cart, orders, payments
├── ip_tracking/          # Security — IP monitoring and blocking
├── media/                # User-uploaded files (images)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env-template.txt
└── README.md
```

---

## Environment Variables

Copy `.env-template.txt` to `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| SECRET_KEY | Yes | Django secret key |
| DEBUG | Yes | True for development, False for production |
| DATABASE_URL | Yes | PostgreSQL connection string |
| CELERY_BROKER_URL | No | Redis URL for Celery (Upstash) |
| FRONTEND_URL | Yes | Frontend URL for CORS |
| GOOGLE_OAUTH2_CLIENT_ID | No | Google OAuth client ID |
| CHAPA_SECRET_KEY | No | Chapa payment secret key |

---

## Deployment

### Backend (Render)

Push to GitHub, create a Web Service on Render, set build command to `./entrypoint.sh`, configure environment variables in Render dashboard.

### Frontend (Vercel)

Import the frontend repo into Vercel, set `VITE_API_BASE` to the backend URL, deploy.

---

## Testing

```bash
python3 manage.py test
python3 manage.py test accounts
python3 manage.py test products
```

---

## License

MIT