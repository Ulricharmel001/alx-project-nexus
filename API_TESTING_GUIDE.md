# API Testing Guide - How to Test All Endpoints

## Prerequisites
1. Django server running: `python manage.py runserver`
2. Postman or similar API client (or curl)
3. Access to Swagger UI at `http://localhost:8000/swagger/`

---

## Method 1: Using Swagger UI (Easiest)

Visit `http://localhost:8000/swagger/` in your browser. All endpoints are documented there with:
- Request/response schemas
- Try-it-out functionality
- Authorization header support

---

## Method 2: Using Postman

### 1. Registration Endpoint
**URL:** POST `http://localhost:8000/api/v1/accounts/register/`

**Body (JSON):**
```json
{
  "email": "testuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password2": "securepassword123"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "date_joined": "2026-01-24T18:30:00Z",
    "profile": {}
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Save the `access` token for authenticated requests.

---

### 2. Login Endpoint
**URL:** POST `http://localhost:8000/api/v1/accounts/login/`

**Body (JSON):**
```json
{
  "email": "testuser@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as registration (returns access + refresh tokens)

Save the tokens for next requests.

---

### 3. Get User Details
**URL:** GET `http://localhost:8000/api/v1/accounts/user/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "id": 1,
  "email": "testuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "date_joined": "2026-01-24T18:30:00Z",
  "profile": {
    "bio": "",
    "profile_picture": null,
    "phone_number": "",
    "address": ""
  }
}
```

---

### 4. Update User Details
**URL:** PUT `http://localhost:8000/api/v1/accounts/user/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Body (JSON):**
```json
{
  "first_name": "Johnny",
  "last_name": "Smith"
}
```

**Response:**
```json
{
  "message": "User updated successfully",
  "data": {
    "id": 1,
    "email": "testuser@example.com",
    "first_name": "Johnny",
    "last_name": "Smith",
    "role": "user",
    "is_active": true,
    "date_joined": "2026-01-24T18:30:00Z",
    "profile": {}
  }
}
```

---

### 5. Get User Profile
**URL:** GET `http://localhost:8000/api/v1/accounts/user/profile/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "bio": "",
  "profile_picture": null,
  "phone_number": "",
  "address": ""
}
```

---

### 6. Update User Profile
**URL:** PUT `http://localhost:8000/api/v1/accounts/user/profile/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "bio": "I am a software developer",
  "phone_number": "+1234567890",
  "address": "123 Main St, City, State"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "data": {
    "bio": "I am a software developer",
    "profile_picture": null,
    "phone_number": "+1234567890",
    "address": "123 Main St, City, State"
  }
}
```

---

### 7. Change Password
**URL:** POST `http://localhost:8000/api/v1/accounts/password/change/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Body (JSON):**
```json
{
  "old_password": "securepassword123",
  "new_password": "newsecurepassword456",
  "new_password2": "newsecurepassword456"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

---

### 8. Request Password Reset
**URL:** POST `http://localhost:8000/api/v1/accounts/password/reset/`

**Body (JSON):**
```json
{
  "email": "testuser@example.com"
}
```

**Response:**
```json
{
  "message": "Password reset link sent to your email"
}
```

**Note:** This endpoint sends an email (configure email settings in settings.py)

---

### 9. Refresh Token
**URL:** POST `http://localhost:8000/api/v1/accounts/token/refresh/`

**Body (JSON):**
```json
{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

**Response:**
```json
{
  "access": "NEW_ACCESS_TOKEN",
  "refresh": "NEW_REFRESH_TOKEN"
}
```

---

### 10. Logout
**URL:** POST `http://localhost:8000/api/v1/accounts/logout/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Body (JSON):**
```json
{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

---

## Method 3: Using cURL

### Registration
```bash
curl -X POST http://localhost:8000/api/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password2": "securepassword123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "securepassword123"
  }'
```

### Get User (Replace TOKEN with your access token)
```bash
curl -X GET http://localhost:8000/api/v1/accounts/user/ \
  -H "Authorization: Bearer TOKEN"
```

### Update Profile
```bash
curl -X PUT http://localhost:8000/api/v1/accounts/user/profile/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "I am a developer",
    "phone_number": "+1234567890"
  }'
```

### Change Password
```bash
curl -X POST http://localhost:8000/api/v1/accounts/password/change/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "securepassword123",
    "new_password": "newsecurepassword456",
    "new_password2": "newsecurepassword456"
  }'
```

---

## Method 4: Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/accounts"

# 1. Register
registration_data = {
    "email": "testuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password2": "securepassword123"
}

response = requests.post(f"{BASE_URL}/register/", json=registration_data)
print("Registration:", response.json())
access_token = response.json()["access"]

# 2. Get User
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/user/", headers=headers)
print("User Details:", response.json())

# 3. Update Profile
profile_data = {
    "bio": "I am a developer",
    "phone_number": "+1234567890"
}

response = requests.put(f"{BASE_URL}/user/profile/", json=profile_data, headers=headers)
print("Update Profile:", response.json())

# 4. Change Password
password_data = {
    "old_password": "securepassword123",
    "new_password": "newsecurepassword456",
    "new_password2": "newsecurepassword456"
}

response = requests.post(f"{BASE_URL}/password/change/", json=password_data, headers=headers)
print("Change Password:", response.json())
```

---

## Testing Checklist

- [ ] Register new user
- [ ] Login with registered user
- [ ] Get user details
- [ ] Update user details
- [ ] Get user profile
- [ ] Update user profile
- [ ] Change password (with old password verification)
- [ ] Login again (verifies password change worked)
- [ ] Request password reset
- [ ] Refresh token
- [ ] Logout
- [ ] Try accessing protected endpoint without token (should fail)

---

## Common Errors & Solutions

**401 Unauthorized**
- Missing or invalid access token
- Token has expired, use refresh token to get new one

**400 Bad Request**
- Check JSON format
- Verify password requirements (8+ chars, not numeric)
- Ensure password confirmation matches

**404 Not Found**
- Check URL path
- Verify endpoint exists in urls.py

**429 Too Many Requests**
- Rate limiting active
- Wait a minute before retrying

---

## Tips

1. Save tokens in Postman variables for easier testing
2. Use Swagger UI first to understand request/response format
3. Always check email format with @ symbol
4. Passwords must be at least 8 characters
5. Use Bearer token format: `Bearer YOUR_TOKEN`
6. Keep refresh tokens safe for token renewal
