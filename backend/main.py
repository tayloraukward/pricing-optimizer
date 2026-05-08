from fastapi import FastAPI, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List

from agent.model import AgentState, CarValuationRequest, SavedValuation
from agent.nodes.parse_input import parse_input
from agent.fetch_valuation_graph import compiled_graph as fetch_valuation_graph
from agent.events import get_events, get_or_create_queue, clear_session, session_exists, set_main_loop
from agent.auth import require_auth_dependency
from agent.dal.saved_valuations_db import (
    get_saved_valuations_for_user,
    get_saved_valuation_by_id,
    save_valuation,
    delete_saved_valuation,
)

import logging
import sys
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="pricing-optimizer API")

# Thread pool for running graph without blocking event loop
graph_executor = ThreadPoolExecutor(max_workers=4)


@app.on_event("startup")
async def startup_event():
    """Set the main event loop reference for thread-safe event publishing."""
    loop = asyncio.get_running_loop()
    set_main_loop(loop)
    logger.info("[STARTUP] Main event loop reference set for event publishing")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/events/{session_id}")
async def event_stream(session_id: str):
    """Stream real-time progress events for a valuation session."""
    logger.info(f"[STREAM] Client connected for session {session_id[:8]}...")
    
    async def generate():
        # Send any existing events first
        existing_events = get_events(session_id)
        logger.info(f"[STREAM] Sending {len(existing_events)} existing events")
        for event in existing_events:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Wait for new events via queue
        queue = get_or_create_queue(session_id)
        logger.info(f"[STREAM] Queue created, waiting for new events...")
        
        try:
            while True:
                # Wait for next event with timeout (120s to allow for slow LLM calls)
                logger.debug(f"[STREAM] Waiting for next event...")
                event = await asyncio.wait_for(queue.get(), timeout=120.0)
                logger.info(f"[STREAM] Yielding event: {event.get('step')} - {event.get('message')[:50]}...")
                yield f"data: {json.dumps(event)}\n\n"
                
                # Stop if this is the final event
                if event.get("step") == "complete":
                    logger.info(f"[STREAM] Complete event received, closing stream")
                    break
                    
        except asyncio.TimeoutError:
            logger.warning(f"[STREAM] Timeout waiting for events (120s)")
            yield f"data: {json.dumps({'error': 'timeout', 'message': 'No events received for 120 seconds'})}\n\n"
        finally:
            # Clean up session after streaming
            logger.info(f"[STREAM] Cleaning up session {session_id[:8]}...")
            clear_session(session_id)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering if using nginx
        }
    )


@app.post("/get-valuation")
async def get_valuation(request: CarValuationRequest):
    """Process valuation with optional session ID for progress tracking."""
    session_id = request.session_id
    logger.info(f"[API] get_valuation called with session_id: {session_id[:8] if session_id else 'None'}")
    
    state = AgentState(raw_input=request, session_id=session_id)
    
    # Run graph in background thread so event loop can process events
    logger.info(f"[API] Starting graph execution in background thread")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(graph_executor, fetch_valuation_graph.invoke, state)
    logger.info(f"[API] Graph execution completed")
    
    # Publish completion event if session exists
    if session_id:
        logger.info(f"[API] Publishing completion event")
        await publish_completion_event(session_id, result)
    
    if result.get("final_message"):
        return {
            "success": False,
            "error": result["final_message"]
        }
    
    return {
        "success": True,
        "valuation": result["valuation"].model_dump() if result["valuation"] else None
    }


async def publish_completion_event(session_id: str, result: dict):
    """Publish final completion event."""
    from agent.events import publish_event
    
    if result.get("valuation"):
        await publish_event(
            session_id,
            "complete",
            "Valuation complete",
            {"valuation": result["valuation"].model_dump()}
        )
    else:
        await publish_event(
            session_id,
            "error",
            result.get("final_message", "Unknown error"),
            {"error": result.get("final_message")}
        )


# =============================================================================
# Saved Valuations Endpoints (Protected by Authentication)
# =============================================================================

@app.get("/valuations")
async def get_user_valuations(user: dict = Depends(require_auth_dependency)):
    """
    Get all saved valuations for the authenticated user.
    Requires: Authorization: Bearer <supabase_token>
    """
    user_id = user["id"]
    logger.info(f"[API] Fetching valuations for user {user_id[:8]}...")
    
    valuations = get_saved_valuations_for_user(user_id)
    
    return {
        "success": True,
        "valuations": [v.model_dump() for v in valuations]
    }


@app.get("/valuations/{valuation_id}")
async def get_single_valuation(
    valuation_id: str, 
    user: dict = Depends(require_auth_dependency)
):
    """
    Get a specific saved valuation by ID.
    User can only access their own valuations (enforced by RLS).
    """
    user_id = user["id"]
    logger.info(f"[API] Fetching valuation {valuation_id[:8]} for user {user_id[:8]}...")
    
    valuation = get_saved_valuation_by_id(valuation_id, user_id)
    
    if not valuation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Valuation not found")
    
    return {
        "success": True,
        "valuation": valuation.model_dump()
    }


@app.post("/valuations/save")
async def create_saved_valuation(
    data: dict = Body(...),
    user: dict = Depends(require_auth_dependency)
):
    """
    Save a new valuation.
    
    Body:
        - title: str (required)
        - parsed_car: dict (required) - parsed vehicle details
        - valuation_result: dict (required) - valuation result
    """
    user_id = user["id"]
    logger.info(f"[API] Saving valuation for user {user_id[:8]}...")
    
    # Validate required fields
    title = data.get("title")
    parsed_car = data.get("parsed_car")
    valuation_result = data.get("valuation_result")
    
    if not title or not parsed_car or not valuation_result:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail="Missing required fields: title, parsed_car, valuation_result"
        )
    
    try:
        saved = save_valuation(
            user_id=user_id,
            title=title,
            parsed_car=parsed_car,
            valuation_result=valuation_result
        )
        
        logger.info(f"[API] Valuation saved with ID {saved.id[:8]}...")
        
        return {
            "success": True,
            "valuation": saved.model_dump()
        }
        
    except Exception as e:
        logger.error(f"[API] Failed to save valuation: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to save valuation: {str(e)}")


@app.delete("/valuations/{valuation_id}")
async def delete_valuation(
    valuation_id: str,
    user: dict = Depends(require_auth_dependency)
):
    """
    Delete a saved valuation.
    User can only delete their own valuations (enforced by RLS).
    """
    user_id = user["id"]
    logger.info(f"[API] Deleting valuation {valuation_id[:8]} for user {user_id[:8]}...")
    
    deleted = delete_saved_valuation(valuation_id, user_id)
    
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Valuation not found or not owned by user")
    
    return {
        "success": True,
        "message": "Valuation deleted successfully"
    }
