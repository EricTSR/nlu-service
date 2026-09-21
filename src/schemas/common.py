from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from src.schemas.enums import (
    Award,
    BestPractiseCategory,
    ImpactAreaDto,
    Intent,
    MessageType,
    OfferCategory,
    SlotFields,
    ThematicFocusDto,
)


class PeriodDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    _TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

    @field_validator("start", "end", mode="before")
    @classmethod
    def convert_timestamp(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).isoformat()
        return value

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def normalize_time(cls, value: Any) -> Any:
        if isinstance(value, str) and len(value) == 8 and value[5:] == ":00":
            return value[:5]
        return value

    start: str | None = Field(None)
    end: str | None = Field(None)
    start_time: str | None = Field(
        default=None,
        pattern=_TIME_PATTERN,
        validation_alias=AliasChoices("startTime", "start_time"),
        serialization_alias="startTime",
    )
    end_time: str | None = Field(
        default=None,
        pattern=_TIME_PATTERN,
        validation_alias=AliasChoices("endTime", "end_time"),
        serialization_alias="endTime",
    )
    permanent: bool | None = Field(False)


class LocationFilterDto(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius: float | None = None


class PreferenceContextDto(BaseModel):
    intent: Intent | None = None
    location: LocationFilterDto | None = None
    online: bool | None = None
    period: PeriodDto = Field(default_factory=PeriodDto)
    sdgs: list[int] = Field(default_factory=list)
    thematicFocus: ThematicFocusDto | None = None
    impactArea: ImpactAreaDto | None = None
    awards: list[Award] | None = None
    offerCategory: OfferCategory | None = None
    bestPractiseCategory: BestPractiseCategory | None = None
    confidence: float | None = None
    handledFields: set[SlotFields] = Field(default_factory=set)
    pendingField: SlotFields | None = None


class DialogMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("id", "number"),
        serialization_alias="id",
    )
    message: str | None = None
    sender: str | None = None
    quickReplies: list[str] | None = None
    messageType: MessageType | None = None
