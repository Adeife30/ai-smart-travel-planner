def build_itinerary_prompt(destination, interests, budget, days, candidate_places):

    places_text = ""
    for place in candidate_places:
        places_text += f"""
- Name: {place['name']}
  Place ID: {place['place_id']}
  Address: {place.get('address', 'N/A')}
  Rating: {place.get('rating', 'N/A')}
"""

    prompt = f"""
You are an AI travel planner.

Create a {days}-day travel itinerary for {destination}.

User preferences:
- Interests: {", ".join(interests)}
- Budget: {budget}

IMPORTANT RULES:
1. You MUST only use the candidate places provided below.
2. Do NOT invent any locations.
3. Every place_id MUST exactly match one from the candidate list.
4. Do NOT use placeholder values like EXACT_PLACE_ID_HERE.
5. Output ONLY valid JSON.
6. Do NOT include explanations or text outside JSON.

Required JSON format:

{{
  "days": [
    {{
      "day": 1,
      "activities": [
        {{
          "time": "09:00",
          "place_name": "Exact name from candidate list",
          "place_id": "Exact place_id from candidate list",
          "activity": "Short description"
        }}
      ]
    }}
  ]
}}

Candidate places:
{places_text}
"""

    return prompt