from fastapi import FastAPI
from app.routes.itinerary import router as itinerary_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI Smart Travel Planner API is running"}

app.include_router(itinerary_router)