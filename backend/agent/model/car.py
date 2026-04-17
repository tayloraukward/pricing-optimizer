from datetime import date
from pydantic import BaseModel, Field

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
    condition: str | None
    cylinders: str | None
    fuel: str | None
    odometer: int | None  # Note: your DB uses "odometer", not "mileage"
    title_status: str | None
    transmission: str | None
    vin: str | None
    drive: str | None
    size: str | None
    type: str | None
    paint_color: str | None
    
    # Media
    image_url: str | None
    description: str | None
    
    # Location
    county: str | None
    state: str
    lat: float | None
    long: float | None
    
    # Metadata
    posting_date: date | None
    
    @property
    def age(self) -> int:
        from datetime import datetime
        return datetime.now().year - self.year