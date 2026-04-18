import os
from openai import OpenAI
from agent.model import AgentState, ParsedCarDetails

# Initialize OpenAI client
# In production, use environment variable: os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_input(state: AgentState) -> dict:
    """Extract structured data from raw text using LLM"""
    
    user_description = state.raw_input.description
    
    system_prompt = """You are a car detail extraction specialist. 
    
Given a user's free-text description of a vehicle, extract the following structured information:
- year: The model year (1900-2026)
- manufacturer: The car make/brand (e.g., Honda, Toyota, Ford)
- model: The specific model name (e.g., Civic, Camry, F-150)
- mileage: The odometer reading in miles (if mentioned)
- condition: Overall condition - one of: excellent, good, fair, poor, new (if mentioned)

Rules:
1. If year, manufacturer, or model cannot be determined, the extraction fails
2. Normalize manufacturer and model names to proper case ("honda" → "Honda")
3. Only include fields you're confident about
4. For condition, map descriptions like "great shape" → "excellent", "some wear" → "fair"
"""
    
    try:
        # Use OpenAI's structured outputs with Pydantic
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # or "gpt-4o" for better accuracy
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract car details from: \"{user_description}\""}
            ],
            response_format=ParsedCarDetails,
            temperature=0.1,  # Low temperature for consistent extraction
        )
        
        parsed_details = response.choices[0].message.parsed
        
        # Validate required fields are present
        if parsed_details.year is None or parsed_details.manufacturer is None or parsed_details.model is None:
            return {
                "parsed_details": None,
                "parsing_error": f"Could not extract required fields (year: {parsed_details.year}, manufacturer: {parsed_details.manufacturer}, model: {parsed_details.model})"
            }
        
        return {
            "parsed_details": parsed_details,
            "parsing_error": None
        }
        
    except Exception as e:
        # Handle API errors, parsing failures, or validation errors
        error_msg = str(e)
        if "Refusal" in error_msg:
            error_msg = "The model refused to parse this input"
        
        return {    
            "parsed_details": None,
            "parsing_error": f"Parsing failed: {error_msg}"
        }
