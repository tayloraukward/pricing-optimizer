from typing import TypedDict, Annotated, Optional, List
from pydantic import BaseModel
import operator
from agent.model import ParsedCarDetails, Car, ValuationResult, CarValuationRequest

class AgentState(BaseModel):
    raw_input: CarValuationRequest
    session_id: Optional[str] = None  # For event correlation
    
    parsed_details: Optional[ParsedCarDetails] = None
    parsing_error: Optional[str] = None
    
    comparable_cars: List[Car] = []
    lookup_error: Optional[str] = None
    
    valuation: Optional[ValuationResult] = None
    
    retry_count: int = 0
    final_message: Optional[str] = None