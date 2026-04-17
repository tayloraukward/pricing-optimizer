from langgraph.graph import StateGraph, END
from agent.model import AgentState, ParsedCarDetails, Car, ValuationResult

# Define your nodes (each receives state, returns updates)
def parse_input(state: AgentState) -> dict:
    """Extract structured data from raw text using LLM"""
    # Returns: {"parsed_details": ParsedCarDetails(...), ...}
    pass

def check_parsing(state: AgentState) -> str:
    """Decide which node to go to next"""
    # Returns: "find_comps" or "retry"
    pass

def find_comps(state: AgentState) -> dict:
    """Query Supabase for similar cars"""
    # Returns: {"comparable_cars": [Car, Car, ...]}
    pass

def check_comps(state: AgentState) -> str:
    """Ensure we have enough USA-based comps"""
    # Returns: "calculate_price" or "error_no_comps"
    pass

def calculate_price(state: AgentState) -> dict:
    """Calculate fair price from comparable cars"""
    # Returns: {"valuation": ValuationResult(...)}
    pass

def validate_and_clamp(state: AgentState) -> dict:
    """Apply guardrails, clamp if necessary"""
    pass