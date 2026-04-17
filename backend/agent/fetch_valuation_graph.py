from langgraph.graph import StateGraph, END
from agent.model import AgentState
from agent.nodes import (
    parse_input,
    check_parsing,
    find_comps,
    check_comps,
    calculate_price,
    validate_and_clamp,
    parsing_error_handler,
)

graph = StateGraph(AgentState)

graph.add_node("parse_input", parse_input)
graph.add_node("check_parsing", check_parsing)
graph.add_node("find_comps", find_comps)
graph.add_node("check_comps", check_comps)
graph.add_node("calculate_price", calculate_price)
graph.add_node("validate_and_clamp", validate_and_clamp)
graph.add_node("parsing_error_handler", parsing_error_handler)

graph.set_entry_point("parse_input")
graph.add_conditional_edges(
    "parse_input",           
    check_parsing,    
    {                  
        "find_comps": "find_comps",
        "parsing_error_handler": "parsing_error_handler"
    }
)

graph.add_edge("find_comps", END) 
graph.add_edge("parsing_error_handler", END)