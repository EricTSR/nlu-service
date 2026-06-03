from typing import List

from pydantic import BaseModel, Field

from src.schemas.common import DialogMessage, PreferenceContextDto
from src.schemas.enums import Recommendation


class NluRankItemDto(BaseModel):
    id: int
    semanticScore: float


class Candidate(BaseModel):
    id: int
    description: str


class SemanticRankResponseDto(BaseModel):
    results: List[NluRankItemDto] = Field(default_factory=list)


class SemanticRankRequestDto(BaseModel):
    preferences: PreferenceContextDto
    dialogContext: List[DialogMessage] = Field(default_factory=list)
    recommendation: Recommendation = Field(default_factory=Recommendation)
    candidates: List[Candidate] = Field(default_factory=list)

