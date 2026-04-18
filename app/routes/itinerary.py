from fastapi import APIRouter, HTTPException

from app.models.travel_request import TravelRequest
from app.services.google_places import get_candidate_places
from app.services.prompt_builder import build_itinerary_messages
from app.services.groq_client import generate_with_groq
from app.services.validator import (
    validate_json_output,
    validate_refs,
    validate_activity_structure,
)


router = APIRouter()

MAX_RETRIES = 2


def enrich_itinerary_with_place_data(itinerary_data, candidate_places):
    enriched_places = []

    for index, place in enumerate(candidate_places, start=1):
        enriched_place = dict(place)
        enriched_place["ref"] = f"P{index}"
        enriched_places.append(enriched_place)

    place_lookup = {place["ref"]: place for place in enriched_places}

    for day in itinerary_data.get("days", []):
        for activity in day.get("activities", []):
            ref = activity.get("ref")
            place = place_lookup.get(ref)

            if not place:
                raise ValueError(f"Unknown ref found during enrichment: {ref}")

            activity["name"] = place["name"]
            activity["place_id"] = place["place_id"]
            activity["category"] = place["category"]
            activity["address"] = place.get("address", "")
            activity["maps_link"] = f"https://www.google.com/maps/place/?q=place_id:{place['place_id']}"

    return itinerary_data


def build_retry_message(last_error: str) -> str:
    return (
        f"Your previous response was rejected: {last_error}. "
        "Return corrected JSON only. "
        "Use only candidate places provided earlier. "
        "Do not invent locations, refs, names, or place_ids. "
        "Copy ref values exactly, for example P1, P2, P3. "
        "Copy place_id values exactly from the candidate list. "
        "Do not shorten, rename, or alter any value. "
        "Output exactly the required number of days. "
        "Output exactly 4 activities per day. "
        "Use these exact times only: 08:00, 11:00, 14:00, 19:00. "
        "Do not repeat the same ref anywhere in the itinerary unless options are extremely limited. "
        "Keep the day realistic and varied. "
        "Return JSON only."
    )


@router.post("/generate-itinerary")
def generate_itinerary(request: TravelRequest):
    try:
        request_data = request.model_dump()
        print("Incoming request data:", request_data)

        candidate_places = get_candidate_places(request_data)
        print("Candidate places found:", len(candidate_places))

        if not candidate_places:
            raise HTTPException(status_code=404, detail="No matching places found")

        messages = build_itinerary_messages(request_data, candidate_places)
        print("Messages built successfully")
        print("MESSAGES TYPE:", type(messages))
        print("MESSAGES VALUE:", messages)

        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            print(f"Groq generation attempt: {attempt + 1}")

            raw_output = generate_with_groq(messages)
            print("Raw LLM output:", raw_output)

            try:
                itinerary_data = validate_json_output(raw_output)
                print("JSON validated successfully")

                validate_refs(itinerary_data, candidate_places)
                validate_activity_structure(itinerary_data, request_data)
                itinerary_data = enrich_itinerary_with_place_data(itinerary_data, candidate_places)

                return {
                    "status": "success",
                    "candidate_count": len(candidate_places),
                    "itinerary": itinerary_data,
                }

            except ValueError as validation_error:
                last_error = str(validation_error)
                print(f"Validation failed on attempt {attempt + 1}: {last_error}")

                if attempt < MAX_RETRIES:
                    messages.append({
                        "role": "user",
                        "content": build_retry_message(last_error),
                    })
                else:
                    raise ValueError(last_error)

    except HTTPException:
        raise

    except ValueError as e:
        print("VALUE ERROR IN /generate-itinerary:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print("Unexpected error in /generate-itinerary:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")