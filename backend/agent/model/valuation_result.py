from pydantic import BaseModel, Field, field_validator


class ValuationResult(BaseModel):
    fair_price: float = Field(..., gt=0, description="Calculated fair market price")
    price_range_low: float = Field(..., gt=0)
    price_range_high: float = Field(..., gt=0)
    explanation: str = Field(..., description="Why this price was suggested")
    comparable_count: int = Field(..., ge=3, description="Number of comps used")
    confidence: str = Field(..., pattern="^(low|medium|high)$")
    
    @field_validator("fair_price", "price_range_low", "price_range_high")
    @classmethod
    def round_to_dollar(cls, v: float) -> float:
        """Round price values to the nearest whole dollar."""
        return round(v)
