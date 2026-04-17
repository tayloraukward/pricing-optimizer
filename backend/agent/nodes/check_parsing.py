from agent.model import AgentState

def check_parsing(state: AgentState) -> str:
    """Decide which node to go to next based on parsing result"""
    if state.parsing_error is not None:
        return "parsing_error_handler"
    return "find_comps"
