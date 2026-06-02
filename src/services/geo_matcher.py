from difflib import SequenceMatcher

from geopy.geocoders import Nominatim
from typing import Optional, Dict, Any

geolocator = Nominatim(user_agent="gwn_recommender")

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def geocode_location(location_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Geocodiert einen Ort und gibt strukturierte Adresskomponenten zurück.
    Gibt None zurück, wenn kein Ort übergeben oder kein Ort gefunden wurde.
    """


    if not location_name or not location_name.strip():
        return None

    original_location_name = location_name.strip()

    location = geolocator.geocode(
        location_name,
        addressdetails=True,
        exactly_one=True,
        country_codes="de"
    )

    if not location:
        return None

    address_dict = location.raw.get("address", {})

    city = (
        address_dict.get("city")
        or address_dict.get("town")
        or address_dict.get("village")
    )

    if not city:
        city = location_name.strip()

    if similarity(original_location_name, city) < 0.75:
        print(f"Geocoding rejected: '{original_location_name}' wurde zu '{city}'")
        return None

    return {
        "name": location.address,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "city": city,
        "state": address_dict.get("state"),
        "country": address_dict.get("country"),
    }