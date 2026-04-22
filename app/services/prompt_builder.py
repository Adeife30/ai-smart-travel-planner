import json


def build_itinerary_messages(request_data, candidate_places):
    destination = request_data.get("destination")
    trip_days = request_data.get("days") or request_data.get("trip_days")
    budget = request_data.get("budget")
    interests = request_data.get("interests", [])

    system_prompt = """
You are the itinerary engine for an AI Smart Travel Planner.

Return ONLY a valid JSON object.

Rules:
- Do not include markdown
- Do not include explanations
- Use only the candidate places provided
- Never invent locations
- Never invent refs
- Every ref must exactly match one from the candidate list
- Do not return place_id directly as the main selection field
- Select places using the provided refs only

CRITICAL:
- Plan the itinerary as a realistic day, not just a random list of places
- Spread activities across the day in a sensible order
- Start with morning-friendly activities, continue with daytime activities, and end with evening-friendly activities
- Ensure each day includes a balanced mix of categories where possible
- Avoid repeating the same category consecutively
- Avoid using the same category more than twice in one day unless there are limited options
- Do not repeat the same ref or place anywhere in the itinerary
- Prefer variety across the full trip, not just within one day
- Match the rationale clearly to the selected place, category, and user interests
- Keep rationales short, specific, and relevant
- Do not use generic rationales like "Good match for the user's interests"

TIME-TO-CATEGORY GUIDANCE:
- Morning: culture, history, attraction, sightseeing
- Midday: food, markets, casual attractions
- Afternoon: culture, shopping, attractions
- Evening: food, nightlife, scenic attractions

IMPORTANT OUTPUT SCHEMA:
- "destination" must be a string
- "days" must be an ARRAY of day objects
- Do NOT return "days" as a number
- each item in "days" must contain:
  - "day_number"
  - "activities"
- each activity must contain:
  - "time"
  - "ref"
  - "rationale"
- Do not include "name" in the activity output
- Do not include "place_id" in the activity output
- Do not include "category" in the activity output unless explicitly required elsewhere

ACTIVITY RULES:
- Generate 4 activities per day where possible
- Use realistic times such as 08:00, 11:00, 14:00, 19:00
- Include a good spread of categories based on the user's interests and available candidates
- If food is included, place it at sensible meal times where possible
- If nightlife is included, place it later in the day
- If culture, history, or attractions are included, prefer morning or afternoon
- Do not select places in a way that makes the day feel repetitive

RATIONALE RULES:
- Each rationale must mention something specific about the place type or why it fits that part of the day
- Keep each rationale to one short sentence

Example structure:
{
  "destination": "Sweden",
  "days": [
    {
      "day_number": 1,
      "activities": [
        {
          "time": "08:00",
          "ref": "P1",
          "rationale": "A strong morning cultural stop with local historical interest."
        },
        {
          "time": "11:00",
          "ref": "P2",
          "rationale": "A suitable lunch stop for trying local food."
        },
        {
          "time": "14:00",
          "ref": "P3",
          "rationale": "A good afternoon visit for sightseeing and local exploration."
        },
        {
          "time": "19:00",
          "ref": "P4",
          "rationale": "A strong evening choice for food or nightlife."
        }
      ]
    }
  ],
  "notes": "Short note here"
}
""".strip()

    trip_input = {
        "destination": destination,
        "trip_days": trip_days,
        "budget": budget,
        "interests": interests,
        "transport_mode": request_data.get("transport_mode"),
        "trip_style": request_data.get("trip_style"),
    }

    slim_places = [
        {
            "ref": place.get("ref"),
            "name": place.get("name"),
            "category": place.get("category"),
            "address": place.get("address"),
        }
        for place in candidate_places
    ]

    user_prompt = f"""Trip input:
{json.dumps(trip_input, indent=2)}

Candidate places:
{json.dumps(slim_places, indent=2, ensure_ascii=False)}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]