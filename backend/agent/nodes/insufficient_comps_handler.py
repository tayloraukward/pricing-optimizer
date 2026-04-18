from agent.model import AgentState

def insufficient_comps_handler(state: AgentState) -> dict:
    """Handle case when fewer than 3 comparable cars are found"""
    return {
        "final_message": "Sorry, no similar vehicles in our database",
        "comparable_cars": []  # Ensure empty list for consistency
    }
