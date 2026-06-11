from typing import Dict

from src.schemas import PreferenceContextDto

# ── SDG-Label-Map für natürlichsprachlichen Kontext ──
SDG_LABELS: Dict[int, str] = {
    1: "Keine Armut", 2: "Kein Hunger", 3: "Gesundheit",
    4: "Bildung", 5: "Gleichstellung", 6: "Sauberes Wasser",
    7: "Saubere Energie", 8: "Menschenwürdige Arbeit",
    9: "Industrie & Innovation", 10: "Weniger Ungleichheiten",
    11: "Nachhaltige Städte", 12: "Nachhaltiger Konsum",
    13: "Klimaschutz", 14: "Leben unter Wasser",
    15: "Leben an Land", 16: "Frieden & Gerechtigkeit",
    17: "Globale Partnerschaften",
}

_FIELD_LABELS: Dict[str, str] = {
    "ONLINE": "Online/Vor-Ort",
    "LOCATION": "Ort",
    "PERIOD": "Zeitraum",
    "SDGS": "Nachhaltigkeitsthema",
    "INTENT": "Art der Suche",
    "THEMATIC_FOCUS": "Thema",
    "IMPACT_AREA": "Wirkungsbereich",
    "AWARDS": "Auszeichnungen",
    "OFFER_CATEGORY": "Angebotskategorie",
    "BEST_PRACTISE_CATEGORY": "Best-Practise-Kategorie",
}

def build_known_preferences_text(prefs: PreferenceContextDto) -> str:
    lines: list[str] = []

    if prefs.pendingField:
        pending = prefs.pendingField.value if hasattr(prefs.pendingField, "value") else str(prefs.pendingField)
        lines.append(f"- Aktuell abgefragtes Feld: {pending}")

    if prefs.intent:
        intent_labels = {
            "SEARCH_MARKETPLACE": "ein Angebot",
            "SEARCH_ORGANISATIONS": "eine Organisation",
            "SEARCH_ACTIVITIES": "eine Aktivität",
        }
        lines.append(f"- Der Nutzer sucht {intent_labels.get(prefs.intent, prefs.intent)}.")

    if prefs.location:
        loc_parts = []
        if prefs.location.city:
            loc_parts.append(prefs.location.city)
        if prefs.location.state:
            loc_parts.append(prefs.location.state)
        if prefs.location.country:
            loc_parts.append(prefs.location.country)
        loc_text = ", ".join(loc_parts) if loc_parts else "Unbekannt"
        lines.append(f"- Ort: {loc_text}")

    if prefs.online:
        lines.append("- Format: Online")
    elif prefs.online is False:
        lines.append("- Format: Vor Ort")

    if prefs.period.start and prefs.period.end:
        lines.append(f"- Zeitraum: {prefs.period.start} bis {prefs.period.end}")
    elif prefs.period.start:
        lines.append(f"- Ab: {prefs.period.start}")
    elif prefs.period.end:
        lines.append(f"- Bis: {prefs.period.start}")

    if prefs.sdgs:
        sdg_text = ", ".join(SDG_LABELS.get(s, f"SDG {s}") for s in prefs.sdgs)
        lines.append(f"- Thema: {sdg_text}")

    print(prefs.handledFields)
    if prefs.handledFields:
        handled = ", ".join(
            field.value if hasattr(field, "value") else str(field).upper()
            for field in prefs.handledFields
        )
        lines.append(f"- Bereits behandelte Felder: {handled}")

    if not lines:
        lines.append("- Noch keine Präferenzen bekannt.")

    return "\n".join(lines)
