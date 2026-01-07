from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import UserModel
from ..utils.jwt_utils import decode_access_token


class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request, call_next: Callable):
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Decode JWT token
            payload = decode_access_token(token)
            
            if payload:
                # Extract user info from token
                user_id = payload.get("sub")
                user_email = payload.get("email")
                user_role = payload.get("role")
                
                # Try to fetch full user from database
                try:
                    if user_id:
                        user = await UserModel.find_by_id(user_id)
                        if user:
                            request.state.user = user
                        else:
                            # Use token data if user not in DB
                            request.state.user = {
                                "id": user_id,
                                "email": user_email,
                                "role": user_role,
                                "firstName": "User",
                                "lastName": ""
                            }
                    else:
                        # Use token data
                        request.state.user = {
                            "id": user_id or "unknown",
                            "email": user_email,
                            "role": user_role,
                            "firstName": "User",
                            "lastName": ""
                        }
                except Exception as e:
                    print(f"Error fetching user: {e}")
                    # Fallback to token data
                    request.state.user = {
                        "id": user_id or "unknown",
                        "email": user_email,
                        "role": user_role,
                        "firstName": "User",
                        "lastName": ""
                    }
            else:
                # Invalid token - set no user (will fail auth checks)
                request.state.user = None
        else:
            # No auth header - set no user
            request.state.user = None

        response = await call_next(request)
        return response


# Dependency function for FastAPI
async def get_current_user(request: Request) -> dict:
    """Get current user from request state"""
    if not hasattr(request.state, "user") or request.state.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.user


async def require_instructor(request: Request) -> dict:
    """Require instructor or admin role"""
    user = await get_current_user(request)
    if user.get("role") not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Instructor access required"
        )
    return user

