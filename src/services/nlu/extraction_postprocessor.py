from src.schemas import LlmExtractResponse
from src.services.geo_matcher import geocode_location
from src.util.timezone_mapper import to_iso_with_timezone


def postprocess_extraction(result: LlmExtractResponse) -> LlmExtractResponse:
    if result.period.start is not None:
        result.period.start = to_iso_with_timezone(result.period.start)

    if result.period.end is not None:
        result.period.end = to_iso_with_timezone(result.period.end)

    if result.location and result.location.city:
        geo = geocode_location(result.location.city)

        if geo:
            result.location.city = geo.get("city") or result.location.city
            result.location.state = geo.get("state")
            result.location.country = geo.get("country")
            result.location.latitude = geo.get("latitude")
            result.location.longitude = geo.get("longitude")

    return result