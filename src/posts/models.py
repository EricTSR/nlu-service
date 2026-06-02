from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Set
from enum import Enum
from datetime import datetime


class Intent(str, Enum):
    SEARCH_MARKETPLACE = "SEARCH_MARKETPLACE"
    SEARCH_ORGANISATIONS = "SEARCH_ORGANISATIONS"
    SEARCH_ACTIVITIES = "SEARCH_ACTIVITIES"


class Award(str, Enum):
    INITIATOR = "INITIATOR"
    AWARD = "AWARD"


class Recommendation(str, Enum):
    ORGANISATION = "ORGANISATION"
    ACTIVITY = "ACTIVITY"
    MARKETPLACE = "MARKETPLACE"


class MessageType(str, Enum):
    GREETING = "GREETING"
    CHITCHAT = "CHITCHAT"
    HELP = "HELP"
    ANSWER = "ANSWER"
    SEARCH_REQUEST = "SEARCH_REQUEST"
    PREFERENCE_UPDATE = "PREFERENCE_UPDATE"
    CONFIRMATION = "CONFIRMATION"
    REJECTION = "REJECTION"
    REFINE_SEARCH = "REFINE_SEARCH"
    EXIT = "EXIT"
    ERROR = "ERROR"


class PeriodDto(BaseModel):
    """Period mit Start/End-Datum für Aktivitäten/Angebote"""

    @field_validator("start", "end", mode="before")
    @classmethod
    def convert_timestamp(cls, value):

        if value is None:
            return None

        # Wenn Timestamp kommt, weil WRITE_DATES_AS_TIMESTAMPS 4
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).isoformat()

        # Wenn schon String
        return value

    start: Optional[str] = Field(None)
    end: Optional[str] = Field(None)
    start_time: Optional[str] = Field(None)
    end_time: Optional[str] = Field(None)
    permanent: Optional[bool] = Field(False)


class ThematicFocusDto(str, Enum):
    PARTICIPATION = "PARTICIPATION"
    EDUCATION = "EDUCATION"
    BIODIVERSITY = "BIODIVERSITY"
    HUMAN_RIGHTS = "HUMAN_RIGHTS"
    GENDER_EQUITY = "GENDER_EQUITY"
    PEACE = "PEACE"
    INTERNATIONAL_RESPONSIBILITY = "INTERNATIONAL_RESPONSIBILITY"
    CLIMATE_PROTECTION = "CLIMATE_PROTECTION"
    CIRCULAR_ECONOMY = "CIRCULAR_ECONOMY"
    CULTURAL_SOCIAL_CHANGE = "CULTURAL_SOCIAL_CHANGE"
    AGRICULTURE = "AGRICULTURE"
    MOBILITY = "MOBILITY"
    SUSTAINABLE_PROCUREMENT = "SUSTAINABLE_PROCUREMENT"
    SUSTAINABLE_FINANCE = "SUSTAINABLE_FINANCE"
    SUSTAINABLE_LIFESTYLE = "SUSTAINABLE_LIFESTYLE"
    SUSTAINABLE_BUILDING = "SUSTAINABLE_BUILDING"
    SUSTAINABLE_BUSINESS = "SUSTAINABLE_BUSINESS"
    SUSTAINABLE_GOVERNANCE = "SUSTAINABLE_GOVERNANCE"
    SOCIAL_JUSTICE = "SOCIAL_JUSTICE"
    SPORT = "SPORT"
    URBAN_DEVELOPMENT = "URBAN_DEVELOPMENT"
    TOURISM = "TOURISM"
    OTHER = "OTHER"
    DIGITALIZATION = "DIGITALIZATION"


class SlotFields(str, Enum):
    INTENT = "INTENT"
    LOCATION = "LOCATION"
    ONLINE = "ONLINE"
    PERIOD = "PERIOD"
    SDGS = "SDGS"
    THEMATIC_FOCUS = "THEMATIC_FOCUS"
    IMPACT_AREA = "IMPACT_AREA"
    AWARDS = "AWARDS"
    OFFER_CATEGORY = "OFFER_CATEGORY"
    BEST_PRACTISE_CATEGORY = "BEST_PRACTISE_CATEGORY"

class SDG(str, Enum):
    GOAL_1  = "Keine Armut"
    GOAL_2  = "Kein Hunger"
    GOAL_3  = "Gesundheit und Wohlergehen"
    GOAL_4  = "Hochwertige Bildung"
    GOAL_5  = "Geschlechtergleichheit"
    GOAL_6  = "Sauberes Wasser und Sanitäreinrichtungen"
    GOAL_7  = "Bezahlbare und saubere Energie"
    GOAL_8  = "Menschenwürdige Arbeit und Wirtschaftswachstum"
    GOAL_9  = "Industrie, Innovation und Infrastruktur"
    GOAL_10 = "Weniger Ungleichheiten"
    GOAL_11 = "Nachhaltige Städte und Gemeinden"
    GOAL_12 = "Nachhaltige/r Konsum und Produktion"
    GOAL_13 = "Maßnahmen zum Klimaschutz"
    GOAL_14 = "Leben unter Wasser"
    GOAL_15 = "Leben an Land"
    GOAL_16 = "Frieden, Gerechtigkeit und starke Institutionen"
    GOAL_17 = "Partnerschaften zur Erreichung der Ziele"

class ImpactAreaDto(str, Enum):
    LOCAL = "LOCAL"
    REGIONAL = "REGIONAL"
    STATE = "STATE"
    COUNTRY = "COUNTRY"
    CONTINENT = "CONTINENT"
    WORLD = "WORLD"


class OfferCategory(str, Enum):
    JOBS = "JOBS"
    REPORTING_STANDARDS = "REPORTING_STANDARDS"
    EDUCATIONAL_OFFERS = "EDUCATIONAL_OFFERS"
    FUNDING_PROGRAMMES_AND_GRANTS = "FUNDING_PROGRAMMES_AND_GRANTS"
    CONTESTS = "CONTESTS"
    VOLUNTEERING = "VOLUNTEERING"
    MATERIALS = "MATERIALS"
    FACILITIES = "FACILITIES"
    CONSULTING = "CONSULTING"
    OTHER = "OTHER"
    NETWORK = "NETWORK"
    PROJECT_SUSTAINABILITY = "PROJECT_SUSTAINABILITY"


class BestPractiseCategory(str, Enum):
    SUSTAINABILITY_REPORTING = "SUSTAINABILITY_REPORTING"
    PROJECT_REPORT = "PROJECT_REPORT"
    OTHER = "OTHER"


class LocationFilterDto(BaseModel):
    """Strukturierte Location mit Adresskomponenten und Geokoordinaten."""
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float] = None  # in km


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


class DialogMessage(BaseModel):
    """Einzelne Nachricht im Dialogverlauf."""
    number: Optional[int] = None
    message: Optional[str] = None
    sender: Optional[str] = None  # "USER" oder "BOT"
    quickReplies: Optional[List[str]] = None
    messageType: Optional[MessageType] = None


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


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


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
