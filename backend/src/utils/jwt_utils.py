"""
JWT Token utilities for authentication
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from jwt.exceptions import InvalidTokenError


# Load JWT configuration from environment
SECRET_KEY = os.environ.get("JWT_SECRET")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 24))


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing user data to encode
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET environment variable is not set")
    
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
    })
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token data or None if invalid
    """
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET environment variable is not set")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        return None


def create_refresh_token(data: Dict) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Dictionary containing user data to encode
    
    Returns:
        Encoded JWT refresh token string
    """
    # Refresh tokens typically last 7 days
    expires_delta = timedelta(days=7)
    return create_access_token(data, expires_delta)


def verify_token(token: str) -> bool:
    """
    Verify if a token is valid
    
    Args:
        token: JWT token string
    
    Returns:
        True if valid, False otherwise
    """
    decoded = decode_access_token(token)
    return decoded is not None

