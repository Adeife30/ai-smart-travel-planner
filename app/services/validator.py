import json


REQUIRED_ACTIVITY_TIMES = ["08:00", "11:00", "14:00", "19:00"]


def validate_json_output(raw_output: str):
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned by LLM")

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object")

    if "destination" not in data or not isinstance(data["destination"], str):
        raise ValueError("Missing or invalid 'destination' field in LLM output")

    if "days" not in data:
        raise ValueError("Missing 'days' field in LLM output")

    if not isinstance(data["days"], list):
        raise ValueError("Field 'days' must be a list")

    if "notes" in data and not isinstance(data["notes"], str):
        raise ValueError("If provided, 'notes' must be a string")

    for day in data["days"]:
        if not isinstance(day, dict):
            raise ValueError("Each day must be an object")

        if "day_number" not in day:
            raise ValueError("Each day must include 'day_number'")

        if not isinstance(day["day_number"], int):
            raise ValueError("'day_number' must be an integer")

        if "theme" in day and not isinstance(day["theme"], str):
            raise ValueError("If provided, 'theme' must be a string")

        if "activities" not in day:
            raise ValueError("Each day must include 'activities'")

        if not isinstance(day["activities"], list):
            raise ValueError("Field 'activities' must be a list")

        for activity in day["activities"]:
            if not isinstance(activity, dict):
                raise ValueError("Each activity must be an object")

            required_fields = ["time", "ref", "rationale"]
            for field in required_fields:
                if field not in activity:
                    raise ValueError(f"Missing required activity field: {field}")

            if not isinstance(activity["time"], str):
                raise ValueError("Activity 'time' must be a string")

            if not isinstance(activity["ref"], str):
                raise ValueError("Activity 'ref' must be a string")

            if not isinstance(activity["rationale"], str):
                raise ValueError("Activity 'rationale' must be a string")

    return data


def validate_refs(itinerary_data, candidate_places):
    valid_refs = {place["ref"] for place in candidate_places}
    candidate_lookup = {place["ref"]: place for place in candidate_places}

    used_refs = set()

    for day in itinerary_data.get("days", []):
        day_refs = set()

        for activity in day.get("activities", []):
            ref = activity.get("ref")

            if ref not in valid_refs:
                raise ValueError(f"Invalid ref found: {ref}")

            if ref in day_refs:
                raise ValueError(f"Duplicate ref found within day {day.get('day_number')}: {ref}")

            if ref in used_refs:
                raise ValueError(f"Duplicate ref found across itinerary: {ref}")

            day_refs.add(ref)
            used_refs.add(ref)

    return True


def validate_place_ids(itinerary_data: dict, candidate_places: list):
    allowed_place_ids = {place["place_id"] for place in candidate_places}

    days = itinerary_data.get("days", [])
    if not isinstance(days, list):
        raise ValueError("Field 'days' must be a list")

    for day in days:
        activities = day.get("activities", [])
        if not isinstance(activities, list):
            raise ValueError("Field 'activities' must be a list")

        for activity in activities:
            place_id = activity.get("place_id")
            if place_id not in allowed_place_ids:
                raise ValueError(f"Invalid place_id found: {place_id}")

    return True


def validate_activity_structure(itinerary_data: dict, request_data: dict):
    requested_days = request_data.get("days")
    days = itinerary_data.get("days", [])

    if requested_days is not None and len(days) != requested_days:
        raise ValueError(
            f"Expected exactly {requested_days} day objects, but got {len(days)}"
        )

    expected_day_numbers = list(range(1, len(days) + 1))
    actual_day_numbers = [day.get("day_number") for day in days]

    if actual_day_numbers != expected_day_numbers:
        raise ValueError(
            f"Day numbers must be sequential starting from 1. Got {actual_day_numbers}"
        )

    for day in days:
        activities = day.get("activities", [])

        if len(activities) != 4:
            raise ValueError(
                f"Day {day.get('day_number')} must contain exactly 4 activities"
            )

        times = [activity.get("time") for activity in activities]

        if times != REQUIRED_ACTIVITY_TIMES:
            raise ValueError(
                f"Day {day.get('day_number')} must use exactly these times in order: {REQUIRED_ACTIVITY_TIMES}"
            )

    return True