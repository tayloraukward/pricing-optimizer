from typing import TypedDict, Annotated
from pydantic import BaseModel
import operator

# We need to track what stage we're in and any errors
class AgentState(BaseModel):
    # Input
    raw_input: str
    
    # Parsing stage
    parsed_details: ParsedCarDetails | None = None
    parsing_error: str | None = None
    
    # Database lookup stage  
    comparable_cars: list[ComparableCar] = []
    lookup_error: str | None = None
    
    # Final result
    valuation: ValuationResult | None = None
    
    # Control flow
    retry_count: int = 0
    final_message: str | None = None  # For "Sorry no similar vehicles..." fallback