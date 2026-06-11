from typing import List, Dict

from schemas import MessageType, PreferenceContextDto, DialogMessage, SlotFields
from services.nlu.preference_context_builder import build_known_preferences_text

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

def build_nlu_question_prompt(
        missing_field: SlotFields,
        message: MessageType,
        preferences: PreferenceContextDto,
        dialog_context: List[DialogMessage]
) -> str:

    known_text = build_known_preferences_text(preferences)

    if missing_field is not None:
        missing_field_key = missing_field.value
        field_label = _FIELD_LABELS.get(missing_field_key, missing_field_key)
        missing_field_text = f"\nFehlende Information: {field_label}"
    else:
        missing_field_text = ""

    dialog_text = "\n".join([
        f"[{msg.sender}]: {msg.message}"
        for msg in dialog_context if msg.message
    ])
    return f"""\
    
Du formulierst die nächste Rückfrage für einen Suchdialog auf einem Nachhaltigkeitsportal.

Regeln:
- Stelle genau eine kurze, freundliche Frage.
- Keine technischen Begriffe (kein "Slot", kein "SDG", kein "Parameter").
- Keine neuen Fakten erfinden.
- Beziehe dich auf bereits erkannte Präferenzen.
- Greife auf welche Informationen schon vorliegen. 
- Maximal 40 Wörter.
- Wenn nach SGD gefragt wird, frage geziehlt nach dem Nachhaltigkeitsziel bzw. Nachhaltigkeitszielen 
- Wenn MessageType = PREFERENCE_UPDATE, schreibe dazu welches Attribut geändert wurde, lies das im Chatverlauf nach, frage danach ob die Suche gestartet werden darf.
- Wenn MassageType = REFINE_SEARCH, frage gezielt danach, welchen Wert der Benutzer dem genanten Attribut oder Attributen geben möchte. 
- Antworte ausschließlich mit gültigem JSON.

Bekannte Präferenzen:
{known_text}

Chatverlauf:
{dialog_text}

{missing_field_text}

MessageType: {message}

JSON-Format:
{{
  "answer": "Deine Frage hier"
}}
"""