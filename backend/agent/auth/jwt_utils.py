import os
import jwt
from typing import Optional, Dict, Any
from datetime import datetime
from functools import lru_cache


@lru_cache()
def get_supabase_jwt_secret() -> str:
    """
    Get the Supabase JWT secret from environment variables.
    Uses SUPABASE_SECRET_API_KEY (service role key) which contains the JWT secret.
    """
    # Try the secret API key first (this is what the user has set)
    secret = os.getenv("SUPABASE_SECRET_API_KEY")
    
    # Fallback to other common env var names
    if not secret:
        secret = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not secret:
        raise ValueError(
            "SUPABASE_SECRET_API_KEY environment variable must be set. "
            "This is your Supabase service role key from the app platform."
        )
    
    return secret


def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Supabase JWT token.
    
    Args:
        token: The JWT token from the Authorization header (without "Bearer " prefix)
    
    Returns:
        The decoded token payload if valid, None if invalid
    """
    try:
        secret = get_supabase_jwt_secret()
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from a valid Supabase token.
    
    Returns:
        Dict with user info including 'sub' (user UUID), 'email', etc.
    """
    payload = verify_supabase_token(token)
    
    if not payload:
        return None
    
    # Extract key user fields from the JWT payload
    # Supabase auth JWTs typically contain:
    # - sub: user UUID
    # - email: user's email
    # - role: user's role (authenticated, anon)
    # - aud: audience (authenticated)
    # - iat: issued at
    # - exp: expiration
    
    return {
        "id": payload.get("sub"),  # User UUID
        "email": payload.get("email"),
        "role": payload.get("role"),
        "aud": payload.get("aud"),
        "raw_payload": payload,
    }


def is_token_valid(token: str) -> bool:
    """Quick check if a token is valid"""
    return verify_supabase_token(token) is not None
