from fastapi import APIRouter
from app.models.travel_request import TravelRequest
from app.services.google_places import get_candidate_places
from app.services.prompt_builder import build_itinerary_prompt
from app.services.groq_client import generate_itinerary_with_groq
from app.services.validator import validate_itinerary

router = APIRouter()

@router.post("/generate-itinerary")
def generate_itinerary(request: TravelRequest):
    candidate_places = get_candidate_places(request.destination)

    prompt = build_itinerary_prompt(
        destination=request.destination,
        interests=request.interests,
        budget=request.budget,
        days=request.days,
        candidate_places=candidate_places
    )

    itinerary_text = generate_itinerary_with_groq(prompt)
    validation_result = validate_itinerary(itinerary_text, candidate_places)

    if not validation_result["valid"]:
        return {
            "destination": request.destination,
            "validation_passed": False,
            "error": validation_result["error"],
            "raw_llm_output": itinerary_text
        }

    return {
        "destination": request.destination,
        "validation_passed": True,
        "itinerary": validation_result["data"]
    }