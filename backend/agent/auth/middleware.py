import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_utils import get_user_from_token
from .supabase_auth import verify_jwt_with_supabase

logger = logging.getLogger(__name__)

# Security scheme for FastAPI docs
security = HTTPBearer(auto_error=False)


def get_bearer_token_from_request(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header in FastAPI request"""
    auth_header = request.headers.get("Authorization", "")
    
    logger.info(f"[AUTH] Authorization header received: {auth_header[:30]}...")
    
    if not auth_header.startswith("Bearer "):
        logger.warning("[AUTH] Authorization header does not start with 'Bearer '")
        return None
    
    # Extract token after "Bearer "
    token = auth_header[7:]  # "Bearer " is 7 characters
    logger.info(f"[AUTH] Extracted token (first 20 chars): {token[:20]}...")
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
    logger.info("[AUTH] require_auth_dependency called")
    
    # Try credentials from security first, then from request header
    token = None
    if credentials:
        token = credentials.credentials
        logger.info(f"[AUTH] Token from credentials (first 20 chars): {token[:20]}...")
    elif request:
        token = get_bearer_token_from_request(request)
        logger.info(f"[AUTH] Token from request header (first 20 chars): {token[:20] if token else 'None'}...")
    
    if not token:
        logger.error("[AUTH] No token found in request")
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Use: 'Bearer <token>'"
        )
    
    # Verify token and get user info using Supabase client
    logger.info("[AUTH] Verifying token with Supabase client...")
    user = verify_jwt_with_supabase(token)
    
    if not user:
        logger.error("[AUTH] Supabase token verification failed - token invalid or expired")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    if not user.get("id"):
        logger.error("[AUTH] User object missing ID")
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID"
        )
    
    logger.info(f"[AUTH] Authentication successful for user: {user['id'][:8]}...")
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
    
    # Try to get user info if token exists using Supabase client
    return verify_jwt_with_supabase(token)


# Convenience function for manual token extraction in WebSocket handlers
def get_token_from_headers(headers: dict) -> Optional[str]:
    """Extract Bearer token from headers dict (for WebSockets)"""
    auth_header = headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    return token if token else None
