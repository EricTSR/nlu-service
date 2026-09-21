import random
from enum import Enum

from src.schemas import (
    SDG,
    Award,
    BestPractiseCategory,
    ImpactAreaDto,
    Intent,
    OfferCategory,
    SlotFields,
    ThematicFocusDto,
)


def _to_camel_case(snake_str: str) -> str:
    """Converts SNAKE_CASE or snake_case to camelCase."""
    parts = snake_str.lower().split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def get_enum_quick_replies(
    missing_field: SlotFields | None,
    sample_size: int = 2,
) -> list[str]:
    """
    Generiert Quick Replies basierend auf Enum-Werten des fehlenden Feldes.

    Format: <fieldName_camelCase>.<optionValue_camelCase>
    Beispiel: "impactArea.local", "impactArea.regional"

    """
    if missing_field is None:
        return []

    # Mapping von Field-Namen zu Enum-Klassen
    enum_map: dict[SlotFields, type[Enum]] = {
        SlotFields.SDGS: SDG,
        SlotFields.IMPACT_AREA: ImpactAreaDto,
        SlotFields.AWARDS: Award,
        SlotFields.OFFER_CATEGORY: OfferCategory,
        SlotFields.BEST_PRACTISE_CATEGORY: BestPractiseCategory,
        SlotFields.THEMATIC_FOCUS: ThematicFocusDto,
        SlotFields.INTENT: Intent,
    }

    enum_class = enum_map.get(missing_field)
    if not enum_class:
        return []
    options = [member.name for member in enum_class]

    sample_size = min(sample_size, len(options))
    selected = random.sample(options, sample_size)

    # Formatierung: fieldName_camelCase.optionValue_camelCase
    field_camel = _to_camel_case(missing_field.value)
    reply_strings = [
        f"response.quickReplies.{field_camel}.{_to_camel_case(opt)}" for opt in selected
    ]

    return reply_strings
