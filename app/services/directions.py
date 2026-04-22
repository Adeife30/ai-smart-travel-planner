import os
import requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def _require_api_key():
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY missing")


def get_travel_info(origin, destination, mode="driving"):
    _require_api_key()

    params = {
        "origin": f"{origin['lat']},{origin['lng']}",
        "destination": f"{destination['lat']},{destination['lng']}",
        "mode": mode,
        "key": GOOGLE_API_KEY,
    }

    try:
        response = requests.get(DIRECTIONS_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            return {
                "distance_text": "N/A",
                "duration_text": "N/A",
                "distance_meters": None,
                "duration_seconds": None,
            }

        leg = data["routes"][0]["legs"][0]

        return {
            "distance_text": leg["distance"]["text"],
            "duration_text": leg["duration"]["text"],
            "distance_meters": leg["distance"]["value"],
            "duration_seconds": leg["duration"]["value"],
        }

    except Exception:
        return {
            "distance_text": "N/A",
            "duration_text": "N/A",
            "distance_meters": None,
            "duration_seconds": None,
        }