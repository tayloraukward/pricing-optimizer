from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.model import AgentState, CarValuationRequest
from agent.nodes.parse_input import parse_input
from agent.fetch_valuation_graph import compiled_graph as fetch_valuation_graph
import logging

app = FastAPI(title="pricing-optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.post("/test-parse")
def test_parse(request: CarValuationRequest):
    """Test endpoint: Parse car description and return structured details"""
    # Create initial state
    state = AgentState(raw_input=request)
    
    # Run parse_input node
    result = parse_input(state)
    
    if result.get("parsing_error"):
        return {
            "success": False,
            "error": result["parsing_error"]
        }
    
    return {
        "success": True,
        "parsed_details": result["parsed_details"].model_dump()
    }

@app.post("/get-valuation")
def get_valuation(request: CarValuationRequest):
    state = AgentState(raw_input=request)
    result = fetch_valuation_graph.invoke(state)
    
    if result.get("final_message"):
        return {
            "success": False,
            "error": result["final_message"]
        }
    
    return {
        "success": True,
        "valuation": result["valuation"].model_dump() if result["valuation"] else None
    }
