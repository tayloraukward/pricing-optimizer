import os
from typing import Optional
from agent.model import AgentState, Car, ParsedCarDetails
from agent.dal.cars_db import get_supabase_client

def find_comps(state: AgentState) -> dict:
    """Query Supabase for comparable cars within ±3 years, same make/model, within 100k miles"""
    
    if not state.parsed_details:
        return {
            "comparable_cars": [],
            "lookup_error": "No parsed details available to search for comps"
        }
    
    parsed: ParsedCarDetails = state.parsed_details
    supabase = get_supabase_client()
    
    try:
        # Build base query: same manufacturer and model, year within ±3
        year_min = parsed.year - 3
        year_max = parsed.year + 3
        
        query = (
            supabase.table("cars")
            .select("*")
            .eq("manufacturer", parsed.manufacturer)
            .eq("model", parsed.model)
            .gte("year", year_min)
            .lte("year", year_max)
            .gt("price", 0)  # Must have a price listed
        )
        
        # Add mileage filter if target has mileage
        if parsed.mileage is not None:
            mileage_min = max(0, parsed.mileage - 100000)
            mileage_max = parsed.mileage + 100000
            query = query.gte("odometer", mileage_min).lte("odometer", mileage_max)
        
        response = query.limit(50).execute()
        
        if not response.data:
            return {
                "comparable_cars": [],
                "lookup_error": None
            }
        
        # Convert to Car models, skip invalid records
        comparable_cars: list[Car] = []
        for record in response.data:
            try:
                car = Car(**record)
                comparable_cars.append(car)
            except Exception:
                print(f"Skipping invalid car record: {record}")
                continue
        
        return {
            "comparable_cars": comparable_cars,
            "lookup_error": None
        }
        
    except Exception as e:
        return {
            "comparable_cars": [],
            "lookup_error": f"Database query failed: {str(e)}"
        }