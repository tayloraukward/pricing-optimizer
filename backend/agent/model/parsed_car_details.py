from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ParsedCarDetails(BaseModel):
    """Parsed vehicle details from user input, with support for refusing non-vehicle input."""
    
    # Vehicle validation flag
    is_vehicle: bool = Field(
        True, 
        description="Whether the input is actually a vehicle description. Set to False for API keys, code, random text, etc."
    )
    refusal_reason: Optional[str] = Field(
        None, 
        description="Explanation of why input was refused if is_vehicle is False"
    )
    
    # Core identification fields - required only if is_vehicle is True
    year: Optional[int] = Field(
        None, ge=1900, le=2026, 
        description="Model year of the vehicle (null if not a vehicle or cannot determine)"
    )
    manufacturer: Optional[str] = Field(
        None, min_length=1, 
        description="Car make/brand (null if not a vehicle or cannot determine)"
    )
    model: Optional[str] = Field(
        None, min_length=1, 
        description="Car model name, base model only no trim (null if not a vehicle or cannot determine)"
    )
    
    # Optional fields - ONLY extract if explicitly mentioned in the description
    odometer: Optional[int] = Field(None, ge=0, description="Odometer reading in miles if mentioned")
    condition: Optional[str] = Field(None, description="Overall condition (excellent, good, fair, poor)")
    fuel: Optional[str] = Field(None, description="Fuel type (gas, diesel, hybrid, electric)")
    transmission: Optional[str] = Field(None, description="Transmission type (automatic, manual)")
    drive: Optional[str] = Field(None, description="Drive type (4wd, fwd, rwd, awd)")
    cylinders: Optional[str] = Field(None, description="Engine cylinders (e.g., '6', '8', '4')")
    title_status: Optional[str] = Field(None, description="Title status (clean, salvage, rebuilt, etc.)")
    paint_color: Optional[str] = Field(None, description="Exterior paint color")
    
    # Description for additional features not captured in structured fields
    description: Optional[str] = Field(
        None, 
        description="Additional vehicle features, modifications, and details"
    )
    
    @field_validator("manufacturer", "model", "fuel", "transmission", "drive", "title_status", "paint_color")
    @classmethod
    def normalize_text(cls, v: str) -> str:
        return v.strip().lower() if v else v
    
    @property
    def mileage(self) -> Optional[int]:
        """Alias for odometer for backward compatibility"""
        return self.odometer