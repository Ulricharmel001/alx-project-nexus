# Accounts Module Documentation

## Overview

The Accounts module provides comprehensive user management functionality for the ALX E-Commerce platform. It handles user registration, authentication, profile management, and integrates with external services like Google OAuth.

## Features

- **User Registration & Authentication**: Secure JWT-based authentication system
- **Email Verification**: In-memory verification code system with rate limiting
- **Password Management**: Reset and change functionality with secure token generation
- **Profile Management**: User profile creation and updates
- **Google OAuth Integration**: Third-party authentication via Google
- **Asynchronous Email Handling**: All emails sent via Celery background tasks

## Architecture

### Models

#### CustomUser
Extends Django's AbstractUser with:
- Email as username field
- Role-based permissions (admin/user)
- First and last name fields
- Active status tracking

#### UserProfile
One-to-one relationship with CustomUser containing:
- Bio field
- Profile picture upload
- Phone number
- Address

### Key Components

#### Authentication Flow
1. User registers with email and password
2. System generates JWT tokens immediately
3. Verification code is stored in-memory and sent via email (async)
4. User verifies email using the code
5. Subsequent logins return JWT tokens

#### Email System
- Uses in-memory storage for verification codes (with expiration)
- Implements rate limiting (1-minute cooldown between resend requests)
- All emails sent asynchronously via Celery tasks
- Automatic retry mechanism for failed deliveries

#### Security Features
- Password strength validation (min 8 chars, not entirely numeric)
- Rate limiting on authentication endpoints
- JWT token blacklisting on logout
- Secure token generation for password resets

## API Endpoints

### Authentication

#### POST `/api/v1/accounts/register/`
Registers a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password2": "securepassword123"
}
```

**Response:**
```json
{
  "message": "User registered successfully. Please check your email for verification code.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  },
  "refresh": "refresh_token_here",
  "access": "access_token_here",
  "email_verification_required": true
}
```

#### POST `/api/v1/accounts/login/`
Authenticates user and returns JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  },
  "refresh": "refresh_token_here",
  "access": "access_token_here"
}
```

#### POST `/api/v1/accounts/logout/`
Logs out the user by blacklisting the refresh token.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "refresh": "refresh_token_to_blacklist"
}
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

### User Management

#### GET `/api/v1/accounts/user/`
Retrieves authenticated user details.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "date_joined": "2023-01-01T00:00:00Z",
  "profile": {
    "bio": "Software developer",
    "profile_picture": "/media/profile_pics/avatar.jpg",
    "phone_number": "+1234567890",
    "address": "123 Main St"
  }
}
```

#### PUT `/api/v1/accounts/user/`
Updates authenticated user details.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response:**
```json
{
  "message": "User updated successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  }
}
```

### Profile Management

#### GET `/api/v1/accounts/user/profile/`
Retrieves authenticated user's profile.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "bio": "Software developer",
  "profile_picture": "/media/profile_pics/avatar.jpg",
  "phone_number": "+1234567890",
  "address": "123 Main St"
}
```

#### PUT `/api/v1/accounts/user/profile/`
Updates authenticated user's profile.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "bio": "Senior Software Developer",
  "phone_number": "+1987654321"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "data": {
    "bio": "Senior Software Developer",
    "profile_picture": "/media/profile_pics/avatar.jpg",
    "phone_number": "+1987654321",
    "address": "123 Main St"
  }
}
```

### Password Management

#### POST `/api/v1/accounts/password/change/`
Changes authenticated user's password.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "old_password": "current_password",
  "new_password": "new_secure_password123",
  "new_password2": "new_secure_password123"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

#### POST `/api/v1/accounts/password/reset/`
Requests password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Password reset link sent to your email"
}
```

#### POST `/api/v1/accounts/password/reset/confirm/{uidb64}/{token}/`
Confirms password reset with new password.

**Request Body:**
```json
{
  "password": "new_secure_password123",
  "password2": "new_secure_password123"
}
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

### Email Verification

#### POST `/api/v1/accounts/email/verify/`
Verifies user email with code.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "message": "Code verified successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  }
}
```

#### POST `/api/v1/accounts/email/resend/`
Resends verification email with new code.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Verification email has been queued and will be sent shortly",
  "code_expires_in": 300
}
```

### Google OAuth

#### GET `/api/v1/accounts/google/login/`
Gets Google OAuth login authorization URL.

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=email%20profile&access_type=offline"
}
```

#### POST `/api/v1/accounts/google/callback/`
Exchanges Google authorization code for JWT tokens.

**Request Body:**
```json
{
  "code": "authorization_code_from_google"
}
```

**Response:**
```json
{
  "message": "Google login successful",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  },
  "access": "access_token_here",
  "refresh": "refresh_token_here"
}
```

#### POST `/api/v1/accounts/google/token/`
Verifies Google token and logs in user.

**Request Body:**
```json
{
  "token": "google_id_token"
}
```

**Response:**
```json
{
  "message": "Google login successful",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "profile": null
  },
  "access": "access_token_here",
  "refresh": "refresh_token_here"
}
```

