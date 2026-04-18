from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ParsedCarDetails(BaseModel):
    year: int = Field(..., ge=1900, le=2026, description="Model year of the vehicle")
    manufacturer: str = Field(..., min_length=1, description="Car make/brand")
    model: str = Field(..., min_length=1, description="Car model name")
    mileage: Optional[int] = Field(None, ge=0, description="Odometer reading if mentioned")
    condition: Optional[str] = Field(None, description="Overall condition (excellent, good, fair, poor)")
    
    @field_validator("manufacturer", "model")
    @classmethod
    def normalize_text(cls, v: str) -> str:
        return v.strip().title() if v else v