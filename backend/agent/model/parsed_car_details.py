from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ParsedCarDetails(BaseModel):
    # Required core fields
    year: int = Field(..., ge=1900, le=2026, description="Model year of the vehicle")
    manufacturer: str = Field(..., min_length=1, description="Car make/brand")
    model: str = Field(..., min_length=1, description="Car model name (base model only, no trim)")
    
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
    description: Optional[str] = Field(None, description="Additional vehicle features, modifications, and details (e.g., aftermarket wheels, leveling kit, premium features, recent maintenance, etc.)")
    
    @field_validator("manufacturer", "model", "fuel", "transmission", "drive", "title_status", "paint_color")
    @classmethod
    def normalize_text(cls, v: str) -> str:
        return v.strip().lower() if v else v
    
    @property
    def mileage(self) -> Optional[int]:
        """Alias for odometer for backward compatibility"""
        return self.odometer