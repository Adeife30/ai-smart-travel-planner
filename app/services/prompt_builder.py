import json


def build_itinerary_messages(trip_input: dict, candidate_places: list):
    llm_trip_input = {
        "destination": trip_input.get("destination"),
        "trip_days": trip_input.get("days"),
        "budget": trip_input.get("budget"),
        "interests": trip_input.get("interests"),
        "transport_mode": trip_input.get("transport_mode"),
        "trip_style": trip_input.get("trip_style"),
    }

    enriched_places = []
    for index, place in enumerate(candidate_places, start=1):
        ref = f"P{index}"
        enriched_places.append({
            "ref": ref,
            "place_id": place["place_id"],
            "name": place["name"],
            "category": place["category"],
            "address": place.get("address", "")
        })

    system_prompt = """
You are the itinerary engine for an AI Smart Travel Planner.

Return ONLY one valid JSON object.
Do not return markdown.
Do not return explanations.
Do not return any text outside the JSON object.

Core rules:
- Use ONLY the candidate places provided
- Never invent locations
- Never invent refs
- Never invent place_ids
- Every ref must exactly match a candidate ref
- Every place_id must exactly match a candidate place_id
- Every name must exactly match the candidate place name
- Do not rename, paraphrase, shorten, or alter place names
- Do not repeat the same ref anywhere in the itinerary unless candidate options are extremely limited

Trip quality rules:
- Create exactly 4 activities per day
- Spread activities realistically across the day using these exact times:
  - 08:00
  - 11:00
  - 14:00
  - 19:00
- Keep the day realistic:
  - morning activity at 08:00
  - late morning activity at 11:00
  - afternoon activity at 14:00
  - evening activity at 19:00
- Nightlife should only appear in the evening where appropriate
- Food places should fit lunch or evening where appropriate
- Avoid repeating the same category too often on the same day
- Avoid two consecutive activities from the same category unless necessary
- Prefer variety across the trip
- Make each rationale match the actual place selected
- Keep rationales short, natural, and specific
- Keep each rationale under 18 words
- Do not schedule two consecutive activities from the same high-level category unless necessary.

Rationale guidance:
- For culture/history places, mention art, heritage, architecture, or significance if appropriate.
- For food places, mention meal timing, local cuisine, or a good break in the day.
- For nature places, mention views, walking, green space, or a relaxed pace.
- For nightlife places, mention evening atmosphere, drinks, music, or social energy.
- Keep each rationale under 18 words.

Schema rules:
- "destination" must be a string
- "days" must be an array
- Output exactly the requested number of day objects
- Each day object must contain:
  - "day_number"
  - "theme"
  - "activities"
- "activities" must be an array of exactly 4 activity objects
- Each activity object must contain:
  - "time"
  - "name"
  - "ref"
  - "place_id"
  - "category"
  - "rationale"
- "notes" must be a short string

Required JSON structure:
{
  "destination": "City name",
  "days": [
    {
      "day_number": 1,
      "theme": "Short theme for the day",
      "activities": [
        {
          "time": "08:00",
          "name": "Exact candidate place name",
          "ref": "Exact candidate ref",
          "place_id": "Exact candidate place_id",
          "category": "Exact candidate category",
          "rationale": "Short place-specific reason"
        },
        {
          "time": "11:00",
          "name": "Exact candidate place name",
          "ref": "Exact candidate ref",
          "place_id": "Exact candidate place_id",
          "category": "Exact candidate category",
          "rationale": "Short place-specific reason"
        },
        {
          "time": "14:00",
          "name": "Exact candidate place name",
          "ref": "Exact candidate ref",
          "place_id": "Exact candidate place_id",
          "category": "Exact candidate category",
          "rationale": "Short place-specific reason"
        },
        {
          "time": "19:00",
          "name": "Exact candidate place name",
          "ref": "Exact candidate ref",
          "place_id": "Exact candidate place_id",
          "category": "Exact candidate category",
          "rationale": "Short place-specific reason"
        }
      ]
    }
  ],
  "notes": "Short summary note"
}

CRITICAL:
- place_id values are case-sensitive
- ref values are case-sensitive
- Copy values exactly from the candidate list
- A single wrong character makes the output invalid
""".strip()

    user_prompt = f"""
Trip input:
{json.dumps(llm_trip_input, indent=2)}

Candidate places:
{json.dumps(enriched_places, indent=2)}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]