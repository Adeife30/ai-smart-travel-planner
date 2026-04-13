import json


def validate_itinerary(itinerary_text: str, candidate_places: list[dict]):
    try:
        itinerary_data = json.loads(itinerary_text)
    except json.JSONDecodeError:
        return {
            "valid": False,
            "error": "Response is not valid JSON"
        }

    valid_place_ids = {place["place_id"] for place in candidate_places}

    for day in itinerary_data.get("days", []):
        for activity in day.get("activities", []):
            if activity.get("place_id") not in valid_place_ids:
                return {
                    "valid": False,
                    "error": f"Invalid place_id found: {activity.get('place_id')}"
                }

    return {
        "valid": True,
        "data": itinerary_data
    }