"""
Example of how to implement JWT authentication in your auth router
Copy the relevant parts to your auth.py file
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models.user import UserModel
from ..utils.jwt_utils import create_access_token, decode_access_token
import hashlib


router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class RegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    role: str = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current user from JWT token
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Fetch user from database
    user = await UserModel.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.post("/register", response_model=dict)
async def register(request_data: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await UserModel.find_by_email(request_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        # Create new user
        user_data = {
            "firstName": request_data.firstName,
            "lastName": request_data.lastName,
            "email": request_data.email,
            "password": hash_password(request_data.password),
            "role": request_data.role,
            "status": 1,
        }

        user = await UserModel.create(user_data)
        
        # Remove password from response
        user.pop("password", None)
        user.pop("_id", None)
        
        # Create JWT token
        token_data = {
            "sub": user.get("id"),  # Subject (user ID)
            "email": user.get("email"),
            "role": user.get("role"),
        }
        access_token = create_access_token(token_data)
        
        return {
            "success": True,
            "message": "Registration successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register"
        )


@router.post("/login", response_model=dict)
async def login(request_data: LoginRequest):
    """Login user and return JWT token"""
    try:
        # Find user by email
        user = await UserModel.find_by_email(request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check password
        hashed_password = hash_password(request_data.password)
        if user.get("password") != hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if account is active
        if user.get("status") == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not activated"
            )

        # Remove password from response
        user.pop("password", None)
        user.pop("_id", None)
        
        # Create JWT token
        token_data = {
            "sub": user.get("id"),  # Subject (user ID)
            "email": user.get("email"),
            "role": user.get("role"),
        }
        access_token = create_access_token(token_data)

        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information from JWT token"""
    return {
        "success": True,
        "user": current_user
    }


@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh JWT token"""
    token_data = {
        "sub": current_user.get("id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
    }
    new_token = create_access_token(token_data)
    
    return {
        "success": True,
        "access_token": new_token,
        "token_type": "bearer"
    }

