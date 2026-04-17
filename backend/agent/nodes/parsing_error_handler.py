from agent.model import AgentState

def parsing_error_handler(state: AgentState) -> dict:
    """Handle parsing errors by setting final message"""
    return {
        "final_message": f"Could not parse car details: {state.parsing_error}"
    }
