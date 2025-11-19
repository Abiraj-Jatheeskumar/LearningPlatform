# JWT Authentication Implementation Guide

Your JWT secret has been configured! Here's everything you need to know.

## ✅ What Was Added

### 1. Environment Variables (`.env`)
```env
JWT_SECRET=dWSTzj8wEZRcgNHQxKmBtiuO2sXGUIFYa69yhDe7n4pC1fv53oqlJVrMkP0LbA
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### 2. JWT Utilities (`src/utils/jwt_utils.py`)
Functions for creating and verifying JWT tokens:
- `create_access_token(data, expires_delta)` - Create JWT token
- `decode_access_token(token)` - Decode and verify token
- `create_refresh_token(data)` - Create long-lived refresh token
- `verify_token(token)` - Quick token validation

### 3. Example Implementation (`src/routers/auth_jwt_example.py`)
Complete example showing how to use JWT in your auth endpoints

### 4. Dependencies
Added `PyJWT==2.8.0` to requirements.txt and installed it

## 🚀 How to Use JWT in Your Code

### Using the JWT Secret

```python
import os

# Get JWT secret from environment
SECRET_KEY = os.environ.get("JWT_SECRET")
```

### Creating a Token (Login/Register)

```python
from src.utils.jwt_utils import create_access_token

# After successful login
token_data = {
    "sub": user["id"],        # Subject (user ID)
    "email": user["email"],
    "role": user["role"],
}
access_token = create_access_token(token_data)

# Return to client
return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": user
}
```

### Verifying a Token (Protected Routes)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt_utils import decode_access_token

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    # Fetch user from database using user_id
    return user

# Use in your routes
@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"message": f"Hello {current_user['email']}"}
```

## 📝 Update Your Auth Router

Replace your current `src/routers/auth.py` with JWT implementation:

### Current Login Endpoint
```python
# OLD - No JWT
@router.post("/login")
async def login(request_data: LoginRequest):
    # ... validate user ...
    return {
        "success": True,
        "user": user  # Just return user data
    }
```

### Updated Login Endpoint with JWT
```python
# NEW - With JWT
from src.utils.jwt_utils import create_access_token

@router.post("/login")
async def login(request_data: LoginRequest):
    # ... validate user ...
    
    # Create JWT token
    token_data = {
        "sub": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
    }
    access_token = create_access_token(token_data)
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
```

## 🔒 Frontend Integration

### Storing the Token (React)

```typescript
// After login
const response = await fetch('http://localhost:3001/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();

// Store token in localStorage
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### Sending Token with Requests

```typescript
// Include token in API requests
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:3001/api/protected-route', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Update Your authService.ts

```typescript
// src/services/authService.ts
const API_URL = 'http://localhost:3001/api/auth';

export const login = async (email: string, password: string) => {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Store token
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }
  
  return data;
};

export const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};
```

## 🛡️ Token Payload Structure

Your JWT tokens contain:

```json
{
  "sub": "user_id_here",          // Subject (user ID)
  "email": "user@example.com",
  "role": "student",
  "exp": 1234567890,               // Expiration timestamp
  "iat": 1234567890                // Issued at timestamp
}
```

## ⏰ Token Expiration

- **Access Token:** 24 hours (configurable via `JWT_EXPIRATION_HOURS`)
- **Refresh Token:** 7 days

Change expiration in `.env`:
```env
JWT_EXPIRATION_HOURS=48  # 48 hours
```

## 🔄 Token Refresh Flow

```python
@router.post("/refresh")
async def refresh_token(current_user = Depends(get_current_user)):
    token_data = {
        "sub": current_user.get("id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
    }
    new_token = create_access_token(token_data)
    
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
```

## 📚 Example Protected Routes

```python
from fastapi import Depends
from src.utils.jwt_utils import decode_access_token

@router.get("/me")
async def get_current_user(current_user = Depends(get_current_user)):
    return {"user": current_user}

@router.get("/admin-only")
async def admin_route(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"message": "Admin content"}
```

## 🧪 Testing JWT Tokens

### Using Postman/Thunder Client

1. **Login:**
   ```
   POST http://localhost:3001/api/auth/login
   Body: { "email": "student@example.com", "password": "password123" }
   ```

2. **Copy the `access_token` from response**

3. **Protected Route:**
   ```
   GET http://localhost:3001/api/auth/me
   Headers: Authorization: Bearer YOUR_TOKEN_HERE
   ```

### Using Python

```python
import requests

# Login
response = requests.post('http://localhost:3001/api/auth/login', json={
    'email': 'student@example.com',
    'password': 'password123'
})
data = response.json()
token = data['access_token']

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:3001/api/auth/me', headers=headers)
print(response.json())
```

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use HTTPS in production** - Never send tokens over HTTP
3. **Store tokens securely** - Use httpOnly cookies in production
4. **Short expiration times** - 24 hours is reasonable
5. **Implement refresh tokens** - For better UX
6. **Validate tokens on every request** - Don't trust client data

## 🚨 Common Issues

### Token Invalid
- Check if token is expired
- Verify token is being sent correctly
- Ensure JWT_SECRET is loaded

### Token Not Found
- Check Authorization header format: `Bearer TOKEN`
- Verify token is stored in localStorage/cookies

### Token Expired
- Implement token refresh
- Ask user to login again

## 📖 Complete Example Flow

See `src/routers/auth_jwt_example.py` for a complete working example!

## 🔗 Resources

- [JWT.io](https://jwt.io/) - Decode and inspect tokens
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Your JWT secret is now configured and ready to use!** 🎉

