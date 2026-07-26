# Nexus — E-Commerce Platform

> **Live API:** https://alx-project-nexus-1-q1us.onrender.com  
> **Swagger Docs:** https://alx-project-nexus-1-q1us.onrender.com/swagger/  
> **Frontend:** https://nexus-sparkle-04.vercel.app  
> **Frontend Repo:** https://github.com/Ulricharmel001/nexus-sparkle-04

Full-stack e-commerce platform built with **Django REST Framework** (backend) and **React + TanStack Start** (frontend). Features JWT authentication, product/category management, cart/checkout flow with Chapa payments, Google OAuth, Redis caching, and Celery background tasks.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, Django 5.2, DRF 3.16 |
| **Database** | PostgreSQL |
| **Auth** | JWT (simplejwt), Google OAuth2 |
| **Cache / Queue** | Redis (Upstash), Celery |
| **File Storage** | Django media uploads |
| **Deploy** | Render (backend), Vercel (frontend) |
| **Frontend** | React 19, TanStack Start, Tailwind CSS, Axios |

---

## Key Features

- **JWT Authentication** — Access + refresh tokens with 30-min sliding expiration; active users stay logged in indefinitely
- **Product CRUD** — Full admin management with multi-image upload
- **Category CRUD** — Nested categories with banner image upload
- **Shopping Cart** — Authenticated & guest checkout flows
- **Order Management** — Status tracking (pending → paid → shipped → delivered)
- **Payment Gateway** — Chapa integration for payment processing
- **Google OAuth** — Social login support
- **Email Verification** — Account email confirmation flow
- **Admin Dashboard** — Stats, user management, inventory control
- **API Docs** — Interactive Swagger UI at `/swagger/`
- **Rate Limiting** — Abuse protection with configurable limits
- **IP Tracking** — Suspicious IP detection and blocking

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis (optional — falls back to local memory cache)
- Docker (optional)

### Local Setup

```bash
# Clone
git clone https://github.com/Ulricharmel001/alx-project-nexus.git
cd alx-project-nexus

# Virtual env
python3 -m venv nexus-env
source nexus-env/bin/activate

# Install
pip install -r requirements.txt

# Configure environment
cp .env-template.txt .env
# Edit .env with your database credentials, secret key, etc.

# Database
python3 manage.py migrate

# Admin user
python3 manage.py createsuperuser

# Run
python3 manage.py runserver
```

Visit **http://localhost:8000/swagger/** for API docs.

### Docker

```bash
docker compose up --build
```

---

## API Overview

| Endpoint | Description |
|----------|-------------|
| `/api/v1/accounts/register/` | User registration |
| `/api/v1/accounts/login/` | Login (returns JWT tokens) |
| `/api/v1/accounts/logout/` | Logout (blacklists refresh token) |
| `/api/v1/accounts/user/` | Authenticated user profile |
| `/api/v1/accounts/google/` | Google OAuth flow |
| `/api/v1/products/` | Product listing & create (admin) |
| `/api/v1/products/categories/` | Category listing & create (admin) |
| `/api/v1/products/cart/` | Shopping cart |
| `/api/v1/products/orders/` | Orders |
| `/api/v1/products/admin/dashboard/` | Admin dashboard stats |
| `/api/v1/token/` | JWT token obtain |
| `/api/v1/token/refresh/` | JWT token refresh |

Full interactive docs at `/swagger/` when running.

---

## Project Structure

```
alx-project-nexus/
├── accounts/             # Auth, user management, OAuth
├── e_commerce_api/       # Django settings, URL config, Celery
├── products/             # Product, category, cart, orders, payments
├── ip_tracking/          # Security — IP monitoring & blocking
├── media/                # User-uploaded files (images)
├── Dockerfile            # Container build
├── docker-compose.yml    # Local orchestration
├── requirements.txt      # Python dependencies
├── .env-template.txt     # Environment variable template
└── README.md
```

---

## Environment Variables

Copy `.env-template.txt` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (True/False) |
| `DATABASE_URL` | PostgreSQL connection string |
| `CELERY_BROKER_URL` | Redis URL for Celery (Upstash) |
| `GOOGLE_OAUTH2_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | Google OAuth client secret |
| `CHAPA_SECRET_KEY` | Chapa payment secret key |
| `CHAPA_PUBLIC_KEY` | Chapa payment public key |
| `FRONTEND_URL` | Frontend URL for CORS |

---

## Deployment

### Backend (Render)

Push to GitHub → Render auto-deploys from `main`.  
Set all env vars in Render dashboard.  
See `render.yaml` for service configuration.

### Frontend (Vercel)

Frontend repo: https://github.com/Ulricharmel001/nexus-sparkle-04  
Auto-deploys from `main` branch. Set `VITE_API_BASE` to the backend URL.

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