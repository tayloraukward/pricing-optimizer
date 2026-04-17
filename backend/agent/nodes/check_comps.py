from agent.model import AgentState

def check_comps(state: AgentState) -> str:
    """Ensure we have enough USA-based comps"""
    if len(state.comparable_cars) < 3:
        return "insufficient_comps_handler"
    return "calculate_price"
