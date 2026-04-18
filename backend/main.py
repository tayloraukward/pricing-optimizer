from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.model import AgentState, CarValuationRequest
from agent.nodes.parse_input import parse_input

app = FastAPI(title="pricing-optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


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
