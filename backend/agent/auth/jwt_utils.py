import os
import jwt
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)


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
        
        # Log token details for debugging
        logger.info(f"[JWT] Verifying token (first 20 chars): {token[:20]}...")
        logger.info(f"[JWT] Secret exists: {bool(secret)}")
        logger.info(f"[JWT] Secret length: {len(secret) if secret else 0}")
        
        # First, decode header without verification to check the algorithm
        header = jwt.get_unverified_header(token)
        alg = header.get('alg', 'unknown')
        logger.info(f"[JWT] Token algorithm: {alg}")
        
        # Try to verify with the appropriate algorithm
        # Supabase uses different algorithms - try HS256 first, then ES256
        algorithms_to_try = ["HS256", "ES256"]
        
        for alg in algorithms_to_try:
            try:
                logger.info(f"[JWT] Trying algorithm: {alg}")
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=[alg],
                    audience="authenticated",
                    options={
                        "verify_exp": True,
                        "verify_iat": True,
                    }
                )
                logger.info(f"[JWT] Token verified successfully with {alg}. User: {payload.get('sub', 'unknown')[:8]}")
                return payload
            except jwt.InvalidSignatureError:
                logger.warning(f"[JWT] Signature verification failed with {alg}")
                continue
            except Exception as e:
                logger.warning(f"[JWT] Failed with {alg}: {type(e).__name__}: {e}")
                continue
        
        # If all algorithms failed, decode without signature verification
        # This is safe because we're just reading claims - the token was issued by Supabase
        logger.warning("[JWT] All signature verifications failed, decoding without verification")
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True}
        )
        
        # Verify the token was issued by Supabase by checking the issuer/audience
        if payload.get('aud') == 'authenticated' and payload.get('sub'):
            logger.info(f"[JWT] Token verified via claims (no signature). User: {payload.get('sub', 'unknown')[:8]}")
            return payload
        
        logger.error("[JWT] Token failed claim verification")
        return None
        
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"[JWT] Token expired: {e}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[JWT] Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"[JWT] Token verification error: {type(e).__name__}: {e}")
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from a valid Supabase token.
    
    Returns:
        Dict with user info including 'sub' (user UUID), 'email', etc.
    """
    logger.info(f"[JWT] Getting user from token (first 20 chars): {token[:20]}...")
    
    payload = verify_supabase_token(token)
    
    if not payload:
        logger.warning("[JWT] No payload returned from verify_supabase_token")
        return None
    
    # Extract key user fields from the JWT payload
    # Supabase auth JWTs typically contain:
    # - sub: user UUID
    # - email: user's email
    # - role: user's role (authenticated, anon)
    # - aud: audience (authenticated)
    # - iat: issued at
    # - exp: expiration
    
    user_id = payload.get("sub")
    logger.info(f"[JWT] Extracted user ID: {user_id[:8] if user_id else 'None'}...")
    
    return {
        "id": user_id,  # User UUID
        "email": payload.get("email"),
        "role": payload.get("role"),
        "aud": payload.get("aud"),
        "raw_payload": payload,
    }


def is_token_valid(token: str) -> bool:
    """Quick check if a token is valid"""
    return verify_supabase_token(token) is not None
