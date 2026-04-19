from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class Car(BaseModel):
    # Primary key
    id: int
    
    # URLs and location
    url: str
    region: str
    region_url: str
    
    # Core pricing and year
    price: float = Field(..., gt=0)
    year: int = Field(..., ge=1900, le=2026)
    
    # Make/model
    manufacturer: str
    model: str
    
    # Vehicle specs
    condition: Optional[str] = None
    cylinders: Optional[str] = None
    fuel: Optional[str] = None
    odometer: Optional[int] = None  # Note: your DB uses "odometer", not "mileage"
    title_status: Optional[str] = None
    transmission: Optional[str] = None
    vin: Optional[str] = None
    drive: Optional[str] = None
    size: Optional[str] = None
    type: Optional[str] = None
    paint_color: Optional[str] = None
    
    # Media
    image_url: Optional[str] = None
    description: Optional[str] = None
    
    # Location
    county: Optional[str] = None
    state: str
    lat: Optional[float] = None
    long: Optional[float] = None
    
    # Metadata
    posting_date: Optional[date] = None
    
    @field_validator('posting_date', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Handle ISO datetime strings like '2021-04-23T18:41:15'
            if 'T' in v:
                return datetime.fromisoformat(v).date()
            return date.fromisoformat(v)
        return v
    
    @property
    def age(self) -> int:
        from datetime import datetime
        return datetime.now().year - self.year