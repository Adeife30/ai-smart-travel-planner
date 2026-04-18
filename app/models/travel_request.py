from pydantic import BaseModel
from typing import List, Optional


class TravelRequest(BaseModel):
    destination: str
    days: int
    budget: Optional[str] = None
    interests: List[str]
    transport_mode: Optional[str] = None
    trip_style: Optional[str] = None