from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_utils import get_user_from_token

# Security scheme for FastAPI docs
security = HTTPBearer(auto_error=False)


def get_bearer_token_from_request(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header in FastAPI request"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    # Extract token after "Bearer "
    token = auth_header[7:]  # "Bearer " is 7 characters
    return token if token else None


async def require_auth_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """
    FastAPI dependency to require authentication.
    Use this as: user: dict = Depends(require_auth_dependency)
    
    Returns:
        User dict with 'id', 'email', 'role'
    
    Raises:
        HTTPException 401 if authentication fails
    """
    # Try credentials from security first, then from request header
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = get_bearer_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Use: 'Bearer <token>'"
        )
    
    # Verify token and get user info
    user = get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    if not user.get("id"):
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID"
        )
    
    return user


async def optional_auth_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication.
    Use this as: user: Optional[dict] = Depends(optional_auth_dependency)
    
    Returns:
        User dict with 'id', 'email', 'role' or None if not authenticated
    """
    # Try credentials from security first, then from request header
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = get_bearer_token_from_request(request)
    
    if not token:
        return None
    
    # Try to get user info if token exists
    return get_user_from_token(token)


# Convenience function for manual token extraction in WebSocket handlers
def get_token_from_headers(headers: dict) -> Optional[str]:
    """Extract Bearer token from headers dict (for WebSockets)"""
    auth_header = headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    return token if token else None
