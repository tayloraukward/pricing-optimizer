from agent.model import AgentState

def find_comps(state: AgentState) -> dict:
    """Query Supabase for similar cars"""
    # TODO: Implement database query
    return {
        "comparable_cars": [],
        "lookup_error": None
    }
