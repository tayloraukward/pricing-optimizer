from typing import List, Optional, Dict, Any
from supabase import Client

from agent.dal.cars_db import get_supabase_client
from agent.model import SavedValuation


def get_saved_valuations_for_user(user_id: str) -> List[SavedValuation]:
    """
    Fetch all saved valuations for a specific user.
    Uses the regular client - RLS policies ensure users only see their own data.
    
    Args:
        user_id: The UUID of the authenticated user
        
    Returns:
        List of SavedValuation objects
    """
    supabase: Client = get_supabase_client()
    
    response = (
        supabase
        .table("saved_valuations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    
    return [SavedValuation(**row) for row in response.data]


def get_saved_valuation_by_id(valuation_id: str, user_id: str) -> Optional[SavedValuation]:
    """
    Fetch a specific saved valuation by ID, ensuring it belongs to the user.
    RLS policies ensure users can only access their own valuations.
    
    Args:
        valuation_id: UUID of the saved valuation
        user_id: UUID of the authenticated user
        
    Returns:
        SavedValuation if found and belongs to user, None otherwise
    """
    supabase: Client = get_supabase_client()
    
    response = (
        supabase
        .table("saved_valuations")
        .select("*")
        .eq("id", valuation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    
    if not response.data:
        return None
    
    return SavedValuation(**response.data)


def save_valuation(
    user_id: str,
    title: str,
    parsed_car: Dict[str, Any],
    valuation_result: Dict[str, Any]
) -> SavedValuation:
    """
    Save a new vehicle valuation for a user.
    
    Args:
        user_id: UUID of the authenticated user
        title: User-provided title for the saved valuation
        parsed_car: Parsed car details (JSONB)
        valuation_result: Valuation result (JSONB)
        
    Returns:
        The newly created SavedValuation
    """
    supabase: Client = get_supabase_client()
    
    data = {
        "user_id": user_id,
        "title": title,
        "parsed_car": parsed_car,
        "valuation_result": valuation_result,
    }
    
    response = (
        supabase
        .table("saved_valuations")
        .insert(data)
        .execute()
    )
    
    return SavedValuation(**response.data[0])


def delete_saved_valuation(valuation_id: str, user_id: str) -> bool:
    """
    Delete a saved valuation. RLS policies ensure users can only delete their own.
    
    Args:
        valuation_id: UUID of the valuation to delete
        user_id: UUID of the authenticated user
        
    Returns:
        True if deleted, False if not found or not owned by user
    """
    supabase: Client = get_supabase_client()
    
    response = (
        supabase
        .table("saved_valuations")
        .delete()
        .eq("id", valuation_id)
        .eq("user_id", user_id)
        .execute()
    )
    
    # If we got data back, something was deleted
    return len(response.data) > 0
