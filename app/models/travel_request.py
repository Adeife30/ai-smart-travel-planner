from pydantic import BaseModel
from typing import List

class TravelRequest(BaseModel):
    destination: str
    interests: List[str]
    budget: str
    days: int