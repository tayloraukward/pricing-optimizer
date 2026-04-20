"""In-memory event store for session-based progress tracking."""

import asyncio
import time
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# In-memory storage: session_id -> list of events
event_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

# Active queues for real-time streaming: session_id -> Queue
event_queues: Dict[str, asyncio.Queue] = {}

# Reference to main event loop (set by main.py)
_main_loop: Optional[asyncio.AbstractEventLoop] = None

def set_main_loop(loop: asyncio.AbstractEventLoop):
    """Set the main event loop reference for thread-safe event publishing."""
    global _main_loop
    _main_loop = loop


def publish_event_sync(session_id: str, step: str, message: str, data: Optional[dict] = None) -> None:
    """Thread-safe sync version that schedules on the main event loop."""
    event = {
        "step": step,
        "message": message,
        "timestamp": time.time(),
        "data": data or {}
    }
    
    logger.info(f"[EVENT-SYNC] Publishing to session {session_id[:8]}...: {step} - {message}")
    
    # Store in history (sync operation)
    event_store[session_id].append(event)
    
    # Schedule queue update on main event loop
    if _main_loop and session_id in event_queues:
        try:
            # Use call_soon_threadsafe to schedule on main loop from any thread
            _main_loop.call_soon_threadsafe(lambda: _put_in_queue(session_id, event))
            logger.info(f"[EVENT-SYNC] Scheduled for session {session_id[:8]}...")
        except Exception as e:
            logger.warning(f"[EVENT-SYNC] Failed to schedule: {e}")
    else:
        logger.warning(f"[EVENT-SYNC] No main loop or queue for session {session_id[:8]}...")


def _put_in_queue(session_id: str, event: dict):
    """Helper to put event in queue from the main loop."""
    if session_id in event_queues:
        try:
            event_queues[session_id].put_nowait(event)
            logger.debug(f"[EVENT-SYNC] Put in queue for session {session_id[:8]}...")
        except Exception as e:
            logger.warning(f"[EVENT-SYNC] Failed to put in queue: {e}")


async def publish_event(session_id: str, step: str, message: str, data: Optional[dict] = None) -> None:
    """Publish an event to the store and notify any waiting streams."""
    event = {
        "step": step,
        "message": message,
        "timestamp": time.time(),
        "data": data or {}
    }
    
    logger.info(f"[EVENT] Publishing to session {session_id[:8]}...: {step} - {message}")
    
    # Store in history
    event_store[session_id].append(event)
    logger.debug(f"[EVENT] Stored in event_store. Total events for session: {len(event_store[session_id])}")
    
    # Notify real-time consumers
    if session_id in event_queues:
        try:
            await event_queues[session_id].put(event)
            logger.info(f"[EVENT] Sent to queue for session {session_id[:8]}...")
        except Exception as e:
            logger.warning(f"[EVENT] Failed to send to queue: {e}")
    else:
        logger.warning(f"[EVENT] No active queue for session {session_id[:8]}...") 


def get_events(session_id: str) -> List[Dict[str, Any]]:
    """Get all events for a session."""
    return event_store.get(session_id, []).copy()


def get_or_create_queue(session_id: str) -> asyncio.Queue:
    """Get or create an event queue for a session."""
    if session_id not in event_queues:
        event_queues[session_id] = asyncio.Queue()
    return event_queues[session_id]


def clear_session(session_id: str) -> None:
    """Clear all events and queues for a session."""
    event_store.pop(session_id, None)
    event_queues.pop(session_id, None)


def session_exists(session_id: str) -> bool:
    """Check if a session has any events."""
    return session_id in event_store or session_id in event_queues
