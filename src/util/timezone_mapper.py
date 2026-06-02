from datetime import datetime, timezone
from zoneinfo import ZoneInfo

GERMAN_TZ = ZoneInfo("Europe/Berlin")

def to_iso_with_timezone(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=GERMAN_TZ).isoformat()

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=GERMAN_TZ)
        return value.isoformat()

    if isinstance(value, str):
        # Falls Python/Mistral "2026-05-18T02:00:00" ohne Offset liefert
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=GERMAN_TZ)
        return dt.isoformat()

    return value