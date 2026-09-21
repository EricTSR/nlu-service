from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.schemas.common import DialogMessage, LocationFilterDto, PeriodDto, PreferenceContextDto
from src.schemas.enums import (
    Award,
    BestPractiseCategory,
    DialogLocale,
    ImpactAreaDto,
    Intent,
    MessageType,
    OfferCategory,
    SlotFields,
    ThematicFocusDto,
)


class NluExtractRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    dialogContext: list[DialogMessage] = Field(default_factory=list, max_length=100)
    title: str | None = None
    preferences: PreferenceContextDto = Field(default_factory=PreferenceContextDto)
    locale: DialogLocale = DialogLocale.DE

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class LlmExtractResponse(BaseModel):
    @field_validator("period", mode="before")
    @classmethod
    def normalize_null_period(cls, value: Any) -> Any:
        return {} if value is None else value

    title: str | None = None
    messageType: MessageType
    shouldExtractSlots: bool
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


class NextQuestionRequest(BaseModel):
    missingField: SlotFields | None = None
    message: MessageType
    readyForSearch: bool
    preferences: PreferenceContextDto
    dialogContext: list[DialogMessage] = Field(default_factory=list, max_length=100)
    locale: DialogLocale = DialogLocale.DE


class NextQuestionResponse(BaseModel):
    answer: str
    quickReplies: list[str] = Field(default_factory=list)
    preferences: PreferenceContextDto
