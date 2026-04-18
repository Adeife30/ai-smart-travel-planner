import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

INTEREST_MAP = {
    "culture": ["museum", "art gallery", "cultural attractions"],
    "history": ["historical landmarks", "churches", "heritage sites"],
    "food": ["restaurants", "cafes", "local food"],
    "nature": ["parks", "gardens", "scenic spots"],
    "nightlife": ["bars", "night clubs", "live music venues"],
    "shopping": ["shopping malls", "markets", "stores"],
    "landmark": ["tourist attractions", "famous landmarks"],
    "landmarks": ["tourist attractions", "famous landmarks"],
}

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
    "market": "shopping",
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
    for place_type in types:
        if place_type in CATEGORY_MAP:
            return CATEGORY_MAP[place_type]

    fallback = fallback_term.strip().lower()

    if fallback in {"museum", "gallery", "art", "culture", "art gallery", "cultural attractions"}:
        return "culture"
    if fallback in {"history", "historic", "historical", "church", "churches", "heritage sites", "historical landmarks"}:
        return "history"
    if fallback in {"park", "nature", "garden", "gardens", "scenic spots"}:
        return "nature"
    if fallback in {"food", "restaurant", "restaurants", "cafe", "cafes", "bakery", "local food"}:
        return "food"
    if fallback in {"nightlife", "bar", "bars", "club", "night club", "night clubs", "live music", "live music venues"}:
        return "nightlife"
    if fallback in {"shopping", "mall", "shopping malls", "market", "markets", "store", "stores"}:
        return "shopping"
    if fallback in {"landmark", "landmarks", "attraction", "tourist attraction", "tourist attractions", "famous landmarks"}:
        return "landmark"

    return "general"


def _normalise_place(place: dict[str, Any], fallback_term: str) -> dict[str, Any] | None:
    place_id = place.get("place_id")
    name = place.get("name")
    geometry = place.get("geometry", {}).get("location", {})
    lat = geometry.get("lat")
    lng = geometry.get("lng")

    if not place_id or not name or lat is None or lng is None:
        return None

    types = place.get("types", [])
    category = _infer_category(types, fallback_term)

    return {
        "place_id": place_id,
        "name": name,
        "category": category,
        "address": place.get("formatted_address", ""),
        "lat": lat,
        "lng": lng,
        "rating": place.get("rating") or 0,
        "user_ratings_total": place.get("user_ratings_total") or 0,
        "types": types,
    }


def _map_interest_to_category(interest: str) -> str:
    mapped = interest.strip().lower()

    if mapped in {"museum", "gallery", "art", "culture", "art gallery", "cultural attractions"}:
        return "culture"
    if mapped in {"history", "historic", "historical", "church", "churches", "heritage sites", "historical landmarks"}:
        return "history"
    if mapped in {"park", "nature", "garden", "gardens", "scenic spots"}:
        return "nature"
    if mapped in {"food", "restaurant", "restaurants", "cafe", "cafes", "bakery", "local food"}:
        return "food"
    if mapped in {"nightlife", "bar", "bars", "club", "night club", "night clubs", "live music", "live music venues"}:
        return "nightlife"
    if mapped in {"shopping", "mall", "shopping malls", "market", "markets", "store", "stores"}:
        return "shopping"
    if mapped in {"landmark", "landmarks", "attraction", "tourist attraction", "tourist attractions", "famous landmarks"}:
        return "landmark"

    return "general"


def _balance_candidate_places(
    candidate_places: list[dict[str, Any]],
    interests: list[str],
    max_total: int = 20,
    per_category_limit: int = 4,
) -> list[dict[str, Any]]:
    grouped = defaultdict(list)

    for place in candidate_places:
        grouped[place["category"]].append(place)

    for category in grouped:
        grouped[category] = sorted(
            grouped[category],
            key=lambda p: (
                p.get("rating", 0),
                p.get("user_ratings_total", 0),
            ),
            reverse=True,
        )

    interest_priority = []
    for interest in interests:
        mapped_category = _map_interest_to_category(interest)
        if mapped_category not in interest_priority:
            interest_priority.append(mapped_category)

    fallback_order = [
        "landmark",
        "culture",
        "history",
        "nature",
        "food",
        "shopping",
        "nightlife",
        "general",
    ]

    ordered_categories = interest_priority + [
        category for category in fallback_order if category not in interest_priority
    ]

    balanced: list[dict[str, Any]] = []
    seen_place_ids = set()

    for category in ordered_categories:
        if category not in grouped:
            continue

        added_for_category = 0
        for place in grouped[category]:
            if place["place_id"] in seen_place_ids:
                continue

            balanced.append(place)
            seen_place_ids.add(place["place_id"])
            added_for_category += 1

            if added_for_category >= per_category_limit:
                break

            if len(balanced) >= max_total:
                return balanced

    if len(balanced) < max_total:
        remaining_places = sorted(
            candidate_places,
            key=lambda p: (
                p.get("rating", 0),
                p.get("user_ratings_total", 0),
            ),
            reverse=True,
        )

        for place in remaining_places:
            if place["place_id"] in seen_place_ids:
                continue

            balanced.append(place)
            seen_place_ids.add(place["place_id"])

            if len(balanced) >= max_total:
                break

    return balanced


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