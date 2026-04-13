import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def get_candidate_places(destination: str):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    query = f"tourist attractions in {destination}"

    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    places = []

    for place in data.get("results", [])[:5]:
        places.append({
            "name": place.get("name"),
            "place_id": place.get("place_id"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating")
        })

    return places