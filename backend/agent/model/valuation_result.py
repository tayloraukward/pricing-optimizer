from pydantic import BaseModel

class ValuationResult(BaseModel):
    fair_price: float = Field(..., gt=0, description="Calculated fair market price")
    price_range_low: float = Field(..., gt=0, lt=price_range_high)
    price_range_high: float = Field(..., gt=0,)
    explanation: str = Field(..., description="Why this price was suggested")
    comparable_count: int = Field(..., ge=3, description="Number of comps used")  # Guardrail!
    confidence: str = Field(..., pattern="^(low|medium|high)$")
