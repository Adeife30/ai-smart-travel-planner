from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.itinerary import router as itinerary_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Smart Travel Planner API is running"}

app.include_router(itinerary_router)