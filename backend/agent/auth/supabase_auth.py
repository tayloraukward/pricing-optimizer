import os
from supabase import create_client, Client
from functools import lru_cache


@lru_cache()
def get_supabase_admin_client() -> Client:
    """
    Get a Supabase client with admin/service role privileges.
    
    WARNING: This client bypasses RLS policies. Only use it for admin operations
    like creating users, fetching all records, etc.
    
    Requires:
        - SUPABASE_URL: Your Supabase project URL
        - SUPABASE_SECRET_API_KEY: The service_role key (NOT the anon key)
    
    Returns:
        Supabase client with admin privileges
    """
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SECRET_API_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SECRET_API_KEY must be set in environment variables. "
            "Do not use the anon key - you need the service_role key for admin operations."
        )
    
    return create_client(url, service_key)


def get_user_by_id(user_id: str) -> dict:
    """
    Fetch a user by their UUID from Supabase Auth.
    Requires admin client.
    
    Args:
        user_id: The UUID of the user to fetch
        
    Returns:
        User object with email, id, created_at, etc.
        
    Raises:
        Exception if user not found or auth error
    """
    supabase = get_supabase_admin_client()
    
    # Use admin.get_user_by_id() to fetch any user
    response = supabase.auth.admin.get_user_by_id(user_id)
    
    if not response.user:
        raise Exception(f"User not found: {user_id}")
    
    return {
        "id": response.user.id,
        "email": response.user.email,
        "created_at": response.user.created_at,
        "updated_at": response.user.updated_at,
        "user_metadata": response.user.user_metadata,
        "app_metadata": response.user.app_metadata,
    }


def list_users() -> list:
    """
    List all users in the Supabase Auth system.
    Requires admin client.
    
    Returns:
        List of user objects
    """
    supabase = get_supabase_admin_client()
    
    response = supabase.auth.admin.list_users()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "user_metadata": user.user_metadata,
        }
        for user in response.users
    ]
