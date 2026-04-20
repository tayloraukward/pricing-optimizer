import logging
from agent.model import AgentState, ValuationResult

logger = logging.getLogger(__name__)

# Guardrail constants
MAX_REASONABLE_PRICE = 500_000  # $500k absolute max
MIN_REASONABLE_PRICE = 500       # $500 absolute min
MAX_RANGE_SPREAD = 0.50          # Price range can't exceed 50% of fair price


def validate_and_clamp(state: AgentState) -> dict:
    """
    Apply guardrails and validation to the calculated price.
    - Ensures price is within reasonable bounds
    - Validates comparable count matches actual comps
    - Checks price range spread is reasonable
    - Adjusts confidence if guardrails were triggered
    """
    logger.info(f"validate_and_clamp called for {state.parsed_details.year} {state.parsed_details.manufacturer} {state.parsed_details.model}")

    valuation = state.valuation

    if not valuation:
        logger.error("No valuation found in state - cannot validate")
        return {
            "valuation": None,
            "final_message": "Unable to calculate price - no valuation generated"
        }

    original_valuation = valuation.model_copy()
    guardrails_triggered = []
    adjustments_made = []

    logger.debug(f"Original valuation: ${valuation.fair_price:,.2f}, range: ${valuation.price_range_low:,.2f} - ${valuation.price_range_high:,.2f}")

    # Guardrail 1: Clamp fair_price to reasonable bounds
    if valuation.fair_price > MAX_REASONABLE_PRICE:
        logger.warning(f"Guardrail triggered: fair_price ${valuation.fair_price:,.2f} exceeds max ${MAX_REASONABLE_PRICE:,.2f}")
        guardrails_triggered.append(f"fair_price clamped from ${valuation.fair_price:,.2f} to ${MAX_REASONABLE_PRICE:,.2f}")
        valuation.fair_price = MAX_REASONABLE_PRICE
        adjustments_made.append("fair_price_max_clamp")

    if valuation.fair_price < MIN_REASONABLE_PRICE:
        logger.warning(f"Guardrail triggered: fair_price ${valuation.fair_price:,.2f} below min ${MIN_REASONABLE_PRICE:,.2f}")
        guardrails_triggered.append(f"fair_price clamped from ${valuation.fair_price:,.2f} to ${MIN_REASONABLE_PRICE:,.2f}")
        valuation.fair_price = MIN_REASONABLE_PRICE
        adjustments_made.append("fair_price_min_clamp")

    # Guardrail 2: Ensure range_low < fair_price < range_high
    if valuation.price_range_low >= valuation.fair_price:
        logger.warning(f"Guardrail triggered: price_range_low ${valuation.price_range_low:,.2f} >= fair_price ${valuation.fair_price:,.2f}")
        old_low = valuation.price_range_low
        valuation.price_range_low = valuation.fair_price * 0.85  # 15% below
        guardrails_triggered.append(f"price_range_low adjusted from ${old_low:,.2f} to ${valuation.price_range_low:,.2f}")
        adjustments_made.append("range_low_adjustment")

    if valuation.price_range_high <= valuation.fair_price:
        logger.warning(f"Guardrail triggered: price_range_high ${valuation.price_range_high:,.2f} <= fair_price ${valuation.fair_price:,.2f}")
        old_high = valuation.price_range_high
        valuation.price_range_high = valuation.fair_price * 1.15  # 15% above
        guardrails_triggered.append(f"price_range_high adjusted from ${old_high:,.2f} to ${valuation.price_range_high:,.2f}")
        adjustments_made.append("range_high_adjustment")

    # Guardrail 3: Check range spread isn't too wide
    range_spread = (valuation.price_range_high - valuation.price_range_low) / valuation.fair_price
    if range_spread > MAX_RANGE_SPREAD:
        logger.warning(f"Guardrail triggered: range spread {range_spread:.1%} exceeds max {MAX_RANGE_SPREAD:.1%}")
        # Tighten the range around fair_price
        valuation.price_range_low = valuation.fair_price * (1 - MAX_RANGE_SPREAD/2)
        valuation.price_range_high = valuation.fair_price * (1 + MAX_RANGE_SPREAD/2)
        guardrails_triggered.append(f"price range tightened to {MAX_RANGE_SPREAD:.0%} spread")
        adjustments_made.append("range_spread_clamp")

    # Guardrail 4: Verify comparable_count matches actual comps
    actual_comps = len(state.comparable_cars)
    if valuation.comparable_count != actual_comps:
        original_count = valuation.comparable_count
        logger.warning(f"Guardrail triggered: comparable_count mismatch - reported {original_count}, actual {actual_comps}")
        valuation.comparable_count = actual_comps
        adjustments_made.append("comparable_count_correction")

    # Guardrail 5: Lower confidence if guardrails were triggered
    if guardrails_triggered and valuation.confidence == "high":
        logger.info("Lowering confidence from 'high' to 'medium' due to guardrail triggers")
        valuation.confidence = "medium"
        adjustments_made.append("confidence_lowered_due_to_guardrails")

    # Log summary
    if guardrails_triggered:
        logger.warning(f"Guardrails applied: {len(guardrails_triggered)} adjustments")
        for trigger in guardrails_triggered:
            logger.warning(f"  - {trigger}")
    else:
        logger.info("All guardrails passed - no adjustments needed")

    logger.info(f"Final validated price: ${valuation.fair_price:,.2f} (confidence: {valuation.confidence})")
    logger.debug(f"Adjustments made: {adjustments_made}")

    return {
        "valuation": valuation,
        "final_message": None 
    }
