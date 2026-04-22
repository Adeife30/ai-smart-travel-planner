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
from app.services.directions import get_travel_info


router = APIRouter()

MAX_RETRIES = 2


def add_refs_to_candidate_places(candidate_places):
    enriched_places = []

    for index, place in enumerate(candidate_places, start=1):
        enriched_place = dict(place)
        enriched_place["ref"] = f"P{index}"
        enriched_places.append(enriched_place)

    return enriched_places


def enrich_itinerary_with_place_data(itinerary_data, candidate_places, transport_mode="driving"):
    place_lookup = {place["ref"]: place for place in candidate_places}

    for day in itinerary_data.get("days", []):
        activities = day.get("activities", [])

        for activity in activities:
            ref = activity.get("ref")
            place = place_lookup.get(ref)

            if not place:
                raise ValueError(f"Unknown ref during enrichment: {ref}")

            activity["name"] = place["name"]
            activity["place_id"] = place["place_id"]
            activity["category"] = place["category"]
            activity["address"] = place.get("address", "")
            activity["maps_link"] = f"https://www.google.com/maps/place/?q=place_id:{place['place_id']}"

            if "lat" in place and "lng" in place:
                activity["_coords"] = {
                    "lat": place["lat"],
                    "lng": place["lng"],
                }

        for i in range(len(activities) - 1):
            current = activities[i]
            nxt = activities[i + 1]

            if "_coords" in current and "_coords" in nxt:
                travel = get_travel_info(
                    current["_coords"],
                    nxt["_coords"],
                    transport_mode
                )

                current["travel_to_next"] = {
                    "distance": travel["distance_text"],
                    "duration": travel["duration_text"],
                }

        for activity in activities:
            activity.pop("_coords", None)

    return itinerary_data


def build_retry_message(last_error: str) -> str:
    return (
        f"Your previous response was rejected: {last_error}. "
        "Return corrected JSON only. "
        "Use only candidate refs provided earlier. "
        "Do not invent anything. "
        "Copy each ref exactly as given, for example P1, P2, P3. "
        "Do not return place_id directly unless explicitly required. "
        "Output exactly the required number of days and 4 activities per day. "
        "Use times: 08:00, 11:00, 14:00, 19:00."
    )


@router.post("/generate-itinerary")
def generate_itinerary(request: TravelRequest):
    try:
        request_data = request.model_dump()

        candidate_places = get_candidate_places(request_data)

        if not candidate_places:
            raise HTTPException(status_code=404, detail="No matching places found")

        candidate_places_with_refs = add_refs_to_candidate_places(candidate_places)

        messages = build_itinerary_messages(request_data, candidate_places_with_refs)

        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            raw_output = generate_with_groq(messages)

            try:
                itinerary_data = validate_json_output(raw_output)
                validate_refs(itinerary_data, candidate_places_with_refs)
                validate_activity_structure(itinerary_data, request_data)

                itinerary_data = enrich_itinerary_with_place_data(
                    itinerary_data,
                    candidate_places_with_refs,
                    request_data.get("transport_mode", "driving")
                )

                return {
                    "status": "success",
                    "candidate_count": len(candidate_places_with_refs),
                    "itinerary": itinerary_data,
                }

            except ValueError as validation_error:
                last_error = str(validation_error)

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
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")