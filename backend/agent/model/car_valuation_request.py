from pydantic import BaseModel

class CarValuationRequest(BaseModel):
    description: str  # "2018 Honda Civic, 45k miles, good condition"