from datetime import datetime
from typing import List, Optional, Set

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
    def convert_timestamp(cls, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).isoformat()
        return value

    start: Optional[str] = Field(None)
    end: Optional[str] = Field(None)
    start_time: Optional[str] = Field(None)
    end_time: Optional[str] = Field(None)
    permanent: Optional[bool] = Field(False)


class LocationFilterDto(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float] = None


class PreferenceContextDto(BaseModel):
    intent: Optional[str] = None
    location: Optional[LocationFilterDto] = None
    online: Optional[bool] = None
    period: PeriodDto = Field(default_factory=PeriodDto)
    sdgs: List[int] = Field(default_factory=list)
    thematicFocus: Optional[ThematicFocusDto] = None
    impactArea: Optional[ImpactAreaDto] = None
    awards: Optional[List[Award]] = None
    offerCategory: Optional[OfferCategory] = None
    bestPractiseCategory: Optional[BestPractiseCategory] = None
    confidence: Optional[float] = None
    handledFields: Set[SlotFields] = Field(default_factory=set)
    pendingField: Optional[SlotFields] = None


class DialogMessage(BaseModel):
    number: Optional[int] = None
    message: Optional[str] = None
    sender: Optional[str] = None
    quickReplies: Optional[List[str]] = None
    messageType: Optional[MessageType] = None

