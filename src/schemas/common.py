from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.schemas.enums import (
    Award,
    BestPractiseCategory,
    ImpactAreaDto,
    MessageType,
    OfferCategory,
    SlotFields,
    ThematicFocusDto,
)


class PeriodDto(BaseModel):
    @field_validator("start", "end", mode="before")
    @classmethod
    def convert_timestamp(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).isoformat()
        return value

    start: str | None = Field(None)
    end: str | None = Field(None)
    start_time: str | None = Field(None)
    end_time: str | None = Field(None)
    permanent: bool | None = Field(False)


class LocationFilterDto(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius: float | None = None


class PreferenceContextDto(BaseModel):
    intent: str | None = None
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
    number: int | None = None
    message: str | None = None
    sender: str | None = None
    quickReplies: list[str] | None = None
    messageType: MessageType | None = None
