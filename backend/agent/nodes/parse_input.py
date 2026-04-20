import logging
from agent.model import AgentState, ParsedCarDetails
from agent.events import publish_event_sync
from agent.llm import parse_structured

logger = logging.getLogger(__name__)


def parse_input(state: AgentState) -> dict:
    """Extract structured data from raw text using LLM"""
    
    user_description = state.raw_input.description
    
    # Publish start event
    if state.session_id:
        logger.info(f"[PARSE] Publishing start event for session {state.session_id[:8]}...")
        publish_event_sync(
            state.session_id,
            "parse_input",
            "Reading your vehicle description..."
        )
    
    system_prompt = """You are a car detail extraction specialist.

    Given a user's free-text description of a vehicle, extract the following structured information:

    REQUIRED FIELDS (must be determined or extraction fails):
    - year: The model year (1900-2026)
    - manufacturer: The car make/brand (e.g., Honda, Toyota, Ford) - lowercase
    - model: The specific model name ONLY (e.g., civic, camry, tundra, f-150). DO NOT include trim levels. - lowercase

    OPTIONAL FIELDS - ONLY extract if explicitly mentioned in the description. DO NOT GUESS:
    - odometer: The odometer reading in miles (number only, if mentioned)
    - condition: Overall condition - one of: excellent, good, fair, poor, new
    - fuel: Fuel type - one of: gas, diesel, hybrid, electric (if mentioned)
    - transmission: Transmission type - one of: automatic, manual (if mentioned)
    - drive: Drive type - one of: 4wd, fwd, rwd, awd (if mentioned)
    - cylinders: Engine cylinders as string - e.g., "4", "6", "8" (if mentioned)
    - title_status: Title status - one of: clean, salvage, rebuilt, lien, missing (if mentioned)
    - paint_color: Exterior paint color (e.g., "red", "black", "silver") - lowercase (if mentioned)
    - description: Include ALL additional vehicle features, modifications, and details not captured in other fields. This is CRITICAL for accurate valuation. Examples:
      * Aftermarket modifications: "35\" Nitto Ridge Grapplers tires, Fuel Vector Wheels, 3\" leveling kit"
      * Premium features: "leather seats, sunroof, navigation, premium audio"
      * Recent maintenance: "new brakes, fresh oil change, new tires"
      * Known issues: "minor dent on rear bumper, needs new tires"
      * Other details: "smoker-free, garage kept, single owner"

    CRITICAL RULES FOR MODEL EXTRACTION:
    1. Extract ONLY the base model name, NEVER include trim levels (SR5, TRD, EX, LX, Limited, Platinum, etc.)
    2. Examples of correct extraction:
    - "Tundra SR5" → model: "tundra"
    - "Civic EX" → model: "civic"
    - "F-150 Limited" → model: "f-150"
    - "Camry TRD" → model: "camry"
    - "Tundra SR5 with leveling kit" → model: "tundra"
    3. Trim levels to IGNORE: SR5, TRD, Limited, Platinum, EX, LX, Lariat, XLT, Sport, Touring, etc.

    CRITICAL RULES FOR OPTIONAL FIELDS:
    1. ONLY extract a field if the user EXPLICITLY mentions it
    2. Examples:
    - "2018 Tundra, 45k miles, 4x4" → extract: odometer=45000, drive=4wd
    - "2018 Tundra with leather seats" → do NOT extract fuel, transmission, drive, etc.
    - "2018 Tundra, clean title, automatic" → extract: title_status=clean, transmission=automatic
    3. DO NOT infer or guess any values - if not mentioned, leave as null
    4. Normalize all string values to lowercase

    General Rules:
    1. If year, manufacturer, or model cannot be determined, the extraction fails
    2. Normalize manufacturer and model to lowercase ("Honda" → "honda")
    3. Only include optional fields if explicitly mentioned with high confidence
    4. For condition, map descriptions like "great shape" → "excellent", "some wear" → "fair"
    5. If condition is not mentioned, but odometer is greater than 10,000, set condition to "good" (standard used car), otherwise null
    """
    
    try:
        # Use OpenAI facade for structured parsing
        parsed_details = parse_structured(
            system_prompt=system_prompt,
            user_content=f"Extract car details from: \"{user_description}\"",
            response_format=ParsedCarDetails,
        )
        
        # Validate required fields are present
        if parsed_details.year is None or parsed_details.manufacturer is None or parsed_details.model is None:
            return {
                "parsed_details": None,
                "parsing_error": f"Could not extract required fields (year: {parsed_details.year}, manufacturer: {parsed_details.manufacturer}, model: {parsed_details.model})"
            }
        
        # Publish completion event
        if state.session_id:
            publish_event_sync(
                state.session_id,
                "parse_input",
                f"Found {parsed_details.year} {parsed_details.manufacturer} {parsed_details.model}"
            )
        
        return {
            "parsed_details": parsed_details,
            "parsing_error": None
        }
        
    except ValueError as e:
        # Handle model refusal or validation errors
        return {
            "parsed_details": None,
            "parsing_error": f"Parsing failed: {str(e)}"
        }
    except Exception as e:
        # Handle other API errors
        logger.error(f"Unexpected error in parse_input: {e}")
        return {
            "parsed_details": None,
            "parsing_error": f"Parsing failed: {str(e)}"
        }
