"""
LLM-basierte Slot-Extraktion via Mistral API.
Erkennt messageType, intent, Ort, Datum, SDGs aus Freitext.
Generiert kontextbezogene Rückfragen für fehlende Slots.
"""

import json
import os
import random
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
from enum import Enum

from dotenv import load_dotenv
from mistralai.client import Mistral
from datetime import datetime, timezone, date

from src.posts.models import (
    DialogMessage, LlmExtractResponse, NextQuestionResponse, 
    PreferenceContextDto, MessageType, ImpactAreaDto, Award, 
    OfferCategory, BestPractiseCategory, ThematicFocusDto, Intent
)
from src.services.geo_matcher import geocode_location
from src.util.timezone_mapper import to_iso_with_timezone

from src.config import MISTRAL_MODEL, MISTRAL_EXTRACT_TEMP, MISTRAL_QUESTION_TEMP

load_dotenv()

_API_KEY = os.getenv("MISTRAL_API_KEY")
if not _API_KEY:
    raise RuntimeError("MISTRAL_API_KEY nicht gesetzt – bitte in .env eintragen")

client = Mistral(api_key=_API_KEY)
_DE_TZ = ZoneInfo("Europe/Berlin")

SYSTEM_PROMPT = f"""\
Du extrahierst Suchpräferenzen für ein Nachhaltigkeitsportal.

Antworte ausschließlich mit gültigem JSON.

Erlaubte messageTypes:
GREETING: Wenn der Benutzer ohne Angabe von Präferenzen eine Begrüßung schreibt.
CHITCHAT: Small Talk oder nicht zuordnungbare Nachrichten, insbesondere wenn kein intent erkannt wurde
HELP: Wenn der Nutzer explizit um Hilfe bittet oder Fragen zum Portal hat.
ANSWER: Wenn der Benutzer auf eine Frage vom Bot anwortet die nicht fragt, ob der Benutzer suchen will
PREFERENCE_UPDATE: Wenn eine Präferenz aktualisiert wird, bevorzuge diesen messageType immer gegenüber ANSWER, auch wenn es sich um eine Antwort auf eine Bot-Frage handelt, z. B. "Nein, ich möchte nicht online suchen, sondern vor Ort."
CONFIRMATION: Wenn der Benutzer einer Suche zustimmt.
REFINE_SEARCH: Wenn der Benutzer seine Suche verfeinern möchte.
REJECTION: Wenn der Benutzer eine Suche oder auch Frage ablehnt.
EXIT: Beenden des Chats
Erlaubte intents:
SEARCH_ACTIVITIES, SEARCH_ORGANISATIONS, SEARCH_MARKETPLACE, null

Wichtig:
Wenn der letzte Bot eine Frage zu einem konkreten Slot gestellt hat,
z. B. Ort, SDGs, Thema, Auszeichnungen, Zeitraum oder Wirkungsbereich,
dann ist eine Antwort wie "Nein", "egal", "keine", "nicht wichtig"
als Antwort auf diesen Slot zu interpretieren.

In diesem Fall:
- messageType = ANSWER
- der entsprechende Slot bleibt leer oder wird auf einen leeren Wert gesetzt
- das Feld wird in handledFields aufgenommen
- nicht CONFIRMATION setzen

CONFIRMATION nur setzen, wenn der Bot explizit gefragt hat,
ob die Suche gestartet werden soll, z. B.:
"Soll ich die Suche jetzt starten?"
"Möchtest du jetzt suchen?"
"Passt das so?"

Erstelle einen kurzen, prägnanten Titel für diesen Chat basierend auf dem aktuellsten inhaltlichen Kontext.

Regeln:
- Maximal 5 Wörter
- Nur relevante Schlagwörter verwenden
- Keine Füllwörter, Begrüßungen oder Smalltalk
- Keine vollständigen Sätze
- Keine Beschreibung offener oder noch fehlender Präferenzen
- Wenn der bestehende Titel weiterhin grob passt, übernehme ihn unverändert
- Wenn kein sinnvoller neuer Kontext erkennbar ist, übernehme ihn unverändert
- Wenn im gesamten Chat kein sinnvoller Kontext erkennbar ist, setze:
  title = null
  
Erlaubte awards Werte:

INITIATOR = Initiator / ausgezeichnete Initiative
AWARD = Preisträger / ausgezeichnetes Projekt

  
Erlaubte thematicFocus Werte:

PARTICIPATION = Beteiligung, Engagement und Partizipation
EDUCATION = Bildung, Forschung und Wissenschaft
BIODIVERSITY = Biodiversität und Naturschutz
HUMAN_RIGHTS = Demokratie und Menschenrechte
GENDER_EQUITY = Diversität, Gleichstellung und Inklusion
PEACE = Frieden und Sicherheit
INTERNATIONAL_RESPONSIBILITY = Internationale Verantwortung
CLIMATE_PROTECTION = Klimaschutz und Energiewende
CIRCULAR_ECONOMY = Kreislaufwirtschaft
CULTURAL_SOCIAL_CHANGE = Kultur und gesellschaftlicher Wandel
AGRICULTURE = Landwirtschaft und Ernährung
MOBILITY = Mobilität und Verkehrswende
SUSTAINABLE_PROCUREMENT = Nachhaltige Beschaffung
SUSTAINABLE_FINANCE = Nachhaltige Finanzen
SUSTAINABLE_LIFESTYLE = Nachhaltiger Konsum und Lebensstil
SUSTAINABLE_BUILDING = Nachhaltiges Bauen und Wohnen
SUSTAINABLE_BUSINESS = Nachhaltiges Wirtschaften
SUSTAINABLE_GOVERNANCE = Nachhaltigkeitsgovernance
SOCIAL_JUSTICE = Soziale Gerechtigkeit und gute Arbeit
SPORT = Sport
URBAN_DEVELOPMENT = Stadtentwicklung und ländliche Räume
TOURISM = Tourismus
DIGITALIZATION = Digitalisierung
OTHER = Sonstiges


Erlaubte impactArea Werte:

LOCAL = lokal
REGIONAL = regional
STATE = landesweit
COUNTRY = bundesweit
CONTINENT = europaweit
WORLD = global


Erlaubte offerCategory Werte:

JOBS = Jobs
REPORTING_STANDARDS = Berichtstandards
EDUCATIONAL_OFFERS = Bildungsangebote
FUNDING_PROGRAMMES_AND_GRANTS = Förderprogramme und Finanzhilfen
CONTESTS = Wettbewerbe
VOLUNTEERING = Ehrenamtliche Unterstützung
MATERIALS = Materialien
FACILITIES = Räumlichkeiten
CONSULTING = Beratung
NETWORK = Netzwerk
PROJECT_SUSTAINABILITY = Projekt Nachhaltigkeit
OTHER = Sonstiges


Erlaubte bestPractiseCategory Werte:

SUSTAINABILITY_REPORTING = Nachhaltigkeitsberichterstattung
PROJECT_REPORT = Projektberichte
OTHER = Sonstiges

Beispiele:
- "Aktivitäten in Leipzig"
- "Organisationen zum Thema Bildung"

Regeln:
- Wenn nur Smalltalk/Begrüßung vorkommt, shouldExtractSlots = false.
- Erfinde keine Werte.
- Ort nur setzen, wenn ein Ort ausdrücklich genannt wurde.
- Datum im Format YYYY-MM-DD.
- Wenn Datum erkannt, Datum muss in der Zukunft liegen (ab heute), sonst period.start = heute.
- Wenn kein Datum erkennbar ist: period.start = null, period.end = null.
- SDGs nur als Zahlen 1 bis 17.
- Wenn keine SDGs erkennbar sind: sdgs = [].
- Heute ist {date.today().isoformat()}.
+ Heute ist {datetime.now(_DE_TZ).strftime('%Y-%m-%d')} (Zeitzone: Europe/Berlin, aktuelle Uhrzeit: {datetime.now(_DE_TZ).strftime('%H:%M')}).
- Berücksichtige den bisherigen Dialogverlauf, um den Kontext zu verstehen.
- Wenn der Nutzer auf eine Rückfrage antwortet, extrahiere die Antwort als Slot-Wert.
- period.start und period.end enthalten ausschließlich das Datum im Format: YYYY-MM-DDTHH:mm:ssZ
- Beispiel: "2026-06-12T00:00:00Z"
- startTime und endTime enthalten ausschließlich die Uhrzeit im Format HH:mm:ss.
- Wenn ein Datum erkannt wird, setze period.start und period.end auf dieses Datum. 
- Wenn eine Uhrzeit erkannt wird, setze startTime auf diese Uhrzeit.
- Wenn nur eine Start-Uhrzeit genannt wird, setze endTime = null.
- Wenn ein Angebot dauerhaft/permanent ist, setze period.permanent = true, sonst null.

Erlaubte handledFields Werte:
INTENT, LOCATION, ONLINE, PERIOD, SDGS, THEMATIC_FOCUS, IMPACT_AREA, AWARDS, OFFER_CATEGORY, BEST_PRACTISE_CATEGORY

Wichtig:
- handledFields darf ausschließlich diese Enum-Werte enthalten.
- Verwende niemals Kleinbuchstaben wie "location", "sdgs" oder "intent".
- Richtig: "LOCATION"
- Falsch: "location"

JSON-Format:
{{ 
  "title:" null,
  "messageType": "....",
  "shouldExtractSlots": true,
  "intent": null,
  "location": null,
  "latitude": null,
  "longitude": null,
  "online": null,
  "period": {{
    "start": null,
    "end": null,
    "start_time": null,
    "end_time": null,
    "permanent": null
  }},
  "sdgs": [],
  "thematicFocus": null,
  "impactArea": null,
  "awards": [],
  "offerCategory": null,
  "bestPractiseCategory": null,
  "confidence": null,
  "handledFields": []
}}
"""


