from typing import List, Optional, Set

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
    dialogContext: List[DialogMessage] = Field(default_factory=list)
    title: Optional[str] = None
    preferences: PreferenceContextDto = Field(default_factory=PreferenceContextDto)


class LlmExtractResponse(BaseModel):
    title: Optional[str] = None
    messageType: MessageType
    shouldExtractSlots: bool
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


class NextQuestionRequest(BaseModel):
    missingField: Optional[str] = None
    message: MessageType
    readyForSearch: bool
    preferences: PreferenceContextDto
    dialogContext: List[DialogMessage] = Field(default_factory=list)


class NextQuestionResponse(BaseModel):
    answer: str
    quickReplies: List[str] = Field(default_factory=list)
    preferences: PreferenceContextDto

