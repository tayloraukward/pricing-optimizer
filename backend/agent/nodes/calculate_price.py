import os
import logging
from agent.model import AgentState, ValuationResult, Car
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def calculate_price(state: AgentState) -> dict:
    """
    Calculate fair price from comparable cars using LLM analysis.
    Compares the target vehicle to comparable listings and suggests a fair market price.
    """
    logger.info(f"calculate_price called with {len(state.comparable_cars)} comparable cars")

    if not state.parsed_details:
        logger.error("Cannot calculate price: parsed_details is None")
        return {
            "valuation": None,
            "lookup_error": "Cannot calculate price without parsed car details"
        }

    parsed = state.parsed_details
    comps = state.comparable_cars

    logger.info(f"Calculating price for: {parsed.year} {parsed.manufacturer} {parsed.model}")

    # Build the system prompt for LLM analysis
    system_prompt = _build_pricing_prompt(parsed, comps)

    try:
        # Use OpenAI structured outputs with Pydantic
        response = client.beta.chat.completions.parse(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Analyze the comparable cars and provide a fair market price for the target vehicle."}
            ],
            response_format=ValuationResult,
        )

        valuation = response.choices[0].message.parsed

        logger.info(f"Price calculation successful: ${valuation.fair_price:,.2f}")
        logger.info(f"Price range: ${valuation.price_range_low:,.2f} - ${valuation.price_range_high:,.2f}")
        logger.info(f"Confidence: {valuation.confidence}, Comps used: {valuation.comparable_count}")
        logger.debug(f"Explanation: {valuation.explanation}")

        return {
            "valuation": valuation,
            "lookup_error": None
        }

    except Exception as e:
        logger.error(f"Price calculation failed: {e}", exc_info=True)
        return {
            "valuation": None,
            "lookup_error": f"Price calculation failed: {str(e)}"
        }


def _build_pricing_prompt(parsed, comps: list[Car]) -> str:
    """
    Build a detailed prompt comparing the target car to comparable listings.
    """
    # Format target car details
    target_details = f"""
TARGET VEHICLE TO PRICE:
- Year: {parsed.year}
- Make: {parsed.manufacturer}
- Model: {parsed.model}
- Mileage: {parsed.mileage if parsed.mileage else 'Not specified'}
- Condition: {parsed.condition if parsed.condition else 'Not specified'}
"""

    # Format comparable cars
    comps_details = "\nCOMPARABLE LISTINGS:\n"
    for i, car in enumerate(comps, 1):
        price_str = f"${car.price:,.0f}" if car.price else "Price not listed"

        # Include description if available (truncated for readability)
        description = car.description
        if description and len(description) > 200:
            description = description[:200] + "..."

        comp_detail = f"""
Car #{i}:
  - Year: {car.year}
  - Price: {price_str}
  - Mileage: {car.odometer if car.odometer else 'Not specified'}
  - Condition: {car.condition if car.condition else 'Not specified'}
  - Location: {car.state}
  - Fuel: {car.fuel if car.fuel else 'Not specified'}
  - Transmission: {car.transmission if car.transmission else 'Not specified'}
  - Title Status: {car.title_status if car.title_status else 'Not specified'}
  - Posting Date: {car.posting_date if car.posting_date else 'Not specified'}
  - Description: {description if description else 'Not available'}
"""
        comps_details += comp_detail

    prompt = f"""You are an expert automotive appraiser. Your task is to analyze comparable car listings and determine a fair market price for a target vehicle.

{target_details}

{comps_details}

ANALYSIS INSTRUCTIONS:
1. Read each comparable car's DESCRIPTION carefully. Look for important details that impact price:
   - Aftermarket modifications (lift kits, performance upgrades, custom wheels)
   - Known issues or damage mentioned (engine problems, accidents, rust)
   - Premium features (leather seats, sunroof, navigation, premium audio)
   - Maintenance history cues (new tires, recent brakes, fresh oil change)
   - Motivation indicators ("must sell", "moving", "need gone today")
   - Seasonal factors ("winter beater", "summer convertible")

2. Compare the target vehicle to each comparable listing, noting:
   - Year differences (older = lower value, newer = higher value)
   - Mileage impact (lower miles = higher value, high miles = lower value)
   - Condition differences (excellent > good > fair > poor)
   - Title status (clean titles worth more than salvage/rebuilt)
   - Transmission type (automatic vs manual market preferences)
   - Fuel type (gas vs hybrid vs electric market factors)

3. Price Calculation Approach:
   - Start with the average price of comparable listings
   - Adjust up/down based on mileage differences 
   - Adjust for year differences 
   - Adjust for condition differences 
   - Consider regional market factors from the comparable locations

4. Confidence Assessment:
   - HIGH: Many comps (10+), similar specs, recent listings, tight price clustering
   - MEDIUM: Moderate comps (5-9), some variance in specs or prices
   - LOW: Few comps (3-4), significant variance, old listings, outliers present

5. Provide a clear explanation of your reasoning, citing specific comps that influenced your decision.

OUTPUT REQUIREMENTS:
- fair_price: The single best estimate of fair market value (be specific, not rounded)
- price_range_low: Conservative lower bound (10-15% below fair price)
- price_range_high: Optimistic upper bound (10-15% above fair price)
- explanation: 2-4 sentences explaining your analysis and key factors
- comparable_count: Number of comps used in analysis (must be >= 3)
- confidence: "low", "medium", or "high" based on comp quality and consistency

Be objective and data-driven. Base your price on the actual comparable sales, not general market knowledge."""

    return prompt