def _build_chat_messages(
        message: str,
        dialog_context: Optional[List[DialogMessage]],
        title: Optional[str] = None,
        preferences: Optional[PreferenceContextDto] = None,
) -> List[Dict[str, str]]:
    """Baut die Mistral-Messages aus System-Prompt + Dialog-History + aktuelle Nachricht."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # ── Bisherige Präferenzen als Kontext ──
    if preferences:
        pref_text = _build_known_preferences_text(preferences)
        messages.append({
            "role": "system",
            "content": f"Bereits bekannte Nutzerpräferenzen:\n{pref_text}",
        })

    # ── Dialog-History einbinden ──
    if dialog_context:
        for msg in dialog_context:
            role = "user" if msg.sender == "USER" else "assistant"
            if msg.message:
                messages.append({"role": role, "content": msg.message})

    # ── Aktuelle Nachricht ──
    messages.append({"role": "user", "content": message})

    return messages


def extract_with_mistral(
        message: str,
        dialog_context: Optional[List[DialogMessage]] = None,
        title: Optional[str] = None,
        preferences: Optional[PreferenceContextDto] = None,
) -> LlmExtractResponse:
    """Sendet die Nachricht + Dialogkontext an Mistral und gibt ein LlmExtractResponse zurück."""
    chat_messages = _build_chat_messages(message, dialog_context, title,  preferences)

    print(f"🤖 Mistral request: '{message}' (history: {len(chat_messages) - 2} messages)")

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=chat_messages,
        temperature=MISTRAL_EXTRACT_TEMP,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    print(f"🤖 Mistral response: {content}")

    data = json.loads(content)
    result = LlmExtractResponse(**data)
    if result.period.start is not None:
        result.period.start = to_iso_with_timezone(result.period.start)
    if result.period.end is not None:
        result.period.end = to_iso_with_timezone(result.period.end)

    # ── Geocoding: if location was found ──
    if result.location:
        geo = geocode_location(result.location)
        if geo:
            print(f"📍 Geocoded '{result.location}' → {geo['name']} ({geo['latitude']}, {geo['longitude']})")
            result.location = geo["name"]
            result.latitude = geo["latitude"]
            result.longitude = geo["longitude"]
        else:
            print(f"⚠️ Geocoding failed for '{result.location}'")
    return result


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

# QuickReply-Vorschläge je Slot
_QUICK_REPLIES: Dict[str, list[str]] = {
    "ONLINE": ["Online", "Vor Ort", "Beides ist okay"],
    "LOCATION": ["In meiner Nähe", "Deutschlandweit", "Online"],
    "PERIOD": ["Heute", "Diese Woche", "Nächste Woche", "Diesen Monat"],
    "SDGS": ["Klima", "Bildung", "Energie", "Gleichstellung", "Alle Themen"],
    "INTENT": ["Veranstaltungen", "Organisationen", "Angebote"],
}


def _build_known_preferences_text(prefs: PreferenceContextDto) -> str:
    """Formuliert die bekannten Präferenzen als natürlichsprachigen Kontext."""
    lines: list[str] = []

    intent_labels = {
        "SEARCH_MARKETPLACE": "ein Angebot/Veranstaltung",
        "SEARCH_ORGANISATIONS": "eine Organisation",
        "SEARCH_ACTIVITIES": "eine Aktivität",
    }
    if prefs.intent:
        lines.append(f"- Der Nutzer sucht {intent_labels.get(prefs.intent, prefs.intent)}.")

    if prefs.location:
        # Kurzname: erstes Komma-Segment
        short_loc = prefs.location.split(",")[0].strip()
        lines.append(f"- Ort: {short_loc}")

    if prefs.online is True:
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


def _to_camel_case(snake_str: str) -> str:
    """Converts SNAKE_CASE or snake_case to camelCase."""
    parts = snake_str.lower().split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def _get_enum_quick_replies(missing_field: str, sample_size: int = 2) -> List[str]:
    """
    Generiert Quick Replies basierend auf Enum-Werten des fehlenden Feldes.
    
    Format: <fieldName_camelCase>.<optionValue_camelCase>
    Beispiel: "impactArea.local", "impactArea.regional"
    
    Args:
        missing_field: Feldname (z.B. "IMPACT_AREA", "AWARDS")
        sample_size: Anzahl der zufällig zu wählenden Optionen (default: 2)
    
    Returns:
        Liste von Quick-Reply-Strings im Format <field>.<option>
    """
    field_normalized = normalize_slot_field(missing_field)
    
    # Mapping von Field-Namen zu Enum-Klassen
    enum_map: Dict[str, type[Enum]] = {
        "IMPACT_AREA": ImpactAreaDto,
        "AWARDS": Award,
        "OFFER_CATEGORY": OfferCategory,
        "BEST_PRACTISE_CATEGORY": BestPractiseCategory,
        "THEMATIC_FOCUS": ThematicFocusDto,
        "INTENT": Intent,
    }
    
    enum_class = enum_map.get(field_normalized)
    if not enum_class:
        # Fallback für Felder ohne Enum (z.B. ONLINE, LOCATION, PERIOD, SDGS)
        return []
    
    # Extrahiere alle Enum-Optionen
    try:
        options = [member.name for member in enum_class]  # Namen: "LOCAL", "REGIONAL" etc.
    except Exception as e:
        print(f"⚠️ Fehler beim Extrahieren von Enum-Optionen für {field_normalized}: {e}")
        return []
    
    # Zufällig sample_size Optionen auswählen (mindestens so viele wie vorhanden)
    sample_size = min(sample_size, len(options))
    selected = random.sample(options, sample_size)
    
    # Formatierung: fieldName_camelCase.optionValue_camelCase
    field_camel = _to_camel_case(field_normalized)
    reply_strings = [f"{field_camel}.{_to_camel_case(opt)}" for opt in selected]
    
    print(f"📋 Generated quick replies for {field_normalized}: {reply_strings}")
    return reply_strings

def normalize_slot_field(field: str) -> str:
    if field is None:
        return ""

    return str(field).upper()

def generate_next_question(
        missing_field: str,
        message: MessageType,
        readyForSearch: bool,
        preferences: PreferenceContextDto,
        dialogContext: List[DialogMessage]
) -> NextQuestionResponse:
    """Generiert via Mistral eine natürlichsprachige Rückfrage für den fehlenden Slot."""

    known_text = _build_known_preferences_text(preferences)
    missing_field_key = normalize_slot_field(missing_field)
    field_label = _FIELD_LABELS.get(missing_field_key, missing_field_key)

    dialog_text = "\n".join([
        f"[{msg.sender}]: {msg.message}"
        for msg in dialogContext if msg.message
    ])

    prompt = f"""\
