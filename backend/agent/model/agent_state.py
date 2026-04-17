from typing import TypedDict, Annotated
from pydantic import BaseModel
import operator
from agent.model import ParsedCarDetails, Car, ValuationResult, CarValuationRequest

# We need to track what stage we're in and any errors
class AgentState(BaseModel):
    # Input
    raw_input: CarValuationRequest
    
    # Parsing stage
    parsed_details: ParsedCarDetails | None = None
    parsing_error: str | None = None
    
    # Database lookup stage  
    comparable_cars: list[Car] = []
    lookup_error: str | None = None
    
    # Final result
    valuation: ValuationResult | None = None
    
    # Control flow
    retry_count: int = 0
    final_message: str | None = None  # For "Sorry no similar vehicles..." fallback