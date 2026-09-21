from pydantic import BaseModel, Field

from src.schemas.common import DialogMessage, LocationFilterDto, PeriodDto, PreferenceContextDto
from src.schemas.enums import (
    Award,
    BestPractiseCategory,
    ImpactAreaDto,
    MessageType,
    OfferCategory,
    SlotFields,
    ThematicFocusDto,
)


class NluExtractRequest(BaseModel):
    message: str
    dialogContext: list[DialogMessage] = Field(default_factory=list)
    title: str | None = None
    preferences: PreferenceContextDto = Field(default_factory=PreferenceContextDto)


class LlmExtractResponse(BaseModel):
    title: str | None = None
    messageType: MessageType
    shouldExtractSlots: bool
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


class NextQuestionRequest(BaseModel):
    missingField: SlotFields | None = None
    message: MessageType
    readyForSearch: bool
    preferences: PreferenceContextDto
    dialogContext: list[DialogMessage] = Field(default_factory=list)


class NextQuestionResponse(BaseModel):
    answer: str
    quickReplies: list[str] = Field(default_factory=list)
    preferences: PreferenceContextDto