Du formulierst die nächste Rückfrage für einen Suchdialog auf einem Nachhaltigkeitsportal.

Regeln:
- Stelle genau eine kurze, freundliche Frage.
- Keine technischen Begriffe (kein "Slot", kein "SDG", kein "Parameter").
- Keine neuen Fakten erfinden.
- Beziehe dich auf bereits erkannte Präferenzen.
- Greife auf welche Informationen schon vorliegen. 
- Maximal 40 Wörter.
- Wenn nach SGD gefragt wird, frage geziehlt nach dem Nachhaltigkeitsziel bzw. Nachhaltigkeitszielen 
- Wenn MessageType = PREFERENCE_UPDATE, schreibe dazu welches was geändert wurde, lies das im Chatverlauf nach.
- Antworte ausschließlich mit gültigem JSON.

Bekannte Präferenzen:
{known_text}

Chatverlauf:
{dialog_text}

Fehlende Information: {field_label}

MessageType: {message}

JSON-Format:
{{
  "answer": "Deine Frage hier"
}}
"""

    print(f"❓ NextQuestion request: missingField={missing_field}")

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": "Du bist ein freundlicher Assistent auf einem Nachhaltigkeitsportal."},
            {"role": "user", "content": prompt},
        ],
        temperature=MISTRAL_QUESTION_TEMP,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    print(f"❓ NextQuestion response: {content}")

    data = json.loads(content)
    answer = data.get("answer", f"Was möchtest du zu {field_label} angeben?")

    if readyForSearch:
        answer += " Ich kann die Suche auch jetzt schon starten."

    # Generiere Quick Replies basierend auf Enum-Werten
    quick_replies = _get_enum_quick_replies(missing_field, sample_size=2)

    if preferences.period.start is not None:
        preferences.period.start = ensure_utc_iso(preferences.period.start)

    if preferences.period.end is not None:
        preferences.period.end = ensure_utc_iso(preferences.period.end)

    return NextQuestionResponse(
        answer=answer,
        quickReplies=quick_replies,
        preferences=preferences,
    )

def ensure_utc_iso(value: str | None) -> str | None:
    if value is None:
        return None

    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")