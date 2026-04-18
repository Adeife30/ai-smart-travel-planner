import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

print("DEBUG ENV PATH:", ENV_PATH)
print("DEBUG GOOGLE KEY LOADED:", bool(os.getenv("GOOGLE_API_KEY")))


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

CATEGORY_MAP = {
    "museum": "culture",
    "art_gallery": "culture",
    "tourist_attraction": "landmark",
    "church": "history",
    "historical_landmark": "history",
    "park": "nature",
    "zoo": "nature",
    "shopping_mall": "shopping",
    "store": "shopping",
    "restaurant": "food",
    "cafe": "food",
    "bakery": "food",
    "bar": "nightlife",
    "night_club": "nightlife",
    "live_music_venue": "nightlife",
}


def _require_api_key() -> None:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing from environment variables")


def _get_destination_coordinates(destination: str) -> tuple[float, float]:
    params = {
        "address": destination,
        "key": GOOGLE_API_KEY,
    }

    response = requests.get(GEOCODE_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Could not geocode destination: {destination}")

    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def _expand_interests(interests: list[str]) -> list[str]:
    expanded: list[str] = []

    for interest in interests:
        key = interest.strip().lower()
        mapped_terms = INTEREST_MAP.get(key)

        if mapped_terms:
            expanded.extend(mapped_terms)
        else:
            expanded.append(key)

    seen = set()
    unique_terms = []
    for term in expanded:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return unique_terms


def _search_places_for_term(destination: str, term: str) -> list[dict[str, Any]]:
    query = f"{term} in {destination}"

    params = {
        "query": query,
        "key": GOOGLE_API_KEY,
    }

    response = requests.get(TEXT_SEARCH_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    status = data.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        raise ValueError(f"Google Places error for query '{query}': {status}")

    return data.get("results", [])


def _infer_category(types: list[str], fallback_term: str) -> str:
    type_set = set(types)

    if "restaurant" in type_set or "cafe" in type_set:
        return "food"
    if "bar" in type_set or "night_club" in type_set:
        return "nightlife"
    if "shopping_mall" in type_set or "store" in type_set or "market" in type_set:
        return "shopping"
    if "museum" in type_set or "art_gallery" in type_set:
        return "culture"
    if "park" in type_set or "garden" in type_set:
        return "nature"
    if "tourist_attraction" in type_set:
        return "attraction"

    return fallback_term.lower()


def _normalise_place(place: dict[str, Any], fallback_term: str) -> dict[str, Any] | None:
    place_id = place.get("place_id")
    name = place.get("name")
    geometry = place.get("geometry", {}).get("location", {})
    lat = geometry.get("lat")
    lng = geometry.get("lng")

    if not place_id or not name or lat is None or lng is None:
        return None

    types = place.get("types", [])

    return {
        "place_id": place_id,
        "name": name,
        "category": _infer_category(types, fallback_term),
        "address": place.get("formatted_address", ""),
        "lat": lat,
        "lng": lng,
        "rating": place.get("rating"),
        "user_ratings_total": place.get("user_ratings_total"),
        "types": types,
    }


def _balance_candidate_places(
    candidate_places: list[dict[str, Any]],
    interests: list[str],
    max_total: int = 20,
    per_category_limit: int = 5,
) -> list[dict[str, Any]]:
    grouped = defaultdict(list)

    for place in candidate_places:
        grouped[place["category"]].append(place)

    balanced: list[dict[str, Any]] = []

    for interest in interests:
        category = interest.lower()
        if category in grouped:
            balanced.extend(grouped[category][:per_category_limit])

    if len(balanced) < max_total:
        for extra_category in ["culture", "nature", "shopping", "food", "nightlife", "attraction"]:
            if extra_category not in [i.lower() for i in interests] and extra_category in grouped:
                balanced.extend(grouped[extra_category][:per_category_limit])
            if len(balanced) >= max_total:
                break

    seen = set()
    unique_balanced = []
    for place in balanced:
        if place["place_id"] not in seen:
            seen.add(place["place_id"])
            unique_balanced.append(place)

    return unique_balanced[:max_total]


def get_candidate_places(request_data: dict[str, Any]) -> list[dict[str, Any]]:
    _require_api_key()

    destination = request_data.get("destination")
    interests = request_data.get("interests", [])

    if not destination:
        raise ValueError("Destination is required")

    if not interests:
        raise ValueError("At least one interest is required")

    if not isinstance(interests, list):
        raise ValueError("Interests must be a list")

    print("=== GOOGLE PLACES DEBUG START ===")
    print("Request data:", request_data)
    print("Destination:", destination)
    print("Interests:", interests)

    lat, lng = _get_destination_coordinates(destination)
    print("Destination coordinates:", lat, lng)

    search_terms = _expand_interests(interests)
    print("Expanded search terms:", search_terms)

    unique_places: dict[str, dict[str, Any]] = {}

    for term in search_terms:
        print(f"Searching Places for term: {term}")
        raw_results = _search_places_for_term(destination, term)
        print(f"Raw results for '{term}': {len(raw_results)}")

        for place in raw_results:
            normalised = _normalise_place(place, term)
            if not normalised:
                continue

            place_id = normalised["place_id"]
            if place_id not in unique_places:
                unique_places[place_id] = normalised

    candidate_places = list(unique_places.values())
    print("Final raw candidate places count:", len(candidate_places))

    candidate_places = _balance_candidate_places(candidate_places, interests)
    print("Balanced candidate places count:", len(candidate_places))

    print("=== GOOGLE PLACES DEBUG END ===")
    return candidate_places