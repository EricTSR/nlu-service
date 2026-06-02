from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="gwn_recommender")


def geocode_location(location_name: str):
    location = geolocator.geocode(location_name)

    if not location:
        return None

    return {
        "name": location.address,
        "latitude": location.latitude,
        "longitude": location.longitude
    }