### Token Management

#### POST `/api/v1/accounts/token/refresh/`
Refreshes JWT access token using refresh token.

**Request Body:**
```json
{
  "refresh": "refresh_token_here"
}
```

**Response:**
```json
{
  "access": "new_access_token_here"
}
```

#### POST `/api/v1/accounts/token/blacklist/`
Blacklists refresh token (logout).

**Request Body:**
```json
{
  "refresh": "refresh_token_to_blacklist"
}
```

**Response:**
```json
{
  "message": "Token blacklisted successfully"
}
```

## Frontend Integration Guide

### Authentication Flow

1. **Registration**:
   - Collect user details (email, first name, last name, password)
   - Call `/api/v1/accounts/register/` endpoint
   - Store JWT tokens in local storage/session
   - Prompt user to check email for verification code

2. **Login**:
   - Collect email and password
   - Call `/api/v1/accounts/login/` endpoint
   - Store JWT tokens in local storage/session
   - Redirect to dashboard/home page

3. **Protected Routes**:
   - Include `Authorization: Bearer {access_token}` header in API calls
   - Handle 401 responses by refreshing token or redirecting to login

4. **Token Refresh**:
   - When access token expires, call `/api/v1/accounts/token/refresh/`
   - Update stored access token

5. **Logout**:
   - Call `/api/v1/accounts/logout/` with refresh token
   - Clear stored tokens from local storage/session

### Error Handling

Common error responses:
- `400 Bad Request`: Validation errors or incorrect credentials
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded (for email resend)

### Email Verification

1. After registration, show message prompting user to check email
2. Provide form to enter verification code
3. Call `/api/v1/accounts/email/verify/` with email and code
4. On success, update UI to show verified status

### Password Reset

1. Show password reset form with email field
2. Call `/api/v1/accounts/password/reset/` with user's email
3. Inform user to check email for reset link
4. When user clicks reset link, show new password form
5. Call `/api/v1/accounts/password/reset/confirm/{uidb64}/{token}/` with new password

### Google OAuth Integration

1. **Option 1 - Authorization Code Flow**:
   - Call `/api/v1/accounts/google/login/` to get authorization URL
   - Redirect user to Google for authentication
   - Handle callback at your frontend route
   - Send authorization code to `/api/v1/accounts/google/callback/`

2. **Option 2 - Token Flow**:
   - Use Google Sign-In SDK to get ID token
   - Send token to `/api/v1/accounts/google/token/`

## Security Best Practices

1. **Token Storage**: Store JWT tokens securely (preferably in httpOnly cookies or secure local storage)
2. **Token Expiration**: Handle token expiration gracefully with automatic refresh
3. **Password Strength**: Enforce strong password policies on frontend
4. **Rate Limiting**: Respect API rate limits to prevent abuse
5. **HTTPS**: Always use HTTPS in production environments

## Environment Variables

The accounts module relies on the following environment variables:

```env
# Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH2_REDIRECT_URI=http://localhost:8000/api/v1/accounts/google/callback/

# Email Configuration
GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=noreply@ecommerce.com

# Frontend URL for email links
FRONTEND_URL=http://localhost:3000

# JWT Settings
SECRET_KEY=your_secret_key
TOKEN_EXPIRE_HOURS=24
PASSWORD_RESET_TIMEOUT=3600

# Celery Configuration
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

## Testing

The accounts module includes comprehensive tests covering all endpoints and functionality. Run tests using:

```bash
python manage.py test accounts
```

## Troubleshooting

### Common Issues

1. **Email not sending**: Ensure Celery workers are running and email configuration is correct
2. **JWT token expiration**: Implement automatic token refresh in your frontend
3. **Rate limiting**: Implement cooldown indicators for email resend functionality
4. **Google OAuth**: Verify client ID, secret, and redirect URI are correctly configured

### Debugging Tips

- Check Django logs for detailed error information
- Verify environment variables are properly set
- Ensure Redis and Celery services are running for email functionality
- Test endpoints individually using tools like Postman or curl

## Dependencies

- Django 5.2+
- Django REST Framework
- Django Simple JWT
- Celery (for background tasks)
- Redis (for caching and Celery broker)
- Google Auth Library
- DRF-YASG (for API documentation)

## Maintenance Mode Middleware

The accounts app includes a maintenance mode middleware that allows administrators to temporarily restrict access to the application during maintenance periods while still allowing admin users to access the system.

### Features:
- Blocks non-admin users during maintenance mode
- Allows admin users to continue accessing the application during maintenance
- Configurable maintenance message
- Environment variable based configuration

### Configuration:
Add the following environment variables to enable maintenance mode:
```
MAINTENANCE_MODE=true
MAINTENANCE_MESSAGE="Custom maintenance message here"
```

### How it works:
1. When `MAINTENANCE_MODE` is set to `true`, the middleware intercepts requests
2. Admin users (users with `is_staff` or `is_superuser` flag) are allowed access
3. Regular users receive a maintenance message with HTTP 503 status code