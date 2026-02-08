# E-Commerce Backend - ProDev BE

## About This Project

This is a comprehensive e-commerce backend platform built with Django and PostgreSQL, designed to simulate real-world development challenges in backend engineering. The platform provides a robust foundation for e-commerce applications with focus on scalability, security, and performance.

The backend handles core e-commerce functionality including product management, user authentication, and API services for filtering, sorting, and pagination. It implements industry-standard practices for database optimization, secure authentication with JWT, and comprehensive API documentation.

## Technologies Used

- **Backend Framework**: Django 5.2.11 with Django REST Framework
- **Database**: PostgreSQL for optimized relational data management
- **Authentication**: JWT (JSON Web Tokens) for secure user authentication
- **Documentation**: Swagger/OpenAPI for API documentation and testing
- **Web Server**: Gunicorn for production deployment
- **Development Tools**: Docker for containerization
- **Additional Features**: Redis for caching, Celery for background tasks, GraphQL support

## Key Features

- **CRUD Operations**: Full create, read, update, and delete APIs for products and categories
- **User Management**: Secure user authentication and management system with JWT tokens
- **API Functionality**: Advanced filtering, sorting, and pagination for efficient product discovery
- **Database Optimization**: High-performance database schema with proper indexing
- **API Documentation**: Comprehensive documentation using Swagger UI for easy frontend integration
- **Rate Limiting**: Protection against API abuse with configurable rate limits
- **Email Integration**: Support for email notifications and verification
- **OAuth Integration**: Google OAuth2 support for social login
- **Payment Integration**: Support for payment processing (Chapa)
- **IP Tracking**: Suspicious IP detection and blocking capabilities

## Project Structure

```
alx-project-nexus/
├── accounts/                 # User authentication and management
├── e_commerce_api/          # Main Django project settings
├── ip_tracking/             # IP address tracking and security
├── products/                # Product management and catalog
├── scripts/                 # Utility scripts
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-container orchestration
├── entrypoint.sh            # Container startup script
├── manage.py                # Django management commands
├── requirements.txt         # Python dependencies
├── .env-template.txt        # Environment variable template
└── README.md               # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- Docker and Docker Compose (optional)
- Redis (for caching and background tasks)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd alx-project-nexus
   ```

2. Create a virtual environment:
   ```bash
   python -m venv nexus-env
   source nexus-env/bin/activate  # On Windows: nexus-env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template and configure your settings:
   ```bash
   cp .env-template.txt .env
   # Edit .env with your specific configuration
   ```

5. Set up the database:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser account:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Docker Setup

To run the application using Docker:

1. Build and run the containers:
   ```bash
   docker compose up --build
   ```

2. The application will be available at `http://localhost:8000`
3. Adminer (database interface) will be available at `http://localhost:8080`

### Environment Variables

The application requires several environment variables. Copy `.env-template.txt` to `.env` and customize:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=your_database_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password

# OAuth configuration
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# Payment gateway
CHAPA_SECRET_KEY=your-chapa-secret-key
CHAPA_PUBLIC_KEY=your-chapa-public-key
```

## API Documentation

The API documentation is available through Swagger UI at `/swagger/` endpoint when the application is running.

Key API endpoints include:
- `/api/v1/products/` - Product listings with filtering, sorting, and pagination
- `/api/v1/accounts/` - User authentication and profile management
- `/api/v1/orders/` - Order management (if implemented)
- `/api/v1/categories/` - Category management

## Running Tests

To run the test suite:

```bash
python manage.py test
```

For specific app tests:
```bash
python manage.py test accounts
python manage.py test products
```

## Deployment

### Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Configure a production-ready database (PostgreSQL recommended)
3. Set up a reverse proxy (Nginx/Apache) with SSL
4. Use Gunicorn to serve the application:
   ```bash
   gunicorn e_commerce_api.wsgi:application --bind 0.0.0.0:8000
   ```

### Docker Production Deployment

For production Docker deployment:
```bash
docker compose -f docker-compose.prod.yml up -d
```

## Security Features

- JWT token-based authentication with configurable expiration
- Rate limiting to prevent API abuse
- CORS headers configured for secure cross-origin requests
- SQL injection prevention through ORM usage
- XSS protection through Django's built-in security features
- IP tracking and suspicious activity detection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, create an issue in the repository.