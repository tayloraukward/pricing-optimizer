from langgraph.graph import StateGraph, END
from agent.model import AgentState, ParsedCarDetails, Car, ValuationResult

# Define your nodes (each receives state, returns updates)
def parse_input(state: AgentState) -> dict:
    """Extract structured data from raw text using LLM""""
    return {
        "parsed_details": [state.raw_input],
        "parsing_error": None
    }

def check_parsing(state: AgentState) -> str:
    """Decide which node to go to next"""
    if state.parsing_error is not None:
        return "parsing_error_handler"
    return "find_comps"

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

graph = StateGraph(AgentState)

graph.add_node("parse_input", parse_input)
graph.add_node("check_parsing", check_parsing)
graph.add_node("find_comps", find_comps)
graph.add_node("check_comps", check_comps)
graph.add_node("calculate_price", calculate_price)
graph.add_node("validate_and_clamp", validate_and_clamp)

graph.set_entry_point("parse_input")
graph.add_conditional_edges(
    "parse_input",           # source node
    check_parsing,     # function that returns next node name
    {                  # map return values to node names
        "find_comps": "find_comps",
        "parsing_error_handler": "parsing_error_handler"
    }
)

graph.add_edge("find_comps", END) 
graph.add_edge("parsing_error_handler", END)