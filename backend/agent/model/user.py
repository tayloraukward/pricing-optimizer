from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """
    User model matching Supabase auth.users table structure.
    Users are managed by Supabase Auth - we only need to track the UUID locally.
    """
    
    # Primary key - UUID from Supabase Auth
    id: str = Field(..., description="UUID from Supabase auth.users")
    
    # User profile info
    email: str = Field(..., description="User's email address from Google Auth")
    
    # Timestamps (managed by Supabase, but we track locally for convenience)
    created_at: Optional[datetime] = Field(default=None, description="When user first signed in")
    updated_at: Optional[datetime] = Field(default=None, description="Last profile update")
    
    # Optional display name (from Google profile)
    display_name: Optional[str] = Field(default=None, description="User's display name from Google")
    
    # Avatar URL from Google
    avatar_url: Optional[str] = Field(default=None, description="URL to user's Google profile picture")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @property
    def is_authenticated(self) -> bool:
        """Always returns True for User objects (anonymous users are handled separately)"""
        return True
